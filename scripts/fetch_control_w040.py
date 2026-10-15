#!/usr/bin/env python
"""fetch_control_w040.py -- download the w040 known-text control (PHerc0139) from the public bucket and checksum it.

Fetches level 0 of the native 9.362 um surface volume (28 x 6400 x 7980, uncompressed) plus its group metadata, and
the tifxyz mesh, from s3://vesuvius-challenge-open-data (anonymous; no credentials needed). Idempotent: files already
present with the right size are skipped. Then writes <out>/MANIFEST.sha256 (sha256 of every file, sorted by path) and
prints one digest over that manifest, so a single line says whether two copies of the input are identical.

The labels and the checkpoint come from Hugging Face; see docs/REPRODUCE.md for the two `hf` commands.
usage: fetch_control_w040.py <out_dir> [--manifest-only] [--threads 16]
"""
import argparse, concurrent.futures as cf, hashlib, os, sys

BUCKET = "vesuvius-challenge-open-data"
SEGMENT = "PHerc0139/segments/20250831000000-w040_2025083102/"
PARTS = ("surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr/",
         "mesh/20250831000000-on-20250728140407-9.362um.tifxyz/")


def s3_client(threads):
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    return boto3.client("s3", region_name="us-east-1", config=Config(signature_version=UNSIGNED,
                        max_pool_connections=max(threads, 10), retries={"max_attempts": 10}))


def list_keys(s3):
    keys = []
    for part in PARTS:
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=SEGMENT + part):
            for o in page.get("Contents", []):
                rel = o["Key"][len(SEGMENT + part):]
                if part.startswith("surface") and "/" in rel and not rel.startswith("0/"):
                    continue                      # level 0 only (the model reads level 0), plus group metadata
                keys.append((o["Key"], o["Size"]))
    return keys


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def write_manifest(out):
    files = sorted(os.path.relpath(os.path.join(d, f), out) for d, _, fs in os.walk(out) for f in fs
                   if f != "MANIFEST.sha256" and not f.endswith(".part"))
    with cf.ThreadPoolExecutor(8) as ex:
        sums = list(ex.map(lambda r: sha256_file(os.path.join(out, r)), files))
    text = "".join("%s  %s\n" % (s, r) for s, r in zip(sums, files))
    open(os.path.join(out, "MANIFEST.sha256"), "w").write(text)
    return len(files), hashlib.sha256(text.encode()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out"); ap.add_argument("--manifest-only", action="store_true"); ap.add_argument("--threads", type=int, default=16)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    if not a.manifest_only:
        s3 = s3_client(a.threads)
        keys = list_keys(s3)
        print("%d objects, %.1f MB" % (len(keys), sum(s for _, s in keys) / 1e6), flush=True)

        def get(k):
            key, size = k
            dst = os.path.join(a.out, key[len(SEGMENT):])
            if os.path.exists(dst) and os.path.getsize(dst) == size:
                return 0
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            s3.download_file(BUCKET, key, dst + ".part"); os.replace(dst + ".part", dst)
            return size
        with cf.ThreadPoolExecutor(a.threads) as ex:
            got = sum(ex.map(get, keys))
        print("downloaded %.1f MB" % (got / 1e6), flush=True)
    n, digest = write_manifest(a.out)
    print("MANIFEST.sha256: %d files; manifest digest %s" % (n, digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
