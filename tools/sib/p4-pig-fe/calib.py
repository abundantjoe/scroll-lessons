"""p4-pig-fe calibration on the CONTROL strips only (C at 1.129 um, C2 at 2.4 um). Numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]

Frozen rules (applied here, written to logs/sib/p4-pig-fe/calib_control.json; no title-strip byte is read):
  sample     2 % of the control's level-L chunk positions inside the canvas, numpy default_rng(20260926), whole
             depth range centre-22 .. centre+32 fetched by one range request
  voxels     nonzero, at mesh-valid px (C: hz_common mesh rule; C2: the surface volume is masked to the mesh, so
             nonzero at every slice of the fetched range)
  side       recto surface layer on the + side iff mean(c-12..c-4) > mean(c+4..c+12) (sheet mass on the - side);
             otherwise all bands are mirrored
  v_air      p10 of voxels in slices c+12 .. c+27 (gap side)
  v_pap      p75 of voxels in slices c-12 .. c-4 (sheet core)
  B_lo       p95 of voxels in the S and I bands
  B_hi       min(254, round(v_air + 4.5 (v_pap - v_air)))   (standard ochre ink, electron-density regime, full voxel)
Usage: python calib.py <scratch>
"""
import concurrent.futures as cf
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import fe  # noqa: E402

Q = {}


def fetch(args):
    name, yx, lo, hi = args
    b = fe.get(f"{fe.url_chunks(name)}/{yx[0]}/{yx[1]}", (lo * fe.PLANE, hi * fe.PLANE - 1))
    if b is None:
        return yx, None
    return yx, b


def worker(args):
    name, items, lo, hi, meshmask_path = args
    mesh = np.load(meshmask_path, mmap_mode="r") if meshmask_path else None
    n = hi - lo
    H = np.zeros((n, 256), np.int64)
    with cf.ThreadPoolExecutor(32) as ex:
        for yx, b in ex.map(fetch, [(name, yx, lo, hi) for yx in items]):
            if b is None:
                continue
            a = np.frombuffer(b, np.uint8).reshape(n, fe.CH, fe.CH)
            ok = (a > 0).all(0)
            if mesh is not None:
                ys = yx[0] * fe.CH + np.arange(fe.CH)
                xs = yx[1] * fe.CH + np.arange(fe.CH)
                gy = np.minimum(ys // 10, mesh.shape[0] - 1)
                gx = np.minimum(xs // 10, mesh.shape[1] - 1)
                ok &= np.asarray(mesh[gy][:, gx])
            if not ok.any():
                continue
            v = a[:, ok]
            for k in range(n):
                H[k] += np.bincount(v[k], minlength=256)
    return H


def main(scr):
    out = {"provenance": fe.PROV, "serves": "DECL-P4-10 FE detector calibration, control strips only", "materials": {}}
    for name in ("C", "C2"):
        m = fe.MAT[name]
        c = m["centre"]
        lo, hi = c - 22, c + 33
        za = json.loads(fe.get(fe.url_level(name) + "/.zarray"))
        nz, H, W = za["shape"]
        ny, nx = -(-H // fe.CH), -(-W // fe.CH)
        rng = np.random.default_rng(20260926)
        allpos = [(y, x) for y in range(ny) for x in range(nx)]
        sel = sorted(rng.choice(len(allpos), size=int(0.02 * len(allpos)), replace=False))
        items = [allpos[i] for i in sel]
        meshp = None
        if name == "C":
            sys.path.insert(0, os.path.dirname(__file__))
            import hz_common as hz
            mat = hz.load_material("C", scr)
            meshp = os.path.join(scr, "valid_C.npy")
            out["materials"][name + "_mesh_inputs"] = mat["mesh_inputs"]
        t0 = time.time()
        parts = [items[i::4] for i in range(4)]
        with mp.Pool(4) as p:
            Hs = p.map(worker, [(name, pt, lo, hi, meshp) for pt in parts])
        Hh = sum(Hs)
        idx = lambda s: slice(s - lo, s - lo + 1)
        prof = [(float((np.arange(256) * h).sum() / h.sum()) if h.sum() else None) for h in Hh]
        core = Hh[(c - 12) - lo:(c - 4) + 1 - lo].sum(0)
        gapp = Hh[(c + 4) - lo:(c + 12) + 1 - lo].sum(0)
        mean = lambda h: float((np.arange(256) * h).sum() / h.sum())
        side = +1 if mean(core) > mean(gapp) else -1
        bd = fe.bands(name)
        if side < 0:
            raise SystemExit(f"{name}: sheet mass on the + side; mirrored fetch range needed (not implemented)")
        if side < 0:
            bd = {k: (2 * c + 1 - v[1], 2 * c + 1 - v[0]) for k, v in bd.items()}
        gap = Hh[(c + 12 * side if side > 0 else c - 27) - lo:(c + 27 + 1 if side > 0 else c - 12 + 1) - lo].sum(0)
        corep = Hh[(c - 12 if side > 0 else c + 4) - lo:(c - 4 + 1 if side > 0 else c + 12 + 1) - lo].sum(0)
        SI = Hh[bd["S"][0] - lo:bd["S"][1] - lo].sum(0) + Hh[bd["I"][0] - lo:bd["I"][1] - lo].sum(0)
        v_air, v_pap = fe.hist_pct(gap, 0.10), fe.hist_pct(corep, 0.75)
        B_lo = fe.hist_pct(SI, 0.95)
        B_hi = int(min(254, round(v_air + 4.5 * (v_pap - v_air))))
        out["materials"][name] = {
            "segment": m["seg"], "sv": m["sv"], "level": m["level"], "zarray_shape": za["shape"],
            "fetch_slices": [lo, hi], "sampled_chunks": len(items), "secs": round(time.time() - t0, 1),
            "voxels_counted": int(Hh.sum()), "depth_profile_mean": prof, "side": side, "bands": bd,
            "v_air_p10_gap": v_air, "v_pap_p75_core": v_pap, "B_lo_p95_SI": B_lo, "B_hi": B_hi,
            "SI_pcts": {q: fe.hist_pct(SI, q) for q in (0.5, 0.9, 0.95, 0.99, 0.999)},
            "SI_frac_ge_B_hi": float(SI[B_hi:].sum() / SI.sum()),
            "hist_S": Hh[bd["S"][0] - lo:bd["S"][1] - lo].sum(0).tolist(),
            "hist_I": Hh[bd["I"][0] - lo:bd["I"][1] - lo].sum(0).tolist(),
            "hist_D": Hh[bd["D"][0] - lo:bd["D"][1] - lo].sum(0).tolist(),
        }
        print(name, {k: v for k, v in out["materials"][name].items() if not k.startswith(("hist", "depth"))}, flush=True)
    out["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(out, open(os.path.join(os.path.dirname(fe.PARAMS), "calib_control.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
