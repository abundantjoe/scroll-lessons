# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fetch the official 9.362 um tifxyz meshes (geometry only) of every organizer
segment of one scroll from s3://vesuvius-challenge-open-data (anonymous), plus
the volume metadata.json (voxel size) and the bucket index entries (label
sources). No ink map, label image or surface volume is downloaded.

Writes <out>/<segment>/{x,y,z}.tif + meta.json and a manifest with the sha256
of every downloaded object.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path

import boto3
from botocore import UNSIGNED
from botocore.config import Config

BUCKET = "vesuvius-challenge-open-data"


def client():
    return boto3.client("s3", config=Config(signature_version=UNSIGNED, retries={"max_attempts": 8}),
                        region_name="us-east-1")


def get(s3, key: str) -> bytes:
    for i in range(5):
        try:
            return s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
        except Exception:  # network retry with backoff
            if i == 4:
                raise
            time.sleep(2 ** (i + 1))
    raise RuntimeError("unreachable")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def list_prefixes(s3, prefix: str) -> list[str]:
    out = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefix, Delimiter="/"):
        out += [p["Prefix"] for p in page.get("CommonPrefixes", [])]
    return out


def list_keys(s3, prefix: str) -> list[tuple[str, int]]:
    out = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefix):
        out += [(o["Key"], o["Size"]) for o in page.get("Contents", [])]
    return out


def label_sources(ent: dict) -> dict:
    """Human ink-label sets and model ink maps of one bucket-index segment entry
    (from the object paths only; nothing is downloaded)."""
    human, model = [], []
    for d in ent.get("data", []):
        for o in d.get("origins", []):
            path = o.get("path", "")
            if d.get("type") == "ink-labels":
                parts = path.rstrip("/").split("/")
                human.append({"label_set": parts[-1], "target": parts[-2],
                              "source_path": o.get("copy_info", {}).get("source_path")})
            elif d.get("type") == "ink-detection":
                stem = path.rsplit("/", 1)[-1]
                toks = stem.split("-")
                ids = [t for t in toks if len(t) == 14 and t.isdigit()]
                mid = ids[-1] if len(ids) >= 3 else None  # segment, volume, model
                model.append({"file": stem, "model_id": mid})
    return {"human_ink_labels": human, "model_ink_maps": model}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scroll", default="PHerc0139")
    ap.add_argument("--volume", default="20250728140407", help="canvas volume id (9.362 um for 0139)")
    ap.add_argument("--out", default="/work/sib_contam/meshes")
    ap.add_argument("--manifest", required=True)
    a = ap.parse_args(argv)
    s3 = client()
    out = Path(a.out) / a.scroll
    out.mkdir(parents=True, exist_ok=True)
    man: dict = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
                 "bucket": BUCKET, "scroll": a.scroll, "canvas_volume": a.volume,
                 "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "objects": {}, "segments": {}}

    vols = [p for p in list_prefixes(s3, f"{a.scroll}/volumes/") if p.split("/")[-2].startswith(a.volume)]
    if len(vols) != 1:
        print("volume prefix not unique:", vols, file=sys.stderr)
        return 2
    vkey = vols[0] + "metadata.json"
    vb = get(s3, vkey)
    man["objects"][vkey] = sha(vb)
    (out / "volume_metadata.json").write_bytes(vb)
    man["volume_metadata"] = json.loads(vb)

    idx = get(s3, "metadata.json")
    man["objects"]["metadata.json"] = sha(idx)
    try:
        idx_json = json.loads(gzip.decompress(idx))
        man["index_sha256_decompressed"] = sha(gzip.decompress(idx))
    except OSError:
        idx_json = json.loads(idx)
    (out / "bucket_index_sha256.txt").write_text(man["objects"]["metadata.json"] + "\n")
    idx_entries = {}
    for sid, ent in idx_json.get("samples", {}).get(a.scroll, {}).get("segments", {}).items():
        if isinstance(ent, dict) and "long_id" in ent:
            idx_entries[ent["long_id"]] = ent

    for seg_prefix in list_prefixes(s3, f"{a.scroll}/segments/"):
        seg = seg_prefix.split("/")[-2]
        keys = [k for k, _ in list_keys(s3, seg_prefix + "mesh/")
                if f"-on-{a.volume}-" in k and ".tifxyz/" in k and "/intermediate/" not in k]
        rec: dict = {"files": {}}
        ent = idx_entries.get(seg)
        if ent is not None:
            rec["label_sources"] = label_sources(ent)
            rec["index_creation"] = ent.get("creation", {}).get("metadata", {}).get("uuid")
        if not keys:
            rec["status"] = f"no tifxyz on {a.volume}"
            man["segments"][seg] = rec
            continue
        d = out / seg
        d.mkdir(exist_ok=True)
        for k in keys:
            b = get(s3, k)
            name = k.rsplit("/", 1)[1]
            (d / name).write_bytes(b)
            rec["files"][name] = {"key": k, "sha256": sha(b), "bytes": len(b)}
            man["objects"][k] = sha(b)
        rec["status"] = "ok"
        man["segments"][seg] = rec
        print(seg, rec["status"], flush=True)
    Path(a.manifest).write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")
    print("segments", len(man["segments"]), "ok", sum(r["status"] == "ok" for r in man["segments"].values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
