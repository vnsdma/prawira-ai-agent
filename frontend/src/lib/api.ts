// API Client helper for Prawira Tobacco Enterprise Backend

const DEFAULT_ENDPOINTS = [
  process.env.NEXT_PUBLIC_API_URL,
  "https://prawira-ai-agent.onrender.com/api",
  "http://localhost:8000/api",
  "http://localhost:8001/api",
].filter(Boolean) as string[];

let activeBaseUrl = DEFAULT_ENDPOINTS[0] || "https://prawira-ai-agent.onrender.com/api";

async function fetchWithFallback(endpoint: string, options?: RequestInit): Promise<Response> {
  // Try active first
  const tryUrl = (base: string) => `${base.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;

  try {
    const res = await fetch(tryUrl(activeBaseUrl), options);
    if (res.ok) return res;
  } catch (err) {
    // Try fallback ports if connection failed
    for (const alt of DEFAULT_ENDPOINTS) {
      if (alt === activeBaseUrl) continue;
      try {
        const altRes = await fetch(tryUrl(alt), options);
        if (altRes.ok) {
          activeBaseUrl = alt;
          return altRes;
        }
      } catch {
        continue;
      }
    }
    throw err;
  }

  // If status was not ok on active, retry other ports in case of port conflict
  for (const alt of DEFAULT_ENDPOINTS) {
    if (alt === activeBaseUrl) continue;
    try {
      const altRes = await fetch(tryUrl(alt), options);
      if (altRes.ok) {
        activeBaseUrl = alt;
        return altRes;
      }
    } catch {
      continue;
    }
  }

  // Fallback to active response
  return fetch(tryUrl(activeBaseUrl), options);
}

export interface HealthInfo {
  status: string;
  database: string;
  llm_provider: string;
  total_products: number;
  total_document_chunks: number;
}

export interface ProductItem {
  id: number;
  sku: string;
  name: string;
  category: string;
  similarity_grade: string;
  stock: number;
  unit: string;
  weight_grams: number;
  price: number;
  shelf_location: string;
  description: string;
}

export interface DocumentItem {
  document_name: string;
  chunks_count: number;
  total_pages: number;
  uploaded_at: string;
}

export interface Citation {
  document: string;
  page: number;
  similarity: number;
  preview: string;
}

export interface ExecutedTool {
  tool: string;
  arguments: Record<string, any>;
  result: Record<string, any>;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  executed_tools: ExecutedTool[];
  provider: string;
}

export interface StreamEvent {
  type: "status" | "citations" | "tool_start" | "tool_end" | "token" | "done" | "error";
  message?: string;
  stage?: string;
  citations?: Citation[];
  tool?: string;
  arguments?: Record<string, any>;
  result?: Record<string, any>;
  content?: string;
  provider?: string;
  latency_ms?: number;
}

export async function sendChatMessageStream(
  message: string,
  callbacks: {
    onStatus?: (stage: string, message: string) => void;
    onCitations?: (citations: Citation[]) => void;
    onToolStart?: (tool: string, args: Record<string, any>) => void;
    onToolEnd?: (tool: string, args: Record<string, any>, result: Record<string, any>) => void;
    onToken?: (token: string) => void;
    onDone?: (provider: string, latencyMs?: number) => void;
    onError?: (error: Error) => void;
  }
): Promise<void> {
  const tryUrl = (base: string) => `${base.replace(/\/$/, "")}/chat/stream`;

  let response: Response | null = null;
  const targetEndpoints = [activeBaseUrl, ...DEFAULT_ENDPOINTS.filter(b => b !== activeBaseUrl)];

  for (const base of targetEndpoints) {
    try {
      const res = await fetch(tryUrl(base), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      if (res.ok && res.body) {
        activeBaseUrl = base;
        response = res;
        break;
      }
    } catch {
      continue;
    }
  }

  // Graceful fallback to non-streaming endpoint if streaming fails or not supported
  if (!response || !response.body) {
    try {
      const nonStreamRes = await sendChatMessage(message);
      if (nonStreamRes.citations && callbacks.onCitations) callbacks.onCitations(nonStreamRes.citations);
      if (nonStreamRes.executed_tools && callbacks.onToolEnd) {
        for (const t of nonStreamRes.executed_tools) {
          callbacks.onToolEnd(t.tool, t.arguments, t.result);
        }
      }
      if (callbacks.onToken) callbacks.onToken(nonStreamRes.answer);
      if (callbacks.onDone) callbacks.onDone(nonStreamRes.provider);
      return;
    } catch (err: any) {
      if (callbacks.onError) callbacks.onError(err);
      throw err;
    }
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data:")) continue;
        const jsonStr = trimmed.replace(/^data:\s*/, "");
        if (!jsonStr) continue;

        try {
          const event: StreamEvent = JSON.parse(jsonStr);
          if (event.type === "status" && callbacks.onStatus) {
            callbacks.onStatus(event.stage || "", event.message || "");
          } else if (event.type === "citations" && callbacks.onCitations && event.citations) {
            callbacks.onCitations(event.citations);
          } else if (event.type === "tool_start" && callbacks.onToolStart && event.tool) {
            callbacks.onToolStart(event.tool, event.arguments || {});
          } else if (event.type === "tool_end" && callbacks.onToolEnd && event.tool) {
            callbacks.onToolEnd(event.tool, event.arguments || {}, event.result || {});
          } else if (event.type === "token" && callbacks.onToken && event.content !== undefined) {
            callbacks.onToken(event.content);
          } else if (event.type === "done" && callbacks.onDone) {
            callbacks.onDone(event.provider || "Gemini Flash Agent", event.latency_ms);
          }
        } catch {
          // ignore corrupted SSE frame
        }
      }
    }
  } catch (err: any) {
    if (callbacks.onError) callbacks.onError(err);
    throw err;
  }
}

export async function fetchHealth(): Promise<HealthInfo> {
  const res = await fetchWithFallback("/health");
  if (!res.ok) throw new Error("Backend offline");
  return res.json();
}

export async function fetchProducts(category?: string): Promise<{ count: number; products: ProductItem[] }> {
  const endpoint = category && category !== "all" 
    ? `/products?category=${encodeURIComponent(category)}`
    : `/products`;
  const res = await fetchWithFallback(endpoint);
  if (!res.ok) throw new Error("Gagal mengambil data produk");
  return res.json();
}

export async function fetchDocuments(): Promise<{ count: number; documents: DocumentItem[] }> {
  const res = await fetchWithFallback("/documents");
  if (!res.ok) throw new Error("Gagal mengambil daftar dokumen");
  return res.json();
}

export async function syncSupabase(): Promise<{ success: boolean; message: string }> {
  const res = await fetchWithFallback("/sync-supabase", { method: "POST" });
  if (!res.ok) throw new Error("Gagal sinkronisasi Supabase");
  return res.json();
}

export async function uploadPdfDocument(file: File): Promise<{ success: boolean; filename: string; chunks_stored: number; message: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetchWithFallback("/upload-document", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Gagal mengunggah dokumen" }));
    throw new Error(err.detail || "Gagal mengunggah dokumen");
  }

  return res.json();
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const res = await fetchWithFallback("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Gagal memproses pesan" }));
    throw new Error(err.detail || "Terjadi kesalahan pada agent");
  }

  return res.json();
}
