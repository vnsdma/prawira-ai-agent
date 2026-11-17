# UI/UX Pro Max Design System & Craft Specification
### *Prawira Tobacco Enterprise Operations Edition*

## 1. Visual World & Aesthetic Identity
- **Style Archetype:** **Liquid Glass + Obsidian Luxury Boutique**
  - Tailored specifically for an artisan tobacco enterprise atelier (`Prawira Tobacco`).
  - Dark luxury depth with optical glass layering, frosted reflections, and warm amber accents.
- **Palette Mood:**
  - **Canvas Base:** Deep Obsidian Void (`#080a0f`)
  - **Glass Surfaces:** Frosted Liquid Glass (`rgba(14, 18, 26, 0.75)` with `backdrop-filter: blur(16px)`)
  - **Elevated Cards:** Obsidian Surface (`rgba(20, 25, 36, 0.65)` with `border-white/[0.07]`)
  - **Tobacco Cured Accent:** Amber-500 (`#f59e0b`) & Dark Cured Amber-600 (`#d97706`) for primary interactive states.
  - **Verification & Live Signals:** Emerald-500 (`#10b981`) for live Supabase sync, in-stock counters, and WhatsApp Gateway actions.
  - **High-Contrast Text Floor:** Slate-50 (`#f8fafc`) for headers, Slate-200 (`#e2e8f0`) for body, Slate-400 (`#94a3b8`) for secondary tags (WCAG AA ≥ 4.5:1 ratio).

## 2. Typography System (Triple Stack)
- **Brand & Display:** `Playfair Display` (High-elegance luxury serif for titles, brand crest, and key metric numbers).
- **Interface & Readability:** `Plus Jakarta Sans` (Contemporary, clean, geometric sans-serif for comfortable multi-turn conversation and dense tables).
- **Technical & Deterministic:** `JetBrains Mono` (Reserved exclusively for SKUs, pricing numbers, vector embeddings, similarity percentages, timestamps, and phone numbers).
- **Legibility Floor:** All functional labels are strictly ≥11px. No unreadable micro-typography.

## 3. Core Interface Views
1. **Asisten AI Prawira (`ChatInterface.tsx`):**
   - Multi-turn conversation stream with Google Gemini / OpenAI orchestrator.
   - Frequent Consultation Prompt Chips (One-click inquiries for SOP Kelembaban, Garansi Retur, Rekomendasi Mild/Manis, and WhatsApp dispatch).
   - Real-time tool execution cards with rich interactive layouts:
     - `check_inventory_stock`: SKU, stock count, formatted price (IDR), status badge, and warehouse shelf.
     - `send_whatsapp_action`: WhatsApp Fonnte Gateway delivery pill, recipient `+6283132001855`, payload preview, and one-click `wa.me` launch button.
   - Expandable Verified Citations accordion with exact document name, page badge, and cosine similarity progress meter.
2. **Katalog & Stok Live (`CatalogBrowser.tsx`):**
   - Direct synchronization with live Supabase database (`mitkblmftejogdxmewet.supabase.co`).
   - 24 verified products organized across 5 flavor taxonomy profiles:
     - *Manis, Buah & Kopi* (Melon Ice, Strawberry, Cappucino, Purple Ice, Coklat Ice)
     - *Gurih Mantap (Kretek)* (Surya, Samsu, Marlong, GGF, Magnum, Sampurna)
     - *Dingin / Ice Menthol* (Barrack Whiskey Ice, Melon Ice, Purple Ice Burst)
     - *Mild & Halus (Pemula)* (Linting Mild, Barrack Soju, Bayote, Melisa)
     - *Aksesoris & Perlengkapan* (Papir, Busa Filter, Cengkeh, Lem)
   - Real-time search, live stock gauges, and one-click "Tanya AI" or "Pesan WA" triggers.
3. **Pusat SOP & Dokumen (`DocumentManager.tsx`):**
   - Ingestion and chunk inspection for `SOP_Penyimpanan_dan_Garansi_Prawira.pdf` and `Katalog_Varian_Prawira_Tobacco.pdf`.
   - Vector chunk inspector showing token counts, page numbers, and cosine similarity tester.
   - Drag & drop PDF uploader with real-time feedback.

## 4. Anti-Slop & Quality Enforcement
- **0 Anti-patterns:**
  - ❌ No generic glowing purple-pink AI halos.
  - ❌ No ungrounded placeholder text or fake dummy products.
  - ❌ No layout-shifting hover scales.
  - ❌ No missing cursor-pointer on clickable elements.
  - ❌ No emojis used as functional icons (100% Lucide SVG icons).
