# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-N: copy the PHercParis4 m7 L2 surface-prediction chunks around window A (strip-a c9-c15, top of the
official 20260701183124-w010-027 mesh) into a LOCAL zarr with a shifted origin. Compressed chunk bytes are
copied unchanged (same 192^3 chunking and codec); every key is recorded with sha256. Prediction data only;
no CT and no image is read or rendered.
Local (z,y,x) = global L2 (z,y,x) - ORIGIN. Global L2 = native 2.4 um / 4."""
import hashlib, json, sys, os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import boto3
from botocore import UNSIGNED
from botocore.config import Config

B = "vesuvius-challenge-open-data"
SRC = ("PHercParis4/representations/predictions/surfaces/"
       "20260411134726-surface-20260413222639-surface-m7-L2-th0.2.zarr")
C = 192
CZ, CY, CX = (81, 99), (25, 32), (19, 26)          # chunk index ranges [a, b)
ORIGIN = (CZ[0] * C, CY[0] * C, CX[0] * C)          # (15552, 4800, 3648) global L2 zyx
OUT = Path("/work/p4n/m7l2_local.zarr")
MAN = Path("/home/user/dominion/logs/sib/tracer/p4n/m7l2_chunks_sha256.jsonl")

s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=32), region_name="us-east-1")


def main():
    za = json.loads(s3.get_object(Bucket=B, Key=f"{SRC}/0/.zarray")["Body"].read())
    sep = za.get("dimension_separator", ".")
    shape_g = za["shape"]
    shape = [min(shape_g[0], CZ[1] * C) - ORIGIN[0], min(shape_g[1], CY[1] * C) - ORIGIN[1],
             min(shape_g[2], CX[1] * C) - ORIGIN[2]]
    (OUT / "0").mkdir(parents=True, exist_ok=True)
    loc = dict(za); loc["shape"] = shape; loc["dimension_separator"] = "."
    (OUT / "0/.zarray").write_text(json.dumps(loc, indent=1))
    (OUT / ".zgroup").write_text(json.dumps({"zarr_format": 2}))
    (OUT / ".zattrs").write_text(json.dumps({"multiscales": [{"version": "0.4", "name": "/",
        "axes": [{"name": a, "type": "space"} for a in "zyx"],
        "datasets": [{"path": "0", "coordinateTransformations": [{"type": "scale", "scale": [1.0, 1.0, 1.0]}]}]}],
        "hrc_origin_global_L2_zyx": ORIGIN, "hrc_source": f"s3://{B}/{SRC}/0", "hrc_L2_per_native": 0.25}, indent=1))
    (OUT / "meta.json").write_text(json.dumps({"type": "vol", "uuid": "p4n_m7l2_local", "name": "p4n_m7l2_local",
        "format": "zarr", "width": shape[2], "height": shape[1], "slices": shape[0], "voxelsize": 9.6,
        "min": 0.0, "max": 255.0}, indent=1))
    jobs = [(z, y, x) for z in range(*CZ) for y in range(*CY) for x in range(*CX)]

    def get(j):
        z, y, x = j
        key = f"{SRC}/0/{z}{sep}{y}{sep}{x}"
        try:
            b = s3.get_object(Bucket=B, Key=key)["Body"].read()
        except s3.exceptions.NoSuchKey:
            return {"key": key, "missing": True}
        (OUT / "0" / f"{z-CZ[0]}.{y-CY[0]}.{x-CX[0]}").write_bytes(b)
        return {"key": f"s3://{B}/{key}", "size": len(b), "sha256": hashlib.sha256(b).hexdigest()}

    MAN.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(16) as ex, open(MAN, "w") as mf:
        for r in ex.map(get, jobs):
            mf.write(json.dumps(r) + "\n")
    print("done", len(jobs), "origin", ORIGIN, "shape", shape)


if __name__ == "__main__":
    main()
