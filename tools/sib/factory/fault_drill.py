# Provenance: Project HERCULES | owner the owner | [id removed]
"""Plant faults into copies of a finished package and confirm the verifier rejects each one.
Faults: hidden PNG tEXt chunk; scale bar 6 px short; Unicode Cf (U+200B) in README.txt; wrong volume ID;
'DRY RUN' relabelled as a real package; gamma applied to the CT panel. Hashes (package.json image sha256 and
SHA256SUMS) are refreshed after each plant, so only the targeted check can catch it.
Usage: fault_drill.py PACKAGE_DIR OUT_JSON   (copies go to /work/factory/drill/)"""
import json
import os
import shutil
import struct
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import factory as F  # noqa: E402
import pngio  # noqa: E402
import verify as V  # noqa: E402


def pj(d):
    return json.load(open(os.path.join(d, "package.json")))


def save(d, p):
    open(os.path.join(d, "package.json"), "w").write(json.dumps(p, indent=1, sort_keys=True) + "\n")


def reseal(d):
    p = pj(d)
    p["image"]["sha256"] = F.sha256_file(os.path.join(d, p["image"]["file"]))
    save(d, p)
    F.write_manifest(d)


def img_of(d):
    return pngio.decode_canonical_png(open(os.path.join(d, pj(d)["image"]["file"]), "rb").read())


def put_img(d, img):
    open(os.path.join(d, pj(d)["image"]["file"]), "wb").write(pngio.encode_png_gray8(img))
    reseal(d)


def f_text_chunk(d):
    f = os.path.join(d, pj(d)["image"]["file"])
    b = open(f, "rb").read()
    body = b"Comment\x00planted"
    ch = struct.pack(">I", len(body)) + b"tEXt" + body + struct.pack(">I", zlib.crc32(b"tEXt" + body) & 0xFFFFFFFF)
    open(f, "wb").write(b[:33] + ch + b[33:])
    reseal(d)


def f_scale_bar(d):
    p = pj(d)
    img = img_of(d)
    y0, y1 = p["scale_bar"]["rows"]
    x0, L = p["scale_bar"]["x0"], p["scale_bar"]["length_px"]
    img[y0:y1, x0 + L - 6:x0 + L] = 0
    put_img(d, img)


def f_cf(d):
    f = os.path.join(d, "README.txt")
    s = open(f).read()
    open(f, "w", encoding="utf-8").write(s.replace("Package:", "Pack" + chr(0x200B) + "age:"))
    F.write_manifest(d)


def f_volume_id(d):
    p = pj(d)
    p["volume_id"] = "20250821151825"  # an eligible id (PHerc0125) that is not this package's volume
    save(d, p)
    F.write_manifest(d)


def f_relabel_real(d):
    p = pj(d)
    p["dry_run"] = False
    save(d, p)
    F.write_manifest(d)


def f_gamma(d):
    p = pj(d)
    img = img_of(d)
    a, b = p["image"]["panel_rows"]
    img[a:b] = np.rint(255.0 * (img[a:b] / 255.0) ** 0.8).astype(np.uint8)
    put_img(d, img)


FAULTS = {"hidden_png_text_chunk": (f_text_chunk, "png_no_metadata"),
          "scale_bar_6px_short": (f_scale_bar, "scale_bar_measured"),
          "cf_char_in_readme": (f_cf, "no_cf_characters"),
          "wrong_volume_id": (f_volume_id, "volume_eligible"),
          "dry_run_relabelled_real": (f_relabel_real, "dry_run_marking"),
          "gamma_on_ct_panel": (f_gamma, "linear_display")}


def main(pkg, out):
    base = V.verify(pkg)
    if not base["passed"]:
        print("clean package does not verify; drill invalid:", [c for c in base["checks"] if not c["ok"]])
    res = dict(provenance=F.PROV, package=os.path.basename(pkg), clean_passed=base["passed"], faults={})
    for name, (fn, expect) in FAULTS.items():
        root = f"/work/factory/drill/{name}/packages/dryrun"
        shutil.rmtree(f"/work/factory/drill/{name}", ignore_errors=True)
        os.makedirs(root)
        d = os.path.join(root, os.path.basename(pkg))
        shutil.copytree(pkg, d)
        fn(d)
        r = V.verify(d)
        failed = [c["check"] for c in r["checks"] if not c["ok"]]
        det = next(c["detail"] for c in r["checks"] if c["check"] == expect)
        res["faults"][name] = dict(rejected=not r["passed"], expected_check=expect,
                                   expected_check_failed=expect in failed and not det.startswith("not run"),
                                   failed_checks=failed,
                                   detail=next(c["detail"] for c in r["checks"] if c["check"] == expect))
    res["all_rejected_by_expected_check"] = res["clean_passed"] and all(v["rejected"] and v["expected_check_failed"] for v in res["faults"].values())
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))
    return 0 if res["clean_passed"] and res["all_rejected_by_expected_check"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
