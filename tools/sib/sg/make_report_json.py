# Provenance: Project HERCULES | owner the owner | [id removed]
"""Assemble logs/sib/sg/sg_report.json from files on disk (no hand-typed numbers).

  python tools/sib/sg/make_report_json.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "tools/sib/sg/pkg"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(PKG / "src" / "hercules"))  # staged package, imported as top-level "sg"

from hercules.records.codehash import combined_sha256, file_sha256  # noqa: E402

from sg import constants as C  # noqa: E402

CODE = sorted(str(p.relative_to(ROOT)) for p in (PKG / "src/hercules/sg").glob("*.py"))
TOOLS = sorted(str(p.relative_to(ROOT)) for p in list((ROOT / "tools/sib/sg").glob("*.*")) + [PKG / "run_merged_tests.sh"])
TESTS = sorted([str(p.relative_to(ROOT)) for p in (PKG / "tests").glob("test_sg_*.py")] +
               [str(p.relative_to(ROOT)) for p in (ROOT / "tests").glob("sib_sg_*.py")])
SCORER_REUSED = ["src/hercules/scorer/canon.py", "src/hercules/scorer/consensus.py", "src/hercules/scorer/letters.py",
                 "src/hercules/scorer/matching.py", "src/hercules/scorer/constants.py"]


def hashes(paths):
    pairs = [(p, file_sha256(ROOT / p)) for p in paths]
    return {"files": dict(pairs), "combined_sha256": combined_sha256(pairs)}


def main() -> None:
    null = json.loads((ROOT / "logs/sib/sg/copytest_null.json").read_text())
    cells = {k: {kk: c[kk] for kk in ("d", "sigma", "n_eff_approx", "median_max_ncc", "false_flag_fraction")} |
             {"n_patches": c.get("n_patches", null["n_patches"]), "max_of_max_ncc": max(c["max_ncc_per_crop"])}
             for k, c in sorted(null["cells"].items())}
    runs = [json.loads(l) for l in (ROOT / "logs/sib/sg/runs.jsonl").read_text().splitlines() if l.strip()]
    synth = ROOT / "logs/sib/sg/synthetic_pass_result.json"
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    bars = {k: getattr(C, k) for k in dir(C) if k.isupper() and not k.startswith("_")}
    rep = {
        "provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
        "task": "sg",
        "sg_version": C.SG_VERSION,
        "declarations": ["RULES.md DECL-SG", "RULES.md DECL-EMPNULL"],
        "base_commit_at_assembly": head,
        "code_hashes": hashes(CODE),
        "code_hashes_note": "paths are the staged ones; after the merge hash src/hercules/sg/*.py (same bytes)",
        "tool_hashes": hashes(TOOLS),
        "test_hashes": hashes(TESTS),
        "scorer_modules_reused": hashes(SCORER_REUSED),
        "constants": {k: (list(v) if isinstance(v, tuple) else v) for k, v in bars.items()},
        "computed_items": list(C.COMPUTED_ITEMS),
        "partial_items": C.PARTIAL_ITEMS,
        "attested_items": ["0", "8", "10", "12", "14_profile", "14_tests"],
        "fresh_reads": list(C.FRESH_READS),
        "synthetic_pass_result_sha256": file_sha256(synth) if synth.exists() else None,
        "copytest_null": {"seed": null["seed"], "rotations": null["rotations"], "n_crops": null["n_crops"],
                          "json_sha256": file_sha256(ROOT / "logs/sib/sg/copytest_null.json"), "cells": cells},
        "runs": runs,
        "proposals": ["logs/sib/sg/proposals/PROPOSAL-SG-CODE-1.md", "logs/sib/sg/proposals/PROPOSAL-SG-LINESPACING-1.md"],
        "rulings_applied": "logs/sib/sg/rulings_applied.md",
        "ask": "logs/sib/sg/ASK.md",
        "copytest_null_abs": {"json_sha256": file_sha256(ROOT / "logs/sib/sg/copytest_null_abs.json"),
                              "cells": {k: {kk: c[kk] for kk in ("d", "sigma", "n_eff_approx", "median_max_ncc", "false_flag_fraction")}
                                        | {"max_of_max_abs_ncc": max(c["max_ncc_per_crop"]), "n_patches": c.get("n_patches", 100)}
                                        for k, c in sorted(json.loads((ROOT / "logs/sib/sg/copytest_null_abs.json").read_text())["cells"].items())}},
        "label_survey_0139": {"json_sha256": file_sha256(ROOT / "logs/sib/sg/label_survey_0139.json"),
                              "letter_blobs": json.loads((ROOT / "logs/sib/sg/label_survey_0139.json").read_text())["letter_blobs_2p4um_level2"],
                              "n_components_per_set": {p["segment"][15:19] + "@" + p["labels_on"][:8]: p["n_components"]
                                                       for p in json.loads((ROOT / "logs/sib/sg/label_survey_0139.json").read_text())["per_set"]}},
        "label_spacing_0139_t20_t30": "INVALID as statistics (2-13 blobs per tile); kept as the logged record",
    }
    out = ROOT / "logs/sib/sg/sg_report.json"
    out.write_text(json.dumps(rep, indent=1, sort_keys=True, ensure_ascii=True) + "\n")
    print(file_sha256(out), out.relative_to(ROOT))


if __name__ == "__main__":
    main()
