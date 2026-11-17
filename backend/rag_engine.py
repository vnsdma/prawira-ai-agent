import os
import io
import math
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from sqlalchemy.orm import Session
from sqlalchemy import text
from config import settings
from database import DocumentChunk, is_sqlite

logger = logging.getLogger("prawira_agent.rag")

def get_fallback_embedding(text_content: str, dim: int = 768) -> List[float]:
    """
    Deterministic pseudo-embedding fallback when API keys are not yet configured.
    Ensures the RAG pipeline continues working safely in test environments.
    """
    hasher = hashlib.sha256(text_content.encode('utf-8'))
    digest = hasher.digest()
    vec = []
    for i in range(dim):
        byte_val = digest[i % len(digest)]
        val = math.sin((byte_val + i) * 0.1)
        vec.append(val)
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [round(x / norm, 6) for x in vec]

def generate_embedding(text_content: str) -> List[float]:
    """
    Generates embedding using Gemini or OpenAI based on LLM_PROVIDER setting.
    """
    cleaned_text = text_content.strip().replace("\n", " ")
    if not cleaned_text:
        return [0.0] * 768

    # 1. Gemini Provider
    if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                contents=cleaned_text,
            )
            if hasattr(response, 'embeddings') and len(response.embeddings) > 0:
                return response.embeddings[0].values
            elif hasattr(response, 'embedding') and hasattr(response.embedding, 'values'):
                return response.embedding.values
        except Exception as e:
            try:
                import google.generativeai as gai
                gai.configure(api_key=settings.GEMINI_API_KEY)
                res = gai.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    content=cleaned_text,
                    task_type="retrieval_document"
                )
                return res['embedding']
            except Exception as e2:
                logger.warning(f"Gemini embedding error: {e}. Falling back to deterministic embedding.")

    # 2. OpenAI Provider
    elif settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(
                input=cleaned_text,
                model=settings.OPENAI_EMBEDDING_MODEL
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"OpenAI embedding error: {e}. Falling back to deterministic embedding.")

    # 3. Fallback when keys are missing or provider offline
    return get_fallback_embedding(cleaned_text, dim=768)

def split_text_into_chunks(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """
    Splits long text into overlapping chunks cleanly without cutting sentences abruptly.
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        if end < len(text):
            last_break = max(chunk.rfind("\n"), chunk.rfind(". "), chunk.rfind("? "), chunk.rfind("! "))
            if last_break > chunk_size // 2:
                end = start + last_break + 1
                chunk = text[start:end]

        cleaned_chunk = chunk.strip()
        if cleaned_chunk:
            chunks.append(cleaned_chunk)
        start += max(1, chunk_size - overlap)

    return chunks

def extract_and_chunk_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Extracts text from PDF bytes and splits into chunks with page metadata.
    """
    reader = PdfReader(io.BytesIO(file_bytes))
    all_chunks = []
    chunk_counter = 0

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        page_text = page.extract_text() or ""
        page_chunks = split_text_into_chunks(page_text, chunk_size=800, overlap=100)
        
        for ch in page_chunks:
            all_chunks.append({
                "document_name": filename,
                "page_number": page_num,
                "chunk_index": chunk_counter,
                "content": ch
            })
            chunk_counter += 1

    return all_chunks

def ingest_pdf_to_db(db: Session, file_bytes: bytes, filename: str) -> int:
    """
    Parses PDF, computes embeddings, and stores them in PostgreSQL/SQLite document_chunks table.
    """
    # Delete existing chunks for same document if re-uploading
    db.query(DocumentChunk).filter(DocumentChunk.document_name == filename).delete()
    db.commit()

    chunk_records = extract_and_chunk_pdf(file_bytes, filename)
    if not chunk_records:
        return 0

    inserted_count = 0
    for chunk_info in chunk_records:
        emb = generate_embedding(chunk_info["content"])
        doc_chunk = DocumentChunk(
            document_name=chunk_info["document_name"],
            page_number=chunk_info["page_number"],
            chunk_index=chunk_info["chunk_index"],
            content=chunk_info["content"],
            embedding=emb if not is_sqlite else None,
            embedding_json=json.dumps(emb)
        )
        db.add(doc_chunk)
        inserted_count += 1

    db.commit()
    logger.info(f"Ingested {inserted_count} chunks from '{filename}'.")
    return inserted_count

def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1)) or 1.0
    norm2 = math.sqrt(sum(b * b for b in vec2)) or 1.0
    return dot / (norm1 * norm2)

def search_relevant_chunks(db: Session, query: str, top_k: int = 4, threshold: float = 0.40) -> List[Dict[str, Any]]:
    """
    Performs cosine similarity search over document_chunks.
    Uses pgvector native operator if on PostgreSQL, or in-memory vector comparison for SQLite.
    """
    query_emb = generate_embedding(query)

    # 1. Native pgvector if available
    if not is_sqlite:
        vec_str = "[" + ",".join(str(round(x, 6)) for x in query_emb) + "]"
        sql = text("""
            SELECT 
                id,
                document_name,
                page_number,
                chunk_index,
                content,
                1 - (embedding <=> :vec::vector) AS similarity
            FROM document_chunks
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :vec::vector ASC
            LIMIT :limit;
        """)
        try:
            result = db.execute(sql, {"vec": vec_str, "limit": top_k}).fetchall()
            matching_chunks = []
            for row in result:
                sim = float(row.similarity) if row.similarity is not None else 0.0
                if sim >= threshold:
                    matching_chunks.append({
                        "id": row.id,
                        "document_name": row.document_name,
                        "page_number": row.page_number,
                        "chunk_index": row.chunk_index,
                        "content": row.content,
                        "similarity": round(sim, 4)
                    })
            if matching_chunks:
                return matching_chunks
        except Exception as e:
            db.rollback()
            logger.debug(f"pgvector query skipped ({e}), falling back to memory vector search.")

    # 2. In-memory Cosine Similarity across document chunks
    all_chunks = db.query(DocumentChunk).all()
    scored_chunks = []
    for c in all_chunks:
        if c.embedding_json:
            try:
                emb = json.loads(c.embedding_json)
                sim = _cosine_similarity(query_emb, emb)
                if sim >= threshold:
                    scored_chunks.append({
                        "id": c.id,
                        "document_name": c.document_name,
                        "page_number": c.page_number,
                        "chunk_index": c.chunk_index,
                        "content": c.content,
                        "similarity": round(sim, 4)
                    })
            except Exception:
                continue

    # Sort descending by similarity
    scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
    if scored_chunks:
        return scored_chunks[:top_k]

    # 3. Keyword / BM25 Fallback when embeddings are pseudo-hashes (offline mode without API keys)
    query_words = set(w.lower() for w in query.split() if len(w) > 3)
    keyword_scored = []
    for c in all_chunks:
        content_lower = c.content.lower()
        match_count = sum(1 for w in query_words if w in content_lower)
        if match_count > 0:
            keyword_scored.append({
                "id": c.id,
                "document_name": c.document_name,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
                "content": c.content,
                "similarity": round(min(0.95, 0.50 + (match_count * 0.15)), 4)
            })

    keyword_scored.sort(key=lambda x: x["similarity"], reverse=True)
    return keyword_scored[:top_k]
