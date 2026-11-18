import os
import sys
import re

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, SessionLocal, Product
from agent_orchestrator import (
    _extract_requested_count,
    _execute_deterministic_agent,
    run_agent_turn,
    FLAVOR_CATALOG
)

def count_product_mentions(text: str) -> int:
    """Helper to count how many distinct official products are mentioned in the text without substring collisions."""
    official_products = [
        "Linting Melon Ice", "Linting Strawberry", "Linting Cappucino", "Purple Ice Burst",
        "Coklat Ice Premium", "Linting Surya", "Linting Samsu", "Linting Marlong",
        "Linting GGF", "Magnum Premium", "Sampurna Premium", "GGF Premium",
        "Barrack Whiskey Ice", "Linting Mild", "Barrack Soju", "Barrack Bayote",
        "Barrack Melisa", "Barrack Whiskey"
    ]
    # Sort by length descending so longer titles match first (e.g. Barrack Whiskey Ice before Barrack Whiskey)
    sorted_prods = sorted(official_products, key=lambda s: len(s), reverse=True)
    temp_text = text.lower()
    found = []
    for p in sorted_prods:
        pattern = rf"\b{re.escape(p.lower())}\b"
        if re.search(pattern, temp_text):
            found.append(p)
            # Mask out the matched product to prevent shorter substrings from double-counting
            temp_text = re.sub(pattern, " [MATCHED_PROD] ", temp_text)
    return len(found)

