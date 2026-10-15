# Provenance: Project HERCULES | owner the owner | [id removed]
"""FL pass 2, PHerc0800: list the organizer tifxyz segments (anonymous S3), compute each
mesh area from its x/y/z grids (sum of quad areas over fully valid quads, voxel size from
the volume's metadata.json), rank by area and apply the brief's filter (area >= 16 cm^2).
Numbers only; writes logs/sib/fl2-pherc0800/segments.json."""
import hashlib, io, json, sys
import boto3, numpy as np, tifffile
from botocore import UNSIGNED
from botocore.config import Config

B = "vesuvius-challenge-open-data"
SCROLL = "PHerc0800"
VOL = "PHerc0800/volumes/20250521135224-8.640um-1.2m-116keV-masked.zarr/metadata.json"
s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
mb = s3.get_object(Bucket=B, Key=VOL)["Body"].read()
vox_mm = json.loads(mb)["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]
segs = []
for p in s3.list_objects_v2(Bucket=B, Prefix=f"{SCROLL}/segments/", Delimiter="/")["CommonPrefixes"]:
    pre = p["Prefix"]
    keys = {o["Key"] for o in s3.list_objects_v2(Bucket=B, Prefix=pre + "mesh/")["Contents"]}
    for xk in sorted(k for k in keys if k.endswith(".tifxyz/x.tif")):  # the organizer mesh, not mesh/intermediate/
        base = xk[:-5]
        arrs, sha = [], {}
        for c in "xyz":
            b = s3.get_object(Bucket=B, Key=base + c + ".tif")["Body"].read()
            sha[c] = hashlib.sha256(b).hexdigest()
            arrs.append(tifffile.imread(io.BytesIO(b)))
        P = np.stack(arrs, -1).astype(float)
        v = (P[..., 0] != -1) & np.isfinite(P).all(-1)
        a, b_, c_, d = P[:-1, :-1], P[1:, :-1], P[:-1, 1:], P[1:, 1:]
        q = v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]
        A = 0.5 * np.linalg.norm(np.cross(b_ - a, c_ - a), axis=-1) + 0.5 * np.linalg.norm(np.cross(b_ - d, c_ - d), axis=-1)
        segs.append(dict(segment=pre.split("/")[-2], tifxyz=f"s3://{B}/{base}", grid=list(P.shape[:2]),
                         valid_vertices=int(v.sum()), area_cm2=round(float(A[q].sum()) * (vox_mm / 10) ** 2, 4), sha256=sha))
segs.sort(key=lambda s: -s["area_cm2"])
for i, s in enumerate(segs):
    s["rank"] = i + 1
rng = [s for s in segs if 4 <= s["rank"] <= 9]
out = dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
           scroll=SCROLL, pass_=2, voxel_mm_from_metadata=vox_mm, metadata_json_sha256=hashlib.sha256(mb).hexdigest(),
           organizer_segments=segs, rank_range="4-9", in_range=[s["segment"] for s in rng],
           kept=[s["segment"] for s in rng if s["area_cm2"] >= 16.0], min_area_cm2=16.0,
           auto_grow_applies=len(segs) == 0)
json.dump(out, open("logs/sib/fl2-pherc0800/segments.json", "w"), indent=1)
print(json.dumps({k: out[k] for k in ("voxel_mm_from_metadata", "in_range", "kept", "auto_grow_applies")}),
      [(s["rank"], s["area_cm2"]) for s in segs])
sys.exit(0)
