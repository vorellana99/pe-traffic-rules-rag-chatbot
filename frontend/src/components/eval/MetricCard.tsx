import { cn } from "@/lib/utils";

interface Props {
  label: string;
  sublabel: string;
  value: number; // 0..1
}

function toneFor(value: number): string {
  if (value >= 0.8) return "text-emerald-500";
  if (value >= 0.6) return "text-amber-500";
  return "text-destructive";
}

export function MetricCard({ label, sublabel, value }: Props) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="text-sm font-medium">{label}</div>
      <div className="text-xs text-muted-foreground">{sublabel}</div>
      <div className={cn("mt-3 text-3xl font-semibold", toneFor(value))}>
        {(value * 100).toFixed(1)}
        <span className="text-lg text-muted-foreground">%</span>
      </div>
    </div>
  );
}
