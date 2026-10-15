#!/usr/bin/env python
"""Level-4 preservation survey of the 23 eligible volumes (master prompt v4, 1 and 6; day-0 task).

Per volume: (a) fetch <ct>.zarr/metadata.json and compare
scan.tomo.acquisition.detector.samplePixelSize*1000 with the catalogue pixel_size_um and the master
prompt pitch (any mismatch > 0.001 um is flagged); (b) read the level-4 .zarray and fail loudly unless
uint8, no compressor, 128^3 chunks, '/' separator; (c) fetch only the chunk plane containing the middle
z slice at level 4 (16-way thread pool, cached under <cache>/<scroll>/4/iz/iy/ix) and assemble the mid
xy slice; (d) compute the metric below and write records/survey_<date>.json + a montage PNG.

METRIC (declared before the first run, fixed):
  on-scroll mask   = (slice > 0) eroded by 3 px (binary erosion, 3x3 cross, 3 iterations).
  layer contrast   = median over the mask of local_std / max(local_mean, 1), where local_mean and
                     local_std are computed in a 7x7 uniform window on the float slice (scipy uniform_filter;
                     std = sqrt(max(E[x^2] - E[x]^2, 0))). High = many bright/dark alternations
                     (well-separated windings), ~0 for a uniform disk.
  air-gap fraction = fraction of mask pixels with value < 0.5 * median(slice[mask]).
  on-scroll area   = mask pixel count * (16*um/1e4 cm)^2, in cm^2 at level 4.
Only the ranking by layer contrast is compared with the section-6 ranking (Spearman rho); the scale
differs because the section-6 metric was undocumented.

Montage: one panel per scroll, the raw slice (vmin 0, vmax 255, no enhancement), 1 cm bar =
round(10000/(16*um)) px, um/px stated, metric in the title. Idempotent per volume (skips volumes with an
entry in the JSON); montage/ranking are regenerated from the JSON on every run.

usage: survey_level4.py [--out-dir records] [--cache /home/user/hercules_data/ct_l4_cache] [--only PHerc0125 ...]
"""
import argparse, json, os, sys, datetime
from concurrent.futures import ThreadPoolExecutor
import numpy as np, requests
from scipy.ndimage import binary_erosion, uniform_filter
from scipy.stats import spearmanr
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
CATALOGUE = DATA + "/cat/metadata.min.json"
CACHE = DATA + "/ct_l4_cache"
LEVEL = 4
SCALE = 2 ** LEVEL
WINDOW = 7          # declared metric window
ERODE = 3           # declared mask erosion in px
THREADS = 16
# Master prompt v4 section 1: eligible volumes and pitch.
UM864 = {"PHerc0175A", "PHerc0175B", "PHerc0268", "PHerc0306B", "PHerc0343", "PHerc0483A", "PHerc0483B",
         "PHerc0490A", "PHerc0490B", "PHerc0800", "PHerc1218", "PHerc1447"}
ELIGIBLE = [("PHerc0125", "20250821151825"), ("PHerc0175A", "20250521115057"), ("PHerc0175B", "20250521125822"),
            ("PHerc0191", "20250821151635"), ("PHerc0211", "20250821151803"), ("PHerc0257", "20250821151750"),
            ("PHerc0268", "20251110183117"), ("PHerc0306B", "20250521133212"), ("PHerc0343", "20250521140437"),
            ("PHerc0358", "20250821151737"), ("PHerc0483A", "20250521140913"), ("PHerc0483B", "20251124083638"),
            ("PHerc0490A", "20250521151210"), ("PHerc0490B", "20250521151215"), ("PHerc0800", "20250521135224"),
            ("PHerc0813", "20250821151723"), ("PHerc0826", "20250821151701"), ("PHerc0846A", "20250728152254"),
            ("PHerc0846B", "20250804142305"), ("PHerc1203", "20250820131727"), ("PHerc1218", "20250521120456"),
            ("PHerc1447", "20250521151220"), ("PHerc1545", "20250821151648")]
PROMPT_PITCH = {s: (8.64 if s in UM864 else 9.362) for s, _ in ELIGIBLE}
# Master prompt v4 section 6: previous (undocumented) survey values, for the ranking comparison only.
SECTION6 = {"PHerc1447": .535, "PHerc0175A": .507, "PHerc0800": .501, "PHerc0343": .496, "PHerc0306B": .479,
            "PHerc0490A": .467, "PHerc0490B": .450, "PHerc0813": .447, "PHerc0483B": .443, "PHerc0826": .434,
            "PHerc0175B": .424, "PHerc1203": .421, "PHerc0191": .414, "PHerc0358": .414, "PHerc1218": .410,
            "PHerc0125": .409, "PHerc0483A": .403, "PHerc0211": .397, "PHerc0257": .393, "PHerc0846B": .391,
            "PHerc0846A": .379, "PHerc0268": .371, "PHerc1545": .346}


