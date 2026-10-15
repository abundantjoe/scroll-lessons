# P4 reconnaissance: PHerc. Paris 4 (Scroll 1) Title Prize

Provenance: Project HERCULES | owner the owner | [id removed]
Generated: 2026-09-26T00:06:34Z. Serves RULES.md DECL-P4-1 item 1. Machine-readable version: logs/p4/recon.json.
Viewing: no image or CT chunk was opened. Only metadata, listings, model cards and official pages were read. No title words, readings, transcriptions or author attributions are recorded here.

## Prize
- "PHerc. Paris 4's Title", $50,000, open. The deadline is June 25th, 2027 (11:59pm Pacific), and submissions stay open until the prize is won. Any published Scroll 1 scan qualifies, including the 2.4 um volumes.
- Page: https://scrollprize.org/prizes. The page was re-fetched at 2026-09-26T00:04:18Z (sha256 4214ffc9...). Its text is identical to the 23:53:29Z fetch (sha256 b5649c1f...); the hashes differ only because of Cloudflare markup. The winners page lists no Paris 4 title award.
- The submission needs:
  - a tifxyz mesh with a low-distortion isometric flattening;
  - a programmatic image of the unwrapped region, with no manual annotation;
  - ink predictions shown in the spatial context of the title search;
  - a 1 cm scale bar and letter sizes;
  - the image named after the mesh.
  Ink outputs of the region must not overlap training data. The method must be reproducible (Docker, or instructions plus video) and include false-positive mitigation on held-out ground truth.

## Volumes (7 scans, 7 volumes)
- Main volume: 20260411134726, 2.4 um, 78 keV, from scan 20260311024914. L0 is [75784, 32693, 32693] uint8, uncompressed, in 128^3 chunks, about 81 TB. Every segment, label, prediction and representation targets it.
- 20260608103018 (1.129 um mosaic): covers only the central/inner region (x 13.9-51 mm, y 12.6-53.9 mm, z 67-135 mm). It does not cover the outer windings.
- 20260323153942 (2.4 um, 137 keV): a small ROI near the axis.
- 20260310170716 and 20260310173927: 45.5 um overview volumes.
- DLS 7.91 um volumes 20230205180739 and 20230206171837: listed in root metadata only. They are hosted on data.aws.ash2txt.org under the EduceLab licence, not in the bucket, and their .zarray was not fetched.
- Conflict (re-verified): the transform.json of 20260310170716 (15 landmarks) does not match the root metadata.json transform (8 landmarks).

## Segments (81)
- 11 segments from the 2023 Grand Prize era (bbox half-extent 9-15 mm, i.e. middle windings).
- 3 re-traces from 2026 (v14, v2_flatboi, v8).
- 9 strips named 5753_*.
- Spiral-fit winding strips: 28 in the 20260701 set and 30 in the 20260623 set. The fit has 130 windings and wNNN counts outward.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
  - official 2D ink predictions (model 20260417190342) exist on 2.4 um.
- Mesh folders are named `<14-digit id>-on-<volume>-<px>.tifxyz`.
- Anomaly: the v14 mesh bbox extends beyond the volume bounds.

## Labels
- The ink_9um aligned set has **8** Paris 4 cases, not the 10 that DECL-P4-1 wording implies. There is no w04, and w08 is unused and has no labels.
  - w00 = 20231016151002
  - w01 = 20230702185753
  - w02 = 20231031143852
  - w03 = 20231106155351
  - w05 = 20231012184424
  - w06 = 20231210121321
  - w07 = 20231007101619
  - w09 = 20230929220926
- Each case is aligned to level 2 (9.6 um) of the segment's 2.4um-0.22m-78keV-volume-20260411134726 render.
- The same 8 segments carry the S3 label set 20260918.

## Predictions and training use
- 2D ink: 80 segments with model 20260417190342 on 2.4 um, and 37 with model 20260709123958 on 1.129 um L1. There is also one 3D ink volume (20260428123845). No ink_9um product exists for Paris 4.
- ink_9um step-075000: both seeds (42 and 43) trained on all 8 Paris 4 cases, and no Paris 4 case was held out.
- ink_3d_dino_guided and hecate also used Paris 4 supervision.
- For the 2 um and 1 um models, training on Paris 4 data is unknown.

## Where the title is expected (official statements, location only)
- Prize page and data browser: the expected title region shows no detectable ink so far (possibly a different ink), and its top rows are physically missing. The organizers suggest better methods, higher resolution, or looking somewhere new.
- The organizers' 2024 Scroll 1 title post says titles usually sit at the end of the roll, after the final text column, or below a short last column. The segments of that search appear only inside a figure, which was not viewed.
- A 2024-06-04 post lists 5 segment ids near the end of the scroll: 20240102231959, 20240110113230, 20240116164433, 20240101215220 and 20240109095720. Linking them to the title search is our inference. They live only on dl.ash2txt.org (7.91 um volumes). That host is outside the declared source list and was not re-fetched.
- The Grand Prize page places the known text at the end of the scroll.
- Nov 2024: a large title-region segment was uploaded, but it is linked only via Discord.
- No official winding, segment id or coordinates are given. Which physical end (inner or outer) holds the end of the roll is not stated. Precedents (PHerc. 172, Scroll 5) place end titles near the core.

