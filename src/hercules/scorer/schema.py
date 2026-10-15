# Provenance: Project HERCULES | owner the owner | [id removed]
"""Spec A: validation of reader outputs against configs/reader_output.schema.json.

``validate_reader_output`` only reports; it never repairs.  The caller discards any reader
whose output is not valid.
"""

from __future__ import annotations

import functools
import json
import math
import unicodedata
from pathlib import Path
from typing import Any

import jsonschema

from .constants import INPUT_UNICODE_FORM

# Repository layout: <root>/src/hercules/scorer/schema.py -> <root>/configs/...
REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "configs" / "reader_output.schema.json"


@functools.lru_cache(maxsize=1)
def _schema_text() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


def load_schema() -> dict:
    """Return a fresh copy of the reader output JSON Schema (draft 2020-12)."""
    return json.loads(_schema_text())


@functools.lru_cache(maxsize=1)
def _validator() -> jsonschema.Draft202012Validator:
    schema = load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _path_str(path) -> str:
    return "/" + "/".join(str(p) for p in path)


def _finite(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _extra_checks(obj: dict) -> list[tuple[str, str]]:
    """Checks JSON Schema cannot express.  Only run on schema-valid objects."""
    errors: list[tuple[str, str]] = []
    seen: dict[str, int] = {}
    for i, item in enumerate(obj["items"]):
        if item["id"] in seen:
            errors.append((f"/items/{i}/id", f"duplicate item id {item['id']!r} (first at /items/{seen[item['id']]})"))
        else:
            seen[item["id"]] = i
        for side in ("left", "right"):
            for j, letter in enumerate(item[side]["letters"]):
                base = f"/items/{i}/{side}/letters/{j}"
                ch = letter["ch"]
                if len(unicodedata.normalize(INPUT_UNICODE_FORM, ch)) != 1:
                    errors.append((base + "/ch", f"ch must be exactly one character after {INPUT_UNICODE_FORM}"))
                for key in ("x", "y"):
                    if not _finite(letter[key]):
                        errors.append((f"{base}/{key}", "must be a finite number"))
                for k, v in enumerate(letter["box"]):
                    if not _finite(v):
                        errors.append((f"{base}/box/{k}", "must be a finite number"))
    return errors


def validate_reader_output(obj: Any) -> tuple[bool, list[str]]:
    """Validate one reader's output.

    Returns ``(ok, errors)``; ``errors`` is a deterministic, sorted list of
    ``"<json-pointer>: <message>"`` strings, empty when ``ok``.
    """
    raw = [(_path_str(e.absolute_path), e.message) for e in _validator().iter_errors(obj)]
    if not raw:
        raw = _extra_checks(obj)
    errors = [f"{p}: {m}" for p, m in sorted(set(raw))]
    return (not errors, errors)
