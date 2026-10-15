Provenance: Project HERCULES | owner the owner | [id removed]

# Task pairs0814: known-text protocol check and PHerc0814 D2 training pairs

STATUS: DONE (stage C run once over both halves: this session's 17 segments and pairs0814b's 20250928235953 and 20250926051122, see HANDOVER.md)

## Goal (a): field-by-field protocol check

Source: official root index (decoded sha256 8119d1c2d48b54f880c81bfd7ff9a51eb5edd166c9c06eac754abf15dba7e0ac, unchanged since the D0 catalogue) and each volume's own metadata.json (voxel size = scan.tomo.acquisition.detector.samplePixelSize). References were re-derived from the index; every brief value agreed (JULY 7/7, MAY 4/4).

| Scroll | Volume | session | voxel um | keV | distance m | exposure s | Paganin | unsharp | vs JULY | vs MAY |
|---|---|---|---|---|---|---|---|---|---|---|
| PHerc0814 | 20250804134230 | 20250717 | 9.362 | 113.0 | 1.2 | 0.012 | 1000.0 | [4.0, 1.2] | 7/7 | 0/4 |
| PHerc0814 | 20260309142202 | 20251130 | 2.399 | 78.0 | 0.22 | 0.013 | 1000.0 | [4.0, 1.2] | 2/7 | 0/4 |
| PHerc0814 | 20260521123630 | None | None | 59.0 | 0.22 | 0.013 | 500.0 | [4.0, 2.5] | 0/7 | 0/4 |
| PHerc0500P2 | 20250526151718 | 20250506 | 2.215 | 111.0 | 0.4 | 0.035 | 1000.0 | [4.0, 1.2] | 2/7 | 1/4 |
| PHerc0500P2 | 20250528085330 | 20250506 | 4.317 | 111.0 | 1.2 | 0.03 | 1000.0 | [4.0, 1.2] | 3/7 | 2/4 |
| PHerc0500P2 | 20250820143440 | 20250717 | 9.362 | 113.0 | 1.2 | 0.012 | 1000.0 | [4.0, 1.2] | 7/7 | 0/4 |
| PHerc0500P2 | 20250821110041 | None | None | 65.35 | 0.07 | None | None | None | 0/7 | 0/4 |
| PHerc0332 | 20231027191953 | None | None | 53.0 | None | None | None | None | 0/7 | 0/4 |
| PHerc0332 | 20231117143551 | None | None | 53.0 | None | None | None | None | 0/7 | 0/4 |
| PHerc0332 | 20231201141544 | None | None | 70.0 | None | None | None | None | 0/7 | 0/4 |
| PHerc0332 | 20251211183505 | None | 2.399 | 78.0 | 0.22 | 0.013 | 1000.0 | [4.0, 1.2] | 2/7 | 0/4 |
| PHerc1451 | 20250521151225 | 20250506 | 8.64 | 116.0 | 1.20002 | 0.03 | 1000.0 | [4.0, 1.2] | 3/7 | 4/4 |
| PHerc1451 | 20260319101107 | None | 2.399 | 78.0 | 0.22 | 0.013 | 1000.0 | [4.0, 1.2] | 2/7 | 0/4 |

Verdicts: PHerc0814 JULY (JULY volumes ['20250804134230'], MAY volumes []); PHerc0500P2 JULY (JULY volumes ['20250820143440'], MAY volumes []); PHerc0332 NEITHER (JULY volumes [], MAY volumes []); PHerc1451 MAY (JULY volumes [], MAY volumes ['20250521151225']).
Volumes with voxel None have no readable metadata.json on the bucket (404, or no scan block for the 1.129 um mosaic); none of them is a ~9 um candidate, so no verdict depends on them.

## Segment inventories

