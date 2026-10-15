#!/usr/bin/env python
"""RULES G-GP: mesh parameterisation quality of a tifxyz grid.

A tifxyz is a COARSE control mesh (meta "scale" = grid nodes per level-0 voxel, 0.05 -> one node per 20 voxels);
vc_render_tifxyz interpolates between nodes at render time. This measures how faithful that grid is, with no
inference and no render:

  stretch    |t_u| / step and |t_v| / step, central-difference tangents against the nominal node spacing (1.0 = isometric)
  anisotropy max(s_u, s_v) / min(s_u, s_v)                                                  (1.0 = balanced)
  shear      |cos(t_u, t_v)|                                                                (0.0 = orthogonal)
  sag        distance in MICROMETRES from a node to the plane through its four grid neighbours

usage: mesh_distortion.py <tifxyz dir> [...] --um 9.362 [--label NAME] [--json out.json]
       mesh_distortion.py --batch <dir of tifxyz dirs> --um 9.362 [--json out.json]
"""
import argparse, json, os, sys
import numpy as np, tifffile


def load(patch_dir):
    g = [tifffile.imread(os.path.join(patch_dir, n + ".tif")).astype(np.float64) for n in "xyz"]
    meta = {}
    mp = os.path.join(patch_dir, "meta.json")
    if os.path.exists(mp):
        meta = json.load(open(mp))
    return np.stack(g, -1), meta


def pct(a, q):
    return float(np.percentile(a, q)) if a.size else float("nan")


def node_spacing_vx(P, valid):
    """Median 3D distance between horizontally adjacent valid nodes, in level-0 voxels."""
    d = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)
    m = valid[:, 1:] & valid[:, :-1] & (d > 0)
    return float(np.median(d[m])) if m.any() else float("nan")


