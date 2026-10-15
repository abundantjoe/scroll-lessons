# Provenance: Project HERCULES | owner the owner | [id removed]
"""Called by reproduce.sh. Fresh metadata.json fetch, fresh official render of the given mesh in a clean
work directory, image rebuild, sha256 comparison with package.json. Prints one JSON object; exit 0 only if
the raw render, the CT panel and the whole PNG are byte-identical to the package."""
import argparse
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_image as BI  # noqa: E402
import pngio  # noqa: E402
import render_build as RB  # noqa: E402


def h(b):
    return hashlib.sha256(b).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", required=True)
    ap.add_argument("--volume-url", required=True)
    ap.add_argument("--mesh", required=True)
    ap.add_argument("--workdir", required=True)
    a = ap.parse_args(argv)
    pkg = json.load(open(os.path.join(a.package, "package.json")))
    os.makedirs(a.workdir, exist_ok=False)
    md = os.path.join(a.workdir, "metadata.json")
    md_sha = RB.fetch_metadata(a.volume_url, md)
    voxel = RB.voxel_um_from_metadata(md)
    raw, cmd, t0, t1 = RB.render(a.volume_url, a.mesh, os.path.join(a.workdir, "render"), voxel)
    img, info = BI.compose(raw, voxel, pkg["image"]["scale"], pkg["dry_run"])
    png = pngio.encode_png_gray8(img)
    p0, p1 = info["panel_rows"]
    res = dict(
        utc_start=t0, utc_end=t1, workdir=a.workdir, volume_url=a.volume_url,
        volume_url_matches_package=a.volume_url == pkg["volume_url"],
        metadata_sha256=md_sha, metadata_matches=md_sha == pkg["volume_metadata"]["sha256"],
        voxel_size_um=voxel, voxel_matches=voxel == pkg["voxel_size_um"],
        raw_pixels_sha256=h(np.ascontiguousarray(raw).tobytes()),
        raw_identical=h(np.ascontiguousarray(raw).tobytes()) == pkg["raw_render"]["pixels_sha256"],
        panel_sha256=h(np.ascontiguousarray(img[p0:p1]).tobytes()),
        panel_identical=h(np.ascontiguousarray(img[p0:p1]).tobytes()) == pkg["image"]["panel_sha256"],
        png_sha256=h(png), png_identical=h(png) == pkg["image"]["sha256"],
    )
    ok = all(res[k] for k in ("volume_url_matches_package", "metadata_matches", "voxel_matches", "raw_identical",
                              "panel_identical", "png_identical"))
    res["reproduced_byte_identical"] = ok
    open(os.path.join(a.workdir, "reproduce_result.json"), "w").write(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
