# Provenance: Project HERCULES | owner the owner | [id removed]
"""PHerc. Paris 4 Title Prize variant of the submit-kit (RULES.md DECL-P4-2 item 7):
draft answer sheet and texts for a P4 title-region candidate.  DRAFT ONLY, like generate.py.

Inputs: the P4-B record (numbers and identifiers only), the P4 package manifest (with
``declared_bars``: every bar quoted from DECL-P4-2 / DECL-FACTORY as a JSON number) and
nothing else.  Outputs: answer_sheet.json/.md (one entry per question of the Title Prize
form), methodology.md, fp_mitigation.md, disclosure.md, tp_checklist.md, trace.json.

Guards (tested):
* no title words: the P4 record may not carry reader text.  Any key in FORBIDDEN_KEYS, or
  any string value holding a Greek character, is refused; output holds no Greek character;
* every number comes from a named JSON field (shared Renderer and literal-digit check);
* identity, contact, terms and hosting fields are OWNER-ONLY and empty;
* refuses unless the record's status is EXT-CONFIRMED (only EXT-CONFIRMED counts: DECL-P4-12,
  DECL-P4-14) or the manifest is a DRY RUN; the material (official prediction, raw-CT channel,
  cross-scroll model) selects the ink-map, training-separation and disclosure sentences;
  every file is headed DRAFT (and DRY RUN when it is one); no network or submission code.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import generate as G
import tp_requirements as TPR

DRAFT_P4 = ("DRAFT - NOT SUBMITTED - the owner files (DECL-P4-1); the organizers' papyrologists read the image; "
            "the project names no title words")
FORBIDDEN_KEYS = {"namings", "naming", "letters", "letter", "ch", "chars", "transcription", "text", "reading", "readings",
                  "words", "word", "title", "title_text", "identity", "identities", "boxes"}

FORM_P4 = [  # the Title Prize form (logs/sib/sg/submit_kit/p4_form_questions.json) + its Email field
    {"question": "Email", "owner_only": True},
    {"question": "Your full name", "owner_only": True},
    {"question": "Team name", "owner_only": True},
    {"question": "Additional information as described on https://scrollprize.org/prizes", "owner_only": True,
     "note": "OWNER: host the package (methodology.md, fp_mitigation.md, disclosure.md, both images, cropped mesh, "
             "container) and paste the link here (TP-12)."},
    {"question": "Terms and Conditions", "owner_only": True,
     "note": "Accepting terms (open-sourcing, payment information) is the owner's decision; never ticked by an agent."},
    {"question": "Scan (stated in the hosted document, TP-06)", "owner_only": False,
     "answer": "PHerc. Paris 4 (Scroll 1), volume {{man:scan_volume_id}}, voxel size {{man:voxel_size_um}} um"},
]

METHOD = """## Methodology (TP-09, TP-10, TP-11)

Scan: PHerc. Paris 4 (Scroll 1), volume {{man:scan_volume_id}}, voxel size {{man:voxel_size_um}} um from the volume's metadata.json (TP-06).

{{MATERIAL_METHOD}}

Surface: official mesh {{man:mesh.tifxyz_name}} (sha256 {{man:mesh.sha256}}), cropped by code to the candidate tile plus {{man:mesh.crop_margin_mm}} mm on each side and flattened with {{man:mesh.flattening_method}}; quads whose edges all lie within {{bar:flat1_tol_pct}} % of their three-dimensional lengths: {{man:mesh.flat1_quads_within_tol_pct}} % (declared reporting bar {{bar:flat1_quads_min_pct}} %).

Images (TP-02, TP-03, TP-05): the official prediction over the crop, raw; and a linear {{man:ct_render.window_pct_low}} to {{man:ct_render.window_pct_high}} percentile window slab-mean render of CT volume {{man:ct_render.volume_id}} over the same crop. Both come from the submitted mesh by code, without any annotation of characters or text.

