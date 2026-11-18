import os
import logging
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from config import settings
from database import init_db, get_db, Product, DocumentChunk
from rag_engine import ingest_pdf_to_db
from agent_orchestrator import run_agent_turn, run_agent_turn_stream

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("prawira_agent.main")

app = FastAPI(
    title="Prawira Tobacco Document Intelligence & Action Agent",
    description="Enterprise RAG with Tool Calling (Database Inventory & WhatsApp Dispatch)",
    version="1.0.0"
)

# Enable CORS for Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing Prawira Tobacco Agent backend...")
    init_db()
    try:
        from sync_supabase import sync_products_from_supabase
        sync_products_from_supabase()
    except Exception as e:
        logger.warning(f"Auto-sync from Supabase at startup skipped: {e}")

    # Auto-seed sample PDF documents if document chunks are empty
    try:
        from database import SessionLocal
        db = SessionLocal()
        chunk_count = db.query(DocumentChunk).count()
        if chunk_count == 0:
            logger.info("No documents in database. Auto-ingesting sample PDFs...")
            sample_candidates = [
                os.path.join(os.path.dirname(__file__), "..", "sample_documents"),
                os.path.join(os.path.dirname(__file__), "sample_documents"),
                os.path.abspath("sample_documents")
            ]
            for s_dir in sample_candidates:
                if os.path.exists(s_dir):
                    for fname in os.listdir(s_dir):
                        if fname.lower().endswith(".pdf"):
                            fpath = os.path.join(s_dir, fname)
                            with open(fpath, "rb") as f:
                                cnt = ingest_pdf_to_db(db, f.read(), fname)
                                logger.info(f"Auto-ingested {cnt} chunks from '{fname}'.")
                    break
        db.close()
    except Exception as e:
        logger.warning(f"Auto-ingest sample docs skipped: {e}")

@app.get("/api/debug-status")
def debug_status():
    """Provides diagnostic status for production verification."""
    from database import SessionLocal
    db = SessionLocal()
    prod_cnt = db.query(Product).count()
    chunk_cnt = db.query(DocumentChunk).count()
    db.close()

    gemini_key_set = bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 5)
    key_preview = f"{settings.GEMINI_API_KEY[:4]}...{settings.GEMINI_API_KEY[-4:]}" if gemini_key_set else "NOT_SET"

    gemini_test_result = "not_tested"
    try:
        if gemini_key_set:
            import google.generativeai as gai
            gai.configure(api_key=settings.GEMINI_API_KEY)
            m = gai.GenerativeModel("models/gemini-flash-lite-latest")
            res = m.generate_content("test")
            gemini_test_result = f"ok: {res.text.strip()[:40]}"
    except Exception as e:
        gemini_test_result = f"error: {str(e)}"

    return {
        "status": "healthy",
        "llm_provider": settings.LLM_PROVIDER,
        "has_gemini_key": gemini_key_set,
        "gemini_key_preview": key_preview,
        "gemini_test": gemini_test_result,
        "total_products": prod_cnt,
        "total_document_chunks": chunk_cnt,
        "gemini_model": settings.GEMINI_MODEL
    }

@app.post("/api/sync-supabase")
def trigger_supabase_sync():
    """Manual sync trigger endpoint for Frontend UI."""
    from sync_supabase import sync_products_from_supabase
    ok = sync_products_from_supabase()
    return {
        "success": ok, 
        "message": "Katalog Supabase Prawira Tobacco berhasil disinkronkan!" if ok else "Gagal sinkronisasi dari Supabase."
    }

# Request & Response Schemas
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_session"

class HealthResponse(BaseModel):
    status: str
    database: str
    llm_provider: str
    total_products: int
    total_document_chunks: int

@app.get("/api/test-version")
def test_version():
    return {"version": "2.0-latest"}

@app.get("/api/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    try:
        prod_count = db.query(Product).count()
        chunk_count = db.query(DocumentChunk).count()
        db_status = "connected"
    except Exception as e:
        logger.warning(f"DB health check error: {e}")
        db_status = f"offline ({e})"
        prod_count = 0
        chunk_count = 0

    return HealthResponse(
        status="healthy",
        database=db_status,
        llm_provider=settings.LLM_PROVIDER,
        total_products=prod_count,
        total_document_chunks=chunk_count
    )

@app.get("/api/products")
def list_products(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Product)
    if category and category != "all":
        query = query.filter(Product.category == category)
    products = query.order_by(Product.name.asc()).all()
    return {
        "count": len(products),
        "products": [
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "category": p.category,
                "similarity_grade": p.similarity_grade,
                "stock": p.stock,
                "unit": p.unit,
                "weight_grams": p.weight_grams,
                "price": float(p.price),
                "shelf_location": p.shelf_location,
                "description": p.description
            }
            for p in products
        ]
    }

@app.get("/api/documents")
def list_documents(db: Session = Depends(get_db)):
    """Returns list of unique documents and their chunk counts."""
    docs = db.query(
        DocumentChunk.document_name,
        func.count(DocumentChunk.id).label("chunks_count"),
        func.max(DocumentChunk.page_number).label("total_pages"),
        func.min(DocumentChunk.created_at).label("uploaded_at")
    ).group_by(DocumentChunk.document_name).all()

    return {
        "count": len(docs),
        "documents": [
            {
                "document_name": d.document_name,
                "chunks_count": d.chunks_count,
                "total_pages": d.total_pages,
                "uploaded_at": str(d.uploaded_at) if d.uploaded_at else ""
            }
            for d in docs
        ]
    }

@app.post("/api/upload-document")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Hanya berkas berformat .pdf yang didukung.")

    try:
        content_bytes = await file.read()
        chunks_stored = ingest_pdf_to_db(db, content_bytes, file.filename)
        return {
            "success": True,
            "filename": file.filename,
            "chunks_stored": chunks_stored,
            "message": f"Berhasil memproses dan menyimpan {chunks_stored} potongan dokumen ke pgvector."
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal memproses dokumen: {str(e)}")

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong.")

    try:
        result = run_agent_turn(db, user_message=req.message)
        return result
    except Exception as e:
        logger.error(f"Chat turn error: {e}")
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan pada agent: {str(e)}")

@app.post("/api/chat/stream")
def chat_stream_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Real-time Server-Sent Events (SSE) streaming endpoint:
    Streams RAG citations, live tool execution events, and token-by-token answer generation.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong.")

    try:
        return StreamingResponse(
            run_agent_turn_stream(db, user_message=req.message),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Chat stream endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan streaming: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
