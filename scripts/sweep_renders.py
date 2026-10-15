#!/usr/bin/env python
"""Delete renders no read still needs.

--delete-renders removes a render after a successful read, but a read that is interrupted (a paused loop, a restarted
container, a killed process) leaves its render behind, and renders are the largest thing this pipeline writes. A render
is removable when the patch has at least one FINISHED read and no UNFINISHED one: an unfinished read dir means an
inference is either running or queued against that render, so it is kept.

Both completion markers go with it (ours and vc_tools.sh's), or a later re-read would skip rendering.

usage: sweep_renders.py [--patches DIR] [--dry-run]
"""
import argparse, glob, os, shutil, sys, time
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA


MIN_AGE_S = 600      # a render written within the last 10 minutes is assumed live


def removable(patch, render, now=None):
    """A render is removable only when it is FINISHED and nothing still needs it.

    Finished means its completion marker exists: a render being written has no marker, and deleting one mid-write is
    exactly what happened to PHerc1203 on 2026-09-18 - the patch had a finished earlier read, so an unconditional
    'all reads done' test called the in-progress re-read's render removable and killed it three times in a row.
    A recent mtime is a second guard for the same case.
    """
    if not os.path.exists(render + ".complete") and not os.path.exists(os.path.join(patch, ".render_complete")):
        return False                                   # no completion marker: the render is being written
    try:
        age = (now or time.time()) - max(os.path.getmtime(dp) for dp, _, _ in os.walk(render))
    except ValueError:
        return False
    if age < MIN_AGE_S:
        return False                                   # touched very recently: assume live
    reads = glob.glob(os.path.join(patch, "read_*"))
    if not reads:
        return False                                   # never read: the render may be about to be read
    done = [r for r in reads if os.path.exists(os.path.join(r, ".read_complete"))]
    return bool(done) and len(done) == len(reads)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--patches", default=DATA + "/patches")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    freed = n = 0
    for render in sorted(glob.glob(os.path.join(a.patches, "*", "*", "render.zarr"))):
        patch = os.path.dirname(render)
        if not removable(patch, render):
            continue
        size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(render) for f in fs)
        print(f"[sweep_renders] {os.path.relpath(patch, a.patches)}: {size / 1e6:.0f} MB, every read finished")
        if not a.dry_run:
            shutil.rmtree(render, ignore_errors=True)
            for m in (os.path.join(patch, ".render_complete"), render + ".complete"):
                if os.path.exists(m):
                    os.remove(m)
        freed += size; n += 1
    print(f"[sweep_renders] {n} render(s), {freed / 1e6:.0f} MB{' (dry run)' if a.dry_run else ' freed'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
