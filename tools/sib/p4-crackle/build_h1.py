"""P4-H tile builder (RULES.md DECL-P4-9 items 1 and 3) on the E1 (= M2a) grid of 20260623141924-w010-027.
Run ONLY after logs/sib/p4-crackle/gate.json says GATE PASS.

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only: no image, tile or CT pixel is ever displayed or printed. PNG bytes are hashed and
written, never opened. Grid, tile list, valid_fraction and frac_outside are taken verbatim from
p4-tiles-b e1a1/manifest.json (the E1 grid, T = 8872, eligible 60 tiles).

Usage:
  python build_h1.py <scratch_dir> rows <r> [<r> ...]   build rows, commit + push per row
  python build_h1.py <scratch_dir> merge                 manifest.json from rows/*.json (+ M2a AUC report)
"""
import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import sys
import time

import cv2
import numpy as np
import requests
import tifffile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import crackle as C  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "src"))
from hercules.display.builder import png_bytes  # noqa: E402

SCR = sys.argv[1]
OUT = os.path.join(REPO, "logs/sib/p4-crackle/h1")
TB = "origin/claude/gifted-bell-gavnl5-sib-p4-tiles-b"
TA = "origin/claude/gifted-bell-gavnl5-sib-p4-tiles-a"
SEG = "20260623141924-w010-027"
SV = f"PHercParis4/segments/{SEG}/surface-volumes/1.129um-0.23m-78keV-volume-20260608103018-L1.zarr"
XKEY = f"PHercParis4/segments/{SEG}/mesh/20260623141924-on-20260608103018-1.129um.tifxyz/x.tif"
PX_UM = 20000.0 / C.OUT_SIDE
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
BR = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
ATTR = os.environ.get("P4C_ATTR", "")


def log(**kw):
    kw = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **kw}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "runs.jsonl"), "a") as f:
        f.write(json.dumps(kw) + "\n")
    print(json.dumps(kw), flush=True)


def git_bytes(ref_path):
    return subprocess.run(["git", "show", ref_path], cwd=REPO, capture_output=True, check=True).stdout


def sh(*cmd):
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)


def commit_push(paths, msg):
    sh("git", "add", *paths)
    sh("git", "commit", "-q", "-m", msg + "\n\n" + PROV + ("\n\n" + ATTR if ATTR else ""))
    for i in range(5):
        p = sh("git", "push", "-q", "origin", BR)
        if p.returncode == 0:
            log(run="h1-push", msg=msg, commit=sh("git", "rev-parse", "--short", "HEAD").stdout.strip())
            return
        time.sleep(2 ** (i + 1))
    log(run="h1-push", status="FAILED", stderr=p.stderr[-400:])


def e1_manifest():
    b = git_bytes(f"{TB}:logs/sib/p4-tiles-b/e1a1/manifest.json")
    return json.loads(b), hashlib.sha256(b).hexdigest()


def grid_valid(man):
    p = os.path.join(SCR, "w010_valid.npy")
    want = [i for i in man["inputs"] if i["key"] == XKEY][0]["sha256"]
    if os.path.exists(p):
        return np.load(p)
    b = requests.get(f"{C.BUCKET}/{XKEY}", timeout=900).content
    assert hashlib.sha256(b).hexdigest() == want
    tp = os.path.join(SCR, "w010_x.tif")
    open(tp, "wb").write(b)
    del b
    x = tifffile.imread(tp)
    os.remove(tp)
    v = (x != -1) & np.isfinite(x)
    np.save(p, v)
    return v


def gate_passed():
    g = json.load(open(os.path.join(REPO, "logs/sib/p4-crackle/gate.json")))
    return g["decision"]["GATE"] == "PASS"


