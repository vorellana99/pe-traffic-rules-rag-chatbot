import { CheckCircle2, Loader2, XCircle } from "lucide-react";

import type { DocumentOut } from "@/lib/api";
import { cn } from "@/lib/utils";

const CONFIG: Record<
  DocumentOut["status"],
  { label: string; className: string }
> = {
  processing: {
    label: "Procesando",
    className: "border-amber-500/30 bg-amber-500/15 text-amber-500",
  },
  ready: {
    label: "Listo",
    className: "border-emerald-500/30 bg-emerald-500/15 text-emerald-500",
  },
  error: {
    label: "Error",
    className: "border-destructive/30 bg-destructive/15 text-destructive",
  },
};

export function StatusBadge({ status }: { status: DocumentOut["status"] }) {
  const { label, className } = CONFIG[status] ?? CONFIG.error;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
        className,
      )}
    >
      {status === "processing" && <Loader2 className="h-3 w-3 animate-spin" />}
      {status === "ready" && <CheckCircle2 className="h-3 w-3" />}
      {status === "error" && <XCircle className="h-3 w-3" />}
      {label}
    </span>
  );
}
