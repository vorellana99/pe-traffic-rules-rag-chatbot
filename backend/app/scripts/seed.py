"""Seed del corpus: ingesta vía API todos los PDFs de `data/seed_pdfs/`.

Se ejecuta DENTRO del contenedor `api` (`make seed` ->
`docker compose exec api python -m app.scripts.seed`), por eso llama a la API
en `localhost:8000`. Sube cada PDF y espera a que quede `ready` antes del
siguiente. Si la carpeta está vacía, falla con un mensaje instructivo.

NO descarga PDFs de ningún sitio: usa los archivos ya colocados manualmente.
"""
import sys
import time
from pathlib import Path

import httpx

# La carpeta va montada (read-only) en el contenedor api (ver docker-compose.yml).
SEED_DIR = Path("/app/data/seed_pdfs")
# El script corre dentro del contenedor api, así que la API está en localhost.
API_BASE = "http://localhost:8000/api"

POLL_INTERVAL_S = 8
MAX_WAIT_S = 120 * 60  # el embedding corre en CPU: seed puede tardar bastante

MISSING_MSG = """\
[seed] No se encontraron PDFs en data/seed_pdfs/.

Coloca manualmente (NO se descargan en el script) los documentos del corpus:
  1. TUO del Reglamento Nacional de Tránsito (D.S. 016-2009-MTC y modificatorias).
  2. Tabla de tipificación de infracciones y sanciones (Anexo I del RNT).
  3. Reglamento Nacional del Sistema de Emisión de Licencias de Conducir
     (D.S. 007-2016-MTC).

Fuentes: portal del MTC (www.gob.pe/mtc) o el SPIJ del Ministerio de Justicia
(spij.minjus.gob.pe). Ver data/seed_pdfs/README.md.
"""


def _upload(client: httpx.Client, pdf: Path) -> str:
    resp = client.post(
        f"{API_BASE}/documents",
        files={"file": (pdf.name, pdf.read_bytes(), "application/pdf")},
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _wait_ready(client: httpx.Client, doc_id: str, name: str) -> str:
    waited = 0
    while waited < MAX_WAIT_S:
        resp = client.get(f"{API_BASE}/documents/{doc_id}")
        resp.raise_for_status()
        data = resp.json()
        status = data["status"]
        if status == "ready":
            print(
                f"  ✓ {name}: ready "
                f"({data['chunk_count']} chunks, {data['pages']} páginas)"
            )
            return status
        if status == "error":
            print(
                f"  ✗ {name}: error -> {data.get('error_message')}", file=sys.stderr
            )
            return status
        print(f"  … {name}: {status} ({waited}s)", flush=True)
        time.sleep(POLL_INTERVAL_S)
        waited += POLL_INTERVAL_S
    print(f"  ✗ {name}: timeout tras {MAX_WAIT_S}s", file=sys.stderr)
    return "timeout"


def main() -> int:
    pdfs = sorted(SEED_DIR.glob("*.pdf"))
    if not pdfs:
        print(MISSING_MSG, file=sys.stderr)
        return 1

    print(f"[seed] {len(pdfs)} PDF(s) en {SEED_DIR}:")
    for pdf in pdfs:
        print(f"   - {pdf.name}")

    ready = 0
    with httpx.Client(timeout=120) as client:
        for pdf in pdfs:
            print(f"→ Subiendo {pdf.name} ...", flush=True)
            doc_id = _upload(client, pdf)
            if _wait_ready(client, doc_id, pdf.name) == "ready":
                ready += 1

    print(f"\n[seed] Resumen: {ready}/{len(pdfs)} documentos ready.")
    # DoD: el seed es exitoso si deja >= 2 documentos ready.
    return 0 if ready >= 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