def build_rows(rows):
    assert gate_passed(), "DECL-P4-9 item 2: the gate did not pass; no title-strip tile may be computed"
    man, man_sha = e1_manifest()
    T, s = man["T_px"], 10
    assert T == 8872
    za = requests.get(f"{C.BUCKET}/{SV}/0/.zarray", timeout=60).json()
    assert za["shape"][0] == C.N_SLICES and za["chunks"] == [116, 128, 128] and za["compressor"] is None
    H, W = za["shape"][1], za["shape"][2]
    gv = grid_valid(man)
    os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "masks"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "rows"), exist_ok=True)
    for r in rows:
        tl = [t for t in man["tiles"] if t["r"] == r]
        recs = []
        with cf.ThreadPoolExecutor(1) as pre:
            fut = pre.submit(C.fetch_tile, SV, H, W, T, r, tl[0]["c"])
            for i, t in enumerate(tl):
                c = t["c"]
                slab, finfo = fut.result()
                if i + 1 < len(tl):
                    fut = pre.submit(C.fetch_tile, SV, H, W, T, r, tl[i + 1]["c"])
                e, pos, mv, info = C.compute_tile(slab, gv, s, T, r, c)
                del slab
                u8, lo, hi = C.display_u8(e, pos)
                b = png_bytes(u8)
                chunks, k = [], 8
                while k < len(b):
                    n = int.from_bytes(b[k:k + 4], "big")
                    chunks.append(b[k + 4:k + 8].decode("ascii"))
                    k += 12 + n
                assert set(chunks) <= {"IHDR", "IDAT", "IEND"}, chunks
                name = f"{SEG}_r{r}_c{c}.png"
                open(os.path.join(OUT, "tiles", name), "wb").write(b)
                np.savez_compressed(os.path.join(OUT, "masks", f"r{r}_c{c}.npz"),
                                    pos=np.packbits(pos), mv=np.packbits(mv), shape=np.array(pos.shape))
                rec = {"r": r, "c": c, "file": f"tiles/{name}", "canvas_rows": [r * T, (r + 1) * T],
                       "canvas_cols": [c * T, (c + 1) * T], "valid_fraction": t["valid_fraction"],
                       "frac_mesh_points_outside_1129_volume": t["frac_outside"],
                       "png_sha256": hashlib.sha256(b).hexdigest(), "png_bytes": len(b),
                       "masks_file": f"masks/r{r}_c{c}.npz",
                       "stats": dict(info, stretch_p1=lo, stretch_p99=hi, pos_fraction_1068=float(pos.mean()),
                                     energy_median_pos=float(np.median(e[pos])) if pos.any() else None)}
                recs.append(rec)
                log(run="h1-tile", tile=f"r{r}_c{c}", fetch=finfo["fetch_secs"], compute=info["compute_secs"])
        rj = os.path.join(OUT, "rows", f"row{r}.json")
        json.dump({"provenance": PROV, "row": r, "e1a1_manifest_sha256": man_sha, "tiles": recs}, open(rj, "w"), indent=1)
        commit_push([os.path.join(OUT, "tiles"), os.path.join(OUT, "masks"), rj, os.path.join(OUT, "runs.jsonl")],
                    f"p4-crackle h1: row {r} ({len(recs)} P4-H tiles, DECL-P4-9)")


