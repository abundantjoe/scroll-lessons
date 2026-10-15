"""flatcheck demo on PUBLIC Vesuvius Challenge open data (anonymous S3):
PHerc0139 organizer meshes on volume 20250728140407 (9.362 um), segments
w052 (a crushed, curved region where ABF++ collapses) and w059 (a gentle
region). Downloads ~3 MB per mesh; no CT volume and no image is read.

    pip install -e '.[demo]'
    python demo/run_demo.py [--abf]      # --abf needs FLATCHECK_ABF_CMD

Windows: the 4.00 cm^2 rectangles of the validation study, in the grid
produced by `flatcheck flatten --level` (levelled, 20 vox step).
"""

import argparse
import json
import sys
from pathlib import Path

import boto3
import botocore

from flatcheck import cli

BUCKET = "vesuvius-challenge-open-data"
CASES = {
    "w052_hard_H2": ("PHerc0139/segments/20260227000000-w052_2026022705/mesh/20260227000000-on-20250728140407-9.362um.tifxyz/",
                     (27, 305, 87, 133)),
    "w052_hard_H1": ("PHerc0139/segments/20260227000000-w052_2026022705/mesh/20260227000000-on-20250728140407-9.362um.tifxyz/",
                     (22, 324, 87, 131)),
    "w059_gentle": ("PHerc0139/segments/20250223000000-w059_2025022312/mesh/20250223000000-on-20250728140407-9.362um.tifxyz/",
                    (225, 300, 106, 108)),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--abf", action="store_true")
    ap.add_argument("--work", default="demo_work")
    a = ap.parse_args()
    s3 = boto3.client("s3", config=botocore.config.Config(signature_version=botocore.UNSIGNED))
    work = Path(a.work)
    out = {}
    for name, (key, rect) in CASES.items():
        d = work / key.split("/")[-2]
        d.mkdir(parents=True, exist_ok=True)
        for f in ("meta.json", "x.tif", "y.tif", "z.tif"):
            if not (d / f).exists():
                s3.download_file(BUCKET, key + f, str(d / f))
        cli.main(["report", str(d), "--json", str(work / f"{name}_report.json")])
        methods = ["slim", "arap"] + (["vc_flatten"] if a.abf else [])
        cli.main(["flatten", str(d), "--level", "--rect", *map(str, rect), "--out", str(work / name), "--method", *methods])
        res = json.loads((work / name / "flatcheck_result.json").read_text())
        rep = json.loads((work / f"{name}_report.json").read_text())
        out[name] = {"segment_mesh": key, "rect_levelled_grid": rect, "whole_mesh_report": {
            k: rep[k] for k in ("n_valid_quads", "pct_quads_within_tol_raw", "pct_quads_within_tol_norm", "fold_triangles")},
            "window": res["summary"]}
    Path("demo/demo_result.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    sys.exit(main())
