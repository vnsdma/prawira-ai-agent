import urllib.parse
import logging
import httpx
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from config import settings
from database import Product

logger = logging.getLogger("prawira_agent.tools")

def check_inventory_stock(db: Session, search_term: str, category: Optional[str] = None) -> Dict[str, Any]:
    """
    Queries the Prawira Tobacco products table for real-time stock, pricing, and shelf location.
    Prioritizes live Supabase cloud database if configured, with automatic fallback to local DB.
    """
    # 1. Prioritize Live Supabase Cloud Query
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        try:
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"
            }
            url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/products"
            params = {
                "select": "*",
                "name": f"ilike.*{search_term}*",
                "limit": "5"
            }
            with httpx.Client(timeout=4.0) as client:
                res = client.get(url, headers=headers, params=params)
                if res.status_code == 200:
                    data = res.json()
                    if data:
                        items = []
                        for p in data:
                            stock_val = p.get("in_stock", 0) or 0
                            price_val = float(p.get("price", 0) or 0)
                            items.append({
                                "sku": f"PT-{p.get('id', 0):04d}",
                                "name": p.get("name"),
                                "category": p.get("category", "tobacco"),
                                "similarity_grade": "premium",
                                "stock": stock_val,
                                "unit": "pack",
                                "weight_grams": p.get("weight") or 100,
                                "price": price_val,
                                "formatted_price": f"Rp {int(price_val):,}".replace(",", "."),
                                "shelf_location": "Gudang Prawira (Live Supabase)",
                                "in_stock": stock_val > 0,
                                "status": "Tersedia" if stock_val > 0 else "Stok Habis"
                            })
                        return {
                            "found": True,
                            "count": len(items),
                            "source": "Live Supabase Cloud",
                            "message": f"Ditemukan {len(items)} produk cocok di live database Supabase Prawira Tobacco.",
                            "items": items
                        }
        except Exception as se:
            logger.debug(f"Live Supabase query failed: {se}. Falling back to local database.")

    # 2. Local Database Query Fallback
    try:
        query = db.query(Product).filter(
            or_(
                Product.name.ilike(f"%{search_term}%"),
                Product.sku.ilike(f"%{search_term}%"),
                Product.description.ilike(f"%{search_term}%")
            )
        )
        if category and category.lower() != "all":
            query = query.filter(Product.category.ilike(f"%{category}%"))

        products = query.limit(5).all()

        if not products:
            return {
                "found": False,
                "count": 0,
                "message": f"Tidak ditemukan produk dengan kata kunci '{search_term}' di database gudang.",
                "items": []
            }

        items = []
        for p in products:
            items.append({
                "sku": p.sku,
                "name": p.name,
                "category": p.category,
                "similarity_grade": p.similarity_grade,
                "stock": p.stock,
                "unit": p.unit,
                "weight_grams": p.weight_grams,
                "price": float(p.price),
                "formatted_price": f"Rp {int(p.price):,}".replace(",", "."),
                "shelf_location": p.shelf_location or "Belum dialokasikan",
                "in_stock": p.stock > 0,
                "status": "Tersedia" if p.stock > 0 else "Stok Habis"
            })

        return {
            "found": True,
            "count": len(items),
            "message": f"Ditemukan {len(items)} produk cocok di database gudang.",
            "items": items
        }
    except Exception as e:
        logger.error(f"Error checking inventory: {e}")
        return {
            "found": False,
            "count": 0,
            "error": str(e),
            "message": "Gagal membaca database stok barang."
        }

def send_whatsapp_action(phone_number: str, message_body: str, action_title: str = "Prawira Tobacco") -> Dict[str, Any]:
    """
    Dispatches a WhatsApp message via Fonnte Gateway or generates an instant click-to-chat link.
    """
    # Clean digits
    clean_phone = "".join(filter(str.isdigit, phone_number))
    if clean_phone.startswith("08"):
        clean_phone = "62" + clean_phone[1:]
    elif not clean_phone.startswith("62") and len(clean_phone) > 8:
        clean_phone = "62" + clean_phone

    if not clean_phone:
        clean_phone = settings.STORE_DEFAULT_PHONE

    encoded_msg = urllib.parse.quote_plus(message_body)
    direct_link = f"https://wa.me/{clean_phone}?text={encoded_msg}"

    # Check if Fonnte Token is configured
    if settings.FONNTE_TOKEN:
        try:
            headers = {"Authorization": settings.FONNTE_TOKEN}
            payload = {
                "target": clean_phone,
                "message": message_body,
                "countryCode": "62"
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post("https://api.fonnte.com/send", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "success": True,
                        "mode": "gateway",
                        "provider": "Fonnte API",
                        "target_phone": clean_phone,
                        "action_title": action_title,
                        "message_preview": message_body,
                        "direct_url": direct_link,
                        "status_text": f"Pesan terkirim via WhatsApp Gateway ke {clean_phone}."
                    }
        except Exception as e:
            logger.warning(f"WhatsApp Gateway failed: {e}. Falling back to direct wa.me link.")

    # Fallback to direct link
    return {
        "success": True,
        "mode": "direct_link",
        "provider": "WhatsApp Web / Direct Link",
        "target_phone": clean_phone,
        "action_title": action_title,
        "message_preview": message_body,
        "direct_url": direct_link,
        "status_text": f"Tautan WhatsApp langsung dibuat untuk nomor {clean_phone}."
    }

# Tool Definitions for Agent Function Calling
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "check_inventory_stock",
            "description": "Periksa ketersediaan stok fisik, harga, varian, dan lokasi rak produk di gudang Prawira Tobacco secara real-time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Nama produk, varian tembakau, atau aksesoris yang dicari (contoh: 'Djarum Super', 'Marlboro', 'Papir Gizeh', 'Filter')."
                    },
                    "category": {
                        "type": "string",
                        "enum": ["all", "tembakau_kretek", "tembakau_mild", "tembakau_dingin", "aksesoris_papir", "aksesoris_filter", "aksesoris_alat"],
                        "description": "Kategori produk untuk mempersempit pencarian (opsional)."
                    }
                },
                "required": ["search_term"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp_action",
            "description": "Kirimkan ringkasan informasi, hasil pengecekan stok, atau rekomendasi racikan tembakau ke nomor WhatsApp pelanggan atau staf.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "Nomor tujuan WhatsApp (format Indonesia, contoh: '083132001855' atau '6283132001855')."
                    },
                    "message_body": {
                        "type": "string",
                        "description": "Isi pesan lengkap dan rapi yang akan dikirim via WhatsApp."
                    },
                    "action_title": {
                        "type": "string",
                        "description": "Judul singkat aksi (contoh: 'Ringkasan Cek Stok Gudang' atau 'Rekomendasi Varian Tembakau')."
                    }
                },
                "required": ["phone_number", "message_body"]
            }
        }
    }
]
