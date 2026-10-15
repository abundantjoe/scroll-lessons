# Provenance: Project HERCULES | owner the owner | [id removed]
"""Anonymous streaming reader for the two official PHerc0841 OME-zarr volumes (zarr v2,
uint8, 128^3 chunks, no compressor, '/' separator). Missing chunks (masked air) are 0.
Every chunk fetched is sha256-hashed; hashes are appended to CHUNK_LOG (gzip jsonl)."""
import concurrent.futures as cf, gzip, hashlib, json, os, threading, time
import numpy as np, requests

BASE = "https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0841/volumes/"
VOL = {"v9": "20250821151531-9.366um-1.2m-113keV-masked.zarr",
       "v2": "20260319124803-2.403um-0.2m-77keV-masked.zarr"}
# voxel sizes (um) from each volume's metadata.json scan.tomo.acquisition.detector.samplePixelSize
VOXEL_UM = {"v9": 9.366, "v2": 2.403}
SHAPES = {}
CHUNK_LOG = os.environ.get("REG_CHUNK_LOG", "/work/reg/chunk_sha256.jsonl.gz")
_lock = threading.Lock()
_tls = threading.local()


def _sess():
    if not hasattr(_tls, "s"):
        _tls.s = requests.Session()
    return _tls.s


def meta(vol, level):
    k = (vol, level)
    if k not in SHAPES:
        r = _sess().get(f"{BASE}{VOL[vol]}/{level}/.zarray", timeout=60); r.raise_for_status()
        a = r.json(); assert a["compressor"] is None and a["dtype"] == "|u1" and a["order"] == "C"
        SHAPES[k] = (tuple(a["shape"]), tuple(a["chunks"]))
    return SHAPES[k]


def _get(url, n):
    for i in range(6):
        try:
            r = _sess().get(url, timeout=120)
            if r.status_code == 404:
                return None, "404"
            r.raise_for_status()
            b = r.content
            if len(b) != n:
                raise IOError(f"size {len(b)} != {n}")
            return b, hashlib.sha256(b).hexdigest()
        except Exception as e:  # network retry with backoff
            if i == 5:
                raise
            time.sleep(2 ** i)


def read(vol, level, z0, z1, y0, y1, x0, x1, threads=24, tag=""):
    """Return uint8 array [z0:z1, y0:y1, x0:x1] (clipped to the volume; outside = 0)."""
    shape, ch = meta(vol, level)
    out = np.zeros((z1 - z0, y1 - y0, x1 - x0), np.uint8)
    lo = [max(0, v) for v in (z0, y0, x0)]; hi = [min(s, v) for s, v in zip(shape, (z1, y1, x1))]
    if any(h <= l for l, h in zip(lo, hi)):
        return out, {"n_chunks": 0}
    idx = [range(l // c, (h - 1) // c + 1) for l, h, c in zip(lo, hi, ch)]
    jobs = [(a, b, c) for a in idx[0] for b in idx[1] for c in idx[2]]

    def work(j):
        cz, cy, cx = j
        full = [min(ch[d], shape[d] - j[d] * ch[d]) for d in range(3)]
        # zarr v2 stores edge chunks at full chunk size
        b, h = _get(f"{BASE}{VOL[vol]}/{level}/{cz}/{cy}/{cx}", ch[0] * ch[1] * ch[2])
        if b is not None:
            arr = np.frombuffer(b, np.uint8).reshape(ch)
            s = [slice(max(lo[d], j[d] * ch[d]), min(hi[d], j[d] * ch[d] + full[d])) for d in range(3)]
            src = tuple(slice(ss.start - j[d] * ch[d], ss.stop - j[d] * ch[d]) for d, ss in enumerate(s))
            dst = tuple(slice(ss.start - o, ss.stop - o) for ss, o in zip(s, (z0, y0, x0)))
            out[dst] = arr[src]
        return f"{vol}/{level}/{cz}/{cy}/{cx}", h

    with cf.ThreadPoolExecutor(threads) as ex:
        hs = list(ex.map(work, jobs))
    hs.sort()
    with _lock, gzip.open(CHUNK_LOG, "at") as f:
        for k, h in hs:
            f.write(json.dumps({"k": k, "sha256": h, "tag": tag}) + "\n")
    dig = hashlib.sha256("".join(k + h for k, h in hs).encode()).hexdigest()
    return out, {"n_chunks": len(hs), "n_missing": sum(h == "404" for _, h in hs), "chunkset_sha256": dig,
                 "array_sha256": hashlib.sha256(out.tobytes()).hexdigest()}
