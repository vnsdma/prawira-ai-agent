# 🍃 Enterprise Document Intelligence & WhatsApp Action Agent
### *Prawira Tobacco Enterprise Operations Edition*

[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-black?style=flat&logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20pgvector-336791?style=flat&logo=postgresql)](https://github.com/pgvector/pgvector)
[![Supabase](https://img.shields.io/badge/Cloud%20Catalog-Supabase-3ECF8E?style=flat&logo=supabase)](https://supabase.com/)
[![Gemini](https://img.shields.io/badge/AI%20Agent-Google%20Gemini-4285F4?style=flat&logo=google)](https://ai.google.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC?style=flat&logo=tailwind-css)](https://tailwindcss.com/)

---

## 📌 1. Gambaran Sistem (System Overview)

**Prawira Tobacco Enterprise Agent** adalah platform asisten kecerdasan buatan (*AI Agent*) terintegrasi yang dirancang khusus untuk operasional retail spesialis tembakau linting artisan (**Prawira Tobacco**). Sistem ini menghubungkan tiga pilar operasional utama toko:

1. **Document Intelligence & Grounded RAG**:
   - Membaca, membagi secara semantik (*chunking*), dan mengindeks dokumen resmi PDF toko (`SOP_Penyimpanan_dan_Garansi_Prawira.pdf` dan `Katalog_Varian_Prawira_Tobacco.pdf`).
   - Menyimpan representasi vektor berdimensi tinggi ke **PostgreSQL `pgvector`** dengan indeks *HNSW cosine distance*.
   - Menyediakan sitasi transparan (nama dokumen dan nomor halaman persis) dengan ambang batas kesesuaian (*cosine threshold* 0.45) guna mencegah halusinasi.

2. **Pengecekan Stok Gudang Real-Time (`check_inventory_stock`)**:
   - Secara otonom mengeksekusi *function calling* langsung ke basis data live cloud **Supabase** (`mitkblmftejogdxmewet.supabase.co`) dengan fallback lokal.
   - Mengembalikan data SKU resmi, nama produk, status ketersediaan, kuantitas stok fisik, harga terkini, dan posisi rak gudang.

3. **Otomasi Tindakan WhatsApp Gateway (`send_whatsapp_action`)**:
   - Menghubungkan konsultasi pelanggan dan pembuatan ringkasan pesanan ke WhatsApp Gateway resmi (**Fonnte API**) langsung ke nomor operasional toko (`083132001855`).
   - Menyediakan tautan aksi instan `https://wa.me/6283132001855?text=...` untuk tindak lanjut pesanan satu klik.

---

## 🏗️ 2. Arsitektur Sistem (System Architecture)

```text
[ Pelanggan & Staf Toko ]
          │
          ▼
[ Frontend: Next.js 15 + React 19 (Port 3000) ]
   ├── Asisten AI Prawira (Chat Studio, Quick Action Chips, Sitasi RAG)
   ├── Katalog Supabase (24 Varian Resmi, Peta Rasa, Filter Kategori)
   └── Pusat SOP & Dokumen (Unggah PDF & Inspeksi Vektor Chunks)
          │
          │ (REST API via /api/chat, /api/products, /api/documents)
          ▼
[ Backend: Python FastAPI (Port 8000) ]
   ├── RAG Vector Engine (pypdf + Recursive Chunker + Gemini Embeddings)
   ├── Agent Orchestrator (Google Gemini 2.5 Flash / Hybrid Fallback)
   └── Autonomous Tool Calling:
         ├── Tool 1: check_inventory_stock (Query tabel products di Supabase / Postgres)
         └── Tool 2: send_whatsapp_action (Fonnte Gateway API / wa.me action URLs)
          │
          ▼
[ Basis Data & Penyimpanan Terpadu ]
   ├── PostgreSQL 16 + pgvector (Tabel: document_chunks & products)
   └── Supabase Cloud (Live Source of Truth 24 SKU Prawira Tobacco)
```

---

## 🛡️ 3. Aturan Ketat Anti-Halusinasi & Konsultasi Rasa

Sistem dirancang dengan protokol integritas data yang kokoh:
* **Larangan Halusinasi Produk**: AI dilarang keras mengarang merek atau nama varian tembakau fiktif. Seluruh rekomendasi produk bersumber eksklusif dari 24 produk resmi yang tersinkronisasi di Supabase toko.
* **Penolakan Pertanyaan di Luar Konteks**: Jika pengguna menanyakan hal yang tidak berhubungan dengan tembakau, aksesoris, atau SOP toko (seperti tiket pesawat, saham, atau topik umum), asisten menolak secara sopan dan menjelaskan batas layanannya.
* **Edukasi Tembakau Linting**: Untuk pertanyaan mengenai rokok batangan pabrikan umum (misal: Marlboro, Djarum Super, Sampoerna Mild), AI menjelaskan bahwa Prawira Tobacco khusus melayani tembakau linting artisan (*tingwe*) dan memberikan rekomendasi padanan profil rasa resmi kami (misal: Marlboro &rarr; Linting Marlong; Djarum Super &rarr; Linting Surya / Magnum Premium).

---

## 🚀 4. Panduan Menjalankan Sistem (Quick Start)

### Prasyarat
- Python 3.10+
- Node.js 18+ (disarankan Node 20+)
- Akun Google Gemini API (atau OpenAI)

---

### Langkah A: Menjalankan Backend (FastAPI)

1. Buka terminal dan masuk ke folder `backend`:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Konfigurasi file `.env` di direktori root (pastikan `GEMINI_API_KEY`, `SUPABASE_URL`, dan `STORE_DEFAULT_PHONE=6283132001855` sudah terisi).

3. Jalankan server FastAPI:
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```
   *Backend secara otomatis menjalankan auto-seeding ke SQLite lokal (`prawira_dev.db`) jika PostgreSQL eksternal belum aktif.*

4. Jalankan pengujian pipeline backend untuk memastikan seluruh modul berjalan optimal:
   ```bash
   python test_pipeline.py
   ```

---

### Langkah B: Menjalankan Frontend (Next.js 15)

1. Buka terminal baru dan masuk ke folder `frontend`:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. Buka browser di [http://localhost:3000](http://localhost:3000).

---

## 📁 5. Struktur Berkas Repositori

```text
prawira-enterprise/
├── README.md                          # Dokumentasi resmi sistem
├── product.md                         # Spesifikasi produk & aturan bisnis
├── DESIGN.md                          # Spesifikasi desain UI/UX Pro Max
├── docker-compose.yml                 # Konfigurasi PostgreSQL 16 + pgvector lokal
├── .env                               # Konfigurasi environment (LLM, Supabase, WhatsApp)
│
├── backend/                           # Layanan API & Otomasi AI (FastAPI)
│   ├── main.py                        # Endpoint REST API (/api/chat, /api/products, dll)
│   ├── config.py                      # Pydantic Settings & pembaca konfigurasi
│   ├── database.py                    # Koneksi SQLAlchemy & definisi model data
│   ├── rag_engine.py                  # Parser PDF, recursive chunking, & vector search
│   ├── agent_tools.py                 # Definisi fungsi check_inventory_stock & send_whatsapp_action
│   ├── agent_orchestrator.py          # Decision engine: Gemini tool calling & smart fallback
│   ├── sync_supabase.py               # Modul sinkronisasi katalog langsung dari Supabase
│   ├── test_pipeline.py               # Unit & integration test otomatis (5/5 lulus)
│   └── test_recommendation_cardinality.py # Pengujian kepatuhan jumlah rekomendasi (1 vs N produk)
│
├── frontend/                          # Antarmuka Dashboard (Next.js 15 App Router)
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx               # Halaman utama (Command bar & navigasi tab)
│   │   │   ├── layout.tsx             # Root layout & konfigurasi metadata
│   │   │   └── globals.css            # Styling Obsidian Liquid Glass & font tokens
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx      # Antarmuka obrolan AI, pintasan konsultasi, & sitasi
│   │   │   ├── CatalogBrowser.tsx     # Browser 24 varian produk Supabase & filter rasa
│   │   │   ├── DocumentManager.tsx    # Manajemen arsip PDF SOP & inspeksi chunks
│   │   │   └── ToolCard.tsx           # Kartu interaktif hasil stok & aksi WhatsApp
│   │   └── lib/
│   │       └── api.ts                 # Klien fetcher REST API ke backend
│   └── tailwind.config.ts
│
└── sample_documents/                  # Berkas dokumen resmi toko
    ├── SOP_Penyimpanan_dan_Garansi_Prawira.pdf
    └── Katalog_Varian_Prawira_Tobacco.pdf
```

---

## 📲 6. Integrasi WhatsApp Gateway & Kontak Toko

- **Target Hotline Resmi:** `+62 831-3200-1855` (`083132001855`)
- **Gateway Provider:** Fonnte WhatsApp API (`https://api.fonnte.com/send`) dengan fallback otomatis ke tautan instan `https://wa.me/6283132001855?text=...`.
- **Format Pesan:** Pesan disusun secara terstruktur memuat nama produk, varian, SKU, harga resmi, dan salam penutup representatif dari Prawira Tobacco.
