import { Loader2 } from "lucide-react";

import type { Stage } from "@/hooks/useChatStream";

const LABELS: Record<Exclude<Stage, null>, string> = {
  rewriting: "Reformulando…",
  retrieving: "Buscando…",
  generating: "Generando…",
};

export function StageIndicator({ stage }: { stage: Stage }) {
  if (!stage) return null;
  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" />
      {LABELS[stage]}
    </div>
  );
}
