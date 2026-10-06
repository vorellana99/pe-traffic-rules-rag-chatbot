import {
  MessagesSquare,
  PanelRightClose,
  PanelRightOpen,
  Plus,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ChatInput } from "@/components/chat/ChatInput";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { SourcesPanel } from "@/components/chat/SourcesPanel";
import { Button } from "@/components/ui/button";
import { useChatStream } from "@/hooks/useChatStream";
import type { Source } from "@/lib/api";

export function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const conversationId = searchParams.get("c");

  const { messages, stage, isStreaming, error, sendMessage } = useChatStream({
    conversationId,
    onConversationId: (id) => setSearchParams({ c: id }, { replace: true }),
  });

  const [panelOpen, setPanelOpen] = useState(false);
  const [panelSources, setPanelSources] = useState<Source[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  // Fuentes del último mensaje del asistente (para el botón "Fuentes").
  const lastSources = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.role === "assistant" && m.sources && m.sources.length > 0) {
        return m.sources;
      }
    }
    return [];
  }, [messages]);

  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, stage]);

  const newChat = () => {
    setSearchParams({}, { replace: true });
    setPanelOpen(false);
    setPanelSources([]);
    setSelectedIndex(null);
  };

  const handleCitationClick = (sources: Source[], index: number) => {
    setPanelSources(sources);
    setSelectedIndex(index);
    setPanelOpen(true);
  };

  const togglePanel = () => {
    if (panelOpen) {
      setPanelOpen(false);
    } else {
      setPanelSources(lastSources);
      setSelectedIndex(null);
      setPanelOpen(true);
    }
  };

  return (
    <div className="flex h-full">
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="text-sm font-semibold tracking-tight">
            {conversationId ? "Conversación" : "Nueva conversación"}
          </h2>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={togglePanel}>
              {panelOpen ? (
                <PanelRightClose className="h-4 w-4" />
              ) : (
                <PanelRightOpen className="h-4 w-4" />
              )}
              Fuentes
              {lastSources.length > 0 && (
                <span className="ml-1 rounded bg-secondary px-1.5 text-xs">
                  {lastSources.length}
                </span>
              )}
            </Button>
            <Button variant="outline" size="sm" onClick={newChat}>
              <Plus className="h-4 w-4" />
              Nueva
            </Button>
          </div>
        </header>

        <div ref={scrollRef} className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl space-y-4 p-4">
            {messages.length === 0 && !isStreaming && (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <MessagesSquare className="mb-4 h-10 w-10 text-muted-foreground" />
                <p className="max-w-md text-sm text-muted-foreground">
                  Pregunta en español sobre normativa de tránsito y licencias de
                  conducir del Perú. Las respuestas incluyen citas verificables
                  a los documentos.
                </p>
              </div>
            )}

            {messages.map((message, index) => {
              const isLast = index === messages.length - 1;
              return (
                <ChatMessage
                  key={message.id ?? index}
                  message={message}
                  isStreaming={
                    isStreaming && isLast && message.role === "assistant"
                  }
                  stage={stage}
                  onCitationClick={handleCitationClick}
                />
              );
            })}

            {error && (
              <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-2 text-sm text-destructive">
                {error}
              </div>
            )}
          </div>
        </div>

        <ChatInput onSend={sendMessage} disabled={isStreaming} />
      </div>

      {panelOpen && (
        <SourcesPanel
          sources={panelSources}
          selectedIndex={selectedIndex}
          onClose={() => setPanelOpen(false)}
        />
      )}
    </div>
  );
}
