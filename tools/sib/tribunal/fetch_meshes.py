# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fetch official 9 um segment meshes (tifxyz: x/y/z.tif + meta.json only; geometry, no
images) from s3://vesuvius-challenge-open-data anonymously; record sha256 of every file.

    python tools/sib/tribunal/fetch_meshes.py OUT_DIR OUT_JSON SCROLL:VOLUME_ID [...] [--only tag1,tag2]
"""
import hashlib
import json
import sys
from pathlib import Path

import boto3
from botocore import UNSIGNED
from botocore.config import Config

B = "vesuvius-challenge-open-data"
s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, retries={"max_attempts": 8}))


def prefixes(p):
    r = s3.list_objects_v2(Bucket=B, Prefix=p, Delimiter="/")
    return [c["Prefix"] for c in r.get("CommonPrefixes", [])]


def main():
    args = sys.argv[1:]
    only = None
    if "--only" in args:  # --only w040,w044 : fetch only segments whose id contains -<tag>_
        i = args.index("--only")
        only = args[i + 1].split(",")
        args = args[:i] + args[i + 2:]
    out, out_json, specs = Path(args[0]), Path(args[1]), args[2:]
    rec = {"bucket": B, "files": {}, "segments": {}}
    for spec in specs:
        scroll, vol = spec.split(":")
        for seg in prefixes(f"{scroll}/segments/"):
            sid = seg.rstrip("/").split("/")[-1]
            if only and not any(f"-{t}_" in sid for t in only):
                continue
            ts = sid.split("-")[0]
            mp = f"{seg}mesh/{ts}-on-{vol}.tifxyz/"
            got = []
            for name in ("x.tif", "y.tif", "z.tif", "meta.json"):
                key = mp + name
                dst = out / key
                dst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    s3.download_file(B, key, str(dst))
                except Exception as e:  # noqa: BLE001 - recorded, not fatal
                    rec["segments"].setdefault(f"{scroll}/{sid}", {})["error"] = f"{name}: {type(e).__name__}"
                    break
                rec["files"][key] = hashlib.sha256(dst.read_bytes()).hexdigest()
                got.append(name)
            if len(got) == 4:
                rec["segments"][f"{scroll}/{sid}"] = {"mesh": str(out / mp), "volume": vol}
    out_json.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(len(rec["files"]), "files;", sum("mesh" in v for v in rec["segments"].values()), "meshes")


if __name__ == "__main__":
    main()
