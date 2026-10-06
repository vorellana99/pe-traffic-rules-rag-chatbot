import { Trash2 } from "lucide-react";
import { useState } from "react";

import { Dropzone } from "@/components/documents/Dropzone";
import { StatusBadge } from "@/components/documents/StatusBadge";
import { Button } from "@/components/ui/button";
import { useDocuments } from "@/hooks/useDocuments";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function DocumentsPage() {
  const { query, upload, remove } = useDocuments();
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const documents = query.data ?? [];

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-4xl space-y-6 p-6">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Documentos</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Sube PDFs de normativa; se indexan automáticamente para el chat.
          </p>
        </div>

        <Dropzone
          onFile={(f) => upload.mutate(f)}
          disabled={upload.isPending}
        />

        {upload.isError && (
          <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-2 text-sm text-destructive">
            No se pudo subir el archivo. ¿Es un PDF válido?
          </div>
        )}

        <div className="overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-muted/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-2 font-medium">Nombre</th>
                <th className="px-4 py-2 font-medium">Páginas</th>
                <th className="px-4 py-2 font-medium">Chunks</th>
                <th className="px-4 py-2 font-medium">Estado</th>
                <th className="px-4 py-2 font-medium">Fecha</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-10 text-center text-sm text-muted-foreground"
                  >
                    {query.isLoading
                      ? "Cargando…"
                      : "Aún no hay documentos. Sube un PDF para empezar."}
                  </td>
                </tr>
              )}
              {documents.map((doc) => (
                <tr
                  key={doc.id}
                  className="border-b border-border last:border-0 hover:bg-muted/20"
                >
                  <td className="max-w-[16rem] truncate px-4 py-3 font-medium">
                    {doc.filename}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {doc.pages ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {doc.chunk_count}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={doc.status} />
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {formatDate(doc.created_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {confirmId === doc.id ? (
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => {
                            remove.mutate(doc.id);
                            setConfirmId(null);
                          }}
                        >
                          Eliminar
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setConfirmId(null)}
                        >
                          Cancelar
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Eliminar documento"
                        onClick={() => setConfirmId(doc.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
