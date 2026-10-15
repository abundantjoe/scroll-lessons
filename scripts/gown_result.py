#!/usr/bin/env python
"""gown_result.py -- RULES G-OWN: does OUR tracer's geometry preserve the ink signal on a sheet we know carries text?

Every number here is decided by bars fixed in the RULES declaration before the trace was started.  This script
chooses nothing: it applies the admissibility gate, computes the one declared statistic, and prints the verdict the
declaration assigns to it.

  gown_result.py --patch <tifxyz dir> [--read <read dir>] [--mesh <w040 mesh dir>] [--out JSON]
"""
import argparse, glob, json, os, sys
import numpy as np, tifffile
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule55
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

D = DATA
UM = 9.362
WRAP_UM = 449.0                       # R-INTERIOR's measured wrap spacing
MIN_ON_SHEET_FRAC = 0.50              # admissibility gate, fixed in the declaration
PASS_BAR = 0.0128                     # half the team mesh's +0.0255 on this same text
COLLAPSE_BAR = 0.0042                 # the R-BLANK bar
TEAM_MESH_MARGIN = 0.0255
CORPUS_MARGIN = 0.0014
CONTROL_BLANK = 0.0134
CONTROL_INKED = 0.0438


def grid_points(d):
    """Valid level-0 voxel coordinates (N, 3) of a tifxyz grid."""
    x = tifffile.imread(os.path.join(d, "x.tif")).astype(np.float64)
    y = tifffile.imread(os.path.join(d, "y.tif")).astype(np.float64)
    z = tifffile.imread(os.path.join(d, "z.tif")).astype(np.float64)
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(z) & (x > 0) & (y > 0) & (z > 0)
    return np.stack([x[ok], y[ok], z[ok]], axis=1)


def on_sheet_fraction(patch_pts, mesh_pts, wrap_um=WRAP_UM, um=UM):
    """Fraction of patch points within one wrap spacing of the known-text mesh, and the distance summary (um)."""
    tol_vx = wrap_um / um
    d, _ = cKDTree(mesh_pts).query(patch_pts, k=1)
    return float((d <= tol_vx).mean()), d * um


def whole_map_margin(read_dir):
    """mean(forward) - mean(reverse) over on-sheet pixels, plus the pieces, from a read directory's map pair."""
    tifs = sorted(glob.glob(os.path.join(read_dir, "*.tif")))
    rev = [t for t in tifs if "reverse" in os.path.basename(t)]
    fwd = [t for t in tifs if "reverse" not in os.path.basename(t)]
    if not fwd or not rev:
        return None
    f = tifffile.imread(fwd[0]).astype(np.float32) / rule55.prob_scale(tifffile.imread(fwd[0]))
    r = tifffile.imread(rev[0]).astype(np.float32) / rule55.prob_scale(tifffile.imread(rev[0]))
    on = (f > 0) | (r > 0)
    if not on.any():
        return None
    return dict(forward_mean=float(f[on].mean()), reverse_mean=float(r[on].mean()),
                margin=float(f[on].mean() - r[on].mean()), onsheet_px=int(on.sum()),
                forward_map=fwd[0], reverse_map=rev[0])


def matched_region(patch_pts, mesh_dir, um=UM):
    """Canvas mask of the w040 control that OUR trace covers: each trace point -> nearest mesh node -> its 20x20 block.

    DESCRIPTIVE ONLY, declared in RULES as such: it cannot move the G-OWN verdict, which stands on the declared bar
    against the team mesh's whole-canvas +0.0255.  It answers the sharper question - what does the team's own mesh
    get on exactly this patch of papyrus?"""
    x = tifffile.imread(os.path.join(mesh_dir, "x.tif")).astype(np.float64)
    y = tifffile.imread(os.path.join(mesh_dir, "y.tif")).astype(np.float64)
    z = tifffile.imread(os.path.join(mesh_dir, "z.tif")).astype(np.float64)
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(z) & (x > 0) & (y > 0) & (z > 0)
    rows, cols = np.nonzero(ok)
    nodes = np.stack([x[ok], y[ok], z[ok]], axis=1)
    d, idx = cKDTree(nodes).query(patch_pts, k=1)
    near = d <= WRAP_UM / um                       # only points actually on the known-text sheet select a block
    hit = np.unique(idx[near])
    step = int(round(1.0 / json.load(open(os.path.join(mesh_dir, "meta.json")))["scale"][0]))
    return rows[hit], cols[hit], step, int(near.sum())


def team_margin_on_region(rows, cols, step, forward_tif, reverse_tif):
    """mean(fwd) - mean(rev) over the control's own maps, restricted to the blocks our trace covers."""
    f = tifffile.imread(forward_tif); r = tifffile.imread(reverse_tif)
    sc = rule55.prob_scale(f)
    mask = np.zeros(f.shape, bool)
    for rr, cc in zip(rows, cols):
        mask[rr * step:(rr + 1) * step, cc * step:(cc + 1) * step] = True
    mask &= (f > 0) | (r > 0)
    if not mask.any():
        return None
    fm = float(f[mask].astype(np.float64).mean() / sc); rm = float(r[mask].astype(np.float64).mean() / sc)
    return dict(forward_mean=fm, reverse_mean=rm, margin=fm - rm, px=int(mask.sum()),
                cm2=rule55.px_to_cm2(int(mask.sum()), UM))


