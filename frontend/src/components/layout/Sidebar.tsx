import { BarChart3, FileText, MessagesSquare } from "lucide-react";
import { NavLink } from "react-router-dom";

import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Chat", icon: MessagesSquare, end: true },
  { to: "/documentos", label: "Documentos", icon: FileText, end: false },
  { to: "/evaluacion", label: "Evaluación", icon: BarChart3, end: false },
];

export function Sidebar() {
  return (
    <aside className="flex w-64 flex-col border-r border-border bg-card">
      <div className="border-b border-border p-4">
        <h1 className="text-lg font-semibold tracking-tight">TránsitoRAG</h1>
        <p className="text-xs text-muted-foreground">
          Normativa de tránsito · Perú
        </p>
      </div>

      <nav className="space-y-1 p-2">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-2 flex-1 overflow-y-auto px-2">
        <p className="px-3 py-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Conversaciones
        </p>
        <p className="px-3 text-xs text-muted-foreground/70">
          Sin conversaciones aún.
        </p>
      </div>

      <div className="border-t border-border p-3">
        <p className="text-[10px] leading-tight text-muted-foreground/70">
          Proyecto de demostración. No constituye asesoría legal; la normativa
          puede haber cambiado.
        </p>
      </div>
    </aside>
  );
}
