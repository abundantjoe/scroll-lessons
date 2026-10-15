#!/usr/bin/env python
"""The w028 JUDGE (master prompt 5.4): pixel ROC AUC of a 9 um map on UNLABELLED w028 text vs blank.
Reference = the team's 2.4 um w028 prediction block-averaged 4x4 onto the pooled canvas (9355x7585) / 255.
text = reference >= 0.40; blank = reference <= 0.25; on-sheet only (pooled CT mid slice > 0);
pixels within 60 px of any labelled letter (inklabels slice 10 > 0) excluded. Constants are frozen here.
Subcommands:
  build  --team-tif T --pooled P --labels L --out DIR   -> reference_u8.npy (mean*255), class masks, preview PNG, meta.json
  score  --ref DIR --forward F.tif [--reverse R.tif] [--json out]   -> AUC forward (and reverse)
"""
import argparse, json, os
import numpy as np, tifffile, zarr
from scipy import ndimage
from sklearn.metrics import roc_auc_score

TEXT_THR, BLANK_THR, EXCL_PX, UM = 0.40, 0.25, 60, 2.399 * 4  # frozen (5.4)

def block_average_4x4(tif_path, out_shape):
    """Stream the tiled 2.4 um TIFF in row bands and mean-pool 4x4 -> uint8 (mean*1, i.e. still 0..255 scale)."""
    store = tifffile.imread(tif_path, aszarr=True)
    z = zarr.open(store, mode="r")
    H, W = z.shape
    assert (H // 4, W // 4) == tuple(out_shape), (z.shape, out_shape)
    out = np.zeros(out_shape, dtype=np.uint8)
    band = 1024
    for y0 in range(0, H, band):
        y1 = min(H, y0 + band)
        a = np.asarray(z[y0:y1, :W - W % 4]).astype(np.float32)
        a = a[: (y1 - y0) - (y1 - y0) % 4]
        m = a.reshape(a.shape[0] // 4, 4, a.shape[1] // 4, 4).mean(axis=(1, 3))
        out[y0 // 4: y0 // 4 + m.shape[0], : m.shape[1]] = np.rint(m).astype(np.uint8)
    store.close()
    return out

def build(a):
    os.makedirs(a.out, exist_ok=True)
    marker = os.path.join(a.out, ".complete")
    if os.path.exists(marker) and not a.force:
        print("reference exists", a.out); return
    g = zarr.open_group(a.pooled, mode="r"); ct = g["0"]
    nz = ct.shape[0]; mid = ct[nz // 2]
    ref = block_average_4x4(a.team_tif, mid.shape)
    lab = zarr.open_group(a.labels, mode="r")["0"][10] > 0
    excl = ndimage.binary_dilation(lab, iterations=EXCL_PX) if lab.any() else lab
    onsheet = mid > 0
    r = ref.astype(np.float32) / 255.0
    text = onsheet & ~excl & (r >= TEXT_THR)
    blank = onsheet & ~excl & (r <= BLANK_THR)
    np.save(os.path.join(a.out, "reference_u8.npy"), ref)
    np.save(os.path.join(a.out, "text_mask.npy"), text); np.save(os.path.join(a.out, "blank_mask.npy"), blank)
    np.save(os.path.join(a.out, "onsheet_mask.npy"), onsheet); np.save(os.path.join(a.out, "excluded_mask.npy"), excl)
    meta = {"team_tif": a.team_tif, "pooled": a.pooled, "labels": a.labels, "canvas": list(mid.shape), "um": UM,
            "mid_slice": nz // 2, "text_thr": TEXT_THR, "blank_thr": BLANK_THR, "exclude_px": EXCL_PX,
            "n_onsheet": int(onsheet.sum()), "n_excluded_onsheet": int((excl & onsheet).sum()),
            "n_text": int(text.sum()), "n_blank": int(blank.sum()), "labelled_px": int(lab.sum())}
    json.dump(meta, open(os.path.join(a.out, "meta.json"), "w"), indent=1); print(json.dumps(meta, indent=1))
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        s = 8; bar = round(10000 / UM) // s
        fig, ax = plt.subplots(1, 3, figsize=(18, 7))
        ax[0].imshow(mid[::s, ::s], cmap="gray"); ax[0].set_title("pooled CT mid slice")
        ax[1].imshow(ref[::s, ::s], cmap="magma", vmin=0, vmax=255); ax[1].set_title("team 2.4um prediction, 4x4 mean (reference)")
        cls = np.zeros(mid[::s, ::s].shape + (3,), np.uint8); cls[text[::s, ::s]] = (255, 80, 0); cls[blank[::s, ::s]] = (0, 120, 255); cls[excl[::s, ::s] & onsheet[::s, ::s]] = (90, 90, 90)
        ax[2].imshow(cls); ax[2].set_title("judge classes: text (orange) / blank (blue) / excluded (grey)")
        for x in ax:
            x.plot([20, 20 + bar], [x.get_ylim()[0] - 40] * 2, "w-", lw=4); x.text(20, x.get_ylim()[0] - 60, f"1 cm = {round(10000/UM)} px @ {UM:.3f} um/px", color="w", fontsize=8); x.set_xticks([]); x.set_yticks([])
        plt.tight_layout(); plt.savefig(os.path.join(a.out, "reference_preview.png"), dpi=110); plt.close()
    except Exception as e:
        print("preview failed:", e)
    open(marker, "w").write("ok\n")

def score_one(ref_dir, tif):
    text = np.load(os.path.join(ref_dir, "text_mask.npy")); blank = np.load(os.path.join(ref_dir, "blank_mask.npy"))
    p = tifffile.imread(tif)
    if p.ndim == 3: p = p[0]
    assert p.shape == text.shape, (p.shape, text.shape)
    y = np.concatenate([np.ones(int(text.sum()), np.uint8), np.zeros(int(blank.sum()), np.uint8)])
    s = np.concatenate([p[text], p[blank]]).astype(np.float32) / 255.0
    return {"tif": tif, "auc": float(roc_auc_score(y, s)), "mean_text": float(s[y == 1].mean()), "mean_blank": float(s[y == 0].mean()),
            "n_text": int(text.sum()), "n_blank": int(blank.sum())}

def score(a):
    out = {"forward": score_one(a.ref, a.forward)}
    if a.reverse: out["reverse"] = score_one(a.ref, a.reverse)
    print(json.dumps(out, indent=1))
    if a.json: json.dump(out, open(a.json, "w"), indent=1)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--team-tif", required=True); b.add_argument("--pooled", required=True); b.add_argument("--labels", required=True); b.add_argument("--out", required=True); b.add_argument("--force", action="store_true"); b.set_defaults(f=build)
    s = sub.add_parser("score"); s.add_argument("--ref", required=True); s.add_argument("--forward", required=True); s.add_argument("--reverse"); s.add_argument("--json"); s.set_defaults(f=score)
    a = ap.parse_args(); a.f(a)
