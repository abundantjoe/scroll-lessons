# Provenance: Project HERCULES | owner the owner | [id removed]
"""flatpkg timings per 4 cm^2 rectangle at 9.362 and 2.399 um (FLAT-1 w059
and w047 patches; 3 CPU for ABF++ in docker, 1 thread for libigl), with
package write + verify. Output: logs/sib/flat1/flatpkg_timing.json."""
import json
import time
from pathlib import Path

import flatpkg as P
from hercules.geometry import tifxyz as T

CASES = {"9.362um": ("/work/flat1/abf/{s}/patch.tifxyz", 9.362), "2.399um": ("/work/flat1/2p4um/abf/{s}/patch.tifxyz", 2.399)}
SEGS = ("20250223000000-w059_2025022312", "20260206000001-w047_2026020613")
out = []
for res, (tmpl, vox) in CASES.items():
    for s in SEGS:
        m = T.read_tifxyz(tmpl.format(s=s))
        for meth in P.METHODS:
            r = P.flatten(m.points, meth, voxel_um=vox)
            t0 = time.time()
            d = Path("/work/flat1/timing") / res / s / meth
            rec = P.write_package(d, m.points, r.uv, method=meth, voxel_um=vox, info=r.info)
            ok, _ = P.verify_package(d)
            row = {"resolution": res, "segment": s, "grid": list(m.points.shape[:2]), "method": meth,
                   "flatten_seconds": r.seconds, "package_write_verify_seconds": time.time() - t0, "verified": ok,
                   "pct_quads_within_5pct": rec["metrics"]["pct_quads_within_5pct"], "collapsed": rec["collapse"]["collapsed"]}
            out.append(row)
            print(row, flush=True)
Path("logs/sib/flat1/flatpkg_timing.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
