# Provenance: Project HERCULES | owner the owner | [id removed]
"""Anonymous fetch from s3://vesuvius-challenge-open-data into /work/p139/s3/<key>; every file's sha256 is appended
to /work/p139/fetch_manifest.jsonl (copied to logs/sib/pairs0139/). Usage:
  fetch.py catalogue            -> /work/p139/catalogue.json (per-segment keys + sizes for PHerc0139)
  fetch.py meshes [9|2|both]    -> the 9.362 um and/or 2.399 um organizer tifxyz of every segment
  fetch.py keys KEY...          -> the given keys"""
import os, sys, json, hashlib, datetime
from concurrent.futures import ThreadPoolExecutor
import boto3
from botocore import UNSIGNED
from botocore.config import Config

B = "vesuvius-challenge-open-data"
ROOT = "/work/p139/s3"
MAN = "/work/p139/fetch_manifest.jsonl"
s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=32,
                                      retries=dict(max_attempts=8, mode="adaptive")))


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def listing(prefix, delim=None):
    kw = dict(Bucket=B, Prefix=prefix)
    if delim:
        kw["Delimiter"] = delim
    objs, pre = [], []
    while True:
        r = s3.list_objects_v2(**kw)
        objs += [(o["Key"], o["Size"]) for o in r.get("Contents", [])]
        pre += [c["Prefix"] for c in r.get("CommonPrefixes", [])]
        if not r.get("IsTruncated"):
            return objs, pre
        kw["ContinuationToken"] = r["NextContinuationToken"]


def get(key, size=None):
    dst = os.path.join(ROOT, key)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not (os.path.exists(dst) and (size is None or os.path.getsize(dst) == size)):
        s3.download_file(B, key, dst + ".part")
        os.replace(dst + ".part", dst)
    h = sha256(dst)
    with open(MAN, "a") as f:
        f.write(json.dumps(dict(utc=utc(), key=key, bytes=os.path.getsize(dst), sha256=h)) + "\n")
    return dst, h


def catalogue():
    _, segs = listing("PHerc0139/segments/", "/")
    cat = {}
    for sp in segs:
        sid = sp.rstrip("/").split("/")[-1]
        objs, _ = listing(sp)
        ent = dict(files={})
        for k, sz in objs:
            rel = k[len(sp):]
            if "/surface-volumes/" in "/" + rel and not rel.endswith((".zarray", ".zattrs", ".zgroup", "zarr.json")):
                continue          # chunk keys are not listed individually
            ent["files"][rel] = sz
        ent["sv"] = sorted({k[len(sp):].split("/")[1] for k, _ in objs if k[len(sp):].startswith("surface-volumes/")})
        cat[sid] = ent
        print(sid, len(ent["files"]), flush=True)
    json.dump(dict(generated_utc=utc(), bucket=B, segments=cat), open("/work/p139/catalogue.json", "w"), indent=1)


def meshes(which):
    cat = json.load(open("/work/p139/catalogue.json"))["segments"]
    jobs = []
    for sid, e in cat.items():
        for rel, sz in e["files"].items():
            if not rel.startswith("mesh/") or "/intermediate/" in "/" + rel:
                continue
            if (which in ("9", "both") and "-on-20250728140407-9.362um.tifxyz/" in rel) or \
               (which in ("2", "both") and "-on-20260102150214-2.399um.tifxyz/" in rel):
                jobs.append((f"PHerc0139/segments/{sid}/{rel}", sz))
    with ThreadPoolExecutor(8) as ex:
        for (k, _), (d, h) in zip(jobs, ex.map(lambda j: get(*j), jobs)):
            print(k, h, flush=True)


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "catalogue":
        catalogue()
    elif a == "meshes":
        meshes(sys.argv[2] if len(sys.argv) > 2 else "both")
    elif a == "keys":
        for k in sys.argv[2:]:
            print(k, get(k)[1])
