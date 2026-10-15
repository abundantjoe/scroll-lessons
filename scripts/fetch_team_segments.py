#!/usr/bin/env python
"""Fetch the team's PUBLISHED surface segments for a scroll into our patches dir, so the normal read pipeline
(run_patch_dir.py: QC 5.8 -> render -> R-CREST -> inference both orders -> rule 5.5 -> ledger) reads them with no
tracing at all.

Three eligible volumes publish segments in the open-data bucket (verified 2026-09-18):
    PHerc1447  53 surfaces   PHerc1203  22 surfaces   PHerc0800  6 surfaces
and nothing else among the 23 does. Two layouts occur under <scroll>/segments/ :

  raw/<uuid>/                                   x.tif y.tif z.tif meta.json [generations.tif]   (grown patch, as ours)
  <stamp>-<uuid>/mesh/<name>.tifxyz/            x.tif y.tif z.tif meta.json                     (flattened, resampled
                                                                                                 onto the volume)

A surface is fetched ONCE per uuid: the flattened mesh variant when it exists (that is the one the team renders),
otherwise the raw one. Which variant was taken, and the exact bucket prefix it came from, is written to source.json
inside the local dir, so every ledger line traces back to a public key. Local dirs are named team_<uuid> — distinct
from our own auto_grown_<timestamp> dirs, so ledger keys can never collide with a patch we traced ourselves.

usage: fetch_team_segments.py PHerc1203 [--out /home/user/hercules_data/patches/PHerc1203] [--limit N] [--raw]
"""
import argparse, json, os, sys, urllib.parse, urllib.request, xml.etree.ElementTree as ET
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
NEEDED = ("x.tif", "y.tif", "z.tif", "meta.json")
EXTRA = ("generations.tif",)


def list_keys(prefix, bucket=BUCKET):
    """Every key under prefix, following continuation tokens (a listing is capped at 1000)."""
    keys, token = [], None
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            q["continuation-token"] = token
        with urllib.request.urlopen(f"{bucket}/?{urllib.parse.urlencode(q)}", timeout=120) as r:
            root = ET.fromstring(r.read())
        keys += [(c.findtext(NS + "Key"), int(c.findtext(NS + "Size") or 0)) for c in root.findall(NS + "Contents")]
        if root.findtext(NS + "IsTruncated") != "true":
            return keys
        token = root.findtext(NS + "NextContinuationToken")


def segments(keys):
    """Group keys into {dir_prefix: {filename: size}} for dirs holding a complete tifxyz."""
    dirs = {}
    for k, size in keys:
        d, _, name = k.rpartition("/")
        dirs.setdefault(d + "/", {})[name] = size
    return {d: f for d, f in dirs.items() if all(n in f for n in NEEDED)}


def uuid_of(prefix):
    """The identity of a surface, from its path: the auto_grown_<stamp> component when present (both layouts carry
    it, raw/<uuid>/ and <stamp>-<uuid>/mesh/...), else the segment folder under segments/."""
    parts = [p for p in prefix.strip("/").split("/") if p]
    for p in reversed(parts):
        if "auto_grown_" in p:
            return p[p.index("auto_grown_"):]
    if "segments" in parts:
        i = parts.index("segments")
        if len(parts) > i + 1 and parts[i + 1] != "raw":
            return parts[i + 1]
    return parts[-1]


def fetch(url, dest):
    tmp = dest + ".part"
    with urllib.request.urlopen(url, timeout=300) as r, open(tmp, "wb") as fh:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            fh.write(b)
    os.replace(tmp, dest)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scroll")
    ap.add_argument("--out", default=None, help="default /home/user/hercules_data/patches/<scroll>")
    ap.add_argument("--limit", type=int, default=None, help="fetch at most N surfaces (largest area first)")
    ap.add_argument("--raw", action="store_true", help="take the raw grown patch even when a flattened mesh exists")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    out = a.out or f"{DATA}/patches/{a.scroll}"

    keys = list_keys(f"{a.scroll}/segments/")
    # mesh/intermediate/* holds pre-flattening scratch copies of the same surface: never a reading surface
    keys = [(k, n) for k, n in keys if "/mesh/intermediate/" not in k]
    segs = segments(keys)
    if not segs:
        print(f"{a.scroll}: no published segments under {a.scroll}/segments/")
        return 1

    # one entry per uuid; prefer the flattened mesh variant unless --raw
    best = {}
    for d, files in segs.items():
        u = uuid_of(d)
        flat = "/mesh/" in d
        rank = (0 if a.raw else 1) if flat else (1 if a.raw else 0)
        cur = best.get(u)
        if cur is None or rank > cur[0]:
            best[u] = (rank, d, files)

    rows = []
    for u, (_, d, files) in best.items():
        rows.append(dict(uuid=u, prefix=d, files=files, variant=("flattened" if "/mesh/" in d else "raw"),
                         bytes=sum(files[n] for n in NEEDED if n in files)))
    rows.sort(key=lambda r: -r["bytes"])
    if a.limit:
        rows = rows[: a.limit]

    print(f"{a.scroll}: {len(segs)} tifxyz dirs under segments/, {len(best)} distinct surfaces, fetching {len(rows)}")
    total = 0
    for r in rows:
        dest = os.path.join(out, "team_" + r["uuid"].replace("auto_grown_", ""))
        marker = os.path.join(dest, "source.json")
        if os.path.exists(marker):
            print(f"  have {os.path.basename(dest)}")
            continue
        if a.dry_run:
            print(f"  would fetch {r['prefix']} -> {dest} ({r['variant']}, {r['bytes'] / 1e6:.2f} MB)")
            continue
        os.makedirs(dest, exist_ok=True)
        for name in NEEDED + EXTRA:
            if name not in r["files"]:
                continue
            fetch(f"{BUCKET}/{urllib.parse.quote(r['prefix'] + name)}", os.path.join(dest, name))
            total += r["files"][name]
        meta = json.load(open(os.path.join(dest, "meta.json")))
        json.dump(dict(scroll=a.scroll, uuid=r["uuid"], variant=r["variant"], bucket_prefix=r["prefix"],
                       url=f"{BUCKET}/{r['prefix']}", area_cm2=meta.get("area_cm2"), fetched_by="scripts/fetch_team_segments.py"),
                  open(marker, "w"), indent=1)
        print(f"  fetched {os.path.basename(dest)}  {r['variant']}  area {meta.get('area_cm2', float('nan')):.2f} cm2  from {r['prefix']}")
    print(f"{a.scroll}: {total / 1e6:.1f} MB into {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
