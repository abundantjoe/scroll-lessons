#!/usr/bin/env python
"""rsens.py -- RULES R-SENS: the ink-coverage floor of rule 5.5, measured on the Gate B control.

Descriptive only. Alters no map, no verdict, no bar, and creates no candidate.
Arm 1 (analytic): solve the frozen levels for the unit ink area fraction phi, using Gate A's measured per-class
levels on this same control.  Arm 2 (empirical): tile the control at a half-unit stride and report firing vs phi.
"""
import argparse, json, os, sys
import numpy as np, tifffile, zarr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule55
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

D = DATA


def label_slice(path, z):
    g = zarr.open_group(path, mode="r")
    a = g["0"] if "0" in g else g
    return np.asarray(a[z])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gateb", default=os.path.join(D, "gates", "gateB"))
    ap.add_argument("--labels", default=os.path.join(D, "labels", "w040", "w040_inklabels.zarr"))
    ap.add_argument("--mask", default=os.path.join(D, "labels", "w040", "w040_supervision_mask.zarr"))
    ap.add_argument("--slice", type=int, default=14)
    ap.add_argument("--crop", nargs=4, type=int, default=[1152, 2048, 2048, 2048])
    ap.add_argument("--um", type=float, default=9.362)
    ap.add_argument("--out", default=os.path.join(D, "gates", "rsens", "rsens.json"))
    a = ap.parse_args()

    out = {"control": "Gate B render of the w040 known-text mesh crop", "slice": a.slice, "crop": a.crop,
           "um": a.um, "levels": dict(fwd_min=rule55.FWD_MIN, margin_min=rule55.MARGIN_MIN)}

    # ---- arm 1: analytic, from Gate A's measured per-class levels on this control ----
    ga = json.load(open(os.path.join(D, "gates", "gateA", "auc_w040_full_plain.json")))
    gr = json.load(open(os.path.join(D, "gates", "gateA", "auc_w040_full_plain_reverse.json")))
    fi, fb = ga["mean_on_ink"], ga["mean_on_blank"]
    ri, rb = gr["mean_on_ink"], gr["mean_on_blank"]
    # fwd(phi) = fi*phi + fb*(1-phi);  rev(phi) = ri*phi + rb*(1-phi)
    phi_fwd = (rule55.FWD_MIN - fb) / (fi - fb)
    dm = (fi - fb) - (ri - rb)
    phi_mar = (rule55.MARGIN_MIN - (fb - rb)) / dm
    out["analytic"] = dict(mean_on_ink_fwd=fi, mean_on_blank_fwd=fb, mean_on_ink_rev=ri, mean_on_blank_rev=rb,
                           phi_floor_forward_level=phi_fwd, phi_floor_margin=phi_mar,
                           phi_floor_binding=max(phi_fwd, phi_mar),
                           binding="forward level 0.36" if phi_fwd > phi_mar else "margin 0.08")
    print("== ARM 1 (analytic, from Gate A's own per-class levels on this control) ==")
    print("  forward: ink %.4f  blank %.4f     reverse: ink %.4f  blank %.4f" % (fi, fb, ri, rb))
    print("  phi needed for forward mean >= %.2f : %.4f  (%.1f %% of the unit inked)" % (rule55.FWD_MIN, phi_fwd, 100 * phi_fwd))
    print("  phi needed for margin      >= %.2f : %.4f  (%.1f %%)" % (rule55.MARGIN_MIN, phi_mar, 100 * phi_mar))
    print("  BINDING FLOOR: phi >= %.4f = %.1f %% of a 0.5 cm2 unit must be inked, at this control's own contrast"
          % (max(phi_fwd, phi_mar), 100 * max(phi_fwd, phi_mar)))

    # ---- arm 2: empirical, half-unit stride over the control ----
    fwd = tifffile.imread(os.path.join(a.gateb, "render_plain.tif")).astype(np.float64) / 255.0
    rev = tifffile.imread(os.path.join(a.gateb, "render_plain_reverse.tif")).astype(np.float64) / 255.0
    g = zarr.open_group(os.path.join(a.gateb, "render.zarr"), mode="r")["0"]
    ct = np.asarray(g[g.shape[0] // 2]); onsheet = ct > 0
    X, Y, W, H = a.crop
    lab = label_slice(a.labels, a.slice)[Y:Y + H, X:X + W] > 128
    sup = label_slice(a.mask, a.slice)[Y:Y + H, X:X + W] > 0
    assert fwd.shape == rev.shape == onsheet.shape == lab.shape, (fwd.shape, rev.shape, onsheet.shape, lab.shape)

    out["empirical"] = {}
    for area, tag in ((0.5, "0.5cm2"), (1.0, "1cm2")):
        side = rule55.unit_side(a.um, area)
        stride = max(1, side // 2)
        rows = []
        for y in range(0, fwd.shape[0] - side + 1, stride):
            for x in range(0, fwd.shape[1] - side + 1, stride):
                os_w = onsheet[y:y + side, x:x + side]
                su_w = sup[y:y + side, x:x + side]
                n = float(side * side)
                if os_w.sum() / n < rule55.VALID_ONSHEET_FRAC or su_w.sum() / n < 0.90:
                    continue
                m = os_w
                f = float(fwd[y:y + side, x:x + side][m].mean())
                r = float(rev[y:y + side, x:x + side][m].mean())
                phi = float((lab[y:y + side, x:x + side] & su_w).sum() / max(1.0, su_w.sum()))
                fire = bool(f >= rule55.FWD_MIN and (f - r) >= rule55.MARGIN_MIN)
                rows.append(dict(y=y, x=x, phi=phi, fwd=f, rev=r, margin=f - r, fires=fire))
        if not rows:
            print("\n== ARM 2 (%s): no eligible window ==" % tag); out["empirical"][tag] = dict(n=0); continue
        ph = np.array([r["phi"] for r in rows]); fr = np.array([r["fires"] for r in rows])
        fired = ph[fr]; notf = ph[~fr]
        print("\n== ARM 2 (empirical, %s windows at half-unit stride, %d eligible) ==" % (tag, len(rows)))
        print("   phi range %.3f - %.3f ; fired %d, did not fire %d" % (ph.min(), ph.max(), int(fr.sum()), int((~fr).sum())))
        if fired.size:
            print("   smallest phi among FIRING windows     : %.4f (%.1f %%)" % (fired.min(), 100 * fired.min()))
        if notf.size:
            print("   largest  phi among NON-FIRING windows : %.4f (%.1f %%)" % (notf.max(), 100 * notf.max()))
        # the fitted line, as a cross-check on arm 1
        A = np.vstack([ph, np.ones_like(ph)]).T
        cf, _, _, _ = np.linalg.lstsq(A, np.array([r["fwd"] for r in rows]), rcond=None)
        cm, _, _, _ = np.linalg.lstsq(A, np.array([r["margin"] for r in rows]), rcond=None)
        print("   fitted  fwd(phi) = %.4f phi + %.4f   ->  0.36 at phi = %.4f" % (cf[0], cf[1], (rule55.FWD_MIN - cf[1]) / cf[0]))
        print("   fitted  mar(phi) = %.4f phi + %.4f   ->  0.08 at phi = %.4f" % (cm[0], cm[1], (rule55.MARGIN_MIN - cm[1]) / cm[0]))
        out["empirical"][tag] = dict(n=len(rows), side_px=side, stride=stride,
                                     phi_min=float(ph.min()), phi_max=float(ph.max()),
                                     n_fired=int(fr.sum()), n_not=int((~fr).sum()),
                                     phi_min_firing=(float(fired.min()) if fired.size else None),
                                     phi_max_nonfiring=(float(notf.max()) if notf.size else None),
                                     fit_fwd=[float(cf[0]), float(cf[1])], fit_margin=[float(cm[0]), float(cm[1])],
                                     fit_phi_floor_fwd=float((rule55.FWD_MIN - cf[1]) / cf[0]),
                                     fit_phi_floor_margin=float((rule55.MARGIN_MIN - cm[1]) / cm[0]),
                                     windows=rows)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print("\nwrote %s" % a.out)


if __name__ == "__main__":
    main()