def measure(patch_dir, um, baseline_um=None):
    """Distortion statistics for one tifxyz dir, or None when the grid is too small / all invalid.

    With baseline_um the tangents and the sag are taken across k nodes rather than 1, k chosen so that
    k * (this mesh's own node spacing) is closest to that physical baseline. That is the only way to compare
    two meshes whose node spacing differs -- sag shrinks with the baseline for any smooth surface, so a denser
    grid scores better on raw sag without being any more faithful. Part 1 needed no such correction: every mesh
    it compared has a 20-voxel spacing (verified, median tangent length 20.0-21.8 vx over all 173).
    """
    P, meta = load(patch_dir)
    valid = np.isfinite(P).all(-1) & (P > 0).all(-1)
    if P.shape[0] < 3 or P.shape[1] < 3:
        return None
    scale = meta.get("scale") or [0.05, 0.05]
    step = 1.0 / float(scale[0])                      # nominal node spacing in level-0 voxels
    k = 1
    h_vx = node_spacing_vx(P, valid)
    if baseline_um:
        if not np.isfinite(h_vx) or h_vx <= 0:
            return None
        k = max(1, int(round(baseline_um / (h_vx * um))))
        step = h_vx * k                               # the baseline stride IS the nominal step in this mode
    if P.shape[0] < 2 * k + 1 or P.shape[1] < 2 * k + 1:
        return None
    tu = (P[k:-k, 2 * k:] - P[k:-k, :-2 * k]) / 2.0   # d/du across columns, stride k
    tv = (P[2 * k:, k:-k] - P[:-2 * k, k:-k]) / 2.0   # d/dv down rows, stride k
    ok = (valid[k:-k, 2 * k:] & valid[k:-k, :-2 * k] & valid[2 * k:, k:-k] & valid[:-2 * k, k:-k]
          & valid[k:-k, k:-k])
    lu, lv = np.linalg.norm(tu, axis=-1), np.linalg.norm(tv, axis=-1)
    ok = ok & (lu > 0) & (lv > 0)
    if int(ok.sum()) < 25:                            # too few interior nodes to describe a distribution
        return None
    su, sv = lu[ok] / step, lv[ok] / step
    hi, lo = np.maximum(su, sv), np.minimum(su, sv)
    aniso = hi / lo
    with np.errstate(invalid="ignore", divide="ignore"):
        shear = np.abs((tu * tv).sum(-1)[ok] / (lu[ok] * lv[ok]))
    # sag: node minus the centroid of its four neighbours, projected on the local normal, in micrometres
    n = np.cross(tu, tv)
    nn = np.linalg.norm(n, axis=-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        nhat = n / nn[..., None]
    cen = (P[k:-k, 2 * k:] + P[k:-k, :-2 * k] + P[2 * k:, k:-k] + P[:-2 * k, k:-k]) / 4.0
    sag = np.abs(((P[k:-k, k:-k] - cen) * nhat).sum(-1))[ok & (nn > 0)] * um
    return dict(
        patch=os.path.basename(patch_dir.rstrip("/")), dir=patch_dir, um=um,
        baseline_um=None if not baseline_um else round(step * um, 1), stride_nodes=k,
        node_spacing_um=round(h_vx * um, 2) if np.isfinite(h_vx) else None,
        grid_shape=[int(P.shape[0]), int(P.shape[1])], nominal_step_vx=step, n_nodes=int(ok.sum()),
        area_cm2=meta.get("area_cm2"), max_gen=meta.get("max_gen"),
        tangent_len_vx_median=round(float(np.median(np.concatenate([lu[ok], lv[ok]]))), 3),
        stretch_median=round(float(np.median(np.concatenate([su, sv]))), 4),
        stretch_p90=round(pct(np.concatenate([su, sv]), 90), 4),
        anisotropy_median=round(float(np.median(aniso)), 4), anisotropy_p90=round(pct(aniso, 90), 4),
        shear_median=round(float(np.median(shear)), 4), shear_p90=round(pct(shear, 90), 4),
        sag_um_median=round(float(np.median(sag)), 2) if sag.size else None,
        sag_um_p90=round(pct(sag, 90), 2) if sag.size else None,
    )


HDR = "%-42s %6s %7s %8s %8s %8s %8s %9s %9s" % (
    "surface", "nodes", "sp um", "str med", "str p90", "ani med", "ani p90", "sag med um", "sag p90 um")


def line(r):
    f = lambda v: "-" if v is None else ("%9.2f" % v)
    return "%-42s %6d %7.1f %8.3f %8.3f %8.3f %8.3f %s %s" % (
        r["patch"][:42], r["n_nodes"], r.get("node_spacing_um") or float("nan"),
        r["stretch_median"], r["stretch_p90"],
        r["anisotropy_median"], r["anisotropy_p90"], f(r["sag_um_median"]), f(r["sag_um_p90"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="*")
    ap.add_argument("--batch", action="append", default=[], help="a directory whose children are tifxyz dirs")
    ap.add_argument("--um", type=float, required=True)
    ap.add_argument("--baseline-um", type=float, default=None,
                    help="compare at a matched physical baseline: tangents and sag across k nodes, k chosen per "
                         "mesh from its own node spacing. Required whenever the meshes compared differ in density.")
    ap.add_argument("--label", default="")
    ap.add_argument("--json")
    a = ap.parse_args()
    targets = list(a.dirs)
    for b in a.batch:
        targets += sorted(os.path.join(b, d) for d in os.listdir(b)
                          if os.path.exists(os.path.join(b, d, "x.tif")))
    rows, skipped = [], []
    for d in targets:
        try:
            r = measure(d, a.um, baseline_um=a.baseline_um)
        except Exception as e:                        # a truncated or unreadable grid is reported, never silent
            skipped.append((d, str(e))); continue
        if r is None:
            skipped.append((d, "grid too small or fewer than 25 valid interior nodes")); continue
        rows.append(r)
    if a.label:
        print("== %s (voxel %.3f um%s)" % (a.label, a.um,
              "" if not a.baseline_um else ", matched baseline %.1f um" % a.baseline_um))
    print(HDR)
    for r in rows:
        print(line(r))
    out = dict(label=a.label, um=a.um, n=len(rows), rows=rows,
               skipped=[{"dir": d, "reason": w} for d, w in skipped])
    if rows:
        for k in ("stretch_p90", "anisotropy_p90", "sag_um_p90", "anisotropy_median", "sag_um_median"):
            vals = [r[k] for r in rows if r.get(k) is not None]
            out["pooled_" + k] = round(float(np.percentile(vals, 90)), 4) if vals else None
            out["median_" + k] = round(float(np.median(vals)), 4) if vals else None
        print("  pooled over %d surfaces: p90-of-p90 anisotropy %.3f  sag %.1f um   median-of-p90 anisotropy %.3f  sag %.1f um"
              % (len(rows), out["pooled_anisotropy_p90"], out["pooled_sag_um_p90"] or float("nan"),
                 out["median_anisotropy_p90"], out["median_sag_um_p90"] or float("nan")))
    for d, w in skipped:
        print("  skipped %s: %s" % (os.path.basename(d.rstrip("/")), w))
    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump(out, open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
