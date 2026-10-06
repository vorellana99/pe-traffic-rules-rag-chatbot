// Cliente API tipado. Las rutas van bajo /api (proxy de Vite -> api:8000).

export interface DocumentOut {
  id: string;
  filename: string;
  title: string | null;
  pages: number | null;
  status: "processing" | "ready" | "error";
  error_message: string | null;
  chunk_count: number;
  created_at: string;
}

export interface Source {
  chunk_id: string;
  document_id: string;
  filename: string;
  page: number | null;
  content: string;
  score: number;
}

export interface MessageOut {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: Source[] | null;
  created_at: string;
}

export interface ConversationOut {
  id: string;
  title: string | null;
  created_at: string;
}

export interface EvalMetrics {
  faithfulness: number;
  answer_relevancy: number;
  context_precision: number;
}

export interface EvalResults {
  timestamp: string;
  models: { llm: string; embedding: string };
  global: EvalMetrics;
  per_question: Array<EvalMetrics & { question: string }>;
}

const API_BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    throw new Error(`API ${res.status} ${res.statusText}`);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export const api = {
  listDocuments: () => request<DocumentOut[]>("/documents"),
  getDocument: (id: string) => request<DocumentOut>(`/documents/${id}`),
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ id: string; status: string }>("/documents", {
      method: "POST",
      body: form,
    });
  },
  deleteDocument: (id: string) =>
    request<void>(`/documents/${id}`, { method: "DELETE" }),
  listConversations: () => request<ConversationOut[]>("/conversations"),
  getMessages: (conversationId: string) =>
    request<MessageOut[]>(`/conversations/${conversationId}/messages`),
  // Devuelve null si aún no hay resultados (404).
  getEvalResults: async (): Promise<EvalResults | null> => {
    const res = await fetch(`${API_BASE}/eval/results`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`API ${res.status} ${res.statusText}`);
    return (await res.json()) as EvalResults;
  },
};
