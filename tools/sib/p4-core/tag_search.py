# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-15 (c) P4-TAG: search for a separate thin sheet (title tag /
sillybos, or wrapper) attached outside the roll body of PHerc. Paris 4, at the
top and bottom edges of the two outermost windings. Numbers only: CT chunks
are streamed into memory, reduced to voxel masks, component statistics and
coordinates, and discarded. No image is produced or viewed.

Fixed before the search (this file's first commit precedes any L4 read):
  * Material: 2.4 um volume 20260411134726 (SAM2-masked), pyramid level 4
    (38.4 um voxels) for the search.
  * Bands: L0 z from the first scanned slice to (outer-mesh z-min + 15 mm),
    and from (outer-mesh z-max - 15 mm) to the last slice.
  * Roll-body outline per 1 mm z-bin: the maximum radius per 1-degree angle
    bin (about the official umbilicus) of the vertices of the outer meshes
[line withheld: prize-candidate detail under review]
    z-range, the outline of the nearest 2 mm of mesh.
  * Papyrus-density threshold thr = 0.5 x the median L4 intensity sampled at
    the outer-mesh vertices inside the bands (sensitivity: 0.35 x).
  * Candidate voxel: I > thr and (radial excess over the outline > 0.5 mm
    OR z beyond the roll body's physical end by > 0.5 mm). The physical end
    is the last z whose in-outline occupancy is >= 5 % of the band median.
  * Components: 26-connected; a component is SHEET-LIKE if its thickness is
    <= 0.6 mm, its area is >= 2 mm^2, and its PCA planarity (l3/l1) is < 0.1.
    It is ATTACHED if its minimum excess over the outline is <= 0.6 mm.
"""

from __future__ import annotations

import json
import math
import sys
import time
import concurrent.futures as cf
import urllib.request
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

VOL = ("https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/volumes/"
       "20260411134726-2.400um-0.2m-78keV-masked.zarr")
LEVEL = 4
F = 2 ** LEVEL                  # L0 voxels per L4 voxel
VOX_MM = 2.4e-3 * F             # 0.0384 mm
CH = 128
Z_FIRST, Z_LAST = 1528, 75783   # L0 z crop of the scan (metadata.json zarr_export)
[line withheld: prize-candidate detail under review]
NBIN = 360
EXCESS_MM = 0.5
BAND_MM = 15.0


def fetch_chunk(level, cz, cy, cx):
    url = f"{VOL}/{level}/{cz}/{cy}/{cx}"
    for k in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return np.frombuffer(r.read(), np.uint8).reshape(CH, CH, CH)
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
        except Exception:
            pass
        time.sleep(2 ** k)
    raise RuntimeError(url)


def read_block(level, z0, z1, y0, y1, x0, x1, workers=32):
    """vol[level][z0:z1, y0:y1, x0:x1] as uint8 (absent chunks = 0)."""
    out = np.zeros((z1 - z0, y1 - y0, x1 - x0), np.uint8)
    jobs = [(cz, cy, cx) for cz in range(z0 // CH, (z1 - 1) // CH + 1)
            for cy in range(y0 // CH, (y1 - 1) // CH + 1) for cx in range(x0 // CH, (x1 - 1) // CH + 1)]
    absent = 0
    with cf.ThreadPoolExecutor(workers) as ex:
        for (cz, cy, cx), a in zip(jobs, ex.map(lambda j: fetch_chunk(level, *j), jobs)):
            if a is None:
                absent += 1
                continue
            gz, gy, gx = cz * CH, cy * CH, cx * CH
            sz = slice(max(z0, gz), min(z1, gz + CH))
            sy = slice(max(y0, gy), min(y1, gy + CH))
            sx = slice(max(x0, gx), min(x1, gx + CH))
            out[sz.start - z0:sz.stop - z0, sy.start - y0:sy.stop - y0, sx.start - x0:sx.stop - x0] = \
                a[sz.start - gz:sz.stop - gz, sy.start - gy:sy.stop - gy, sx.start - gx:sx.stop - gx]
    return out, absent, len(jobs)


class Outline:
    """Per 1 mm z-bin, r_out(theta) in L0 voxels about the umbilicus."""

    def __init__(self, outer_dir: Path, umb_json: Path):
        a = json.load(open(umb_json))
        self.U = np.array(sorted([[p["z"], p["x"], p["y"]] for p in a["control_points"]]), float)
        P = []
        for s in OUTER:
            x, y, z = (np.load(outer_dir / f"{s}_{c}.npy") for c in "xyz")
            m = (x != -1) & (z > 0) & np.isfinite(z)
            P.append(np.stack([x[m], y[m], z[m]], 1))
        P = np.concatenate(P).astype(np.float64)
        self.P = P
        self.zmin, self.zmax = float(P[:, 2].min()), float(P[:, 2].max())
        ux, uy = self.umb(P[:, 2])
        th = np.arctan2(P[:, 1] - uy, P[:, 0] - ux)
        r = np.hypot(P[:, 0] - ux, P[:, 1] - uy)
        b = ((th + math.pi) / (2 * math.pi) * NBIN).astype(int) % NBIN
        zb_mm = 1.0 / 2.4e-3
        self.zb0 = self.zmin
        nzb = int((self.zmax - self.zmin) // zb_mm) + 1
        zi = ((P[:, 2] - self.zmin) // zb_mm).astype(int)
        R = np.full((nzb, NBIN), np.nan)
        np.fmax.at(R, (zi, b), r)
        self.empty_frac = np.mean(~np.isfinite(R), 1)
        # circular fill of empty angle bins
        for i in range(nzb):
            row = R[i]
            f = np.isfinite(row)
            if f.sum() >= 3:
                idx = np.where(f)[0]
                vals = row[idx]
                R[i] = np.interp(np.arange(NBIN), np.r_[idx - NBIN, idx, idx + NBIN], np.r_[vals, vals, vals])
        self.R = R
        self.zb_vox = zb_mm

    def umb(self, z):
        z = np.clip(z, self.U[0, 0], self.U[-1, 0])
        return np.interp(z, self.U[:, 0], self.U[:, 1]), np.interp(z, self.U[:, 0], self.U[:, 2])

    def rout(self, z_l0: float) -> np.ndarray:
        """Outline for L0 z; beyond the mesh, the max over the nearest 2 mm."""
        n = self.R.shape[0]
        i = int((z_l0 - self.zb0) // self.zb_vox)
        if i < 0:
            return np.nanmax(self.R[:2], 0)
        if i >= n:
            return np.nanmax(self.R[-2:], 0)
        return self.R[i]


def excess_map(outline: Outline, z_l0: float, shape_yx, origin_yx_l4):
    """Radial excess over the outline (mm) for every pixel of one L4 slice."""
    H, W = shape_yx
    ux, uy = outline.umb(np.array([z_l0]))
    yy, xx = np.mgrid[0:H, 0:W]
    X = (xx + origin_yx_l4[1] + 0.5) * F
    Y = (yy + origin_yx_l4[0] + 0.5) * F
    th = np.arctan2(Y - uy[0], X - ux[0])
    r = np.hypot(X - ux[0], Y - uy[0])
    b = ((th + math.pi) / (2 * math.pi) * NBIN).astype(int) % NBIN
    ro = outline.rout(z_l0)[b]
    return (r - ro) * 2.4e-3


def components(coords: np.ndarray):
    """26-connected components of sparse integer voxel coords (n, 3)."""
    n = len(coords)
    if n == 0:
        return np.zeros(0, int), 0
    c = coords.astype(np.int64) + 1
    key = (c[:, 0] << 42) | (c[:, 1] << 21) | c[:, 2]
    order = np.argsort(key)
    ks = key[order]
    rows, cols = [], []
    offs = [(a, b, d) for a in (-1, 0, 1) for b in (-1, 0, 1) for d in (-1, 0, 1) if (a, b, d) > (0, 0, 0)]
    for o in offs:
        nk = ((c[:, 0] + o[0]) << 42) | ((c[:, 1] + o[1]) << 21) | (c[:, 2] + o[2])
        pos = np.searchsorted(ks, nk)
        pos = np.minimum(pos, n - 1)
        hit = ks[pos] == nk
        rows.append(np.nonzero(hit)[0])
        cols.append(order[pos[hit]])
    rows = np.concatenate(rows)
    cols = np.concatenate(cols)
    g = coo_matrix((np.ones(len(rows), np.int8), (rows, cols)), shape=(n, n))
    k, lab = connected_components(g, directed=False)
    return lab, k


def component_stats(coords, excess_mm, lab, k, min_vox=8):
    out = []
    for c in range(k):
        m = lab == c
        nv = int(m.sum())
        if nv < min_vox:
            continue
        P = coords[m].astype(float)
        lo = P.min(0).astype(int)
        hi = P.max(0).astype(int)
        big = np.prod(hi - lo + 3) > 2e8
        if big:  # thickness from a 200^3 sub-box around the component's median voxel
            ctr = np.median(P, 0).astype(int)
            sub = np.all(np.abs(P - ctr) < 100, 1)
            Ps = P[sub]
            lo, hi = Ps.min(0).astype(int), Ps.max(0).astype(int)
        else:
            Ps = P
        box = np.zeros(tuple(hi - lo + 3), bool)
        q = (Ps - lo + 1).astype(int)
        box[q[:, 0], q[:, 1], q[:, 2]] = True
        edt = ndimage.distance_transform_edt(box)
        # thickness: 2 x (median of local maxima of the EDT) - 1 voxel, in mm
        mx = (edt == ndimage.maximum_filter(edt, 3)) & box
        thick_vox = max(1.0, 2 * float(np.median(edt[mx])) - 1)
        vol_mm3 = nv * VOX_MM ** 3
        thick_mm = thick_vox * VOX_MM
        area_mm2 = vol_mm3 / thick_mm
        ev = np.sort(np.linalg.eigvalsh(np.cov((P - P.mean(0)).T))) if nv > 3 else np.array([0, 0, 1.0])
        planar = float(ev[0] / ev[2]) if ev[2] > 0 else 1.0
        e = excess_mm[m]
        i0 = int(np.argmin(e))
        att = coords[m][i0]
        out.append({"n_vox": nv, "volume_mm3": vol_mm3, "thickness_mm": thick_mm, "area_mm2": area_mm2,
                    "planarity_l3_over_l1": planar,
                    "z_extent_mm": [float(P[:, 0].min() * VOX_MM), float(P[:, 0].max() * VOX_MM)],
                    "bbox_l4_zyx": [P.min(0).astype(int).tolist(), P.max(0).astype(int).tolist()], "thickness_from_subbox": bool(big),
                    "min_excess_mm": float(e.min()), "max_excess_mm": float(e.max()),
                    "attachment_point_l0_xyz": [int(att[2] * F), int(att[1] * F), int(att[0] * F)],
                    "attached": bool(e.min() <= 0.6),
                    "sheet_like": bool(thick_mm <= 0.6 and area_mm2 >= 2.0 and planar < 0.1)})
    return out