def verdict(on_frac, margin_abs):
    if on_frac < MIN_ON_SHEET_FRAC:
        return "VOID-OFF-SHEET", ("only %.1f %% of the trace lies within one wrap spacing of the known-text mesh "
                                 "(gate %.0f %%); the run says nothing and is re-seeded" % (100*on_frac, 100*MIN_ON_SHEET_FRAC))
    if margin_abs is None:
        return "PENDING", "the trace is admissible; no read has produced a map pair yet"
    if margin_abs >= PASS_BAR:
        return "PASS", ("|margin| %.4f >= %.4f: our tracer's geometry preserves the depth-asymmetric ink signal"
                        % (margin_abs, PASS_BAR))
    if margin_abs <= COLLAPSE_BAR:
        return "COLLAPSE", ("|margin| %.4f <= %.4f: our own geometry destroys the ink signal on a sheet known to "
                            "carry text" % (margin_abs, COLLAPSE_BAR))
    return "PARTIAL", ("|margin| %.4f is between %.4f and %.4f: the geometry costs %.0f %% of the team mesh's signal"
                       % (margin_abs, COLLAPSE_BAR, PASS_BAR, 100*(1 - margin_abs / TEAM_MESH_MARGIN)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch", required=True)
    ap.add_argument("--read", default=None)
    ap.add_argument("--mesh", default=os.path.join(D, "controls", "w040", "mesh"))
    ap.add_argument("--out", default=os.path.join(D, "gates", "gown", "gown_result.json"))
    ap.add_argument("--team-forward", default=os.path.join(D, "gates", "gateA", "w040_full_plain.tif"))
    ap.add_argument("--team-reverse", default=os.path.join(D, "gates", "gateA", "w040_full_plain_reverse.tif"))
    a = ap.parse_args()

    pts = grid_points(a.patch); mesh = grid_points(a.mesh)
    on_frac, dist = on_sheet_fraction(pts, mesh)
    mm = whole_map_margin(a.read) if a.read else None
    margin_abs = abs(mm["margin"]) if mm else None
    v, why = verdict(on_frac, margin_abs)

    matched = None
    if os.path.exists(a.team_forward) and os.path.exists(a.team_reverse):
        try:
            rr, cc, step, n_near = matched_region(pts, a.mesh)
            if len(rr):
                matched = team_margin_on_region(rr, cc, step, a.team_forward, a.team_reverse)
                if matched:
                    matched["n_mesh_nodes_covered"] = int(len(rr))
                    matched["n_trace_points_on_sheet"] = int(n_near)
                    if margin_abs is not None and abs(matched["margin"]) > 1e-9:
                        matched["kept_fraction"] = float(margin_abs / abs(matched["margin"]))
        except Exception as e:                      # descriptive only: it must never break the declared verdict
            matched = {"error": "%s: %s" % (type(e).__name__, e)}

    out = dict(patch=a.patch, read=a.read, mesh=a.mesh, verdict=v, verdict_reason=why, matched_region=matched,
               n_patch_points=int(len(pts)), n_mesh_points=int(len(mesh)),
               on_sheet_frac=on_frac, gate_min_on_sheet_frac=MIN_ON_SHEET_FRAC, wrap_um=WRAP_UM,
               dist_um=dict(median=float(np.median(dist)), p90=float(np.percentile(dist, 90)), max=float(dist.max())),
               bars=dict(pass_bar=PASS_BAR, collapse_bar=COLLAPSE_BAR, team_mesh_margin=TEAM_MESH_MARGIN,
                         corpus_margin=CORPUS_MARGIN, control_blank=CONTROL_BLANK, control_inked=CONTROL_INKED),
               whole_map=mm, margin_abs=margin_abs)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, sort_keys=True)

    print("patch points %d ; known-text mesh points %d" % (len(pts), len(mesh)))
    print("distance to the known-text sheet: median %.0f um, p90 %.0f um, max %.0f um (one wrap = %.0f um)"
          % (out["dist_um"]["median"], out["dist_um"]["p90"], out["dist_um"]["max"], WRAP_UM))
    print("ON-SHEET FRACTION %.4f  (admissibility gate %.2f)" % (on_frac, MIN_ON_SHEET_FRAC))
    if mm:
        print("whole-map on-sheet: forward %.4f  reverse %.4f  margin %+.4f  |margin| %.4f  (%d px)"
              % (mm["forward_mean"], mm["reverse_mean"], mm["margin"], margin_abs, mm["onsheet_px"]))
        print("   team mesh on this text %+.4f | control INKED units %+.4f | control BLANK units %+.4f | corpus %+.4f"
              % (TEAM_MESH_MARGIN, CONTROL_INKED, CONTROL_BLANK, CORPUS_MARGIN))
    if matched and "margin" in matched:
        print("AREA-MATCHED control (the team's own maps over the %.2f cm2 our trace covers, %d mesh nodes):"
              % (matched["cm2"], matched["n_mesh_nodes_covered"]))
        print("   forward %.4f  reverse %.4f  margin %+.4f%s"
              % (matched["forward_mean"], matched["reverse_mean"], matched["margin"],
                 ("   -> our geometry keeps %.1f %% of it" % (100 * matched["kept_fraction"]))
                 if "kept_fraction" in matched else ""))
        print("   (descriptive, declared as such; the verdict below stands on the declared bar against +0.0255)")
    print("\nG-OWN VERDICT: %s -- %s" % (v, why))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
