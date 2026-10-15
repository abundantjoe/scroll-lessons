"""p4-purple-mo gate (PROTOCOL sections 3-5 with amendment A1): per-tile cell maps, then AUCs, bootstrap, rot-90 null.

Provenance: Project HERCULES | owner the owner | [id removed]

Control strip w028-037 gate tiles only. Numbers only.
Usage: python gate.py <scratch> compute <worker> <n_workers> | analyse
"""
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mo  # noqa: E402

SCR = sys.argv[1]
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
OUT = os.path.join(REPO, "logs/sib/p4-purple/mo")
TESTS = ["F1+", "F1-", "F2", "F3+", "F3-", "F4+", "F4-", "F5+", "F5-"]
NB = 4096


def log(**kw):
    kw = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **kw}
    with open(os.path.join(SCR, "runs.jsonl"), "a") as f:
        f.write(json.dumps(kw) + "\n")
    print(json.dumps(kw), flush=True)


def compute_tile(r, c, tf, vg, pt):
    I0, I1, J0, J1 = mo.tile_cells(r, c)
    i0, i1, j0, j1 = 2 * I0, 2 * I1, 2 * J0, 2 * J1
    ny, nx = i1 - i0, j1 - j0
    keys = ["hpA", "hmA", "epA", "emA", "hpO", "hmO", "epO", "emO"]
    M = {k: np.full((ny, nx), np.nan, np.float32) for k in keys}
    V = mo.valid4(vg, i0, i1, j0, j1)
    cy0, cy1 = (8 * I0) // mo.CH, -(-(8 * I1) // mo.CH)
    cx0, cx1 = (8 * J0) // mo.CH, -(-(8 * J1) // mo.CH)
    wins = [(a, min(a + 8, cy1), b, min(b + 8, cx1)) for a in range(cy0, cy1, 8) for b in range(cx0, cx1, 8)]
    t0, nmiss = time.time(), 0
    with cf.ThreadPoolExecutor(1) as pre:
        fut = pre.submit(mo.fetch_window, *wins[0], 32)
        for n, w in enumerate(wins):
            arr, present = fut.result()
            if n + 1 < len(wins):
                fut = pre.submit(mo.fetch_window, *wins[n + 1], 32)
            nmiss += int((~present).sum())
            P = mo.block_profile(arr)
            E = mo.dog_energy_blocks(arr)
            del arr
            pres = np.repeat(np.repeat(present, 32, 0), 32, 1)
            out = {}
            for tag, anc in (("A", True), ("O", False)):
                hp, hm, zp, zm, _ = mo.faces(P, tf, anchor=anc)
                out["hp" + tag], out["hm" + tag] = hp, hm
                out["ep" + tag], out["em" + tag] = mo.energy_at(E, zp), mo.energy_at(E, zm)
            del P, E
            wi0, wj0 = w[0] * 32, w[2] * 32
            wi1, wj1 = wi0 + pres.shape[0], wj0 + pres.shape[1]
            a0, a1 = max(wi0, i0), min(wi1, i1)
            b0, b1 = max(wj0, j0), min(wj1, j1)
            for k in keys:
                src = np.where(pres, out[k], np.nan)
                M[k][a0 - i0:a1 - i0, b0 - j0:b1 - j0] = src[a0 - wi0:a1 - wi0, b0 - wj0:b1 - wj0]
            V[a0 - i0:a1 - i0, b0 - j0:b1 - j0] &= pres[a0 - wi0:a1 - wi0, b0 - wj0:b1 - wj0]
    for k in keys:
        M[k] = np.where(V, M[k], np.nan)
    pred = pt.region_mean8(I0, I1, J0, J1)
    p = os.path.join(SCR, f"tile_r{r}_c{c}.npz")
    np.savez(p, V=V, pred=pred, **M)
    log(run="tile", tile=f"r{r}_c{c}", windows=len(wins), missing_chunks=nmiss, secs=round(time.time() - t0, 1),
        valid_cells_96=int(V.sum()), frac_hpA=float(np.isfinite(M["hpA"]).sum() / max(1, V.sum())),
        frac_hmA=float(np.isfinite(M["hmA"]).sum() / max(1, V.sum())))


def compute(worker, nw):
    tf = json.load(open(os.path.join(OUT, "tface.json")))["T_face"]["T_face"]
    vg, _ = mo.mesh_valid_grid(SCR)
    pt = mo.PredTiff()
    for n, (r, c) in enumerate(mo.GATE):
        if n % nw != worker or os.path.exists(os.path.join(SCR, f"tile_r{r}_c{c}.npz")):
            continue
        compute_tile(r, c, tf, vg, pt)


