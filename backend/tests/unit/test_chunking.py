"""Tests unitarios de parsing y chunking sobre un PDF fixture pequeño."""
from pathlib import Path

import pytest

from app.services.ingestion_service import (
    ParsedChunk,
    chunk_pages,
    extract_pages,
    parse_pdf,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sample.pdf"


@pytest.fixture
def pdf_bytes() -> bytes:
    return FIXTURE.read_bytes()


def test_extract_pages_count(pdf_bytes: bytes) -> None:
    pages = extract_pages(pdf_bytes)
    assert len(pages) == 2
    assert pages[0][0] == 1 and pages[1][0] == 2
    assert "Artículo 1" in pages[0][1]
    assert "Artículo 3" in pages[1][1]


def test_parse_pdf_reports_page_count(pdf_bytes: bytes) -> None:
    parsed = parse_pdf(pdf_bytes)
    assert parsed.pages == 2
    assert len(parsed.chunks) >= 2


def test_chunks_preserve_correct_page(pdf_bytes: bytes) -> None:
    chunks = parse_pdf(pdf_bytes).chunks

    # Todo chunk pertenece a una página válida.
    assert all(c.page in (1, 2) for c in chunks)

    # El texto de la página 1 (larga) genera varios chunks, todos con page == 1.
    page1_chunks = [c for c in chunks if c.page == 1]
    assert len(page1_chunks) >= 2
    assert any("Artículo 1" in c.content for c in page1_chunks)

    # La página 2 aporta al menos un chunk con su contenido propio.
    page2_chunks = [c for c in chunks if c.page == 2]
    assert len(page2_chunks) >= 1
    assert any("Artículo 3" in c.content for c in page2_chunks)


def test_positions_are_sequential(pdf_bytes: bytes) -> None:
    chunks = parse_pdf(pdf_bytes).chunks
    positions = [c.position for c in chunks]
    assert positions == list(range(len(chunks)))


def test_empty_pages_are_skipped() -> None:
    chunks = chunk_pages([(1, "  \n  "), (2, "Artículo 9. Contenido real.")])
    assert len(chunks) == 1
    assert chunks[0] == ParsedChunk(
        content="Artículo 9. Contenido real.", page=2, position=0
    )
