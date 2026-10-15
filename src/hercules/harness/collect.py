# Provenance: Project HERCULES | owner the owner | [id removed]
"""Scorer-side collection of sealed agent answers (DECL-HARNESS-A1).

Only aggregate numbers leave this module's CLI; letter content never is printed.
"""
import json
import os

from hercules.scorer.keyaccess import decrypt_answer_logged
from hercules.scorer.schema import validate_reader_output

PICK_MIN_LETTERS = 5  # "at least 5 nameable letters" (DECL-READCAL, DECL-SEAL)


def load_answer(path, purpose, decrypt=decrypt_answer_logged):
    """Decrypt one sealed answer; returns the object (never printed)."""
    return decrypt(path, purpose)


def validate_picker(obj):
    """Picker answers: {"windows": {uuid: {"rows": "Y"|"N", "letters": [...]}}}."""
    if not isinstance(obj, dict) or not isinstance(obj.get("windows"), dict):
        return False
    for v in obj["windows"].values():
        if not isinstance(v, dict) or v.get("rows") not in ("Y", "N"):
            return False
        if not isinstance(v.get("letters"), list):
            return False
    return True


def picker_counts(obj):
    """uuid -> (n_letters, n_firm, rows) from a validated picker answer."""
    out = {}
    for u, v in obj["windows"].items():
        letters = [x for x in v["letters"] if isinstance(x, dict) and x.get("ch")]
        out[u] = (len(letters), sum(1 for x in letters if x.get("conf") == "firm"), v["rows"])
    return out


def select_windows(counts, key, target=8, max_per_segment=3, min_letters=PICK_MIN_LETTERS):
    """Deterministic READ-CAL selection: windows with >= min_letters named, ranked by
    (n_letters, n_firm, uuid), at most max_per_segment per segment, no two selected
    windows overlapping on the same segment canvas. key: uuid -> {segment, y0, x0, h, w}."""
    ranked = sorted((u for u, c in counts.items() if c[0] >= min_letters and u in key),
                    key=lambda u: (-counts[u][0], -counts[u][1], u))
    chosen, per_seg = [], {}
    for u in ranked:
        k = key[u]
        if per_seg.get(k["segment"], 0) >= max_per_segment:
            continue
        clash = any(key[c]["segment"] == k["segment"]
                    and abs(key[c]["y0"] - k["y0"]) < k["h"] and abs(key[c]["x0"] - k["x0"]) < k["w"]
                    for c in chosen)
        if clash:
            continue
        chosen.append(u)
        per_seg[k["segment"]] = per_seg.get(k["segment"], 0) + 1
        if len(chosen) >= target:
            break
    return chosen


def validate_reader(obj):
    ok, _ = validate_reader_output(obj)
    return ok
