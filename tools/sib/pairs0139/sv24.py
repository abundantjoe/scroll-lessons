# Provenance: Project HERCULES | owner the owner | [id removed]
"""Range reader for the organizer 2.399 um surface volumes of PHerc0139 segments (zarr v2, chunks (109,128,128),
uncompressed, C order, '/' separator): only the requested slice range of each chunk is fetched (HTTP Range).
Missing chunks read as 0 (the zarr fill value = invalid)."""
import json, threading
import numpy as np
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from concurrent.futures import ThreadPoolExecutor

B = "vesuvius-challenge-open-data"
_local = threading.local()


def _s3():
    if not hasattr(_local, "c"):
        _local.c = boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=64,
                                                    retries=dict(max_attempts=10, mode="adaptive")))
    return _local.c


class SV24:
    def __init__(self, seg, level=0, workers=24):
        self.prefix = f"PHerc0139/segments/{seg}/surface-volumes/2.399um-0.22m-78keV-volume-20260102150214.zarr/{level}"
        za = json.loads(_s3().get_object(Bucket=B, Key=self.prefix + "/.zarray")["Body"].read())
        assert za["compressor"] is None and za["order"] == "C" and za["dtype"] == "|u1" and za["filters"] is None
        self.shape = tuple(za["shape"]); self.chunks = tuple(za["chunks"])
        assert self.chunks[0] == self.shape[0]
        self.ex = ThreadPoolExecutor(workers)
        self.bytes = 0; self.requests = 0

    def _chunk(self, cy, cx, z0, z1):
        ch = self.chunks
        off = z0 * ch[1] * ch[2]; n = (z1 - z0) * ch[1] * ch[2]
        for a in range(6):
            try:
                r = _s3().get_object(Bucket=B, Key=f"{self.prefix}/0/{cy}/{cx}", Range=f"bytes={off}-{off + n - 1}")
                b = r["Body"].read()
                break
            except _s3().exceptions.NoSuchKey:
                return None
            except Exception:
                if a == 5:
                    raise
        self.bytes += len(b); self.requests += 1
        assert len(b) == n, (len(b), n)
        return np.frombuffer(b, np.uint8).reshape(z1 - z0, ch[1], ch[2])

    def read(self, z0, z1, y0, y1, x0, x1):
        """uint8 (z1-z0, y1-y0, x1-x0); outside the array or missing chunks -> 0."""
        ch = self.chunks
        out = np.zeros((z1 - z0, y1 - y0, x1 - x0), np.uint8)
        H, W = self.shape[1:]
        ya, yb, xa, xb = max(y0, 0), min(y1, H), max(x0, 0), min(x1, W)
        if ya >= yb or xa >= xb:
            return out
        jobs = [(cy, cx) for cy in range(ya // ch[1], (yb - 1) // ch[1] + 1)
                for cx in range(xa // ch[2], (xb - 1) // ch[2] + 1)]
        res = self.ex.map(lambda j: self._chunk(j[0], j[1], z0, z1), jobs)
        for (cy, cx), a in zip(jobs, res):
            if a is None:
                continue
            gy0, gx0 = cy * ch[1], cx * ch[2]
            sy0, sy1 = max(ya, gy0), min(yb, gy0 + ch[1]); sx0, sx1 = max(xa, gx0), min(xb, gx0 + ch[2])
            out[:, sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = a[:, sy0 - gy0:sy1 - gy0, sx0 - gx0:sx1 - gx0]
        return out
