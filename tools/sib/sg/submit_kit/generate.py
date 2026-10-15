# Provenance: Project HERCULES | owner the owner | [id removed]
"""Truthful submission-text generator (DRAFT ONLY).

Takes an SG record (hercules.sg.gate.sg_check output), the package manifest and the SG
constants (logs/sib/sg/sg_report.json "constants") and writes, into an output directory:
answer_sheet.json/.md (one entry per form question), methodology.md, fp_mitigation.md
(FL-14/FL-24/FL-25), heldout_table.md (FL-15), disclosure.md, fl_checklist.md and
trace.json.

Rules enforced here and by the tests:
* Every number in the output comes from a named JSON field through a placeholder
  ``{{sg:...}}``, ``{{man:...}}`` or ``{{bar:...}}``; template literal text holds no digits
  except rule identifiers (FL-NN, SG N, K7, DECL names).  An unresolvable field renders as
  ``[MISSING: <source>:<path>]`` and is listed; nothing is invented.
* Identity, contact, payment, tax, credential and terms-acceptance fields are left EMPTY
  and marked OWNER-ONLY.  The hosting link is OWNER-ONLY.
* Output is a draft: every file starts with the provenance line and the header
  "DRAFT - NOT SUBMITTED - K7: no form unless SG 0-14 all pass and the owner is present".
  This module contains no network, browser or form-submission code (tested).
* It refuses unless the SG record's overall is PASS, or the manifest is a DRY RUN; a DRY
  RUN is stamped on every file.
* No model names or identifiers of AI systems are written; no invisible characters.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

PROVENANCE = "Provenance: Project HERCULES | owner the owner | [id removed]"
DRAFT = "DRAFT - NOT SUBMITTED - K7: no form unless SG 0-14 all pass and the owner is present"
DRY = "DRY RUN - NOT A CANDIDATE - NOT FOR SUBMISSION"
OWNER_ONLY = "OWNER-ONLY (left empty by design; never filled by an agent)"
PH = re.compile(r"\{\{(sg|man|bar|p4):([A-Za-z0-9_.+\-]+)\}\}")


class Refused(Exception):
    pass


def resolve(src: dict, path: str) -> Any:
    cur: Any = src
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            raise KeyError(path)
    return cur


def fmt(v: Any) -> str:
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.4g}"
    if isinstance(v, list):
        return ", ".join(fmt(x) for x in v) if v else "none"
    if v is None:
        return "none"
    return str(v)


class Renderer:
    def __init__(self, sg: dict, man: dict, bar: dict, p4: dict | None = None):
        self.src = {"sg": sg, "man": man, "bar": bar, "p4": p4 or {}}
        self.used: list[dict] = []
        self.missing: list[str] = []

    def __call__(self, template: str) -> str:
        def sub(m):
            ref = f"{m.group(1)}:{m.group(2)}"
            try:
                v = resolve(self.src[m.group(1)], m.group(2))
            except KeyError:
                self.missing.append(ref)
                return f"[MISSING: {ref}]"
            self.used.append({"ref": ref, "value": v if isinstance(v, (int, float, str, bool)) or v is None else fmt(v)})
            return fmt(v)
        return PH.sub(sub, template)


# ------------------------------------------------------------------ templates (no literal numbers)

FORM = [  # one entry per question of the official form (logs/sib/sg/submit_kit/form_questions.json)
    {"question": "Email", "owner_only": True},
    {"question": "Your full name", "owner_only": True},
    {"question": "Team name", "owner_only": True},
    {"question": "Scroll / Volume with evidence of letters", "owner_only": False,
     "answer": "{{man:scroll}} / volume {{man:volume_id}}"},
    {"question": "Additional information as described on https://scrollprize.org/prizes", "owner_only": True,
     "note": "OWNER: host the package (methodology.md, fp_mitigation.md, heldout_table.md, disclosure.md, image, "
             "meshes, container) and paste the link here (FL-19)."},
    {"question": "Terms and Conditions", "owner_only": True,
     "note": "Accepting terms (open-sourcing, payment information) is the owner's decision; never ticked by an agent."},
]

METHODOLOGY = """## Methodology (FL-16, FL-17, FL-18)

