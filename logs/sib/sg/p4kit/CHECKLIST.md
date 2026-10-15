Provenance: Project HERCULES | owner the owner | [id removed]

# PHerc. Paris 4 Title Prize: submission-readiness checklist

The kit is `tools/sib/sg/submit_kit/p4_generate.py` (sha256 1e7485910e74b60b...). It is a **draft only**: no code opens, fills or submits the form.

**Gate.** A real (non-DRY) draft is produced only for an **EXT-CONFIRMED** record ("Only EXT-CONFIRMED counts": DECL-P4-12 item 4, DECL-P4-14 item 4). The material (`official_prediction` | `raw_ct_channel` | `cross_scroll_model`) selects truthful ink-map, training and disclosure sentences. Any other material is refused. The kit writes no title words and refuses any reader-text field.

**Filing within the hour after an EXT-CONFIRMED lead:**
1. Builders drop the manifest fields below.
2. Run: `PYTHONPATH=tools/sib/sg/submit_kit python tools/sib/sg/submit_kit/p4_generate.py --p4 <ext_record.json> --manifest <p4_manifest.json> --out <dir>`
3. The owner hosts the package, fills the OWNER-ONLY fields and files.

Every number comes from a named JSON field. A missing field prints `[MISSING: ...]` and the TP checklist shows MISSING DATA.

Requirements are quoted verbatim in `tools/sib/sg/submit_kit/tp_requirements.py`, tested against the live page (TP-01..TP-22). They agree with the p4-research DOSSIER section 3.1 (origin/claude/gifted-bell-gavnl5-sib-p4-research b2127d1).

| # | Requirement (TP) | Kit field or text | Evidence path / producer | Status now |
|---|---|---|---|---|
| 1 | tifxyz mesh of the region, with low-distortion flattening (TP-01) | `man:mesh.{tifxyz_name, sha256, crop_margin_mm, flattening_method, flat1_quads_within_tol_pct}`, bar `declared_bars.flat1_quads_min_pct` | flat1: `tools/sib/flat1/p4_package.py` (branch sib-flat1 9f14b53; DECL-P4-2 item 7: crop tile +-1 cm, vc_flatten, % within +-5 % vs 93.1). Window A is being prepared by flat1 | PENDING: flat1 window A. Use the official S3 mesh, never an EduceLab mesh (Q11) |
| 2 | Programmatic image from CT + mesh, no manual annotation; ink predictions in spatial context (TP-02, TP-03, TP-05) | `man:images.{prediction_file, context_file}`, `man:ct_render.*`, `man:material.kind` | Image by the lead's channel builder (M1 official prediction; P4-L p4-l2 raw-CT channel; P4-O ckpt-screen), plus the linear 1-99 % slab-mean CT render of DECL-P4-2 item 7 over the same crop | PENDING: the lead's builder |
| 3 | Scan named (TP-06) | answer-sheet entry "Scan" from `man:scan_volume_id`, `man:voxel_size_um` (metadata.json) | kit, auto-filled | READY (fills from data) |
| 4 | 1 cm scale bar; pixel and mm dimensions of representative letters (TP-07) | `man:images.scale_bar_1cm` (bool), `man:images.letter_dimensions` [{px_w, px_h, mm_w, mm_h}] | Image builder draws the bar programmatically (px/mm = 1000 / voxel_um x render scale, never assumed). Dimensions are numbers only from box sizes; no identities | PENDING: image builder |
| 5 | Image named after the tifxyz mesh (TP-08) | `man:images.named_after_mesh` (bool; false gives NOT MET) | image builder | PENDING: image builder |
| 6 | Docker, or instructions plus a video (TP-10, TP-11) | `man:container.{image_ref, sha256, system_requirements}`, `man:human_in_loop`; methodology text | The pipeline is automated (no human-in-the-loop video needed if `human_in_loop` says none). A container ref or written instructions is still needed | PENDING: container or instructions (owner or orchestrator to assign) |
| 7 | False-positive mitigation; held-out validation (TP-13, TP-14, TP-16) | FP section from `p4:phase1.*`, `p4:phase2.*` (N0 null, agreement, positive control), `man:heldout`, `man:heldout_note` | tribunal sibling (branch sib-tribunal 6a03e62, REAL-TRIB-2) is building the controls. The known-text gate (DECL-P4-12 item 2, DECL-P4-14 item 3) is the built-in validation | PENDING: tribunal. TP-16 prints MISSING DATA until `man:heldout` has rows |
| 8 | No training-data overlap (TP-05, TP-15) | material-dependent sentence + `p4:tile.min_dist_to_labelled_mm`, `man:material.provenance_record` | M1: exclusion < 1.2 mm (DECL-P4-2). P4-L: model-free, flag reported (DECL-P4-12 item 3). P4-O: documented no-Paris-4 training (DECL-P4-14; provenance.json per checkpoint) | READY in the kit; data PENDING per lead |
| 9 | Embargo: nothing public before the official announcement (TP-20) | disclosure + OWNER status | Q11.md (MUST NOT). Branches stay private; no public post | OWNER (standing rule) |
| - | Form fields: Email, name, team, additional-information link (TP-12), Terms | OWNER-ONLY, empty | `logs/sib/sg/submit_kit/p4_form_questions.json` | OWNER-ONLY, never filled by an agent |
| - | Licence (Q11) | PKG-01 row in the TP checklist | `logs/sib/sg/p4kit/Q11.md`: code permissive after winning; derived images CC BY-NC after announcement; EduceLab meshes never redistributed | RESOLVED |

