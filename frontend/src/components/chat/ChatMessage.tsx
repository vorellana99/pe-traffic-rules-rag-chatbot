import ReactMarkdown from "react-markdown";

import { CitationChips } from "@/components/chat/CitationChips";
import { StageIndicator } from "@/components/chat/StageIndicator";
import type {
  ChatMessage as ChatMessageType,
  Stage,
} from "@/hooks/useChatStream";
import type { Source } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Props {
  message: ChatMessageType;
  isStreaming?: boolean;
  stage?: Stage;
  onCitationClick?: (sources: Source[], index: number) => void;
}

export function ChatMessage({
  message,
  isStreaming = false,
  stage = null,
  onCitationClick,
}: Props) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-primary px-4 py-2 text-sm text-primary-foreground">
          {message.content}
        </div>
      </div>
    );
  }

  const showStage = isStreaming && !message.content;

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] rounded-2xl rounded-bl-sm bg-card px-4 py-3">
        {showStage ? (
          <StageIndicator stage={stage} />
        ) : (
          <div className={cn("prose-chat text-sm leading-relaxed")}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {isStreaming && (
              <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-foreground/60 align-middle" />
            )}
          </div>
        )}
        {message.sources && message.sources.length > 0 && (
          <CitationChips
            sources={message.sources}
            onCitationClick={(index) =>
              onCitationClick?.(message.sources!, index)
            }
          />
        )}
      </div>
    </div>
  );
}
