// API Client helper for Prawira Tobacco Enterprise Backend

const DEFAULT_ENDPOINTS = [
  process.env.NEXT_PUBLIC_API_URL,
  "http://localhost:8000/api",
  "http://localhost:8001/api",
].filter(Boolean) as string[];

let activeBaseUrl = DEFAULT_ENDPOINTS[0] || "http://localhost:8000/api";

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