Search: the prediction canvas was cut into tiles of {{bar:tile_mm}} mm; {{p4:phase1.n_tiles_read}} tiles ({{p4:phase1.area_read_cm2}} cm²) were read once each in the census by fresh blind machine readers, and candidates were confirmed by fresh readers in a second phase (DECL-P4-2). Reader key sheet: {{man:reading.key_sheet_variant}} (DECL-P4-2-A2; sha256 {{man:reading.key_sheet_sha256}}).

Reproduction: container {{man:container.image_ref}} (sha256 {{man:container.sha256}}); system requirements: {{man:container.system_requirements}}. Human in the loop: {{man:human_in_loop}}.
"""

FP = """## False-positive mitigation (TP-13, TP-14, TP-15, TP-16)

Null: {{p4:phase1.n0_tiles}} census tiles were shown rotated a quarter turn (null N0). A census tile counted as positive only with rows and at least the larger of {{bar:min_letters}} letters and the N0 {{bar:null_percentile}}th percentile ({{p4:phase1.n0_pctl_letters}} letters).

Confirmation: {{p4:phase2.readers_ge_min}} of {{p4:phase2.n_readers}} fresh readers named at least {{bar:min_letters}} letters on the candidate; the best pair agreed on {{p4:phase2.best_pair_agreed}} same-identity letters within {{bar:consensus_px}} px, against a maximum of {{p4:phase2.n0_max_agreed}} over {{p4:phase2.n_n0_tiles}} second-phase null tiles. Positive control read with rows in every counted session: {{p4:phase2.positive_control_ok}}.

{{MATERIAL_TRAINING}}

Held-out validation (TP-16): {{man:heldout_note}}
"""

DISCLOSURE = """## Disclosure (verbatim)