def run_cardinality_tests():
    print("=" * 70)
    print("PRAWIRA TOBACCO AGENT — RECOMMENDATION CARDINALITY TEST SUITE")
    print("Pengujian Kepatuhan Jumlah Rekomendasi (1 Produk vs Multi Produk)")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. TEST REGEX EXTRACTOR FOR REQUESTED COUNT
    # -------------------------------------------------------------
    print("\n[Stage 1/3] Testing Regex Cardinality Extractor (_extract_requested_count)")
    test_cases = [
        ("Rekomendasikan 1 tembakau manis yang paling enak", 1),
        ("Pilihin satu varian tembakau kretek yang paling mantap", 1),
        ("Kasih 1 saja yang paling enak", 1),
        ("Pilihkan 1 varian terbaik untuk pemula", 1),
        ("Cuma 1 produk ya", 1),
        ("Beri saya 2 rekomendasi tembakau rasa kopi atau buah", 2),
        ("Kasih dua varian kretek", 2),
        ("Kasih 3 varian dingin ice menthol", 3),
        ("Minta 4 rekomendasi tembakau", 4),
        ("Ada rekomendasi tembakau mild pemula?", None),
        ("Berapa sisa stok Linting Surya kirim ke WA 083132001855", None),
        ("SOP penyimpanan RH 65-70% dan garansi retur 2x24 jam", None)
    ]

    for query, expected in test_cases:
        res = _extract_requested_count(query)
        print(f"  • Query: \"{query[:45]}...\" -> Extracted: {res} (Expected: {expected})")
        assert res == expected, f"Failed on '{query}': got {res}, expected {expected}"
    print("  >>> Stage 1: All extractor unit tests PASSED (12/12)!")

    # -------------------------------------------------------------
    # 2. TEST DETERMINISTIC FALLBACK AGENT CARDINALITY
    # -------------------------------------------------------------
    print("\n[Stage 2/3] Testing Deterministic Fallback Engine Cardinality")
    init_db()

    with SessionLocal() as db:
        # Case A: 1 Recommendation Request
        print("  • Testing 1 Recommendation ('Pilihin satu varian tembakau manis')...")
        out_single = _execute_deterministic_agent(
            db, 
            user_message="Pilihin satu varian tembakau manis", 
            chunks=[], 
            citations=[]
        )
        ans_single = out_single["answer"]
        tools_single = [t["tool"] for t in out_single["executed_tools"]]
        prod_count_single = count_product_mentions(ans_single)
        print(f"    Products recommended: {prod_count_single} | Stock check tools: {tools_single.count('check_inventory_stock')}")
        assert prod_count_single == 1, f"Expected 1 product, found {prod_count_single} in answer."
        assert tools_single.count("check_inventory_stock") == 1, "Expected exactly 1 stock check tool call."
        assert "**Linting Melon Ice**" in ans_single, "Expected featured single card for Melon Ice."

        # Case B: 2 Recommendations Request
        print("  • Testing 2 Recommendations ('Beri saya 2 rekomendasi kretek')...")
        out_two = _execute_deterministic_agent(
            db, 
            user_message="Beri saya 2 rekomendasi tembakau kretek", 
            chunks=[], 
            citations=[]
        )
        ans_two = out_two["answer"]
        tools_two = [t["tool"] for t in out_two["executed_tools"]]
        prod_count_two = count_product_mentions(ans_two)
        print(f"    Products recommended: {prod_count_two} | Stock check tools: {tools_two.count('check_inventory_stock')}")
        assert prod_count_two == 2, f"Expected 2 products, found {prod_count_two} in answer."
        assert "1. **Linting Surya**" in ans_two and "2. **Linting Samsu**" in ans_two, "Expected Surya and Samsu."

        # Case C: 3 Recommendations Request
        print("  • Testing 3 Recommendations ('Kasih 3 varian dingin ice menthol')...")
        out_three = _execute_deterministic_agent(
            db, 
            user_message="Kasih 3 varian dingin ice menthol", 
            chunks=[], 
            citations=[]
        )
        ans_three = out_three["answer"]
        prod_count_three = count_product_mentions(ans_three)
        print(f"    Products recommended: {prod_count_three}")
        assert prod_count_three == 3, f"Expected 3 products, found {prod_count_three} in answer."

        # Case D: Unspecified count -> Default to top 2-3
        print("  • Testing Unspecified Count ('Rekomendasi tembakau untuk pemula')...")
        out_default = _execute_deterministic_agent(
            db, 
            user_message="Rekomendasi tembakau untuk pemula", 
            chunks=[], 
            citations=[]
        )
        ans_default = out_default["answer"]
        prod_count_default = count_product_mentions(ans_default)
        print(f"    Products recommended: {prod_count_default}")
        assert 2 <= prod_count_default <= 3, f"Expected 2-3 products, found {prod_count_default}."

    print("  >>> Stage 2: Deterministic engine cardinality PASSED (4/4)!")

    # -------------------------------------------------------------
    # 3. TEST END-TO-END AGENT (ACTIVE PROVIDER / GEMINI)
    # -------------------------------------------------------------
    print("\n[Stage 3/3] Testing End-to-End Agent with Prompt Alignment")
    with SessionLocal() as db:
        query_e2e_1 = "Rekomendasikan 1 tembakau manis yang paling enak dan cek stoknya"
        print(f"  • Sending Query: \"{query_e2e_1}\"")
        out_e2e = run_agent_turn(db, user_message=query_e2e_1)
        print(f"    Provider: {out_e2e.get('provider')}")
        print(f"    Tools Executed: {[t['tool'] for t in out_e2e['executed_tools']]}")
        print("    Answer Preview:")
        preview_lines = out_e2e["answer"].strip().split("\n")[:8]
        for line in preview_lines:
            print(f"      {line}")
        
        prod_mentions = count_product_mentions(out_e2e["answer"])
        print(f"    Official products cited: {prod_mentions}")
        # When 1 is requested, it must be exactly 1
        assert prod_mentions == 1, f"Expected exactly 1 product cited, found {prod_mentions}."
        print("    >>> Exactly 1 product verified!")

        query_e2e_2 = "Kasih 2 rekomendasi tembakau kretek yang mantap"
        print(f"\n  • Sending Query: \"{query_e2e_2}\"")
        out_e2e_2 = run_agent_turn(db, user_message=query_e2e_2)
        print(f"    Provider: {out_e2e_2.get('provider')}")
        print(f"    Tools Executed: {[t['tool'] for t in out_e2e_2['executed_tools']]}")
        print("    Answer Preview:")
        preview_lines2 = out_e2e_2["answer"].strip().split("\n")[:8]
        for line in preview_lines2:
            print(f"      {line}")
        prod_mentions_2 = count_product_mentions(out_e2e_2["answer"])
        print(f"    Official products cited: {prod_mentions_2}")
        assert prod_mentions_2 == 2, f"Expected exactly 2 products cited, got {prod_mentions_2}."
        print("    >>> Exactly 2 products verified!")

    print("\n" + "=" * 70)
    print("ALL RECOMMENDATION CARDINALITY TESTS PASSED 100%!")
    print("=" * 70)

if __name__ == "__main__":
    run_cardinality_tests()
