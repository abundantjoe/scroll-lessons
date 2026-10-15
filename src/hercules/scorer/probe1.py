# Provenance: Project HERCULES | owner the owner | [id removed]
"""READ-CAL PROBE-1 scorer (DECL-READCAL-PROBE1): SG item 1 statistics on REF.

Reader answers use the prompt-P item schema, one image per item (reported in "left").
Every naming is mapped to the common state-A levelled window frame with the key's
affine ``[y, x] = M [iy, ix, 1]``; within one reader, same-kind namings closer than
DEDUP_RADIUS in that frame (overlapping tiles) are merged (first kept). Agreement:
hercules.scorer.consensus.agreed_letters (150 px, >= 2 of 3 readers).
"""
import json
import sys

import numpy as np

from hercules.scorer.consensus import agreed_letters, identity_shuffle_null
from hercules.scorer.letters import normalize_letter

DEDUP_RADIUS = 150.0
AGREE_RADIUS = 150.0
N_PERM = 2000


def map_namings(answer, key_images):
    """-> {window: [naming dicts in window frame]} for one reader answer."""
    out = {}
    for item in answer.get("items", []):
        img = key_images.get(item.get("id"))
        if img is None:
            continue
        M = np.asarray(img["image_to_levelled_window_px"], dtype=float)
        for n in (item.get("left") or {}).get("letters", []):
            ch = normalize_letter(n.get("ch"))
            if ch is None:
                continue
            y, x = M @ np.array([float(n["y"]), float(n["x"]), 1.0])
            out.setdefault(img["window"], []).append(
                {"ch": ch, "x": float(x), "y": float(y), "conf": n.get("conf", "tentative")})
    return {w: dedup(v) for w, v in out.items()}


def dedup(namings):
    kept = []
    for n in namings:
        if any(k["ch"] == n["ch"] and np.hypot(k["x"] - n["x"], k["y"] - n["y"]) < DEDUP_RADIUS
               for k in kept):
            continue
        kept.append(n)
    return kept


def score_arm(per_reader, windows):
    """per_reader: {reader_id: {window: namings}} -> per-window and summed statistics."""
    res, tot = {}, {"agreed": 0, "agreed_firm": 0, "named": 0}
    for w in windows:
        by_reader = {r: v.get(w, []) for r, v in per_reader.items()}
        groups = agreed_letters(by_reader, radius=AGREE_RADIUS, min_readers=2)
        firm = sum(1 for g in groups if sum(1 for m in g["members"] if m["conf"] == "firm") >= 2)
        named = sum(len(v) for v in by_reader.values())
        null = identity_shuffle_null(by_reader, n_perm=N_PERM, radius=AGREE_RADIUS) if named else None
        res[w] = {"agreed": len(groups), "agreed_firm": firm, "named_total": named,
                  "shuffle_p": (str(null["p"]) if null else None)}
        tot["agreed"] += len(groups)
        tot["agreed_firm"] += firm
        tot["named"] += named
    return {"per_window": res, "total": tot}


if __name__ == "__main__":
    # usage: probe1.py KEY ANSWERS_JSON  (answers: {arm: {reader_id: answer_obj}})
    key = json.load(open(sys.argv[1]))
    answers = json.load(open(sys.argv[2]))
    imgs = key["images"]
    windows = sorted({v["window"] for v in imgs.values()})
    out = {arm: score_arm({r: map_namings(a, imgs) for r, a in rd.items()}, windows)
           for arm, rd in answers.items()}
    print(json.dumps(out, indent=1))
