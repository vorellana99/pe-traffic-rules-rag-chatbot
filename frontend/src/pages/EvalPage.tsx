import { useQuery } from "@tanstack/react-query";
import { BarChart3 } from "lucide-react";

import { MetricCard } from "@/components/eval/MetricCard";
import { api, type EvalMetrics } from "@/lib/api";
import { cn } from "@/lib/utils";

const METRICS: { key: keyof EvalMetrics; label: string; sublabel: string }[] = [
  {
    key: "faithfulness",
    label: "Faithfulness",
    sublabel: "Fidelidad al contexto",
  },
  {
    key: "answer_relevancy",
    label: "Answer Relevancy",
    sublabel: "Relevancia de la respuesta",
  },
  {
    key: "context_precision",
    label: "Context Precision",
    sublabel: "Precisión del contexto",
  },
];

function metricTone(value: number): string {
  if (value >= 0.8) return "text-emerald-500";
  if (value >= 0.6) return "text-amber-500";
  return "text-destructive";
}

export function EvalPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["eval-results"],
    queryFn: api.getEvalResults,
  });

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-4xl space-y-6 p-6">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Evaluación</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Métricas de calidad del sistema RAG (RAGAS) sobre el dataset de
            evaluación.
          </p>
        </div>

        {isLoading && (
          <p className="text-sm text-muted-foreground">Cargando…</p>
        )}

        {isError && (
          <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-2 text-sm text-destructive">
            No se pudieron cargar los resultados.
          </div>
        )}

        {!isLoading && !isError && !data && (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-20 text-center">
            <BarChart3 className="mb-4 h-10 w-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Aún no hay resultados de evaluación.
            </p>
            <p className="mt-1 text-xs text-muted-foreground/70">
              Ejecuta <code className="rounded bg-muted px-1">make eval</code>{" "}
              para generarlos.
            </p>
          </div>
        )}

        {data && (
          <>
            <div className="grid gap-4 sm:grid-cols-3">
              {METRICS.map((m) => (
                <MetricCard
                  key={m.key}
                  label={m.label}
                  sublabel={m.sublabel}
                  value={data.global[m.key]}
                />
              ))}
            </div>

            <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground">
              <span>
                Modelos: {data.models.llm} · {data.models.embedding}
              </span>
              <span>
                Generado: {new Date(data.timestamp).toLocaleString("es-PE")}
              </span>
              <span>{data.per_question.length} preguntas</span>
            </div>

            <div className="overflow-hidden rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead className="border-b border-border bg-muted/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <tr>
                    <th className="px-4 py-2 font-medium">Pregunta</th>
                    <th className="px-4 py-2 text-right font-medium">Faith.</th>
                    <th className="px-4 py-2 text-right font-medium">
                      Ans. Rel.
                    </th>
                    <th className="px-4 py-2 text-right font-medium">
                      Ctx. Prec.
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.per_question.map((row, i) => (
                    <tr
                      key={i}
                      className="border-b border-border last:border-0 hover:bg-muted/20"
                    >
                      <td className="max-w-[24rem] px-4 py-3">
                        {row.question}
                      </td>
                      {(
                        [
                          "faithfulness",
                          "answer_relevancy",
                          "context_precision",
                        ] as const
                      ).map((k) => (
                        <td
                          key={k}
                          className={cn(
                            "px-4 py-3 text-right tabular-nums",
                            metricTone(row[k]),
                          )}
                        >
                          {(row[k] * 100).toFixed(0)}%
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
