#!/usr/bin/env python3
"""Download one public tifxyz mesh from the Vesuvius Challenge open-data bucket
(anonymous HTTPS, standard library only). Only the four mesh files are fetched
(x.tif, y.tif, z.tif, meta.json); no CT volume is downloaded.

Example (PHerc0139, 9.362 um volume 20250728140407, about 2.3 MB):
  python scripts/fetch_segment.py PHerc0139 20260227000000-w052_2026022705 20250728140407-9.362um data_cache/
"""

import argparse
import hashlib
import urllib.request
from pathlib import Path

BUCKET_URL = "https://vesuvius-challenge-open-data.s3.amazonaws.com"


def fetch(scroll: str, segment: str, volume_tag: str, out: Path) -> Path:
    ts = segment.split("-")[0]
    name = f"{ts}-on-{volume_tag}.tifxyz"
    key = f"{scroll}/segments/{segment}/mesh/{name}"
    d = out / scroll / segment / name
    d.mkdir(parents=True, exist_ok=True)
    for f in ("meta.json", "x.tif", "y.tif", "z.tif"):
        p = d / f
        if not p.exists():
            with urllib.request.urlopen(f"{BUCKET_URL}/{key}/{f}", timeout=120) as r:
                p.write_bytes(r.read())
        print(f"{key}/{f}  {p.stat().st_size} B  sha256 {hashlib.sha256(p.read_bytes()).hexdigest()}")
    return d


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scroll")
    ap.add_argument("segment")
    ap.add_argument("volume_tag", help="e.g. 20250728140407-9.362um (the '<volume id>-<voxel size>' part of the mesh name)")
    ap.add_argument("out", type=Path)
    a = ap.parse_args()
    print(fetch(a.scroll, a.segment, a.volume_tag, a.out))


if __name__ == "__main__":
    main()
