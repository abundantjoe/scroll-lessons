#!/usr/bin/env python
"""sweep_partial_reads.py -- remove a KILLED read's leftover maps before they can pair with a fresh one.

A read that is killed mid-way leaves its output directory holding a forward map, no reverse, no read_stats.json and
no .read_complete. Nothing ever scores it, so it corrupts no verdict on its own -- but the next run into that same
directory can write a fresh reverse beside the stale forward, and that pairing is the R-DEPTH artefact. Observed
twice on 2026-09-19: resuming R-CREST-POWER found one such leftover from the previous day, and a sweep then found
two more.

The predicate is deliberately conservative, because deleting a LIVE read's output is far worse than leaving a dead
one behind:
  - no `.read_complete` marker (a finished read is never touched), AND
  - the directory holds at least one .tif (nothing to do otherwise), AND
  - nothing in it has been modified for --min-age-h hours.
The age bar is 6 h by default against a longest-observed single-direction write of 1.9 h (the skew measurements in
`map_integrity.py`'s STALE note), so a slow live read is never in range. `--dry-run` is the default; deleting
requires --go.
"""
import argparse, glob, json, os, time
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

MIN_AGE_H = 6.0


def partial_reads(root=DATA + "/patches", min_age_h=MIN_AGE_H, now=None):
    now = now if now is not None else time.time()
    out = []
    for d in sorted(glob.glob(os.path.join(root, "*", "*", "read_*/"))):
        if os.path.exists(os.path.join(d, ".read_complete")):
            continue
        tifs = glob.glob(os.path.join(d, "*.tif"))
        if not tifs:
            continue
        newest = max(os.path.getmtime(p) for p in glob.glob(os.path.join(d, "*")))
        age_h = (now - newest) / 3600.0
        if age_h < min_age_h:
            continue
        out.append(dict(dir=d, n_tif=len(tifs), age_h=round(age_h, 2),
                        bytes=sum(os.path.getsize(p) for p in tifs)))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DATA + "/patches")
    ap.add_argument("--min-age-h", type=float, default=MIN_AGE_H)
    ap.add_argument("--go", action="store_true", help="actually delete; without it this only reports")
    a = ap.parse_args(argv)
    rows = partial_reads(a.root, a.min_age_h)
    if not rows:
        print("no partial reads older than %.1f h" % a.min_age_h)
        return 0
    total = sum(r["bytes"] for r in rows)
    for r in rows:
        print("%s partial read %-76s %d tif, %.1f h old, %.1f MB"
              % ("REMOVING" if a.go else "would remove", "/".join(r["dir"].split("/")[-4:-1]),
                 r["n_tif"], r["age_h"], r["bytes"] / 1e6))
        if a.go:
            import shutil
            shutil.rmtree(r["dir"])
    print("%d partial read(s), %.1f MB%s" % (len(rows), total / 1e6, "" if a.go else "  (--go to delete)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
