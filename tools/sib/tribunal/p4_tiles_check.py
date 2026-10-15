# Provenance: Project HERCULES | owner the owner | [id removed]
"""REAL-TRIB-2 (iv): Paris 4 P4-B tile checks. Numbers only for the real tiles (grid.json,
manifest.json, tiles.jsonl of the p4-tiles-a/b branches; no PNG is opened); planted pixel faults on
synthetic arrays only.

    python tools/sib/tribunal/p4_tiles_check.py P4_DIR OUT.json [--trials 200]
P4_DIR holds a/grid.json and b/{grid.json,manifest.json,tiles.jsonl} copied by `git show`.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from hercules.pipeline.window import voxel_size_from_metadata
from hercules.tribunal import tiles as TL

META_KEY = "PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr/metadata.json"


def fetch_meta(dst: Path) -> tuple[float, str]:
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        boto3.client("s3", config=Config(signature_version=UNSIGNED)).download_file(
            "vesuvius-challenge-open-data", META_KEY, str(dst))
    return voxel_size_from_metadata(dst) / 1000.0, hashlib.sha256(dst.read_bytes()).hexdigest()


def manifest_faults(n, tiles, vox_mm, rng, trials):
    """Numeric faults in copies of the real manifest; each must fail its intended check."""
    out = {}

    def grid_fail(nn, check):
        return any(r["check"] == check and not r["passed"] for r in TL.check_grid(nn, voxel_mm_metadata=vox_mm))

    def tile_fail(tt, nn, cond):
        return any(cond in r["failed"] for r in TL.check_tiles(nn, tt))

    cases = {
        "wrong_T": lambda: (dict(n, T=n["T"] + int(rng.choice([-3, -2, -1, 1, 2, 3]))), None, ("grid", "T_rule")),
        "wrong_px_per_mm": lambda: (_ppm_fault(n, rng), None, ("grid", "ppm_recomputed")),
        "wrong_voxel": lambda: (dict(n, voxel_mm=float(rng.choice([0.002399, 0.0024 * 1.001, 0.009362]))), None,
                                ("grid", "voxel_from_metadata")),
        "offset_8px_origin": lambda: (n, _tile_fault(tiles, rng, "origin"), ("tile", "origin_or_extent")),
        "wrong_valid_fraction": lambda: (n, _tile_fault(tiles, rng, "vf"), ("tile", "valid_fraction_vs_valid_px")),
        "swapped_rc": lambda: (n, _tile_fault(tiles, rng, "swap"), ("tile", "origin_or_extent")),
        "extra_png_chunk": lambda: (n, _tile_fault(tiles, rng, "chunk"), ("tile", "png_chunks")),
    }
    for name, make in cases.items():
        caught = 0
        for _ in range(trials):
            nn, tt, (kind, check) = make()
            caught += grid_fail(nn, check) if kind == "grid" else tile_fail(tt, nn, check)
        out[name] = {"n": trials, "caught": int(caught)}
    return out


def _ppm_fault(n, rng):
    f = float(rng.choice([0.97, 0.98, 0.99, 1.01, 1.02, 1.03]))
    ppm = n["px_per_mm"] * f
    return dict(n, px_per_mm=ppm, T=int(round(20 * ppm)))  # consistent T: only the recomputation catches it


def _tile_fault(tiles, rng, kind):
    tt = copy.deepcopy(list(tiles))
    i = int(rng.integers(len(tt)))
    t = tt[i]
    if kind == "origin":
        d = int(rng.choice([-8, 8]))
        t["canvas_rows"] = [t["canvas_rows"][0] + d, t["canvas_rows"][1] + d]
    elif kind == "vf":
        t["valid_fraction"] = t["valid_fraction"] + float(rng.choice([-0.01, 0.01]))
    elif kind == "swap":
        cands = [k for k, x in enumerate(tt) if x["r"] != x["c"]]
        t = tt[cands[int(rng.integers(len(cands)))]]
        t["r"], t["c"] = t["c"], t["r"]
    elif kind == "chunk":
        t["png_chunks"] = list(t["png_chunks"]) + ["tEXt"]
    return tt


def synthetic_pixel_suite(rng, trials):
    """Planted pixel faults on synthetic prediction canvases (never real tiles)."""
    res = {k: {"n": 0, "caught": 0, "diagnosed_as": {}} for k in
           ("clean", "offset8", "rot90", "wrong_px_per_mm", "mirror_lr", "n0_rotation_missing")}
    side = 256
    for t in range(trials):
        T = int(rng.integers(1600, 2400))
        H, W = 2 * T + int(rng.integers(0, T)), 3 * T + int(rng.integers(0, T))
        tex = gaussian_filter(rng.standard_normal((H // 4, W // 4)), 3.0)
        tex = np.kron(tex, np.ones((4, 4)))[:H, :W]
        tex = gaussian_filter(tex, 2.0)
        canvas = np.clip((tex - tex.mean()) / (tex.std() + 1e-12) * 50 + 90, 0, 255).astype(np.uint8)
        valid = gaussian_filter(rng.standard_normal((H // 64, W // 64)), 1.5)
        valid = np.kron(valid > -0.8, np.ones((64, 64), bool))[:H, :W]
        valid = np.pad(valid, ((0, H - valid.shape[0]), (0, W - valid.shape[1])))
        r, c = int(rng.integers(0, 2)), int(rng.integers(0, 3))
        good = TL.expected_tile(canvas, valid, r, c, T, side, 0)
        d = int(rng.choice([-8, 8]))
        ax = int(rng.integers(2))
        sub = np.roll(canvas, -d, axis=ax)
        vsub = np.roll(valid, -d, axis=ax)
        f = float(rng.choice([0.95, 0.97, 0.98, 0.99, 1.01, 1.02, 1.03, 1.05]))
        faults = {
            "clean": (good, 0),
            "offset8": (TL.expected_tile(sub, vsub, r, c, T, side, 0), 0),
            "rot90": (np.ascontiguousarray(np.rot90(good, -1)), 0),
            "wrong_px_per_mm": (TL.expected_tile(canvas, valid, r, c, int(round(T * f)), side, 0), 0),
            "mirror_lr": (np.ascontiguousarray(good[:, ::-1]), 0),
            "n0_rotation_missing": (good, 90),  # an N0 tile keyed 90 cw but delivered unrotated
        }
        for name, (tile, rot) in faults.items():
            v = TL.verify_tile(tile, canvas, valid, r, c, T, side=side, rotation=rot)
            res[name]["n"] += 1
            res[name]["caught"] += int(not v["passed"])
            if not v["passed"] and "diagnosis" in v:
                b = v["diagnosis"]["best"].split("_")[0]
                res[name]["diagnosed_as"][b] = res[name]["diagnosed_as"].get(b, 0) + 1
    return res


def main():
    p4, out = Path(sys.argv[1]), Path(sys.argv[2])
    trials = int(sys.argv[sys.argv.index("--trials") + 1]) if "--trials" in sys.argv else 200
    rng = np.random.default_rng(20260926)
    vox_mm, meta_sha = fetch_meta(Path("/work/tribunal/meta") / META_KEY.replace("/", "_"))
    res = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
           "rule": "REAL-TRIB-2 (iv), PREREG.md", "not_opened": "no PNG tile or prediction pixel was opened",
           "metadata": {"key": META_KEY, "sha256": meta_sha, "voxel_mm": vox_mm}, "real": {}}
    for s in ("a", "b"):
        g = json.loads((p4 / s / "grid.json").read_text())
        n = TL.normalize_grid(g)
        tl = [json.loads(x) for x in (p4 / s / "tiles.jsonl").read_text().splitlines() if x.strip()] \
            if (p4 / s / "tiles.jsonl").exists() else []
        gridc = TL.check_grid(n, voxel_mm_metadata=vox_mm)
        tc = TL.check_tiles(n, tl)
        res["real"][s] = {"segment": g.get("segment"), "normalized": {k: v for k, v in n.items() if k != "valid_matrix"},
                          "grid_checks": gridc, "n_tiles_listed": len(tl),
                          "tiles_failing": [x for x in tc if x["failed"]], "count_checks": TL.check_counts(n, tl),
                          "all_passed": all(x["passed"] for x in gridc) and not any(x["failed"] for x in tc)}
    na, nb = res["real"]["a"]["normalized"], res["real"]["b"]["normalized"]
    res["cross_segment"] = {"px_per_mm": [na["px_per_mm"], nb["px_per_mm"]], "T": [na["T"], nb["T"]],
                            "formulas": "a: scale / (median of all valid edges x voxel); b: scale / (median of "
                                        "row+col valid edges x voxel) - same definition, per-segment values"}
    nb_full = TL.normalize_grid(json.loads((p4 / "b" / "grid.json").read_text()))
    tlb = [json.loads(x) for x in (p4 / "b" / "tiles.jsonl").read_text().splitlines() if x.strip()]
    res["manifest_faults"] = manifest_faults(nb_full, tlb, vox_mm, rng, trials)
    res["pixel_faults_synthetic"] = synthetic_pixel_suite(rng, trials)
    allc = all(v["caught"] == v["n"] for v in res["manifest_faults"].values()) and all(
        v["caught"] == v["n"] for k, v in res["pixel_faults_synthetic"].items() if k != "clean")
    res["verdict"] = "PASS" if allc and res["pixel_faults_synthetic"]["clean"]["caught"] == 0 else "FAIL"
    out.write_text(json.dumps(res, indent=1, sort_keys=True, default=float) + "\n")
    print(json.dumps({"verdict": res["verdict"], "real_all_passed": {s: res["real"][s]["all_passed"] for s in "ab"},
                      "manifest_faults": res["manifest_faults"],
                      "pixel": {k: (v["caught"], v["n"]) for k, v in res["pixel_faults_synthetic"].items()}}, indent=1))


if __name__ == "__main__":
    main()
