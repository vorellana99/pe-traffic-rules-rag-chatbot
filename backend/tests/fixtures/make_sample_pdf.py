"""Genera un PDF fixture pequeño y determinista para los tests de chunking.

Página 1: texto largo (varios artículos) para forzar múltiples chunks.
Página 2: texto corto (un artículo).

Regenerar:  python tests/fixtures/make_sample_pdf.py
"""
from pathlib import Path

import fitz  # PyMuPDF

OUTPUT = Path(__file__).with_name("sample.pdf")

PAGE_1 = (
    "Artículo 1. Ámbito de aplicación.\n\n"
    + (
        "El presente reglamento regula el tránsito de vehículos y personas en las "
        "vías públicas terrestres. Sus disposiciones son de observancia obligatoria "
        "en todo el territorio nacional. "
    )
    * 11
    + "\n\nArtículo 2. Definiciones.\n\n"
    + (
        "Para efectos del presente reglamento se entiende por vía toda calzada "
        "destinada a la circulación de vehículos. Se entiende por conductor a la "
        "persona habilitada para conducir un vehículo automotor. "
    )
    * 11
)

PAGE_2 = (
    "Artículo 3. Límites de velocidad.\n\n"
    "En zona urbana el límite de velocidad es de sesenta kilómetros por hora, "
    "salvo señalización en contrario."
)


def _write_page(doc: fitz.Document, text: str) -> None:
    page = doc.new_page()
    rect = fitz.Rect(40, 40, 555, 800)
    # insert_textbox devuelve el espacio vertical sobrante (>=0) si el texto
    # cupo, o un número negativo si desbordó (en cuyo caso no se renderiza).
    leftover = page.insert_textbox(rect, text, fontsize=9, fontname="helv")
    if leftover < 0:
        raise RuntimeError(
            f"El texto no cabe en la página (faltan {-leftover:.0f}pt). "
            "Reduce el contenido o el fontsize."
        )


def main() -> None:
    doc = fitz.open()
    _write_page(doc, PAGE_1)
    _write_page(doc, PAGE_2)
    doc.save(OUTPUT)
    doc.close()
    print(f"Escrito: {OUTPUT}")


if __name__ == "__main__":
    main()
