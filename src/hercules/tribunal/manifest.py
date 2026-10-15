# Provenance: Project HERCULES | owner the owner | [id removed]
"""Input manifest for the batch-control builders (the orchestrator chooses the material).

Manifest (JSON)::

    {"manifest_version": 1, "batch_id": str,
     "voxel": {"metadata_source": "<volume url>/metadata.json", "voxel_um": float},
     "display": {"window": "raw", "display_scale": 0.5},
     "positive_canaries": [{"canary_id", "tile": {"scroll", "segment", "window": {y0, x0, h, w}},
                            "ref_map": {"source", "sha256"}, "sigma_mm", "ref_ceiling": {"recall", "rows_found"},
                            "seal_sha256"}],
     "baits": [{"bait_id", "kind": wrong_order|blank|null_arm, "tile": {...},
                "map": {"source", "sha256"} | null, "blank_mode": null|constant|pixel_shuffle|phase_scramble,
                "derive_from": canary_id (blank synthesised from that canary's map)}],
     "mirror_canaries": {"glyphs": "EKRCGBN", "letter_height_mm", "sigma_mm", "canvas_hw", "font_sha256"}}

Rules enforced by :func:`validate_manifest`: positive canaries come from clean PHerc0139
only (plan section 6.8.7, until fold K exists); no source may be PHerc0841 or any of the 23
eligible scrolls (data/catalogue/eligible_products.json); every numeric field the build
needs is present (``for_build``); every source carries a sha256 that the loader's bytes
must match.
"""

from __future__ import annotations

import functools
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from . import controls as K
from .validity import panel_area_cm2

REPO_ROOT = Path(__file__).resolve().parents[3]
ELIGIBLE_JSON = REPO_ROOT / "data" / "catalogue" / "eligible_products.json"
POSITIVE_SCROLLS = ("PHerc0139",)
ALWAYS_FORBIDDEN = ("PHerc0841",)


@functools.lru_cache(maxsize=1)
def eligible_scrolls() -> frozenset:
    d = json.loads(ELIGIBLE_JSON.read_text(encoding="utf-8"))
    return frozenset(v["scroll"] for v in d["volumes"])


def forbidden_scrolls() -> frozenset:
    return eligible_scrolls() | frozenset(ALWAYS_FORBIDDEN)


def _num(v, lo=None, hi=None) -> bool:
    ok = isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    return ok and (lo is None or v >= lo) and (hi is None or v <= hi)


def validate_manifest(m: Mapping[str, Any], *, for_build: bool) -> list[str]:
    """Return a list of errors (empty = valid). ``for_build`` also requires every value
    the build needs (sigma, ceilings, sha256) to be filled in."""
    err: list[str] = []
    bad = forbidden_scrolls()
    if m.get("manifest_version") != 1:
        err.append("manifest_version must be 1")
    vox = m.get("voxel", {})
    if not str(vox.get("metadata_source", "")).endswith("/metadata.json"):
        err.append("voxel.metadata_source must be the volume's metadata.json")
    if for_build and not _num(vox.get("voxel_um"), 0.1, 100):
        err.append("voxel.voxel_um missing (take it from metadata.json)")
    pos = m.get("positive_canaries", [])
    if not pos:
        err.append("no positive canary")
    ids = set()
    for c in pos:
        cid = c.get("canary_id")
        ids.add(cid)
        sc = c.get("tile", {}).get("scroll")
        if sc not in POSITIVE_SCROLLS:
            err.append(f"canary {cid}: scroll {sc!r} not allowed for positives (clean PHerc0139 only)")
        if sc in bad:
            err.append(f"canary {cid}: scroll {sc!r} is forbidden")
        if for_build:
            if not _num(c.get("sigma_mm"), 0.0, 2.0):
                err.append(f"canary {cid}: sigma_mm missing")
            rc = c.get("ref_ceiling") or {}
            if not _num(rc.get("recall"), 1e-9, 1.0) or not _num(rc.get("rows_found"), 0.0, 1.0):
                err.append(f"canary {cid}: ref_ceiling recall/rows_found missing")
            if not c.get("ref_map", {}).get("sha256"):
                err.append(f"canary {cid}: ref_map sha256 missing")
    for b in m.get("baits", []):
        bid = b.get("bait_id")
        if b.get("kind") not in K.BAIT_KINDS:
            err.append(f"bait {bid}: kind {b.get('kind')!r}")
        sc = b.get("tile", {}).get("scroll")
        if sc in bad:
            err.append(f"bait {bid}: scroll {sc!r} is forbidden")
        if b.get("derive_from") is not None:
            if b.get("kind") != "blank" or b.get("blank_mode") not in K.BLANK_MODES:
                err.append(f"bait {bid}: derive_from needs kind blank and a blank_mode")
            if b["derive_from"] not in ids:
                err.append(f"bait {bid}: derive_from {b['derive_from']!r} is not a canary id")
        elif for_build and not (b.get("map") or {}).get("sha256"):
            err.append(f"bait {bid}: map sha256 missing")
    if not m.get("baits"):
        err.append("no bait")
    mc = m.get("mirror_canaries")
    if not mc:
        err.append("no mirror canaries")
    else:
        if set(mc.get("glyphs", "")) != set(K.MIRROR_GLYPHS):
            err.append("mirror glyphs must be E K R C G B N")
        if for_build and mc.get("font_sha256") != K.font_sha256():
            err.append("mirror font sha256 differs from the installed font")
    return err


