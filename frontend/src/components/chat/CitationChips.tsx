import type { Source } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Props {
  sources: Source[];
  onCitationClick?: (index: number) => void;
}

export function CitationChips({ sources, onCitationClick }: Props) {
  if (!sources.length) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {sources.map((source, index) => (
        <button
          key={source.chunk_id}
          type="button"
          onClick={() => onCitationClick?.(index)}
          title={`${source.filename}${source.page != null ? ` · pág. ${source.page}` : ""}`}
          className={cn(
            "inline-flex h-6 min-w-6 items-center justify-center rounded-md border border-border",
            "bg-secondary px-1.5 text-xs font-medium text-secondary-foreground",
            "transition-colors hover:bg-accent hover:text-accent-foreground",
          )}
        >
          {index + 1}
        </button>
      ))}
    </div>
  );
}
