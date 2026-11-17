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
      <header className="border-b border-white/[0.08] bg-[#0c0f17]/90 backdrop-blur-xl px-4 sm:px-6 py-3 shrink-0 flex items-center justify-between z-30">
        {/* Brand & Atelier Identity */}
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/40 flex items-center justify-center text-amber-300 font-bold shadow-lg shadow-black/50">
            <Sparkles className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-sm sm:text-base tracking-wider uppercase text-amber-100 font-serif">
                Prawira Tobacco
              </span>
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-amber-950/80 text-amber-300 border border-amber-800/60 hidden xs:inline-block">
                Enterprise AI Agent
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden md:block">
              Sistem Intelijen Dokumen RAG & Otomasi Tindakan WhatsApp
            </p>
          </div>
        </div>

        {/* View Switcher Tabs (Focused on Core Utility) */}
        <nav className="flex items-center bg-[#121622] p-1 rounded-2xl border border-white/[0.08] shadow-inner">
          <button
            onClick={() => setActiveTab("agent")}
            className={`flex items-center gap-2 px-3 sm:px-4 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === "agent"
                ? "bg-amber-600 text-slate-950 shadow-md shadow-amber-900/40 font-bold"
                : "text-slate-300 hover:text-white hover:bg-white/[0.04]"
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Asisten AI Prawira</span>
            <span className="sm:hidden">Chat AI</span>
          </button>

          <button
            onClick={() => setActiveTab("catalog")}
            className={`flex items-center gap-2 px-3 sm:px-4 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === "catalog"
                ? "bg-amber-600 text-slate-950 shadow-md shadow-amber-900/40 font-bold"
                : "text-slate-300 hover:text-white hover:bg-white/[0.04]"
            }`}
          >
            <Package className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Katalog & Stok Live</span>
            <span className="sm:hidden">Katalog</span>
          </button>

          <button
            onClick={() => setActiveTab("documents")}
            className={`flex items-center gap-2 px-3 sm:px-4 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === "documents"
                ? "bg-amber-600 text-slate-950 shadow-md shadow-amber-900/40 font-bold"
                : "text-slate-300 hover:text-white hover:bg-white/[0.04]"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Pusat SOP & Dokumen</span>
            <span className="sm:hidden">SOP</span>
          </button>
        </nav>

        {/* Official Store WhatsApp Hotline */}
        <div className="flex items-center gap-3">
          <a
            href="https://wa.me/6283132001855?text=Halo%20Prawira%20Tobacco,%20saya%20ingin%20berkonsultasi%20mengenai%20produk%20tembakau."
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/35 text-emerald-300 border border-emerald-500/30 text-xs font-medium transition-all"
            title="Hubungi WhatsApp Toko Resmi"
          >
            <Smartphone className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-mono hidden sm:inline">0831-3200-1855</span>
            <span className="sm:hidden">WhatsApp</span>
            <ExternalLink className="w-3 h-3 text-emerald-400" />
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