Loader = Callable[[Mapping[str, Any]], tuple[np.ndarray, str]]


def build_from_manifest(m: Mapping[str, Any], loader: Loader, out_dir: str | Path, *,
                        rng: np.random.Generator) -> dict:
    """Build and write every control image. ``loader(source)`` returns (array on the
    canvas, sha256 of the source bytes); a hash mismatch aborts. Returns the scorer-side
    keys and the control skeleton for validity.score_batch (item ids are assigned when
    the harness builds items; the seal comes from the orchestrator)."""
    errs = validate_manifest(m, for_build=True)
    if errs:
        raise ValueError("manifest invalid: " + "; ".join(errs))
    vox = float(m["voxel"]["voxel_um"])
    ppm = 1000.0 / vox
    disp = m.get("display", {})
    win, scale = disp.get("window", "raw"), float(disp.get("display_scale", 0.5))
    built, maps, controls = [], {}, []

    def load(src):
        arr, sha = loader(src)
        if sha != src["sha256"]:
            raise ValueError(f"source hash mismatch for {src.get('source')}")
        return arr

    for c in m["positive_canaries"]:
        ref = load(c["ref_map"])
        maps[c["canary_id"]] = ref
        img, key = K.build_positive_canary(ref, sigma_mm=c["sigma_mm"], px_per_mm=ppm, display_scale=scale,
                                           window=win, canary_id=c["canary_id"],
                                           source={"tile": c["tile"], "ref_map": c["ref_map"]})
        built.append((img, key))
        controls.append({"type": "positive_canary", "control_id": c["canary_id"], "item_ids": [],
                         "ref_ceiling": c["ref_ceiling"], "seal_sha256": c.get("seal_sha256")})
    for b in m["baits"]:
        if b.get("derive_from") is not None:
            src = maps[b["derive_from"]]
        else:
            src = load(b["map"])
        img, key = K.build_bait(b["kind"], src, display_scale=scale, window=win, bait_id=b["bait_id"],
                                blank_mode=b.get("blank_mode"), rng=rng,
                                source={"tile": b.get("tile"), "map": b.get("map"), "derive_from": b.get("derive_from")})
        built.append((img, key))
        h, w = np.asarray(src).shape
        controls.append({"type": "bait", "control_id": b["bait_id"], "kind": b["kind"], "item_ids": [],
                         "area_cm2": panel_area_cm2(h, w, vox)})
    mc = m["mirror_canaries"]
    for img, key in K.build_mirror_canaries(glyphs=tuple(mc["glyphs"]), letter_height_mm=mc["letter_height_mm"],
                                            px_per_mm=ppm, canvas_hw=tuple(mc["canvas_hw"]),
                                            sigma_mm=mc.get("sigma_mm", 0.0), display_scale=scale, window=win, rng=rng):
        built.append((img, key))
    keys = K.write_controls(built, out_dir)
    for k in keys:
        if k["type"] == "mirror_canary":
            controls.append({"type": "mirror_canary", "control_id": k["control_uid"], "item_id": None,
                             "mirrored": k["mirrored"], "image": k["image"]["name"]})
    return {"keys": keys, "controls": controls, "voxel_um": vox}