# ---------------------------------------------------------------- pure functions (tested)
def scroll_mask(sl, erode=ERODE):
    return binary_erosion(sl > 0, iterations=erode) if erode else sl > 0


def layer_contrast(sl, mask, window=WINDOW):
    f = sl.astype(np.float64)
    m = uniform_filter(f, window, mode="reflect")
    v = uniform_filter(f * f, window, mode="reflect") - m * m
    ratio = np.sqrt(np.maximum(v, 0)) / np.maximum(m, 1.0)
    return float(np.median(ratio[mask])) if mask.any() else float("nan")


def air_gap_fraction(sl, mask):
    if not mask.any():
        return float("nan")
    vals = sl[mask].astype(np.float64)
    return float((vals < 0.5 * np.median(vals)).mean())


def area_cm2(mask, um, scale=SCALE):
    return float(mask.sum() * (scale * um / 1e4) ** 2)


def metrics(sl, um):
    mask = scroll_mask(sl)
    return {"layer_contrast": layer_contrast(sl, mask), "air_gap_fraction": air_gap_fraction(sl, mask),
            "on_scroll_area_cm2": area_cm2(mask, um), "on_scroll_px": int(mask.sum()),
            "on_scroll_median": float(np.median(sl[mask])) if mask.any() else float("nan")}


# ---------------------------------------------------------------- remote access
def ct_path(scroll, vol, cat):
    for d in cat["samples"][scroll]["volumes"][vol]["data"]:
        if d["type"] == "ome-zarr":
            return d["origins"][0]["path"].rstrip("/")
    raise KeyError(f"no ome-zarr for {scroll}/{vol}")


def get(url, cache_path=None, retries=4):
    if cache_path and os.path.exists(cache_path):
        return open(cache_path, "rb").read()
    for i in range(retries):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 404:
                return None
            r.raise_for_status(); break
        except Exception as e:
            if i == retries - 1: raise
            print("  retry", i + 1, url, e, file=sys.stderr)
    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        tmp = cache_path + ".part"; open(tmp, "wb").write(r.content); os.replace(tmp, cache_path)
    return r.content


def check_zarray(meta):
    ok = (meta.get("zarr_format") == 2 and meta.get("dtype") == "|u1" and meta.get("compressor") is None
          and list(meta.get("chunks", [])) == [128, 128, 128] and meta.get("dimension_separator") == "/"
          and meta.get("order") == "C" and not meta.get("filters"))
    if not ok:
        raise SystemExit(f"level-{LEVEL} .zarray does not match the expected layout: {meta}")


