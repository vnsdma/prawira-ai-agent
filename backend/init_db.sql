-- ============================================================
-- Prawira Tobacco Enterprise Database Initialization Script
-- Supports PostgreSQL with pgvector extension
-- ============================================================

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create document_chunks table for RAG
CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_name VARCHAR(255) NOT NULL,
    chunk_index INT NOT NULL,
    page_number INT DEFAULT 1,
    content TEXT NOT NULL,
    -- 768 dimensions for Gemini text-embedding-004, 1536 for OpenAI text-embedding-3-small
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Cosine distance index using HNSW for millisecond similarity queries
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- 3. Create products table for Tool Calling (Inventory check)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    similarity_grade VARCHAR(50) DEFAULT 'premium', -- 'premium', 'harian', 'ekonomis'
    stock INT NOT NULL DEFAULT 0,
    unit VARCHAR(20) DEFAULT 'pack',
    weight_grams INT DEFAULT 100,
    price NUMERIC(12, 2) NOT NULL,
    shelf_location VARCHAR(50),
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Products data is synchronized exclusively from live Supabase (mitkblmftejogdxmewet.supabase.co)
-- Run python sync_supabase.py or trigger via API /api/sync-supabase

