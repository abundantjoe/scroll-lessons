#!/usr/bin/env python
"""RULES G-GP part 3/4: materialise a BOX of a surface-prediction zarr locally.

vc_grow_seg_from_segments opens its volume with VcDataset, a local-filesystem zarr reader, so stage 2 cannot stream
from s3:// the way vc_grow_seg_from_seed does. This fetches only the level-0 chunks covering a given voxel box.

Chunks outside the box are simply absent, and a zarr reader returns the array's fill_value (0) for them. For a
SURFACE PREDICTION 0 means "not a sheet", so growth stops at the box edge instead of being misled -- a bounded,
honest failure mode. (Contrast the direction-field case recorded in RULES, where a missing chunk decodes to a
confident WRONG direction; that is why this is safe and that would not have been.)

usage: fetch_pred_box.py --scroll PHerc0826 --vol 20250821151701 --box x0 x1 y0 y1 z0 z1 --out <dir>
                         [--margin 200] [--min-free-gb 3] [--um 9.362]
"""
import argparse, json, os, sys, time
import numpy as np
import requests

BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
SUFFIX = "-surface-20260413222639-surface-m7-L0-th0.2"
CA = os.environ.get("CURL_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")


def free_gb(path):
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize / 1e9


def get(sess, url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return 0
    for attempt in range(5):
        try:
            r = sess.get(url, timeout=60)
        except Exception:
            time.sleep(2 * (attempt + 1)); continue
        if r.status_code == 404:
            return 0                       # absent chunk: the reader returns fill_value 0 = "not a sheet"
        if r.status_code == 200:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest + ".part", "wb") as f:
                f.write(r.content)
            os.replace(dest + ".part", dest)
            return len(r.content)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError("failed to fetch " + url)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scroll", required=True)
    ap.add_argument("--vol", required=True)
    ap.add_argument("--box", nargs=6, type=float, required=True, metavar=("X0", "X1", "Y0", "Y1", "Z0", "Z1"))
    ap.add_argument("--margin", type=float, default=200.0, help="voxels of slack around the box")
    ap.add_argument("--out", required=True)
    ap.add_argument("--um", type=float, default=9.362)
    ap.add_argument("--min-free-gb", type=float, default=3.0)
    a = ap.parse_args(argv)
    base = "%s/%s/representations/predictions/surfaces/%s%s.zarr" % (BUCKET, a.scroll, a.vol, SUFFIX)
    os.makedirs(a.out, exist_ok=True)
    sess = requests.Session()
    sess.verify = CA
    for rel in (".zattrs", ".zgroup", "0/.zarray"):
        try:
            get(sess, base + "/" + rel, os.path.join(a.out, rel))
        except Exception as e:
            print("  %s: %s" % (rel, e))
    zarray = json.load(open(os.path.join(a.out, "0", ".zarray")))
    cz, cy, cx = zarray["chunks"]            # store axes are z, y, x
    x0, x1, y0, y1, z0, z1 = a.box
    cx0, cx1 = int((x0 - a.margin) // cx), int((x1 + a.margin) // cx)
    cy0, cy1 = int((y0 - a.margin) // cy), int((y1 + a.margin) // cy)
    cz0, cz1 = int((z0 - a.margin) // cz), int((z1 + a.margin) // cz)
    keys = [(z, y, x) for z in range(max(0, cz0), cz1 + 1)
            for y in range(max(0, cy0), cy1 + 1) for x in range(max(0, cx0), cx1 + 1)]
    print("fetching %d chunks of %s into %s (box x %d-%d y %d-%d z %d-%d, margin %.0f)"
          % (len(keys), os.path.basename(base), a.out, x0, x1, y0, y1, z0, z1, a.margin))
    total = present = 0
    t0 = time.time()
    for i, (z, y, x) in enumerate(keys):
        if free_gb(a.out) < a.min_free_gb:
            print("STOPPING at %d/%d chunks: free disk %.1f GB below the %.1f GB floor"
                  % (i, len(keys), free_gb(a.out), a.min_free_gb))
            break
        n = get(sess, "%s/0/%d/%d/%d" % (base, z, y, x), os.path.join(a.out, "0", str(z), str(y), str(x)))
        total += n
        present += 1 if n else 0
        if (i + 1) % 100 == 0:
            print("  %4d/%d chunks, %6.1f MB, %5.0f s" % (i + 1, len(keys), total / 1e6, time.time() - t0),
                  flush=True)
    json.dump({"voxelsize": a.um, "format": "zarr", "scroll": a.scroll, "volume": a.vol,
               "note": "PARTIAL local copy: only chunks covering the recorded box are present; every other chunk "
                       "reads as the array fill value 0, which for a surface prediction means 'not a sheet', so "
                       "growth stops at the box edge.",
               "box": dict(x=[x0, x1], y=[y0, y1], z=[z0, z1], margin=a.margin),
               "chunks_requested": len(keys), "chunks_present": present, "bytes": total},
              open(os.path.join(a.out, "meta.json"), "w"), indent=1)
    print("done: %d/%d chunks present, %.1f MB, %.0f s" % (present, len(keys), total / 1e6, time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
