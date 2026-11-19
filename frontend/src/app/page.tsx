"use client";

import React, { useState } from "react";
import { ChatInterface } from "@/components/ChatInterface";
import { CatalogBrowser } from "@/components/CatalogBrowser";
import { DocumentManager } from "@/components/DocumentManager";
import { 
  MessageSquare, 
  Package, 
  FileText, 
  Sparkles, 
  ExternalLink,
  Smartphone,
  Database
} from "lucide-react";

type ActiveTab = "agent" | "catalog" | "documents";

export default function Home() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("agent");
  const [pendingPrompt, setPendingPrompt] = useState<string>("");

  const handleAskAgentFromCatalog = (prompt: string) => {
    setPendingPrompt(prompt);
    setActiveTab("agent");
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#080a0f] text-slate-100">
      {/* Top Global Command Bar */}
      <header className="border-b border-white/[0.08] bg-[#0c0f17]/95 backdrop-blur-xl px-4 sm:px-8 py-3.5 shrink-0 flex items-center justify-between z-30">
        {/* Brand & Identity */}
        <div className="flex items-center gap-3.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/40 flex items-center justify-center text-amber-300 font-bold shadow-md shadow-black/40">
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-sm sm:text-base tracking-wide uppercase text-amber-100 font-serif">
                Prawira Tobacco
              </span>
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-950/70 border border-emerald-800/60 text-[10px] font-mono text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Live Online
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden md:block">
              Konsultasi Tembakau Tingwe &amp; Pengecekan Stok Real-Time
            </p>
          </div>
        </div>

        {/* View Switcher Tabs (Focused, Clean & Minimal) */}
        <nav className="flex items-center bg-[#121622] p-1 rounded-xl border border-white/[0.08] shadow-inner">
          <button
            onClick={() => setActiveTab("agent")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "agent"
                ? "bg-amber-600 text-slate-950 shadow-sm font-bold"
                : "text-slate-300 hover:text-white hover:bg-white/[0.04]"
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Asisten Sommelier</span>
            <span className="sm:hidden">Chat</span>
          </button>

          <button
            onClick={() => setActiveTab("catalog")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "catalog"
                ? "bg-amber-600 text-slate-950 shadow-sm font-bold"
                : "text-slate-300 hover:text-white hover:bg-white/[0.04]"
            }`}
          >
            <Package className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Katalog &amp; Stok</span>
            <span className="sm:hidden">Katalog</span>
          </button>

          <button
            onClick={() => setActiveTab("documents")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "documents"
                ? "bg-amber-600 text-slate-950 shadow-sm font-bold"
                : "text-slate-300 hover:text-white hover:bg-white/[0.04]"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Dokumen SOP</span>
            <span className="sm:hidden">SOP</span>
          </button>
        </nav>

        {/* Official Store WhatsApp Hotline */}
        <div className="flex items-center gap-2">
          <a
            href="https://wa.me/6283132001855?text=Halo%20Prawira%20Tobacco,%20saya%20ingin%20berkonsultasi%20mengenai%20produk%20tembakau."
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-600/15 hover:bg-emerald-600/25 text-emerald-300 border border-emerald-500/30 text-xs font-medium transition-all"
            title="Hubungi WhatsApp Toko Resmi"
          >
            <Smartphone className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-mono hidden sm:inline">CS WhatsApp</span>
            <ExternalLink className="w-3 h-3 text-emerald-400 opacity-70" />
          </a>
        </div>
      </header>

      {/* Dynamic Viewport Content */}
      <main className="flex-1 overflow-hidden relative">
        {activeTab === "agent" && (
          <ChatInterface 
            initialPrompt={pendingPrompt} 
            onClearInitialPrompt={() => setPendingPrompt("")} 
          />
        )}

        {activeTab === "catalog" && (
          <CatalogBrowser onAskAgent={handleAskAgentFromCatalog} />
        )}

        {activeTab === "documents" && (
          <DocumentManager />
        )}
      </main>
    </div>
  );
}