| Scroll | segments | 9.362 um mesh | 9.362 um SV | high-res mesh | high-res SV | ink maps by um | with labels |
|---|---|---|---|---|---|---|---|
| PHerc0814 | 19 | 19 | 19 | 19 | 19 | {'1.129': 19, '2.399': 19} | 1 |
| PHerc0500P2 | 46 | 46 | 46 | 46 | 46 | {'2.215': 48} | 1 |
| PHerc0332 | 2 | 0 | 0 | 0 | 0 | {} | 0 |
| PHerc1451 | 1 | 0 | 0 | 0 | 0 | {} | 0 |

Full paths and counts per segment: inventory_<scroll>.json and segment_inventory.json. PHerc0500P2 (fragment) matches JULY: all 46 segments were traced on its 4.317 um MAY-session volume, carry 9.362/4.317/2.215 um meshes and SVs, and their ink maps are on the 2.215 um MAY-session scan 20250526151718; 1 segment has official labels. As instructed, no 0500P2 pairs were built (held-out fold candidate). PHerc0332 matches neither protocol (2 folders with .obj meshes only). PHerc1451 matches MAY (one unindexed raw/ folder of 17 debug traces).

## Goal (b): PHerc0814 D2 pairs

### Method (DECL-D2; ASK.md defaults accepted by the orchestrator)

1. Stage A (tools/sib/pairs0814/stage_a.py): 2-D canvas affine c9 = M c2 + t fitted from the two organizer meshes of each segment (2.399 um mesh vertices -> index landmark affine 20260309142202 -> 20250804134230 -> projected onto the 9.362 um mesh; 4-MAD trimmed LSQ). Official 2.399 um ink map area-averaged onto the 9.362 um canvas (ref9).
2. Stage B (stage_b.py): 384 px patches (stride 384, >= 90 % valid on both canvases); official vc_render_tifxyz -n 31, --flip-normals, voxel size 9.362 um from metadata.json; 2.4 um CT = organizer 2.399 um SV slice 54 of 109 read by HTTP range requests and area-averaged onto the 9 um canvas; gate NCC >= 0.8 (zero shift) AND >= 7 of 9 128 px windows with sub-pixel shift norm <= 1.0 px; labels ink = ref9 >= 150, blank <= 100, rest and invalid 255.
3. Stage C (stage_c.py): consistency checks, CORR-RETRACE-RULE same-papyrus annotation (base papyrus 46527, cross-segment duplicate groups), packing into shards.

### Validation

* Mesh affine (19 segments): kept-point residual p99 max 0.1562 px; normal distance p95 max 8.7675 vox; the fit equals the separable 0841 rule c9 = (c2 + 10.5) N9/N2 - 10.5 to p95 <= 1407.7585 px; trimmed projection outliers 0.5-14.4 % (points snapped to a wrong place on the 9 um mesh; they do not affect the fit).
* Our 9.362 um render vs the organizer 9.362 um SV (segment 20250925212701, 1536 px crop): NCC 0.9968 at the surface, same slice direction (opposite direction 0.005-0.012).
* Range-read 2.4 um chunk slices equal full-chunk slices bit for bit; stage B block labels equal stage A ref9 (max 1 grey level on 2 of 2.36 M px, ink >= 150 agreement 100 %); tiled-TIFF reader bit exact.
* Unit tests: tests/sib_pairs0814_test_numerics.py (13 passed), incl. the CORR-RETRACE-RULE half-cell re-trace case.

### Results (this session's segments)