## Channel-specific evidence (added 2026-09-26T21:4xZ; sibling commits as fetched)

Set the manifest's `material.kind` and fields from the channel that produced the EXT-CONFIRMED lead. The kit then writes that channel's training-separation and multiplicity sentences.

| Channel | Declarations | `material.kind` and fields | Training overlap | Evidence paths (branch commit) |
|---|---|---|---|---|
| P4-L (L2): thin-slab maximum around the official mesh | DECL-P4-12, -A1; result P4-L2-CENSUS-RESULT | `raw_ct_channel`; `variant` = "L2", `volume_id`, `parameters_record` = the frozen thresholds record | **None by construction.** No trained model is applied, and the labelled-adjacency flag is reported, not excluded (DECL-P4-12 item 3) | sib-p4-l2 (0446be9): `logs/sib/p4-l2/STATUS.md`, `logs/sib/p4-l2/*`; harness rh-e2 (batches l2 / nl2 / census_l2) |
| P4-L2S: same channel, per-tile 1-99 % stretch | DECL-P4-12-A2 | `raw_ct_channel`; `variant` = "L2S" | **None by construction** (model-free) | sib-p4-l2 (0446be9): `logs/sib/p4-l2/l2s/census_w*.jsonl` |
| P4-L3: depth-calibrated thin slab at d* | DECL-P4-12-A3 | `raw_ct_channel`; `variant` = "L3", `parameters_record` = the frozen d* record | **None by construction** (model-free). d* was calibrated only on the control strip w028-037 | sib-p4-depth (c39d977): `logs/sib/p4-depth/calib_params.json`, `unit_tests.json`, `STATUS.md` |
| P4-O: PHerc.1667 cross-scroll models (6 eligible iterations) | DECL-P4-14, -A1; RULES.md P4-O-PROVENANCE, P4-O-PROVENANCE-2 | `cross_scroll_model`; `checkpoint_id`, `checkpoint_sha256`, `iteration`, `provenance_record` | **None by documented provenance.** The quoted model cards list training segments of PHerc0009B, PHerc0343P and PHerc0500P2 only, and `paris4_scroll1_in_documentation = false`. Labelled adjacency is reported, not excluded (DECL-P4-14 item 4) | sib-ckpt-screen-b (ca732ae): `logs/sib/ckpt-screen-b/p4o/provenance.json` (1667 family, eligible). Screens a (90e7afb) and c (dbfeae5): `logs/sib/ckpt-screen-{a,c}/p4o/provenance.json` (0 eligible). Tribunal copy: `logs/sib/tribunal/p4val/p4o_inputs/provenance_a.json` |
| M1: official prediction | DECL-P4-2 | `official_prediction` | Exclusion below 1.2 mm to the 8 labelled segments (DECL-P4-2) | as in rows 1-2 above |

Package evidence as it lands:

| Item | Path (branch commit) | Status |
|---|---|---|
| Flattening of the candidate window (TP-01) | sib-flat1 (b6e1443): `tools/sib/flat1/p4win.py`, `logs/sib/flat1/p4win/metrics.json`; `tools/sib/flat1/p4_package.py` (crop +-1 cm, vc_flatten, % within +-5 % vs 93.1) | LANDED (the tool and window metrics). Copy `flat1_quads_within_tol_pct` into `man:mesh` for the lead's window |
| Orientation (text upright, unmirrored) | sib-handed: `p4orient.json` | **NOT YET LANDED** (sib-handed at a0fa2d1 has no p4orient file). Needed before filing; add it to `man:images` / the methodology when it lands |
| Held-out validation (TP-16) | sib-tribunal (47e4f06): `logs/sib/tribunal/p4val/PLAN.md`, `known_text_map.json`, `census_a_summary.json`, `l2_manifest_3f0dcfc.json` | IN PROGRESS. Fill `man:heldout` from its results; TP-16 prints MISSING DATA until then |

Multiplicity is disclosed by the kit for every channel: several displays of one volume (L2, L2S, L3), and up to six correlated PHerc.1667 iterations. Each is its own material with its own gate and N0, and there is no pooling.

**DRY RUN proof.** `logs/sib/sg/submit_kit/dryrun_p4_output/` was generated from an EXT-CONFIRMED synthetic record with 0 missing fields. 31 kit tests pass, including one per material, the EXT-CONFIRMED gate, the reader-text and Greek refusals, and the no-network check.

Integrity: no issues. No image, map, CT or EXPECTED-TEXT content was viewed or read; only DOSSIER section 3.1 was read. No credential, payment or ID field was filled. No title words were written.
