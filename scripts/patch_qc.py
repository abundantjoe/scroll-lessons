#!/usr/bin/env python
"""Patch QC (MASTER_PROMPT_v4 5.8) for a tifxyz dir (x/y/z.tif float32 level-0 voxel coordinates, meta.json; invalid <= 0 or NaN).
Geometry: per-cell normals = cross(u diff, v diff); PASS if mean |n_z| <= 0.50 AND frac(|n_z| > 0.7) <= 0.25 AND area >= 0.5 cm^2
  (sum of cell parallelogram areas in vx^2 x (um*1e-4)^2).
CT-mask check: 100 well-spread valid points sampled at CT level 4 (coords / 16, axes z y x) from the remote zarr-v2 over HTTPS,
  one 128^3 chunk at a time (no compressor, verified in .zarray; cached under --cache; 404 = fill). A patch proceeds
  when zero_frac <= 0.50 OR the estimated in-mask area (1 - zero_frac) * area_cm2 >= 1.5 cm2 (RULES, in-mask area arm);
  otherwise UNREADABLE.
Overlay (--overlay): level-4 CT slice at the patch's median z (values unaltered, integer nearest-neighbour upscale only) with the
  patch points within +-8 level-0 voxels drawn as red dots; 1 cm bar = round(10000/(um/px)) px, um/px stated.
Idempotent: qc.json + marker .qc_done in the patch dir; a cached result is reused only if it covers the requested um / coord_scale /
  CT url / overlay; --force re-runs. Without --ct-url the voxel size is UNVERIFIED (provisional verdict).
Batch: patch_qc.py <parent_dir> --batch ... prints one line per auto_grown_* child (--overlay is then a directory)."""
import argparse, json, os, sys, time, threading
import numpy as np, tifffile, requests
from concurrent.futures import ThreadPoolExecutor; from requests.adapters import HTTPAdapter; from urllib3.util.retry import Retry
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

# Bars from MASTER_PROMPT_v4 section 5.8 (frozen)
NZ_MEAN_MAX, NZ_FRAC_LEVEL, NZ_FRAC_MAX, AREA_CM2_MIN = 0.50, 0.7, 0.25, 0.5
CT_LEVEL, CT_SCALE, CT_N_SAMPLES, CT_ZERO_FRAC_MAX, SLAB_HALF_VX = 4, 16, 100, 0.50, 8
CT_IN_MASK_CM2_MIN = 1.5   # RULES: second arm of the CT-mask bar, (1 - zero_frac) * area_cm2
BARS = {"mean_abs_nz_max": NZ_MEAN_MAX, "frac_abs_nz_gt_0p7_max": NZ_FRAC_MAX, "area_cm2_min": AREA_CM2_MIN,
        "ct_level": CT_LEVEL, "ct_n_samples": CT_N_SAMPLES, "ct_zero_frac_max": CT_ZERO_FRAC_MAX,
        "ct_in_mask_cm2_min": CT_IN_MASK_CM2_MIN}
MARKER, CATALOGUE = ".qc_done", DATA + "/cat/metadata.min.json"


def load_tifxyz(patch_dir):
    mp = os.path.join(patch_dir, "meta.json")
    return (*[tifffile.imread(os.path.join(patch_dir, n + ".tif")).astype(np.float64) for n in "xyz"],
            json.load(open(mp)) if os.path.exists(mp) else {})


def valid_mask(x, y, z):
    return np.isfinite(x) & np.isfinite(y) & np.isfinite(z) & (x > 0) & (y > 0) & (z > 0)