* Candidates 1502, gated 1502, PASS 564 (rate 0.375); segments complete 19/19; handed over ['20250926051122-auto_grown_20250926051122829', '20250928235953-auto_grown_20250928235953722'].
* Patch NCC at zero shift: p5 0.386, p25 0.641, median 0.791, p75 0.851, p95 0.900; fraction >= 0.8: 0.469.
* Control (not gating), best NCC at +-5 px shifts: median 0.577, p95 0.700, max 0.790, fraction >= 0.8: 0.000 -> the 0.8 bar separates aligned from shifted CT.
* Aligned windows per patch (histogram 0..9): {'0': 424, '1': 103, '2': 49, '3': 59, '4': 51, '5': 57, '6': 61, '7': 46, '8': 141, '9': 511}.
* Labels in PASS patches: ink 12788274 px (11.209 cm^2), blank 64581905 px (56.604 cm^2), ignored 5795005 px; patch area 72.89 cm^2.
* Base papyrus (46527, CORR-RETRACE-RULE fail-closed (vertex OR point-to-surface bins, >= 1000 points within 2 vox, c0 >= 2 c2) vs 20260226000000-46527_2um_try2): {"passed_same_papyrus_46527_by_rule": 7, "passed_on_46527_itself": 4, "passed_with_any_base_point": 29, "passed_within_128vox_of_46527": 282, "passed_within_64vox_of_46527": 205}.
* Duplicates: {"groups": 342, "groups_without_base_points": 330, "passed_patches_in_multi_groups": 292, "edges": 546, "clean_patches_not_in_any_group_touching_46527": 526, "clean_groups": 327}.
* Shards: 180 files, 1560.9 MB total, max 33.6 MB (shards.json lists sha256 and patch ids).
* Consistency problems: none.

| Segment | source | candidates | PASS | fail NCC only | fail align only | fail both | render failed | ink px | blank px | ignored px |
|---|---|---|---|---|---|---|---|---|---|---|
| 20250925161630-auto_grown_20250925161630635 | pairs0814 | 96 | 53 | 3 | 8 | 32 | 0 | 1226940 | 6025865 | 562363 |
| 20250925182632-auto_grown_20250925182632715 | pairs0814 | 114 | 50 | 10 | 15 | 39 | 0 | 1026308 | 5840148 | 506344 |
| 20250925204843-auto_grown_20250925204843950 | pairs0814 | 147 | 21 | 15 | 6 | 105 | 0 | 616222 | 2206292 | 274062 |
| 20250925212701-auto_grown_20250925212701145 | pairs0814 | 29 | 11 | 2 | 9 | 7 | 0 | 198880 | 1308306 | 114830 |
| 20250925222237-auto_grown_20250925222237459 | pairs0814 | 58 | 23 | 7 | 10 | 18 | 0 | 336530 | 2887821 | 167137 |
| 20250926051122-auto_grown_20250926051122829 | pairs0814b | 241 | 95 | 19 | 20 | 107 | 0 | 2569477 | 10414605 | 1024238 |
| 20250926165636-auto_trace_20250926165636789 | pairs0814 | 136 | 22 | 13 | 9 | 92 | 0 | 523607 | 2452826 | 267599 |
| 20250926203608-auto_grown_20250926203608932 | pairs0814 | 115 | 27 | 20 | 5 | 63 | 0 | 589198 | 3116912 | 275202 |
| 20250928235953-auto_grown_20250928235953722 | pairs0814b | 304 | 140 | 17 | 28 | 119 | 0 | 2991172 | 16263538 | 1389130 |
| 20250928235954-auto_grown_20250928235953722_copy | pairs0814 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20250929040153-auto_grown_20250929040153260 | pairs0814 | 47 | 31 | 4 | 4 | 8 | 0 | 737382 | 3489975 | 343779 |
| 20250930083742-auto_grown_20250930083742882 | pairs0814 | 92 | 43 | 4 | 13 | 32 | 0 | 1061841 | 4833596 | 445171 |
| 20251001060526-auto_grown_20251001060526760 | pairs0814 | 103 | 44 | 8 | 14 | 37 | 0 | 796118 | 5297276 | 394670 |
| 20260225160055-auto_grown_20260225160055913 | pairs0814 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20260226000000-46527_2um_try2 | pairs0814 | 19 | 4 | 11 | 0 | 4 | 0 | 114599 | 444745 | 30480 |
| 20260226110425-auto_grown_20260226110425097_abf | pairs0814 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20260226113324-auto_grown_20260226113324624_abf | pairs0814 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20260226121302-auto_grown_20260226121302716_abf | pairs0814 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20260226123353-auto_grown_20260226123353106 | pairs0814 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### Outputs

