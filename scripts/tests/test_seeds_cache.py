"""The seed cache must be keyed by SOURCE, not by chunk key alone.

Two runs over different volumes sharing one --cache directory silently served each other's chunks: regenerating
PHerc0358's seeds into PHerc0826's cache produced 90 IDENTICAL seeds with PHerc0826's level-3 shape and every
per-slice n_pred, under PHerc0358's own prediction URL in the header. It was caught only because two different
scrolls cannot have identical numbers.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import seeds


def test_two_sources_get_different_cache_namespaces():
    a = seeds._cache_ns("https://x/PHerc0826/.../20250821151701-surface.zarr")
    b = seeds._cache_ns("https://x/PHerc0358/.../20250821151737-surface.zarr")
    assert a != b


def test_the_namespace_is_stable_and_ignores_a_trailing_slash():
    u = "https://x/PHerc0826/pred.zarr"
    assert seeds._cache_ns(u) == seeds._cache_ns(u + "/") == seeds._cache_ns(u)


def test_cached_chunks_land_under_the_namespace(tmp_path, monkeypatch):
    calls = []

    class R:
        status_code = 200
        content = b"payload"

        def raise_for_status(self):
            return None

    monkeypatch.setattr(seeds.requests, "get", lambda url, timeout=None, **k: (calls.append(url), R())[1])
    base = "https://x/PHerc0826/pred.zarr"
    seeds._get(base, "3/2/0/0", str(tmp_path))
    ns = seeds._cache_ns(base)
    assert (tmp_path / ns / "3_2_0_0").read_bytes() == b"payload"
    # a second source with the same chunk key must not read the first one's file
    other = "https://x/PHerc0358/pred.zarr"
    seeds._get(other, "3/2/0/0", str(tmp_path))
    assert (tmp_path / seeds._cache_ns(other) / "3_2_0_0").exists()
    assert len(calls) == 2, "the second source must fetch, not reuse the first source's cached chunk"
