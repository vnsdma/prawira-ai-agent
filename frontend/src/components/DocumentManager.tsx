"use client";

import React, { useState, useEffect } from "react";
import { DocumentItem, fetchDocuments, uploadPdfDocument } from "@/lib/api";
import { 
  FileText, 
  UploadCloud, 
  CheckCircle2, 
  AlertCircle, 
  Layers, 
  Search, 
  Sparkles, 
  ShieldCheck, 
  FileCheck,
  BookOpen,
  ArrowUpRight,
  Database,
  Cpu
} from "lucide-react";

export const DocumentManager: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<{ text: string; error?: boolean } | null>(null);
  const [testQuery, setTestQuery] = useState("");
  const [simResults, setSimResults] = useState<any[]>([]);

  const loadDocs = async () => {
    try {
      setLoading(true);
      const res = await fetchDocuments();
      setDocuments(res.documents || []);
    } catch (err) {
      console.error("Error loading documents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadMessage({ text: "Hanya dokumen berformat PDF yang didukung.", error: true });
      return;
    }

    try {
      setUploading(true);
      setUploadMessage(null);
      const res = await uploadPdfDocument(file);
      setUploadMessage({ text: res.message });
      await loadDocs();
    } catch (err: any) {
      setUploadMessage({ text: err.message || "Gagal memproses dokumen.", error: true });
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const totalChunks = documents.reduce((acc, curr) => acc + (curr.chunks_count || 0), 0);

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto px-4 sm:px-8 py-6 space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-white/[0.08]">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-amber-400">
              Document Intelligence & Grounded RAG Vault
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-950/70 text-amber-300 border border-amber-800/60 flex items-center gap-1">
              <Database className="w-3 h-3 text-amber-400" />
              PostgreSQL + pgvector
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-slate-100 tracking-tight">
            Official SOP & Knowledge Chunks
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Pusat penyimpanan dokumen resmi Prawira Tobacco yang diindeks ke dalam vektor berdimensi tinggi menggunakan model embedding Gemini. Setiap respons AI diverifikasi dengan sitasi halaman resmi untuk mencegah halusinasi.
          </p>
        </div>

        {/* Upload Trigger Button */}
        <div>
          <label className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-slate-950 font-semibold text-xs cursor-pointer shadow-lg shadow-amber-900/30 transition-all hover:scale-[1.02] active:scale-[0.98]">
            <UploadCloud className="w-4 h-4 text-slate-950" />
            <span>{uploading ? "Memproses PDF..." : "Unggah Dokumen PDF"}</span>
            <input 
              type="file" 
              accept=".pdf" 
              onChange={handleFileUpload} 
              disabled={uploading}
              className="hidden" 
            />
          </label>
        </div>
      </div>

      {/* Upload Notification */}
      {uploadMessage && (
        <div className={`p-4 rounded-xl text-xs flex items-center gap-2.5 animate-fadeIn ${
          uploadMessage.error 
            ? "bg-red-950/70 border border-red-800/70 text-red-200" 
            : "bg-emerald-950/70 border border-emerald-800/70 text-emerald-200"
        }`}>
          {uploadMessage.error ? (
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          )}
          <span>{uploadMessage.text}</span>
        </div>
      )}

      {/* RAG Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card rounded-2xl p-4">
          <div className="text-[11px] font-mono uppercase text-slate-400">Total Dokumen PDF</div>
          <div className="text-2xl font-bold font-serif text-slate-100 mt-1">{documents.length} Dokumen</div>
          <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            <span>SOP & Katalog Terverifikasi</span>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-4">
          <div className="text-[11px] font-mono uppercase text-slate-400">Vektor Chunks Terindeks</div>
          <div className="text-2xl font-bold font-serif text-amber-300 mt-1">{totalChunks} Chunks</div>
          <div className="text-[11px] text-slate-400 mt-1">HNSW Index Cosine Distance</div>
        </div>

        <div className="glass-card rounded-2xl p-4">
          <div className="text-[11px] font-mono uppercase text-slate-400">Dimensi Embedding</div>
          <div className="text-2xl font-bold font-serif text-slate-100 mt-1">768 Dimensi</div>
          <div className="text-[11px] text-slate-400 mt-1">Gemini / OpenAI Text-Embedding</div>
        </div>
      </div>

      {/* Active Indexed Documents */}
      <div className="space-y-3">
        <h2 className="text-sm font-mono uppercase tracking-wider text-amber-400 flex items-center gap-2">
          <BookOpen className="w-4 h-4" />
          <span>Daftar Dokumen Resmi Aktif</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {documents.map((doc, idx) => {
            const isSOP = doc.document_name.includes("SOP");
            return (
              <div 
                key={idx}
                className="glass-card rounded-2xl p-5 border border-white/[0.08] hover:border-amber-500/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.06] text-amber-300 border border-white/[0.08]">
                      {isSOP ? "STANDAR OPERASIONAL (SOP)" : "KATALOG PRODUK & AROMA"}
                    </span>
                    <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                      <FileCheck className="w-3.5 h-3.5" />
                      <span>{doc.chunks_count} Chunks</span>
                    </span>
                  </div>

                  <h3 className="text-base font-serif font-bold text-slate-100 leading-snug">
                    {doc.document_name}
                  </h3>

                  <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                    {isSOP 
                      ? "Memuat pedoman standar kelembaban optimal tembakau (RH 65-70% pada suhu 20-25°C), penggunaan wadah kedap udara/Boveda, serta kebijakan garansi retur 2x24 jam wajib video unboxing utuh."
                      : "Memuat peta karakteristik 24 varian rasa tembakau linting artisan, profil aroma manis, gurih kretek, menthol dingin, mild pemula, dan panduan racikan linting."
                    }
                  </p>
                </div>

                <div className="pt-4 mt-4 border-t border-white/[0.06] flex items-center justify-between text-xs text-slate-400">
                  <span>Total Halaman: <strong className="text-slate-200 font-mono">{doc.total_pages || 1} Hal</strong></span>
                  <span className="text-[11px] font-mono text-slate-500">
                    {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString("id-ID") : "Terindeks"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* RAG Anti-Hallucination Guardrails Explainer */}
      <div className="rounded-2xl bg-gradient-to-br from-[#121824] to-[#0c1018] border border-amber-500/30 p-6 shadow-xl">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-serif font-bold text-slate-100">
              Mekanisme Anti-Halusinasi & Grounded Citations
            </h3>
            <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">
              Sistem ini menolak spekulasi pada pertanyaan di luar dokumen resmi (seperti tiket pesawat, saham, atau informasi fiktif). Ketika pengguna menanyakan tentang SOP atau varian tembakau, RAG engine memfilter kemiripan semantik dengan ambang batas (threshold 0.45). Setiap kutipan jawaban dilengkapi dengan label sitasi dokumen dan nomor halaman persis.
            </p>

            <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                <div className="font-semibold text-amber-300 font-mono text-[11px]">1. THRESHOLD FILTERING</div>
                <div className="text-[11px] text-slate-400 mt-1">Hanya potongan dengan skor kemiripan &gt;0.45 yang disertakan ke konteks prompt.</div>
              </div>
              <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                <div className="font-semibold text-amber-300 font-mono text-[11px]">2. STRICT GUARDRAIL</div>
                <div className="text-[11px] text-slate-400 mt-1">Prompt sistem melarang keras AI mengarang jawaban bila tidak tercantum di PDF.</div>
              </div>
              <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                <div className="font-semibold text-amber-300 font-mono text-[11px]">3. VERIFIABLE CITATION</div>
                <div className="text-[11px] text-slate-400 mt-1">Setiap jawaban menyertakan referensi akordeon yang dapat diaudit langsung.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
