#!/usr/bin/env bash
# loop.sh — Ejecuta Claude Code en loop sobre PLAN.md hasta completar todas las tareas.
#
# Uso:
#   ./loop.sh            # corre hasta terminar el plan (o hasta MAX_ITERATIONS)
#   ./loop.sh 5          # corre como máximo 5 iteraciones
#
# Requisitos: Claude Code instalado y autenticado; ejecutar desde la raíz del repo (donde está PLAN.md).
# ADVERTENCIA: usa --dangerously-skip-permissions (el agente ejecuta comandos sin pedir confirmación).
# Úsalo solo en este repo aislado. Revisa los commits entre sesiones.

set -euo pipefail

MAX_ITERATIONS="${1:-30}"
LOG_DIR=".loop-logs"
mkdir -p "$LOG_DIR"

PROMPT='Lee PLAN.md completo y CLAUDE.md. Identifica la PRIMERA tarea sin marcar [ ] en orden estricto.
Implementa SOLO esa tarea por completo. Ejecuta su comando de Verificación tal como está escrito en PLAN.md.
Solo si la verificación pasa: marca la tarea como [x] en PLAN.md y haz un commit atómico.
Si falla, arregla el problema y reintenta la verificación antes de terminar.
Al completar UNA tarea (verificada y commiteada), detente y resume brevemente qué hiciste.'

pending_tasks() {
  grep -c '^- \[ \]' PLAN.md || true
}

for i in $(seq 1 "$MAX_ITERATIONS"); do
  remaining="$(pending_tasks)"
  if [ "$remaining" -eq 0 ]; then
    echo "✅ Plan completo: no quedan tareas pendientes en PLAN.md."
    exit 0
  fi

  echo "════════════════════════════════════════════════════"
  echo "🔁 Iteración $i/$MAX_ITERATIONS — tareas pendientes: $remaining"
  echo "════════════════════════════════════════════════════"

  before="$remaining"
  log_file="$LOG_DIR/iter-$(printf '%03d' "$i")-$(date +%Y%m%d-%H%M%S).log"

  # -p: modo no interactivo. Salida completa guardada en log por iteración.
  claude -p "$PROMPT" --dangerously-skip-permissions 2>&1 | tee "$log_file"

  after="$(pending_tasks)"
  if [ "$after" -ge "$before" ]; then
    echo "⚠️  La iteración $i no marcó ninguna tarea como completada."
    echo "    Revisa $log_file — probablemente una verificación está fallando."
    echo "    Corrige manualmente (o con una sesión interactiva de claude) y relanza ./loop.sh"
    exit 1
  fi

  echo "✔ Tarea completada en iteración $i (pendientes: $before → $after)"
done

echo "⏸ Alcanzado MAX_ITERATIONS=$MAX_ITERATIONS con $(pending_tasks) tareas pendientes."
echo "  Relanza ./loop.sh para continuar."
