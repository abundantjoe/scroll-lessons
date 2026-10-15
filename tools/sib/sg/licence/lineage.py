# Provenance: Project HERCULES | owner the owner | [id removed]
"""Licence-lineage checker (PRIZE-CHECK-20260925 item b): a pre-submission package item,
never an SG bar.

Winners must open-source "their code, data, model weights and results" and, per the form's
terms, under a permissive licence.  For every checkpoint and dataset in a candidate
reader's lineage this reports:
  PERMITS-RELEASE  the licence is a recognised permissive licence, stated consistently;
  BLOCKS           the licence forbids the release the prize asks for: code and checkpoints must
                   be permissive; NC, ND, SA, copyleft or proprietary terms block them. A dataset
                   under CC BY-NC 4.0 (no ND/SA) PERMITS release under the same terms, because the
                   organizers' own dataset rule asks for CC-BY-NC 4.0 (logs/sib/sg/p4kit/Q11.md);
  UNVERIFIED       no licence, an unrecognised one, or inconsistent statements.
Overall: BLOCKS if any item BLOCKS, else UNVERIFIED if any item is UNVERIFIED, else
PERMITS-RELEASE.  Inputs are public model-card and dataset metadata only (the project's
catalogue records, which cite their source URLs and hashes); nothing is downloaded here.
The verdicts are mechanical readings of licence identifiers, not legal advice; the owner
decides.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

PERMISSIVE = {"mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc", "cc0-1.0", "cc-by-4.0", "unlicense", "zlib"}
BLOCKING_PATTERNS = [
    (r"\bcc[- ]?by[- ]?nc", "non-commercial (NC) terms forbid permissive relicensing"),
    (r"\bcc[- ]?by[- ]?(?:[a-z]+-)?nd\b|no ?derivatives", "no-derivatives (ND) terms"),
    (r"\bcc[- ]?by[- ]?sa\b|share ?alike", "share-alike (SA) terms: derivatives must keep SA"),
    (r"\b(?:a|l)?gpl", "copyleft (GPL family)"),
    (r"all rights reserved|proprietary", "proprietary terms"),
]
ALIASES = {"apache 2.0": "apache-2.0", "apache-2": "apache-2.0", "cc by 4.0": "cc-by-4.0", "cc0": "cc0-1.0",
           "mit license": "mit", "bsd-3": "bsd-3-clause", "bsd-2": "bsd-2-clause"}
RANK = {"PERMITS-RELEASE": 0, "UNVERIFIED": 1, "BLOCKS": 2}
NC_ONLY = r"^cc[- ]?by[- ]?nc(?:[- ]?4\.0)?$"  # CC BY-NC without ND or SA


def norm(s: Any) -> str | None:
    if s is None:
        return None
    t = str(s).strip().lower()
    if t in ("", "none", "null", "unknown", "other", "[]"):
        return None
    t = t.removeprefix("license:").strip()
    return ALIASES.get(t, t)


def classify(item: dict) -> dict:
    """item: {"kind", "id", "source", "licence_ids": [identifiers from card YAML / tags /
    dataset metadata], "licence_text": optional free text}."""
    ids = sorted({x for x in (norm(v) for v in item.get("licence_ids", [])) if x})
    text = str(item.get("licence_text") or "")
    res = {"kind": item.get("kind"), "id": item.get("id"), "source": item.get("source"), "licence_ids": ids}
    # Datasets: the organizers require datasets to be released under CC-BY-NC 4.0 (prize page, 2027 Grand Prize
    # "Compute and data conditions", quoted in logs/sib/sg/p4kit/Q11.md), so a CC BY-NC dataset (no ND / SA)
    # can be released under those same terms.
    if item.get("kind") == "dataset" and ids and all(re.search(NC_ONLY, i) for i in ids):
        return {**res, "verdict": "PERMITS-RELEASE", "reason": "dataset under CC BY-NC 4.0: release under the same terms",
                "caveat": "not permissively relicensable; the organizers' dataset rule asks for CC-BY-NC 4.0 (Q11.md)"}
    blocks = [why for pat, why in BLOCKING_PATTERNS for i in ids if re.search(pat, i)]
    if blocks:
        return {**res, "verdict": "BLOCKS", "reason": sorted(set(blocks))[0],
                "note": "release under the same terms may be possible; permissive release is not"}
    if not ids:
        return {**res, "verdict": "UNVERIFIED", "reason": "no licence identifier in the public metadata"}
    if len(ids) > 1:
        return {**res, "verdict": "UNVERIFIED", "reason": f"inconsistent licence statements: {ids}"}
    if ids[0] in PERMISSIVE:
        caveat = [why for pat, why in BLOCKING_PATTERNS if re.search(pat, text.lower())]
        out = {**res, "verdict": "PERMITS-RELEASE", "reason": f"permissive licence {ids[0]}"}
        if caveat:
            out["caveat"] = ("the licence text also names non-permissive terms for other material ("
                             + caveat[0] + "); list that material as its own lineage item")
        return out
    return {**res, "verdict": "UNVERIFIED", "reason": f"unrecognised licence {ids[0]}"}


def check(lineage: dict) -> dict:
    items = [classify(i) for i in lineage["items"]]
    overall = max((i["verdict"] for i in items), key=RANK.__getitem__) if items else "UNVERIFIED"
    return {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
            "lineage_id": lineage.get("lineage_id"), "overall": overall, "items": items,
            "status": "pre-submission package item (PRIZE-CHECK-20260925 b); not an SG bar; not legal advice"}


def base_lineage_from_catalogue(root: Path) -> dict:
    """The current base reader's lineage, from the project's catalogue records only."""
    ck = json.loads((root / "data/catalogue/checkpoints.json").read_text())
    kt = json.loads((root / "data/catalogue/known_text.json").read_text())
    base = ck["targets"]["a_ink_9um_hybrid_3d2d_seed42_step075000"]
    tags = base.get("licence_tags") or []
    if isinstance(tags, str):
        tags = re.findall(r"license:[\w.\-]+", tags)
    bucket = kt["sources"]["bucket_licence"]
    labels = ck.get("ink_9um_labels_dataset", {})
    return {"lineage_id": "base ink_9um step-075000 (C2-NT chain)", "items": [
        {"kind": "checkpoint", "id": base["repo"] + "@" + base["commit_sha"], "source": base["url"],
         "licence_ids": [base.get("card_licence")] + list(tags), "licence_text": base.get("licence_text")},
        {"kind": "dataset", "id": "vesuvius-challenge-open-data (CT volumes, segments, labels on S3)",
         "source": bucket["url"] + " sha256 " + bucket["sha256"], "licence_ids": [bucket["text"].split(" (")[0]],
         "licence_text": bucket["text"]},
        {"kind": "dataset", "id": "ink_9um training labels (HF bucket scrollprize/datasets ink_9um)",
         "source": "data/catalogue/checkpoints.json ink_9um_labels_dataset", "licence_ids": [],
         "licence_text": labels.get("licence")},
    ]}


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lineage", help="lineage JSON; default: the base lineage from the catalogue")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    root = Path(__file__).resolve().parents[4]
    lin = json.loads(Path(a.lineage).read_text()) if a.lineage else base_lineage_from_catalogue(root)
    res = check(lin)
    res["lineage_input"] = lin
    Path(a.out).write_text(json.dumps(res, indent=1, sort_keys=True, ensure_ascii=True) + "\n")
    print("overall", res["overall"], {i["id"][:40]: i["verdict"] for i in res["items"]})
    return 0


if __name__ == "__main__":
    sys.exit(main())