* pair_registry.json: every PASS patch (segment, 9 um canvas box, 2.4 um footprint, 3-D centre and bbox in 9.362 um voxels, gate numbers, median window shift, label counts, shard and index, base-papyrus and duplicate annotations); pair_registry_xyz.npz: 17 x 17 xyz grid per PASS patch.
* registry/<segment>.jsonl: every candidate incl. failures with all 9 window shifts and controls.
* Shards = the staged block files (one per 1536 px block, <= 16 patches, each < 90 MB): logs/sib/pairs0814/blockpairs/<segment>/<y>_<x>.npz on this branch and data/sib/pairs0814b/blockpairs/... on pairs0814b; arrays images uint8 (N, 21, 384, 384) = render slices 5..25, ref9, labels (1 ink, 0 blank, 255 ignore), valid, xyz, patch_id. Not repacked (repacking would duplicate every patch and exceed the 1.5 GB branch budget). shards.json lists branch, path, sha256 and patch ids of every file.
* protocol_check.json, segment_inventory.json, inventory_<scroll>.json, stage_a/<segment>.json, summary.json, shards.json, runs.jsonl (every run, failures included).

### Failures and deviations

* setup_env: exit 1 at the vesuvius Python 3.14 install step (not needed: no inference here); the C++ apps and /opt/hv built fine. The proxy port changed, so tools/sib/pairs0814/setup_env_sib.sh and vc_build_sib.sh take it from HTTPS_PROXY.
* Stage B stopped silently at 2026-09-25T19:57Z while the session was suspended (usage limit) and was restarted from block checkpoints at 23:26Z (dockerd restarted); no block was lost or duplicated (stage C uniqueness check).
* Five small 2026 segments (0.2-0.3 cm^2) have no 384 px patch >= 90 % valid, so 0 candidates.
* Split: segments 20250928235953 (71 blocks) and 20250926051122 (65 blocks) handed to pairs0814b (HANDOVER.md); their block files and registry rows live on that branch, and the final stage C read them through git objects of the recorded commit (below) to annotate base papyrus and duplicates across both halves.

## What the orchestrator needs to declare next

1. The D2 pair recipe as built (ASK.md Q1-Q6), incl. that labels are not shift-corrected (median window shifts are recorded per patch if a corrected variant is wanted).
2. Exclusions: which base-papyrus (46527) patches and which members of each duplicate group enter D2 training (DECL-D2-POOL-1, proposed); stage C only flagged, no patch was dropped.
3. Whether PHerc0500P2 (JULY match; maps on the MAY-session 2.215 um scan) becomes the L-0500P2 fold; its pairs would use the same code with the 2.215 um volume and SV.

## Provenance of this run

* pairs0814b commit used by stage C (read through git objects only): d1b6af5b28bd8285a579d3680db9c6a23f8d54de ({"20250928235953": {"rows": 304, "passed": 140, "segment_done": {"utc": "2026-09-25T23:59:19Z", "candidates": 304, "blocks": 71}}, "20250926051122": {"rows": 241, "passed": 95, "segment_done": {"utc": "2026-09-26T00:30:23Z", "candidates": 241, "blocks": 65}}}).
* Host: CPU(s) 4; Model name Intel(R) Xeon(R) Processor @ 2.80GHz; Thread(s) per core 1; Socket(s) 1; AMX flags: none (this container has no AMX; docker/TOOLING.md described a 2.1 GHz AMX host)
* Final commit: see git log of claude/gifted-bell-gavnl5-sib-pairs0814 (the commit that adds this REPORT.md).

## Duplicate groups (multi-member) and base-papyrus flags

70 multi-member groups; members listed in pair_registry.json (duplicate_group). Base-papyrus (46527 same-papyrus by rule) patches: 20250925182632_2304_18432, 20250925182632_2304_18816, 20260226000000_768_1152, 20260226000000_384_1536, 20260226000000_384_2688, 20260226000000_1152_1536, 20250928235953_1152_17664.

