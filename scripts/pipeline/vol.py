"""Self-contained readers for the PHerc0268 open data (anonymous S3): CT pyramid, lasagna phase fields, organizers' surface prediction.

Coordinates are always (z, y, x).  `Vol(name, level)` reads any pyramid level as dense blocks; `Sampler` does trilinear sampling of
level-0 (or any level) at arbitrary points with an in-RAM chunk cache bounded by `max_gb` (oldest chunks evicted).
"""
import json, time, numpy as np
from concurrent.futures import ThreadPoolExecutor

BUCKET = 'vesuvius-challenge-open-data/PHerc0268'
CT = f'{BUCKET}/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr'
LAS = f'{BUCKET}/representations/predictions/lasagna/20251110183117-lasagna-20260419180421'
SURF = f'{BUCKET}/representations/predictions/surfaces/20251110183117-surface-20260413222639-surface-m7-L0-th0.2.zarr'
PATHS = {'ct': CT, 'surf': SURF, 'cos': f'{LAS}/PHerc0268_cos.ome.zarr', 'grad_mag': f'{LAS}/PHerc0268_grad_mag.ome.zarr',
         'nx': f'{LAS}/PHerc0268_nx.ome.zarr', 'ny': f'{LAS}/PHerc0268_ny.ome.zarr'}
VOX_UM = 8.64
_FS = None


def fs():
    global _FS
    if _FS is None:
        import s3fs; _FS = s3fs.S3FileSystem(anon=True)
    return _FS


