# Provenance: Project HERCULES | owner the owner | [id removed]
"""Canonical JSON and hashing.

Two canonical encodings, both with sorted keys, compact separators and no NaN/Infinity:

* ``canonical_json`` -- UTF-8 text (``ensure_ascii=False``); REFUSES any string or key
  containing a Unicode format character (category Cf, e.g. zero-width space, BOM).  Used
  for sealed files and for score outputs.
* ``hash_json`` -- the same but ASCII-escaped (``ensure_ascii=True``).  Used only to hash
  scorer INPUTS, which may legitimately contain arbitrary reader-supplied characters
  (they are escaped, hence visible, in the hashed text).
"""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from typing import Any

from .constants import FORBIDDEN_CATEGORY


def contains_forbidden(text: str) -> bool:
    """True if ``text`` contains a Unicode format (Cf) character."""
    return any(unicodedata.category(c) == FORBIDDEN_CATEGORY for c in text)


def _check(obj: Any, path: str, forbid_cf: bool) -> None:
    if obj is None or isinstance(obj, bool):
        return
    if isinstance(obj, str):
        if forbid_cf and contains_forbidden(obj):
            raise ValueError(f"format (Cf) character in string at {path}")
        return
    if isinstance(obj, int):
        return
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError(f"non-finite float at {path}")
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise ValueError(f"non-string key {k!r} at {path}")
            if forbid_cf and contains_forbidden(k):
                raise ValueError(f"format (Cf) character in key at {path}")
            _check(v, f"{path}/{k}", forbid_cf)
        return
    if isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _check(v, f"{path}/{i}", forbid_cf)
        return
    raise ValueError(f"type {type(obj).__name__} at {path} is not JSON-canonical")


def canonical_json(obj: Any) -> str:
    """Sorted-key, compact, UTF-8 JSON text; raises ValueError on Cf characters or NaN."""
    _check(obj, "$", forbid_cf=True)
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def canonical_bytes(obj: Any) -> bytes:
    try:
        return canonical_json(obj).encode("utf-8")
    except UnicodeEncodeError as exc:  # lone surrogates
        raise ValueError(f"not encodable as UTF-8: {exc}") from exc


def hash_json(obj: Any) -> str:
    """ASCII-escaped canonical JSON used for hashing scorer inputs."""
    _check(obj, "$", forbid_cf=False)
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