Scroll {{man:scroll}}, volume {{man:volume_id}}, voxel size {{man:voxel_size_um}} um (from the volume's metadata.json).

Surface. Mesh {{man:mesh.tifxyz_name}} (sha256 {{man:mesh.sha256}}), flattened by {{man:mesh.flattening_method}}; quads within the declared edge-length tolerance of their three-dimensional lengths on the region's own flattening: {{man:mesh.flat1_quads_within_tol_pct}} %.

Ink signal. Model {{man:ink_model.name}} (checkpoint sha256 {{man:ink_model.checkpoint_sha256}}); trained on this scroll: {{man:ink_model.trained_on_this_scroll}}; training scrolls: {{man:ink_model.training_scrolls}}.

Reading. Letters were named by blind machine readers under a declared display and prompt, and scored by deterministic code (SG version {{sg:sg_version}}, input hash {{sg:inputs_sha256}}). The region R ({{sg:R.area_cm2}} cm², aspect {{sg:R.aspect}}) was computed by code from the discovery namings and declared before confirmation reads (record {{sg:R.declared_record}}).

Reproduction. Container {{man:container.image_ref}} (sha256 {{man:container.sha256}}); system requirements: {{man:container.system_requirements}}. Human in the loop: {{man:human_in_loop}}.

Open source (FL-04): {{man:open_source_plan}}.
"""

FP = """## False-positive mitigation (FL-14, FL-24, FL-25)

Agreement: {{sg:items.1.a.agreed}} letters of the same identity named within {{bar:CONSENSUS_RADIUS_PX}} px by at least {{bar:MIN_READERS_AGREE}} of {{bar:N_READERS}} fresh blind readers; {{sg:items.1.b.firm_2readers}} firm for at least two readers.

Empirical null: {{sg:items.1.c.n_null}} matched null tiles; their {{bar:SG1C_PERCENTILE}}th percentile of agreed counts is {{sg:items.1.c.p99}} and their maximum {{sg:items.1.c.null_max}} (margin {{sg:items.1.c.margin}}).

Identity shuffle between readers: p = {{sg:items.1.d.p.exact}} against a bar of {{sg:items.1.d.alpha.exact}} (m = {{sg:items.1.d.m}} candidates escalated on this scroll).

Opposite order: {{sg:items.3.namings_in_R}} namings in R. Slice re-reads: {{sg:items.4.per_offset.-1.fraction}} and {{sg:items.4.per_offset.+1.fraction}} re-confirmed. Second lineage: {{sg:items.5.fraction}}. Independent re-trace (overlap {{sg:items.6.overlap_fraction}}): {{sg:items.6.fraction}}. Render rotation: {{sg:items.14.rotation.fraction}}.

Copy test against every training-label patch at every rotation step: maximum |NCC| {{sg:items.7.max_abs_ncc}} (bar {{bar:SG7_NCC_MAX}}); crops evaluable at n_eff at least {{bar:SG7_NEFF_MIN}} (minimum observed {{sg:items.7.n_eff_min}}); copy-test null on the real patch set: {{sg:items.7.copy_test_null.status}} ({{sg:items.7.copy_test_null.false_flags}} false flags on {{sg:items.7.copy_test_null.n_null_tiles}} tiles).

Training and prediction separation (FL-09, FL-25): certificate record {{sg:items.8.record}}. Held-out letters on a different region (FL-24): see the held-out table.

Reader freshness: {{sg:readers_fresh.status}} ({{sg:readers_fresh.n_readers}} readers over {{sg:readers_fresh.n_reads}} reads). Reader model mix: {{sg:model_mix.status}}.
"""

HELDOUT_HEAD = """## Held-out validation (FL-15)

| benchmark | scroll | windows | sealed letters | metric | value | REF ceiling | p |
|---|---|---|---|---|---|---|---|
"""
HELDOUT_ROW = ("| {{man:heldout.I.benchmark}} | {{man:heldout.I.scroll}} | {{man:heldout.I.n_windows}} | "
               "{{man:heldout.I.n_sealed_letters}} | {{man:heldout.I.metric}} | {{man:heldout.I.value}} | "
               "{{man:heldout.I.ref_ceiling}} | {{man:heldout.I.p}} |\n")

DISCLOSURE = """## Disclosure (verbatim)

- The whole pipeline (surface tracing, rendering, ink detection, blind reading, scoring and gating) was built and run by AI agents for Project HERCULES.
- Letter namings come from blind machine (LLM) readers whose errors are correlated with each other. The transcription is a machine proposal, not a papyrological reading.
- Area read on this scroll: {{man:reading.area_read_cm2}} cm² in {{man:reading.tiles_read}} tiles; candidates escalated: {{man:reading.candidates_escalated}}; candidates that failed the gate: {{man:reading.candidates_failed}}.
- Rescans used: {{man:rescans_used}}. Training on this scroll: {{man:ink_model.trained_on_this_scroll}}.
- Mesh trimming: {{man:mesh.trimming}}. Mirroring applied: {{man:mesh.mirrored}} (handedness record {{sg:items.12.record}}).
- Seal separation (answers hidden from readers and from the building agents) was an agent-run procedural control, audited but not enforced by separate machines or people.
- Licence lineage of the reader (checkpoints and datasets; pre-submission item, not a gate): {{man:licence_lineage.overall}} (record {{man:licence_lineage.record}}).
"""

CHECK_HEAD = "## FL-01..FL-25 checklist (with package items PKG)\n\n| id | requirement | answered by | status |\n|---|---|---|---|\n"


SECTIONS = {"sheet": "answer_sheet.md", "methodology": "methodology.md", "fp_mitigation": "fp_mitigation.md",
            "heldout_table": "heldout_table.md", "disclosure": "disclosure.md"}
MANIFEST_FIELDS = {"manifest.meshes": "mesh.tifxyz_name", "manifest.flattening": "mesh.flattening_method",
                   "manifest.image": "image.file", "manifest.scale_bar": "image.scale_bar_1cm",
                   "manifest.image_name_check": "image.named_after_mesh", "manifest.row_annotation": "image.rows_annotated",
                   "manifest.container": "container.image_ref", "letter_dimensions table": "image.letter_dimensions"}


def fl_status(by: str, files: dict, sg: dict, man: dict) -> str:
    """OWNER / DRAFTED / MISSING DATA / NOT MET for one FL requirement."""
    if by.startswith("owner"):
        return "OWNER"
    parts = [p.strip() for p in re.split(r"\+", by)]
    status = "DRAFTED"
    for part in parts:
        key = part.split(".")[0] if not part.startswith("manifest.") else part
        if part == "results table":
            ok = resolve_or(sg, "items.1.a.status") == "PASS"
            status = status if ok else "NOT MET"
        elif part.startswith("FL-09 certificate"):
            rec = resolve_or(sg, "items.8.record")
            status = status if rec else "MISSING DATA"
        elif key in SECTIONS:
            if "[MISSING:" in files[SECTIONS[key]]:
                status = "MISSING DATA"
        elif part in MANIFEST_FIELDS:
            v = resolve_or(man, MANIFEST_FIELDS[part])
            if v is None or v == []:
                status = "MISSING DATA"
            elif v is False:
                return "NOT MET"
    return status


LINEAGE_STATUS = {"PERMITS-RELEASE": "DRAFTED", "BLOCKS": "BLOCKED (owner decision)", "UNVERIFIED": "UNVERIFIED"}


def pkg_rows(man: dict) -> list[dict]:
    """Package items that are not FL requirements (sg-pkg2 part 4): draft fields only."""
    lin = resolve_or(man, "licence_lineage.overall")
    ref = resolve_or(man, "sg11_refcal.record")
    return [
        {"id": "PKG-01", "requirement": "Licence lineage permits release of code, data and weights (PRIZE-CHECK-20260925 b)",
         "answered_by": "man:licence_lineage (tools/sib/sg/licence/lineage.py)",
         "status": LINEAGE_STATUS.get(lin, "MISSING DATA")},
        {"id": "PKG-02", "requirement": "SG 11 known-text pass rate recorded (DECL-SG11-REFCAL-1, proposed)",
         "answered_by": "man:sg11_refcal.record (hercules.sg.refcal)", "status": "DRAFTED" if ref else "MISSING DATA"},
        {"id": "PKG-03", "requirement": "PHerc. Paris 4 Title Prize variant (DECL-P4-2 item 7)",
         "answered_by": "tools/sib/sg/submit_kit/p4_generate.py", "status": "SEPARATE KIT (not part of a First Letters filing)"},
    ]


def resolve_or(src: dict, path: str) -> Any:
    try:
        return resolve(src, path)
    except KeyError:
        return None


def _digits_ok(template: str) -> bool:
    """Template literal text (placeholders removed) holds no digits except rule identifiers."""
    lit = PH.sub("", template)
    lit = re.sub(r"SG \d{1,2}-\d{1,2}|(?:FL|TP|PKG)-\d{2}|SG \d{1,2}|\bK7\b|\bsha256\b|\bDECL-[A-Z0-9-]*[A-Z0-9]"
                 r"|Paris 4|Scroll 1|\bN0\b", "", lit)
    return not re.search(r"\d", lit)


TEMPLATES = {"methodology": METHODOLOGY, "fp": FP, "heldout_head": HELDOUT_HEAD, "heldout_row": HELDOUT_ROW,
             "disclosure": DISCLOSURE, "check_head": CHECK_HEAD, "draft": DRAFT, "dry": DRY}


def _clean(text: str) -> str:
    bad = [c for c in text if unicodedata.category(c) == "Cf"]
    if bad:
        raise ValueError("invisible (Cf) character in output")
    return text


def generate(sg: dict, man: dict, bar: dict, out_dir: str | Path) -> dict:
    """Write the draft files; returns the trace (used fields, missing fields, FL status)."""
    dry = man.get("dry_run") is True
    if sg.get("overall") != "PASS" and not dry:
        raise Refused("SG record is not an overall PASS and the manifest is not a DRY RUN: nothing is generated")
    for name, t in TEMPLATES.items():
        assert _digits_ok(t), f"template {name} holds a literal number"
    import fl_requirements as FLR

    r = Renderer(sg, man, bar)
    head = f"{PROVENANCE}\n\n{DRAFT}\n" + (f"{DRY}\n" if dry else "") + "\n"
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    # answer sheet
    sheet = []
    for q in FORM:
        e = {"question": q["question"], "owner_only": q["owner_only"]}
        if q["owner_only"]:
            e["answer"] = ""
            e["status"] = OWNER_ONLY
            if "note" in q:
                e["note"] = q["note"]
        else:
            e["answer"] = r(q["answer"])
            e["status"] = "FILLED FROM DATA" if "[MISSING:" not in e["answer"] else "MISSING DATA"
        sheet.append(e)
    files["answer_sheet.json"] = json.dumps({"provenance": PROVENANCE, "header": DRAFT, "dry_run": dry, "entries": sheet},
                                            indent=1, ensure_ascii=True) + "\n"
    md = head + "## Answer sheet (one entry per form question)\n\n"
    for e in sheet:
        md += f"### {e['question']}\n\n{e['answer'] if e['answer'] else '(empty)'}\n\nStatus: {e['status']}\n"
        md += (f"\nNote: {e['note']}\n" if e.get("note") else "") + "\n"
    files["answer_sheet.md"] = md
    files["methodology.md"] = head + r(METHODOLOGY)
    files["fp_mitigation.md"] = head + r(FP)
    rows = ""
    for i in range(len(man.get("heldout", []))):
        rows += r(HELDOUT_ROW.replace(".I.", f".{i}."))
    if not rows:
        r.missing.append("man:heldout")
        rows = "| [MISSING: man:heldout] | | | | | | | |\n"
    files["heldout_table.md"] = head + HELDOUT_HEAD + rows
    files["disclosure.md"] = head + r(DISCLOSURE)
    # FL checklist: each requirement's status from the data it depends on
    fl = []
    for fid, req, _q, by in FLR.FL:
        st = fl_status(by, files, sg, man)
        fl.append({"id": fid, "requirement": req, "answered_by": by, "status": st})
    fl += pkg_rows(man)
    files["fl_checklist.md"] = head + CHECK_HEAD + "".join(
        f"| {f['id']} | {f['requirement']} | {f['answered_by']} | {f['status']} |\n" for f in fl)
    trace = {"provenance": PROVENANCE, "dry_run": dry, "sg_overall": sg.get("overall"), "used_fields": r.used,
             "missing_fields": sorted(set(r.missing)), "fl": fl, "fl_page_sha256": FLR.PAGE_SHA256}
    files["trace.json"] = json.dumps(trace, indent=1, ensure_ascii=True, default=str) + "\n"
    for name, text in files.items():
        (out / name).write_text(_clean(text), encoding="utf-8")
    return trace


def main(argv=None) -> int:
    import argparse
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    ap = argparse.ArgumentParser(description="Draft-only submission text generator")
    ap.add_argument("--sg", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--constants", required=True, help="JSON with the SG constants (sg_report.json 'constants')")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))  # noqa: E731
    bar = load(a.constants)
    bar = bar.get("constants", bar)
    try:
        t = generate(load(a.sg), load(a.manifest), bar, a.out)
    except Refused as e:
        print(f"refused: {e}")
        return 3
    print(f"draft written to {a.out}; missing fields: {len(t['missing_fields'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