class Vol:
    """One pyramid level of one dataset. Missing chunks read as 0."""
    def __init__(self, name, level, threads=48):
        self.key = f'{PATHS.get(name, name)}/{level}'; self.level = level; za = json.loads(fs().cat_file(self.key + '/.zarray'))
        self.shape, self.chunks, self.sep = za['shape'], za['chunks'], za.get('dimension_separator', '.')
        self.codec = None
        if za.get('compressor'):
            from numcodecs import get_codec; self.codec = get_codec(za['compressor'])
        self.ex = ThreadPoolExecutor(threads); self.cache = {}; self.cache_max = 0; self.fetched = 0

    def set_cache(self, gb):
        """Keep up to `gb` GB of decoded chunks in RAM (oldest evicted first): blocks that overlap reuse them."""
        self.cache_max = int(gb * 1e9 / np.prod(self.chunks))

    def chunk(self, ijk):
        """Fetch and decode one chunk (thread-safe; no caching here)."""
        self.fetched += 1; k = self.key + '/' + self.sep.join(str(v) for v in ijk)
        for attempt in range(6):
            try: raw = fs().cat_file(k); break
            except FileNotFoundError: return ijk, None
            except Exception:
                if attempt == 5: raise
                time.sleep(1.5 * (attempt + 1))
        if self.codec is not None: raw = self.codec.decode(raw)
        return ijk, np.frombuffer(raw, np.uint8).reshape(self.chunks)

    def block(self, z0, z1, y0, y1, x0, x1):
        """Dense uint8 block in this level's voxel units; out-of-range parts are 0."""
        cz, cy, cx = self.chunks; Z, Y, X = self.shape; out = np.zeros((z1 - z0, y1 - y0, x1 - x0), np.uint8)
        a0, b0, c0 = max(z0, 0), max(y0, 0), max(x0, 0); a1, b1, c1 = min(z1, Z), min(y1, Y), min(x1, X)
        if a1 <= a0 or b1 <= b0 or c1 <= c0: return out
        keys = [(i, j, k) for i in range(a0 // cz, (a1 - 1) // cz + 1) for j in range(b0 // cy, (b1 - 1) // cy + 1) for k in range(c0 // cx, (c1 - 1) // cx + 1)]
        miss = [q for q in keys if q not in self.cache]; got = dict(self.ex.map(self.chunk, miss))
        if self.cache_max:
            self.cache.update(got)
            while len(self.cache) > self.cache_max: self.cache.pop(next(iter(self.cache)))
        for (i, j, k) in keys:
            a = got[(i, j, k)] if (i, j, k) in got else self.cache.get((i, j, k))
            if a is None: continue
            zs, ze = max(a0, i * cz), min(a1, (i + 1) * cz); ys, ye = max(b0, j * cy), min(b1, (j + 1) * cy); xs, xe = max(c0, k * cx), min(c1, (k + 1) * cx)
            out[zs - z0:ze - z0, ys - y0:ye - y0, xs - x0:xe - x0] = a[zs - i * cz:ze - i * cz, ys - j * cy:ye - j * cy, xs - k * cx:xe - k * cx]
        return out


class Sampler:
    """Trilinear sampling of one level at (n, 3) z, y, x points given in THAT level's voxel units. Values are float32 (0..255)."""
    def __init__(self, name='ct', level=0, max_gb=6.0):
        self.v = Vol(name, level); self.cache = {}; self.order = []; self.max = int(max_gb * 1e9); self.bytes = 0; self.fetched = 0

    def _need(self, keys):
        miss = [k for k in keys if k not in self.cache]
        for (ijk, a) in self.v.ex.map(self.v.chunk, miss):
            self.cache[ijk] = a; self.order.append(ijk); self.fetched += 1
            if a is not None: self.bytes += a.nbytes
        while self.bytes > self.max and len(self.order) > len(keys):
            old = self.order.pop(0)
            if old in keys: self.order.append(old); continue
            a = self.cache.pop(old, None)
            if a is not None: self.bytes -= a.nbytes

    def sample(self, pts):
        pts = np.asarray(pts, np.float64); out = np.zeros(len(pts), np.float32)
        if len(pts) == 0: return out
        c = np.array(self.v.chunks); S = np.array(self.v.shape)
        f = np.floor(pts).astype(np.int64); fr = (pts - f).astype(np.float32)
        ck = f // c; ids = ck[:, 0] * 1_000_000_000 + ck[:, 1] * 100_000 + ck[:, 2]
        for u in np.unique(ids):
            sel = np.nonzero(ids == u)[0]; i, j, k = ck[sel[0]]
            # the 2x2x2 stencil can cross into the next chunk: assemble a (c+1)^3 brick
            need = [(i + a, j + b, k + d) for a in (0, 1) for b in (0, 1) for d in (0, 1)]; self._need(need)
            brick = np.zeros(tuple(c + 1), np.float32)
            for (a, b, d) in [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)]:
                ch = self.cache.get((i + a, j + b, k + d))
                if ch is None: continue
                sz, sy, sx = (slice(0, c[0]) if a == 0 else slice(c[0], c[0] + 1)), (slice(0, c[1]) if b == 0 else slice(c[1], c[1] + 1)), (slice(0, c[2]) if d == 0 else slice(c[2], c[2] + 1))
                brick[sz, sy, sx] = ch[:sz.stop - sz.start, :sy.stop - sy.start, :sx.stop - sx.start]
            l = f[sel] - np.array([i, j, k]) * c; w = fr[sel]
            ok = ((f[sel] >= 0) & (f[sel] + 1 < S)).all(1)
            l = np.clip(l, 0, c - 1); z, y, x = l[:, 0], l[:, 1], l[:, 2]; wz, wy, wx = w[:, 0], w[:, 1], w[:, 2]
            v = (brick[z, y, x] * (1 - wz) * (1 - wy) * (1 - wx) + brick[z + 1, y, x] * wz * (1 - wy) * (1 - wx) + brick[z, y + 1, x] * (1 - wz) * wy * (1 - wx) +
                 brick[z, y, x + 1] * (1 - wz) * (1 - wy) * wx + brick[z + 1, y + 1, x] * wz * wy * (1 - wx) + brick[z + 1, y, x + 1] * wz * (1 - wy) * wx +
                 brick[z, y + 1, x + 1] * (1 - wz) * wy * wx + brick[z + 1, y + 1, x + 1] * wz * wy * wx)
            out[sel] = np.where(ok, v, 0)
        return out
