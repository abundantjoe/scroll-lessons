"""P4-H validation gate (RULES.md DECL-P4-9 item 2), exactly as pre-registered in
logs/sib/p4-crackle/gate_plan.json (commit 44b77c3).

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only: no image, tile or CT pixel is ever displayed or printed. The M2b prediction PNGs are
read from git as bytes, sha256-checked and decoded to arrays.

Usage: python gate.py <scratch_dir> compute|analyse
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
SCR = sys.argv[1]
OUT = os.path.join(REPO, "logs/sib/p4-crackle")
TB = "origin/claude/gifted-bell-gavnl5-sib-p4-tiles-b"
SEG = "20260623142658-w028-037"
SV = f"PHercParis4/segments/{SEG}/surface-volumes/1.129um-0.23m-78keV-volume-20260608103018-L1.zarr"
XKEY = f"PHercParis4/segments/{SEG}/mesh/20260623142658-on-20260608103018-1.129um.tifxyz/x.tif"
PX_UM = 20000.0 / C.OUT_SIDE
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"


def log(**kw):
    kw = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **kw}
    with open(os.path.join(OUT, "runs.jsonl"), "a") as f:
        f.write(json.dumps(kw) + "\n")
    print(json.dumps(kw), flush=True)


def git_bytes(ref_path):
    return subprocess.run(["git", "show", ref_path], cwd=REPO, capture_output=True, check=True).stdout


def load_plan():
    plan = json.load(open(os.path.join(OUT, "gate_plan.json")))
    man_b = git_bytes(f"{TB}:logs/sib/p4-tiles-b/m2b/manifest.json")
    assert hashlib.sha256(man_b).hexdigest() == plan["control"]["m2b_manifest_sha256"]
    man = json.loads(man_b)
    tiles = [tuple(int(v) for v in k[1:].split("_c")) for k in plan["tile_draw"]["tiles"]]
    return plan, man, tiles


def grid_valid():
    p = os.path.join(SCR, "w028_x.npy")
    if os.path.exists(p):
        return np.load(p), json.load(open(p + ".json"))
    b = requests.get(f"{C.BUCKET}/{XKEY}", timeout=600).content
    sha = hashlib.sha256(b).hexdigest()
    tp = os.path.join(SCR, "x.tif")
    open(tp, "wb").write(b)
    del b
    x = tifffile.imread(tp)
    os.remove(tp)
    v = (x != -1) & np.isfinite(x)
    del x
    rec = {"key": XKEY, "sha256": sha}
    np.save(p, v)
    json.dump(rec, open(p + ".json", "w"))
    return v, rec


def compute():
    plan, man, tiles = load_plan()
    za = requests.get(f"{C.BUCKET}/{SV}/0/.zarray", timeout=60).json()
    assert za["shape"][0] == C.N_SLICES and za["chunks"] == [116, 128, 128] and za["compressor"] is None
    H, W = za["shape"][1], za["shape"][2]
    assert [H, W] == man["canvas_shape"]
    T, s = man["T_px"], 10
    gv, xrec = grid_valid()
    assert list(gv.shape) == man["grid_shape"]
    assert xrec["sha256"] == [i for i in man["inputs"] if i["key"] == XKEY][0]["sha256"]
    rv = C.verify_range_read(SV, (tiles[0][0] * T + T // 2) // 128, (tiles[0][1] * T + T // 2) // 128)
    assert rv.get("range_equal_full_slices"), rv
    json.dump({"zarray": za, "mesh_x": xrec, "range_check": rv}, open(os.path.join(SCR, "gate_inputs.json"), "w"))
    log(run="gate-compute", status="started", tiles=len(tiles), range_check=rv)
    todo = [t for t in tiles if not os.path.exists(os.path.join(SCR, f"gate_r{t[0]}_c{t[1]}.npz"))]
    with cf.ThreadPoolExecutor(1) as pre:
        fut = pre.submit(C.fetch_tile, SV, H, W, T, *todo[0]) if todo else None
        for i, (r, c) in enumerate(todo):
            slab, finfo = fut.result()
            if i + 1 < len(todo):
                fut = pre.submit(C.fetch_tile, SV, H, W, T, *todo[i + 1])
            e, pos, mv, info = C.compute_tile(slab, gv, s, T, r, c)
            del slab
            info.update(finfo)
            np.savez(os.path.join(SCR, f"gate_r{r}_c{c}.npz"), e=e, pos=pos, mv=mv, info=json.dumps(info))
            log(run="gate-tile", tile=f"r{r}_c{c}", **info)


def analyse():
    plan, man, tiles = load_plan()
    mt = {(t["r"], t["c"]): t for t in man["tiles"]}
    inp = json.load(open(os.path.join(SCR, "gate_inputs.json")))
    per, preds = [], {}
    for r, c in tiles:
        z = np.load(os.path.join(SCR, f"gate_r{r}_c{c}.npz"))
        e, pos, mv, info = z["e"], z["pos"], z["mv"], json.loads(str(z["info"]))
        b = git_bytes(f"{TB}:logs/sib/p4-tiles-b/m2b/{mt[(r, c)]['file']}")
        assert hashlib.sha256(b).hexdigest() == mt[(r, c)]["png_sha256"], (r, c)
        pred = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_UNCHANGED)
        assert pred.shape == (C.OUT_SIDE, C.OUT_SIDE) and pred.dtype == np.uint8
        u8, lo, hi = C.display_u8(e, pos)
        preds[(r, c)] = dict(e=e, u8=u8, pos=pos, mv=mv, pred=pred, info=info, lo=lo, hi=hi,
                             png_sha256=mt[(r, c)]["png_sha256"])
    res = {}
    for mode in ("aligned", "rot90"):
        am, pr = {}, {}
        for k, d in preds.items():
            if mode == "aligned":
                pr[k], mvp = d["pred"], d["mv"]
            else:
                pr[k], mvp = np.rot90(d["pred"], 1), np.rot90(d["mv"], 1)
            am[k] = d["pos"] & d["mv"] & mvp
        pool = np.concatenate([pr[k][am[k]] for k in preds]).astype(np.float64)
        p90, p50 = np.percentile(pool, [90, 50])
        hists, rows = {}, []
        for k, d in preds.items():
            ink, bg = C.class_masks(pr[k], am[k], p90, p50, PX_UM)
            hi_ = np.bincount(d["u8"][ink], minlength=256)
            hb_ = np.bincount(d["u8"][bg], minlength=256)
            hists[k] = (hi_, hb_)
            tp = pr[k][am[k]].astype(np.float64)
            t90, t50 = (np.percentile(tp, [90, 50]) if tp.size else (np.nan, np.nan))
            ink2, bg2 = C.class_masks(pr[k], am[k], t90, t50, PX_UM) if tp.size else (ink & False, bg & False)
            rows.append({"tile": f"r{k[0]}_c{k[1]}", "n_analysis_px": int(am[k].sum()),
                         "n_ink": int(ink.sum()), "n_bg": int(bg.sum()),
                         "auc_display_u8": C.auc_hist(hi_, hb_),
                         "auc_float_energy": C.auc_float(d["e"][ink].astype(np.float64), d["e"][bg].astype(np.float64)),
                         "per_tile_thresholds": {"p90": float(t90), "p50": float(t50), "n_ink": int(ink2.sum()),
                                                 "n_bg": int(bg2.sum()),
                                                 "auc_display_u8": C.auc_hist(np.bincount(d["u8"][ink2], minlength=256),
                                                                              np.bincount(d["u8"][bg2], minlength=256))}})
        HI = sum(h[0] for h in hists.values())
        HB = sum(h[1] for h in hists.values())
        pooled = C.auc_hist(HI, HB)
        keys = list(preds)
        rng = np.random.default_rng(20260927)
        boots = []
        for _ in range(2000):
            ix = rng.integers(0, len(keys), len(keys))
            boots.append(C.auc_hist(sum(hists[keys[i]][0] for i in ix), sum(hists[keys[i]][1] for i in ix)))
        boots = np.array(boots)
        boots = boots[np.isfinite(boots)]
        res[mode] = {"thresholds_pooled": {"p90": float(p90), "p50": float(p50), "n_pool_px": int(pool.size)},
                     "pooled_auc": pooled, "n_ink": int(HI.sum()), "n_bg": int(HB.sum()),
                     "bootstrap_ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
                     "bootstrap_n": int(boots.size), "per_tile": rows}
    a, s_ = res["aligned"]["pooled_auc"], res["rot90"]["pooled_auc"]
    pass_auc, pass_san = a >= 0.70, 0.47 <= s_ <= 0.53
    gate = {"provenance": PROV, "serves": "RULES.md DECL-P4-9 item 2; sibling task p4-crackle",
            "plan": "logs/sib/p4-crackle/gate_plan.json (pre-registered, commit 44b77c3)",
            "plan_sha256": hashlib.sha256(open(os.path.join(OUT, "gate_plan.json"), "rb").read()).hexdigest(),
            "inputs": inp, "control_tiles": [f"r{r}_c{c}" for r, c in tiles],
            "tile_compute": {f"r{k[0]}_c{k[1]}": dict(d["info"], stretch_lo=d["lo"], stretch_hi=d["hi"],
                                                      m2b_png_sha256=d["png_sha256"],
                                                      display_u8_sha256=hashlib.sha256(d["u8"].tobytes()).hexdigest(),
                                                      pos_fraction_1068=float(d["pos"].mean()))
                             for k, d in preds.items()},
            "pixel_um": PX_UM, "aligned": res["aligned"], "rot90": res["rot90"],
            "decision": {"pooled_auc": a, "bar": 0.70, "auc_pass": bool(pass_auc),
                         "rot90_pooled_auc": s_, "sanity_band": [0.47, 0.53], "sanity_pass": bool(pass_san),
                         "GATE": "PASS" if (pass_auc and pass_san) else "FAIL"},
            "viewing": "no image, tile or CT pixel was opened, displayed or described by the builder",
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(gate, open(os.path.join(OUT, "gate.json"), "w"), indent=1)
    np.savez_compressed(os.path.join(SCR, "gate_arrays.npz"),
                        **{f"r{k[0]}_c{k[1]}__u8": d["u8"] for k, d in preds.items()},
                        **{f"r{k[0]}_c{k[1]}__pos": d["pos"] for k, d in preds.items()})
    log(run="gate-analyse", GATE=gate["decision"]["GATE"], pooled_auc=a, rot90=s_,
        ci=res["aligned"]["bootstrap_ci95"], ci_rot=res["rot90"]["bootstrap_ci95"])


if __name__ == "__main__":
    {"compute": compute, "analyse": analyse}[sys.argv[2]]()
