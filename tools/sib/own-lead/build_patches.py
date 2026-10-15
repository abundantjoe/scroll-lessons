# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-OWN patch-set builder (DECL-P4-23 items 1-3; order step 2). Deterministic; numbers only (no pixel is viewed).

Inputs:
  * p4-excl certification of T (logs/sib/p4-excl/p4own/): certified cells {seg, y0, x0, h, w, min_dist_mm} in canvas px
    of each segment's 2.4 um canvas, every mesh point of a cell >= 1.2 mm (3-D point-to-surface) from every X mesh
    point; and label shards (.npz: seg, y0, x0, ink uint8/bool, sup bool; optional scale = canvas px per label px).
    `load_excl` is the only format adapter.
  * CT: organizer 2.4 um surface volume, level 0, slices 23..84 forward (own_common.read_region = p4o_tiles).
Rules (fixed before any label pixel is read):
  * Zone T: w010-027 tiles c0-c8 r0-r7 and every w028-037 tile. A patch is kept only if every pixel lies in T tiles and
    inside certified cells (so every mesh point is >= 1.2 mm from X), and it never touches X (asserted).
  * Training patch: a P x P px input window whose central CORE x CORE px (the loss region; margin M = (P-CORE)/2) lies
    on the CORE grid aligned at canvas (0, 0). The WHOLE input window must be in T and certified (its CT voxels enter
    training). Kept if the core is mesh-valid >= 50 % and label-covered (sup & mesh-valid) >= 25 %.
  * Cap (disk): at most --max-patches; if more qualify, all ink patches (core ink >= 2 %) are kept first and the rest
    are drawn with numpy default_rng(20260927).choice without replacement, then re-sorted.
  * Feasibility count (DECL-P4-23 item 2): 64 x 64 px cells on the grid aligned at (0,0) inside certified T with
    (sup & mesh-valid) >= 50 % of the cell and ink >= 2 % of those covered px. INFEASIBLE if < 2000.
