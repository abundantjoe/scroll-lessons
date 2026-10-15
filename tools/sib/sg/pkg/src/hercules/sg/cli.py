# Provenance: Project HERCULES | owner the owner | [id removed]
"""Command line runner for the submission gate SG.

  python -m hercules.sg.cli INPUTS.json --out RESULT.json [--crops CROPS.npz --patches PATCHES.npz]
  python -m hercules.sg.cli --synthetic --out RESULT.json          (known-answer self-test)

INPUTS.json follows hercules.sg.gate.sg_check.  CROPS.npz / PATCHES.npz hold one 2-D float array per
key (letter crops cut by code at the agreed boxes; training-label patches at the same
px/mm); when given, the copy test (DECL-SG 7) is computed here.  The result is written as
sorted-key JSON; its sha256 is printed.  Exit code: 0 if SG passes, 1 if not, 2 on error.
Nothing here opens, displays or describes an image; npz arrays are only correlated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from . import gate as sg_gate


def _load_npz(path: str) -> list[np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return [np.asarray(z[k], dtype=np.float64) for k in sorted(z.files)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="?")
    ap.add_argument("--out", required=True)
    ap.add_argument("--crops")
    ap.add_argument("--patches")
    ap.add_argument("--synthetic", action="store_true", help="run on hercules.sg.synth.passing_inputs()")
    a = ap.parse_args(argv)
    if a.synthetic:
        from . import synth as sg_synth

        inputs = sg_synth.passing_inputs()
        inputs.pop("_sealers_for_band")
    elif a.inputs:
        inputs = json.loads(Path(a.inputs).read_text(encoding="utf-8"))
    else:
        ap.error("INPUTS.json or --synthetic is required")
    if bool(a.crops) != bool(a.patches):
        ap.error("--crops and --patches go together")
    crops = _load_npz(a.crops) if a.crops else None
    patches = _load_npz(a.patches) if a.patches else None
    res = sg_gate.sg_check(inputs, copy_crops=crops, copy_patches=patches)
    text = json.dumps(sg_gate._hashable(res), sort_keys=True, indent=1, ensure_ascii=True, allow_nan=False)
    Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(f"overall {res['overall']} not_passed {','.join(res['not_passed']) or '-'}")
    print(f"sha256 {hashlib.sha256((text + chr(10)).encode('ascii')).hexdigest()}  {a.out}")
    return 0 if res["overall"] == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        print(f"error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
