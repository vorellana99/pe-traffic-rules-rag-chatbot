import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";

import { api, type Source } from "@/lib/api";
import { parseSSEStream } from "@/lib/sse";

export type Stage = "rewriting" | "retrieving" | "generating" | null;

export interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[] | null;
}

interface Options {
  conversationId: string | null;
  onConversationId: (id: string) => void;
}

function updateLastAssistant(
  messages: ChatMessage[],
  update: (m: ChatMessage) => ChatMessage,
): ChatMessage[] {
  const next = [...messages];
  for (let i = next.length - 1; i >= 0; i--) {
    if (next[i].role === "assistant") {
      next[i] = update(next[i]);
      break;
    }
  }
  return next;
}

export function useChatStream({ conversationId, onConversationId }: Options) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [stage, setStage] = useState<Stage>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const historyQuery = useQuery({
    queryKey: ["messages", conversationId],
    queryFn: () =>
      conversationId ? api.getMessages(conversationId) : Promise.resolve([]),
    enabled: !!conversationId,
  });

  // Carga el historial desde la API (y limpia al iniciar conversación nueva).
  useEffect(() => {
    if (!conversationId) {
      setMessages([]);
      return;
    }
    if (historyQuery.data) {
      setMessages(
        historyQuery.data.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          sources: m.sources,
        })),
      );
    }
  }, [conversationId, historyQuery.data]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isStreaming) return;
      setError(null);
      setStage(null);
      setIsStreaming(true);
      setMessages((prev) => [
        ...prev,
        { role: "user", content: text },
        { role: "assistant", content: "", sources: null },
      ]);

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            conversation_id: conversationId,
            message: text,
          }),
        });
        if (!res.ok || !res.body) {
          throw new Error(`HTTP ${res.status}`);
        }

        for await (const ev of parseSSEStream(res.body)) {
          const data = JSON.parse(ev.data);
          switch (ev.event) {
            case "status":
              setStage(data.stage as Stage);
              break;
            case "sources":
              setMessages((prev) =>
                updateLastAssistant(prev, (m) => ({
                  ...m,
                  sources: data as Source[],
                })),
              );
              break;
            case "token":
              setMessages((prev) =>
                updateLastAssistant(prev, (m) => ({
                  ...m,
                  content: m.content + data.text,
                })),
              );
              break;
            case "done":
              setMessages((prev) =>
                updateLastAssistant(prev, (m) => ({
                  ...m,
                  id: data.message_id,
                })),
              );
              if (!conversationId) onConversationId(data.conversation_id);
              break;
            case "error":
              setError(data.detail ?? "Error desconocido");
              break;
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setIsStreaming(false);
        setStage(null);
      }
    },
    [conversationId, isStreaming, onConversationId],
  );

  return { messages, stage, isStreaming, error, sendMessage };
}
