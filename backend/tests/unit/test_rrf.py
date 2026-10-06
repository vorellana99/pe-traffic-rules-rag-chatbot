"""Test unitario de la fusión Reciprocal Rank Fusion (función pura, sin DB)."""
import uuid

import pytest

from app.services.retrieval_service import _rrf_fuse


def test_rrf_fuse_prioritizes_items_in_multiple_lists() -> None:
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    # `a` aparece primero en ambas listas -> debe quedar primero.
    fused = _rrf_fuse([[a, b], [a, c]], k=60)
    ids = [chunk_id for chunk_id, _ in fused]
    scores = dict(fused)

    assert ids[0] == a
    assert set(ids) == {a, b, c}
    assert scores[a] > scores[b]
    assert scores[a] == pytest.approx(2 / 61)
