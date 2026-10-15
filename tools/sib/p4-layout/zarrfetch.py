"""Anonymous chunk reader for the official Paris 4 2.4 um volume (zarr v2, 128^3 u8, uncompressed).

Provenance: Project HERCULES | owner the owner | [id removed]
Numbers only. Streams chunks over HTTPS; an optional bounded on-disk cache; absent chunks (404) = fill 0.
Every fetched chunk's key, status and sha256 is appended to a manifest (jsonl).
"""
import hashlib, json, os, threading, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
import numpy as np

BASE = "https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr"
SHAPES = {0: (75784, 32693, 32693), 1: (37892, 16347, 16347), 2: (18946, 8174, 8174),
          3: (9473, 4087, 4087), 4: (4737, 2044, 2044), 5: (2369, 1022, 1022)}
C = 128


class Vol:
    def __init__(self, level, manifest_path, cache_dir=None, mem_chunks=6000, threads=32):
        self.L, self.shape = level, SHAPES[level]
        self.mem, self.lock = {}, threading.Lock()
        self.mem_chunks, self.threads = mem_chunks, threads
        self.cache_dir = cache_dir
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
        self.man = open(manifest_path, "a")
        self.n_get = self.n_404 = self.bytes = 0

    def _get(self, key):
        url = f"{BASE}/{self.L}/{key[0]}/{key[1]}/{key[2]}"
        cp = os.path.join(self.cache_dir, f"{self.L}_{key[0]}_{key[1]}_{key[2]}") if self.cache_dir else None
        if cp and os.path.exists(cp):
            b = open(cp, "rb").read()
            return np.frombuffer(b, np.uint8).reshape(C, C, C) if b else None
        for i in range(5):
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    b = r.read()
                st = 200
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    b, st = b"", 404
                    break
                time.sleep(2 ** i)
            except Exception:
                time.sleep(2 ** i)
        else:
            raise RuntimeError("fetch failed " + url)
        if st == 200:
            assert len(b) == C ** 3, (url, len(b))
        with self.lock:
            self.n_get += 1
            self.n_404 += st == 404
            self.bytes += len(b)
            self.man.write(json.dumps({"L": self.L, "k": [int(x) for x in key], "status": st,
                                       "sha256": hashlib.sha256(b).hexdigest() if b else None}) + "\n")
        if cp:
            with open(cp + ".tmp", "wb") as f:
                f.write(b)
            os.replace(cp + ".tmp", cp)
        return np.frombuffer(b, np.uint8).reshape(C, C, C) if b else None

    def prefetch(self, keys):
        keys = [k for k in set(tuple(int(x) for x in k) for k in keys) if k not in self.mem and self._inb(k)]
        with ThreadPoolExecutor(self.threads) as ex:
            for k, a in zip(keys, ex.map(self._get, keys)):
                self.mem[k] = a
        if len(self.mem) > self.mem_chunks:  # drop oldest inserted
            for k in list(self.mem)[: len(self.mem) - self.mem_chunks]:
                del self.mem[k]
        self.man.flush()

    def _inb(self, k):
        return all(0 <= k[i] < -(-self.shape[i] // C) for i in range(3))

    def sample(self, zyx):
        """Nearest-voxel values at float level-L coords (N,3) zyx. Out of volume or absent chunk -> 0.
        Missing chunks are fetched on demand (batched)."""
        zyx = np.rint(np.asarray(zyx)).astype(np.int64)
        out = np.zeros(len(zyx), np.float32)
        inb = np.all((zyx >= 0) & (zyx < np.array(self.shape)), 1)
        idx = np.nonzero(inb)[0]
        if len(idx) == 0:
            return out
        p = zyx[idx]
        ck = p // C
        code = (ck[:, 0] * 4096 + ck[:, 1]) * 4096 + ck[:, 2]
        u, inv = np.unique(code, return_inverse=True)
        keys = [(int(c // (4096 * 4096)), int((c // 4096) % 4096), int(c % 4096)) for c in u]
        need = [k for k in keys if k not in self.mem]
        if need:
            self.prefetch(need)
        order = np.argsort(inv, kind="stable")
        bounds = np.searchsorted(inv[order], np.arange(len(u) + 1))
        loc = p - ck * C
        for n, k in enumerate(keys):
            a = self.mem.get(k)
            if a is None:
                continue
            sel = order[bounds[n]:bounds[n + 1]]
            l = loc[sel]
            out[idx[sel]] = a[l[:, 0], l[:, 1], l[:, 2]]
        return out

    def chunks_for(self, zyx, pad=0):
        zyx = np.asarray(zyx)
        lo = np.floor((zyx - pad) / C).astype(int)
        hi = np.floor((zyx + pad) / C).astype(int)
        ks = set()
        for a, b in zip(lo, hi):
            for z in range(a[0], b[0] + 1):
                for y in range(a[1], b[1] + 1):
                    for x in range(a[2], b[2] + 1):
                        ks.add((z, y, x))
        return ks
