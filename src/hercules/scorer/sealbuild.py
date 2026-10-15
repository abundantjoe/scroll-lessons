# Provenance: Project HERCULES | owner the owner | [id removed]
"""Build a window-set seal from three sealers' answers (RULES.md DECL-SEAL, DECL-D1-A3 item 3).

Sealer answers use the prompt-P item schema (one image per item, reported in "left").
Each naming's centre and box are mapped from image px to the window frame of the key
(``image_to_levelled_window_px``: [y, x] = M [iy, ix, 1]); items whose id is not in the key
(the key sheet) are ignored.  Per window, ``sealpos.make_seal_with_labels`` gives the seal
letters (>= 2 of 3 within 150 px; firm = 3/3 or 2/3 both firm; label-centroid positions
where a label mask is given).  Blank windows get ``{"blank": true, "letters": []}``.
``summary`` holds only counts and agreement statistics (what the orchestrator may see).
"""
from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from hercules.scorer.letters import normalize_letter
from hercules.scorer.sealpos import make_seal_with_labels


def _affine(m: Any) -> np.ndarray:
    a = np.asarray(m, dtype=float)
    if a.shape == (3, 3):
        a = a[:2]
    if a.shape != (2, 3):
        raise ValueError(f"affine must be 2x3 or 3x3, got {a.shape}")
    return a


def _map(M: np.ndarray, x: float, y: float) -> tuple[float, float]:
    yy, xx = M @ np.array([float(y), float(x), 1.0])
    return float(xx), float(yy)


def map_answer(answer: Mapping[str, Any], key_images: Mapping[str, Mapping[str, Any]]) -> dict[str, list[dict]]:
    """-> {window: [namings in the window frame with ch, x, y, conf, box]} for one sealer."""
    out: dict[str, list[dict]] = {}
    for item in answer.get("items", []):
        img = key_images.get(item.get("id"))
        if img is None:
            continue
        M = _affine(img["image_to_levelled_window_px"])
        lst = out.setdefault(img["window"], [])
        for n in (item.get("left") or {}).get("letters", []):
            x, y = _map(M, n["x"], n["y"])
            d = {"ch": n.get("ch"), "x": x, "y": y, "conf": n.get("conf")}
            b = n.get("box")
            if isinstance(b, (list, tuple)) and len(b) == 4:
                try:
                    c = [_map(M, b[0], b[1]), _map(M, b[2], b[3])]
                    d["box"] = [min(c[0][0], c[1][0]), min(c[0][1], c[1][1]), max(c[0][0], c[1][0]), max(c[0][1], c[1][1])]
                except (TypeError, ValueError):
                    pass
            lst.append(d)
    return out


def build_seal(
    answers: Mapping[str, Mapping[str, Any]],
    key_images: Mapping[str, Mapping[str, Any]],
    windows: list[str],
    labels: Mapping[str, np.ndarray] | None = None,
    blank_windows: list[str] = (),
    organizer_affines: Mapping[str, Any] | None = None,
) -> tuple[dict, dict]:
    """answers: {sealer_id: answer}; exactly 3 sealers.  Returns (seal, summary)."""
    if len(answers) != 3:
        raise ValueError("a seal needs exactly 3 sealers")
    mapped = {sid: map_answer(a, key_images) for sid, a in answers.items()}
    seal: dict[str, Any] = {"windows": {}}
    summary: dict[str, Any] = {"windows": {}}
    for w in sorted(windows):
        per = {sid: [n for n in mapped[sid].get(w, []) if n.get("conf") in ("firm", "tentative")] for sid in sorted(mapped)}
        lab = None if labels is None else labels.get(w)
        letters, stats = make_seal_with_labels(per, lab)
        if organizer_affines is not None and w in organizer_affines:
            A = _affine(organizer_affines[w])
            for l in letters:
                l["org_x"], l["org_y"] = _map(A, l["x"], l["y"])
        seal["windows"][w] = {"blank": False, "letters": letters}
        summary["windows"][w] = {
            "n_letters": stats["n_letters"], "n_firm": stats["n_firm"], "n_agree_3": stats["n_agree_3"],
            "n_agree_2": stats["n_agree_2"], "n_label_positioned": stats.get("n_label_positioned", 0),
            "per_sealer": {sid: {k: v for k, v in s.items()} for sid, s in stats["per_sealer"].items()},
            "n_unknown_letters_named": sum(1 for sid in per for n in per[sid] if normalize_letter(n.get("ch")) is None),
        }
    for w in sorted(blank_windows):
        seal["windows"][w] = {"blank": True, "letters": []}
        summary["windows"][w] = {"blank": True}
    summary["S_prime"] = sum(v["n_letters"] for k, v in summary["windows"].items() if not v.get("blank"))
    summary["n_firm_total"] = sum(v["n_firm"] for k, v in summary["windows"].items() if not v.get("blank"))
    return seal, summary