def pool_valid(v):
    y, x = v.shape
    return v[:y // 2 * 2, :x // 2 * 2].reshape(y // 2, 2, x // 2, 2).all(axis=(1, 3))


def rot_sq(a, fill):
    s = 1038
    q = np.full((s, s), fill, a.dtype)
    q[:a.shape[0], :a.shape[1]] = a
    return np.rot90(q, 1)[:a.shape[0], :a.shape[1]]


def tile_features(z, tag):
    F = mo.features(z["hp" + tag], z["hm" + tag], z["ep" + tag], z["em" + tag])
    return {k: mo.pool2(F[k]) for k in TESTS}


def stats(tiles, feats, masks):
    """feats[t][test], masks[t] = (ink, bg). Returns per-test pooled AUC, hist AUC, bootstrap CIs, per-tile AUC."""
    res = {}
    rng = np.random.default_rng(20260929)
    boot_ix = [rng.integers(0, len(tiles), len(tiles)) for _ in range(2000)]
    for te in TESTS:
        xi = [feats[t][te][masks[t][0] & np.isfinite(feats[t][te])].astype(np.float64) for t in tiles]
        xb = [feats[t][te][masks[t][1] & np.isfinite(feats[t][te])].astype(np.float64) for t in tiles]
        ai, ab = np.concatenate(xi), np.concatenate(xb)
        auc = mo.auc_float(ai, ab)
        edges = np.quantile(np.concatenate([ai, ab]), np.linspace(0, 1, NB + 1)[1:-1])
        hi = np.array([np.bincount(np.searchsorted(edges, x, side="right"), minlength=NB) for x in xi])
        hb = np.array([np.bincount(np.searchsorted(edges, x, side="right"), minlength=NB) for x in xb])
        ah = mo.auc_hist(hi.sum(0), hb.sum(0))
        bs = np.array([mo.auc_hist(hi[ix].sum(0), hb[ix].sum(0)) for ix in boot_ix])
        bs = bs[np.isfinite(bs)]
        per = {t: {"auc": mo.auc_float(xi[n], xb[n]), "n_ink": int(xi[n].size), "n_bg": int(xb[n].size)}
               for n, t in enumerate(tiles)}
        eff = float(np.median(ai) - np.median(ab)) if ai.size and ab.size else None
        res[te] = {"auc": auc, "auc_hist4096": ah, "n_ink": int(ai.size), "n_bg": int(ab.size),
                   "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                   "ci_bonf9": [float(np.percentile(bs, 100 * 0.05 / 18)), float(np.percentile(bs, 100 * (1 - 0.05 / 18)))],
                   "bootstrap_n": int(bs.size), "median_ink_minus_bg": eff, "per_tile": per}
    return res


def analyse():
    tiles = [f"r{r}_c{c}" for r, c in mo.GATE]
    Z = {t: dict(np.load(os.path.join(SCR, f"tile_{t}.npz"))) for t in tiles}
    sha = {t: hashlib.sha256(open(os.path.join(SCR, f"tile_{t}.npz"), "rb").read()).hexdigest() for t in tiles}
    v19 = {t: pool_valid(Z[t]["V"]) for t in tiles}
    pred = {t: Z[t]["pred"][:v19[t].shape[0], :v19[t].shape[1]] for t in tiles}
    featA = {t: tile_features(Z[t], "A") for t in tiles}
    featO = {t: tile_features(Z[t], "O") for t in tiles}
    out = {}
    for mode in ("aligned", "rot90"):
        am, pr = {}, {}
        for t in tiles:
            if mode == "aligned":
                pr[t], am[t] = pred[t], v19[t]
            else:
                pr[t] = rot_sq(pred[t], np.float32(0))
                am[t] = v19[t] & rot_sq(v19[t], False)
        pool = np.concatenate([pr[t][am[t]] for t in tiles]).astype(np.float64)
        p90, p50 = np.percentile(pool, [90, 50])
        masks = {t: mo.class_masks(pr[t], am[t], p90, p50) for t in tiles}
        out[mode] = {"thresholds": {"p90": float(p90), "p50": float(p50), "n_pool_cells": int(pool.size)},
                     "n_ink_cells": int(sum(m[0].sum() for m in masks.values())),
                     "n_bg_cells": int(sum(m[1].sum() for m in masks.values())),
                     "A1": stats(tiles, featA, masks)}
        if mode == "aligned":
            out[mode]["original_rule_descriptive"] = stats(tiles, featO, masks)
        log(run="analyse", mode=mode, **{te: round(out[mode]["A1"][te]["auc"], 4) for te in TESTS})
    pc = json.load(open(os.path.join(OUT, "posctl.json")))["PASS"]
    gate = {}
    for te in TESTS:
        a = out["aligned"]["A1"][te]
        nl = out["rot90"]["A1"][te]["auc"]
        face = te[-1] if te[-1] in "+-" else None
        pc_ok = True
        if te.startswith("F1"):
            pc_ok = bool(pc[face])
        elif te == "F2":
            pc_ok = bool(pc["+"] or pc["-"])
        conds = {"auc_ge_0.70": a["auc"] >= 0.70, "bonf_lower_gt_0.60": a["ci_bonf9"][0] > 0.60,
                 "ci95_lower_gt_0.60": a["ci95"][0] > 0.60, "null_in_0.47_0.53": 0.47 <= nl <= 0.53,
                 "posctl_ok_or_na": pc_ok}
        gate[te] = {"auc": a["auc"], "ci95": a["ci95"], "ci_bonf9": a["ci_bonf9"], "rot90_auc": nl, **conds,
                    "reversed_strong": a["auc"] <= 0.30,
                    "GATE": "PASS" if (conds["auc_ge_0.70"] and conds["bonf_lower_gt_0.60"] and conds["null_in_0.47_0.53"]
                                       and pc_ok) else "FAIL"}
    rec = {"provenance": mo.PROV, "serves": "DECL-P4-16 item 4; PROTOCOL.md sections 4-5 with amendment A1",
           "gate_tiles": tiles, "tile_npz_sha256": sha, "T_face": json.load(open(os.path.join(OUT, "tface.json")))["T_face"],
           "pred_key": mo.PRED, "results": out, "gate": gate,
           "viewing": "no image, tile or CT pixel was opened, displayed or described",
           "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(rec, open(os.path.join(OUT, "gate.json"), "w"), indent=1)
    print(json.dumps(gate, indent=1))


if __name__ == "__main__":
    if sys.argv[2] == "compute":
        compute(int(sys.argv[3]), int(sys.argv[4]))
    else:
        analyse()