def cell_normals(x, y, z):
    """Unit normals (H-1, W-1, 3), parallelogram areas in vx^2 and the valid-cell mask (three corners valid)."""
    P = np.stack([x, y, z], -1)
    v = valid_mask(x, y, z)
    du, dv = P[:-1, 1:] - P[:-1, :-1], P[1:, :-1] - P[:-1, :-1]
    n = np.cross(du, dv); area = np.linalg.norm(n, axis=-1)
    ok = v[:-1, :-1] & v[:-1, 1:] & v[1:, :-1] & (area > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        n = n / area[..., None]
    return n, area, ok


def geometry_stats(x, y, z, um):
    n, area, ok = cell_normals(x, y, z)
    nz, v = np.abs(n[..., 2][ok]), valid_mask(x, y, z)
    area_vx2 = float(area[ok].sum())
    r = {"grid_shape": list(x.shape), "n_valid_points": int(v.sum()), "n_valid_cells": int(ok.sum()),
         "mean_abs_nz": float(nz.mean()) if nz.size else None,
         "frac_abs_nz_gt_0p7": float((nz > NZ_FRAC_LEVEL).mean()) if nz.size else None,
         "area_vx2": area_vx2, "area_cm2": area_vx2 * (um * 1e-4) ** 2,
         "bbox_min_xyz": [float(a[v].min()) for a in (x, y, z)] if v.any() else None,
         "bbox_max_xyz": [float(a[v].max()) for a in (x, y, z)] if v.any() else None,
         "median_z": float(np.median(z[v])) if v.any() else None}
    r["geometry_pass"] = bool(nz.size and r["mean_abs_nz"] <= NZ_MEAN_MAX
                              and r["frac_abs_nz_gt_0p7"] <= NZ_FRAC_MAX and r["area_cm2"] >= AREA_CM2_MIN)
    return r


def spread_points(x, y, z, n):
    """n well-spread valid points (x, y, z): farthest-point sampling in grid-index space from the centroid."""
    rr, cc = np.nonzero(valid_mask(x, y, z))
    if rr.size == 0: return np.zeros((0, 3))
    ij = np.stack([rr, cc], 1).astype(np.float64)
    chosen = [int(np.argmin(((ij - ij.mean(0)) ** 2).sum(1)))]
    d = ((ij - ij[chosen[0]]) ** 2).sum(1)
    for _ in range(min(n, rr.size) - 1): k = int(np.argmax(d)); chosen.append(k); d = np.minimum(d, ((ij - ij[k]) ** 2).sum(1))
    return np.stack([a[rr[chosen], cc[chosen]] for a in (x, y, z)], 1)


class ChunkedCT:
    """One pyramid level of a remote zarr-v2 volume (uint8, no compressor, '/' separator), chunk by chunk over
    HTTPS with a disk cache. A 404 chunk is the fill value (masked volumes omit empty chunks)."""

    def __init__(self, base_url, level, cache_dir=None):
        self.url, self.level = base_url.rstrip("/"), level
        self.cache = os.path.join(cache_dir, str(level)) if cache_dir else None
        self.s = requests.Session()
        self.s.mount("http", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])))
        self.n_fetched, self.n_http, self.n_missing, self.lock = 0, 0, 0, threading.Lock()
        za = json.loads(self.get(".zarray").decode())
        if not (za.get("zarr_format") == 2 and za.get("compressor") is None and za.get("filters") is None
                and za.get("dtype") == "|u1" and za.get("order") == "C" and za.get("dimension_separator") == "/"):
            raise RuntimeError(f"unexpected .zarray for {self.url}/{level}: {za}")
        self.zarray, self.shape, self.chunks = za, tuple(za["shape"]), tuple(za["chunks"])
        self.fill = int(za.get("fill_value") or 0)

    def get(self, key, level=True):
        """Raw bytes of <url>/<level>/<key> (or <url>/<key> if level=False, cached at the store root); None for 404."""
        path = os.path.join(self.cache if level else os.path.dirname(self.cache), key) if self.cache else None
        if path and os.path.exists(path): return open(path, "rb").read()
        elif path and os.path.exists(path + ".missing"): return None
        r = self.s.get(f"{self.url}/{self.level}/{key}" if level else f"{self.url}/{key}", timeout=120)
        data = None if r.status_code == 404 else (r.raise_for_status() or r.content)
        with self.lock: self.n_http += 1
        if path:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if data is None: open(path + ".missing", "w").close()
            else: open(path + ".part", "wb").write(data); os.replace(path + ".part", path)
        return data

    def chunk(self, cz, cy, cx):
        data = self.get(f"{cz}/{cy}/{cx}")
        with self.lock: self.n_missing += data is None; self.n_fetched += data is not None
        if data is None: return np.full(self.chunks, self.fill, np.uint8)
        if len(data) != int(np.prod(self.chunks)): raise RuntimeError(f"chunk {cz}/{cy}/{cx}: {len(data)} bytes")
        return np.frombuffer(data, np.uint8).reshape(self.chunks)

    def blocks(self, keys):
        with ThreadPoolExecutor(4) as ex:
            return dict(zip(keys, ex.map(lambda k: self.chunk(*k), keys)))

    def sample(self, idx_zyx):
        """uint8 values at integer level indices (N, 3) in z y x order; outside the array -> fill value."""
        idx, ch = np.asarray(idx_zyx, int).reshape(-1, 3), np.array(self.chunks)
        out, inside, ck = np.full(len(idx), self.fill, np.uint8), np.all((idx >= 0) & (idx < np.array(self.shape)), 1), idx // ch
        bl = self.blocks(sorted({tuple(k) for k in ck[inside]}))
        for i in np.nonzero(inside)[0]:
            o = idx[i] - ck[i] * ch
            out[i] = bl[tuple(ck[i])][o[0], o[1], o[2]]
        return out

    def slice(self, zi):
        """The whole level slice at z index zi (H, W) uint8."""
        (cz, oz), ch, img = divmod(int(zi), self.chunks[0]), self.chunks, np.full(self.shape[1:], self.fill, np.uint8)
        bl = self.blocks([(cz, cy, cx) for cy in range(-(-self.shape[1] // ch[1])) for cx in range(-(-self.shape[2] // ch[2]))])
        for (_, cy, cx), b in bl.items():
            h, w = min(ch[1], self.shape[1] - cy * ch[1]), min(ch[2], self.shape[2] - cx * ch[2])
            img[cy * ch[1]:cy * ch[1] + h, cx * ch[2]:cx * ch[2] + w] = b[oz][:h, :w]
        return img


def voxel_size_um(ct, catalogue=None):
    """um from the volume's metadata.json (samplePixelSize mm x 1000) and, if the catalogue is present, its
    pixel_size_um for the same <scroll>/volumes/<vol> path; None where unavailable."""
    out, data, parts = {"metadata_um": None, "catalogue_um": None}, ct.get("metadata.json", level=False), ct.url.split("/")
    if data: out["metadata_um"] = float(json.loads(data)["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]) * 1000
    if catalogue and os.path.exists(catalogue) and "volumes" in parts:
        scroll, vol = parts[parts.index("volumes") - 1], parts[-1].split("-")[0]
        try: out["catalogue_um"] = float(json.load(open(catalogue))["samples"][scroll]["volumes"][vol]["properties"]["pixel_size_um"])
        except (KeyError, ValueError): pass
    return out


def draw_overlay(ct_slice, pts_xy_l4, um_per_px_l4, out_png, zi, upscale=None):
    """Level-4 CT slice (values unaltered, integer nearest-neighbour upscale) with patch points as red dots;
    1 cm bar of exactly round(10000/um_per_px) px and the um/px text in a black band below the panel."""
    import cv2
    (H, W), k = ct_slice.shape, int(upscale or max(1, round(1200 / ct_slice.shape[1]))); um_px = um_per_px_l4 / k
    bar, bx, band = int(round(10000 / um_px)), 8, 32
    img = np.zeros((H * k + band, max(W * k, bar + 2 * bx + 1), 3), np.uint8)  # canvas never narrower than the bar
    img[:H * k, :W * k] = np.repeat(np.repeat(ct_slice, k, 0), k, 1)[..., None]
    for X, Y in pts_xy_l4:
        cv2.circle(img, (int(round(X * k)), int(round(Y * k))), max(1, k // 2), (0, 0, 255), -1)
    by, bh = H * k + 6, 4
    img[by:by + bh, bx:bx + bar] = 255
    txt = f"1 cm = {bar} px   {um_px:.3f} um/px   CT level {CT_LEVEL} z={zi}   {len(pts_xy_l4)} patch points within +-{SLAB_HALF_VX} vx"
    cv2.putText(img, txt, (bx, by + bh + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imwrite(out_png, img)
    return {"path": os.path.abspath(out_png), "slice_z_l4": int(zi), "n_points_drawn": int(len(pts_xy_l4)),
            "bar_px": bar, "bar_xy": [bx, by], "bar_height_px": bh, "um_per_px": um_px, "upscale": k,
            "panel_size_px": [W * k, H * k], "image_size_px": [img.shape[1], img.shape[0]]}


def cached_covers(c, um, coord_scale, ct_url, overlay):
    """True if a cached qc.json was produced with the same um / coord_scale and already includes the requested CT
    check and overlay (a geometry-only run must not shadow a later CT-mask check or overlay request)."""
    return (c.get("um") == um and c.get("coord_scale") == coord_scale
            and (ct_url is None or bool(c.get("ct")) and c["ct"].get("url") == ct_url.rstrip("/"))
            and (overlay is None or bool(c.get("overlay")) and os.path.exists(c["overlay"]["path"])
                 and os.path.abspath(c["overlay"]["path"]) == os.path.abspath(overlay)))


def qc_patch(patch_dir, um, ct_url=None, overlay=None, cache=None, force=False, coord_scale=1.0, catalogue=CATALOGUE):
    """Run the QC on one tifxyz dir; returns (result dict, skipped). coord_scale = level-0 CT voxels per
    tifxyz coordinate unit (4 for meshes traced on an L2 surface prediction of a 2.4 um volume)."""
    qc_path, marker = os.path.join(patch_dir, "qc.json"), os.path.join(patch_dir, MARKER)
    if os.path.exists(marker) and os.path.exists(qc_path) and not force and cached_covers(json.load(open(qc_path)), um, coord_scale, ct_url, overlay):
        return json.load(open(qc_path)), True
    x, y, z, meta = load_tifxyz(patch_dir)
    r = {"patch_dir": os.path.abspath(patch_dir), "um": um, "coord_scale": coord_scale, "bars": BARS,
         "meta_scale": meta.get("scale"), "meta_bbox": meta.get("bbox")}
    r.update(geometry_stats(x, y, z, um))
    if "area_vx2" in meta:
        r["meta_area_vx2"], r["meta_area_cm2"] = float(meta["area_vx2"]), float(meta["area_vx2"]) * (um * 1e-4) ** 2
    verdict, r["ct"], r["overlay"], r["voxel_size_check"] = ("PASS" if r["geometry_pass"] else "FAIL"), None, None, "UNVERIFIED"
    if ct_url and r["n_valid_points"]:
        ct_url = ct_url.rstrip("/"); ct = ChunkedCT(ct_url, CT_LEVEL, cache)
        r["voxel_size_check"] = vs = voxel_size_um(ct, catalogue)
        for k, v in vs.items():
            if v is not None and abs(v * coord_scale - um) > 0.005 * um:
                raise SystemExit(f"--um {um} disagrees with {k} {v} x coord_scale {coord_scale}; refusing")
        pts = spread_points(x, y, z, CT_N_SAMPLES)
        vals = ct.sample(np.floor(pts[:, ::-1] * coord_scale / CT_SCALE).astype(int))
        zf = float((vals == 0).mean())
        r["ct"] = {"url": ct_url, "level": CT_LEVEL, "shape": list(ct.shape), "chunks": list(ct.chunks),
                   "zarray": ct.zarray, "n_samples": int(vals.size), "n_zero": int((vals == 0).sum()), "zero_frac": zf,
                   "mean_value": float(vals.mean()), "chunks_loaded": ct.n_fetched, "chunks_http": ct.n_http, "chunks_missing": ct.n_missing}
        # RULES "QC CT-mask bar: an in-mask AREA arm beside the zero-fraction arm": the zero-fraction bar sits inside a
        # dense continuum, not a gap, and it gates render COST only (the read takes its on-sheet mask from the render's
        # CT mid slice and rule 5.5 needs >= 90 % on-sheet per unit). A patch also proceeds when the estimated in-mask
        # area is at least the 1.5 cm2 rule 5.5 needs before it will call anything BLANK.
        in_mask = (1.0 - zf) * float(r["area_cm2"])
        r["ct"]["in_mask_cm2"] = round(in_mask, 4)
        r["ct"]["in_mask_cm2_min"] = CT_IN_MASK_CM2_MIN
        if zf <= CT_ZERO_FRAC_MAX:
            r["ct"]["arm"] = "zero_frac"
        elif in_mask >= CT_IN_MASK_CM2_MIN:
            r["ct"]["arm"] = "in_mask_area"
        else:
            r["ct"]["arm"] = None
            verdict = "UNREADABLE"
        if overlay:
            zi = int(r["median_z"] * coord_scale // CT_SCALE)
            slab = valid_mask(x, y, z) & (np.abs(z * coord_scale - (zi * CT_SCALE + CT_SCALE / 2)) <= SLAB_HALF_VX)
            pts_l4 = np.stack([x[slab], y[slab]], 1) * coord_scale / CT_SCALE
            r["overlay"] = draw_overlay(ct.slice(zi), pts_l4, CT_SCALE * um / coord_scale, overlay, zi)
    r["verdict"], r["time"] = verdict, time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(r, open(qc_path, "w"), indent=1)
    open(marker, "w").write(verdict + "\n")
    return r, False


def one_line(r, skipped=False):
    f = lambda v, p=3: "nan" if v is None else f"{v:.{p}f}"
    ct = r.get("ct") or {}
    return (f"{os.path.basename(r['patch_dir'])} {r['verdict']} mean|nz|={f(r['mean_abs_nz'])} "
            f"frac>0.7={f(r['frac_abs_nz_gt_0p7'])} area={f(r['area_cm2'], 2)}cm2 cells={r['n_valid_cells']} "
            f"ct_zero={f(ct.get('zero_frac'), 2)}/{ct.get('n_samples', 0)}" + (" [cached]" if skipped else "")
            + (" [um UNVERIFIED: no --ct-url]" if r.get("voxel_size_check") == "UNVERIFIED" else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("patch_dir", help="tifxyz dir, or a parent dir of auto_grown_* patches (batch)")
    ap.add_argument("--um", type=float, required=True, help="um per coordinate unit (from the volume metadata.json; cross-checked against it and the catalogue when --ct-url is given, else UNVERIFIED)")
    ap.add_argument("--ct-url", default=None, help="base URL of the masked CT OME-zarr (levels 0..5); omit for a provisional geometry-only run")
    ap.add_argument("--overlay", default=None, help="overlay PNG (single patch) or output dir (batch)"); ap.add_argument("--cache", default=None, help="chunk cache dir, e.g. /home/user/hercules_data/ct_l4_cache/<scroll>")
    ap.add_argument("--coord-scale", type=float, default=1.0, help="level-0 CT voxels per coordinate unit (4 for L2-traced 2.4 um meshes)")
    ap.add_argument("--catalogue", default=CATALOGUE); ap.add_argument("--batch", action="store_true"); ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    dirs = [a.patch_dir]
    if a.batch or not os.path.exists(os.path.join(a.patch_dir, "x.tif")):
        dirs = sorted(d.path for d in os.scandir(a.patch_dir) if d.is_dir() and (d.name.startswith("auto_grown_") or d.name.startswith("team_")))
        if not dirs: sys.exit(f"{a.patch_dir}: no x.tif and no auto_grown_* children")
    for d in dirs:
        ov = a.overlay
        if ov and (len(dirs) > 1 or a.batch or os.path.isdir(ov)):
            os.makedirs(ov, exist_ok=True); ov = os.path.join(ov, os.path.basename(d.rstrip("/")) + "_overlay.png")
        try:
            r, skipped = qc_patch(d, a.um, a.ct_url, ov, a.cache, a.force, a.coord_scale, a.catalogue)
            print(one_line(r, skipped), flush=True)
        except Exception as e:  # batch mode: one failing patch must not stop the others
            if len(dirs) == 1: raise
            print(f"{os.path.basename(d)} ERROR {type(e).__name__}: {e}", flush=True)


if __name__ == "__main__":
    main()
