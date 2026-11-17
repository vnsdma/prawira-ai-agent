import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, SessionLocal, Product, DocumentChunk
from rag_engine import ingest_pdf_to_db, search_relevant_chunks
from agent_tools import check_inventory_stock, send_whatsapp_action
from agent_orchestrator import run_agent_turn

def run_all_tests():
    print("=== [1/5] Testing Database Initialization & Seeding ===")
    success = init_db()
    assert success, "Failed to initialize database."
    
    with SessionLocal() as db:
        prod_count = db.query(Product).count()
        print(f"Products in DB: {prod_count}")
        assert prod_count >= 10, "Expected at least 10 seeded products."

    print("\n=== [2/5] Testing PDF Ingestion (RAG) ===")
    sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_documents")
    sop_file = os.path.join(sample_dir, "SOP_Penyimpanan_dan_Garansi_Prawira.pdf")
    
    assert os.path.exists(sop_file), f"File not found: {sop_file}"
    with open(sop_file, "rb") as f:
        pdf_bytes = f.read()

    with SessionLocal() as db:
        chunks_count = ingest_pdf_to_db(db, pdf_bytes, "SOP_Penyimpanan_dan_Garansi_Prawira.pdf")
        print(f"Ingested chunks: {chunks_count}")
        assert chunks_count > 0, "No chunks were created from PDF."

    print("\n=== [3/5] Testing RAG Vector Search ===")
    with SessionLocal() as db:
        query = "Berapa kadar kelembaban optimal untuk penyimpanan tembakau?"
        results = search_relevant_chunks(db, query=query, top_k=2)
        print(f"Query: '{query}'")
        print(f"Top result: {results[0]['content'][:120]}... (Sim: {results[0]['similarity']})")
        assert len(results) > 0, "Expected matching RAG chunks."

    print("\n=== [4/5] Testing Tool Calling Functions ===")
    with SessionLocal() as db:
        stock_res = check_inventory_stock(db, search_term="Surya")
        print(f"check_inventory_stock result: Found={stock_res['found']}, Items={len(stock_res['items'])}")
        assert stock_res["found"] is True, "Expected Linting Surya to be found."

        wa_res = send_whatsapp_action(phone_number="083132001855", message_body="Tes pesanan Prawira")
        print(f"send_whatsapp_action result: Mode={wa_res['mode']}, URL={wa_res['direct_url'][:45]}...")
        assert "wa.me" in wa_res["direct_url"], "Expected valid wa.me URL."

    print("\n=== [5/5] Testing End-to-End Agent Orchestrator ===")
    with SessionLocal() as db:
        agent_out = run_agent_turn(
            db, 
            user_message="Berapa sisa stok Linting Surya dan tolong siapkan ringkasannya untuk WA ke 083132001855"
        )
        print("\nAgent Response:")
        print("--------------------------------------------------")
        print(agent_out["answer"])
        print("--------------------------------------------------")
        print(f"Tools Executed: {[t['tool'] for t in agent_out['executed_tools']]}")
        print(f"Citations: {len(agent_out['citations'])}")
        assert len(agent_out["executed_tools"]) >= 1, "Expected tools to be executed by the agent."

    print("\nALL BACKEND PIPELINE TESTS PASSED 100%!")

if __name__ == "__main__":
    run_all_tests()