## Feasibility (4 vCPU, no GPU, 2.2 GB free disk measured, not ~3 GB)
- 2.4 um surface volume cost per cm^2:
  - L0 with 109 layers: 1.89 GB
  - L0 with 31 layers: 0.54 GB
  - L2 (9.6 um): 118 MB
  - ink_9um input with 21 slices: 23 MB
- A 2x2 cm window costs 7.6 GB at L0, 473 MB at L2 and 91 MB as ink_9um input. That is about 289 L2 chunks of 1.79 MB each.
[line withheld: prize-candidate detail under review]
- Only windowed streaming fits the disk.

## Gaps
- No official coordinates for the title region, and the 2024 figure was not viewed.
- The 2024 and Nov 2024 title-search segments are not in the bucket.
- Inner vs outer end of the roll is not stated.
- The outer-wrap ranking uses bboxes, not per-vertex radii.
- The DLS .zarray was not fetched.
- The 45 um transform conflict is unresolved.
- The v14 bbox anomaly is unexplained.
- The 20260623 vs 20260701 spiral sets have no official explanation.
- The DECL-P4-1 w00..w09 wording needs correcting, and the seed is unspecified.
- Equality of the HF and S3 label sets was not checked.
- Training data for the 2 um and 1 um models is unknown.
- The mapping_validity arrays are missing from S3.
- The stored mesh grid resolution is unknown without reading the TIFF headers.

## Critic additions (2026-09-26T00:12:30Z)
These were appended by the completeness and integrity critic. Nothing above was removed. The full records, with sources and fetch times, are in recon.json under `critic_additions`.

**Integrity**
- No Greek characters, title-like words, readings, transcriptions or author attributions appear in either file.
- Six spot-checks against live sources all held:
  - prize-page quote and deadline (00:09:08Z)
  - root metadata ETag (00:09:07Z)
  - 2.4 um L0 .zarray (00:09:07Z)
[line withheld: prize-candidate detail under review]
  - ink_9um card training on Paris 4 (8) (00:09:15Z)
  - data-browser caveat (00:08:57Z)
- Minor discrepancy: the "9-15 mm" figure for gp-2023 is the mean x/y bbox half-extent (9.3-15.4 mm). The max-axis half-extent is 10.5-18.4 mm.

**New official location statements (location only)**
- Data browser (00:08:57Z):
  - "Substantial continuous Greek text recovered; ink clearly legible at 2.4µm."
  - Image captions: "Ink detection across windings 28–37 (2.4µm)" and "2.4µm ink detection (segment 20231210121321)". The images were not viewed.
- Spiral tutorial (00:09:53Z): "the defaults, 4,000 and 17,000, span the whole written region of Scroll 1". The unit is full-resolution voxels of the spiral dataset, which is 9.6 um. This is corroborated by the 20260701 source tag `fitted_m7_ds2_z3000_18000_allgpu` matching its z range of 28.8-172.8 mm. Derived: the written region is about z 38.4-163.2 mm in the 2.4 um frame.

**Derived radial placement (inference, not an organizer statement)**
[line withheld: prize-candidate detail under review]
- By the organizers' rule that the title follows the end of the text, the title is more likely inward, toward the core, as with the PHerc. 172 and Scroll 5 precedents. It is less likely on the outermost windings that recon ranked.
- This needs a per-vertex winding check before DECL-P4-2 relies on it.
- Coverage of the inner windings:
  - No official strip covers w000-w009.
  - The inner strips are:
    - 20260701 set: w010-027 (641.42 cm^2) and w028-037 (676.2 cm^2), 2.4 um only.
    - 20260623 set: w010-027 (415.32 cm^2) and w028-037 (438.29 cm^2), which also have 1.129 um meshes and 1 um predictions.
  - The 1.129 um volume and the 137 keV ROI both cover the core.

**Meshes**
- All 81 segments have `mesh/intermediate/` with original, normalized and flattened OBJs (listing at 00:11:02-00:11:40Z).
- The tutorial says render_ink SLIM-flattens each strip before rendering, so the official tifxyz meshes already carry a flattening.
- The distortion of those flattenings has not been measured, and the OBJs were not downloaded.

**ink_9um applicability** (card, 00:09:15Z)
- The models expect ~9 um isotropic input. A 2.4 um surface volume must first be pooled to XY level 2 with 4x z mean-pooling (`scripts/prepare_9um_isotropic_input.py`). This fits the 20260411134726 volume and the label alignment.
- There is no documented recipe for 1.129 um or 45 um.
- The models are sensitive to z-offset.
- The no-ink baseline is ~0.25; for display use (p-0.25)/0.5.
- The model was trained on all 8 labelled Paris 4 segments. So:
  - a DECL-P4-2 region must exclude their supervised areas (prize rule: no overlap with training data);
  - held-out false-positive checks on Paris 4 would need k-fold retraining.

**Organizers on ink so far**
- The text is clearly legible at 2.4 um.
- The expected title region has shown no detectable ink so far (possibly a different ink, and the top rows are physically missing).
- There is no official report of any ink detected in the title region.

**Remaining gaps for DECL-P4-2**
- No official title-region coordinates.
- The winding of the last text column is unknown (it needs tifxyz x/y/z, which were not read).
- No mesh exists for w000-009.
- The distortion of the official flattenings is not measured.
- The z extent of the missing top rows is not stated.
- The 2024 title-search figure was not viewed, and its segments are outside the bucket.