- The whole search (tiling, blind reading, scoring, mesh cropping, flattening and rendering) was built and run by AI agents for Project HERCULES.
- Letter namings come from blind machine (LLM) readers whose errors are correlated with each other. During the programme the readers were changed to a model whose legibility on this display was not calibrated (DECL-P4-2-A1).
{{MATERIAL_DISCLOSURE}}
- The reads were not sealed against a reference, because no reference exists for this region.
- The project names no title words. It submits an image; the organizers' papyrologists read it (TP-04).
- Area read: {{p4:phase1.area_read_cm2}} cm² in {{p4:phase1.n_tiles_read}} tiles; candidates escalated: {{p4:phase2.n_candidates}}; candidates that did not confirm: {{p4:phase2.n_not_confirmed}}.
- Answer separation was an agent-run procedural control, audited but not enforced by separate machines or people.
- Licence lineage (pre-submission item, not a gate): {{man:licence_lineage.overall}} (record {{man:licence_lineage.record}}).
"""

# Material-dependent sentences (DECL-P4-2 M1; DECL-P4-12 P4-L; DECL-P4-14 P4-O). man:material.kind selects one.
MATERIALS = {
    "official_prediction": {
        "method": "Ink map: the organizers' published prediction of model {{man:prediction_source.model_id}} on volume "
                  "{{man:prediction_source.volume_id}} for segment {{man:segment_id}} (sha256 {{man:prediction_source.sha256}}), "
                  "used exactly as published. No ink model was trained or run by the project.",
        "training": "Training separation (TP-15): the official model was trained on labelled Paris 4 segments; the candidate "
                    "tile's minimum three-dimensional distance to them is {{p4:tile.min_dist_to_labelled_mm}} mm (tiles closer "
                    "than {{bar:labelled_adjacent_mm}} mm were excluded by declaration).",
        "disclosure": "- The ink maps are the organizers' official model output, not the project's.",
    },
    "raw_ct_channel": {
        "method": "Ink channel: a model-free thin-slab maximum of the CT surface volume {{man:material.volume_id}} around the "
                  "official mesh of segment {{man:segment_id}} (DECL-P4-12; thresholds frozen from the known-text control "
                  "before any tile), display variant {{man:material.variant}} (DECL-P4-12-A2, DECL-P4-12-A3; parameters in "
                  "{{man:material.parameters_record}}). No ink model was trained or applied.",
        "training": "Training separation (TP-15): no trained model produced this image, so no ink-model output overlaps "
                    "training data. The labelled-adjacency flag is reported as declared (DECL-P4-12): minimum "
                    "three-dimensional distance to the labelled segments {{p4:tile.min_dist_to_labelled_mm}} mm.",
        "disclosure": "- The image channel applies no trained model; it is a thresholded view of the CT itself. Several "
                      "displays of the same volume were read, each as its own material with its own gate and "
                      "null; this multiplicity is disclosed.",
    },
    "cross_scroll_model": {
        "method": "Ink map: checkpoint {{man:material.checkpoint_id}} (sha256 {{man:material.checkpoint_sha256}}), whose "
                  "documented training data contain no PHerc. Paris 4 segment or label (provenance record "
                  "{{man:material.provenance_record}}; DECL-P4-14 and its provenance records in RULES.md), iteration "
                  "{{man:material.iteration}} of its model family, run on segment {{man:segment_id}}. No model was "
                  "trained by the project.",
        "training": "Training separation (TP-15): the checkpoint's documented training data contain no Paris 4 data, so "
                    "its outputs here overlap no training data (DECL-P4-14; provenance {{man:material.provenance_record}}). "
                    "Labelled-adjacency is reported, not excluded: {{p4:tile.min_dist_to_labelled_mm}} mm.",
        "disclosure": "- The ink map comes from a third-party public checkpoint run by the project; its training-data "
                      "statement is quoted in the provenance record. Several iterations of the same model family were "
                      "read, each as its own material with its own gate and null; these highly correlated materials "
                      "are disclosed (DECL-P4-14-A1).",
    },
}
ACCEPTED_STATUS = ("EXT-CONFIRMED",)  # DECL-P4-12 item 4, DECL-P4-14 item 4: "Only EXT-CONFIRMED counts"

CHECK_HEAD = "## TP-01..TP-22 checklist (PHerc. Paris 4 Title Prize, with package items PKG)\n\n| id | requirement | answered by | status |\n|---|---|---|---|\n"
TEMPLATES = {"method": METHOD, "fp": FP, "disclosure": DISCLOSURE, "check_head": CHECK_HEAD, "draft": DRAFT_P4}

MANIFEST_FIELDS = {"manifest.meshes": "mesh.tifxyz_name", "manifest.flattening": "mesh.flattening_method",
                   "manifest.image": "images.prediction_file", "manifest.context_image": "images.context_file",
                   "manifest.scale_bar": "images.scale_bar_1cm", "letter_dimensions table": "images.letter_dimensions",
                   "manifest.image_name_check": "images.named_after_mesh", "manifest.container": "container.image_ref"}
SECTIONS = {"methodology": "methodology.md", "fp_mitigation": "fp_mitigation.md", "disclosure": "disclosure.md",
            "sheet": "answer_sheet.md"}


def _no_reader_text(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in FORBIDDEN_KEYS:
                raise G.Refused(f"P4 record field {path}/{k} could carry reader text; the kit takes numbers and ids only")
            _no_reader_text(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _no_reader_text(v, f"{path}[{i}]")
    elif isinstance(obj, str) and any("GREEK" in unicodedata.name(c, "") for c in obj):
        raise G.Refused(f"P4 record value at {path} holds Greek characters; the kit never writes letters")


def tp_status(by: str, files: dict, p4: dict, man: dict, bars: dict) -> str:
    if by.startswith("owner"):
        return "OWNER"
    status = "DRAFTED"
    for part in (x.strip() for x in by.split("+")):
        if part == "training_overlap":
            d, lim = G.resolve_or(p4, "tile.min_dist_to_labelled_mm"), bars.get("labelled_adjacent_mm")
            if d is None or lim is None:
                status = "MISSING DATA"
            elif d < lim:
                return "NOT MET"
        elif part == "heldout_table":
            if not man.get("heldout"):
                status = "MISSING DATA"
        elif part in SECTIONS:
            if "[MISSING:" in files[SECTIONS[part]]:
                status = "MISSING DATA"
        elif part == "sheet.scan":
            if "[MISSING:" in files["answer_sheet.md"]:
                status = "MISSING DATA"
        elif part in MANIFEST_FIELDS:
            v = G.resolve_or(man, MANIFEST_FIELDS[part])
            if v is None or v == []:
                status = "MISSING DATA"
            elif v is False:
                return "NOT MET"
    return status


def generate(p4: dict, man: dict, out_dir: str | Path) -> dict:
    dry = man.get("dry_run") is True
    if p4.get("status") not in ACCEPTED_STATUS and not dry:
        raise G.Refused("the P4 record is not EXT-CONFIRMED and the manifest is not a DRY RUN: nothing is generated")
    _no_reader_text(p4)
    kind = G.resolve_or(man, "material.kind")
    if kind not in MATERIALS:
        raise G.Refused(f"unknown or missing material.kind {kind!r}; one of {sorted(MATERIALS)} is required")
    mat = MATERIALS[kind]
    for name, t in list(TEMPLATES.items()) + [(f"material.{k}", v) for m in MATERIALS.values() for k, v in m.items()]:
        assert G._digits_ok(t), f"template {name} holds a literal number"
    bars = man.get("declared_bars") or {}
    r = G.Renderer({}, man, bars, p4)
    head = f"{G.PROVENANCE}\n\n{DRAFT_P4}\n" + (f"{G.DRY}\n" if dry else "") + "\n"
    files = {}
    sheet = []
    for q in FORM_P4:
        e = {"question": q["question"], "owner_only": q["owner_only"]}
        if q["owner_only"]:
            e.update(answer="", status=G.OWNER_ONLY)
            if "note" in q:
                e["note"] = q["note"]
        else:
            e["answer"] = r(q["answer"])
            e["status"] = "FILLED FROM DATA" if "[MISSING:" not in e["answer"] else "MISSING DATA"
        sheet.append(e)
    files["answer_sheet.json"] = json.dumps({"provenance": G.PROVENANCE, "header": DRAFT_P4, "dry_run": dry,
                                             "entries": sheet}, indent=1, ensure_ascii=True) + "\n"
    md = head + "## Answer sheet (PHerc. Paris 4 Title Prize form)\n\n"
    for e in sheet:
        md += f"### {e['question']}\n\n{e['answer'] or '(empty)'}\n\nStatus: {e['status']}\n"
        md += (f"\nNote: {e['note']}\n" if e.get("note") else "") + "\n"
    files["answer_sheet.md"] = md
    files["methodology.md"] = head + r(METHOD.replace("{{MATERIAL_METHOD}}", mat["method"]))
    files["fp_mitigation.md"] = head + r(FP.replace("{{MATERIAL_TRAINING}}", mat["training"]))
    files["disclosure.md"] = head + r(DISCLOSURE.replace("{{MATERIAL_DISCLOSURE}}", mat["disclosure"]))
    tp = [{"id": tid, "requirement": req, "answered_by": by, "status": tp_status(by, files, p4, man, bars)}
          for tid, req, _q, by in TPR.TP]
    tp += [row for row in G.pkg_rows(man) if row["id"] == "PKG-01"]  # PKG-02 (SG 11) and PKG-03 do not apply to P4
    files["tp_checklist.md"] = head + CHECK_HEAD + "".join(
        f"| {f['id']} | {f['requirement']} | {f['answered_by']} | {f['status']} |\n" for f in tp)
    trace = {"provenance": G.PROVENANCE, "dry_run": dry, "p4_status": p4.get("status"), "used_fields": r.used,
             "missing_fields": sorted(set(r.missing)), "tp": tp, "tp_page_sha256": TPR.PAGE_SHA256}
    files["trace.json"] = json.dumps(trace, indent=1, ensure_ascii=True, default=str) + "\n"
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        if any("GREEK" in unicodedata.name(c, "") for c in text):
            raise ValueError(f"Greek character in {name}: the kit never writes letters")
        (out / name).write_text(G._clean(text), encoding="utf-8")
    return trace


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Draft-only Paris 4 Title Prize text generator")
    ap.add_argument("--p4", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))  # noqa: E731
    try:
        t = generate(load(a.p4), load(a.manifest), a.out)
    except G.Refused as e:
        print(f"refused: {e}")
        return 3
    print(f"draft written to {a.out}; missing fields: {len(t['missing_fields'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
