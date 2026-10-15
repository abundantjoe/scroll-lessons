# Provenance: Project HERCULES | owner the owner | [id removed]
"""Raw (unorganized) segments of a volume: frame check against the eligible
volume at level 4 (chunks in memory only), packaged rule decision, and the
longest row span in turns (F5 needs > 1 turn). Numbers only.
Usage: python raw_segments.py SCROLL VOLUME_PREFIX OUT_JSON"""
import json
import sys
from pathlib import Path

import boto3
import numpy as np
from botocore import UNSIGNED
from botocore.config import Config

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_rule as AR  # noqa: E402  (loads the packaged module as hercules.geometry.handed_rule)
import analyze_meshes as A  # noqa: E402
from hercules.geometry.tifxyz import read_tifxyz, valid_mask  # noqa: E402

HR = AR.HR
scroll, pre, out = sys.argv[1:4]
assert scroll != "PHerc0841"
B = "vesuvius-challenge-open-data"
s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=16))
za = json.loads(s3.get_object(Bucket=B, Key=f"{pre}/4/.zarray")["Body"].read())
Z4, Y4, X4 = za["shape"]
c = za["chunks"][0]
za0 = json.loads(s3.get_object(Bucket=B, Key=f"{pre}/0/.zarray")["Body"].read())
cache = {}


def sampler(P):
    i = np.floor(P / 16).astype(int)
    v = np.zeros(len(P))
    keys = np.stack([i[:, 2] // c, i[:, 1] // c, i[:, 0] // c], 1)
    for k in {tuple(x) for x in keys.tolist()}:
        if k not in cache:
            try:
                b = s3.get_object(Bucket=B, Key=f"{pre}/4/" + "/".join(map(str, k)))["Body"].read()
                cache[k] = np.frombuffer(b, np.uint8).reshape(c, c, c)
            except s3.exceptions.NoSuchKey:
                cache[k] = None
        sel = np.all(keys == k, 1)
        if cache[k] is not None:
            q = i[sel]
            v[sel] = cache[k][q[:, 2] % c, q[:, 1] % c, q[:, 0] % c]
    return v


vol = pre.split("/")[-1].split("-")[0]
props = A.vol_props(scroll, vol)
cj = json.loads((A.CEN / f"{scroll}.json").read_text())
cc, ci = A.centroid_curve(scroll)
vi = HR.VolumeInfo.from_metadata(cj["zattrs"], props, centroid=cc, umbilicus=A.umbilicus_curve(scroll, vol)[0])
res = []
for d in sorted((A.S3 / scroll / "segments" / "raw").iterdir()):
    p = read_tifxyz(d).points.astype(np.float64)
    fc = HR.frame_check_from_volume(p, sampler, tuple(za0["shape"]), stride=4)
    dec = HR.orient_for_reading(p, vi, frame=fc)
    ws = HR.winding_sense(p, cc)
    wt = HR.winding_sense(np.ascontiguousarray(np.swapaxes(p, 0, 1)), cc)
    res.append(dict(segment=d.name, n_valid=int(valid_mask(p).sum()), frame=vars(fc), state=dec.state,
                    confidence=dec.confidence, mirror_u=dec.mirror_u, flip_v=dec.flip_v, flags=dec.flags,
                    max_span_turns=max(ws["max_row_span_turns"], wt["max_row_span_turns"]),
                    w=ws["w"] or wt["w"]))
    r = res[-1]
    print(d.name, "zero %.3f out %.3f" % (fc.frac_zero_ct, fc.frac_outside), r["state"], r["confidence"], r["mirror_u"],
          r["flip_v"], "span %.2f turns" % r["max_span_turns"], "w", r["w"], flush=True)
Path(out).write_text(json.dumps(res, indent=1, default=float))
