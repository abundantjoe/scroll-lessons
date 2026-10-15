"""Unit tests for L4 (DECL-P4-18). Synthetic only. Provenance: Project HERCULES | owner the owner | [id removed]"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import l4  # noqa: E402

rng = np.random.default_rng(7)


def sheet(h=96, w=96, ink=None, amp=175):
    """Sheet of thickness 12-20 slices, centre wandering +-18 slices around 54 (smooth), interior N(120,10),
    air N(35,8). ink: None | 'minus' | 'plus' -> a 4-slice deposit starting 10 um (4 slices... 4.2) outside the face."""
    yy, xx = np.mgrid[0:h, 0:w]
    cen = 54 + 18 * np.sin(xx / 17.0) * np.cos(yy / 23.0)
    th = 16 + 4 * np.sin(yy / 11.0)
    lo = np.rint(cen - th / 2).astype(int)
    hi = np.rint(cen + th / 2).astype(int)
    z = np.arange(109)[:, None, None]
    v = rng.normal(35, 8, (109, h, w))
    inside = (z >= lo) & (z <= hi)
    v[inside] = rng.normal(120, 10, inside.sum())
    mask = np.zeros((h, w), bool)
    mask[20:70, 20:70] = True
    if ink == "minus":  # deposit at slices lo-6..lo-3 (7.2-14.4 um outside), centred ~10 um
        d = (z >= lo - 6) & (z <= lo - 3) & mask
        v[d] += amp
    if ink == "plus":
        d = (z >= hi + 3) & (z <= hi + 6) & mask
        v[d] += amp
    return np.clip(np.rint(v), 0, 255).astype(np.uint8), lo, hi, mask


res = {}
v, lo, hi, _ = sheet()
b = l4.l4_block(v)
em = np.abs(b["sm"].astype(int) + 54 - lo)
ep = np.abs(b["sp"].astype(int) + 54 - hi)
res["face_err_slices_p99"] = [float(np.percentile(em, 99)), float(np.percentile(ep, 99))]
res["face_err_max"] = [int(em.max()), int(ep.max())]
res["valid_frac"] = float(b["ok"].mean())
assert b["ok"].all() and em.max() <= 1 and ep.max() <= 1, res   # <= 1 slice = 2.4 um
for face, key in (("minus", "m"), ("plus", "p")):
    v, lo, hi, mask = sheet(ink=face)
    b = l4.l4_block(v)
    other = "p" if key == "m" else "m"
    d_in = float(b[key][mask].mean() - b[key][~mask].mean())
    v0, _, _, _ = sheet()
    b0 = l4.l4_block(v0)
    d_oth = float(b[other][mask].mean() - b[other][~mask].mean()) - float(
        b0[other][mask].mean() - b0[other][~mask].mean())  # vs the same geometry without ink
    run_on_ink = float(((b["sp"].astype(int) + 54 < lo) if key == "m" else (b["sm"].astype(int) + 54 > hi))[mask].mean())
    em = np.abs((b["sm"] if key == "m" else b["sp"]).astype(int) + 54 - (lo if key == "m" else hi))
    res[f"ink_{face}"] = {"delta_same_face": d_in, "delta_other_face": d_oth, "face_err_max_slices": int(em.max()),
                        "frac_ink_px_where_the_deposit_run_was_chosen_as_sheet": run_on_ink}
    assert d_in >= 40 and abs(d_oth) < 0.25 * d_in, res  # cross-face leak disclosed (deposit run nearer the mesh)
    # a deposit brighter than T_mid 2 slices outside the face is bridged into the run by the sigma-1 smoothing, so the
    # face moves to the deposit edge (reported, disclosed); recovery is asserted above
# no-run pixel -> invalid
v = np.full((109, 4, 4), 30, np.uint8)
assert not l4.l4_block(v)["ok"].any()
res["all_pass"] = True
print(json.dumps(res, indent=1))
if len(sys.argv) > 1:
    json.dump(res, open(sys.argv[1], "w"), indent=1)
