# Product Context

## Platform
web (Next.js 15, React 19, Tailwind CSS, Python FastAPI, PostgreSQL 16 + pgvector)

## Product
**Enterprise Document Intelligence & WhatsApp Action Agent (Prawira Tobacco Edition)**  
An enterprise-grade AI agent system designed for retail and e-commerce enterprises, specifically customized for **Prawira Tobacco**. It combines semantic document intelligence (RAG over official SOPs and product catalogs), real-time inventory querying against a live PostgreSQL / Supabase cloud database, and automated multi-channel tool calling via WhatsApp Gateway.

## Target Audience & Situations
- **Retail Customers / Buyers:** Seeking personalized tobacco flavor recommendations (sweet/fruity, bold kretek, menthol ice, mild beginner) and real-time stock availability.
- **Store Operations & Warehouse Supervisors:** Needing immediate verification of warehouse storage SOPs (optimal relative humidity 65-70%, airtight containment) and return/warranty claim policies (2x24h unboxing video requirements).
- **Store Management & Retail Operations:** Ensuring grounded SOP guidance, live inventory sync with Supabase, and automated WhatsApp order dispatching.

## Core Capabilities & Workflows
1. **Document Intelligence & Grounded RAG:**
   - Ingests and semantically chunks official PDF documentation (`SOP_Penyimpanan_dan_Garansi_Prawira.pdf` and `Katalog_Varian_Prawira_Tobacco.pdf`).
   - Generates high-dimensional vector embeddings stored in PostgreSQL with HNSW cosine distance indexing.
   - Provides verifiable citations (exact document name, page number, and similarity score) to prevent hallucinations.
2. **Live Database Inventory Tool Calling (`check_inventory_stock`):**
   - Directly queries the live cloud Supabase database (`mitkblmftejogdxmewet.supabase.co`) with fallback to local PostgreSQL.
   - Accurately reports product SKU, name, price, stock quantity, and warehouse location.
3. **WhatsApp Action Dispatcher (`send_whatsapp_action`):**
   - Dispatches structured summaries and order links via the official Fonnte WhatsApp API Gateway directly to the store device (`083132001855`).
   - Generates instant clickable `https://wa.me/6283132001855?text=...` action URLs for one-click customer follow-up.
4. **Hybrid Fallback Orchestrator:**
   - Primary LLM reasoning with Google Gemini (`gemini-2.5-flash`) / OpenAI compatibility.
   - Consultative fallback engine equipped with Prawira Tobacco's complete flavor taxonomy and live Supabase catalog for 100% offline and rate-limit resilience.

## Durable Constraints & Business Rules
- **Recommendation Cardinality Mandate:** If the user requests 1 recommendation ("rekomendasikan 1", "pilihin satu", "kasih 1 saja"), the agent must select EXACTLY 1 product and provide an in-depth flavor analysis, querying stock for only that product. If the user specifies $N$ items, the agent must provide exactly $N$ items. If unspecified, provide 2-3 top recommendations.
- **Anti-Hallucination Mandate:** The AI must NEVER invent brand names, unverified products, or fake blend names. Recommendations must come exclusively from the 24 verified products synchronized with Prawira Tobacco's Supabase database.
- **WhatsApp Target Phone:** Official store device number is `083132001855` (`6283132001855`).
- **Data Source of Truth:** Live catalog data is synced from Supabase Cloud (`https://mitkblmftejogdxmewet.supabase.co`).
