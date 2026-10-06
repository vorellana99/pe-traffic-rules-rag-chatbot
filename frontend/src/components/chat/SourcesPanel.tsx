import { FileSearch, X } from "lucide-react";
import { useEffect, useRef } from "react";

import type { Source } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Props {
  sources: Source[];
  selectedIndex: number | null;
  onClose: () => void;
}

export function SourcesPanel({ sources, selectedIndex, onClose }: Props) {
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    if (selectedIndex != null) {
      cardRefs.current[selectedIndex]?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [selectedIndex]);

  return (
    <aside className="flex w-80 shrink-0 flex-col border-l border-border bg-card">
      <header className="flex items-center justify-between border-b border-border px-4 py-3">
        <h3 className="text-sm font-semibold tracking-tight">Fuentes</h3>
        <button
          type="button"
          onClick={onClose}
          className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
          aria-label="Cerrar panel de fuentes"
        >
          <X className="h-4 w-4" />
        </button>
      </header>

      {sources.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center p-6 text-center">
          <FileSearch className="mb-3 h-8 w-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Sin fuentes todavía.</p>
          <p className="mt-1 text-xs text-muted-foreground/70">
            Haz una pregunta para ver los fragmentos citados.
          </p>
        </div>
      ) : (
        <div className="flex-1 space-y-3 overflow-y-auto p-3">
          {sources.map((source, index) => (
            <div
              key={source.chunk_id}
              ref={(el) => {
                cardRefs.current[index] = el;
              }}
              className={cn(
                "rounded-md border p-3 text-xs transition-colors",
                index === selectedIndex
                  ? "border-primary bg-accent/50 ring-1 ring-primary"
                  : "border-border",
              )}
            >
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="font-medium text-foreground">
                  [{index + 1}] {source.filename}
                </span>
                {source.page != null && (
                  <span className="shrink-0 text-muted-foreground">
                    pág. {source.page}
                  </span>
                )}
              </div>
              <div className="mb-2 text-[10px] uppercase tracking-wide text-muted-foreground/70">
                score {source.score.toFixed(4)}
              </div>
              <p className="max-h-48 overflow-y-auto whitespace-pre-wrap leading-relaxed text-muted-foreground">
                {source.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
