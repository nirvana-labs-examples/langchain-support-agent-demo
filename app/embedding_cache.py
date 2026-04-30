"""
Pre-computed embedding cache shared by app.ingest and benchmarks.

Cache files live in data/.cache/ and are split into ≤48 MB parts so they
can be committed to git. Use benchmarks.precompute to regenerate.
"""

import json
from pathlib import Path

import numpy as np

from app.config import settings

_CACHE_DIR = Path(__file__).parent.parent / "data" / ".cache"
_MAX_PART_BYTES = 48 * 1024 * 1024


def cache_key(dataset: str) -> dict[str, object]:
    return {
        "dataset": dataset,
        "embedding_model": settings.embedding_model,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
    }


def _key_path(dataset: str) -> Path:
    return _CACHE_DIR / f"{dataset}_key.json"


def _vector_parts(dataset: str) -> list[Path]:
    return sorted(_CACHE_DIR.glob(f"{dataset}_vectors.part*.npy"))


def _payload_parts(dataset: str) -> list[Path]:
    return sorted(_CACHE_DIR.glob(f"{dataset}_payloads.part*.json"))


def is_cached(dataset: str) -> bool:
    key_path = _key_path(dataset)
    if not key_path.exists() or not _vector_parts(dataset):
        return False
    stored_key: object = json.loads(key_path.read_text())  # pyright: ignore[reportAny]
    return stored_key == cache_key(dataset)


def load_cache(dataset: str) -> tuple[list[list[float]], list[dict[str, object]]]:
    vector_parts = _vector_parts(dataset)
    payload_parts = _payload_parts(dataset)
    vectors: list[list[float]] = np.concatenate(  # pyright: ignore[reportAny]
        [np.load(p) for p in vector_parts]
    ).tolist()
    payloads: list[dict[str, object]] = []
    for p in payload_parts:
        chunk: list[dict[str, object]] = json.loads(p.read_text())  # pyright: ignore[reportAny]
        payloads.extend(chunk)
    return vectors, payloads


def save_cache(dataset: str, vectors: np.ndarray, payloads: list[dict[str, object]]) -> None:  # pyright: ignore[reportMissingTypeArgument,reportUnknownParameterType]
    _CACHE_DIR.mkdir(exist_ok=True)

    for old in list(_CACHE_DIR.glob(f"{dataset}_vectors.part*.npy")) + \
               list(_CACHE_DIR.glob(f"{dataset}_payloads.part*.json")):
        old.unlink()

    dims = vectors.shape[1]
    rows_per_part = max(1, _MAX_PART_BYTES // (dims * 4))
    num_parts = (len(vectors) + rows_per_part - 1) // rows_per_part

    for i, start in enumerate(range(0, len(vectors), rows_per_part)):
        end = min(start + rows_per_part, len(vectors))
        np.save(_CACHE_DIR / f"{dataset}_vectors.part{i:02d}.npy", vectors[start:end])
        _ = (_CACHE_DIR / f"{dataset}_payloads.part{i:02d}.json").write_text(
            json.dumps(payloads[start:end])
        )

    _ = _key_path(dataset).write_text(json.dumps(cache_key(dataset)))

    total_mb = vectors.nbytes / 1_000_000
    num_parts_str = str(num_parts)
    total_mb_str = f"{total_mb:.1f}"
    print(f"  Saved in {num_parts_str} part(s) ({total_mb_str} MB total)")