def merge():
    assert gate_passed()
    man, man_sha = e1_manifest()
    recs = []
    for f in sorted(os.listdir(os.path.join(OUT, "rows"))):
        d = json.load(open(os.path.join(OUT, "rows", f)))
        assert d["e1a1_manifest_sha256"] == man_sha
        recs += d["tiles"]
    recs.sort(key=lambda t: (t["r"], t["c"]))
    want = sorted((t["r"], t["c"]) for t in man["tiles"])
    assert [(t["r"], t["c"]) for t in recs] == want, "tile set differs from the 60 E1-grid eligible tiles"
    for t in recs:
        assert hashlib.sha256(open(os.path.join(OUT, t["file"]), "rb").read()).hexdigest() == t["png_sha256"]
    outside = [t["frac_mesh_points_outside_1129_volume"] for t in recs]
    m = {"provenance": PROV, "serves": "RULES.md DECL-P4-9 item 3 (P4-H tiles); sibling task p4-crackle",
         "segment": SEG, "material": "P4-H crackle channel of the 1.129 um L1 surface volume (level 0)",
         "surface_volume": SV, "grid": "E1 = P4-D M2a grid, p4-tiles-b e1a1/manifest.json", "e1a1_manifest_sha256": man_sha,
         "T_px": man["T_px"], "tile_grid_rows_cols": man["tile_grid_rows_cols"],
         "channel": {"slices": f"{C.SL0}..{C.SL1 - 1} (centre 58, +-18.06 um)", "dog_sigma_px": [C.SIG1, C.SIG2],
                     "energy": "mean over slices of DoG^2", "display_grid": "cv2.INTER_AREA T -> 1068",
                     "stretch": "DECL-P4-5-A1 over 1068 px fully mesh-valid with 17-slice CT mean > 0; 0 elsewhere"},
         "display": {"side_px": 1068, "px_per_mm": 53.4, "encoder": "builder.png_bytes; IHDR/IDAT/IEND only"},
         "eligibility": man["eligibility"], "tiles_eligible": len(recs),
         "frac_mesh_points_outside_1129_volume": {"max": max(outside), "mean": float(np.mean(outside))},
         "gate": "logs/sib/p4-crackle/gate.json (PASS)",
         "viewing": "no image, tile or CT pixel was opened, displayed or described by the builder",
         "tiles": recs, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(m, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    rep = m2a_auc(recs)
    json.dump(rep, open(os.path.join(OUT, "m2a_auc_report.json"), "w"), indent=1)
    log(run="h1-merge", tiles=len(recs), m2a_auc=rep["aligned"]["pooled_auc"], m2a_rot90=rep["rot90"]["pooled_auc"])


def m2a_auc(recs):
    """Report only (DECL-P4-9 item 3): the gate AUC method on the title strip vs M2a."""
    ma = json.loads(git_bytes(f"{TA}:logs/sib/p4-tiles-a/m2a/manifest.json"))
    mt = {(t["r"], t["c"]): t for t in ma["tiles"]}
    data = {}
    for t in recs:
        k = (t["r"], t["c"])
        u8 = cv2.imdecode(np.frombuffer(open(os.path.join(OUT, t["file"]), "rb").read(), np.uint8), cv2.IMREAD_UNCHANGED)
        z = np.load(os.path.join(OUT, t["masks_file"]))
        n = int(np.prod(z["shape"]))
        pos = np.unpackbits(z["pos"])[:n].reshape(z["shape"]).astype(bool)
        mv = np.unpackbits(z["mv"])[:n].reshape(z["shape"]).astype(bool)
        b = git_bytes(f"{TA}:logs/sib/p4-tiles-a/m2a/{mt[k]['file']}")
        assert hashlib.sha256(b).hexdigest() == mt[k]["png_sha256"], k
        pred = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_UNCHANGED)
        assert pred.shape == u8.shape
        data[k] = (u8, pos, mv, pred, mt[k]["png_sha256"])
    out = {"provenance": PROV, "note": "report only; no claim (DECL-P4-9 item 3)", "m2a_ref": TA}
    for mode in ("aligned", "rot90"):
        am, pr = {}, {}
        for k, (u8, pos, mv, pred, _) in data.items():
            pr[k] = pred if mode == "aligned" else np.rot90(pred, 1)
            am[k] = pos & mv & (mv if mode == "aligned" else np.rot90(mv, 1))
        pool = np.concatenate([pr[k][am[k]] for k in data]).astype(np.float64)
        p90, p50 = np.percentile(pool, [90, 50])
        HI, HB, rows = np.zeros(256), np.zeros(256), []
        hs = {}
        for k, (u8, *_r) in data.items():
            ink, bg = C.class_masks(pr[k], am[k], p90, p50, PX_UM)
            hi_, hb_ = np.bincount(u8[ink], minlength=256), np.bincount(u8[bg], minlength=256)
            hs[k] = (hi_, hb_)
            HI, HB = HI + hi_, HB + hb_
            rows.append({"tile": f"r{k[0]}_c{k[1]}", "n_ink": int(ink.sum()), "n_bg": int(bg.sum()),
                         "auc": C.auc_hist(hi_, hb_)})
        keys = list(data)
        rng = np.random.default_rng(20260927)
        bo = np.array([C.auc_hist(sum(hs[keys[i]][0] for i in ix), sum(hs[keys[i]][1] for i in ix))
                       for ix in (rng.integers(0, len(keys), len(keys)) for _ in range(2000))])
        bo = bo[np.isfinite(bo)]
        out[mode] = {"p90": float(p90), "p50": float(p50), "pooled_auc": C.auc_hist(HI, HB),
                     "n_ink": int(HI.sum()), "n_bg": int(HB.sum()),
                     "bootstrap_ci95": [float(np.percentile(bo, 2.5)), float(np.percentile(bo, 97.5))],
                     "per_tile": rows}
    return out


if __name__ == "__main__":
    if sys.argv[2] == "rows":
        build_rows([int(a) for a in sys.argv[3:]])
    else:
        merge()