def fetch_mid_slice(base, meta, cache_dir):
    Z, Y, X = meta["shape"]; cz, cy, cx = meta["chunks"]
    z = Z // 2; iz, oz = divmod(z, cz)
    ny, nx = -(-Y // cy), -(-X // cx)
    out = np.zeros((Y, X), np.uint8)
    def one(iy_ix):
        iy, ix = iy_ix
        raw = get(f"{base}/{LEVEL}/{iz}/{iy}/{ix}", os.path.join(cache_dir, str(LEVEL), str(iz), str(iy), str(ix)))
        return iy, ix, raw
    with ThreadPoolExecutor(THREADS) as ex:
        for iy, ix, raw in ex.map(one, [(iy, ix) for iy in range(ny) for ix in range(nx)]):
            if raw is None: continue
            blk = np.frombuffer(raw, np.uint8).reshape(cz, cy, cx)[oz]
            h, w = min(cy, Y - iy * cy), min(cx, X - ix * cx)
            out[iy * cy:iy * cy + h, ix * cx:ix * cx + w] = blk[:h, :w]
    return z, out


def survey_one(scroll, vol, cat, cache):
    path = ct_path(scroll, vol, cat); base = f"{BUCKET}/{path}"
    md = json.loads(get(f"{base}/metadata.json"))
    um_meta = md["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"] * 1000
    um_cat = cat["samples"][scroll]["volumes"][vol]["properties"]["pixel_size_um"]
    um_prompt = PROMPT_PITCH[scroll]
    mismatch = max(abs(um_meta - um_cat), abs(um_meta - um_prompt)) > 1e-3
    meta = json.loads(get(f"{base}/{LEVEL}/.zarray")); check_zarray(meta)
    cdir = os.path.join(cache, scroll); os.makedirs(cdir, exist_ok=True)
    z, sl = fetch_mid_slice(base, meta, cdir)
    np.save(os.path.join(cdir, f"mid_slice_L{LEVEL}_z{z}.npy"), sl)
    rec = {"scroll": scroll, "volume": vol, "ct_path": path, "um_metadata": um_meta, "um_catalogue": um_cat,
           "um_prompt": um_prompt, "pixel_size_mismatch": bool(mismatch), "level": LEVEL,
           "level_shape_zyx": meta["shape"], "mid_z_level4": z, "mid_z_level0": z * SCALE,
           "um_per_px_level4": um_meta * SCALE, "bar_px": round(10000 / (SCALE * um_meta)),
           "slice_file": os.path.join(cdir, f"mid_slice_L{LEVEL}_z{z}.npy")}
    rec.update(metrics(sl, um_meta))
    return rec


# ---------------------------------------------------------------- outputs
def ranking_table(recs):
    ours = sorted(recs, key=lambda r: -r["layer_contrast"])
    prev = sorted(SECTION6, key=lambda s: -SECTION6[s])
    rank_prev = {s: i + 1 for i, s in enumerate(prev)}
    rho = spearmanr([r["layer_contrast"] for r in ours], [SECTION6[r["scroll"]] for r in ours]).statistic \
        if len(ours) > 2 else float("nan")
    lines = [f"{'#':>2} {'ours (layer contrast)':<28} {'air-gap':>7} {'cm2':>6} | {'section 6':<20} | prev rank"]
    for i, r in enumerate(ours):
        p = prev[i] if i < len(prev) else ""
        lines.append(f"{i+1:>2} {r['scroll']:<11}{r['layer_contrast']:.4f}{'':<11} {r['air_gap_fraction']:7.3f} "
                     f"{r['on_scroll_area_cm2']:6.2f} | {p:<11}{SECTION6.get(p, float('nan')):.3f}{'':<6} | "
                     f"{rank_prev[r['scroll']]:>3}")
    lines.append(f"Spearman rho (ours vs section 6, n={len(ours)}): {rho:.3f}")
    return "\n".join(lines), float(rho)


def montage(recs, png, um_note="level 4"):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    ours = sorted(recs, key=lambda r: -r["layer_contrast"])
    n = len(ours); cols = 5; rows = -(-n // cols)
    fig, axs = plt.subplots(rows, cols, figsize=(cols * 3.2, rows * 3.4))
    for ax in axs.flat: ax.axis("off")
    for ax, r in zip(axs.flat, ours):
        sl = np.load(r["slice_file"])
        ax.imshow(sl, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        bar = r["bar_px"]; H, W = sl.shape
        ax.plot([W * 0.05, W * 0.05 + bar], [H * 0.95, H * 0.95], color="yellow", lw=3)
        ax.text(W * 0.05, H * 0.93, f"1 cm = {bar} px", color="yellow", fontsize=7)
        ax.set_title(f"{r['scroll']} LC {r['layer_contrast']:.3f}\nair {r['air_gap_fraction']:.2f} "
                     f"{r['on_scroll_area_cm2']:.1f} cm2 {r['um_per_px_level4']:.3f} um/px", fontsize=8)
    fig.suptitle(f"Mid xy slice at pyramid {um_note}, raw uint8 (no enhancement); sorted by layer contrast")
    fig.tight_layout(rect=(0, 0, 1, 0.97)); fig.savefig(png, dpi=110); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "records"))
    ap.add_argument("--cache", default=CACHE); ap.add_argument("--catalogue", default=CATALOGUE)
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--only", nargs="*", default=None, help="subset of scroll ids")
    a = ap.parse_args()
    cat = json.load(open(a.catalogue)); os.makedirs(a.out_dir, exist_ok=True)
    jpath = os.path.join(a.out_dir, f"survey_{a.date}.json")
    doc = json.load(open(jpath)) if os.path.exists(jpath) else {"metric": __doc__.split("METRIC")[1].split("Montage")[0].strip(),
                                                                "level": LEVEL, "volumes": {}}
    for scroll, vol in ELIGIBLE:
        if a.only and scroll not in a.only: continue
        if scroll in doc["volumes"]:
            print("skip (done)", scroll); continue
        print("survey", scroll, vol, flush=True)
        rec = survey_one(scroll, vol, cat, a.cache)
        print(f"  um meta {rec['um_metadata']:.4f} cat {rec['um_catalogue']} prompt {rec['um_prompt']} "
              f"mismatch={rec['pixel_size_mismatch']} z={rec['mid_z_level4']} LC={rec['layer_contrast']:.4f} "
              f"air={rec['air_gap_fraction']:.3f} area={rec['on_scroll_area_cm2']:.2f} cm2", flush=True)
        doc["volumes"][scroll] = rec
        json.dump(doc, open(jpath, "w"), indent=1)
    recs = list(doc["volumes"].values())
    if not recs: return
    table, rho = ranking_table(recs)
    doc["ranking_ours"] = [r["scroll"] for r in sorted(recs, key=lambda r: -r["layer_contrast"])]
    doc["ranking_section6"] = sorted(SECTION6, key=lambda s: -SECTION6[s])
    doc["spearman_vs_section6"] = rho
    doc["mismatches"] = [r["scroll"] for r in recs if r["pixel_size_mismatch"]]
    doc["montage_png"] = os.path.join(a.out_dir, f"survey_{a.date}_montage.png")
    json.dump(doc, open(jpath, "w"), indent=1)
    montage(recs, doc["montage_png"])
    print(table); print("mismatches:", doc["mismatches"]); print("wrote", jpath, doc["montage_png"])


if __name__ == "__main__":
    main()
