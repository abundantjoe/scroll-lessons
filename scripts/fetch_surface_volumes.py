#!/usr/bin/env python
"""Fetch the team's PUBLISHED surface volumes (their own renders of their own segments) into our patch dirs as
render.zarr, so run_patch_dir.py skips rendering entirely and goes straight to R-CREST -> inference -> rule 5.5.

Two eligible volumes publish these, under each segment:
    <scroll>/segments/<stamp>-<uuid>/surface-volumes/<pitch>-volume-<vol>.zarr/     31 slices, uint8, chunks 31x128x128
PHerc1447 has 15 (202.8 cm2 of canvas, 8.4 GB) and PHerc0800 6 (19.5 cm2, 0.8 GB). PHerc1203 publishes none, so its
surfaces are rendered by us as usual.

Using their render instead of ours is sound because Gate B established that our rebuilt vc_render_tifxyz reproduces a
team stack pixel for pixel (Pearson 0.999999, 99.6 % of pixels identical) and scores the same through the model. The
provenance of every fetched stack is written to render_source.json beside it, and the local patch dir is team_<uuid>,
so a ledger line can never be mistaken for one of our own traces.

Disk: this box has ~30 GB. --max-ahead keeps at most N unread published renders on disk at a time; a render is
dropped by the read loop (--delete-renders) once its read is in the ledger.

usage: fetch_surface_volumes.py PHerc0800 [--max-ahead 2] [--loop 120] [--dry-run]
"""
import argparse, concurrent.futures as cf, json, os, sys, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
PATCHES = DATA + "/patches"


def list_keys(prefix, bucket=BUCKET):
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


def surface_volumes(scroll):
    """{uuid: {'prefix': .., 'keys': [(key, size)], 'bytes': n}} for every published surface-volume zarr."""
    out = {}
    for key, size in list_keys(f"{scroll}/segments/"):
        if "/surface-volumes/" not in key or ".zarr/" not in key:
            continue
        head, _, _ = key.partition(".zarr/")
        prefix = head + ".zarr/"
        seg = key.split("/segments/", 1)[1].split("/", 1)[0]
        uuid = seg[seg.index("auto_grown_"):] if "auto_grown_" in seg else seg
        e = out.setdefault(uuid, dict(prefix=prefix, keys=[], bytes=0))
        e["keys"].append((key, size)); e["bytes"] += size
    return out


def fetch_one(key, dest_root, prefix):
    rel = key[len(prefix):]
    dest = os.path.join(dest_root, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest):
        return 0
    tmp = dest + ".part"
    with urllib.request.urlopen(f"{BUCKET}/{urllib.parse.quote(key)}", timeout=300) as r, open(tmp, "wb") as fh:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            fh.write(b)
    os.replace(tmp, dest)
    return os.path.getsize(dest)


def unread_renders(scroll):
    """Published renders already on disk whose read is not finished yet."""
    n = 0
    root = os.path.join(PATCHES, scroll)
    for d in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        p = os.path.join(root, d)
        if not os.path.exists(os.path.join(p, "render.zarr.complete")):
            continue
        import glob
        if not glob.glob(os.path.join(p, "read_*", ".read_complete")):
            n += 1
    return n


def already_read(patch):
    import glob
    return bool(glob.glob(os.path.join(patch, "read_*", ".read_complete")))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scroll")
    ap.add_argument("--max-ahead", type=int, default=2, help="keep at most N unread published renders on disk")
    ap.add_argument("--min-free-gb", type=float, default=4.0, help="never start a fetch below this much free disk")
    ap.add_argument("--loop", type=int, default=0, help="keep topping up every N seconds (0 = one pass)")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    vols = surface_volumes(a.scroll)
    if not vols:
        print(f"{a.scroll}: no published surface volumes"); return 1
    order = sorted(vols.items(), key=lambda kv: kv[1]["bytes"])   # cheapest first: more reads per GB
    print(f"{a.scroll}: {len(vols)} published surface volumes, {sum(v['bytes'] for v in vols.values()) / 1e9:.2f} GB total")
    for u, v in order:
        print(f"  {u}  {v['bytes'] / 1e6:8.1f} MB  {v['prefix']}")
    if a.dry_run:
        return 0

    while True:
        for uuid, v in order:
            patch = os.path.join(PATCHES, a.scroll, "team_" + uuid.replace("auto_grown_", ""))
            if not os.path.isdir(patch):
                continue                      # surface not fetched by fetch_team_segments.py
            out = os.path.join(patch, "render.zarr")
            if os.path.exists(out + ".complete") or already_read(patch):
                continue
            free = os.statvfs("/").f_bavail * os.statvfs("/").f_frsize / 1e9
            if free < a.min_free_gb:
                print(f"[fetch_surface_volumes] {free:.1f} GB free < {a.min_free_gb}: waiting"); break
            if unread_renders(a.scroll) >= a.max_ahead:
                break
            t = time.time()
            print(f"[fetch_surface_volumes] {uuid}: {v['bytes'] / 1e6:.0f} MB -> {out}", flush=True)
            try:                      # a transient proxy/network error must not end the loop: retry on the next pass
                with cf.ThreadPoolExecutor(a.threads) as ex:
                    list(ex.map(lambda k: fetch_one(k[0], out, v["prefix"]), v["keys"]))
            except Exception as exc:
                print(f"[fetch_surface_volumes] {uuid}: fetch failed ({exc}); will retry", flush=True)
                continue
            json.dump(dict(scroll=a.scroll, uuid=uuid, bucket_prefix=v["prefix"], url=f"{BUCKET}/{v['prefix']}",
                           bytes=v["bytes"], n_keys=len(v["keys"]),
                           note="published surface volume (the team's own render of this segment); our renderer reproduces "
                                "such stacks pixel for pixel, see RULES Gate B"),
                      open(os.path.join(patch, "render_source.json"), "w"), indent=1)
            open(out + ".complete", "w").write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} fetched from {v['prefix']}\n")
            print(f"[fetch_surface_volumes] {uuid}: done in {time.time() - t:.0f} s", flush=True)
        if not a.loop:
            return 0
        time.sleep(a.loop)
        try:                          # the listing can fail the same way; keep the loop alive
            vols = surface_volumes(a.scroll); order = sorted(vols.items(), key=lambda kv: kv[1]["bytes"])
        except Exception as exc:
            print(f"[fetch_surface_volumes] listing failed ({exc}); keeping the previous list", flush=True)


if __name__ == "__main__":
    sys.exit(main())
