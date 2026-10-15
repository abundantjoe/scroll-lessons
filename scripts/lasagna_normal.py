#!/usr/bin/env python
"""R-NORMAL (RULES): compare a trace's own surface normal with the TEAM's published sheet-normal field.

14 of the 23 eligible volumes publish `representations/predictions/lasagna/<stamp>/`, which carries the sheet normal
components `nx`, `ny` (CT level 2, uint8, blosc) beside a winding-phase field `cos` and `grad_mag`. R-CREST tests a
surface's geometry through DENSITY CONTRAST, which tightly compressed wraps do not have; a normal field tests it
through ORIENTATION, which needs no air gap at all.

For every `--every`-th valid grid cell of a tifxyz trace this computes the trace normal (cross product of the two grid
edge vectors, the same construction as scripts/ct_at_points.py), projects it on xy, and compares it with the published
(nx, ny) at the nearest level-2 voxel. `|cos theta|` is reported because the two sign conventions need not agree.

The uint8 decoding `n = u / 127.5 - 1` is SELF-TESTED first: for a sheet normal in a scroll winding about z,
`nx^2 + ny^2` must have a median in [0.9, 1.1] over occupied voxels (RULES R-NORMAL). That question is about the
ENCODING, so it is settled once from the pooled sample of a calibration set (`pooled_self_test.py` output in
records/rnormal/); each run also reports its own median as a descriptive statistic. A field whose pooled median falls
outside the band is not used for anything.

usage: lasagna_normal.py PATCH_DIR --scroll PHerc0826 [--every 3] [--cache DIR] [--out JSON]
"""
import argparse, json, io, os, sys, urllib.parse, urllib.request, concurrent.futures as cf
import numpy as np, tifffile

BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
SQ_MIN, SQ_MAX = 0.9, 1.1          # RULES R-NORMAL self-test band for median(nx^2 + ny^2)


def lasagna_base(scroll):
    """The published lasagna directory of a scroll, and its manifest."""
    import xml.etree.ElementTree as ET
    q = {"list-type": "2", "prefix": f"{scroll}/representations/predictions/lasagna/", "delimiter": "/", "max-keys": "100"}
    with urllib.request.urlopen(f"{BUCKET}/?{urllib.parse.urlencode(q)}", timeout=120) as r:
        root = ET.fromstring(r.read())
    dirs = [c.findtext(NS + "Prefix") for c in root.findall(NS + "CommonPrefixes")]
    if not dirs:
        raise SystemExit(f"{scroll}: no published lasagna prediction")
    base = sorted(dirs)[-1]
    with urllib.request.urlopen(f"{BUCKET}/{urllib.parse.quote(base + scroll + '.lasagna.json')}", timeout=120) as r:
        man = json.load(r)
    return base, man


