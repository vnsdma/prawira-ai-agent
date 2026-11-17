"use client";

import React, { useState, useEffect } from "react";
import { ProductItem, fetchProducts, syncSupabase } from "@/lib/api";
import { 
  Package, 
  Search, 
  RefreshCw, 
  ExternalLink, 
  Sparkles, 
  MessageSquare, 
  CheckCircle2, 
  Flame, 
  IceCream, 
  Coffee, 
  Wind, 
  Layers, 
  ShieldCheck,
  AlertCircle,
  Tag,
  MapPin,
  ArrowRight
} from "lucide-react";

interface CatalogBrowserProps {
  onAskAgent: (prompt: string) => void;
}

type FlavorFilter = "all" | "sweet" | "kretek" | "ice" | "mild" | "accessories";

export const CatalogBrowser: React.FC<CatalogBrowserProps> = ({ onAskAgent }) => {
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeFilter, setActiveFilter] = useState<FlavorFilter>("all");
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await fetchProducts();
      setProducts(res.products || []);
    } catch (err) {
      console.error("Error loading products:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSync = async () => {
    try {
      setSyncing(true);
      const res = await syncSupabase();
      setSyncMessage(res.message);
      await loadData();
      setTimeout(() => setSyncMessage(null), 4000);
    } catch (err: any) {
      setSyncMessage("Gagal menyinkronkan data dengan Supabase.");
      setTimeout(() => setSyncMessage(null), 4000);
    } finally {
      setSyncing(false);
    }
  };

  // Filter categorization based on official Prawira Tobacco Taxonomy
  const filteredProducts = products.filter((p) => {
    const textMatch = 
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchTerm.toLowerCase()));

    if (!textMatch) return false;

    const lowerName = p.name.toLowerCase();
    const lowerCat = p.category.toLowerCase();

    if (activeFilter === "sweet") {
      return (
        lowerName.includes("melon") ||
        lowerName.includes("strawberry") ||
        lowerName.includes("cappucino") ||
        lowerName.includes("purple") ||
        lowerName.includes("coklat")
      );
    }
    if (activeFilter === "kretek") {
      return (
        lowerName.includes("surya") ||
        lowerName.includes("samsu") ||
        lowerName.includes("marlong") ||
        lowerName.includes("ggf") ||
        lowerName.includes("magnum") ||
        lowerName.includes("sampurna")
      );
    }
    if (activeFilter === "ice") {
      return (
        lowerName.includes("ice") ||
        lowerName.includes("burst") ||
        lowerName.includes("whiskey ice")
      );
    }
    if (activeFilter === "mild") {
      return (
        lowerName.includes("mild") ||
        lowerName.includes("soju") ||
        lowerName.includes("bayote") ||
        lowerName.includes("melisa")
      );
    }
    if (activeFilter === "accessories") {
      return (
        lowerCat.includes("aksesoris") ||
        lowerName.includes("papir") ||
        lowerName.includes("busa") ||
        lowerName.includes("cengkeh") ||
        lowerName.includes("lem")
      );
    }

    return true;
  });

  const totalStockCount = products.reduce((acc, curr) => acc + (curr.stock || 0), 0);
  const inStockCount = products.filter((p) => (p.stock || 0) > 0).length;

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto px-4 sm:px-8 py-6 space-y-6">
      {/* Header Banner & Telemetry */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-white/[0.08]">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-amber-400">
              Katalog Resmi Terverifikasi
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/70 text-emerald-300 border border-emerald-800/60 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Live Supabase Cloud
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-slate-100 tracking-tight">
            Prawira Tobacco Atelier Inventory
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Basis data inventaris resmi toko spesialis tembakau linting artisan. Menampilkan 24 produk terverifikasi dengan stok fisik dan harga *real-time* yang disinkronkan ke Supabase.
          </p>
        </div>

        {/* Sync Action & Metrics */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/40 font-semibold text-xs transition-all shadow-sm active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? "animate-spin text-amber-400" : ""}`} />
            <span>{syncing ? "Menyinkronkan..." : "Sync Supabase"}</span>
          </button>
        </div>
      </div>

      {/* Sync Alert if Any */}
      {syncMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-950/70 border border-emerald-700/60 text-emerald-200 text-xs flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{syncMessage}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <div className="glass-card rounded-2xl p-4">
          <div className="text-[11px] font-mono uppercase text-slate-400">Total Varian Resmi</div>
          <div className="text-2xl font-bold font-serif text-slate-100 mt-1">{products.length || 24} SKU</div>
          <div className="text-[11px] text-amber-400/80 mt-1">100% Anti-Halusinasi</div>
        </div>

        <div className="glass-card rounded-2xl p-4">
          <div className="text-[11px] font-mono uppercase text-slate-400">Ketersediaan Stok</div>
          <div className="text-2xl font-bold font-serif text-emerald-300 mt-1">{inStockCount} / {products.length}</div>
          <div className="text-[11px] text-slate-400 mt-1">{totalStockCount.toLocaleString()} total unit fisik</div>
        </div>

        <div className="glass-card rounded-2xl p-4">
          <div className="text-[11px] font-mono uppercase text-slate-400">Peta Rasa (Taxonomy)</div>
          <div className="text-2xl font-bold font-serif text-amber-200 mt-1">5 Profil</div>
          <div className="text-[11px] text-slate-400 mt-1">Manis, Kretek, Dingin, Mild, Aksesoris</div>
        </div>

        <div className="glass-card rounded-2xl p-4">
          <div className="text-[11px] font-mono uppercase text-slate-400">Hotline Pemesanan</div>
          <div className="text-base sm:text-lg font-mono font-bold text-emerald-400 mt-1.5 flex items-center gap-1.5">
            <span>0831-3200-1855</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Fonnte API Gateway Aktif</div>
        </div>
      </div>

      {/* Search & Flavor Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pt-2">
        {/* Search Bar */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Cari varian rasa, nama produk, atau SKU (contoh: Surya, Melon, Papir)..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#10141e] border border-white/[0.08] text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-all"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-500 hover:text-slate-300"
            >
              ✕
            </button>
          )}
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          <button
            onClick={() => setActiveFilter("all")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium shrink-0 transition-all ${
              activeFilter === "all"
                ? "bg-amber-600 text-slate-950 font-semibold shadow-md"
                : "bg-white/[0.04] text-slate-300 hover:bg-white/[0.08]"
            }`}
          >
            Semua ({products.length})
          </button>

          <button
            onClick={() => setActiveFilter("sweet")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium shrink-0 transition-all ${
              activeFilter === "sweet"
                ? "bg-amber-600 text-slate-950 font-semibold shadow-md"
                : "bg-white/[0.04] text-slate-300 hover:bg-white/[0.08]"
            }`}
          >
            <IceCream className="w-3.5 h-3.5" />
            <span>Manis & Kopi</span>
          </button>

          <button
            onClick={() => setActiveFilter("kretek")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium shrink-0 transition-all ${
              activeFilter === "kretek"
                ? "bg-amber-600 text-slate-950 font-semibold shadow-md"
                : "bg-white/[0.04] text-slate-300 hover:bg-white/[0.08]"
            }`}
          >
            <Flame className="w-3.5 h-3.5 text-amber-400" />
            <span>Kretek Mantap</span>
          </button>

          <button
            onClick={() => setActiveFilter("ice")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium shrink-0 transition-all ${
              activeFilter === "ice"
                ? "bg-amber-600 text-slate-950 font-semibold shadow-md"
                : "bg-white/[0.04] text-slate-300 hover:bg-white/[0.08]"
            }`}
          >
            <Wind className="w-3.5 h-3.5 text-cyan-400" />
            <span>Ice Menthol</span>
          </button>

          <button
            onClick={() => setActiveFilter("mild")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium shrink-0 transition-all ${
              activeFilter === "mild"
                ? "bg-amber-600 text-slate-950 font-semibold shadow-md"
                : "bg-white/[0.04] text-slate-300 hover:bg-white/[0.08]"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>Mild Pemula</span>
          </button>

          <button
            onClick={() => setActiveFilter("accessories")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium shrink-0 transition-all ${
              activeFilter === "accessories"
                ? "bg-amber-600 text-slate-950 font-semibold shadow-md"
                : "bg-white/[0.04] text-slate-300 hover:bg-white/[0.08]"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Aksesoris</span>
          </button>
        </div>
      </div>

      {/* Product Grid */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="w-8 h-8 text-amber-500 animate-spin" />
          <p className="text-xs text-slate-400 font-mono">Memuat inventaris dari database Supabase...</p>
        </div>
      ) : filteredProducts.length === 0 ? (
        <div className="py-16 text-center rounded-2xl glass-panel p-8">
          <AlertCircle className="w-10 h-10 text-amber-500/80 mx-auto mb-3" />
          <h3 className="font-semibold text-slate-200 text-sm">Tidak ada produk yang cocok</h3>
          <p className="text-xs text-slate-400 mt-1">Coba gunakan kata kunci lain atau ubah filter kategori di atas.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProducts.map((p) => {
            const inStock = (p.stock || 0) > 0;
            return (
              <div 
                key={p.id}
                className="glass-card rounded-2xl p-5 flex flex-col justify-between group"
              >
                <div>
                  {/* Top Bar: SKU and Status Badge */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-white/[0.06] text-amber-300 font-medium border border-white/[0.08]">
                      {p.sku}
                    </span>
                    <span className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded-full flex items-center gap-1 ${
                      inStock 
                        ? "bg-emerald-950/70 text-emerald-300 border border-emerald-800/60" 
                        : "bg-red-950/70 text-red-300 border border-red-800/60"
                    }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${inStock ? "bg-emerald-400" : "bg-red-400"}`}></span>
                      {inStock ? `${p.stock} ${p.unit || "pack"} Tersedia` : "Stok Habis"}
                    </span>
                  </div>

                  {/* Title & Category */}
                  <h3 className="text-base font-serif font-bold text-slate-100 group-hover:text-amber-200 transition-colors">
                    {p.name}
                  </h3>
                  <div className="text-[11px] text-amber-400/90 font-medium mt-0.5 capitalize">
                    {p.category?.replace("_", " ")}
                  </div>

                  {/* Description / Tasting Notes */}
                  <p className="text-xs text-slate-300 mt-2.5 line-clamp-3 leading-relaxed">
                    {p.description || "Tembakau linting resmi Prawira Tobacco dengan cita rasa dan aroma terjamin kualitasnya."}
                  </p>
                </div>

                {/* Footer Section: Price & Action Buttons */}
                <div className="pt-4 mt-4 border-t border-white/[0.06] space-y-3">
                  <div className="flex items-baseline justify-between">
                    <span className="text-[11px] text-slate-400">Harga Satuan:</span>
                    <span className="text-lg font-bold font-serif text-slate-100">
                      Rp {p.price ? Number(p.price).toLocaleString("id-ID") : "0"}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => onAskAgent(`Bagaimana karakteristik rasa dan ketersediaan stok untuk produk ${p.name}?`)}
                      className="px-3 py-2 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 text-xs font-medium flex items-center justify-center gap-1.5 transition-all"
                    >
                      <MessageSquare className="w-3.5 h-3.5 text-amber-400" />
                      <span>Tanya AI</span>
                    </button>

                    <a
                      href={`https://wa.me/6283132001855?text=Halo%20Prawira%20Tobacco,%20saya%20ingin%20memesan%20${encodeURIComponent(p.name)}%20(SKU:%20${p.sku})`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-2 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/35 text-emerald-300 border border-emerald-500/30 text-xs font-medium flex items-center justify-center gap-1.5 transition-all"
                    >
                      <span>Pesan WA</span>
                      <ExternalLink className="w-3.5 h-3.5 text-emerald-400" />
                    </a>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
