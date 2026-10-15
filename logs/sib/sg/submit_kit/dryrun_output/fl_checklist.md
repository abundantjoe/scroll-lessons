Provenance: Project HERCULES | owner the owner | [id removed]

DRAFT - NOT SUBMITTED - K7: no form unless SG 0-14 all pass and the owner is present
DRY RUN - NOT A CANDIDATE - NOT FOR SUBMISSION

## FL-01..FL-25 checklist (with package items PKG)

| id | requirement | answered by | status |
|---|---|---|---|
| FL-01 | Eligible volume | sheet.scroll_volume | DRAFTED |
| FL-02 | Deadline | owner (filing date) | OWNER |
| FL-03 | 10 letters in one 4 cm2 area | results table | DRAFTED |
| FL-04 | Open-source code, data, model weights and results after winning | methodology.open_source | DRAFTED |
| FL-05 | Mesh in tifxyz | manifest.meshes | DRAFTED |
| FL-06 | Low-distortion isometric flattening included | manifest.flattening | DRAFTED |
| FL-07 | Unwrapped image with >= 10 legible letters in 4 cm2 | manifest.image | DRAFTED |
| FL-08 | Single static image | manifest.image | DRAFTED |
| FL-09 | Programmatic image; no manual annotation; no training overlap | disclosure + FL-09 certificate | DRAFTED |
| FL-10 | Name the scroll; one submission per scroll | sheet.scroll_volume | DRAFTED |
| FL-11 | Scale bar and letter dimensions | manifest.scale_bar + letter_dimensions table | DRAFTED |
| FL-12 | Image named after the tifxyz mesh | manifest.image_name_check | DRAFTED |
| FL-13 | Annotate rows without obscuring letters | manifest.row_annotation | DRAFTED |
| FL-14 | False-positive mitigation | fp_mitigation | DRAFTED |
| FL-15 | Held-out validation with known ground truth | heldout_table | DRAFTED |
| FL-16 | Detailed, reproducible methodology | methodology | DRAFTED |
| FL-17 | Docker image and system requirements (automated software) | manifest.container | DRAFTED |
| FL-18 | Human-in-the-loop instructions and video | methodology.human_in_loop | DRAFTED |
| FL-19 | Accessible download link | owner (hosting link) | OWNER |
| FL-20 | Other information | disclosure | DRAFTED |
| FL-21 | Review for technical validity and papyrological plausibility | disclosure | DRAFTED |
| FL-22 | No public disclosure before the official announcement | owner (confidentiality) | OWNER |
| FL-23 | Submission through the Submission Form | owner (filing) | OWNER |
| FL-24 | Large model windows: show text is not hallucinated | fp_mitigation | DRAFTED |
| FL-25 | No overlap between training and prediction regions | fp_mitigation + FL-09 certificate | DRAFTED |
| PKG-01 | Licence lineage permits release of code, data and weights (PRIZE-CHECK-20260925 b) | man:licence_lineage (tools/sib/sg/licence/lineage.py) | BLOCKED (owner decision) |
| PKG-02 | SG 11 known-text pass rate recorded (DECL-SG11-REFCAL-1, proposed) | man:sg11_refcal.record (hercules.sg.refcal) | DRAFTED |
| PKG-03 | PHerc. Paris 4 Title Prize variant (DECL-P4-2 item 7) | tools/sib/sg/submit_kit/p4_generate.py | SEPARATE KIT (not part of a First Letters filing) |