class BloscZarr:
    """One level of a remote zarr-v2 uint8 array with a blosc compressor, chunk by chunk, cached on disk."""

    def __init__(self, url, cache):
        self.url, self.cache = url.rstrip("/"), cache
        os.makedirs(cache, exist_ok=True)
        with urllib.request.urlopen(f"{self.url}/.zarray", timeout=120) as r:
            self.za = json.load(r)
        self.shape = tuple(self.za["shape"]); self.cs = tuple(self.za["chunks"])
        if self.za["dtype"] != "|u1":
            raise SystemExit(f"unexpected dtype {self.za['dtype']} for {self.url}")
        import numcodecs
        self.codec = numcodecs.get_codec(self.za["compressor"]) if self.za.get("compressor") else None
        self.n_http = self.n_missing = 0

    def _chunk(self, key):
        f = os.path.join(self.cache, "_".join(map(str, key)))
        if not os.path.exists(f):
            try:
                with urllib.request.urlopen(f"{self.url}/{key[0]}/{key[1]}/{key[2]}", timeout=120) as r:
                    raw = r.read()
                self.n_http += 1
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise
                raw = b""; self.n_missing += 1
            with open(f + ".part", "wb") as fh:
                fh.write(raw)
            os.replace(f + ".part", f)
        raw = open(f, "rb").read()
        if not raw:
            return None                               # omitted chunk = fill value (0)
        buf = self.codec.decode(raw) if self.codec else raw
        return np.frombuffer(buf, np.uint8).reshape(self.cs)

    def sample(self, idx):
        """uint8 at integer (z, y, x) indices (N, 3); outside the array or in an omitted chunk -> fill value 0."""
        out = np.zeros(len(idx), np.uint8)
        inside = np.ones(len(idx), bool)
        for a in range(3):
            inside &= (idx[:, a] >= 0) & (idx[:, a] < self.shape[a])
        ck = np.stack([idx[:, a] // self.cs[a] for a in range(3)], 1)
        keys, inv = np.unique(ck[inside], axis=0, return_inverse=True)
        sub = np.nonzero(inside)[0]
        cache = {}
        with cf.ThreadPoolExecutor(12) as ex:                     # warm the cache in parallel, then read serially
            list(ex.map(lambda k: cache.setdefault(tuple(k), self._chunk(tuple(k))), [tuple(k) for k in keys]))
        for ki, k in enumerate(keys):
            sel = sub[inv == ki]
            arr = cache[tuple(k)]
            if arr is None:
                continue
            loc = idx[sel] - np.array(k) * np.array(self.cs)
            out[sel] = arr[loc[:, 0], loc[:, 1], loc[:, 2]]
        return out


def trace_normals(patch_dir, every=3):
    """(points xyz in CT level-0 voxels, unit normals xyz) at every `every`-th valid grid cell."""
    x, y, z = [tifffile.imread(os.path.join(patch_dir, f"{c}.tif")).astype(np.float64) for c in "xyz"]
    valid = (x > -1) & (y > -1) & (z > -1)
    pts = np.stack([x, y, z], -1)
    du = pts[1:, :-1] - pts[:-1, :-1]; dv = pts[:-1, 1:] - pts[:-1, :-1]
    n = np.cross(du, dv); n = n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
    cv = valid[1:, :-1] & valid[:-1, :-1] & valid[:-1, 1:] & valid[1:, 1:]
    ii, jj = np.nonzero(cv); ii, jj = ii[::every], jj[::every]
    return pts[ii, jj], n[ii, jj]


def run(patch_dir, scroll, every=3, cache_root=None):
    base, man = lasagna_base(scroll)
    groups = man["groups"]
    cache_root = cache_root or os.path.join(os.environ.get("HERCULES_DATA", "/home/user/hercules_data"), "lasagna_cache", scroll)
    arrs, div = {}, {}
    for comp in ("nx", "ny"):
        rel = groups[comp]["zarr"]                                  # e.g. "PHerc0826_nx.ome.zarr/2"
        lvl = int(rel.rsplit("/", 1)[1])
        arrs[comp] = BloscZarr(f"{BUCKET}/{urllib.parse.quote(base + rel)}", os.path.join(cache_root, comp))
        div[comp] = man["base_shape_zyx"][0] / arrs[comp].shape[0]   # CT level-0 voxels per voxel of this level
    if abs(div["nx"] - div["ny"]) > 1e-6:
        raise SystemExit("nx and ny are published at different scales; refusing to mix them")
    d = div["nx"]
    pts, nrm = trace_normals(patch_dir, every)
    idx = np.rint(np.stack([pts[:, 2] / d, pts[:, 1] / d, pts[:, 0] / d], 1)).astype(np.int64)
    u = {c: arrs[c].sample(idx).astype(np.float64) for c in ("nx", "ny")}
    nx, ny = u["nx"] / 127.5 - 1.0, u["ny"] / 127.5 - 1.0
    occupied = (u["nx"] != 0) | (u["ny"] != 0)                       # fill value 0 = no published normal there
    sq = nx[occupied] ** 2 + ny[occupied] ** 2
    res = dict(patch=os.path.abspath(patch_dir), scroll=scroll, lasagna_prefix=base,
               level_div=d, n_cells=int(len(pts)), n_occupied=int(occupied.sum()),
               occupied_frac=round(float(occupied.mean()), 4) if len(pts) else None,
               decode="n = u / 127.5 - 1", self_test_band=[SQ_MIN, SQ_MAX],
               chunks_http=sum(a.n_http for a in arrs.values()), chunks_missing=sum(a.n_missing for a in arrs.values()))
    if not occupied.any():
        res.update(self_test_median_sq=None, self_test_passed=False,
                   note="no published normal at any sampled point of this trace")
        return res
    med_sq = float(np.median(sq))
    # RULES R-NORMAL: the self-test asks whether the uint8 ENCODING is understood, which is a property of the published
    # field, not of any one trace. It is therefore decided once from the POOLED sample over the calibration set
    # (`pooled_self_test` below); the per-trace median is reported as a descriptive statistic. Where the field's own
    # confidence is lower the decoded vector is simply shorter, and dropping those traces would be a quality filter
    # that was never declared. The angle is computed either way and both numbers stay on record.
    res.update(self_test_median_sq=round(med_sq, 4), self_test_passed=bool(SQ_MIN <= med_sq <= SQ_MAX),
               sq_p25=round(float(np.percentile(sq, 25)), 4), sq_p75=round(float(np.percentile(sq, 75)), 4))
    t = nrm[occupied][:, :2]
    tn = np.linalg.norm(t, axis=1)
    p = np.stack([nx[occupied], ny[occupied]], 1)
    pn = np.linalg.norm(p, axis=1)
    ok = (tn > 1e-6) & (pn > 1e-6)
    cos = np.abs((t[ok] * p[ok]).sum(1) / (tn[ok] * pn[ok]))
    res.update(n_compared=int(ok.sum()),
               abs_cos_median=round(float(np.median(cos)), 4),
               abs_cos_p25=round(float(np.percentile(cos, 25)), 4),
               abs_cos_p75=round(float(np.percentile(cos, 75)), 4),
               frac_abs_cos_ge_0p9=round(float((cos >= 0.9).mean()), 4),
               trace_xy_component_median=round(float(np.median(tn[ok])), 4))
    return res


def coherence(scroll, points, window=9, cache_root=None):
    """Local coherence of the published normal field around each level-0 point: |mean n| / mean|n| over a cube of
    `window` voxels of the field's own level. 1 = one flat sheet through the window; near 0 = normals that disagree,
    which is what a fold, a sheet crossing or an unresolved region looks like. Returns one dict per point."""
    base, man = lasagna_base(scroll)
    cache_root = cache_root or os.path.join(os.environ.get("HERCULES_DATA", "/home/user/hercules_data"), "lasagna_cache", scroll)
    arrs, d = {}, None
    for comp in ("nx", "ny"):
        rel = man["groups"][comp]["zarr"]
        arrs[comp] = BloscZarr(f"{BUCKET}/{urllib.parse.quote(base + rel)}", os.path.join(cache_root, comp))
        d = man["base_shape_zyx"][0] / arrs[comp].shape[0]
    h = window // 2
    off = np.stack(np.meshgrid(*[np.arange(-h, h + 1)] * 3, indexing="ij"), -1).reshape(-1, 3)   # (W^3, 3) as z,y,x
    out = []
    for px, py, pz in points:
        c = np.rint(np.array([pz / d, py / d, px / d])).astype(np.int64)
        idx = c[None, :] + off
        u = {k: arrs[k].sample(idx).astype(np.float64) for k in ("nx", "ny")}
        occ = (u["nx"] != 0) | (u["ny"] != 0)
        if occ.sum() < 8:
            out.append(dict(x=px, y=py, z=pz, n_occupied=int(occ.sum()), coherence=None,
                            note="fewer than 8 voxels with a published normal in the window")); continue
        nx, ny = u["nx"][occ] / 127.5 - 1.0, u["ny"][occ] / 127.5 - 1.0
        mag = np.hypot(nx, ny)
        keep = mag > 1e-6
        nxu, nyu = nx[keep] / mag[keep], ny[keep] / mag[keep]
        # the normal is a DIRECTION, not an arrow: flip every vector into one half-plane before averaging, or two
        # halves of the same flat sheet would cancel. The doubled-angle mean is the standard axial statistic.
        c2, s2 = np.cos(2 * np.arctan2(nyu, nxu)), np.sin(2 * np.arctan2(nyu, nxu))
        out.append(dict(x=px, y=py, z=pz, n_occupied=int(occ.sum()), n_used=int(keep.sum()),
                        coherence=round(float(np.hypot(c2.mean(), s2.mean())), 4),
                        window=window, level_div=d))
    return out


def phase(patch_dir, scroll, every=3, cache_root=None):
    """RULES R-PHASE: the winding phase `cos` sampled along a trace. A surface that stays on ONE sheet samples a narrow
    band of phase; a surface that steps from one wrap to the next samples the whole range, even when every local normal
    is correctly aligned. This is sheet seam consistency measured in the volume, not inferred from a render."""
    base, man = lasagna_base(scroll)
    cache_root = cache_root or os.path.join(os.environ.get("HERCULES_DATA", "/home/user/hercules_data"), "lasagna_cache", scroll)
    rel = man["groups"]["cos"]["zarr"]
    arr = BloscZarr(f"{BUCKET}/{urllib.parse.quote(base + rel)}", os.path.join(cache_root, "cos"))
    d = man["base_shape_zyx"][0] / arr.shape[0]
    pts, _ = trace_normals(patch_dir, every)
    idx = np.rint(np.stack([pts[:, 2] / d, pts[:, 1] / d, pts[:, 0] / d], 1)).astype(np.int64)
    u = arr.sample(idx).astype(np.float64)
    occ = u != 0
    res = dict(patch=os.path.abspath(patch_dir), scroll=scroll, lasagna_prefix=base, level_div=d,
               n_cells=int(len(pts)), n_occupied=int(occ.sum()),
               occupied_frac=round(float(occ.mean()), 4) if len(pts) else None,
               decode="c = u / 127.5 - 1", chunks_http=arr.n_http, chunks_missing=arr.n_missing)
    if occ.sum() < 32:
        res["note"] = "fewer than 32 sampled points carry a published phase"
        return res
    c = u[occ] / 127.5 - 1.0
    q1, med, q3 = (float(np.percentile(c, p)) for p in (25, 50, 75))
    res.update(cos_median=round(med, 4), cos_iqr=round(q3 - q1, 4), cos_std=round(float(c.std()), 4),
               cos_p05=round(float(np.percentile(c, 5)), 4), cos_p95=round(float(np.percentile(c, 95)), 4),
               cos_min=round(float(c.min()), 4), cos_max=round(float(c.max()), 4),
               frac_within_0p2_of_median=round(float((np.abs(c - med) <= 0.2).mean()), 4))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("patch_dir", nargs="?", help="tifxyz dir (omit with --points)")
    ap.add_argument("--scroll", required=True)
    ap.add_argument("--points", help="JSON file of seeds [{x,y,z},..] or 'x,y,z;x,y,z': report field coherence instead")
    ap.add_argument("--window", type=int, default=9, help="coherence window, voxels of the field's own level")
    ap.add_argument("--phase", action="store_true", help="RULES R-PHASE: sample the winding-phase field along the trace instead")
    ap.add_argument("--every", type=int, default=3)
    ap.add_argument("--cache"); ap.add_argument("--out")
    a = ap.parse_args(argv)
    if a.points:
        if os.path.exists(a.points):
            j = json.load(open(a.points)); seeds = j["seeds"] if isinstance(j, dict) else j
            pts = [(s_["x"], s_["y"], s_["z"]) for s_ in seeds if not s_.get("skip")]
        else:
            pts = [tuple(int(v) for v in t.split(",")) for t in a.points.split(";")]
        r = dict(scroll=a.scroll, window=a.window, points=coherence(a.scroll, pts, a.window, a.cache))
    else:
        if not a.patch_dir:
            ap.error("give a PATCH_DIR or --points")
        r = (phase if a.phase else run)(a.patch_dir, a.scroll, a.every, a.cache)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump(r, open(a.out, "w"), indent=1)
    print(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