Outputs (--out dir): shard_XXX/{x.npy uint8 (n,62,P,P), ink.npy uint8 (n,P,P) = round(255 x ink fraction), sup.npy uint8 (n,P,P) (= sup & valid),
  valid.npy uint8 (n,P,P)} written with np.save (byte-deterministic), patches.json (per patch: seg, y0, x0, tile r/c,
  tiles covered, ink_frac, sup_frac, min_dist_mm), feasibility.json, and build_manifest.json with the sha256 of every
  file. Workers rebuild with the same command and check every sha256 (--verify)."""
import argparse
import concurrent.futures as cf
import glob
import json
import os

import numpy as np

import own_common as C

T_TILES_W010 = {(r, c) for r in range(8) for c in range(9)}
SHARD_MAX_BYTES = 85_000_000


def in_t(seg, r, c):
    if seg == C.X_SEG:
        return (r, c) in T_TILES_W010
    return seg in C.SEGS and seg != C.X_SEG


def tiles_of(y0, y1, x0, x1, T):
    return [(r, c) for r in range(y0 // T, (y1 - 1) // T + 1) for c in range(x0 // T, (x1 - 1) // T + 1)]


class Excl:
    """T certification + labels from p4-excl. Two formats:
    (a) p4-excl t_cert.py: T_cert.json + T_mask_<strip>.npz (per-tile bool masks on the x4 tile grid) and
        labels.json + labels/<strip>_r<R>_c<C>.npz (ink, sup counts of n_sub sub-samples on the x`grid` tile grid);
        see logs/sib/own-lead/p4own/LABEL_INTERFACE.md.
    (b) cells/shards (cert.json + shards.json), used by the synthetic tests.
    labels() returns (ink fraction float32 in [0,1], sup bool) at canvas px; certified() -> (bool, lower bound mm)."""

    def __init__(self, cells=None, shards=None, masks=None, mask_ds=4, lab_tiles=None, lab_grid=4, tile_min=None):
        self.cells = cells or []
        self.shards = shards or []
        self.masks = masks            # {(seg, r, c): bool array} or None
        self.mask_ds = mask_ds
        self.lab_tiles = lab_tiles    # {(seg, r, c): path} or None
        self.lab_grid = lab_grid
        self.tile_min = tile_min or {}
        self._cache = {}
        self._lru = []
        self._idx = {}               # (seg, tile r, tile c) -> cells overlapping that strip-a tile
        for c in self.cells:
            for t in tiles_of(c['y0'], c['y0'] + c['h'], c['x0'], c['x0'] + c['w'], C.tile_px(c['seg'])):
                self._idx.setdefault((c['seg'],) + t, []).append(c)

    def cert_tiles(self):
        if self.masks is not None:
            return sorted(k for k, m in self.masks.items() if m.any())
        return sorted({(c['seg'],) + t for c in self.cells
                       for t in tiles_of(c['y0'], c['y0'] + c['h'], c['x0'], c['x0'] + c['w'], C.tile_px(c['seg']))})

    def _gridded(self, get, seg, y0, y1, x0, x1, g, dtype):
        """Fill a (h, w) canvas-px window from per-tile arrays on the x`g` tile grid (missing tile -> 0)."""
        T = C.tile_px(seg)
        out = np.zeros((y1 - y0, x1 - x0), dtype)
        for r, c in tiles_of(y0, y1, x0, x1, T):
            a = get(seg, r, c)
            if a is None:
                continue
            ya, yb = max(y0, r * T), min(y1, (r + 1) * T)
            xa, xb = max(x0, c * T), min(x1, (c + 1) * T)
            iy = (np.arange(ya, yb) - r * T) // g
            ix = (np.arange(xa, xb) - c * T) // g
            out[ya - y0:yb - y0, xa - x0:xb - x0] = a[np.ix_(iy, ix)]
        return out

    def certified(self, seg, y0, y1, x0, x1):
        """(fully certified, min_dist_mm lower bound): format (a) certifies >= 1.2 mm per cell (p4-excl rule)."""
        if self.masks is not None:
            cov = self._gridded(lambda s, r, c: self.masks.get((s, r, c)), seg, y0, y1, x0, x1, self.mask_ds, bool)
            return bool(cov.all()), 1.2
        cover = np.zeros((y1 - y0, x1 - x0), bool)
        dmin = np.inf
        cand = {id(c): c for t in tiles_of(y0, y1, x0, x1, C.tile_px(seg)) for c in self._idx.get((seg,) + t, [])}
        for c in cand.values():
            ya, yb = max(y0, c['y0']), min(y1, c['y0'] + c['h'])
            xa, xb = max(x0, c['x0']), min(x1, c['x0'] + c['w'])
            if ya < yb and xa < xb:
                cover[ya - y0:yb - y0, xa - x0:xb - x0] = True
                dmin = min(dmin, float(c['min_dist_mm']))
        return bool(cover.all()), dmin

    def _lab_tile(self, seg, r, c):
        k = (seg, r, c)
        if k not in self.lab_tiles:
            return None
        if k not in self._cache:
            z = np.load(self.lab_tiles[k])
            ns = float(z['n_sub']) if 'n_sub' in z else 1.0
            sup_n = z['sup'].astype(np.float32)
            ink_n = z['ink'].astype(np.float32)
            sup = sup_n >= ns / 2
            ink = np.where(sup_n > 0, ink_n / np.maximum(sup_n, 1), 0).astype(np.float32)
            self._cache[k] = (ink, sup)
            self._lru.append(k)
            while len(self._lru) > 24:
                self._cache.pop(self._lru.pop(0), None)
        return self._cache[k]

    def _load(self, s):
        k = s['path']
        if k not in self._cache:
            z = np.load(k)
            ink = (z['ink'] > 0).astype(np.float32)
            sup = z['sup'].astype(bool)
            sc = int(s.get('scale', 1))
            if sc > 1:
                ink = np.repeat(np.repeat(ink, sc, 0), sc, 1)
                sup = np.repeat(np.repeat(sup, sc, 0), sc, 1)
            self._cache = {k: (ink, sup)}   # one shard resident (memory bound)
        return self._cache[k]

    def labels(self, seg, y0, y1, x0, x1):
        if self.lab_tiles is not None:
            g = self.lab_grid
            ink = self._gridded(lambda s, r, c: (self._lab_tile(s, r, c) or (None, None))[0], seg, y0, y1, x0, x1, g,
                                np.float32)
            sup = self._gridded(lambda s, r, c: (self._lab_tile(s, r, c) or (None, None))[1], seg, y0, y1, x0, x1, g,
                                bool)
            return ink, sup
        ink = np.zeros((y1 - y0, x1 - x0), np.float32)
        sup = np.zeros((y1 - y0, x1 - x0), bool)
        for s in self.shards:
            if s['seg'] != seg:
                continue
            ya, yb = max(y0, s['y0']), min(y1, s['y0'] + s['h'])
            xa, xb = max(x0, s['x0']), min(x1, s['x0'] + s['w'])
            if ya < yb and xa < xb:
                si, ss = self._load(s)
                sl = (slice(ya - s['y0'], yb - s['y0']), slice(xa - s['x0'], xb - s['x0']))
                d = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0))
                ink[d] = np.maximum(ink[d], si[sl])
                sup[d] |= ss[sl]
        return ink, sup


SHORT = {s.split('-', 1)[1]: s for s in C.SEGS}


def load_excl(d):
    """p4-excl p4own directory, format (a) if T_cert.json exists, else (b). Every sha256 in the manifests is checked;
    any label file of an X tile is refused."""
    if os.path.exists(os.path.join(d, 'T_cert.json')):
        tc = json.load(open(os.path.join(d, 'T_cert.json')))
        masks, tile_min = {}, {}
        ds = 4
        for name, st in tc['strips'].items():
            seg = SHORT.get(name, name)
            assert int(st['T_px']) == C.tile_px(seg), (name, st['T_px'], C.tile_px(seg))
            p = os.path.join(d, st['mask_file'])
            if C.sha256_file(p) != st['mask_file_sha256']:
                raise SystemExit(f'{p} sha256 mismatch')
            z = np.load(p)
            for k in z.files:
                strip, rr, cc = k.rsplit('_', 2)
                r, c = int(rr[1:]), int(cc[1:])
                if C.in_x_zone(seg, r, c):
                    raise SystemExit(f'T mask for X tile {k}')
                masks[(seg, r, c)] = z[k].astype(bool)
        for k, e in tc['tiles'].items():
            tile_min[(SHORT.get(e['strip'], e['strip']), e['r'], e['c'])] = e.get('min_dist_to_X_mm')
        lab_tiles, g = {}, 4
        import re
        ljs = sorted(glob.glob(os.path.join(d, 'labels_*.json'))) or sorted(glob.glob(os.path.join(d, 'labels.json')))
        for lj in ljs:   # per-strip manifests (labels.json only if none)
            L = json.load(open(lj))
            g = int(re.match(r'x(\d+)', str(L.get('grid', 'x4'))).group(1))
            for f in L['files']:
                seg = SHORT.get(f['strip'], f['strip'])
                if C.in_x_zone(seg, f['r'], f['c']):
                    raise SystemExit(f'label file of X tile {f["file"]} refused')
                p = os.path.join(d, f['file'])
                if C.sha256_file(p) != f['sha256']:
                    raise SystemExit(f'label file {p} sha256 mismatch')
                lab_tiles[(seg, f['r'], f['c'])] = p
        return Excl(masks=masks, mask_ds=ds, lab_tiles=lab_tiles, lab_grid=g, tile_min=tile_min)
    cert = json.load(open(os.path.join(d, 'cert.json')))
    sm = json.load(open(os.path.join(d, 'shards.json')))
    shards = []
    for s in sm['shards']:
        p = os.path.join(d, s['file'])
        got = C.sha256_file(p)
        if got != s['sha256']:
            raise SystemExit(f'label shard {p} sha256 {got} != {s["sha256"]}')
        sc = int(s.get('scale', 1))
        shards.append(dict(seg=s['seg'], y0=int(s['y0']), x0=int(s['x0']), h=int(s['h']) * sc, w=int(s['w']) * sc,
                           scale=sc, path=p))
    for s in shards:
        for (r, c) in tiles_of(s['y0'], s['y0'] + s['h'], s['x0'], s['x0'] + s['w'], C.tile_px(s['seg'])):
            if C.in_x_zone(s['seg'], r, c):
                # labels of X must never be read by this builder: the shard must not overlap X at all
                raise SystemExit(f'label shard {s["path"]} overlaps X tile r{r} c{c}')
    return Excl(cert['cells'], shards)


def candidate_grid(ex, P):
    """Deterministic sorted list of candidate CORE origins (seg, y0, x0) on the P grid over the certified tiles."""
    out = set()
    for seg, r, c in ex.cert_tiles():
        T = C.tile_px(seg)
        for y in range(((r * T) // P) * P, (r + 1) * T, P):
            for x in range(((c * T) // P) * P, (c + 1) * T, P):
                out.add((seg, y, x))
    return sorted(out)


def feasibility(ex, valid_by_seg, cell=64):
    """DECL-P4-23 item 2 count on 64 x 64 cells inside certified T (the (0,0)-aligned 64 grid)."""
    n_lab = n_ink = 0
    for seg, y, x in candidate_grid(ex, cell):
        if not all(in_t(seg, r, cc) for r, cc in tiles_of(y, y + cell, x, x + cell, C.tile_px(seg))):
            continue
        ok, _ = ex.certified(seg, y, y + cell, x, x + cell)
        if not ok:
            continue
        ink, sup = ex.labels(seg, y, y + cell, x, x + cell)
        v = C.canvas_mask(seg, valid_by_seg[seg], y, y + cell, x, x + cell)
        cov = sup & v
        if cov.mean() < 0.5:
            continue
        n_lab += 1
        if ink[cov].mean() >= 0.02:
            n_ink += 1
    return dict(rule='64x64 cells on the (0,0)-aligned grid inside certified T; labelled = (sup & mesh-valid) >= 50 % '
                     'of the cell; ink >= 2 % of covered px (ink = mean label ink fraction)', n_labelled_cells=n_lab,
                n_ink_cells_ge2pct=n_ink, bar=2000, feasible=bool(n_ink >= 2000))


def feasibility_fast(ex, valid_by_seg, cell=64, band=1024):
    """Exact vectorised equivalent of feasibility(): per-strip per-cell sums of certified, covered (sup & valid) and
    ink px at canvas resolution, accumulated tile by tile in row bands."""
    n_lab = n_ink = 0
    for seg in sorted({t[0] for t in ex.cert_tiles()}):
        H, W = C.SEGS[seg]
        T = C.tile_px(seg)
        nc_y, nc_x = -(-H // cell), -(-W // cell)
        CERT = np.zeros((nc_y, nc_x), np.int64)
        COV = np.zeros((nc_y, nc_x), np.int64)
        INK = np.zeros((nc_y, nc_x), np.float64)
        for (s, r, c) in ex.cert_tiles():
            if s != seg or not in_t(seg, r, c):
                continue
            y0, y1 = r * T, min((r + 1) * T, H)
            x0, x1 = c * T, min((c + 1) * T, W)
            for by in range(y0, y1, band):
                be = min(by + band, y1)
                ok = ex._gridded(lambda s_, r_, c_: ex.masks.get((s_, r_, c_)) if ex.masks is not None else None,
                                 seg, by, be, x0, x1, ex.mask_ds, bool) if ex.masks is not None else \
                    np.array([[ex.certified(seg, yy, yy + 1, xx, xx + 1)[0] for xx in range(x0, x1)]
                              for yy in range(by, be)])
                ink, sup = ex.labels(seg, by, be, x0, x1)
                v = C.canvas_mask(seg, valid_by_seg[seg], by, be, x0, x1)
                cov = sup & v & ok
                cy = (np.arange(by, be) // cell)[:, None]
                cx = (np.arange(x0, x1) // cell)[None, :]
                idx = (cy * nc_x + cx).ravel()
                CERT.ravel()[:] += np.bincount(idx, weights=ok.ravel(), minlength=nc_y * nc_x).astype(np.int64)
                COV.ravel()[:] += np.bincount(idx, weights=cov.ravel(), minlength=nc_y * nc_x).astype(np.int64)
                INK.ravel()[:] += np.bincount(idx, weights=(ink * cov).ravel(), minlength=nc_y * nc_x)
        full = CERT == cell * cell
        # cells cut by the canvas edge can never be fully certified (they are not 64 x 64 inside the canvas)
        lab = full & (COV >= 0.5 * cell * cell)
        n_lab += int(lab.sum())
        n_ink += int((lab & (INK >= 0.02 * np.maximum(COV, 1))).sum())
    return dict(rule='64x64 cells on the (0,0)-aligned grid inside certified T; labelled = (sup & mesh-valid) >= 50 % '
                     'of the cell; ink >= 2 % of covered px (ink = mean label ink fraction)', n_labelled_cells=n_lab,
                n_ink_cells_ge2pct=n_ink, bar=2000, feasible=bool(n_ink >= 2000), method='vectorised exact')


def select(ex, valid_by_seg, P, core=None, max_patches=0):
    """Patches as input windows (y0, x0 = window origin, P x P) with loss core CORE x CORE at offset M."""
    core = core or P
    M = (P - core) // 2
    keep = []
    for seg, cy, cx in candidate_grid(ex, core):
        y0, x0 = cy - M, cx - M
        H, W = C.SEGS[seg]
        if y0 < 0 or x0 < 0 or y0 + P > H or x0 + P > W:
            continue
        T = C.tile_px(seg)
        tl = tiles_of(y0, y0 + P, x0, x0 + P, T)
        if any(C.in_x_zone(seg, r, c) for r, c in tl) or not all(in_t(seg, r, c) for r, c in tl):
            continue
        ok, dmin = ex.certified(seg, y0, y0 + P, x0, x0 + P)
        if not ok:
            continue
        assert dmin >= 1.2, (seg, y0, x0, dmin)
        v = C.canvas_mask(seg, valid_by_seg[seg], cy, cy + core, cx, cx + core)
        if v.mean() < 0.5:
            continue
        ink, sup = ex.labels(seg, cy, cy + core, cx, cx + core)
        cov = sup & v
        if cov.mean() < 0.25:
            continue
        yc, xc = cy + core // 2, cx + core // 2
        keep.append(dict(seg=seg, y0=y0, x0=x0, core=core, margin=M, r=yc // T, c=xc // T,
                         tiles=[list(t) for t in tl], ink_frac=float(ink[cov].mean()), sup_frac=float(cov.mean()),
                         min_dist_mm=dmin, tile_min_dist_mm=[ex.tile_min.get((seg,) + tuple(t)) for t in tl]))
    n_q = len(keep)
    if max_patches and n_q > max_patches:
        ink_i = [i for i, p in enumerate(keep) if p['ink_frac'] >= 0.02]
        rest = [i for i, p in enumerate(keep) if p['ink_frac'] < 0.02]
        rng = np.random.default_rng(20260927)
        if len(ink_i) >= max_patches:
            sel = sorted(rng.choice(ink_i, max_patches, replace=False).tolist())
        else:
            sel = sorted(ink_i + rng.choice(rest, max_patches - len(ink_i), replace=False).tolist())
        keep = [keep[i] for i in sel]
    return keep, n_q


def write_shards(ex, valid_by_seg, keep, P, out, threads=4):
    per = max(1, SHARD_MAX_BYTES // (C.NZ * P * P + 3 * P * P))
    files = {}
    for si in range(0, len(keep), per):
        part = keep[si:si + per]
        sd = os.path.join(out, f'shard_{si // per:03d}')
        os.makedirs(sd, exist_ok=True)
        if os.path.exists(os.path.join(sd, 'done.json')):
            files.update(json.load(open(os.path.join(sd, 'done.json'))))
            continue

        def one(p):
            img, rd = C.read_region(p['seg'], p['y0'], p['y0'] + P, p['x0'], p['x0'] + P)
            return np.ascontiguousarray(np.transpose(img, (2, 0, 1))), rd

        with cf.ThreadPoolExecutor(threads) as tp:
            res = list(tp.map(one, part))
        X = np.stack([r[0] for r in res])
        INK = np.zeros((len(part), P, P), np.uint8)
        SUP = np.zeros((len(part), P, P), np.uint8)
        VAL = np.zeros((len(part), P, P), np.uint8)
        for i, p in enumerate(part):
            v = C.canvas_mask(p['seg'], valid_by_seg[p['seg']], p['y0'], p['y0'] + P, p['x0'], p['x0'] + P)
            ink, sup = ex.labels(p['seg'], p['y0'], p['y0'] + P, p['x0'], p['x0'] + P)   # whole window is in T
            INK[i], SUP[i], VAL[i] = np.rint(ink * 255).astype(np.uint8), (sup & v), v
            p['chunks_missing'] = res[i][1]['chunks_missing']
            p['chunk_records_sha256'] = res[i][1]['chunk_records_sha256']
        fs = {}
        for n, a in (('x', X), ('ink', INK), ('sup', SUP), ('valid', VAL)):
            f = os.path.join(sd, f'{n}.npy')
            np.save(f, a)
            fs[os.path.relpath(f, out)] = C.sha256_file(f)
        json.dump(fs, open(os.path.join(sd, 'done.json'), 'w'))
        files.update(fs)
        print(json.dumps(dict(shard=sd, n=len(part), utc=C.utc())), flush=True)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--excl', required=True, help='p4-excl p4own directory (cert.json, shards.json, shards/)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--patch', type=int, required=True, help='input window P')
    ap.add_argument('--core', type=int, default=0, help='loss core (default P)')
    ap.add_argument('--max-patches', type=int, default=0)
    ap.add_argument('--verify', default='', help='build_manifest.json to check every sha256 against')
    ap.add_argument('--count-only', action='store_true')
    ap.add_argument('--manifest-only', action='store_true')
    a = ap.parse_args()
    ex = load_excl(a.excl)
    segs = sorted({t[0] for t in ex.cert_tiles()})
    assert all(s in C.SEGS for s in segs), segs
    valid = {s: C.load_valid(s) for s in segs}
    os.makedirs(a.out, exist_ok=True)
    fp = os.path.join(a.out, 'feasibility.json')
    if a.manifest_only and os.path.exists(fp):
        feas = json.load(open(fp))
    else:
        feas = feasibility_fast(ex, valid)
        json.dump(feas, open(fp, 'w'), indent=1)
    print(json.dumps(feas), flush=True)
    if a.count_only or not feas['feasible']:
        return
    pj = os.path.join(a.out, 'patches.json')
    if a.manifest_only:          # shards and patches.json already complete (resume after a manifest-step crash)
        keep, n_qual = json.load(open(pj))['patches'], None
        files = {}
        for sd in sorted(glob.glob(os.path.join(a.out, 'shard_*'))):
            files.update(json.load(open(os.path.join(sd, 'done.json'))))
    else:
        keep, n_qual = select(ex, valid, a.patch, a.core or a.patch, a.max_patches)
        files = write_shards(ex, valid, keep, a.patch, a.out)
        json.dump(dict(patch=a.patch, core=a.core or a.patch, n=len(keep), patches=keep), open(pj, 'w'))
    man = dict(provenance=C.PROV, declaration='RULES.md DECL-P4-23 items 1-3', patch=a.patch, core=a.core or a.patch,
               n_qualifying=n_qual, max_patches=a.max_patches, n_patches=len(keep),
               n_ink_patches_ge2pct=sum(p['ink_frac'] >= 0.02 for p in keep),
               min_dist_to_X_mm=min(p['min_dist_mm'] for p in keep) if keep else None,
               segments=segs, feasibility=feas, files=files, patches_json_sha256=C.sha256_file(pj),
               excl_sha256={os.path.basename(p): C.sha256_file(p) for p in
                            sorted(glob.glob(os.path.join(a.excl, '*.json')) + glob.glob(os.path.join(a.excl, '*.npz')))},
               total_bytes=int(sum(os.path.getsize(os.path.join(a.out, f)) for f in files)),
               code_sha256={n: C.sha256_file(os.path.join(C.HERE, n)) for n in ('build_patches.py', 'own_common.py')},
               input='2.4 um level 0 slices 23..84 forward; clip(0,200)/255 applied at training time', utc=C.utc())
    mp = os.path.join(a.out, 'build_manifest.json')
    if a.verify:
        ref = json.load(open(a.verify))
        bad = [f for f, h in ref['files'].items() if files.get(f) != h]
        if bad or ref['patches_json_sha256'] != man['patches_json_sha256']:
            raise SystemExit(f'VERIFY FAILED: {len(bad)} shard files differ; patches.json '
                             f'{man["patches_json_sha256"]} vs {ref["patches_json_sha256"]}')
        man['verified_against'] = C.sha256_file(a.verify)
    json.dump(man, open(mp, 'w'), indent=1)
    print(json.dumps({k: v for k, v in man.items() if k != 'files'}), flush=True)


if __name__ == '__main__':
    main()
