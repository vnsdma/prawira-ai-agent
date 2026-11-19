"use client";

import React, { useState, useRef, useEffect } from "react";
import { 
  sendChatMessage, 
  sendChatMessageStream,
  ChatResponse, 
  Citation, 
  ExecutedTool 
} from "@/lib/api";
import { ToolCard } from "./ToolCard";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { 
  Send, 
  Sparkles, 
  User, 
  FileText, 
  ChevronDown, 
  ChevronUp, 
  ShieldCheck, 
  CheckCircle2, 
  Zap, 
  Trash2,
  Activity
} from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "agent";
  text: string;
  citations?: Citation[];
  tools?: ExecutedTool[];
  provider?: string;
  timestamp: string;
  isStreaming?: boolean;
  latencyMs?: number;
}

interface ChatInterfaceProps {
  initialPrompt?: string;
  onClearInitialPrompt?: () => void;
}

const FREQUENT_CONSULTATION_CHIPS = [
  {
    label: "Rekomendasi 1 Rasa Manis",
    prompt: "Rekomendasikan 1 tembakau rasa manis yang paling enak dan cek ketersediaan stoknya",
  },
  {
    label: "Cek Stok Linting Surya",
    prompt: "Cek ketersediaan stok fisik Linting Surya di gudang Supabase",
  },
  {
    label: "Varian Dingin Ice Menthol",
    prompt: "Tampilkan rekomendasi varian tembakau dingin ice menthol",
  },
  {
    label: "SOP Penyimpanan",
    prompt: "Berapa standar suhu dan kadar kelembaban optimal penyimpanan tembakau menurut SOP resmi?",
  },
  {
    label: "Panduan Cara Melinting",
    prompt: "Bagaimana cara melinting tembakau tingwe bagi pemula dan perlengkapan apa saja yang dibutuhkan?",
  },
];

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  initialPrompt, 
  onClearInitialPrompt 
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-msg",
      sender: "agent",
      text: "Selamat datang di **Prawira Tobacco Enterprise**.\n\nSaya adalah asisten AI resmi yang siap membantu Anda dalam:\n- **Konsultasi Rasa & Rekomendasi**: Menemukan varian tembakau sesuai profil selera Anda (manis buah, dingin ice, kretek gurih, atau mild halus).\n- **Pengecekan Stok Real-Time**: Memeriksa ketersediaan stok fisik dan harga dari 24 varian resmi di basis data Supabase.\n- **Pemesanan via WhatsApp**: Menyiapkan ringkasan pesanan ke WhatsApp resmi (+62 831-3200-1855).\n- **SOP Toko**: Informasi standar penyimpanan dan garansi retur resmi.\n\nSilakan tanyakan varian rasa atau informasi yang ingin Anda ketahui.",
      timestamp: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" })
    }
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamStatus, setStreamStatus] = useState<string>("");
  const [openCitations, setOpenCitations] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, streamStatus]);

  useEffect(() => {
    if (initialPrompt) {
      setInput(initialPrompt);
      if (onClearInitialPrompt) onClearInitialPrompt();
    }
  }, [initialPrompt, onClearInitialPrompt]);

  const handleSend = async (messageText?: string) => {
    const query = (messageText || input).trim();
    if (!query || loading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" })
    };

    const agentMsgId = `agent-${Date.now()}`;
    const initialAgentMessage: Message = {
      id: agentMsgId,
      sender: "agent",
      text: "",
      citations: [],
      tools: [],
      provider: "Prawira AI Agent",
      timestamp: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, initialAgentMessage]);
    setInput("");
    setLoading(true);
    setStreamStatus("Menghubungkan ke Prawira AI Agent...");

    try {
      await sendChatMessageStream(query, {
        onStatus: (_stage, message) => {
          setStreamStatus(message);
        },
        onCitations: (citations) => {
          setMessages((prev) =>
            prev.map((m) => (m.id === agentMsgId ? { ...m, citations } : m))
          );
        },
        onToolStart: (tool) => {
          const toolLabel = tool === "check_inventory_stock" ? "Cek Stok Supabase" : "Aksi WhatsApp";
          setStreamStatus(`Memeriksa ${toolLabel}...`);
        },
        onToolEnd: (tool, args, result) => {
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id === agentMsgId) {
                const currentTools = m.tools || [];
                return {
                  ...m,
                  tools: [...currentTools, { tool, arguments: args, result }]
                };
              }
              return m;
            })
          );
        },
        onToken: (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === agentMsgId ? { ...m, text: m.text + token } : m
            )
          );
        },
        onDone: (provider, latencyMs) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === agentMsgId
                ? { ...m, isStreaming: false, provider, latencyMs }
                : m
            )
          );
          setStreamStatus("");
        },
        onError: (err) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === agentMsgId
                ? {
                    ...m,
                    isStreaming: false,
                    text: m.text || `Terjadi kendala saat memproses: ${err.message || "Gagal streaming."}`
                  }
                : m
            )
          );
          setStreamStatus("");
        }
      });
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === agentMsgId
            ? {
                ...m,
                isStreaming: false,
                text: m.text || `Koneksi terputus: ${err.message || "Pastikan backend aktif."}`
              }
            : m
        )
      );
    } finally {
      setLoading(false);
      setStreamStatus("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleCitation = (msgId: string) => {
    setOpenCitations((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const clearChat = () => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        sender: "agent",
        text: "Riwayat percakapan telah dibersihkan. Silakan ajukan pertanyaan atau konsultasikan varian tembakau Prawira Tobacco.",
        timestamp: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" })
      }
    ]);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#080a0f]">
      {/* Clean Session Status Strip */}
      <div className="px-4 sm:px-8 py-2.5 border-b border-white/[0.06] bg-[#0c0f17] flex items-center justify-between text-xs shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
          <span className="font-medium text-slate-300">Asisten Konsultasi Sommelier</span>
          <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">&bull; 24 Varian Supabase Aktif</span>
        </div>

        <button
          onClick={clearChat}
          className="flex items-center gap-1.5 text-[11px] text-slate-400 hover:text-red-400 transition-colors px-2.5 py-1 rounded-lg hover:bg-white/[0.04]"
          title="Bersihkan Percakapan"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Bersihkan Chat</span>
        </button>
      </div>

      {/* Main Messages Scroll Area (Centered & Ergonomic) */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-6 max-w-4xl mx-auto w-full">
        {messages.map((msg) => {
          const isUser = msg.sender === "user";
          const hasCitations = msg.citations && msg.citations.length > 0;
          const hasTools = msg.tools && msg.tools.length > 0;
          const isOpen = openCitations[msg.id];

          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3.5 sm:gap-4 max-w-4xl ${
                isUser ? "ml-auto flex-row-reverse" : "mr-auto"
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-9 h-9 rounded-2xl flex items-center justify-center shrink-0 shadow-lg ${
                  isUser
                    ? "bg-amber-600 text-slate-950 font-bold"
                    : "bg-gradient-to-br from-[#1c2233] to-[#121622] border border-amber-500/30 text-amber-400"
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4 text-amber-400" />}
              </div>

              {/* Message Bubble Container */}
              <div className={`space-y-2 max-w-[88%] sm:max-w-[80%]`}>
                {/* Message Header */}
                <div className={`flex items-center gap-2 text-[11px] text-slate-400 ${isUser ? "justify-end" : "justify-start"}`}>
                  <span className="font-medium text-slate-300">
                    {isUser ? "Anda" : "Prawira Tobacco Agent"}
                  </span>
                  <span>&bull;</span>
                  <span className="font-mono text-slate-500">{msg.timestamp}</span>
                  {msg.provider && !isUser && (
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/[0.05] text-amber-300">
                      {msg.provider}
                    </span>
                  )}
                  {msg.latencyMs !== undefined && !isUser && (
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/[0.03] text-emerald-400">
                      {msg.latencyMs}ms
                    </span>
                  )}
                  {msg.isStreaming && !isUser && (
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30 animate-pulse flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                      Live Stream
                    </span>
                  )}
                </div>

                {/* Bubble Body */}
                <div
                  className={`rounded-2xl p-4 sm:p-5 text-xs sm:text-sm leading-relaxed shadow-lg ${
                    isUser
                      ? "bg-amber-600 text-slate-950 font-medium rounded-tr-sm"
                      : "glass-card text-slate-100 rounded-tl-sm border border-white/[0.08]"
                  }`}
                >
                  {/* Empty message streaming state with animated status */}
                  {!msg.text && msg.isStreaming ? (
                    <div className="flex items-center gap-2.5 text-slate-300 py-1 font-mono text-xs">
                      <Sparkles className="w-4 h-4 text-amber-400 animate-spin" />
                      <span className="text-amber-200 font-medium animate-pulse">
                        {streamStatus || "Asisten sedang menganalisis..."}
                      </span>
                    </div>
                  ) : (
                    <div className="relative">
                      <MarkdownRenderer content={msg.text} isUser={isUser} />
                      {msg.isStreaming && (
                        <span className="inline-block w-2 h-4 ml-1 bg-amber-400 animate-pulse align-middle" />
                      )}
                    </div>
                  )}

                  {/* Render Executed Tools if Any */}
                  {hasTools && (
                    <div className="mt-4 pt-3 border-t border-white/[0.08] space-y-2">
                      <div className="text-[10px] font-mono uppercase tracking-wider text-amber-400 flex items-center gap-1">
                        <Zap className="w-3 h-3 text-amber-400" />
                        <span>Aksi Sistem Berhasil Dijalankan:</span>
                      </div>
                      {msg.tools!.map((t, tidx) => (
                        <ToolCard key={tidx} tool={t} />
                      ))}
                    </div>
                  )}

                  {/* Render Verified Citations Accordion */}
                  {hasCitations && (
                    <div className="mt-3 pt-3 border-t border-white/[0.08]">
                      <button
                        onClick={() => toggleCitation(msg.id)}
                        className="flex items-center justify-between w-full py-1.5 px-3 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-xs text-amber-300 font-medium transition-all"
                      >
                        <div className="flex items-center gap-2">
                          <FileText className="w-3.5 h-3.5 text-amber-400" />
                          <span>
                            {msg.citations!.length} Referensi Dokumen Terverifikasi
                          </span>
                        </div>
                        {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>

                      {isOpen && (
                        <div className="mt-2.5 space-y-2 animate-fadeIn">
                          {msg.citations!.map((cit, cidx) => (
                            <div
                              key={cidx}
                              className="rounded-xl bg-[#0a0d14] border border-white/[0.06] p-3 text-xs space-y-1.5"
                            >
                              <div className="flex items-center justify-between flex-wrap gap-2">
                                <span className="font-semibold text-slate-200 flex items-center gap-1.5">
                                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                                  <span>{cit.document}</span>
                                </span>
                                <div className="flex items-center gap-2 font-mono text-[10px]">
                                  <span className="px-2 py-0.5 rounded bg-white/[0.06] text-amber-300">
                                    Halaman {cit.page}
                                  </span>
                                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                                    Kesesuaian: {(cit.similarity * 100).toFixed(1)}%
                                  </span>
                                </div>
                              </div>
                              <p className="text-[11px] text-slate-400 italic bg-white/[0.02] p-2 rounded-lg border border-white/[0.03]">
                                &ldquo;{cit.preview}&rdquo;
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Real-time Status Floating Badge if Streaming */}
        {loading && streamStatus && !messages.some(m => m.isStreaming && m.text) && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-950/60 border border-amber-500/30 text-xs font-mono text-amber-300 w-fit animate-pulse mr-auto">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>{streamStatus}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Frequent Consultation Prompt Chips */}
      <div className="px-4 sm:px-6 py-2.5 bg-[#0a0d14]/90 border-t border-white/[0.06] shrink-0">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[10px] font-mono uppercase tracking-wider text-amber-400 font-semibold flex items-center gap-1">
            <Zap className="w-3 h-3 text-amber-400" />
            <span>Pintasan Konsultasi & Layanan Cepat:</span>
          </span>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          {FREQUENT_CONSULTATION_CHIPS.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(chip.prompt)}
              disabled={loading}
              className="px-3 py-1.5 rounded-xl bg-white/[0.04] hover:bg-amber-500/20 text-slate-300 hover:text-amber-200 border border-white/[0.08] hover:border-amber-500/40 text-xs shrink-0 transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              <span>{chip.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Input Form Bar */}
      <div className="p-4 sm:p-6 bg-[#0c0f17] border-t border-white/[0.08] shrink-0">
        <div className="relative max-w-4xl mx-auto flex items-end gap-2.5">
          <div className="relative flex-1 rounded-2xl bg-[#121622] border border-white/[0.1] focus-within:border-amber-500/60 focus-within:ring-1 focus-within:ring-amber-500/30 transition-all">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder="Tanyakan rekomendasi tembakau, SOP penyimpanan, cek stok, atau pesan ke WhatsApp..."
              className="w-full bg-transparent px-4 py-3 text-xs sm:text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none resize-none max-h-32"
            />
          </div>

          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="w-11 h-11 rounded-2xl bg-amber-600 hover:bg-amber-500 disabled:opacity-40 disabled:hover:bg-amber-600 text-slate-950 flex items-center justify-center shrink-0 shadow-lg shadow-amber-900/30 transition-all active:scale-95"
            title="Kirim Pesan (Enter)"
          >
            <Send className="w-4 h-4 text-slate-950" />
          </button>
        </div>
      </div>
    </div>
  );
};
