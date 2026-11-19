"use client";

import React from "react";
import { ExecutedTool } from "@/lib/api";
import { 
  Database, 
  PackageCheck, 
  AlertCircle, 
  ExternalLink, 
  Send, 
  MapPin, 
  Tag, 
  CheckCircle2, 
  Smartphone,
  Sparkles,
  ArrowRight
} from "lucide-react";

interface ToolCardProps {
  tool: ExecutedTool;
}

export const ToolCard: React.FC<ToolCardProps> = ({ tool }) => {
  const { tool: toolName, arguments: args, result } = tool;

  if (toolName === "check_inventory_stock") {
    const isFound = result?.found;
    const items = result?.items || [];
    const sourceLabel = result?.source || "Supabase Cloud Database";

    return (
      <div className="my-3 rounded-2xl bg-gradient-to-br from-[#161a24] to-[#11141d] border border-amber-500/25 p-4 shadow-xl shadow-black/40">
        {/* Header Ribbon */}
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-semibold tracking-wide uppercase text-amber-400">
                  Status Stok Gudang Real-Time
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-950/60 text-amber-300 border border-amber-800/50">
                  {sourceLabel}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Pencarian: &ldquo;{args?.search_term}&rdquo;
              </p>
            </div>
          </div>
          <span className={`text-[11px] font-mono font-medium px-2.5 py-1 rounded-full flex items-center gap-1.5 ${
            isFound 
              ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800/60" 
              : "bg-red-950/60 text-red-300 border border-red-800/60"
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isFound ? "bg-emerald-400 animate-pulse" : "bg-red-400"}`}></span>
            {isFound ? `${items.length} Item Ditemukan` : "Tidak Ditemukan"}
          </span>
        </div>

        {/* Content Items */}
        {isFound && items.length > 0 ? (
          <div className="space-y-2.5">
            {items.map((item: any, idx: number) => {
              const inStock = item.stock > 0;
              return (
                <div 
                  key={idx}
                  className="rounded-xl bg-[#0c0e15]/90 border border-white/[0.06] p-3 hover:border-amber-500/40 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-sm text-slate-100">
                        {item.name}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/[0.06] text-amber-300 border border-white/[0.08]">
                        {item.sku}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800/80 text-slate-300 capitalize">
                        {item.category?.replace("_", " ")}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-400 flex-wrap">
                      <span className="flex items-center gap-1 text-slate-300">
                        <Tag className="w-3 h-3 text-amber-400" />
                        <strong className="text-amber-200">{item.formatted_price || `Rp ${item.price?.toLocaleString()}`}</strong>
                      </span>
                      <span className="text-slate-600">&bull;</span>
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-slate-400" />
                        <span>{item.shelf_location || "Gudang Prawira"}</span>
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
                    <span className={`text-xs font-mono px-2.5 py-1 rounded-lg flex items-center gap-1.5 font-medium ${
                      inStock 
                        ? "bg-emerald-950/60 text-emerald-300 border border-emerald-800/60" 
                        : "bg-red-950/60 text-red-300 border border-red-800/60"
                    }`}>
                      <PackageCheck className="w-3.5 h-3.5" />
                      <span>{item.stock} {item.unit || "pack"}</span>
                    </span>
                    <a
                      href={`https://wa.me/6283132001855?text=Halo%20Prawira%20Tobacco,%20saya%20ingin%20memesan%20${encodeURIComponent(item.name)}%20(SKU:%20${item.sku})`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-2.5 py-1 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/30 text-xs font-medium flex items-center gap-1 transition-all"
                    >
                      <span>Pesan</span>
                      <ArrowRight className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-3 text-xs text-slate-400 bg-[#0c0e15] rounded-xl border border-white/[0.04] flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{result?.message || "Produk tidak ditemukan di database gudang."}</span>
          </div>
        )}
      </div>
    );
  }

  if (toolName === "send_whatsapp_action") {
    const isSuccess = result?.success;
    const phone = result?.target_phone || args?.phone_number || "6283132001855";
    const directUrl = result?.direct_url || `https://wa.me/${phone}?text=${encodeURIComponent(args?.message_body || "")}`;
    const provider = result?.provider || "Fonnte WhatsApp API Gateway";

    return (
      <div className="my-3 rounded-2xl bg-gradient-to-br from-[#121d19] to-[#0d1612] border border-emerald-500/30 p-4 shadow-xl shadow-black/40">
        {/* Header Ribbon */}
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-emerald-500/20">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <Smartphone className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-semibold tracking-wide uppercase text-emerald-400">
                  Ringkasan Pesanan WhatsApp
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800">
                  {provider}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Penerima Target: <strong className="text-emerald-300 font-mono">+{phone}</strong>
              </p>
            </div>
          </div>
          <span className="text-[11px] font-mono font-medium px-2.5 py-1 rounded-full bg-emerald-900/60 text-emerald-200 border border-emerald-700/60 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Terkirim & Siap Tindak Lanjut</span>
          </span>
        </div>

        {/* Message Preview Payload */}
        <div className="rounded-xl bg-[#09110d] border border-emerald-900/50 p-3 mb-3">
          <div className="text-[10px] font-mono uppercase tracking-wider text-emerald-500/80 mb-1.5 flex items-center gap-1">
            <Send className="w-3 h-3" />
            <span>Isi Pesan WhatsApp:</span>
          </div>
          <p className="text-xs text-slate-200 whitespace-pre-wrap font-sans leading-relaxed line-clamp-4">
            {args?.message_body || result?.message_preview}
          </p>
        </div>

        {/* Direct WhatsApp Call to Action */}
        <div className="flex items-center justify-between gap-3 pt-1">
          <span className="text-[11px] text-slate-400 hidden sm:inline">
            Tersambung langsung ke nomor WhatsApp toko Prawira
          </span>
          <a
            href={directUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full sm:w-auto px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-semibold text-xs flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/40 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <span>Buka Chat WhatsApp Resmi</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    );
  }

  // Fallback generic tool card
  return (
    <div className="my-2 rounded-xl bg-slate-900/70 border border-slate-700/50 p-3 text-xs">
      <div className="font-mono text-slate-400">Executed: {toolName}</div>
      <pre className="mt-1 text-[11px] text-slate-300 overflow-x-auto">
        {JSON.stringify(result, null, 2)}
      </pre>
    </div>
  );
};
