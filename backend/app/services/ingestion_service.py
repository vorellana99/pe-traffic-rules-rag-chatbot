"""Parsing de PDFs (PyMuPDF) y chunking (RecursiveCharacterTextSplitter).

Extrae texto por página y lo trocea respetando la estructura normativa,
conservando `page` y `position` en cada chunk (ver sección 6 del PLAN).
"""
from dataclasses import dataclass

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

# chunk_size ~800 tokens, overlap 150 tokens; aprox. caracteres = tokens x 4.
CHARS_PER_TOKEN = 4
CHUNK_SIZE_TOKENS = 800
CHUNK_OVERLAP_TOKENS = 150

# Separadores que respetan la estructura normativa (de mayor a menor prioridad).
SEPARATORS = ["\n\nArtículo", "\n\n", "\n", ". ", " ", ""]


@dataclass
class ParsedChunk:
    content: str
    page: int
    position: int


@dataclass
class ParsedDocument:
    pages: int
    chunks: list[ParsedChunk]


def _build_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE_TOKENS * CHARS_PER_TOKEN,
        chunk_overlap=CHUNK_OVERLAP_TOKENS * CHARS_PER_TOKEN,
        separators=SEPARATORS,
        keep_separator=True,
    )


def extract_pages(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """Devuelve [(numero_de_pagina (1-indexed), texto)] para cada página."""
    pages: list[tuple[int, str]] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for index, page in enumerate(doc, start=1):
            pages.append((index, page.get_text("text")))
    return pages


def chunk_pages(pages: list[tuple[int, str]]) -> list[ParsedChunk]:
    """Trocea cada página por separado para preservar el número de página.

    `position` es un índice global creciente en el orden del documento.
    """
    splitter = _build_splitter()
    chunks: list[ParsedChunk] = []
    position = 0
    for page_number, text in pages:
        text = (text or "").strip()
        if not text:
            continue
        for piece in splitter.split_text(text):
            piece = piece.strip()
            if not piece:
                continue
            chunks.append(
                ParsedChunk(content=piece, page=page_number, position=position)
            )
            position += 1
    return chunks


def parse_pdf(pdf_bytes: bytes) -> ParsedDocument:
    """Parsea un PDF completo: extrae páginas y las trocea."""
    pages = extract_pages(pdf_bytes)
    return ParsedDocument(pages=len(pages), chunks=chunk_pages(pages))
