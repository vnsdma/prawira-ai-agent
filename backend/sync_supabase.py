import os
import sys
import httpx
import logging
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from config import settings
from database import init_db, SessionLocal, Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync_supabase")

def sync_products_from_supabase():
    """
    Fetches live catalog and inventory from Prawira Tobacco Supabase database
    and synchronizes it into the local database (PostgreSQL / SQLite).
    """
    supabase_url = settings.SUPABASE_URL or os.getenv("SUPABASE_URL", "https://mitkblmftejogdxmewet.supabase.co")
    supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    if not supabase_key:
        logger.error("SUPABASE_SERVICE_ROLE_KEY is required in .env for syncing.")
        return False

    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/products?select=*"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}"
    }

    logger.info(f"Connecting to live Prawira Tobacco Supabase: {supabase_url}...")
    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.get(endpoint, headers=headers)
            if res.status_code != 200:
                logger.error(f"Failed to fetch products from Supabase: {res.status_code} {res.text}")
                return False
            
            supabase_products = res.json()
            logger.info(f"Retrieved {len(supabase_products)} live products from Supabase.")

        synced_count = 0

        with SessionLocal() as db:
            for sp in supabase_products:
                prod_id = sp.get("id")
                name = sp.get("name", "").strip()
                if not name:
                    continue

                sku = f"PT-{prod_id:04d}" if prod_id else f"PT-{name[:4].upper()}"
                category = sp.get("category") or "tobacco"
                price = float(sp.get("price") or 0.0)
                stock = int(sp.get("in_stock") or 0)
                desc = sp.get("description") or f"Varian resmi Prawira Tobacco: {name}"
                weight = int(sp.get("weight") or 100) if sp.get("weight") else 100

                # Check if product exists by name or SKU
                existing = db.query(Product).filter(
                    (Product.name == name) | (Product.sku == sku)
                ).first()

                if existing:
                    existing.stock = stock
                    existing.price = price
                    existing.description = desc
                    existing.weight_grams = weight
                    existing.category = category
                else:
                    new_prod = Product(
                        sku=sku,
                        name=name,
                        category=category,
                        similarity_grade="premium",
                        stock=stock,
                        unit="pack",
                        weight_grams=weight,
                        price=price,
                        shelf_location="Gudang Utama",
                        description=desc
                    )
                    db.add(new_prod)
                synced_count += 1

            db.commit()

        logger.info(f"SUCCESS: Synchronized {synced_count} products from Prawira Tobacco Supabase into agent database!")
        return True
    except Exception as e:
        logger.error(f"Error during Supabase synchronization: {e}")
        return False

if __name__ == "__main__":
    sync_products_from_supabase()
