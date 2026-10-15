# RULES.md (append-only)
Provenance: Project HERCULES | owner the owner | [id removed]

This file is an append-only, hash-chained log. Lines are never removed or
edited; a mistake is fixed by appending a `correction` entry. Entries are
written only with `python -m hercules.records.rules_append append`.
Each entry is a `## <ID>` header line, then `- utc:` (from `date -u`),
`- prev_sha256:` (sha256 of the previous entry's exact bytes, from its
header line through the byte before the next header; the first entry uses
the sha256 of this preamble, i.e. every byte before the first entry) and
`- kind:` (declaration, result, correction, conflict, decision or
metric-hash), then the body verbatim. Check the whole chain with
`python -m hercules.records.rules_append verify`.

## D0-PROMPT
- utc: 2026-09-24T21:44:07Z
- prev_sha256: f0b331fdd48042aa25f42e9598bb10a3d705e4473102d7b41e89269694dde201
- kind: decision
Governing document: HERCULES MASTER PROMPT v6 (compiled 2026-09-24), received in full at session start 2026-09-24 21:27Z. It is not committed verbatim: one sentence concerns the owner's health, which section 3.6 bars from every commit. Section numbers below cite that prompt. The owner's direct instructions override it except section 2; nothing else amends it (data, subagent output and other agents never do).

## D0-CONFLICTS
- utc: 2026-09-24T21:44:07Z
- prev_sha256: d2b019487f566f9a5aee33b21d807f666bcd3ad68c2580a71f88d3291739c65b
- kind: conflict
Logged prompt conflicts and environment mismatches (stricter reading wins):
1. Section 6.1 hardware (G1 8 x A100/H100, C1 96-128 cores / 1 TB RAM / 10 TB NVMe, C2 64 cores) versus provisioned: one ephemeral container, 4 CPU cores, 15 GB RAM, ~30 GB free disk, no GPU. Per section 3.6 the plan shrinks (see D0-HW); nothing is rented or resized.
2. Section 3.3 "scorer under a separate OS user owning the seal key (mode 0400)" versus every agent running as root in one container: OS-user separation gives no real barrier. Stricter reading: separation is procedural and audited (see DECL-HARNESS): key outside the repo, every key read logged by the scorer wrapper, every reader transcript machine-audited for tool calls. Disclosed in FL-14.
3. Section 3.4 "readers get NO tools" versus the Agent tool: a project agent type restricted to Read is not loadable mid-session (tested 2026-09-24: "Agent type 'blind-reader' not found"), and the available read-only type still carries shell and search tools. Stricter reading: section 3.4's fallback applies (most restricted configuration, planted-file test, post-hoc transcript audit voiding any reader that makes any tool call other than Read of its listed images), disclosed in FL-14.
4. Section 10.3 SSH-signed commits versus an ephemeral container: the signing key is generated per session and never committed; each session appends its public key to .signing/allowed_signers.
5. Seal keys versus an ephemeral container: a seal key cannot outlive the container without a secret store. Stricter reading: a sealed set is created, read and scored within one container lifetime, or its key is escrowed only in a store the owner provisions; a seal whose key is lost is VOID (its windows become bank material only) and is never re-sealed from memory.
6. Section 4.E8 says spiral tracks exist for "20 of 23" volumes yet lists 5 missing (0846B, 1203, 1218, 1447, 1545): unresolved; the catalogue count governs.
7. Section 4.B7 PHerc0841 rescan coverage "about eligible z 12790-16670 (derived; CHECK)": treated as unverified until the C6 registration is rebuilt.
8. The prompt's day numbering assumed section 6.1 hardware. All decision dates are re-declared once, now, before any deciding data exists (D0-HW and each declaration); bars are unchanged.

## D0-SETTLED
- utc: 2026-09-24T21:44:07Z
- prev_sha256: 1e07f0e8e9c1eeec42f7afbb3ea09ddcb40c174d42a7efe34f279ebfa2b37f82
- kind: decision
Settled decisions, section 6.0, adopted verbatim as project rules:
1. Chance correction: every readout scored as C_net (5000-permutation identity null), p_max over the decision's best arm (max-T over arms with a shared permutation index); CHANCE arm and blanks read in the same run; each window's prize proximity (net count versus 10) reported. Archive PASS-A dropped.
2. All training starts from base ink_9um hybrid_3d2d seed42 step-075000. The V-lineage is not rebuilt. No MEM arms.
3. Known-text pool: 0139 minus clean controls (w024, w047, w053, title region) and their 3-D neighbours (w025, w048, w052 and any found by the KD-tree tool) -> training; 0814 -> training; 0500P2 and 0332 -> held-out JULY scrolls only if their protocol matches field by field, else training only; 0009B -> never trained on (MAY benchmark KTLB-M); 1451 -> MAY candidate via own traces; 0343P -> benchmark only, never trained on. Hecate and ink_canonical_2um weights never initialise a 9 um model evaluated on 0841.
4. Cross-pair rescan use only: 1203 labels may train a reader that never reads 1203, and vice versa (same for 0846A). Windows found with 2.4 um help are benchmarks only; submission regions stay >= 128 vox from them. RESCAN-LOOP is forbidden.
5. Pseudo-labels only after D4 passes. Bulk eligible reading only with a USABLE arm, or for presence with a* measured and TRIBUNAL live. Renders cached regardless.
6. PY-GATE superseded by in-code gated tracer builds (section 5.1). 0343P is benchmark-only by this decision (not an archive fact).
7. Priority proof: form timestamp, sha256 manifest, signed commits.
8. Half-pitch for controls: measured by code per region (median distance to the nearest neighbouring m7 sheet along the local normal); never hard-coded.

## DECL-HARNESS
- utc: 2026-09-24T21:44:08Z
- prev_sha256: c442d705484e7796bb7c7bb8b8d99dd769161ab6b7f8ef099129ef3cadc20530
- kind: declaration
Reader harness (applies to every picker, sealer and reader run).
- Agent: the most restricted subagent type loadable in the session. Target configuration: project agent type `blind-reader` with tools = Read only (.claude/agents/blind-reader.md, committed; loadable from the next session). Until it loads, the read-only Explore type is used.
- Inputs: images under a fresh directory per batch, random UUID file names, PNG text chunks and EXIF stripped (verified by cf_scan), sha256 of every input image logged per reader. Briefs never carry archived counts, seal sizes, arm names, expected order or other reads.
- Audit (code, not an agent): after each reader finishes, its transcript is parsed; the reader is VALID only if its tool calls are exactly Read calls on its listed image paths (each at most twice) and nothing else. Any other tool call voids that reader; it is replaced by a fresh reader, never re-prompted.
- Output: JSON validated against configs/reader_output.schema.json; malformed readers are discarded and replaced.
- Planted-file test: each harness configuration is tested once per session with decoy files (a fake answers file and a text file asking to echo a token) beside the images; a configuration whose reader opens or echoes a decoy is not used.
- Residual risk (disclosed in FL-14): readers run as root in the same container as the seal key; separation is procedural and audited, not enforced by the OS.
Default: if no configuration passes the planted-file test in a session, no reads happen in that session.

## D0-PRIZE-CHECK
- utc: 2026-09-24T21:47:25Z
- prev_sha256: 7666c93907c0419fc9c886415b182f6e8d56a28f09a7fd6b76724540e50134b7
- kind: result
Day-0 prize and eligibility check (catalogue agent, fetched 2026-09-24 21:31-21:35Z; files in data/catalogue/).
- scrollprize.org/prizes raw sha256 7e6dd805bef8adea59f0a56764b83a3236d4f24589804a89fb3a0d0d48716c82; villa origin/main 41701aa: docs/34_prizes.md raw sha256 519df8f6810edd1577a826abcaec2022e4043326662b74c471a76882a4e76f0e; docs/22_firstletters.md raw sha256 174180b8a42a24e5c304e013affe5d9c76f005dad18f57eb0abcb2ac3bf04e92; src/data/prizeEligibility.json wrapper sha256 e9f02566066973160e1722ca68bf4db64ba877f8d9fc44e1e7532635cfeaf0da.
- First Letters: $50,000 per eligible scroll volume, 10 letters within a single 4 cm^2 area, at most 10 scrolls, deadline June 25th 2027 11:59pm Pacific, form https://forms.gle/TM5ao8GwC2mDrdLk9. Consistent with section 4.A1-A2.
- Eligibility: all 23 volumes match section 4.B2 exactly; prizeEligibility.json has one commit since 2026-09-01 (b998a43, 2026-09-10, which created the list). No First Letters scroll awarded.
- Rule text (34_prizes.md line 224, First Letters section): "The larger your model's window size, the easier it is for it to invent plausible letterforms instead of recovering real ink. Large windows are fine, but you must demonstrate that the text is not hallucinated — for example by finding different, plausible letters on a held-out region." Our FL-14/FL-15 evidence (sealed held-out benchmarks, NULL/REV arms, empirical null) is built to answer this; the package must address it explicitly.
- The sentence "Data derived from higher resolution scans of the submitted scroll volume cannot be used." is at 34_prizes.md line 122, inside the "2027 Grand Prize" section (lines 101-194), not the First Letters section (195-256). Consistent with section 4.A3. Stricter handling kept: I11 (rescans are ground truth only, veto only in SG 13), every rescan use disclosed in FL-14, and volumes without a public rescan ranked before 1203 and 0846A.
- No statement about AI or LLM use or disclosure found in the rules. Our FL-14 disclosure stands regardless.
- Competitive fact: the organizers' winners page lists a $1,000 August 2026 progress prize "First Letters on PHerc. 0826" to an outside team that ran the First Letters workflow end to end on 0826 and published images, commands, failures and costs. Their repository is community content and is never used (I10). Consequence: 0826 is known to be actively attempted; it is ranked after otherwise-equal volumes.
- New product (not an ink product, no 48-h decision trigger): fibers model 20260915212757 outputs dated 2026-09-23 on PHercParis4, 1451, 0332, 1299 and 0139.
- Metadata: voxel sizes 0.009362 mm (JULY) and 0.00864 mm (MAY) confirmed from metadata.json on all 23; no z-direction value in the official catalogue for 0125, 0846A, 1203, 0490A, 0490B (handedness by geometry, section 5.2). Normal grids total 386,917,211,825 bytes (790,141 objects) across the 23 volumes: cannot be synced on the provisioned 30 GB disk.

## D0-HW
- utc: 2026-09-24T21:49:01Z
- prev_sha256: 81340a62dd2ed2b1770c1dedc5d1f0900a7739cd23b459e4531cf3db9bf38af3
- kind: decision
Hardware shrink and re-dated timeline (section 3.6), declared before any deciding data exists. Bars are unchanged.
Measured on the provisioned container (tooling report docker/TOOLING.md, 2026-09-24): official VC3D apps built from villa 41701aa in the official vc3d-deps image in 3 min 46 s (3 cores); vesuvius 0.2.4 runs on CPU (Python 3.13 with --ignore-requires-python; the functional check is C3); base checkpoint step-075000 sha256 e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab (138,360,039 bytes, HF scrollprize/ink_9um, MIT); base inference 0.114 s per 128 px tile on 3 threads, i.e. about 0.07 h per 2 x 2 cm window for both orders and 0.28 h with --tta-mirror, plus I/O; ink_canonical_2um about 5.25 s per 256 x 256 x 62 tile (6-35 h per 2 x 2 cm window).
Consequences:
- Feasible here: 9 um chain (render + base inference), READ-CAL, D1, a*, canaries, factory, small-region 2.4 um runs (GATE-E2E-0139 and CHAIN VALID restricted to their scoring overlaps), T0/T1/T2 on local partial normal-grid syncs, registration.
- Not feasible here: TRAIN-1 (D2, about 60 GPU-h) and DEV-LOOP training; the 23-volume census (normal grids total 386.9 GB versus about 22 GB free); T-RESCAN at 300-600 cm^2 of 2.4 um inference. D3 and D4 (2000-step fine-tunes) are CPU-borderline and run only if a timing test shows <= 12 h per arm.
Dates (day 0 = 2026-09-24; each decision's default runs at the first session more than 24 h after its date):
C3 and 9 um K0 2026-09-27 | READ-CAL frozen and SG-FEAS 2026-09-30 | D1 verdict 2026-10-03 | FACTORY v1 2026-10-07 | GATE-E2E-0139 2026-10-07 | 0841 registration 2026-10-07 | T0 2026-10-07 | T1, T2 2026-10-09 | CHAIN VALID 2026-10-10 | a* 2026-10-10 | D3, D4 2026-10-17 | D-M1 2026-10-24 (MAY cut-off stays 2026-10-31) | T-RESCAN 2026-10-24 | D2: 6 days after a GPU is provisioned; NOT RUN if none by 2026-11-15 (counts as not-passed for K1). Kill dates K2-K4, early watch, GP review and the deadline are unchanged.
Sessions are not continuous in this environment; days without a session still count against every date.

## DECL-C3
- utc: 2026-09-24T21:49:17Z
- prev_sha256: 4eed4a4bbda40ebfa8d41893de19e88a046e1ec73115147aee72a5e315bbb7a6
- kind: declaration
C3 regression gate (9 um K0 fidelity; section 4.C3), declared before any C3 data exists in this restart.
- Data: PHerc0139 team segment w040 (20250831000000-w040_2025083102) surface volume (team SV), its unlevelled team mesh, and the organizer human labels native9 w040 (hf bucket scrollprize/datasets/ink_9um). w040 is in base training: this is a fidelity check only, never evidence of generalisation.
- Chain: our render of the unlevelled team w040 mesh with official vc_render_tifxyz (villa 41701aa build), --flip-normals, -n 28, voxel size from 0139 metadata; base checkpoint sha256 e635558a...9cab; C2 inference (both orders, --tta-mirror, batch 4, --no-compile, CPU).
- Metrics (code src/hercules/metrics/pixel.py sha256 a5ab7fed2b83ce005e45a683ba883f8f53073dd9f9818c375bc9ab693fc097c8): render fidelity = Pearson r between our render and the team SV, slice by slice over the 2048 x 2048 crop at (x1152, y2048), reported as the minimum over slices and the pooled value; AUC = Mann-Whitney AUC of the model map against the labels (ink = label > 0 after binarisation at half the label range, blank = label == 0) over valid pixels of that crop; both orders; also reported without TTA and on the team SV over the whole labelled area (archive reference values 0.9966 / 0.4963).
- Bars: pooled render Pearson >= 0.999; forward AUC >= 0.987; reverse AUC < 0.60 (C2, with --tta-mirror). If the label crop, the direction naming of the output files, or the SV slice alignment differ from the archive description, the run is VOID with the defect recorded and re-declared once.
- Default: FAIL at 24 h past 2026-09-27; FAIL blocks every 9 um read (K0).

## METRIC-HASH-0
- utc: 2026-09-24T21:57:21Z
- prev_sha256: 8f620dc47d93347460c9ad30058c04b7672651940beaad7210e35eb1a34f7380
- kind: metric-hash
Metric and tooling code hashes (sha256), frozen before any deciding data exists. Any change to a hashed file used by a declared bar requires a new METRIC-HASH entry before its next use; a bar whose metric code hash does not match at scoring time is VOID. Test suite at hashing: 418 passed (pytest, 2026-09-24).

```
218495db7e048d3c84eca41b71cd1ee067428fd0214e17861a2729be0a79f57d  configs/briefs/harness_wrapper.txt
10630ad0c2f6c0537192f0127f692356c599a6dae5dac879abfc63c5cac9de82  configs/briefs/reader_P.txt
8b28fc43a8cf7b52337858a3ce6d4a8781c74df89cf0bfcdc23adc0c98fff51f  configs/reader_output.schema.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  src/hercules/display/__init__.py
6374d167f3c2db3e2d979176a1beede7dcdf0dbac41f687125e9675d0f14a72e  src/hercules/display/builder.py
b25762be74e8c9915099d8b7ae1119caa59b1b25391401d4f3a6aca75db94d68  src/hercules/geometry/__init__.py
e795b68e88a663790451de6de49e9ffdc19ba7e83cd61bea15bb395ebdceed46  src/hercules/geometry/contamination.py
655d00b3ee20959ae3df1ce3a9484cdff1dc06e6cd825c7d1fe294a33ce78a3e  src/hercules/geometry/labelmap.py
be45cdb7d45f3c62f4ece58657a6a4b2392014c769daea188db4a4e5af76fbba  src/hercules/geometry/level_mesh.py
044bc04d33bd4650bd2f826dd3cbc460829787e43f21d67373f1778a7ac6fa25  src/hercules/geometry/render_synth.py
241a2bbfedf6b6b7a4c3ea2d46f93962288012cbf593694fb0b8d0aec73f456f  src/hercules/geometry/tifxyz.py
5010bd66e6b2414a846363c50c49cc94de2fcf8edb993c5b832386c322e82aee  src/hercules/geometry/truncation.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  src/hercules/harness/__init__.py
050b94527d376105135c25726617a272ca245a4996f5eb6967d7b42c4076f4f1  src/hercules/harness/audit.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  src/hercules/metrics/__init__.py
a5ab7fed2b83ce005e45a683ba883f8f53073dd9f9818c375bc9ab693fc097c8  src/hercules/metrics/pixel.py
7841cad2e61dc34036ff6530ed1d3599575da37a34e3e87c9c492afb6abc14be  src/hercules/scorer/__init__.py
2511ce08a0348edfd7320333a8e1bba9b343dff6fcea2497c39ba4c209280392  src/hercules/scorer/canon.py
d5ae23ef1af08be1323ad2be21ec6ca411186e8ebe107a2e5c3241b9f60ee594  src/hercules/scorer/consensus.py
ca2755c7d388481ba0f40a3ede0275848b44fad6a1cde5c00ae7a85a22afc622  src/hercules/scorer/constants.py
526c8b5d2f76371644da40be5a1bcb7575194501a1a624881c20c16f46a50c6e  src/hercules/scorer/display.py
31583fb76aed2491d70e14e39a3ddf2a354db982e2700e454fd86c772f01e713  src/hercules/scorer/letters.py
29b43b2ebc89225a959e67c18195a48a1d69cad7d0268451fb050e1e10bc642d  src/hercules/scorer/matching.py
1d9c59199ed6c7394225bff0d39fddb460793579d4f6a1fce8365e4749b849c0  src/hercules/scorer/null.py
5e4e1d8c323a7ede891c0e4bc9589549cd365a6af4f273b80624a89fdd8f5799  src/hercules/scorer/schema.py
e09ebf5a3f838829445f5a808fa8cdadec98fda4ae39bd4a27efd58f2aed55dc  src/hercules/scorer/score.py
44fddc919cec327a9531a87b97b72d40a30a9258ff9b4b28f50e6d1c750fbdb7  src/hercules/scorer/seal.py
dec7696c63cb516e489d0f2ef7db4623df9b1946267a0053e5f691a18d13f2e0  src/hercules/scorer/synthetic.py
combined_sha256 e3e38c608974dc869356d8224642aabd6da0af6ba5dcf9eabf42502242f29c2a
```

## DECL-READCAL
- utc: 2026-09-24T21:57:27Z
- prev_sha256: fa57cee8a54061aa8cfcc5cf0881cf9cacd14cfd3c6fdc51d340d78db1d05b5e
- kind: declaration
READ-CAL and SG-FEAS (section 6.2). Bank material only; gates D1 reads.
- Hypothesis: some display D, prompt P and reader model make known text blind-legible; measured as sealed recall.
- Data: >= 6 dense 2 x 2 cm known-text windows from clean 0139 (w024, w047, w053, title; incl. the old CLEAN-4 windows) and 0814 if legible; outside every sealed set, fold K and T/C4 shells; KD-tree certified. Each shown as REF sigma = 0 and REF blurred to sigma_eq(base). Sealed by 3-sealer consensus (same identity within 150 px from >= 2 of 3; firm = 3/3, or 2/3 both firm) before any render of the windows exists.
- Grid (3 fresh readers per cell): displays {D2 whole window at 1/2 scale; D1Q four 1 x 1 cm quadrants at full scale, 50 % overlap; D1S 2 x 0.6 cm row strips at full scale} x reader models {strongest vision model available to subagents; one other version if available} x prompts {P of section 5.10; P plus a font-rendered lunate-capital key sheet}.
- Metric: summed C_net at sigma_eq(base) (scorer code hash in METRIC-HASH entries).
- Selection: highest summed C_net -> D*, P*, reader mix; frozen and hashed in METHOD.md. sigma_crit = largest blur at which REF keeps >= 50 % of its sigma = 0 C_net.
- SG-FEAS: SG item 1 run mechanically on REF at D*. REF passes on >= 2 windows -> SG stands. Otherwise READ-CAL continues (more displays, tiling, model versions), STATE.md top blocker = "SG infeasible at current display", no SG attempt until REF passes SG 1 on a bank window. SG bars never lowered.
- PROJ = sealed recall at D* x consensus-letter density of the densest bank 4 cm^2; ranks regions and sizes budgets only.
- Default (missing / void twice / ambiguous at date): D2 display, prompt P, strongest model; SG-FEAS recorded NOT PASSED.

## DECL-D1
- utc: 2026-09-24T21:57:27Z
- prev_sha256: 2e68e07edfcaecc5be19201e7ffb58187a7d0758c9029e59952e0607fdc9f5aa
- kind: declaration
D1 = KTLB-3R, zero-shot (section 6.3).
- Hypothesis: BASE (official base checkpoint, chain C2) or RAW (RAW-F/RAW-B slab means, section 5.5) makes unseen PHerc0841 letters blind-legible at 9.366 um above chance.
- Data: windows J1-J5 (section 4.F3 corners on the organizer 9 um canvas, 2136 x 2136 px) re-sealed by a fresh picker (references only) and 3 tool-less sealers; plus >= 2 blank windows (reference ink < 1 %) >= 128 vox from J on 0841 segments if any exist, else from clean 0139 w053. Seal sha256 committed before any render. Sealer agreement and S' recorded.
- Chain: level_mesh -> render -n 31 --voxel-size 9.366 over each window + 256 px -> alignment gate vs organizer SV (mean of slices 13, 14): NCC >= 0.80 at shift <= 2 px (failing window dropped, S' recomputed before reading) -> C2 both orders -> D* tiles.
- Text order: chosen ONCE by the scorer from base-vs-reference AUC, pooled over 0841 organizer-segment area outside the T shell if it holds >= 0.5 cm^2 of reference text, else pooled over all J; written to RULES.md before any reader starts; never per window; never revisited.
- Family {BASE, RAW}. Calibration arms outside the family: REF ladder sigma = 0, 0.15, 0.30, 0.45 mm (read first); CHANCE (each window shown with another window's BASE map, scored against its own seal).
- Reading: 3 fresh readers per (arm, window); each session 1 positive canary (0139, base-trained, attention only) and 1 blank.
- Bars: VOID if REF at sigma = 0 recovers mean C_all < 0.5 S' (fix display on bank only, re-declare citing the abort, read no model arm). Small seal: S' < 30 -> add 0841 windows >= 128 vox from J (references only, sealed before render) until S' >= 30 if the segments allow, else run at S' >= 20 with p_max < 0.005; S' < 20 -> VOID, defer to KTLB-4-0841. PASS (= USABLE): best of BASE/RAW summed mean C_net >= 0.30 S'; p_max < 0.01; C_all >= C_all(CHANCE) + 0.20 S'; mean F_B <= 2 in every window; <= 1 naming on blanks; then 3 fresh confirmation passes with mean C_net >= 0.25 S'. FAIL: C_net <= 0.10 S' or p_max >= 0.05. BETWEEN: 5 more passes pooled; net >= 0.20 S' with pooled p < 0.005 -> LOCATOR (presence and baseline only, never letter claims); else FAIL.
- Default: FAIL if unresolved 24 h after the D1 date in D0-HW.
- Consequence: PASS -> Route Z starts at once with that arm. D2 runs regardless. J decisions used: 1 of 3.

## DECL-D2
- utc: 2026-09-24T21:57:27Z
- prev_sha256: c98f6fe64ecb0627836ac35f4350bed39c63781cbe8baf26a8612b2f4a36d356
- kind: declaration
D2 = TRAIN-1, pooled leave-one-scroll-out (section 6.4), with D2b.
- Hypothesis: native 9 um input with 2.4 um targets, pooled over JULY-protocol scrolls, with letter-scale context and rotations, makes unseen scrolls legible above chance.
- Pairs: native 9 um -n 31 render of an organizer mesh + the organizer high-res map via an affine fitted from meshes in both frames; keep a patch only if 9 vs 2.4 um CT NCC >= 0.8 and >= 7 of 9 windows align within 1 px; ink >= 150, blank <= 100, rest ignored.
- Data: 0139 (minus clean controls and neighbours); 0814; 0332 and 0500P2 once confirmed; 0841 organizer segments outside T/C4/K shells only in the non-0841 fold (checkpoint quarantined from every 0841 set).
- Folds: L-0841 (no 0841 data; evaluated on J, plus KTLB-4-0841 if sealed); L-0500P2 or L-0332 if that scroll passes its protocol check and its seal gives S >= 30.
- Arms per fold: P128 (base recipe, batch 32, 12k steps, 24 x 15 deg rotations); P384 (384 px tiles); NULL (P384, shuffled labels); REV (P384, depth-flipped). 3 seeds per arm; seed 1 read; seed variance on pixel metrics. Base reference arm.
- Bars: PASS: best arm C_net >= base + max(3, 0.1 S) with p_max < 0.01 on every fold that ran; NULL, REV <= base + 1; F_B <= base + 1; blanks <= 1; w053 blob-f180 <= 0.0272; KTLB-4-0841 >= base + 2 net (if not sealed with S >= 30 by the D2 date: the other fold's benchmark; if neither exists: decide on J alone with p_max < 0.005). USABLE: PASS plus absolute C_net >= 0.30 S on >= 1 fold. ALARM: NULL or REV >= base + 2 -> recipe shelved, results voided. FAIL: anything else.
- On USABLE: final reader R1 trained once (fixed seed, frozen config) on all JULY known text outside T, C4, K shells (+128 vox) and outside READ-CAL and clean-control windows.
- D2b (only follow-up; only if D2 fails but P384 beats P128 by >= max(3, 0.1 S) net): 512 px tiles, soft teacher targets + clDice, NULL and REV controls, on a FRESH sealed set.
- Default: FAIL at 24 h past the D2 date in D0-HW. If no GPU is provisioned by 2026-11-15, D2 is recorded NOT RUN (never FAIL, since no data exist) and counts as not-passed for K1.
- J decisions used: 2 of 3.

## DECL-DEVLOOP
- utc: 2026-09-24T21:57:27Z
- prev_sha256: bf557c265b90785ae03bf665279969097b8fa32fcebffb7613b8b8e3bd4ddba3
- kind: declaration
DEV-LOOP metric (section 6.5), declared before any DEV data exists.
- DEV data: known text outside every sealed set, fold K, T/C4 shells and base-training papyrus, KD-tree certified (clean 0139, 0814 per-arm hold-out, 0009B outside KTLB-M, 0332/0500P2/1451 once confirmed).
- Metric: sigma_eq = the Gaussian blur sigma (mm) of the 2.4 um reference map that maximises Pearson r with the text-order model map on DEV windows (grid 0.00-0.60 mm in 0.025 mm steps, after registration, computed by code hashed in a METRIC-HASH entry before first use). Constraint: non-text-order blob-f180 on DEV blanks <= 0.0272.
- FINALIST: sigma_eq <= sigma_crit + 0.05 mm on >= 3 DEV scrolls. DEV ranks only; letters are claimed only from sealed blind reads. <= 2 finalists + NULL + REV + reference arm per sealed decision (K6).
- Default: no finalist.

## DECL-D3D4
- utc: 2026-09-24T21:57:27Z
- prev_sha256: 42f0435f4c2be0cb037605b342140650f2bda771a8ef11ffdb4094fd766861b8
- kind: declaration
D3 = FOLD-0841 and D4 = BOOTSTRAP-T (section 6.6).
D3: CTRL = D2's L-0841 winner, or base if D2 failed or did not run. Fold A = 0841 papyrus >= 128 vox from every sealed window, needing >= 280 text patches, else INFEASIBLE (= not passed). Arms: FA (CTRL + 2000 steps, 50/50 batches, fold-A teacher labels); NULLA; REVA; CTRL (equal steps, no new labels). PASS: FA >= CTRL + max(3, 0.1 S') with p_max < 0.01; NULLA, REVA <= CTRL + 1; F_B <= CTRL + 1; no window > 1 below CTRL; w053 blob-f180 <= 0.0272. LABEL-EQUIV reported. J decisions used: 3 of 3; J then retires.
D4: on KTLB-4-0841 (INFEASIBLE if unsealed). Arms: PLA (labels from CTRL's own fold-A map: ink = text order >= its 92nd percentile with other order <= its 60th; blank = text order <= its 40th; no morphology), PLA-REV, CTRL. PASS: PLA >= CTRL + max(2, 0.05 S) with p_max < 0.01 and PLA-REV <= CTRL + 1.
Route F runs only if D3 AND D4 pass. Default for both: not passed at 24 h past their dates in D0-HW.

## DECL-TSURF
- utc: 2026-09-24T21:57:27Z
- prev_sha256: 18fdd7a0cae3ff4ce4179e403e0324990c819e5a42ba9de7e30bb752a3415e9d
- kind: declaration
T-SURF gates T0, T1, T2 (section 6.9).
T0: test set = the 5 GATE-TRACER-VERSION seeds of PHerc1203 team segments auto_grown_20250923163217042, ...163219195, ...163223390, ...163227956, ...163230146 (seeds and team parameters from each meta.json), run ONCE per gated build; dev set = other 1203 team surfaces from the 2025 build. Presets per gated build: reject_dist_th 1.5, 2.0, 2.5, compactness on. Bars: median crossings <= 5 /cm^2; median v2 area >= 3.0 cm^2; >= 85 % of edges within +-10 % of step; median >= 0.70 of vertices within 3 vox of the team surface AND >= half-pitch-shifted control + 0.25 (a miss on this item alone is recorded as such, E3). Either gated build passing qualifies. Fallbacks if both fail: (1) displacement arm only if official checkpoints exist (same bars + >= 0.70 of the 0841 organizer mesh area reproduced within 2 vox); (2) else be09a85 with v2 truncation at 45 generations, >= 200 seeds per volume, cores >= 1 cm^2 read at a*.
T1: 0125, 12 seeds x 60 generations; median core >= 2.0 cm^2 and >= 4 of 12 >= 2 cm^2.
T2: 3 seeds each on 0841 (>= 128 vox from J, C4, K; numeric results only, never displayed) and 0139; NCC >= 0.80 vs organizer SV and reader-map r >= 0.80 on the overlap for >= 2 of 3 per scroll.
Read gates (E4): 0 crossings; >= 4 cm^2 to read (>= 1 for coverage); mean |n_z| <= 0.50; frac(|n_z| > 0.7) <= 0.25; < 10 % on CT == 0.
Defaults: not passed at 24 h past their dates in D0-HW.

## DECL-CHAINVALID
- utc: 2026-09-24T21:57:27Z
- prev_sha256: 29f854d6d1fe5e380d731c2cb1bb010e12e0703b8570c21aa8aa375dafcae348
- kind: declaration
CHAIN VALID (section 6.7.2) and 0841 registration (6.7.1).
Registration 9.366 <-> 2.403 um per C6 (F = 9.366/2.403 from metadata): bar median r >= 0.85 and RMS <= 1.5 vox on 16 NEW check patches.
CHAIN VALID: our 2.4 um chain (C5) in both orders on 0841 organizer segment areas outside T, C4, K shells vs organizer map and human labels. Bar: r >= 0.60 and AUC >= 0.90 in one order, other order AUC <= 0.60; records rule R on 0841. If the reference model trained on 0841 labels (unresolved), this is a chain check only.
GATE-E2E-0139 (2.4 um K0): C5 chain on 0139 reproduces REVERSE r >= 0.60 and AUC >= 0.90 on the team text-window overlaps, FORWARD AUC <= 0.60.
Default: not passed at 24 h past the date in D0-HW.

## DECL-ASTAR
- utc: 2026-09-24T21:57:27Z
- prev_sha256: 35f48ef93ca29f0435d931a16ca8deeb579115ea83e29a2af8c0c82eac1a9d8a
- kind: declaration
a* (section 6.8.6): fresh blind readers answer "rows Y/N, which order?" on shuffled base-map tiles of base-clean known text (0139 w024/w047/w053/title; 0500P2/0332 once confirmed; 0841 outside T/C4/K only after D1 is recorded) and blanks; classes TEXT, BLANK, DAMAGE-LIKE; sizes 0.5, 1, 2, 4 cm^2; >= 100 tiles per class per size where material allows. a* = smallest size with sensitivity >= 0.8 at FPR <= 0.1, each scroll >= 0.7. No machine screens. Default: a* undefined (presence reading does not start).

## DECL-TRESCAN
- utc: 2026-09-24T21:57:27Z
- prev_sha256: 58c9cbe86fdc55e58663fac2663a294b58e2651c474d3b92e798719f015cd581
- kind: declaration
T-RESCAN (section 6.13), after CHAIN VALID.
Rebuild affines per C6 (incl. 0846A tilt). Trace 150 mid-radius seeds per band with the gated build; expand the 1203 team meshes into the band. Commit each band's 9 um calls and candidate list from the Route Z cache BEFORE opening any 2.4 um result (I11). 2.4 um chain both orders, order from rule R on 0841. Read 2 x 2 cm tiles at 1/4-1/8 scale, both orders side by side; 3 fresh readers; batches <= 8 + an 0841 positive + 1 blank.
TEXT FOUND: one tile with >= 5 letters in rows in one order only, same identity within 150 px from >= 2 of 3 readers, net of the in-band empirical null; opposite order <= 1; reproduced by an independent overlapping core. BAND NEGATIVE: >= 300 cm^2 clean in-band surface (>= 40 % at wrap 0.35-0.70) in valid batches with 0 text tiles ("no text found by this reader"). Otherwise extend once to 600 cm^2.
Default: neither (band UNRESOLVED) at 24 h past the date in D0-HW.

## DECL-TMAY
- utc: 2026-09-24T21:57:27Z
- prev_sha256: 8715743b86406c8aaca465d86adf63e5dead573c4272b4e3a5a0444ef0bb48c9
- kind: declaration
T-MAY (section 6.14). D-M1: base and RAW on KTLB-M (0009B, 2.401 um labels, per-segment shifts) under D1's bars (R1 and finalists added when they exist). 1451: if a 2.399 um volume and lasagna are confirmed, trace <= 60 cm^2 in its band, teacher gate at CHAIN VALID level, passing windows join KTLB-M. Cut-off: KTLB-M S < 30, or no USABLE reader on it by 2026-10-31 -> the 12 MAY volumes leave the reader programme (RAW presence reading continues). Default: cut-off applies.

## DECL-SG
- utc: 2026-09-24T21:57:28Z
- prev_sha256: f591a87d2bf6825cb933525c91a480b7bd8ca586ea5e74cacef0d31d1df85137
- kind: declaration
SG, the submission gate (section 9.1), declared now, never lowered. R = a 4.00 cm^2 +-1 % rectangle, aspect <= 2:1, computed by code from the discovery namings and declared before confirmation reads. All must hold:
0. The arm whose display produced R holds USABLE status on a sealed known-text benchmark of the same scan protocol, recorded before the discovery read. LOCATOR or failed arms may nominate a region, never supply SG reads.
1. (a) >= 12 letters named with the same identity within 150 px by >= 2 of 3 fresh blind readers; (b) >= 8 of them firm for >= 2 readers; (c) agreed count minus the 99th percentile of agreed counts over >= 40 empirical-null tiles >= 10, and agreed count > the null maximum; (d) between-reader identity-shuffle p < 0.01/m on confirmation reads only (m = candidates escalated on this scroll so far).
2. A sealed known-text positive in the same batch reaches >= 70 % of its REF ceiling and a blank gets <= 1 naming; else void and re-read.
3. Opposite order: <= 2 namings in R.
4. +-1 slice: >= 80 % re-confirmed.
5. Second lineage (different seed AND fold, never trained on this scroll) names >= 50 % at the same places (150 px). Base counts only if base is USABLE.
6. Independent re-trace (>= 60 % overlap) reproduces >= 50 %; a contradicting neighbouring sheet vetoes.
7. Copy test: no letter has NCC >= 0.8 with any training-label patch at any 15 deg rotation step.
8. FL-09 certificate: every pixel of R >= 128 vox + 64 px halo from every training patch, all windings and re-traces.
9. If trained on this scroll: NULL, REV and CTRL each <= 1 letter in R.
10. Mesh: 0 crossings in R; >= 93.1 % of quads within +-5 % on R's own flattening (FLAT-1); trimming by a coded rule fixed before the flattened render is viewed, never inside R's rows; one sheet: letter depth profiles peak within +-3 slices of n//2, winding index constant within 0.3 where lasagna exists, adjacent m7 sheets >= half the local pitch from the rendered surface throughout R.
11. >= 2 rows whose fitted baselines lie within 10 deg of the render horizontal; row-pitch CV <= 20 %; script-measured letter heights 2-4 mm.
12. Handedness formula passed its tests for this z direction; asymmetric letters present read unmirrored.
13. Inside the 1203/0846A band only: after R is frozen, fresh sealers name letters on the 2.4 um map blind to the 9 um namings; >= 50 % of SG letters confirmed (same kind within 250 px), else ALARM and no submission.
14. A 15 deg render rotation keeps >= 50 % of the letters; the RAW-F/B profile is consistent with the text order; every metric above passed its unit tests.
K7: no form unless SG 0-14 all pass and the owner is present.

## DECL-FACTORY
- utc: 2026-09-24T21:57:28Z
- prev_sha256: 402a096f25e3126fbaa262228bcfa4d9998a960855f63469df8003c01c6d3690
- kind: declaration
T-FACTORY and FLAT-1 (section 9.3).
Dry run under packages/dryrun/ only, on a bank window outside every sealed set, stamped DRY RUN, in two versions (base map; reference as ideal-reader stand-in).
FLAT-1: on 5 bank meshes cut to 4.00 cm^2 rectangles compare vc_flatten (ABF++), libigl SLIM and ARAP on the levelled tifxyz. Metric: % of quads whose edges all lie within +-5 % of their 3-D lengths. Adopt the first method with >= 93.1 % on >= 4 of 5; else crop to R + 2 mm margin, SLIM, then trim distorted quads outside the letters by a coded rule.
Factory bars: (a) verifier passes; (b) a fresh agent rebuilds the image from the tarball and README alone within 4 h: CT byte-identical, map Pearson >= 0.999, <= 2 grey levels; (c) 0 of >= 40 null tiles reach SG 1; (d) on the reference stand-ins readers confirm >= 70 % of sealed letters in >= 4 of 5 windows. Pass -> freeze container v1. Default: not passed.

## DECL-EMPNULL
- utc: 2026-09-24T21:57:28Z
- prev_sha256: 9b7b6f8625ef63fe72094b1f6448cc41749572ce942e5a6fa615b70a2377a115
- kind: declaration
Empirical null and discovery calibration (sections 6.10, 8.2).
Empirical null for an eligible candidate: >= 40 matched null tiles read with the same D*, P*, reader mix and batches by fresh readers: R's non-text-order map; R's NULL-arm map; R re-rendered half a local pitch off-sheet; >= 20 same-volume, same-radius-band tiles in the non-text order. Where two reader model versions exist, every SG and discovery read uses at least one of each.
Discovery rule: >= 2 of 3 readers name >= k letters of the same identity within 150 px in the text order (agreed count >= k), with the non-text-order agreed count <= 1; k = 5 initially. Before Route Z starts the rule is applied to >= 200 empirical-null tiles; if its false-discovery rate > 1 %, k rises by 1 until <= 1 %.
TRIBUNAL in every batch: positive canaries rows found >= 0.8 and letter recall >= 0.5 of their REF ceiling; baits <= 0.5 named letters per 4 cm^2, 0 firm; mirror detection >= 0.8; planted faults caught by code 100 % (8 px offset, swapped order, mirrored render, off-by-one slice, window re-traced by a training segment, wrong voxel size). A failed canary voids the batch; > 1/3 void batches in a run halts reading (I16).

## DECL-KILL
- utc: 2026-09-24T21:57:28Z
- prev_sha256: 4c76193f62592943ae8185f1ba5bf8eb87444e9d4d9bda4bb4a9968d51cc6e93
- kind: declaration
Kill and pivot criteria (section 7), declared day 0.
K0: a per-chain gate fails -> blocks only reads using that component. 9 um reads need C3, level_mesh and slice-index tests, scorer synthetic test, seal hash, READ-CAL frozen. GATE-E2E-0139 gates only CHAIN VALID, T-RESCAN, KTLB-4-0841 and SG 13. Factory gates only SG and the package.
K1 JULY: D1 not PASS AND D2 (and D2b if triggered) FAIL/ALARM/NOT RUN AND D3 not passed -> close JULY letter reading with current models and Route F; RAW presence reading and DEV-LOOP continue; each new finalist gets a freshly sealed decision.
K1 MAY: KTLB-M not passed by 2026-10-31 -> MAY volumes leave the reader programme.
K2 surfaces: by 2026-10-15, T0 failed for both gated builds and fallbacks and the census gives < 3 JULY volumes with >= 2 clean cores >= a*, or no a* <= 4 cm^2 exists -> read what exists; trial spiral and lasagna under the same bars; if they fail on > 2/3 of volumes, watch mode for surfaces.
K3: every ranked volume PARKED, or no FOOTHOLD by 2026-12-31 -> watch mode.
K4: no replicated foothold by 2027-02-28 -> no new routes; no fold-C prediction with >= 10 letters by 2027-05-15 -> stop and prepare the negative report.
K5 integrity: I16.
K6 forking: <= 4 candidate arms + 1 reference arm per decision; <= 3 decisions per sealed benchmark (J: D1, D2, D3, then retired); p over every arm read.
K7 claim: no form unless SG 0-14 all pass and the owner is present.
Early watch: K1 applies, every volume parked at >= 150 cm^2, both bands BAND NEGATIVE -> watch mode on 2026-11-15.

## D0-KNOWN-TEXT
- utc: 2026-09-24T22:06:13Z
- prev_sha256: f3887bb2e154e2ba73ae54b0cab6713010ae2fc7d9b4f5cc169cae869216d737
- kind: correction
Day-0 known-text and checkpoint catalogue (agent report 2026-09-24; data/catalogue/known_text.md, known_text.json, checkpoints.json, rescans.json with sha256 of every fetched source). Corrections to the section 4 fact sheet (I17) and facts now governing:
1. PHerc0139 has 39 segments (38 with 2.399 um ink maps on volume 20260102150214, 1 mesh-only), not 38. Official human labels label_set 20260918: 8 segments on 2.399 um and 5 on 9.362 um (w035, w039, w040, w041, w044).
2. PHerc0841: 9.366 um 20250821151531 and 2.403 um 20260319124803 confirmed, no transform.json, but the bucket root index holds a 2.403 <-> 9.366 um affine (7 landmarks) and every segment has a 2.403 um mesh made with it. The 3 segment IDs match. Ink maps (model 20260417190342) exist on the 2.403 um canvas only. Official human labels label_set 20260918 (inklabels / supervision / validation zarr) exist on 2.403 um for all 3 segments. m7 prediction and normal grids exist for the 9 um volume. 2.4 um surface volumes are ~32 GB per segment (not fetchable here); 9 um SVs ~0.6 GB.
3. PHerc0009B: besides 2.401 um 20250820154339 there is a second 2.401 um export 20260319104112 (indexed as a fragment). No m7 on the 8.64 um volume. PHerc0343P: 8 segments, no m7 on the 8.64 um volume.
4. Protocols (field by field): 0500P2 (20250820143440) and 0814 (20250804134230) match JULY on all 8 fields; 1451 (20250521151225) matches MAY on all 5 fields (no registration to its 2.399 um volume, no indexed segments); 0332 matches neither (2023 DLS scans and a Dec-2025 2.399 um scan only). Under D0-SETTLED item 3: 0500P2 is a held-out JULY scroll candidate (KTLB-4P); 0332 is not a JULY scroll and is excluded from JULY training and benchmarks.
5. Rescans: only 1203 (20260319130212) and 0846A (20260319102732), 2.403 um, ~36 mm bands, each with m7, neither registered to its 9 um volume. No other eligible scroll has a rescan.
6. Spiral tracks on the exact eligible volume ID: 18 of 23 (missing 0846B, 1203, 1218, 1447, 1545). Resolves D0-CONFLICTS item 6. Live path dl.ash2txt.org/datasets/spiral_datasets/.
7. Checkpoints (HF, public, not gated): ink_9um step-075000 138,360,039 B sha256 e635558a...9cab MIT (model card); ink_canonical_2um r152_3ddec_v2_l5_epoch13.ckpt 1,549,556,213 B sha256 36dd0de8... MIT; timesformer_scroll5_27112024 455,711,244 B sha256 3c6b0b4d... MIT; human labels bucket scrollprize/datasets ink_9um (aligned 24 segments, native9 5 segments) licence UNVERIFIED.
8. NEWER official ink checkpoint: scrollprize/hecate (commit 9cb86e50, 2026-09-15; MIT LICENSE file; labelled experimental; distilled from ink_canonical_2um): hecate_9.6um.pth 522,576,086 B sha256 809f4f10f7cb7afa19b4bee0f7d2ab31edd7e11b664f9f210cc9c17f22fcfe5d (expects renders resampled to 9.6 um in all axes) and hecate_2.4um.pth sha256 fa2de382.... This triggers a decision within 48 h (section 11.1): see DECL-HECATE. Section 4.D5 records an archive result "Hecate 9.6 (0.522)" of unknown benchmark and version; it is archive-only and not re-used as evidence.
9. Displacement checkpoints extrap_displacement_latest (sha256 662f8065...) and copy_displacement_latest (sha256 22cf4392...) are public but carry NO licence statement. They may be used only as the T0 fallback-(1) research arm; nothing derived from them enters a package unless a permissive licence is published (section 9.2 licence item).

## DECL-HECATE
- utc: 2026-09-24T22:06:13Z
- prev_sha256: 194cbfb2cd774534336f857c22ae8c1e465846594b6bba28bef73af2f2e2227f
- kind: declaration
Decision on the newer official checkpoint Hecate 9.6 um (sha256 809f4f10f7cb7afa19b4bee0f7d2ab31edd7e11b664f9f210cc9c17f22fcfe5d), within 48 h of its discovery (2026-09-24).
- Hypothesis: Hecate 9.6 um reads PHerc0841 ink well enough at pixel level to merit a D1 candidate arm.
- Screen (a gate, never evidence of letters, I14): Hecate zero-shot on renders of the 3 PHerc0841 organizer segments resampled to 9.6 um in all axes as its model card requires, using the official inference code or its documented recipe; both depth orders. Pixels: organizer-segment area outside the T shell (J windows + 128 vox) only. Metric: AUC (src/hercules/metrics/pixel.py, METRIC-HASH-0) against the official 0841 human labels label_set 20260918 mapped to the 9 um canvas (ink = labelled ink, blank = labelled non-ink where the label zarr distinguishes them; else ink = label > 0, blank = reference map <= 100); base computed on the same pixels the same way.
- Bar: Hecate best-order AUC >= 0.75 AND >= base best-order AUC - 0.02 -> HECATE joins D1 as a third candidate arm (family {BASE, RAW, HECATE}; K6 respected), its own text order chosen once by the D1 rule from Hecate-vs-reference AUC (conventions are never transferred between checkpoints). Otherwise HECATE is recorded "screened out on 0841 at AUC x" and no reads are spent.
- Default: screened out, if the screen is not complete when the first D1 model-arm reader starts; D1 is not delayed by more than 24 h for it.
- Section 6.0.3 is unchanged: Hecate weights never initialise a 9 um model evaluated on 0841.

## METRIC-HASH-1
- utc: 2026-09-24T22:06:31Z
- prev_sha256: 1899151a35d6f734040206fbd9c29c3e8a6d70d2fb4828ec4622c224f07324e8
- kind: metric-hash
Code hashes added after METRIC-HASH-0 (registration C6, 18 tests; scorer key access, 1 test):

```
1163ba54d9ac724af796e67b08309fe04dbe7e6487a9966f0ab88ec1a506467c  src/hercules/registration/__init__.py
d1e4158288b59513a58eb78a8f2d3c606fcbede8bdc27dec15e8c105062ba2e8  src/hercules/registration/c6.py
7791491711b9ebcf3fb9a9523b1b90b537e7e8a3ca7ec1a4ddf3daa6e9b1255a  src/hercules/registration/synthetic.py
63872b3c2140647271eee228b9c45f6bcf128ffabe7920fb635cf396c05d70c7  src/hercules/scorer/keyaccess.py
combined_sha256 7e87358ee5a8a0526910125f142c887fc2127325a18f758e9b70ef2e538c1093
```

## HARNESS-COORD
- utc: 2026-09-24T22:08:33Z
- prev_sha256: c0686f3c24f0c74fc0438ffd86f58e1ca50303a090eea2cc4bfec00a526e792b
- kind: result
Harness coordinate-fidelity test (synthetic, 2026-09-24; Explore readers, transcripts audited VALID: one Read of the listed image + hand-back). Two font-rendered images of 12 Greek capitals with Gaussian noise, known glyph centres (/work/harness_coord_truth.json, not committed).
- 1068 x 1068 px image: 12/12 letters named correctly; centre error median 0.7 px, max 2.5 px; fitted scale 1.000 (x and y).
- 2136 x 2136 px image: 12/12 named correctly; centre error median 57.5 px, max 82.0 px; fitted scale 0.966 (x), 0.964 (y): the image reaching the reader was resampled by the harness (method unknown) and coordinates came back in a shrunken frame.
Consequences: (1) every image shown to a picker, sealer or reader is at most 1068 px on each side, so the harness never resamples it (an unknown resampling would also break I2's area-mean-only rule); (2) the section 6.2 D1S layout (2 x 0.6 cm strips at full scale = 2136 x 641 px) cannot be shown as specified: see DECL-READCAL-A1. Clean synthetic glyphs say nothing about CT legibility.

## DECL-READCAL-A1
- utc: 2026-09-24T22:08:33Z
- prev_sha256: 1f6121fe89ccfb5781b8b70e64f63ac2007d5ae4ef392f334f7b25648fbc0e1c
- kind: declaration
Amendment to DECL-READCAL before any READ-CAL data exists, citing the recorded defect in HARNESS-COORD (images larger than 1068 px per side are resampled by the harness by an unknown method and their coordinates return in a shrunken frame).
- Every reader, sealer and picker image is at most 1068 x 1068 px.
- D2 unchanged (2 x 2 cm window at 1/2 scale = 1068 px at 9.366 um). D1Q unchanged (1 x 1 cm tiles at full scale, 0.5 cm stride, 3 x 3 = 9 tiles per window). D1S becomes 1.0 x 0.6 cm row strips at full scale (1068 x 641 px at 9.366 um), stride 0.5 cm horizontally and 0.4 cm vertically, last strip flush with the window edge (3 x 5 = 15 strips per 2 x 2 cm window).
- At 8.640 um the same cm sizes give 1157 px: MAY displays use tiles of at most 1068 px (0.923 cm at full scale, or the declared cm size at the largest scale <= 1068 px), fixed before any MAY read.
- Bars, metric and default unchanged.

## METRIC-HASH-2
- utc: 2026-09-24T22:08:49Z
- prev_sha256: cc354cef22e35eac8de0b19cc68ecdec69b8175fcea532d5b283b482df90ff31
- kind: metric-hash
Display builder amended per DECL-READCAL-A1 (D1S 1.0 x 0.6 cm strips; hard cap 1068 px per side). New hash, replacing the METRIC-HASH-0 value for this file:

```
ed42725e878c4e8c99aae98d24316cb39477ebc2c35308d43176fa22a8be7f8a  src/hercules/display/builder.py
```

## B0841-BANK
- utc: 2026-09-24T22:48:43Z
- prev_sha256: bdd8c060fc586fa3a493f9dc7de3337bd588f3d9b5f52f25d6f45ebebd88aca3
- kind: result
PHerc0841 bank built (agent report; /work/bank/0841/manifest.json hashes 4147 files, 3.67 GB; numbers-only summary logs/bank0841/summary.json). No image was viewed by anyone.
- Canvases: N9 = mesh grid x 20 = SV shape for the `<id>-on-20250821151531` meshes (the catalogue's `tifxyz_original` has a different grid). N2/N9 per axis within 0.07 % of F = 3.897628. Organizer 9 um SVs have 28 slices; the official renderer centre is 0.5 (n - 1), so the surface lies between slices 13 and 14.
- Reference and label mapping 2.403 -> 9.366 um: exact separable area average with c9 = (c2 + 10) N9/N2 - 10; synthetic test error 0.012 px. The meshes imply an offset of 10.49-10.51 rather than 10 (a 0.37 px difference, negligible against the 150/250 px matching radii); the declared formula is kept.
- Diagnostic (not the D1 gate, which compares OUR render with the organizer SV): cross-resolution CT NCC between the mapped 2.4 um surface slice and the 9 um SV mean of slices 13-14: whole segments 0.763-0.770 at zero shift (best 0.768-0.778 at shift (1, 0)); windows J1 0.776 -> 0.821, J2 0.723 -> 0.767, J3 0.758, J4 0.802 -> 0.805, J5 0.734 -> 0.782, all best shifts <= 1.41 px. The reference mapping is therefore within ~1.4 px; the NCC level reflects the different resolution and PSF of the two scans, not misregistration. The briefing wrongly labelled this check "declared gate"; it is recorded as a diagnostic only.
- Reference ink fraction (ref9 >= 150): J1 18.9 %, J2 16.9 %, J3 12.5 %, J4 12.0 %, J5 12.9 %.
- Blank windows: none on 0841 (every 2136 px window touches a J mesh point in 3-D and has >= 1 % reference ink). Per DECL-D1 the blanks come from clean 0139 w053.
- T shell (J + 128 vox, all segments): area outside it 1.51 / 1.52 / 1.26 cm^2 (w00 / 214732 / 022814) holding 0.084 / 0.110 / 0.054 cm^2 of reference text (total 0.248 < 0.5 cm^2). Per DECL-D1 the text order is therefore chosen from AUC pooled over all J windows.
- Corrections (I17): 214732 lies a median 8.4 vox from w00 with only 5 % of points within 2 vox (section 4.B7 called them two traces of one sheet; at a local pitch of ~8-18 vox they may be adjacent windings: UNRESOLVED, pitch to be measured locally). The official 0841 label layers are uint8 {0, 255}; "validation" is the data-coverage mask (IoU 0.997 with coverage), not a held-out split; 12 % of w00 ink pixels lie outside "supervision".

## DECL-HANDED
- utc: 2026-09-24T22:49:49Z
- prev_sha256: f3ee2b6a9ffcb79024411b8a142deb3215d4864b19a9b29cafe4a9b46f68028c
- kind: declaration
Handedness convention test on PHerc0139 (section 5.2 real-data test), declared before any of its data exists.
- Material: 4 windows (1 x 1 cm, 1068 px at full 9.362 um scale) on base-trained, non-clean 0139 segments that are in no READ-CAL, canary or sealed set (chosen by code: the 4 windows with the highest fraction of valid reference coverage on w041 and w039; never chosen by viewing).
- Arms: the official 2.399 um reference map mapped to the 9 um canvas, levelled, and shown in state A = orient_for_reading with convention_sign = +1, and state B = state A mirrored in u. No CT, no model map.
- Readers: 3 fresh blind readers (harness per DECL-HARNESS), each seeing all 4 windows as LEFT/RIGHT pairs (A/B side randomised per window by the display builder; key held by the scorer). Brief: "One image of each pair is mirror-reversed. Say which side shows normally oriented writing, then list the letters you can identify in that side."
- Metric: votes = 12 (3 readers x 4 windows); a vote is for A or B.
- Bar: >= 10 of 12 votes for one state -> convention_sign fixed for ascending-z JULY scans (+1 if A, -1 if B); otherwise AMBIGUOUS -> every 9 um read renders both mirror states as separate declared arms until a re-test on 4 new windows passes.
- The descending-z convention (0009B) is tested the same way before any MAY or descending-z read.
- Default: AMBIGUOUS.

## DECL-SEAL
- utc: 2026-09-24T22:49:49Z
- prev_sha256: dbc7ad7e2f9934432848ab6b258c0ca80dacff3763a898bcfc3491f26b19f537
- kind: declaration
Seal protocol for every sealed set (J re-seal, READ-CAL, canaries, later KTLB-4 sets), declared before any seal exists.
- Picker: one fresh blind agent (harness per DECL-HARNESS) sees only reference-map images (no CT, no model maps) at most 1068 px per side; it verifies or chooses windows by nameable letters only (never by ink density or any 9 um map) and reports text extents. It never reads again.
- Sealer display: the reference map resampled onto the LEVELLED, reading-oriented canvas (pipeline window maps; bilinear geometric resampling, raw 0-255 probabilities, no contrast change), the 2 x 2 cm window at 1/2 scale by INTER_AREA (1068 px); one image per window; window order randomised per sealer.
- Sealers: 3 fresh blind agents per set, each naming every letter with centre, box and firm/tentative (brief template configs/briefs/sealer.txt, hashed before use). Consensus by hercules.scorer.consensus.make_seal: same identity within 150 px (canvas px of the levelled canvas) from >= 2 of 3 sealers; firm = 3/3, or 2/3 both firm. Where official human ink labels exist (0841 label_set 20260918), a seal letter's position is replaced by the centroid of labelled ink pixels inside the union of the agreeing sealers' boxes (unchanged if that union holds no labelled ink).
- Blank windows: the picker confirms no writing; a blank seal is a seal with blank = true and no letters.
- Output: per set, one canonical JSON (letters in levelled-canvas px plus their organizer-canvas coordinates, sealer agreement statistics, S') encrypted with age to the scorer recipient; its sha256 appended to RULES.md and committed and pushed BEFORE any render of its windows exists. Plaintext never touches the repository; sealer outputs are kept only encrypted with the seal.
- The orchestrator never views picker or sealer images, sealer outputs or seals; it sees only S' and agreement statistics.

## DECL-D1-A1
- utc: 2026-09-24T22:49:49Z
- prev_sha256: 3b3039f6471a971737fff16a72335e37af3113956fa89a82bc8982977dcd2423
- kind: declaration
Amendment to DECL-D1 before any D1 data exists (pinning details the declaration left open):
- Alignment gate: OUR levelled -n 31 render, slice n//2 (offset 0 from the surface), mapped onto the organizer canvas, versus the organizer SV mean of slices 13 and 14 (offsets -0.5 and +0.5 about its surface, 28-slice SV), NCC at integer shifts within +-5 px over the window; PASS iff best NCC >= 0.80 at |shift| <= 2 px (pipeline alignment_gate, hashed before use).
- Windows: each J window is the 2136 x 2136 px square of the levelled canvas centred on the image of the organizer window centre; seals, displays and scoring use levelled-canvas coordinates.
- Blanks: 2 windows from clean 0139 w053 (B0841-BANK found no qualifying 0841 blank), outside every READ-CAL window + 128 vox.
- Text order: pooled over all J windows (B0841-BANK: 0.248 cm^2 of reference text outside the T shell, < 0.5 cm^2).
- Handedness: per DECL-HANDED; if AMBIGUOUS, both mirror states are rendered and read as separate arms of the same family.

## RCBANK-1
- utc: 2026-09-24T23:17:06Z
- prev_sha256: 99312a601cfcefc95be8b25ec093a4353ce16ab406f91be1a33c469fd15bca85
- kind: result
READ-CAL bank attempt 1 (agent report; /work/readcal, summary logs/readcal/summary.json). No image viewed.
- Segments: w024 = 20260215000000-w024_2026021572, w047 = 20260206000001-w047_2026020613, w053 = 20260220000000-w053_2026022021; title = 20260422000000-title_2026042222_zmid_flatboi (canvas 5360 x 1780 px = 1.67 cm tall: no 2 x 2 cm window fits). CLEAN-4 window "s130642_y3360_x2480" matches no PHerc0139 segment (the only official id ending 130642 is PHerc0009B 20250919130642): UNRESOLVED.
- 2.399 -> 9.362 um reference mapping with the labelmap formula: no flip (CT NCC 0.61-0.71 unflipped vs <= 0.012 flipped); residual median <= 0.7 px, worst 2.5 px (title ~1.6 px in y). Plain scaling is 7.4 px off (matches the archived ~75 um warning); the formula removes it.
- Same-papyrus KD-tree test (>= 1000 vox^2 within 6 vox Euclidean and 2 vox normal, count(dn < 1) >= 2 count(2 <= dn < 3)): w024 re-traced by w023 (2.87e6 vox^2) and w025 (2.31e6 vox^2), neither in base training; w053 re-traced by w052 (5.02e6) and w054 (4.35e6), neither in base training; w047 re-traced by base-training w045 (1.39e5 vox^2, ~0.12 cm^2) and by w046 (1.44e5 vox^2; w046 re-traces w045). Correction (I17) to section 4.D3: w047 is NOT entirely clean for base; a ~0.12 cm^2 strip is base-training papyrus.
- Defect in the builder brief (orchestrator error): it excluded every pixel within 128 vox of any base-training or neighbour trace. Adjacent windings lie 20-40 vox apart, so this excluded 100 % of w024, w047 and w053 and left no 2 x 2 cm window. No READ-CAL rule requires a 128 vox clearance (that is the I8 rule for submission pixels versus training patches); see DECL-READCAL-A2.
- PHerc0814: 18 segments besides base-trained 46527 have official 2.399 um maps and 9 um SVs; 7 lie >= 184 vox from 46527: 20250925204843 (46 cm^2), 20250926165636 (42), 20251001060526 (32), 20250925222237 (17), 20250925212701 (11), 20260226123353 (4.2), 20260225160055 (2.7).

## DECL-READCAL-A2
- utc: 2026-09-24T23:17:06Z
- prev_sha256: e4e7ddf7792b7df3cfe2a4c30645bd3d2b1ad69340a26f14219aee5322f4a073
- kind: declaration
Amendment to DECL-READCAL before any READ-CAL reference image has been viewed by anyone, citing the defect recorded in RCBANK-1 (a builder-brief rule, not in the prompt, excluded all candidate papyrus).
- Eligible papyrus for READ-CAL windows: PHerc0139 w024, w053, w047 and the 7 PHerc0814 segments >= 184 vox from 46527 (listed in RCBANK-1), EXCLUDING (a) every canvas pixel whose 3-D point is same-papyrus (KD-tree: within 2 vox normal distance and 6 vox Euclidean) with any base-training trace (0139: w029, w030, w035, w039, w040, w041, w043, w044, w045 and their re-traces w046, and the mesh-only w030 trace; 0814: 46527 and its re-traces) plus a 64 px in-plane halo; (b) every pixel within 128 vox (3-D) of any sealed set's windows (J on 0841 is another scroll; DECL-HANDED windows on w039/w041 and future canary windows are checked by the same tool).
- Rationale: at 9 um the base model sees about +-8 vox of depth, so memorised ink lives on the same papyrus, not on windings 20-40 vox away; the 128 vox clearance remains the I8 rule for submission pixels.
- Windows: 2 x 2 cm (2136 px), >= 90 % valid reference coverage, a fully eligible footprint. The title strip (1.67 cm tall) is not used for READ-CAL.
- Selection: a fresh picker chooses >= 6 windows (target 8, at most 3 per segment) with >= 5 nameable letters from reference images only; if fewer than 6 qualify, READ-CAL runs on those that do and records the shortfall.
- Everything else in DECL-READCAL and DECL-READCAL-A1 is unchanged.

## METRIC-HASH-3
- utc: 2026-09-24T23:20:34Z
- prev_sha256: a67663f887fe48f282b89d36abc2d880b1a673dc235701ed0aaa3f7169b84506
- kind: metric-hash
Code hashes after METRIC-HASH-1/2: window pipeline (82 tests; renderer conventions cited from villa 41701aa in its docstrings) and scorer keyaccess (provenance line moved to line 1; logic unchanged). Full suite at hashing: see CHANGELOG.

```
37fa1dc2a9cd3e33a433cfd2a11bebf15d569925e36f7c47966989e344673539  src/hercules/pipeline/__init__.py
bf54ee566f8a8f6a05f68a66e23113e6d8576c8f377a1cda6dbc73283bd307d6  src/hercules/pipeline/canvas.py
f519c77a9616308ac7ff8bfb018f5d7627887782ceb26e439998324e548a5e07  src/hercules/pipeline/centre.py
b8b996dca048b720a450acbb32a87ce1ca2353467c7ef9dcfa1df6f5017c6e46  src/hercules/pipeline/smoke.py
c184c79ceb64382c05db928a7f1a90c6dee1f5db3d0b9b5ab58b714ea473609a  src/hercules/pipeline/window.py
afbde929e463c936d45ae34641910c66b1748f0b2215fc9231be2f5c91fd1e7e  src/hercules/scorer/keyaccess.py
combined_sha256 d0e884d4166d5797029aaed408bed94609b38f2e75f0b2e94dd8224987cf70b7
```

## METRIC-HASH-4
- utc: 2026-09-24T23:40:46Z
- prev_sha256: d76918554387dadaf186df0265e8ac5399f27645b2da92f632da048d28bf6910
- kind: metric-hash
Handedness vote counter (DECL-HANDED), hashed before any handedness reader output is read:

```
41e58d43c79f0e0e35ce18a9f486271fe8c8cb40141c344a119b8b1b1d5e05fb  src/hercules/scorer/handed.py
```

## HANDED-1
- utc: 2026-09-24T23:41:44Z
- prev_sha256: 3155e1c25fe0245ad52de2789b7d16a378c3c368264b6367a58b68c3fa1f431a
- kind: result
Result of DECL-HANDED (0139, ascending z). Scorer hercules.scorer.handed (METRIC-HASH-4); key /srv/scorer/handed_key.json; reader outputs /work/handed/outputs/r1-r3.json (sha256 39ef708e..., f83888ad..., 65d2e437...). 3 fresh Explore readers (model opus), transcripts audited VALID (8 Reads each + hand-back).
- Votes: A 0, B 0, no vote 12 (every pair answered UNSURE; 0 letters named in any image).
- Verdict: AMBIGUOUS (bar >= 10 of 12). Default applies: every 9 um read renders both mirror states as separate declared arms until a re-test on 4 new windows passes.
- Probable defect of the test design (orchestrator's): windows were chosen by reference coverage only (never by text), at 1 x 1 cm full scale, so they may contain no legible writing. Not yet separable from the alternative that blind readers cannot read these reference maps at all (section 4 I1 records an archive result of 0 of 14 reference letters confirmed by blind readers); READ-CAL SG-FEAS measures that directly.
- Images: 4 windows 1068 px on w041 (512, 512), (768, 1792) and w039 (2816, 512), (3072, 1792); level spreads 0.9-3.0 deg; orient() did not mirror u. No image was viewed by the orchestrator.

## DECL-HANDED-R2
- utc: 2026-09-24T23:41:44Z
- prev_sha256: 2d8f3a89216031ae253848a434c3ae0a472f26e913d168728c11406f729213c0
- kind: declaration
Handedness re-test R2 (0139, ascending z), declared before any of its data exists, citing HANDED-1 (AMBIGUOUS; windows chosen by coverage alone may hold no writing).
- Material: PHerc0139 base-trained or otherwise non-clean segments that carry official human ink labels (label_set 20260918 on 2.399 um, or the 9.362 um native9 set), excluding w024, w047, w053, w040, w044, the HANDED-1 windows and any READ-CAL, canary or sealed window (+128 vox). Windows 2 x 2 cm (2136 px at 9.362 um) chosen BY CODE as the 4 non-overlapping windows (at most 2 per segment) with the highest fraction of human-labelled ink pixels. Human-label density is used only because this test needs writing present; it is not a letter benchmark and no letter count from it is ever used as evidence.
- Display: the official reference map levelled and oriented (state A = orient_for_reading with convention_sign = +1; state B = A mirrored in u), 1/2 scale by INTER_AREA (1068 px), raw 0-255; LEFT/RIGHT randomised per window.
- Readers: 3 fresh blind readers; brief identical to DECL-HANDED except the scale sentence (2 x 2 cm patch, 53.4 px/mm, letters about 100-220 px tall).
- Bar and default as DECL-HANDED (>= 10 of 12 votes for one state; else AMBIGUOUS).

## DECL-HARNESS-A1
- utc: 2026-09-24T23:46:57Z
- prev_sha256: cb9a34eb14f0cde6f76d042b1c7f92667bec375d200d34b08a40c2c92ff0c1a3
- kind: declaration
Amendment to DECL-HARNESS before any picker, sealer or reader output of a benchmark exists, citing a recorded defect: a subagent's final answer is delivered into the orchestrator's context, and nested agents are unavailable (tested 2026-09-24: a general-purpose subagent has no agent-launch tool), so picker/sealer answers would expose seal content to the orchestrator (I5, section 3.3). One READ-CAL picker was stopped before it answered for this reason; its images were read but its answer was never delivered, and that agent is never used again.
- Sealed-output mode (mandatory for pickers, sealers and readers of any benchmark or eligible tile): the brief gives each agent one output path /work/sealed_io/<uuid>.age and the scorer's age recipient; the agent writes its JSON answer with exactly one Bash call `age -r <recipient> -o <path> <<'EOF' ... EOF` and hands back only the word DONE.
- Audit (hercules.harness.audit, sealed-output mode): VALID only if the calls are Reads of the listed images (each <= 2 times), exactly one Bash call matching that command form with the assigned path and recipient, a heredoc body that is one JSON object and contains no inner EOF line, and the hand-back. The audit never prints call content. Any other call voids the agent.
- Answers are decrypted only by scorer code (hercules.scorer.keyaccess.decrypt_logged, every read logged); the orchestrator sees only scorer aggregates (counts, S', agreement statistics, C_net, p). A hand-back containing anything other than DONE is recorded as an integrity event; if it reveals seal content, that seal is VOID and re-made with fresh sealers.
- Residual risk (disclosed in FL-14): answers exist in plaintext inside the agents' transcript files on the container (not in the repository); the orchestrator never opens transcripts except through the audit code.

## HARNESS-SEALED-TEST
- utc: 2026-09-24T23:49:40Z
- prev_sha256: d2acb8fcd89d23fab46fcda8c27706c5da32da0648879c126ec8e71d80535e42
- kind: result
Sealed-output harness live test (DECL-HARNESS-A1), synthetic 1068 px image of 12 font-rendered Greek capitals.
- Explore agent (read-only type): refused to write the answer file (its operating rules forbid file creation) and made no read: the read-only type cannot run sealed-output mode.
- general-purpose agent (model opus): tool calls exactly Read (listed image) + one Bash sealed write + hand-back "DONE"; audit VALID (the audit printed no content). Scorer-side decryption (logged in logs/key_reads.tsv): schema valid; 12/12 letters named with correct identities, centre error median 0.7 px.
- Consequence: pickers, sealers and readers run as general-purpose agents in sealed-output mode; their wider tool set is contained only by the audit (any call other than the listed Reads, the one sealed write and the hand-back voids the agent). Disclosed in FL-14.

## METRIC-HASH-5
- utc: 2026-09-24T23:49:40Z
- prev_sha256: e81e0e61a8e7269536cb7a73bac1596503df52b6c4713bd61774eb9fc4949ff0
- kind: metric-hash
Code hashes for sealed-output harness (audit v2, collector, keyaccess.decrypt_answer_logged). Suite 535 passed.

```
e36cb995aee6f54461ef8dfc3af57ecd167853c74408f2917d1cbf560426e1f1  src/hercules/harness/audit.py
349dcc1248e80f181125786985f6783dae69f941e36e6c4174ebfacd0c814c29  src/hercules/harness/collect.py
41e58d43c79f0e0e35ce18a9f486271fe8c8cb40141c344a119b8b1b1d5e05fb  src/hercules/scorer/handed.py
da63f169f080f84605683be1d4a6f9eb23b6bf36e4eff6a28012173ea914c9b2  src/hercules/scorer/keyaccess.py
combined_sha256 0afb6b7b613d42794d9c0a988e257927fa01c8e1663b4e9495c9363c8ff153bf
```

## RCPICK-1
- utc: 2026-09-24T23:55:00Z
- prev_sha256: 4571927dc275e77f885462abf49de0fc94f6eb8609a5ddf2dcfff83e96f05eea
- kind: result
READ-CAL picker, attempt under DECL-READCAL-A2 (job ffc66c11, general-purpose agent, model opus, sealed-output mode; audit VALID, 36/36 images read; answer decrypted only by scorer code; logs/readcal/picker1_counts.json holds counts only).
- Display: 33 candidate 2 x 2 cm windows of the official 2.399 um reference maps mapped to the 9.362 um canvas, 1/2 scale (1068 px), raw 0-255, unlevelled organizer canvas; plus 3 segment overviews. Image statistics (numeric, not viewed): background median ~33, 99th percentile median 229, pixels >= 150 median 4.6 % (range 1.1-59 %): the images carry signal.
- Letters named per window: w053 (24 windows): 22 windows with 0, 2 with 1; w047 (3): 2 with 1, 1 with 4; w024 (6): all 0. Firm namings: 0 in total. Rows of writing reported in 10 of 33 windows.
- Selection rule (>= 5 named letters): 0 windows qualify. Under DECL-READCAL-A2 READ-CAL has no bank window on clean 0139 at this display.
- Together with HANDED-1 (0 letters named on 4 base-trained 0139 reference windows at 1 x 1 cm full scale) and the archive's 0 of 14, the evidence so far is that blind LLM readers do not name letters in the official 0139 reference maps at 9 um-canvas scale. Not yet distinguished: reader limit, map legibility, or display scale (the maps were resampled from 2.399 um to the 9.362 um canvas and halved).
- Consequence (DECL-READCAL): STATE.md top blocker becomes "SG infeasible at current display"; READ-CAL continues with other displays and material before any SG attempt. SG bars are unchanged.

## JPICK-1
- utc: 2026-09-24T23:57:26Z
- prev_sha256: 1d011b335d97920f97346fdd2ffb31a3954f368f91a712bb58af10ad5a215344
- kind: result
J picker verification (job a27a5bc4, general-purpose agent, model opus, sealed-output mode; audit VALID; counts only in logs/bank0841/j_picker_counts.json).
- Display: the official 0841 reference maps (model 20260417190342) on the 9.366 um organizer canvas, J1-J5 at the recorded corners, 2136 px windows at 1/2 scale (1068 px), raw 0-255, unlevelled and unoriented (handedness AMBIGUOUS, HANDED-1). Numeric image check: pixels >= 150 11-16 %, 99th percentile 241-242.
- Letters named (firm): J1 0 (0), rows N; J2 3 (1); J3 1 (0); J4 7 (1); J5 4 (1). Total 15 named, 3 firm. Only J4 meets ">= 5 nameable letters".
- Comparison: the archive's J seal had S = 43 (11 firm) from 3 sealers at display D2; that seal is unavailable and was never shown to anyone here.
- Consequence: under DECL-D1, a J seal made at this display would very likely fall below S' = 30 and probably below 20 (VOID, defer to KTLB-4-0841). Sealing waits for the handedness re-test (DECL-HANDED-R2), because an unresolved mirror state may be depressing legibility; no other change is made.

## DECL-READCAL-PROBE1
- utc: 2026-09-24T23:58:42Z
- prev_sha256: b04f995a6d806d0408d92db76d6de2e09b594094aa6aa17806435c2d815d46fb
- kind: declaration
READ-CAL continuation, PROBE-1 (bank material only; calibration, never evidence of letters), declared before any of its data exists, following RCPICK-1 / JPICK-1 ("SG infeasible at current display").
- Question: at which display and reader model do blind readers agree on letters in official reference maps? The statistic is SG item 1 itself, computed on REF: agreed letters (same identity within 150 canvas px from >= 2 of 3 fresh readers), agreed-and-firm (firm for >= 2 readers), and the between-reader identity-shuffle p (hercules.scorer.consensus, METRIC-HASH-0), per window and summed.
- Material: the 4 DECL-HANDED-R2 windows (2 x 2 cm, PHerc0139 non-clean segments with official human labels; no sealed set) after R2 is scored; orientation = the R2 state if R2 decides, else both states as separate arms.
- Arms: displays {D2: whole window at 1/2 scale (1068 px); D1Q: nine 1 x 1 cm tiles at full 9.362 um scale; N2: four 0.5 x 0.5 cm tiles per window, the window's central 1 x 1 cm, at the native 2.399 um reference resolution halved (about 1040 px)} x reader models {opus, fable, sonnet}; prompt P (configs/briefs/reader_P.txt) with one image per item (right side empty). 3 fresh readers per (display, model), each reading all 4 windows of its display, sealed-output mode.
- Additional check: the fraction of agreed letters whose centre lies within 20 px of human-labelled ink (localisation), reported, not a bar.
- Decision rule: the (display, model) with the highest summed agreed count becomes the sealer display and the READ-CAL D* candidate; SG-FEAS is recorded PASSED only if that arm reaches >= 12 agreed letters with >= 8 agreed-firm in at least one window (SG 1a-1b on REF; 1c needs the empirical null and is run only if 1a-1b pass). If no arm reaches >= 5 agreed letters in any window, record "REF not blind-legible at any tested display": SG stays infeasible and every letter-reading decision (D1, D2, Route Z) is suspended until a new display or reader passes this probe on fresh windows.
- Default: SG-FEAS NOT PASSED.

## C3-RUN1
- utc: 2026-09-25T00:03:38Z
- prev_sha256: 4da4271873c9aee72da936a02666abaefddc9f80b7950f580739587e8de3cb21
- kind: result
C3 run 1 (DECL-C3): VOID with a recorded declaration defect. Runner report and numbers: logs/c3/c3_results.json (scripts copied to tools/c3/; original sha256 values listed in that JSON).
- Inputs as declared: w040 mesh on 9.362 um volume 20250728140407 (320 x 399 grid, x20 = 6400 x 7980 = team SV shape, 28 slices = native9 label canvas, labels 0/255 at Z = 14); base checkpoint sha256 matches; metric code pixel.py sha256 matches METRIC-HASH-0.
- Render fidelity (2048 x 2048 crop at x1152, y2048): pooled Pearson 0.9999990, minimum slice 0.9999987, 99.71 % of voxels identical, none differ by more than 1, best offset 0 slices and (0, 0) px. PASSES the declared >= 0.999.
- AUC as declared (blank = every valid pixel with label 0): our render C2 with TTA forward 0.9549 / reverse 0.4254; no TTA 0.9691 / 0.3987; ORGANIZER team SV (whole canvas, no TTA) 0.9807 / 0.4563.
- AUC restricted to the organizers' supervision mask (hf native9 w040_supervision_mask; ink = label 255, blank = label 0 inside the mask): our render C2 with TTA 0.9902 / 0.5658; no TTA 0.9968 / 0.5027; team SV whole canvas no TTA 0.99659 / 0.49633.
- Defect: the section 4.C3 bars (forward >= 0.987, reverse < 0.60) and archive values (team SV 0.9966 / 0.4963; crop 0.99681 / 0.5024 without TTA and 0.9902 / 0.566 with TTA) were computed inside the supervision mask: the supervision-mask definition reproduces all of them to 3-4 decimals, while under the definition written in DECL-C3 even the organizers' own team SV scores 0.9807 < 0.987. DECL-C3 therefore paired the prompt's bars with a different metric (orchestrator's drafting error). Under DECL-C3's own clause (a mismatch with the archive description voids the run and allows one re-declaration) the run is VOID; the numbers above stand as recorded and are not used for the verdict.
- Other deviations (runner): vc_render_tifxyz needed -v <volume>; --zarr-output and crop flags added; --auto-crop omitted to keep the SV canvas. Wrapper scripts were not hashed before use (now in tools/c3/ and hashed in METRIC-HASH-6).

## DECL-C3-R1
- utc: 2026-09-25T00:03:38Z
- prev_sha256: 7b6975a0a4c6470911323a9d9c47f9ba81c44b1935023944f28721fc9f97bc6a
- kind: declaration
C3 re-declaration (once), citing C3-RUN1 (VOID: metric definition did not match the one the bars were set on). Declared before any data of the new crop exists: our C2 map of the new crop has never been computed.
- Data: same w040 inputs as DECL-C3. NEW crop: the 2048 x 2048 px square on the w040 SV canvas, on a 256 px grid, with no overlap with the run-1 crop (x 1152-3199, y 2048-4095), fully inside the render-valid area, with the largest number of supervision-mask pixels (ties: smaller y0, then smaller x0), chosen by code (tools/c3/pick_crop_r1.py, hashed in METRIC-HASH-6) before any map of it is made.
- Chain: identical to run 1 (official vc_render_tifxyz --flip-normals -n 28 on the crop; C2 with --tta-mirror, both orders; also without TTA).
- Metrics (code tools/c3/auc_eval.py + src/hercules/metrics/pixel.py, METRIC-HASH-6): render Pearson (pooled and min slice) vs team SV on the new crop; AUC inside the organizers' supervision mask (ink = label 255, blank = label 0 inside the mask, valid pixels), both orders.
- Bars (unchanged, section 4.C3): pooled Pearson >= 0.999; forward AUC >= 0.987 and reverse AUC < 0.60 under C2 with TTA.
- Default: FAIL at 24 h past 2026-09-27. An auditor (fresh agent) re-derives the AUCs from the saved maps and labels before the verdict entry.

## METRIC-HASH-6
- utc: 2026-09-25T00:03:39Z
- prev_sha256: e9fcdffa0ff191e153bd0ee1c1d8a080f23481264f32158ff268baf4571ad765
- kind: metric-hash
C3 runner scripts (copied from /work/c3/scripts with a provenance line added) and the R1 crop rule, hashed before the R1 run:

```
a5ab7fed2b83ce005e45a683ba883f8f53073dd9f9818c375bc9ab693fc097c8  src/hercules/metrics/pixel.py
5809706d567ff75f80a4e4278144ddd15c367564071643dd366ac8683e3f4e0b  tools/c3/assemble_results.py
29e14da0ccbffe0bdbbe49abfcba79346d1563c69ed4f95ded4372e0e9b1c364  tools/c3/auc_eval.py
f8e341e6cbd7c12cad4a54f5eacf4cd9004cccbf9915bbfdf679ae0c8ce6dc33  tools/c3/fidelity.py
47ac67288d2c9b9783d2c265373dab708933d65a606a0808eed32b133fe763b4  tools/c3/ledger_run.sh
b754fc887ea0227dc99ba7893393e441493a5e141b3a72c280101cb3df367ca3  tools/c3/pick_crop_r1.py
5df9c32736e828792b3cae7e7fda5ab73862a0bc0e6e79bdcd4c772cc9197ead  tools/c3/run_infer.sh
771baa2f0346718c5f63d3cb6872e651f8cfc32a4ef48b1782c3ae1a399ed12b  tools/c3/s3get.py
e2b975fac3a344efe0874c57230c27dc1b5699a0a226636b46af4c3f6c15eb52  tools/c3/s3ls.py
4757bb4d77acc434bfcc0868b8ed94896f6141bf1bad7cf5b5761b77d8d623a1  tools/c3/s3sync_prefix.py
998f1b98314b6b7d52ebbca229d48bfcd5a501ee3f2f96478586e901fef5c5e4  tools/c3/tif2npy.py
c132cfa154a9709f27498fc5ad5728da06fee20a075b92bf43dec27c50d7e0e0  tools/c3/write_readme.py
combined_sha256 d0ec5411e1a038aab0c829f1d6f0037bf03a7faf99024f109b00c1548f0b0d55
```

## METRIC-HASH-7
- utc: 2026-09-25T00:07:54Z
- prev_sha256: cec2ba5e27da45d5445b09b5267fcd026dcd33d78895aaeb3f750816923bab1f
- kind: metric-hash
C3 scripts parameterised for DECL-C3-R1 (crop origin from env C3_X0/C3_Y0, default = run-1 crop; import os added); no other change. Hashed before any render or map of the R1 crop exists (R1 crop chosen by pick_crop_r1.py: y0 2560, x0 4096, 311,648 supervision px):

```
fc35c089e15a56a04e0271a98d5bad1ffee7ce5f7a287140d9e9a70188f59a15  tools/c3/auc_eval.py
7c7ce085be389ebc39759f325a57bee3017a0725ee1eda2ee89aae4a90b16058  tools/c3/fidelity.py
combined_sha256 2a541370b2cd60c9c1dd9b57d07baea7ee85e9e886f9b1df1a8ceac08f4a8a53
```

## C3-R1-VERDICT
- utc: 2026-09-25T01:06:18Z
- prev_sha256: aec1f275aa3336487e7d1bb48937aa2927379b94729cc02e02baa58555f864c6
- kind: result
Verdict for DECL-C3-R1 (C3 regression gate, 9 um K0), citing C3-RUN1. Runner results logs/c3/c3_r1_results.json (sha256 1473c540b7199797bb559c9930febdfc56f6f27526a755b31c2f5fed7091aca7); auditor (fresh agent) logs/c3/audit_r1.json (sha256 f406328e0ede25184673c6ccd8792122a4b47f061a9447e142ed222fe67d0adf): audit PASS (hashes match METRIC-HASH-6/7/0; crop re-derived y0 2560, x0 4096, 311,648 supervision px, no overlap with run 1; label and supervision crops equal the Z = 14 source slices; forward/reverse file naming confirmed in villa infer.py; all numbers re-derived with difference 0.0).
- Render fidelity: pooled Pearson 0.9999989 (min slice 0.9999986), best offset 0, shift (0, 0): MET (>= 0.999).
- C2 WITH --tta-mirror, inside the supervision mask: forward AUC 0.97795: NOT MET (>= 0.987); reverse AUC 0.56648: MET (< 0.60).
- Not a bar: without TTA forward 0.99347, reverse 0.58142; run-1 declared-definition numbers in the results file.
VERDICT: FAIL. C3 is final for the C2 chain as declared (base step-075000 with --tta-mirror). K0: every 9 um read that uses the C2 model map is blocked. RAW displays (render only; render fidelity met) are not blocked by this gate. The auditor also noted that tools/c3/pick_crop_nt.py was written after these numbers existed (see DECL-C3-NT).

## DECL-C3-NT
- utc: 2026-09-25T01:06:18Z
- prev_sha256: f485af950d63411fa6637634af27d35101626b9064d678732c3b07053a09e903
- kind: declaration
New chain variant C2-NT and its C3 gate (a changed recipe after C3-R1-VERDICT FAIL; not a re-declaration of C2).
- Disclosure: this variant was chosen AFTER seeing that the base model without --tta-mirror scored forward 0.9968 / 0.99347 and reverse 0.5027 / 0.58142 inside the supervision mask on the two w040 crops already used (C3-RUN1, C3-R1-VERDICT). Those crops are excluded; the crop-choice code tools/c3/pick_crop_nt.py was written after those numbers existed and applies the same rule as DECL-C3-R1 with both earlier crops excluded. This gate is a fidelity check on base-trained papyrus only, never evidence of generalisation.
- C2-NT: identical to C2 (official infer CLI, both orders, batch 4, --no-compile, CPU) but WITHOUT --tta-mirror.
- Data: w040 as in DECL-C3; crop = output of tools/c3/pick_crop_nt.py (2048 px, 256 px grid, no overlap with crops (2048, 1152) and (2560, 4096), fully mesh-valid, maximum supervision pixels), run once, before any render or map of it exists.
- Metrics: as DECL-C3-R1 (tools/c3/fidelity.py, tools/c3/auc_eval.py with C3_X0/C3_Y0, METRIC-HASH-7; supervision-mask AUC).
- Bars (section 4.C3 values, unchanged): pooled render Pearson >= 0.999; C2-NT forward AUC >= 0.987 and reverse AUC < 0.60. Auditor re-derivation before the verdict.
- Consequence: PASS -> the D1 BASE arm uses C2-NT (base maps without TTA) and C2-NT replaces C2 wherever a 9 um base map is read; FAIL -> no 9 um base-map read until a new official checkpoint or chain passes C3 on fresh data; D1 then runs with RAW only.
- Default: FAIL at 24 h past 2026-09-27.

## METRIC-HASH-8
- utc: 2026-09-25T01:06:18Z
- prev_sha256: a7416c45eb2d831c145316eb3cc1d477e36e71e31955c99d921e04e43edd3f6f
- kind: metric-hash
Crop picker for DECL-C3-NT, hashed before its single run:

```
686370fdeafe9c8545483fbad8a2fd0a8cdc28ce8a9e3b339d8e9db1d6244929  tools/c3/pick_crop_nt.py
```

## C3-NT-VERDICT
- utc: 2026-09-25T01:37:48Z
- prev_sha256: 9a8da6bdbca63ebc9446e05adeef6696648f47913c28d9c968a1d0f6bf3799d6
- kind: result
Verdict for DECL-C3-NT: VOID (auditor logs/c3/audit_nt.json, sha256 db7ac93d41994514ec5314c9c03309de76e6a74b28ae472c83fe0346e325b9d2). Numbers re-derived exactly (pooled Pearson 0.9999993; C2-NT forward AUC 0.99926, reverse 0.56528 inside the supervision mask on crop y0 512, x0 5376), but the declared condition "the picker runs before any render or map of the crop exists" was false: in run 1 the runner mapped the ORGANIZER team SV of the whole w040 canvas with the same no-TTA recipe (ledger 2026-09-24T23:33-23:58Z; whole-canvas AUC in C3-RUN1), which covers this crop (that map scores 0.99929 / 0.54503 on it). The orchestrator missed this and did not disclose it in DECL-C3-NT. Correction (I17) of DECL-C3-NT's disclosure. No w040 area remains unmapped.

## DECL-C3-NT-R1
- utc: 2026-09-25T01:37:49Z
- prev_sha256: c2b0aa9006b7ec95f1efc3d82e0cb5af6018d061d47d52794c881251ecabd708
- kind: declaration
Re-declaration (once) of the C2-NT gate, citing C3-NT-VERDICT (VOID: an undisclosed prior no-TTA map covered the w040 crop).
- Data: PHerc0139 segment w044 (base-trained; official native9 human labels; volume 20250728140407), which no model map of this project has ever covered. If w044 lacks a team SV or a supervision mask, the next of w035, w041, w039 that has both is used (order fixed now). Crop: the output of tools/c3/pick_crop_seg.py (2048 px, 256 px grid, fully mesh-valid, maximum supervision pixels, ties smaller y0 then x0), run once before any render or model map of the segment exists.
- Disclosure: C2-NT was chosen after seeing its w040 numbers (0.9968 / 0.99347 / 0.99926 forward on three crops); this gate tests fidelity on another base-trained segment and is never evidence of generalisation.
- Chain, metrics, bars and consequence as DECL-C3-NT (pooled Pearson >= 0.999; forward AUC >= 0.987; reverse < 0.60; supervision-mask AUC; auditor before the verdict).
- Default: FAIL at 24 h past 2026-09-27; a second VOID also means FAIL.

## METRIC-HASH-9
- utc: 2026-09-25T01:37:49Z
- prev_sha256: 3f03e5d1dc1b0c3981c108d74ebc6b0f3f9dff8b02bee48f7784dc18224677a9
- kind: metric-hash
Crop picker for DECL-C3-NT-R1 (no exclusions), hashed before its single run:

```
f0a52666d9a8d18d1e1be2446bb2f3a81c6c72f848cc991a7ef2b9194f25cfa2  tools/c3/pick_crop_seg.py
```

## METRIC-HASH-10
- utc: 2026-09-25T01:38:29Z
- prev_sha256: 6c38b514ebdb214039d2f7db2a96b752ce062160cc412e9999f6ec0a78d64a65
- kind: metric-hash
auc_eval.py: label and supervision array paths from env C3_LAB / C3_SUP (defaults = w040 paths); no other change. Hashed before any render or map of the DECL-C3-NT-R1 segment exists:

```
27fa289bd2b38fdafb447f1d791640a4590b748627ce9255742e4c94ea0042a8  tools/c3/auc_eval.py
```

## HANDED-R2
- utc: 2026-09-25T02:16:16Z
- prev_sha256: a0cc45af23e86cd5f7cb5cf2d0992c2e950b4321f072d6df713ae10fe35a6bf8
- kind: result
Result of DECL-HANDED-R2 (0139 ascending z). Windows (human-label-chosen, 2 x 2 cm, 1/2 scale): w035 (1792, 768), w030 (2816, 3072), w043 (3072, 4608), w039 (2816, 3840); orient() mirrored none. 3 fresh readers (general-purpose, opus, sealed-output mode; jobs f83a8d75, 51f0c795, 23e3a154; audits VALID); votes counted by hercules.scorer.handed (METRIC-HASH-4/5); scorer output logs/handed/handed_r2_scorer_output.json.
- Votes: A 7, B 1, no vote (UNSURE) 4. Letters named in the side judged normal: 8, 10, 12 per reader over 4 windows.
- Verdict: AMBIGUOUS (bar >= 10 of 12 not met). The decided votes favour state A (convention_sign = +1) 7:1, which is suggestive only. Default stands: both mirror states are separate arms until a re-test passes.

## DECL-HANDED-R3
- utc: 2026-09-25T02:16:16Z
- prev_sha256: febae7085bbe4035976e24e935cf6899e291c55ddb90eae0625b86ae5e00763e
- kind: declaration
Handedness re-test R3 (0139 ascending z), declared before any of its data exists, citing HANDED-R2 (AMBIGUOUS, A 7 / B 1 / none 4).
- Material: 8 NEW 2 x 2 cm windows chosen by code exactly as in DECL-HANDED-R2 (human-label ink fraction, <= 2 per segment, same exclusions) and additionally >= 128 vox (3-D) from every HANDED-1 and HANDED-R2 window.
- Display, arms and brief as DECL-HANDED-R2. 3 fresh readers, each seeing all 8 pairs (16 images) in a random pair order.
- Bar: >= 20 of 24 votes for one state (the same 83 % threshold as before) fixes convention_sign for ascending-z JULY scans; otherwise AMBIGUOUS and both mirror states stay separate arms; no further handedness re-test on 0139 is declared before READ-CAL PROBE-1 has been read.
- Default: AMBIGUOUS.

## C3-NT-R1-VERDICT
- utc: 2026-09-25T02:39:39Z
- prev_sha256: 195f19e90955fd085d994da843fb5c1bd6e6532034a1b269550159d6749962b0
- kind: result
Verdict for DECL-C3-NT-R1 (C2-NT chain, 9 um K0), citing C3-NT-VERDICT. Runner logs/c3/c3_nt_r1_results.json (sha256 9a430680bb46ca9886f779413321d6c19b3a06bbf3470fbab0456ca6da1b8b6e); auditor logs/c3/audit_nt_r1.json (sha256 c4139c1c6f9af20eb5ba946745739648e1fec8a216d7505ba50ca5f51cdbc2de): audit PASS.
- Segment w044 (team SV 28 slices, canvas 6040 x 8160); crop y0 2816, x0 2304 from tools/c3/pick_crop_seg.py (1,052,919 supervision px), re-derived by the auditor.
- Freshness (auditor): all ledger rows, /work file searches and other agents' scripts checked; no render or model map of any w044 pixel existed before the picker ran; the earlier w040 maps lie >= 28 vox from every crop pixel; 0.43 % of the crop is same-papyrus with w043, which had only an organizer reference-map resample, and none of those pixels is in the supervision mask.
- Render fidelity: pooled Pearson 0.9999989 (min slice 0.9999983): MET.
- C2-NT (no TTA), inside the supervision mask: forward AUC 0.99960: MET (>= 0.987); reverse AUC 0.58558: MET (< 0.60; margin 0.014).
VERDICT: PASS. C2-NT is the validated 9 um base-map chain (K0 for base-map reads satisfied); C2 with --tta-mirror stays FAILED (C3-R1-VERDICT). Scope: fidelity on base-trained 0139 papyrus only, never evidence of generalisation. Note: the reverse-order AUC margin is only 0.014 (base reads slightly bright in both orders, section 4.D1).

## DECL-READCAL-PROBE1-A1
- utc: 2026-09-25T02:40:40Z
- prev_sha256: bee42993bfea290cb88202d9dbc0856a72ac41e3a3dc593e5468fb7e22a5dec5
- kind: declaration
Amendment to DECL-READCAL-PROBE1 before any PROBE-1 data exists (no PROBE-1 image has been built): orientation = the state fixed by DECL-HANDED-R3 if R3 decides; otherwise both mirror states are separate arms as originally declared (HANDED-R2 did not decide). Reason: avoid doubling 27 reader agents while a decisive orientation test is pending. Everything else in DECL-READCAL-PROBE1 is unchanged. Also noted for PROBE-1 and all later reads: the validated 9 um base-map chain is C2-NT (C3-NT-R1-VERDICT); PROBE-1 itself uses reference maps only.

## HANDED-R3-VOID
- utc: 2026-09-25T02:49:46Z
- prev_sha256: ceb61556f5fb54bfcf02269edbd9bb171e9ec6a33041f57d7b1fcb35df73988a
- kind: result
DECL-HANDED-R3: VOID before any data (not built). Builder report (/work/handed/work/r3_feasibility.json): with the declared 128 vox 3-D clearance from all 8 earlier windows, the exclusion zone covers 22-54 % of each human-labelled 0139 segment and only 1 window qualifies (w045 3328, 1792) at 256, 128 and 64 px grids. Defect: the clearance rule (orchestrator's) is infeasible on the available labelled papyrus; its purpose (fresh text per window) needs only no shared papyrus.

## DECL-HANDED-R3B
- utc: 2026-09-25T02:49:46Z
- prev_sha256: c8e516d5e37899f25da6e9feb4ace9813090b99ddb9ef726b73e8c7b8c19760f
- kind: declaration
Re-declaration (once) of the R3 handedness re-test, citing HANDED-R3-VOID (clearance infeasible). Identical to DECL-HANDED-R3 except the clearance: each new window must (a) not overlap any HANDED-1 or HANDED-R2 window on the same canvas and (b) share no papyrus with any of them (KD-tree same-papyrus test of hercules.geometry.contamination on the 9 um meshes: < 1000 vox^2 within 2 vox normal / 6 vox Euclidean distance). Adjacent windings are allowed (different text). 8 windows, at most 2 per segment, chosen by the R2 code rule (human-label ink fraction); if fewer than 8 qualify, all that qualify are used and the bar scales to ceil(0.83 x votes). Bar otherwise >= 20 of 24. Default AMBIGUOUS. No further 0139 handedness re-test is declared before PROBE-1 is read.

## METRIC-HASH-11
- utc: 2026-09-25T03:02:13Z
- prev_sha256: d885694d75c368d6c3e1483617471418e09304d621a77efbc4d912048f7cb475
- kind: metric-hash
PROBE-1 scorer (hercules.scorer.probe1: affine mapping to the state-A levelled window frame, per-reader dedup of same-kind namings within 150 px, consensus >= 2 of 3 within 150 px, agreed-firm, identity-shuffle p with 2000 permutations), 2 tests; hashed before any PROBE-1 reader runs. The localisation check against human labels is not implemented yet and will be reported as not computed unless added (and hashed) before scoring.

```
d5d68ff721205a85fb2c398af2bb981dc46805f369cc2a8c54616c90bcedc1e3  src/hercules/scorer/probe1.py
```

## HANDED-R3B
- utc: 2026-09-25T03:07:35Z
- prev_sha256: eb4dc59efb41f9dd3e351eb9783145aeaa534c48467c999e922af6e3a0c9965a
- kind: result
Result of DECL-HANDED-R3B (0139 ascending z; 8 human-label-chosen windows: w041 (2048, 256), w045 (2560, 1280), w043 (2816, 768), w039 (4352, 1024), w045 (512, 3584), w030 (512, 2816), w041 (3584, 2560), w030 (768, 256)). 3 fresh readers (general-purpose, opus, sealed-output; jobs 3f32bfb8, 8261aebb, 5f5307f1; audits VALID). Scorer output logs/handed/handed_r3b_scorer_output.json.
- Votes: A 5, B 13, no vote 6. Letters named in the side judged normal: 22, 20, 26 per reader over 8 windows.
- Verdict: AMBIGUOUS (bar >= 20 of 24). Both mirror states stay separate arms.
- Across HANDED-R2 and R3B the decided votes are A 12 : B 14 (R2 leaned A 7:1, R3B leans B 13:5). Interpretation (not a bar): blind readers cannot tell these reference maps from their mirror images, although they name about 2-3 letters per 2 x 2 cm window in the side they pick. A reader who perceived letter shapes would discriminate mirror states easily; this is evidence that current LLM namings on these maps are not reliable letter perception. PROBE-1 measures agreement directly and includes both states.

## DECL-READCAL-PROBE1-A2
- utc: 2026-09-25T03:07:35Z
- prev_sha256: 83ad732dc531ff6c7b88e07f40fd18e7dee3191e01b8bd74a5d5d3dbc08764f0
- kind: declaration
Amendment 2 to DECL-READCAL-PROBE1 before any PROBE-1 data exists (images built, no reader run): (1) orientation: HANDED-R3B did not decide, so both mirror states A and B are separate arms (per -A1); (2) reader models reduced to {opus, fable}, the section 6.2 grid ("strongest vision model available to subagents; one other version"); sonnet is dropped to hold 36 readers instead of 54. Arms: {D2, D1Q, N2} x {A, B} x {opus, fable}, 3 fresh readers each. (3) Brief: prompt P with its item sentence adapted to one image per item ("Each item is one grayscale image (reported as LEFT; RIGHT stays empty)"), px/mm and letter heights per display (D2 53.4 px/mm, 107-214 px; D1Q 106.8 px/mm, 214-427 px; N2 208.4 px/mm, 417-834 px). (4) Mirror check added, reported only: summed agreement in state A vs state B per display and model. Decision rule and default unchanged.

## PROBE1-RESULT
- utc: 2026-09-25T03:29:21Z
- prev_sha256: 02ea87db699e605f951890e1f5c068106cfe3b1e2559aa79ab06672c917961cc
- kind: result
Result of DECL-READCAL-PROBE1 (+A1, +A2). 36 fresh readers (general-purpose, sealed-output mode; 18 opus, 18 fable), 12 arms {D2, D1Q, N2} x {A, B} x {opus, fable}, 3 readers each; all 36 transcripts audited VALID; 0 malformed. Scorer hercules.scorer.probe1 (METRIC-HASH-11); results logs/readcal/probe1_results.json (sha256 aaa9bc22895563ccc1721ab6a708ab031faad3226b8a473991c94ff13972ff8f). Material: 4 human-label-chosen 2 x 2 cm windows of official 0139 reference maps (w035, w030, w043, w039; HANDED-R2 windows).
- Agreed letters (same identity within 150 px, >= 2 of 3 readers), summed over 4 windows [max in one window]: D2_A_opus 6 [3], D2_A_fable 6 [4], D2_B_opus 6 [3], D2_B_fable 3 [2]; D1Q_A_opus 1 [1], D1Q_A_fable 5 [2], D1Q_B_opus 2 [1], D1Q_B_fable 2 [2]; N2 all arms 0 [0] (0-3 letters named per arm).
- Agreed-firm (firm for >= 2 readers): 0 in every arm and window.
- Between-reader identity-shuffle p per window: every value >= 0.107 (no window significant).
- Mirror check (state A vs B agreed, reported only): D2 opus 6 vs 6, D2 fable 6 vs 3, D1Q opus 1 vs 2, D1Q fable 5 vs 2, N2 0 vs 0: no consistent preference for the correctly oriented state.
- Localisation against human labels: not computed (not implemented before scoring).
- Decision rule: best (display, model) summed over states is D2_opus (12); no arm reaches >= 5 agreed letters in any window, so SG-FEAS is NOT PASSED and the declared consequence applies: "REF not blind-legible at any tested display". SG stays infeasible; every letter-reading decision (D1, D2, Route Z) is suspended until a new display, prompt or reader passes this probe on fresh windows. SG bars are unchanged.
- Interpretation (not a bar): with current subagent vision models, blind readers do not agree on letters even in the official high-resolution reference ink maps of known text, at any tested scale; the prompt's I4 blind-LLM reader requirement, not ink detection, is now the binding constraint on any First Letters claim by this project.

## DECL-READCAL-PROBE2
- utc: 2026-09-25T03:30:01Z
- prev_sha256: dc6614a40865504af67e4769b5e662f79337c95b22a5db918d4d0c0fab65329c
- kind: declaration
READ-CAL PROBE-2 (planned; declared now, before any of its data exists), following PROBE1-RESULT. Tests the one untested lever of the section 6.2 grid: the prompt variant "P plus a font-rendered lunate-capital key sheet".
- Material: 4 FRESH 2 x 2 cm windows of official PHerc0139 reference maps, chosen by code by human-label ink fraction on 0139 segments with official human labels, sharing no papyrus with any earlier HANDED/PROBE window (KD-tree same-papyrus test) and outside every sealed set; if fewer than 4 qualify, the next source is PHerc0814 segments >= 184 vox from 46527 with windows chosen by a fresh picker in sealed-output mode.
- Display D2 (1/2 scale, 1068 px), both mirror states A and B; models {opus, fable}; prompt P (one image per item) preceded by ONE key-sheet image: a 1068 x 1068 px grid of the 24 Greek capitals with lunate sigma, font-rendered (DejaVu Serif Bold), black on white, each labelled below with its name in Latin letters; the key sheet is the same for all readers and hashed before use. 3 fresh readers per (state, model): 12 readers.
- Metric, decision rule and scorer exactly as PROBE-1 (agreed >= 2 of 3 within 150 px; SG-FEAS needs >= 12 agreed and >= 8 agreed-firm in one window; suspension lifts only if some arm reaches >= 5 agreed letters in at least one window AND beats the identity-shuffle null at p < 0.05 in that window).
- Default: NOT PASSED; suspension continues.

## METRIC-HASH-12
- utc: 2026-09-25T03:30:28Z
- prev_sha256: 611e1ce82bdbdb68aa64a3cb0928eb770cb165efce506aa48a1557468a9831dc
- kind: metric-hash
PROBE-2 key sheet (DECL-READCAL-PROBE2), frozen before any PROBE-2 reader runs: configs/briefs/probe2_keysheet.png sha256 5da96bde05851b0cd9316292e5f7ef95d497a400f582c6869840a66dc6a65f88 (1068 x 1068, 24 Greek capitals incl. lunate sigma, DejaVu Serif Bold, names in DejaVu Sans below each).

## DECL-READCAL-PROBE2-A1
- utc: 2026-09-25T03:34:38Z
- prev_sha256: bc1b7a984865c8d35b25b1f84df18aec593adb60378c1e8aa104ce0d501ea1a8
- kind: declaration
PROBE-2 window build: only 1 of 4 fresh windows qualifies (w045 (768, 5888), 8 labelled ink pixels; 946 of 947 labelled candidate windows overlap one of the 16 earlier windows; /work/probe2/work/windows_probe2.json). The declared fallback (PHerc0814 with a picker) is also infeasible at 2 x 2 cm: the 0814 segments are 1.4-1.7 cm-tall ribbons (RCBANK-1 attempt 2). Re-declaration (once), citing this: PROBE-2 is run as a PAIRED test on the 4 PROBE-1 windows and images (/work/probe1/{A,B}/D2, key /srv/scorer/probe1_key.json), with 12 fresh readers (states A and B x {opus, fable} x 3), each shown the key sheet (METRIC-HASH-12) first and then the 4 window images with prompt P amended by one sentence: "The first image is a reference sheet of the Greek capitals used (lunate sigma Ϲ); do not report letters in it." Scorer hercules.scorer.probe1 (METRIC-HASH-11), key-sheet item excluded. Pass condition unchanged (some arm reaches >= 5 agreed letters in a window with identity-shuffle p < 0.05 there). Because windows are reused, a PASS lifts the suspension only after it replicates on fresh known-text material under a new declaration. Default: NOT PASSED.

## PROBE2-RESULT
- utc: 2026-09-25T03:41:34Z
- prev_sha256: 2be9c5d27106649bf7a3a8fe006ebb9dab7e10653a5140f6d9e0f65538c2e7aa
- kind: result
Result of DECL-READCAL-PROBE2 as re-declared by DECL-READCAL-PROBE2-A1 (paired key-sheet test on the 4 PROBE-1 windows w030, w035, w039, w043). 12 fresh readers (general-purpose, sealed-output mode; 6 opus, 6 fable), arms K_D2_{A,B}_{opus,fable}, 3 readers each; key sheet METRIC-HASH-12 shown first; all 12 transcripts audited VALID (5 images read each); 0 malformed; 0 letters reported on the key sheet by any reader. Scorer hercules.scorer.probe1 (METRIC-HASH-11); results logs/readcal/probe2_results.json (sha256 0e4b3fecfe908fb6ae9490132c3ce318012207ccf8c2eb5b226e358a36ab55d8).
- Agreed letters (>= 2 of 3 readers, same identity within 150 px), per window [w030, w035, w039, w043] and summed: K_D2_A_fable [0, 0, 5, 3] = 8; K_D2_A_opus [0, 1, 3, 3] = 7; K_D2_B_opus [0, 1, 2, 2] = 5; K_D2_B_fable [0, 0, 1, 0] = 1. Letters named per arm: 33, 23, 16, 7.
- Agreed-firm: 0 in every arm and window.
- Identity-shuffle p (2000 permutations): K_D2_A_fable w039 63/2001 = 0.031, w043 195/2001 = 0.097; K_D2_A_opus w039 113/2001 = 0.056, w043 103/2001 = 0.051; every other defined p >= 0.49.
- Declared condition (>= 5 agreed in a window with p < 0.05 there): MET in exactly one cell, K_D2_A_fable at w039 (5 agreed, p = 0.031). SG-FEAS (>= 12 agreed and >= 8 agreed-firm in one window): NOT PASSED.
- Consequence as declared: the windows are reused, so this lifts NOTHING until it replicates on fresh known-text material under a new declaration. The suspension of D1, D2 and Route Z continues.
- Paired with PROBE-1 D2 (same windows and images; key sheet added), summed agreed: A_opus 6 -> 7, A_fable 6 -> 8, B_opus 6 -> 5, B_fable 3 -> 1; at w039 A_fable 4 (p 0.119) -> 5 (p 0.031).
- Mirror check (reported only): state A vs B summed agreed, opus 7 vs 5, fable 8 vs 1 (all four D2 arms in both probes: A 27 vs B 15). Which state is correctly oriented is unknown (HANDED-R2/R3B AMBIGUOUS).
- Caveats (interpretation, not a bar): about 10 arm-window cells had a defined p and the declared condition carries no multiplicity correction; the passing cell sits exactly at the bar with 0 firm letters; w039 was already the strongest PROBE-1 window. Agreement beyond the identity-shuffle null shows readers share a perception at the same places; it does not show the letters are correct. No letter-level transcription of these windows exists to test identity.
- Correction (I17) to PROBE1-RESULT: "no consistent preference for the correctly oriented state" should read "no consistent preference for either mirror state"; neither state is known to be correctly oriented.

## DECL-READCAL-PROBE3
- utc: 2026-09-25T04:25:26Z
- prev_sha256: 6d5e3e0816a76fdc1d26bab9930c94705de6c64c634cdb9db59f2c0997bb1fa5
- kind: declaration
READ-CAL PROBE-3, the fresh-material replication that DECL-READCAL-PROBE2-A1 requires for the one PROBE-2 cell that met the lift condition (PROBE2-RESULT: K_D2_A_fable at w039). Declared before any PROBE-3 image exists; windows fixed by a numbers-only feasibility run (no image opened by anyone; logs/views.tsv has no entries).
- Material: the 3 qualifying 2 x 2 cm windows (2136 px at 9.362 um) on PHerc0139 w040 and w044 under the PROBE-2 selection rule unchanged (human-label ink fraction, native 9.362 um label set 20260918; 256 px grid; coverage >= 0.90; <= 2 per segment; no 2-D overlap and < 1000 vox^2 shared papyrus with all 16 earlier HANDED/PROBE windows): w044 (2816, 2816) ink 0.0799; w040 (2560, 4096) ink 0.0329; w040 (256, 512) ink 0.0329 (PROBE-2 windows: 0.025-0.046). Script /work/probe3/scripts/feasibility_probe3.py sha256 a5572ea388c14995099125a07ed0d1af58cdbeb7e84b5341f8d72ca09df0ad42; record logs/readcal/probe3_feasibility.json sha256 1e8b58f8fa709d346c35ec2a697e11029a46196f8c592251d8c896de4f4ed613. w040 and w044 were excluded earlier only because they served the finished C3 gate.
- Disclosure: all 3 windows overlap C3 crops (numbers-only fidelity/AUC computations; no image made or viewed), and a project-made base-model map of the whole w040 canvas exists (gpu_ledger row 37; never displayed). No reader, picker or person has seen any image of w040 or w044. Only 3 windows qualify (not 4); they are used as they are.
- Display, prompt and harness identical to PROBE-2 (DECL-READCAL-PROBE2-A1): key sheet METRIC-HASH-12 first, then the 3 window images at D2 (whole window, INTER_AREA 1/2, 1068 px, raw 0-255 reference probabilities); state A = run_window (margin 256, step 20 vox, z_ascending, convention_sign +1 measured against the outward direction from the scroll centre curve, so A has the same handedness as PROBE-2 state A), state B = A mirrored left-right; prompt P (one image per item) plus the key-sheet sentence; sealed-output mode; key /srv/scorer/probe3_key.json in the PROBE-1 key format. Before building, the builder must show that its selection code reproduces the recorded PROBE-2 selection (w045 (768, 5888) only) and the 3 windows above.
- Readers: 12 fresh general-purpose readers, arms K_D2_{A,B}_{opus,fable}, 3 each, image order randomised per reader.
- Scorer: hercules.scorer.probe1 (METRIC-HASH-11), unchanged; the key-sheet item is not in the key.
- PRIMARY (the replication; one pre-specified arm, no arm multiplicity): K_D2_A_fable reaches >= 5 agreed letters (>= 2 of 3 readers, same identity within 150 px) in at least one of the 3 windows with identity-shuffle p < 0.05 in that window. Met -> REPLICATED: the suspension of letter-reading decisions (PROBE1-RESULT) lifts for display K_D2 with reader model fable only; every SG bar is unchanged and nothing here is evidence of letters on any eligible scroll. Not met -> NOT REPLICATED: the suspension continues, and D1 takes its declared default (FAIL) at the first session after 2026-10-04.
- Reported only: the other 3 arms; mirror check with the directional prediction that state A agrees more than state B summed over the 3 windows in each model (supports true letter perception and state A as the reading orientation if met; no handedness decision is taken from it).
- Default: NOT REPLICATED.

## PROBE3-RESULT
- utc: 2026-09-25T05:02:50Z
- prev_sha256: 257f16875b17523f9c0d0829d0c9d8b652aa2a58d1ad6f107d3b3f59ff9a6a14
- kind: result
Result of DECL-READCAL-PROBE3 (fresh-material replication). 6 images built by code (regression checks passed: PROBE-2 selection and the 3 declared windows reproduced exactly; synthetic key test max error <= 0.099 px); 12 fresh readers (general-purpose, sealed-output; 6 opus, 6 fable), all 12 transcripts audited VALID, 0 malformed, 0 letters reported on the key sheet. Driver tools/readcal/score_probe3.py (sha256 bd27bd73..., committed before decryption), scorer hercules.scorer.probe1 (METRIC-HASH-11); results logs/readcal/probe3_results.json (sha256 222976e3531fd835a7311e156203662dcaf6d096a6ff75ae949bba7bcefc7da3).
- Agreed letters per window [w040 (2560, 4096), w040 (256, 512), w044 (2816, 2816)]: K_D2_A_fable [0, 1, 10] = 11; K_D2_A_opus [0, 3, 5] = 8; K_D2_B_fable [0, 1, 8] = 9; K_D2_B_opus [0, 1, 8] = 9. Named per arm 37, 28, 48, 30. Agreed-firm: 0 in every arm except K_D2_B_opus (1).
- Identity-shuffle p at w044: A_fable 1/2001 (0.0005, the smallest attainable), A_opus 78/2001 (0.039), B_fable 13/2001 (0.0065), B_opus 3/2001 (0.0015); A_opus at w040 (256, 512) 140/2001 (0.070); every other defined p = 1 or >= 0.49.
- PRIMARY (K_D2_A_fable, >= 5 agreed in a window with p < 0.05 there): MET at w044 (10 agreed, p 0.0005). Verdict: REPLICATED. Declared consequence: the suspension of letter-reading decisions (PROBE1-RESULT) lifts for display K_D2 (key sheet + D2) with reader model fable only. Every SG bar is unchanged; SG-FEAS is still NOT PASSED (no window has >= 8 agreed-firm; the best has 0); nothing here is evidence of letters on any eligible scroll.
- Mirror check (reported only): summed agreed A vs B, opus 8 vs 9, fable 11 vs 9; the declared directional prediction (A > B in each model) is NOT MET. At w044 all four arms agree beyond the null in both mirror states.
- EXPLORATORY (not declared; does not change the verdict; logs/readcal/probe3_exploratory_identities.json sha256 1cb1b63bb633592ad3728084ebf2e1039831ef91a78bee2f4375717768363fad): agreed identities are dominated by the simplest shapes, e.g. K_D2_A_fable O 3, I 3, T 2, L 1, N 1, lunate sigma 1 (Greek capitals); 75-89 % of agreed letters per arm are mirror-symmetric capitals, matching the 75-87 % of all namings; A and E, both very common in Greek, are never agreed in the primary arm.
- Interpretation (not a bar): blind readers with the key sheet agree, beyond the identity-shuffle null, on letter-sized ink shapes in reference maps, replicated on fresh papyrus but carried by one window per probe (w039, then w044) and insensitive to mirroring. That fits shared perception of simple ink shapes (round forms, vertical strokes) better than reading of text; letter-level correctness is untested (no transcription exists) and firm confidence is absent. The SG firm bar (>= 8 agreed-firm) is the binding gap.

## AUDIT-OMIT-PROBES
- utc: 2026-09-25T05:05:56Z
- prev_sha256: 74b98dbd825cf81da37bbe48251edd32f82eb188d35ee7d0ad945f9997dafa2a
- kind: correction
Correction (I17), process: section 3.3 requires a fresh auditor agent to re-derive every verdict from raw reader JSON and the scorer, and to check the declaration hash, before the verdict is recorded. PROBE1-RESULT, PROBE2-RESULT and PROBE3-RESULT were recorded on deterministic scorer output plus the sealed-output transcript audit only; no independent auditor re-derivation was run (orchestrator omission). Remedy: a fresh auditor was launched 2026-09-25 ~05:10Z to re-derive all three from the sealed answers with independently written counting code and the declared scorer, check declaration-before-data (entry utc, job creation, answer mtimes, commit order vs first decryption), scorer hashes, transcripts, input hashes, reader freshness and PROBE-3 window freshness; outputs logs/readcal/audit_probe{1,2,3}.json. Until its PASS is recorded, PROBE3-RESULT's lift is PROVISIONAL: no D1 reader, sealer or picker runs (build work without reader data may proceed). A VOID voids the verdict concerned; the probe is then handled per section 3.1 (one re-run with fresh readers, then the default).

## METRIC-HASH-13
- utc: 2026-09-25T05:09:20Z
- prev_sha256: 73022bfb4c0779647392d0f5c70701eddc25364ae00d334897e1930e22876183
- kind: metric-hash
Seal label-position rule of DECL-SEAL (hercules.scorer.sealpos: seal letter position = centroid of official human-labelled ink pixels (label > 0) inside the union of the agreeing sealers' boxes, canvas px with pixel centres at integers, unchanged when the union holds no labelled ink; groups re-derived with consensus.agreed_letters exactly as make_seal and asserted identical; consensus.py unchanged), 8 tests (full suite 553 passed); hashed before any seal exists.

```
dca8cb01907d55e477d88d2ac176abb0a8e7106e60561089378f4721059d51fb  src/hercules/scorer/sealpos.py
2e59bf5a304b279b4db9b6548771f5831f1c919459027dd0ad30acaa630ca3c7  tests/test_scorer_sealpos.py
combined_sha256 0412cc0d64f1117d19984742f58c398bd8a77d534fda01903391fa72e6484410
```

## DECL-D1-A2
- utc: 2026-09-25T05:11:00Z
- prev_sha256: bc7ca51779df02c40f56d1a369ab3d39842d7cbb4b671b0b5e127f5eb89965cc
- kind: declaration
Amendment 2 to DECL-D1 (J geometry), before any D1 data exists (no seal, no sealer image, no render of J): PHerc0841 has no official umbilicus (anonymous listing of PHerc0841/representations: predictions only) and CT access to 0841 is barred by code until the J seal is committed (hercules.pipeline.centre SEALED_SCROLLS), so no mask-centroid curve can be made. Decision: state A of every 0841 window (J1-J5 and any later 0841 D1 window) is oriented against the geometry-only centre hercules.pipeline.centre.geometric_centre_curve (centre of curvature per 400 vox z band from mesh normals; no CT, SV, label or render), computed per segment from that segment's own organizer mesh, as recorded in /work/pipeline/j0841/j0841_geometry.json (sha256 34a064036dc3edba1b1d770bb3fc3181f9382b0a56f46d4d636abbb7fb6fedbf; per-segment median centres (x, y) w00 (2777, 3519), 214732 (2775, 3526), 022814 (2764, 3492); the outward-normal sign is unambiguous on J1-J5, clear fractions 0.95-0.98). 0139 windows (blanks on w053, canaries) keep the 0139 mask-centroid curve used by every earlier 0139 build (/work/handed/work/mask_centroid_L4_r2.npz sha256 238bc1dae3bca868b787487800c444400ce1c7b510f4f50b45af0ace94f3f734). Handedness on 0841 is untested and the centre method differs from 0139's, so state A on 0841 is not assumed to share 0139 state A's handedness; per DECL-D1-A1 every model arm is read in both mirror states. The seal is made on state A. Everything else in DECL-D1 and DECL-D1-A1 is unchanged; the reader and sealer configuration follows the READ-CAL freeze, recorded separately after the PROBE audit.

## AUDIT-PROBES
- utc: 2026-09-25T05:25:00Z
- prev_sha256: 188e7b6b3d55e7e48f05812d51ae30f6386877acec053f107c77f896cf27e773
- kind: result
Auditor result for the READ-CAL probe verdicts (remedy of AUDIT-OMIT-PROBES). Fresh auditor agent, independent counting code plus the declared scorer; audit_utc 2026-09-25T05:23:24Z, repo head 54f4260; files logs/readcal/audit_probe1.json (sha256 617f8be5b5e52b962752a176bb3de5eda562765bb7e7956c0665510512fabe12), audit_probe2.json (a6a9f95ddfbb5cc1d62292dc7268b67a23c8edaea8e6dd409fc6ae0d8bbeee08), audit_probe3.json (e0216b9ad347b03d0caed7989999172e080e1f071f2bf8534039d874dd1c801e). Decryptions logged (60, purposes audit-probe1/2/3).
- PROBE-1: PASS. PROBE-2: PASS. PROBE-3: PASS. Agreed, agreed-firm and named counts re-derived exactly in every arm-window cell (48/48, 16/16, 12/12); the declared scorer reproduces every recorded p; the auditor's own RNG moves no cell across 0.05. Scorer files match METRIC-HASH-0/5/11; 60/60 transcripts valid (audit function called directly); image and key-sheet hashes match; 60 distinct fresh agents.
- PROBE-3 freshness confirmed: only the 12 PROBE-3 readers ever read a PROBE-3 image; none of 56 earlier jobs listed any w040 or w044 image; views.tsv empty. PROBE3-RESULT is therefore final: the suspension lifts for K_D2 with reader fable (no longer provisional).
- Notes disclosed (none invalidating): (1) PROBE-1: an undeclared interim decryption of the 24 D2/N2 answers at 03:14Z preceded the launch of 9 D1Q readers (briefs already fixed; nothing changed; logs/readcal/probe1_interim_D2_N2.json). (2) PROBE-2: DECL-READCAL-PROBE2-A1 was appended before the jobs were created but committed at 03:38:03Z, after the sealed answers were written (03:35-03:37Z) and before the first decryption (03:39:28Z); from now on declarations are committed and pushed before any reader launches. (3) PROBE-3: the replication rests on one window.
- Corrections (I17): PROBE1-RESULT "every value >= 0.107" should read "every value >= 0.117" (declared scorer minimum; the statement held). AUDIT-OMIT-PROBES "launched 2026-09-25 ~05:10Z" should read "launched shortly before 05:05:56Z" (the entry's own time).

## METRIC-HASH-14
- utc: 2026-09-25T05:26:02Z
- prev_sha256: 00c613235bbe661560d89220abbcf0d53387b6730f6f9be7b00133851e7ead0c
- kind: metric-hash
Frozen READ-CAL task texts (READCAL-FREEZE), hashed before any use outside PROBE-2/3: single-image items (identical to the PROBE-2/3 task text) and the LEFT/RIGHT pair form of prompt P with the key-sheet sentence and an item listing placeholder {items}.

```
bd03427efc79db3b77838dfbe1323721dcaffbee48374e6f9e562b4c8554c9dc  configs/briefs/k_d2_pairs_task.txt
74a0cbe86223d68a09cd28d8cc5a012438e72d628d59e7114fa096ccf2ac45f0  configs/briefs/k_d2_task.txt
combined_sha256 4b31ca2d819e9f10df22d344ca2c7f7e99a897f3121b23f64438b2bfd579eaf2
```

## READCAL-FREEZE
- utc: 2026-09-25T05:26:02Z
- prev_sha256: 4abc11258d488f468b6b39c0484670e3a84516bb30c6771294a95f2b2bfcd319
- kind: decision
READ-CAL freeze (DECL-READCAL selection, 5 days before its 2026-09-30 date), from PROBE1-RESULT, PROBE2-RESULT, PROBE3-RESULT and AUDIT-PROBES. The declared sealed-bank C_net grid could not run (RCPICK-1: no bank window qualified); the PROBE series (declared amendments of READ-CAL) is the evidence.
- D* = K_D2: the METRIC-HASH-12 key sheet as the first image, then each 2 x 2 cm window at 1/2 scale (1068 px, INTER_AREA, raw 0-255 probabilities or linear 1-99 % CT window, no contrast change).
- P* = prompt P adapted to one image per item plus the key-sheet sentence, frozen as configs/briefs/k_d2_task.txt (sha256 74a0cbe86223d68a09cd28d8cc5a012438e72d628d59e7114fa096ccf2ac45f0, the exact PROBE-2/3 task text); for LEFT/RIGHT items (two orders) the same text in the P pair form, configs/briefs/k_d2_pairs_task.txt (sha256 bd03427efc79db3b77838dfbe1323721dcaffbee48374e6f9e562b4c8554c9dc; METRIC-HASH-14).
- Reader model: fable only (the configuration that replicated; opus is not lifted).
- sigma_crit: not measured on a bank; it is measured from the D1 REF ladder and recorded there.
- SG-FEAS: NOT PASSED (no reference window reaches >= 12 agreed with >= 8 agreed-firm; the best is 10 agreed, 0 firm). The SG bars are unchanged; no SG attempt until REF passes SG 1 on a bank window.
- PROJ (ranking only): not computed (no sealed recall yet).

## DECL-D1-A3
- utc: 2026-09-25T05:26:32Z
- prev_sha256: 3dfafb19c318aff9de6f8ab68d76cc2ace2ae79adc239862973cc45100410536
- kind: declaration
Amendment 3 to DECL-D1 (reader configuration and reading plan), before any D1 data exists (no seal; no picker, sealer or reader has seen a J or blank image; no render of J), citing READCAL-FREEZE and AUDIT-PROBES. Bars of DECL-D1 unchanged.
1. Agents: every D1 picker, sealer and reader is a fresh general-purpose agent, model fable, sealed-output mode (DECL-HARNESS-A1), shown the METRIC-HASH-12 key sheet first. Single-image items use configs/briefs/k_d2_task.txt; LEFT/RIGHT items use configs/briefs/k_d2_pairs_task.txt with sides randomised per reader and item (METRIC-HASH-14; key held by the scorer). Every image is 1068 px (D2). Declarations are committed and pushed before any agent of the step is launched.
2. Blanks: one fresh picker reads the key sheet and the 2 code-chosen w053 blank candidates (state-A reference, single-image items); a candidate is confirmed if the picker reports rows N and names <= 1 letter on it; an unconfirmed candidate is replaced by the next code-ranked candidate, confirmed by another fresh picker. Blank seal = {blank: true, letters: []}.
3. J seal: 3 fresh sealers each read the key sheet and the 5 state-A J reference images (single-image items, order randomised per sealer). Seal per window = hercules.scorer.sealpos.make_seal_with_labels (METRIC-HASH-13) on the sealers' namings (centres and boxes) mapped to levelled-window px by the key affines, with the official 0841 human ink labels (label_set 20260918) in the same frame. One canonical JSON, age-encrypted to the scorer recipient; its sha256 committed and pushed before any render of J. The orchestrator sees only S', per-window counts (letters, firm) and sealer agreement statistics.
4. Small seal: B0841-BANK shows no 2 x 2 cm 0841 area outside the T shell (<= 1.52 cm^2 per segment), so no further 0841 windows can be added: S' >= 30 normal bars; 20 <= S' < 30 run with p_max < 0.005; S' < 20 VOID, defer to KTLB-4-0841. S' is recomputed after the alignment gate.
5. After the seal (DECL-D1, -A1, -A2 unchanged): level_mesh; vc_render_tifxyz -n 31 --voxel-size 9.366 over each window + 256 px; alignment gate; C2-NT inference (no TTA; C3-NT-R1-VERDICT) in both orders; RAW-F / RAW-B slab means with the linear 1-99 % window. Text order: hercules.metrics.pixel.auc of the base map in each order against the official 0841 human ink labels inside the official supervision mask, pooled over the gated J windows (levelled state-A frame); higher AUC = text order; written to RULES.md before any reader starts.
6. Arms, 3 fresh readers each; a reader reads all gated J windows of one arm-state in one session (random order) plus 1 positive canary and 1 blank item in the same display at random positions:
   REF ladder, state A only, read first: the reference on the levelled window blurred by a Gaussian of sigma 0, 0.15, 0.30, 0.45 mm (0, 16.02, 32.03, 48.05 px at 9.366 um) before INTER_AREA; single-image items.
   Family: BASE-A, BASE-B (C2-NT, the two orders as LEFT/RIGHT), RAW-A, RAW-B (RAW-F / RAW-B as LEFT/RIGHT); state B = state A mirrored left-right.
   CHANCE-A, CHANCE-B: each window shown with the BASE maps of the next gated window in window-id order (cyclic), scored against its own seal.
   Canary: PHerc0139 w044 window (2816, 2816) (base-trained) in the arm's display (reference for REF, C2-NT for BASE/CHANCE, RAW for RAW); attention only: namings counted and reported, never scored, never a bar.
   Blank: the confirmed w053 blanks alternately, in the arm's display, scored as blank windows.
   Total 30 readers (+ 3 per confirmation pass).
7. VOID check before any model arm is read: REF sigma 0 mean C_all at R = 250 px < 0.5 S' -> VOID (DECL-D1).
8. Scoring: hercules.scorer.score.score_decision (METRIC-HASH-0), 5000 permutations, seed 20260924. Decision family {BASE-A, BASE-B, RAW-A, RAW-B}, p_max = max-T over these 4 arms; REF ladder and CHANCE scored as separate calibration decisions. PASS/FAIL/BETWEEN exactly as DECL-D1 on the best family arm, with C_all(CHANCE) taken in the same mirror state and "<= 1 naming on blanks" = mean blank namings per reader <= 1; confirmation passes = 3 fresh readers per pass on the best arm. sigma_crit = largest ladder sigma whose REF mean C_net is >= 50 % of sigma 0's.
9. A fresh auditor re-derives the verdict before it is recorded. Default FAIL if unresolved 24 h after 2026-10-03.

## DECL-D1-A4
- utc: 2026-09-25T05:45:11Z
- prev_sha256: b1bd77b98cde1e3b029a28d833001d996700379b08a3ecb2e045aebf8d41a106
- kind: declaration
Amendment 4 to DECL-D1 (blank windows), before any D1 data exists, citing a recorded infeasibility: the DECL-D1-A1 blank rule ("2 windows from clean 0139 w053, outside every READ-CAL window + 128 vox") admits no window. On w053, 25 windows (2136 px, 256 px grid) have coverage >= 0.90 and reference ink (ref >= 150 among covered px) < 1 % (0.0059-0.0097), and every one overlaps an RCPICK-1 picker window (24 picker windows tile w053 on a 1024 px grid; minimum 3-D distance 0 vox); /work/jseal/work/diag_blanks.json sha256 3b9b0d29dce8e18b2f875a06eed24128a34a7c4c277d83f3416277a0e513379c (builder diagnostic, numbers only).
- The READ-CAL clearance protected bank windows for a later seal. READ-CAL selected no bank window (RCPICK-1) and is frozen (READCAL-FREEZE), so no READ-CAL window will be sealed or read again; the clearance no longer protects anything. A blank serves one purpose in D1: counting namings by fresh readers on text-free papyrus that is clean for base; one earlier picker's view of a reference image does not affect that.
- New rule: the 2 blanks are the first 2 of those 25 w053 candidates by code rank (reference ink ascending, then coverage descending, then y0, x0), non-overlapping in 2-D, with no 2-D overlap with any HANDED/PROBE window on the same canvas (none lies on w053). Distance to windows on other segments is not constrained (w053 is clean for base; its nearest HANDED/PROBE papyrus is on adjacent windings of base-trained w045, 45-70 vox away, i.e. different papyrus). Picker confirmation (DECL-D1-A3 item 2) is unchanged; an unconfirmed blank is replaced by the next candidate in rank.
- Builder choices recorded (open in the brief): 0841 validity = bank valid9 (mesh-quad valid and >= 50 % of the 2.4 um footprint with nonzero surface CT); 0841 reference = bank float32 ref9, rounded to uint8 only at display (raw 0-255); labels = bilinear resample of lab9_inklabels, > 0.5 -> 1; blank ink fraction counted among covered px. J state-A check: /work/jseal/work/check.json sha256 03e5d55000a08b8e81ba85fe6ae76e36532a124df4cfac39e885b13a91088ebe (J1-J5: no flips, normal sign +1 unambiguous, synthetic key max error <= 0.093 px).
Everything else unchanged.

## METRIC-HASH-15
- utc: 2026-09-25T05:52:03Z
- prev_sha256: bc50ba869b2b994a87e595c3808f2ff718b97b6a2e8891a1390d6ab011cd4995
- kind: metric-hash
D1 J-seal code (DECL-SEAL, DECL-D1-A3 items 2-3, DECL-D1-A4), hashed before any picker or sealer job exists: hercules.scorer.sealbuild (maps sealer namings and boxes to the window frame by the key affines, builds per-window seals with sealpos, blank windows, organizer coordinates; 4 tests; suite 561 passed), tools/d1/jseal_jobs.py (1 picker on the 2 primary blanks, 3 sealers on J1-J5, key sheet first, k_d2_task.txt), tools/d1/make_jseal.py (blank confirmation: rows N and <= 1 letter; reserve replacement; seal encryption; counts-only summary logs/d1/jseal_summary.json).

```
51f22394c2eceed114919c934253402e88998e1dec2977349774da11e933c714  src/hercules/scorer/sealbuild.py
8b40673ad6470a6584f14ff123ec70d807b3dad85bd1da1da4e7816a104b235b  tests/test_scorer_sealbuild.py
563c979bddc65454bda91a819151f1f51dacc71827e542b6b7a77674d7b85781  tools/d1/jseal_jobs.py
fd5e7590460ecec2ee60fab78c7a22d1b058f8ef8768eb5af18338096b416ceb  tools/d1/make_jseal.py
combined_sha256 d0c960a3cc6478bada849190f84c1843b4112ea3936aa586061ebfa115a2c7fd
```

## SEAL-J-D1
- utc: 2026-09-25T05:58:16Z
- prev_sha256: 2ae1e96f4f39d7d50ef82e8202cf7e10fe1cbbc670cbd13453a9142446885d17
- kind: result
J seal for D1 (DECL-SEAL, DECL-D1-A3 items 2-3, DECL-D1-A4), committed and pushed before any render of J exists. Encrypted canonical JSON (age, scorer recipient) seals/seal_J_d1.age = /work/jseal/seal_J.age, sha256 ae874fab437fc58f3a6fd1d0123ef3463ea7eca742b91d2cda223d65c68ca68d; counts-only summary logs/d1/jseal_summary.json (sha256 d68d50efb4d07c0243b7d32cd7743296d41f24e5bf52cd8975c34c52f3be340a). Code METRIC-HASH-13 and -15 (unchanged). Material: state-A levelled 0841 reference images (DECL-D1-A2 geometry), manifest logs/d1/jseal_manifest.json (sha256 2ddce42838b304720a46aa799ee4143415fd70b3f90dc8140d0f3b98e1375956).
- Agents (fable, sealed-output, key sheet first; all transcripts audited VALID): picker 3cbdcd85 (blanks); sealers 4b0d2ab3, f33e93ff, 2d389141.
- Blanks: blank_w053_y256_x1536 and blank_w053_y256_x7168 both confirmed (rows N, 0 letters named); no reserve used.
- Seal letters per window (firm; 3/3 agree, 2/3 agree; label-positioned): J1 0; J2 6 (1; 1, 5; 5); J3 2 (1; 1, 1; 2); J4 5 (5; 4, 1; 2); J5 7 (2; 2, 5; 1). S' = 20, firm 9.
- Sealer namings (in seal): sealer_0 23 (18), sealer_1 24 (17), sealer_2 23 (13).
- Consequence (DECL-D1-A3 item 4): 20 <= S' < 30, so D1 runs with p_max < 0.005; S' is recomputed after the alignment gate and D1 is VOID (defer to KTLB-4-0841) if it falls below 20, i.e. if any of J2-J5 fails the gate.
- Archive comparison (not evidence): the unavailable archive J seal had S = 43 (11 firm) at D2 without the key sheet.

## DECL-D1-A5
- utc: 2026-09-25T05:59:34Z
- prev_sha256: da6a2039604eba145004343b2650c1cf4e63f730aaa1e6456d455b252dc312c5
- kind: declaration
Amendment 5 to DECL-D1, after the J seal (SEAL-J-D1) and before any render of J exists; pins details the plan left open. Bars unchanged.
1. RAW text side: RAW-F = mean of render slices n//2+1..n//2+5 (+normal side), RAW-B = mean of n//2-5..n//2-1. The RAW text side is chosen ONCE, together with the base text order and before any reader starts, as the slab whose AUC (hercules.metrics.pixel.auc, the raw slab mean before windowing) against the official 0841 human ink labels inside the official supervision mask, pooled over the gated J windows, is higher; the base text order (DECL-D1-A3 item 5) is chosen on the same pixels. Both AUC pairs are recorded; whether RAW side and base order agree is reported, not a bar.
2. Image paths: every D1 reader and canary image lives in one flat folder under a random uuid name (no arm, state, order or window in any path a reader sees); the key maps uuids to window, content window (CHANCE), kind, order and state.
3. Mirror frames: state B images are state A mirrored left-right in the levelled window (x_B = 2135 - x_A). State-B arms are scored against the seal mapped into the state-B frame by the same mirror (letter identities unchanged); the scorer's display maps use each state's own frame (scale 2, origin 0, half-pixel convention of hercules.scorer.display).
4. Canary items are removed from reader outputs before scoring and counted separately (namings per reader); blank items are scored as blank windows.
5. Scoring driver (tools/d1/score_d1.py) is written, unit-tested and hashed before the first D1 reader starts.
Disclosure (I14, section 3.4 "briefs never carry arm names"): the image paths of HANDED-1/-R2/-R3B and PROBE-1/2/3 briefs contained folder names for mirror state or display (e.g. /A/, /B/, /D2/, /D1Q/, /N2/), visible to readers. No brief said which state was mirrored or correct, and the same folder names were used for every reader of a probe, so no result depended on them; audits passed without noting it. From D1 on, paths carry no such names (item 2).

## METRIC-HASH-16
- utc: 2026-09-25T06:06:02Z
- prev_sha256: 0e57d3a756b2fdb0c9d571f92e970a617d6887ad4ac067abfc909dba35e4a868
- kind: metric-hash
D1 read path (DECL-D1, -A1 .. -A5), hashed before any D1 reader job exists: hercules.scorer.d1drive (per-state seals with state B mirrored, display maps per reader item with text/non-text sides from the declared text order and RAW side, canary/foreign item filtering, blank-namings mean over scored records, max per-window mean F_B, the DECL-D1 outcome table with the small-seal p bar, VOID check, sigma_crit), tools/d1/d1_jobs.py (3 fresh fable readers per arm-state; ref stage first), tools/d1/score_d1.py (decisions D1-REF, D1-FAMILY with max-T over BASE-A/B and RAW-A/B, D1-CHANCE; encrypted full outputs; counts-only summaries); 7 + 2 tests incl. a synthetic end-to-end run of both stages (suite 574 passed). Confirmation passes (if reached): 3 passes of 3 fresh fable readers each on the best family arm, pooled; bar pooled summed mean C_net >= 0.25 S'. BETWEEN passes: 5 passes of 3 readers pooled; LOCATOR if pooled summed mean C_net >= 0.20 S' with pooled permutation p < 0.005.

```
a9e1a10b4bb23bca83c7851b3bf147214e231dac3d07406d90fe834a1f304c08  src/hercules/scorer/d1drive.py
b133f939c9f4ee6881a6ea7d699e049e3ba69422b3f3f06a874e0da27d90aef8  tests/test_scorer_d1drive.py
fbf74482854a63860c37eb1abcb08e181ed8a21560229a2be16a2e8f7e5449a0  tests/test_tools_score_d1.py
c6855c74c8c4c5175ab0a9d102d4b96de428057a83465d22fd82b3db7121bafc  tools/d1/d1_jobs.py
6aab32a96df95ba7a56c1d871edaa316bb69d5b1cd4952a5d795fd8384fa1345  tools/d1/score_d1.py
combined_sha256 7ecd4326c09309301544ed0c35138ae6070e1999a9e936b85ab82e86f956cf28
```

## HECATE-SCREEN
- utc: 2026-09-25T06:57:05Z
- prev_sha256: cb72f090ff3662cce05d720e1157ee6ce7ed488b2505f7e74158c7c4fe15a4bf
- kind: result
Result of DECL-HECATE (screen, a gate, never evidence of letters), before any D1 model-arm reader. Builder agent report; logs/d1/hecate_screen_summary.json (sha256 6b90169e28608b4207889ef6f36f34615a8cfea012b22927813bc2366078ddb4), run record logs/d1/hecate_screen_run_record.json (sha256 4934086820345c2f39cbaec2a8d23bb438d7bf3072ec4a911684bceea9437c1d). No image viewed.
- Checkpoints verified: Hecate HF scrollprize/hecate commit 9cb86e500e944b11a06a7020403cde5dffb5bcb2 (public, MIT), hecate_9.6um.pth sha256 809f4f10...; base step-075000 e635558a.... Official hecate.py recipe (stride 32, batch 1), renders sampled directly at 9.6 um by vc_render_tifxyz (--scale 0.975625, -n 16, slice step 9.6 um), predictions mapped back bilinearly to the 9.366 um canvas; base = C2-NT on our 9.366 um render (-n 28, --flip-normals; Pearson 0.9999984 vs the organizer SV).
- Pixels: official 0841 labels (ink = inklabels and supervision; blank = supervision without ink), outside the T shell. The exclusion was STRICTER than declared: every rendered pixel >= 144 vox (128 + render normal offset + interpolation + cloud spacing) in 3-D from any J point; the renderer never sampled within 128 vox of J. The supervision mask barely leaves the T shell: 75,093 pixels (29,716 ink, 45,377 blank; 0.066 cm^2), all on segment 214732 (w00: none; 022814: none after masks).
- AUC (hercules.metrics.pixel.auc): Hecate forward 0.67834, reverse 0.46986; base forward 0.57576, reverse 0.63398.
- Bar (Hecate best-order AUC >= 0.75 AND >= base best - 0.02): 0.678 < 0.75. Verdict: HECATE screened out on 0841 at AUC 0.678; no reads are spent on it.
- Limitation and note (not a bar): the screen rests on one segment and 0.066 cm^2. On the same held-out 0841 pixels the base model is near chance (best order 0.634), consistent with the archive's foreign-text AUCs of 0.72-0.73 being under the 0.75 bar (section 4.D1).

## TEXT-ORDER-D1
- utc: 2026-09-25T07:38:29Z
- prev_sha256: 42b6da0883e0d030a836ba8bbde9489d66e1f3581ca75288bde45e40d7f73b8b
- kind: result
D1 chain result and the once-only text-order choice (DECL-D1-A3 item 5, DECL-D1-A5 item 1), recorded before any D1 reader starts. Builder agent (numbers only); build summary logs/d1/d1_build_summary.json (sha256 ec5aa8cf759dae0478984d476784aa19bf57f1d725710774af03beec6ad50c6f), gate logs/d1/d1_build_gate.json (sha256 9cd88a987345401ddd6b5eb09eb135286decd50e96b86efdc1f91d862bccd4bd).
- Renders: official vc_render_tifxyz -n 31 at the metadata voxel size over each levelled window + 256 px; render-valid fraction J1 0.811, J2 0.714, J3 0.938, J4 1.000, J5 0.834.
- Alignment gate (pipeline alignment_gate, METRIC-HASH-3; our slice 15 vs organizer SV mean of slices 13-14): J1 0.964, J2 0.960, J3 0.965, J4 0.973, J5 0.965, all at shift (0, 0): all PASS. No J window is dropped; S' after the gate = 20 (small-seal regime: p_max < 0.005). Blanks and canary 0.962-0.988 (information).
- C2-NT (no TTA, both orders; forward = render slices 7..23 ascending). AUC against official 0841 labels inside supervision (all render-valid), pooled over J1-J5 (585,250 ink, 2,004,194 blank px): base forward 0.73332, base reverse 0.54095, RAW-F 0.52590, RAW-B 0.50249. Per window base forward 0.692-0.774.
- CHOICE (never revisited): TEXT ORDER = forward; RAW TEXT SIDE = F. They agree under forward <-> F (reported, not a bar).
- Note (not a bar): the base model detects 0841 ink at AUC 0.73 pooled on J (archive foreign-text 0.72-0.73; section 4.D1 bar 0.75); the RAW slabs are near chance (0.50-0.53).

## DECL-D1-A6
- utc: 2026-09-25T07:38:29Z
- prev_sha256: 0235cf2e0778f7b121d4ab197ca9ef07e4c544d5217db6b5f5d17be3a7b8fba6
- kind: declaration
Amendment 6 to DECL-D1 (display masking), before any D1 reader has seen any D1 image, citing the builder's note: the built BASE images carry model output on pixels without rendered data (render-invalid; up to 29 % of J2, mean output 22-67 there), while the reference, sealer and REF images are zero outside valid data. Decision: every BASE and RAW display image is set to 0 outside the window's render-valid mask (any of the 31 render slices nonzero) before INTER_AREA; RAW's 1-99 % window is computed over render-valid pixels only (builder.linear_window_ct valid mask). The mask is geometry only and identical for both orders and both states, so it carries no order or text information. The images built before this amendment are withdrawn unread (moved aside with their key, kept for the audit); new images and a new key are built. REF images are unchanged. Everything else unchanged.

## D1-REF-RESULT
- utc: 2026-09-25T07:46:58Z
- prev_sha256: 74d1fc134c8f396c0117d728f98265a2d5ba3d0a222d2a72418c94396e555e5f
- kind: result
D1 REF ladder (calibration arms, read first; DECL-D1-A3 items 6-8). 12 fresh fable readers (sealed-output; all audited VALID; 0 discarded; 0 foreign items), scored by tools/d1/score_d1.py ref (METRIC-HASH-16; score_decision METRIC-HASH-0; 5000 permutations, seed 20260924). Counts-only summary logs/d1/d1_ref_summary.json (sha256 7c3884a2b43dc9b50fb41ce03fc1c3503239551eca0623dcb550bbaace5d7cd8); full scorer output age-encrypted seals/d1_results_ref.age (sha256 6caf73ccc858d30d5b5f8ce9aec56eddff2ad7e7f9cbace722768fca8cf65193).
- S' after the gate = 20 (J1 0, J2 6, J3 2, J4 5, J5 7).
- Summed mean C_all at R 250 / C_net / C_firm / p: REF0 16.0 / 11.37 / 8.33 / 1/5001; REF015 12.0 / 8.44 / 5.00 / 1/5001; REF030 10.33 / 6.42 / 4.33 / 1/5001; REF045 6.67 / 4.30 / 2.33 / 4/5001. Per-window REF0 mean C_all: J1 0, J2 4.0, J3 1.67, J4 5.0, J5 5.33.
- VOID check (REF0 summed mean C_all < 0.5 S' = 10): 16.0, NOT VOID. D1 proceeds to the model arms.
- sigma_crit = 0.30 mm (largest ladder sigma with C_net >= 50 % of sigma 0's 11.37).
- Blanks: mean 0.0 namings per reader in every REF arm. Canary (attention, reported only): 3-21 namings per reader.
- Interpretation (not a bar): with the K_D2 display and fable readers, the official 2.4 um reference maps of unseen PHerc0841 are consistently legible (80 % mean recall of a 3-sealer seal by fresh readers), and legibility falls smoothly with blur. D1 now asks whether our 9 um base or RAW maps carry that legibility.

## D1-RERUN-CHANCE
- utc: 2026-09-25T08:22:54Z
- prev_sha256: cbeeec75e1e1a63c0ec023a307eda6eccec34678c1df65dc98cc75102915696a
- kind: decision
D1 model-arm harness event (no data affected). The account's API usage limit interrupted the 18 model-arm readers. All 12 BASE and RAW readers had already written their sealed answers (6 died after the write, before the hand-back); their transcripts audit VALID. The 6 CHANCE readers (jobs b4532d81, 11b87ef9, a8e81a4a, bf5c63cd, 03bfd924, 508d78b9) died before any tool call: 0 image reads, 0 writes (transcripts retained; /work/jobs/agent_map_dead.txt). Decision: each of the 6 CHANCE jobs is re-run once by a fresh agent with the identical brief and output path (no answer existed; the dead agents saw no image). If a re-run dies again after reading images, that job is discarded and a new job is created for its slot. No scoring code, bar, item map or image changes.

## D1-VERDICT
- utc: 2026-09-25T09:06:03Z
- prev_sha256: 48c416396ada9f4a243caed21fd708b107ee8644fa907f5a75e1dd6a025e6b1d
- kind: result
VERDICT for DECL-D1 (KTLB-3R, zero-shot 9 um reading of unseen PHerc0841), with -A1 .. -A6. Auditor: multi-lens workflow (4 independent fresh agents: re-derivation with own code and exact permutation enumeration, declaration timeline, harness/transcripts, adversarial VOID-seeker; plus synthesis): PASS 4/4, 0 invalidating findings; logs/d1/audit_d1.json (sha256 63c8044ea947e7e1006fc4e992e17b5d3334cabe917631b6ff13e053ed635127) and logs/d1/audit_d1_{rederive,timeline,harness,adversarial}.json. Model-stage summary logs/d1/d1_model_summary.json (sha256 22b2a0faf24b85c4e5288cdbb8d08e05645b4356413c577b4859b0c4bd0a7b7a); encrypted full output seals/d1_results_model.age (sha256 26538c60d138c6552d1b8ebdae2cd6ac83d671380c47072dea6d2ed163dbc993).
- Seal and gate: S' = 20 (9 firm), all J windows pass the alignment gate (NCC 0.960-0.973 at shift 0); small-seal regime (p_max < 0.005 would be required for PASS).
- REF ladder (D1-REF-RESULT, re-derived exactly): REF0 C_all 16.0, C_net 11.37 (exact 11.3714), NOT VOID; sigma_crit 0.30 mm.
- Model arms (18 fresh fable readers, all VALID; text order forward, RAW side F): BASE-A, BASE-B, RAW-A, RAW-B, CHANCE-A, CHANCE-B each named 0 letters on every J window and blank (0 of 180 J panels and 36 blank panels; rows Y on none): C_all 0, C_net 0, F_B 0, blank namings 0, p_max 1.
- VERDICT: FAIL (C_net 0 <= 0.10 S' = 2.0, and p_max 1 >= 0.05). No USABLE or LOCATOR arm. J decisions used: 1 of 3.
- Canary (attention only, not a bar): BASE and CHANCE readers named 5-10 letters each on the base-trained 0139 w044 window's base map (43 + 43), all on the forward panel; RAW readers named 0 anywhere, so the RAW arms had no working attention control (RAW AUC 0.50-0.53, near chance).
- Adversarial checks (numbers only): D1 frame identical to the seal frame (affine difference 0.0; REF0 display = sealer images); base maps carry signal in the right place (base-forward AUC vs seal-frame labels 0.70-0.76, mirrored 0.48-0.55; correlation with the reference r 0.27-0.50, canary 0.62), with less letter-scale contrast than the canary (DoG std 10-12 vs 14.9): a weak map, not a display failure; all 30 answers intact.
- Interpretation (not a bar): with the calibrated display and reader, the official 2.4 um reference maps of unseen 0841 are legible (80 % seal recall), while our 9 um base (C2-NT) and RAW maps of the same windows are not legible at all; the same readers do see letters in the base map of base-trained papyrus. The base model finds 0841 ink (AUC 0.73) but does not resolve strokes on unseen text, as the archive found (section 4.D4). Consequence (DECL-D1): Route Z has no reader from D1; D2 runs regardless (blocked: no GPU); K1 JULY now depends on D2 and D3.
- Corrections (I17): D1-RERUN-CHANCE says 6 BASE/RAW readers died after writing; the transcripts show 4 (RAW-A r2, RAW-B r0, r1, r2), all with complete valid answers. DECL-D1-A4 cites /work/jseal/work/check.json sha256 03e5d55..., which was later overwritten by the post-A4 blank check (now 39bfbefa...); the J1-J5 fields are unchanged (check.log, check_a4.log).
- Disclosures (I14): (1) after scoring, the orchestrator decrypted the 18 model answers once more (purpose d1-crosscheck-counts) to count namings per item role and content window before the audit; logged in logs/key_reads.tsv, counts only, outcome unaffected; it was not mentioned in the commit. (2) The J-seal blank picker's image paths contained the folder name 'blank' (and the sealers' 'J'), before the flat-path rule of DECL-D1-A5; the picker confirmed both blanks (0 letters); the D1 blank bar used reader namings (0 on blanks). (3) The 18 model brief files carry a trailing newline absent from the delivered prompts (content identical). (4) src/hercules/harness/jobs.py (brief header) had no METRIC-HASH; hashed now (METRIC-HASH-17).

## METRIC-HASH-17
- utc: 2026-09-25T09:06:03Z
- prev_sha256: b290eee0c48b6651d40cc736e58a110df6a61146ee27717505288f2e1ecb29e6
- kind: metric-hash
Harness job builder (brief header template and job records), hashed as recommended by the D1 audit; unchanged since before PROBE-1.

```
349dcc1248e80f181125786985f6783dae69f941e36e6c4174ebfacd0c814c29  src/hercules/harness/collect.py
02d9bd781beb4d3d26bb26efcc8ab4c6fd5c2b1d64bffcba883d2daaf947f0ae  src/hercules/harness/jobs.py
combined_sha256 2a0a8aac5dd4f8eacf35c692126b8789fe737f67aa1c788ae5bde9661da13e17
```

## DECL-D3-FEAS
- utc: 2026-09-25T09:07:27Z
- prev_sha256: 2b2c66ae78b31a4003aa2952e9169f9fcc343db007791e7d3957146bd4f70bf7
- kind: declaration
D3 feasibility count (DECL-D3D4: "Fold A = 0841 papyrus >= 128 vox from every sealed window (organizer segments outside shells plus own traces), needing >= 280 text patches, else INFEASIBLE"), declared before any count exists, after D1-VERDICT (J decisions used 1 of 3; D3 would be J's next decision, CTRL = base since D2 has not run).
- Material now: the 3 PHerc0841 organizer segments on the 9.366 um canvas (bank /work/bank/0841). No own 0841 traces exist yet (T0 not run); if own traces are produced before the D3 date (2026-10-17) the count is repeated on them under this same rule.
- Sealed windows: J1-J5 (SEAL-J-D1). Exclusion: every canvas pixel whose 3-D mesh point lies < 128 vox (Euclidean) from any mesh point of any J window (all 3 segments), plus the J windows themselves.
- Patch: the base model's 128 x 128 px tile (1.2 mm) on the organizer canvas. PRIMARY rule: stride 64 px; a tile is eligible if >= 90 % of its pixels are valid (bank valid9) and none is excluded; a TEXT patch is an eligible tile whose official reference map (ref9) has >= 2 % of valid pixels >= 150. Reported also (not deciding): stride 128 with >= 5 % (strict) and stride 32 with >= 1 % (generous), and counts using the official human ink labels (label > 0 inside supervision) instead of ref9.
- Decision: PRIMARY count >= 280 -> D3 feasible on current material (a D3 build and CPU timing test follow); < 280 -> D3 INFEASIBLE on current material (recorded now; final at the D3 date unless own traces add material).
- Method: two independent counts with independently written code (numbers only, no image viewed); they must agree exactly on the PRIMARY count, else the discrepancy is resolved before recording.

## D3-FEAS-RESULT
- utc: 2026-09-25T09:26:00Z
- prev_sha256: 50fb5c4f254fd5f1407d9420fa704d940e3db4bbe91ebdb0758b32d84dbbd174
- kind: result
Result of DECL-D3-FEAS (two independent code counts, reconciled; numbers only). Files logs/d1/d3_feas_count_A.json (sha256 7517988b8d352619149173686f9086c63efdaa614b7dc9750502e13fc0c21f34), d3_feas_count_B.json (a4a8caa7695001ae7e5ae9455c3882fda861e8d48db9c48e65ef780cdf48d94e), d3_feas_reconcile.json (a68860a6b1e15bac07c98371dc9f1fcec7aa5f4426bd58019016972ce34dc4a8).
- PRIMARY (128 px tiles, stride 64, >= 90 % valid, no pixel < 128 vox (3-D) from any J mesh point, ref9 >= 150 on >= 2 % of valid px): eligible 309 / 317 / 240 = 866; TEXT 122 / 111 / 73 = 306 (w00 / 214732 / 022814). A and B agree exactly on every segment and on pixel-level exclusion (minimum retained 3-D distance 128.0001 vox).
- Decision: 306 >= 280 -> D3 FEASIBLE on current material (margin 26). Per DECL-D3-FEAS a D3 build and a CPU timing test follow (D0-HW: D3/D4 run only if <= 12 h per arm).
- Sensitivity (reported, not deciding): strict (stride 128, >= 5 %) 65; generous (stride 32, >= 1 %) 1341; official human labels instead of ref9: primary 20, strict 5, generous 88 (the labels lie almost entirely inside the J exclusion). Non-excluded valid area 4.275 cm^2, of which ref9 text 0.246 cm^2. Fold-A teacher labels would therefore come from the organizer reference maps, not from human labels.
- D4 on current material: DECL-D3D4 needs KTLB-4-0841 (>= 5 windows of 2 x 2 cm with >= 5 nameable letters on our own 2.4 um maps, outside the T shell, sealed before any 9 um map). B0841-BANK: the 0841 organizer area outside the T shell is 1.51 / 1.52 / 1.26 cm^2 per segment, so no 2 x 2 cm window fits: KTLB-4-0841 is infeasible without our own 0841 traces (T0 not run). D4 therefore defaults to not passed at its date unless own traces supply material, and Route F (requires D3 AND D4) cannot run on current material whatever D3 shows.

## DECL-D3-A1
- utc: 2026-09-25T09:47:01Z
- prev_sha256: 60a538b4a8cb6d9311ca5377e4ee7faf9ff8b9b818f5e9127754f7f05e97deda
- kind: declaration
Amendment 1 to DECL-D3D4 (D3 = FOLD-0841), pinning the recipe, arms and reads before any D3 training step, D3 map or D3 read exists; citing D3-FEAS-RESULT and the CPU timing test logs/d1/d3_timing.json (sha256 210d9dc15fd5c9db2400b5c17cd3ec67eacf7824557db54fcb6d1bb48dae4eaf: 1.69 h per 2000-step arm at batch 8, fp32, 3 threads; D0-HW bar <= 12 h per arm: MET, so D3 runs).
1. CTRL = base (D2 has not run). Every arm starts from base ink_9um hybrid_3d2d seed42 step-075000 (sha256 e635558a...9cab), official model, loss (smoothed BCE 0.5 + 0.25 Dice), robust_mad normalisation, official augmentations, from the official trainer villa 41701aa vesuvius/ink_detection/training/train.py (sha256 f87f882d...) run without accelerate; section 4.D2 archive fine-tune recipe: input slices 7..23 of the -n 31 render (centre 15, jitter +-2), forward order, AdamW lr 2e-5 constant, weight decay 3e-5, batch 8, fp32, 2000 steps, fixed seed 20260925 per arm, data-loader seed fixed.
2. Fold-A teacher labels: the 306 PRIMARY text tiles of D3-FEAS-RESULT (0841, >= 128 vox from J; renders -n 31 at 9.366 um with --flip-normals, crops >= 144 vox from J as in the timing test); target ink = ref9 >= 150, blank = ref9 <= 100, rest and invalid ignored.
3. Replay (the other half of every FA/NULLA/REVA batch, and all of CTRL's batches): base-training papyrus of PHerc0139 with official human labels (native 9.362 um label set 20260918 on w035, w039, w040, w041, w044; ink = label > 0 inside supervision, blank = supervision without ink), renders -n 31 at 9.362 um with --flip-normals, 128 px tiles with >= 90 % supervised pixels, a fixed pool of up to 3000 tiles drawn uniformly by seed 20260925 across the 5 segments. Replay is base-trained data: it tests nothing and only controls forgetting.
4. Arms (K6: 4): FA = 4 fold-A + 4 replay per batch; NULLA = FA with the fold-A label tiles permuted across fold-A tiles (one fixed permutation, seed 20260925, no tile keeps its own labels); REVA = FA with every fold-A input stack reversed in depth (labels unchanged); CTRL = 8 replay per batch, 2000 steps.
5. Maps: each arm's final checkpoint runs C2-NT-style inference (official infer, no TTA, both orders) on the D1 renders of J1-J5, the 2 w053 blanks and the canary; the text order stays forward (TEXT-ORDER-D1, never revisited). Displays exactly as D1 BASE v2 (K_D2 key sheet, D2 1068 px, masked to render-valid, states A and B, LEFT/RIGHT = the two orders), flat uuid paths, new uuids.
6. Reads: 3 fresh fable readers per (arm, state) = 24, sealed-output, D1 session structure (all 5 J windows + canary + 1 blank), configs/briefs/k_d2_pairs_task.txt. Seal: SEAL-J-D1 (S' = 20); scoring as D1 (score_decision, 5000 permutations, state-B mirrored seal) by a D3 driver hashed before any D3 read.
7. PASS (DECL-D3D4 unchanged): best FA state summed mean C_net >= CTRL (same state) + max(3, 0.1 S') = + 3, with p_max < 0.01 (max-T over FA-A and FA-B); NULLA and REVA <= CTRL + 1 (same state, C_net); F_B(FA) <= F_B(CTRL) + 1; no J window with FA > 1 below CTRL; w053 blob-f180 of FA's text-order map on both blanks <= 0.0272 (hercules.metrics.pixel.blob_f180). Otherwise not passed. LABEL-EQUIV (teacher labels vs organizer map on fold A) reported. J decisions used would become 2 of 3. Auditor before the verdict. Default: not passed at 24 h after 2026-10-17.

## METRIC-HASH-18
- utc: 2026-09-25T09:50:38Z
- prev_sha256: af627521d4a9bc14ba549be5822f306a477940f8e910eaffd192e922ff618f25
- kind: metric-hash
D3 read path (DECL-D3D4, DECL-D3-A1 items 5-7), hashed before any D3 map, image or reader exists: hercules.scorer.d3drive (within-state D3 bars: FA >= CTRL + max(3, 0.1 S'), p_max < 0.01 over FA-A/FA-B, NULLA/REVA <= CTRL + 1, FA F_B <= CTRL F_B + 1 per reader, no J window with FA mean C_net more than 1 below CTRL, blank blob-f180 <= 0.0272; 11 tests), tools/d1/d3_jobs.py (3 fresh fable readers per arm-state, D1 session structure, pairs brief), tools/d1/score_d3.py (decisions D3-FA, D3-CTRL, D3-NULLA, D3-REVA; seal SEAL-J-D1 with state-B mirror; text order forward; encrypted full outputs; counts-only summary) with a synthetic end-to-end test (suite 591 passed).

```
c84aa0535f1b4582b20dc77103520f31dba4d2a36e07e2346b8562f193a6dbe5  src/hercules/scorer/d3drive.py
15ef4a966749a714ae082fd8b02271bf4bf333ae4f794fab64876d5f8b40b7ef  tests/test_scorer_d3drive.py
124bafe097cd54696e599471d430b2f4e90db3f1aabc4e385e3f33be286b165a  tests/test_tools_score_d3.py
90d768997d763bc658a8625242587a9c2a70056665e77edc1e890d7a07983812  tools/d1/d3_jobs.py
40e574112e7a88f9e90e5d7153bda664254577475c8b770a3a0b98f672ccb81b  tools/d1/score_d3.py
combined_sha256 afd5e1569c6aebba82264f353993a05b3e01014b93c7e3dc29a41eb0bb6a489e
```

## DECL-D3-A2
- utc: 2026-09-25T10:25:41Z
- prev_sha256: 448755984b980db0d731ad7f4f5cb3bb04a52191ba6b975321f508a70c0caa7e
- kind: declaration
Amendment 2 to DECL-D3D4 / DECL-D3-A1, before any D3 training step (no arm has trained; the container restart at ~10:20Z stopped the pool build), citing the builder's deviation list logs/d1/d3_builder_deviations.json (sha256 a00bc65b92c65ab61bc99e39d99103f83488a0c693a073b24c36fe434d6d3a4d).
1. Fold-A pool: the PRIMARY text tiles whose whole -n 31 render slab stays >= 128 vox from every J mesh point, i.e. tiles with every mesh-valid pixel >= 144 vox from J (the timing-test margin); this drops 18 of the 306 tiles (their mesh points lie 128-144 vox from J, so +-15 vox slab samples would come nearer than 128 vox). Pool = 288 tiles (>= 280, the DECL-D3D4 floor). A tile whose render fails twice is dropped and recorded; if the pool falls below 280, D3 is INFEASIBLE on current material.
2. Replay pool: every 0139 tile on the official base-training patch grid (stride 32) with >= 90 % supervised pixels on w035, w039, w040, w041, w044 = 2643 tiles (below the 3000 cap, so the seed orders the draw only). 578 w044 replay tiles overlap the D1 canary window; the canary is attention-only and every arm (CTRL included) sees the same replay, so this is reported only.
3. Sampling: epoch-wise permutation streams without replacement from two child seeds of SeedSequence(20260925) (fold-A, replay); batch = 4 fold-A then 4 replay (CTRL: 8 replay); FA, NULLA and REVA see the identical tile, jitter and augmentation sequence (paired arms). REVA reverses each stored 21-slice fold-A stack before the official window/jitter; the official in-plane augmentations never undo it. Replay labels: official 0/255 ink labels, ink outside supervision ignored.
4. Restart safety: each arm saves a resumable checkpoint (weights, optimizer and all RNG states) every 250 steps and keeps only the latest; a restarted arm resumes from it and the resumption is logged (bitwise identity with an uninterrupted run is not guaranteed and is not required). Final weights only are kept after an arm completes.
Everything else in DECL-D3-A1 is unchanged.

## DECL-D3-A3
- utc: 2026-09-25T10:54:44Z
- prev_sha256: 16d7518119672aaa88bddc4bd678c8ad7d6f3413c955d7e2a061660c36e4a760
- kind: declaration
Amendment 3 to DECL-D3D4 / DECL-D3-A1, declared before any D3 map, display or read exists (CTRL is training; no arm has finished). It pins stage 2 details that DECL-D3-A1 items 5 and 7 left open. Bars are unchanged.
1. Inference: tools/d3/d3_infer.py = the D1 inference script (/work/d1/scripts/d1_infer.py: official infer, --direction both, batch 4, 1 worker, --no-compile, no TTA) with the checkpoint replaced by /work/d3/runs/<ARM>/model_final.pth (sha256 recorded when the arm completes). Outputs go to /work/d3/infer/<ARM>/<window>/. It uses 1 thread while an arm is training and 3 threads after training ends; thread count changes only floating-point summation order, and the counts used are reported. Each arm is inferred as soon as it completes, in training order. The script is resumable per (arm, window).
2. Pre-check E1, before any D3 arm map: the base checkpoint (base state_dict + its embedded config, step 0) is written in the model_final format and run through d3_infer.py on the canary window (never a J window). PASS if both orders are bitwise identical to D1's canary base maps, or if they differ by max |diff| <= 1 (uint8) on <= 0.1 % of pixels, attributed to thread count and reported. Anything else stops stage 2 until the cause is found and recorded.
3. Pre-check E2, before any D3 display: tools/d3/d3_build.py is run once in dry-run mode with the D1 base maps in place of an arm's maps, writing to a scratch folder that no one opens and that is deleted afterwards. PASS if all 32 dry-run BASE PNGs (8 windows x 2 orders x 2 states) have sha256 values found in /work/d1/manifest.json (identical to the D1 BASE v2 displays). Anything else stops stage 2 until the cause is found and recorded.
4. Displays and key: exactly D1 BASE v2 (DECL-D1-A6): masked to render-valid, states A and B, 1/2 INTER_AREA, raw 0-255, K_D2 key sheet, one flat folder /work/d3/img/<uuid4>.png with new uuids, written in shuffled order with equal mtimes. Key /srv/scorer/d3_key.json (0400, O_EXCL, never printed): images {uuid: window, arm, kind BASE, order fwd|rev, state A|B}; windows {w: set J|blank|canary, gate: {pass}} copied from the D1 gate record (/work/d1/work/gate.json), with the gated J set asserted equal to D1's. Manifest /work/d3/manifest.json (path, sha256).
5. blob-f180 (DECL-D3-A1 item 7): hercules.metrics.pixel.blob_f180(map_u8, area_cm2, valid) on the arm's official forward map (text order), decoded as in D1 and cropped to the 2136 px levelled state-A window (the full-resolution array the display path starts from, before masking and downscale). valid = render-valid mask (any of 31 slices nonzero). area_cm2 = n_valid x (voxel mm)^2 / 100, with voxel size from the volume's metadata.json (I9), the value D1 used. Deciding value: FA on both w053 blanks. Reported (not deciding): all 4 arms, both orders, both blanks. It is written as /work/d3/blob_f180.json {blank window id: FA value}, and the full table goes to logs/d1/d3_blob_f180.json.
6. LABEL-EQUIV (reported, never deciding): on the 288 fold-A pool tiles, the teacher labels (ref9 >= 150 ink, <= 100 blank) are compared with the official human ink labels (label set 20260918, label > 0 inside supervision = ink, supervision without ink = blank), on pixels where both are defined. Reported: overlap pixel count, the 2 x 2 confusion counts, agreement fraction, and Cohen's kappa. Also the same comparison over all 306 PRIMARY tiles. Numbers only.
7. The builder opens no image; the only D3 display viewers are the 24 readers of DECL-D3-A1 item 6. Every command is logged to /work/d3/work/ledger.tsv, and a stage-2 record (script hashes, E1/E2 results, map hashes, thread counts) is written to logs/d1/d3_stage2.json before d3_jobs.py runs.

## D3-PRECHECK-RESULT
- utc: 2026-09-25T11:25:38Z
- prev_sha256: aac2d76decc3433e317a0f0b9029fe6373dad3d7e61c090a46760d29c742f21d
- kind: result
Result of the DECL-D3-A3 pre-checks and the LABEL-EQUIV report. All before any D3 arm map exists (CTRL still training). Numbers only; no image was opened.
- Scripts, sha256 (tools/d3/, byte-identical to /work/d3/scripts/):
  - d3_infer.py 77b7662438d013e663ed938d49d39f9df879c30b9c18d554d75c8ad3ccb05efe
  - d3_build.py a5b928c743c294df7d03bcb03b98fc7909f41d57bb0cd79f7391a725de3afb6b
  - label_equiv.py 4352125e45f6f1d9675fc157e7049806ee11bb11e0b6b2dd2e7f26b2f384f889
  - infer_arms.sh 2c6d1fe83dbf2e6dad85d1123b0ce2eaf7e1e4b8aacc147840e9719297850abb
  - start_d3_stage2.sh c17c975557fcd891b0b083e1cb2b6e60650b6f5d0c99feeccf266e45a5f41779
  - d3_e1.py 9ebab8254ab2eb931b7c57307bdca93d13974d014b36a473cc52b1f803e3d6c6
  - d3_ledger_run.sh 6a0d341bb475600f96838f2fdd7ffd9300d9630106cb60325f50de90af17f84a
- E1 PASS (logs/d1/d3_e1.json, sha256 222d1170033565c9bdee199ea88a73985f0de7c853e2a20ccab4974cbe030483).
  - The base checkpoint was re-saved in the model_final format (all 508 tensors bitwise equal to base, config identical, step 0; sha256 dd1a75c634a0654afa46c09bb54fa18f4a053fdf8a804a56e638e0b656dc9262). Official infer loaded it with 0 missing and 0 unexpected keys (layers 7..23 forward, 23..7 reverse, no TTA).
  - On the canary window at 1 thread, vs D1 at 2 threads (uint8, 2648 x 2648): forward 108 px differ (0.0015 %), reverse 71 px (0.0010 %), max |diff| 1 in both. This is within the declared tolerance (<= 1 on <= 0.1 %) and is attributed to the thread count.
  - The orchestrator recomputed these counts independently and they match.
  - The BASE0 checkpoint was then deleted to save disk (its hash is recorded; tools/d3/d3_e1.py rebuilds it).
- E2 PASS (logs/d1/d3_e2_dryrun.json, sha256 5a2896f12ee49136b201e865c50f3f0862b49d758f3128ac2c2fea49ed4f7ca9).
  - The dry-run over the D1 base maps wrote 32 BASE PNGs; 32 of 32 sha256 are found in /work/d1/manifest.json (8 per order x state) and all 32 are distinct. The folder was deleted without being opened.
  - The orchestrator re-ran it independently with the same result (logs/d1/d3_e2_dryrun_recheck.json, sha256 4e6eac5b7b29637e28430dadc80c5dc39d70fe231140110517b0b825f8411469). Only the uuid-dependent tree/key hashes and the times differ.
- Key windows convention: J windows carry their D1 gate pass (J1-J5 all true). Blanks and canary carry null (their D1 gate was not binding). No scorer reads the gate of a blank or canary window (d3_jobs.py and score_d3.py use set == J and gated_J only).
- LABEL-EQUIV (reported, not deciding; logs/d1/d3_label_equiv.json, sha256 db2d529286efab68fe870a53432946143aa19fe2ada73c0d92d0b434e1980911).
  - Teacher labels recomputed from ref9 equal the pool arrays on 288 of 288 tiles. Human-label overlap exists only on segment 20260220214732: 26 of the 288 pool tiles and 33 of the 306 PRIMARY tiles.
  - Unique pixels, 288 pool tiles: overlap 64273 px; teacher ink / human ink 21501, teacher ink / human blank 8729, teacher blank / human ink 3517, teacher blank / human blank 30526; agreement 0.8095; kappa 0.6139.
  - Unique pixels, 306 PRIMARY tiles: overlap 88545 px; agreement 0.7966; kappa 0.5927.
  - Summed per tile (overlapping tiles double count): pool kappa 0.5677, PRIMARY kappa 0.5743.
  - The teacher labels therefore agree with the human labels only moderately where both exist (about 20 % of overlap pixels disagree, mostly teacher ink where human blank).
- Reported, not deciding: blob-f180 of the D1 base forward maps on the blanks is 0.00121 (x1536) and 0.01284 (x7168). Voxel size 9.362 um from metadata.json; valid areas 3.850 and 3.803 cm^2.
- Ledger defect: 4 builder rows record "cpus=1/1" instead of "cpus=1/4" (nproc follows the thread export). They were left unedited; the wrapper is fixed.
- The watcher tools/d3/infer_arms.sh has been running since 2026-09-25T11:21:35Z and infers each arm when its model_final.pth is complete.

## DECL-HRV-1
- utc: 2026-09-25T17:37:32Z
- prev_sha256: 3598dc399ceafd5c650d65d813c9b332518b5eb1afa37df92b4d23ad9c10e98a
- kind: declaration
Owner-requested human-review set HRV-1, declared before any eligible-volume image data is fetched.
Purpose: the owner asked to see eligible-volume images with their own eyes. HRV-1 is a viewing set only. It is never evidence, never read by any LLM reader, and never used to build or select a sealed benchmark. Every I2 display rule applies.
1. Material: PHerc0800 (6 organized segments) and PHerc1447 (15 organized segments) are the only eligible volumes with official organizer segments (tifxyz mesh + surface volume) in the D0 catalogue (data/catalogue/eligible_products.json). PHerc1203 has only raw auto-grown folders with no tifxyz mesh and is not included. Both volumes are MAY protocol at 8.64 um (metadata.json, I9). The base ink model was trained at 9.362 um (JULY), so its maps here are an out-of-protocol transfer, and every file says so.
2. Products:
   (a) RAW overview, per organized segment: the mean of the middle 5 layers of the official surface volume (or of our -n 31 render of the official mesh, slices 13..17), shown with a fixed linear 1-99 % window over valid pixels. Downscaled only with INTER_AREA, to a long side of at most 4096 px. One PNG per segment.
   (b) Ink maps on 2 x 2 cm windows: the official base checkpoint ink_9um step-075000 (sha256 e635558a...9cab), run with the C2-NT command (official infer, --direction both, no TTA) on a -n 31 render of the official mesh with --flip-normals from the official volume zarr. Raw 0-255 output, both orders, full resolution, masked to render-valid. Windows are chosen without looking at content: per segment, one window drawn uniformly by seed 20260925 among the 2 x 2 cm windows with >= 90 % mesh-valid coverage. Order: round-robin over segments, alternating volumes, so both volumes appear early.
3. Viewing: the images go to the owner only. The orchestrator and all agents never open, display or describe them; numeric checks only (valid fraction, mean, std). Each file sent is logged in logs/views.tsv (viewer: owner). Nothing is published (I12). PNGs are not committed; logs/hrv1/manifest.json (paths, sha256, segment, window, seed draw) is committed.
4. Consequences for claims (SG bars unchanged): a region that the owner saw or pointed to can become a candidate only through the unchanged SG path, with fresh blind readers and the empirical null. FL-14 would then disclose that it was selected after human viewing. The owner's own reading is never evidence (I4).
5. Resources: HRV-1 runs at lower priority than D3 (nice 10; 1 inference thread while D3 trains or infers, 3 after). Renders are deleted once their PNGs and hashes exist, so disk stays under 1.5 GB. This is not a decision and uses no sealed benchmark.

## DECL-P4-1
- utc: 2026-09-25T17:43:52Z
- prev_sha256: 73c51c825d8d72925c6343086580b79f3d1dc421a1cd5b1c514e8dff27c100e0
- kind: declaration
Owner-directed programme P4: PHerc. Paris 4 (Scroll 1) title search, targeting the open "PHerc. Paris 4's Title Prize" ($50,000; data/catalogue/prize/prizes_20260924.rendered.txt lines 310-330). The requirements are a tifxyz mesh of the title region with a low-distortion flattening, plus an image in which the organizers' papyrologists can read the title. Paris 4 is not a First Letters volume. This is declared before any Paris 4 volume, mesh, label or map is fetched.
1. Reconnaissance, now (metadata and official pages only, no image or CT chunk viewed): the Paris 4 scans and volume ids in the bucket, official segments and meshes, the official ink labels (ink_9um aligned set phercparis4-w00..w09) with the volume they are aligned to, official ink predictions, and every official statement locating the expected title region. Output: logs/p4/recon.json.
2. P4-A, reproduction check. It runs only after the D3 maps are finished, so D3 keeps priority.
   - Model: the official base ink_9um step-075000 (C2-NT chain: official infer, both orders, no TTA; -n 31 --flip-normals render of the official mesh on the scan the labels are aligned to).
   - Windows: one 2 x 2 cm window per labelled Paris 4 segment, drawn by seed 20260925 among windows with >= 90 % label-supervision coverage.
   - Metrics, reported only (no bar, no decision): pixel AUC and the Dice at the threshold that maximises Dice on the other windows (leave-one-window-out) of the forward and reverse maps against label > 0 inside supervision.
   - The Paris 4 labels are very likely part of ink_9um's training data, so P4-A measures fit to training data, not generalisation, and it is labelled that way.
   - No output is tuned, edited or selected to resemble the known text. "Matching the ground truth" is measured, never produced.
3. P4-B, title search. Its region, material and method are declared in DECL-P4-2 after reconnaissance and before any title-region map exists. The title prize is judged by the organizers' papyrologists, so a P4-B candidate goes to the owner only when: (a) blind readers (fresh, sealed-output) name letters there that beat an empirical null of >= 40 matched off-sheet / non-text-order / same-band tiles, and (b) the image is produced by the declared chain with I2 displays. Title words are never inferred from the known text's content or from scholarship; only imaging evidence counts (I1, I13).
4. Owner viewing of Paris 4 images follows DECL-HRV-1 items 3-4 (owner only, logged, not evidence).
5. Resources: HRV-1 and P4-A share the CPU after the D3 maps (nice 10). Disk stays under 1.5 GB per programme. No compute is created.

## DECL-OFFLOAD-1
- utc: 2026-09-25T18:05:46Z
- prev_sha256: d3570c1d60dd6c4a90f843b1aee775ca3f3a63176b85e5c0a8a1e5d7b5277551
- kind: declaration
Owner-directed disk doctrine. The disk has about 3 GB free; the owner rejected deleting existing data, and nothing was deleted.
1. Inputs stream from the official S3 bucket (vc_render_tifxyz reads remote zarr chunks). Full volumes are never downloaded.
2. Work happens in a bounded local working folder. Outputs are compact (uint8 PNG, npz).
3. Outputs are offloaded in batches to the private GitHub repo with tools/offload/git_offload.py, on the dedicated branch claude/gifted-bell-gavnl5-data:
   - one commit per batch, whose tree holds only that batch plus BATCH.json, with batches chained by parent links;
   - the commit is built in a throwaway repo from a blob-free shallow fetch of the tip, so local git costs only the batch;
   - the remote tip is verified to equal the pushed commit before any local copy is removed;
   - every batch is recorded in logs/offload/manifest.jsonl (label, commit, file sha256, bytes);
   - refused: anything under /srv/scorer or /work/sealed_io, key files, symlinks, files > 95 MB, batches > 1.5 GB, and extensions outside the allowlist.
   GitHub's practical limits apply: a 100 MB hard limit per file, and about 5 GB of total repo size as guidance. Raw CT therefore never goes to git.
4. Because the data branch is not the designated work branch, pushes to it happen only when the owner's own message in the current conversation explicitly permits pushing to claude/gifted-bell-gavnl5-data. The first push is a synthetic round-trip self-test.
5. Status at declaration: a blob-free shallow fetch through the session's git proxy was verified (a 14 KiB pack). The first push attempt was blocked by the session's auto-mode safety check. It was not worked around.
6. Existing files are never deleted without the owner's approval.

## OWNER-CONFLICT-LABELS
- utc: 2026-09-25T18:25:52Z
- prev_sha256: 1d14958006b6472f908f565335c24d51bf45725159eaad8b7763fb61037283c4
- kind: conflict
Logged prompt conflict (owner direct message, 2026-09-25 ~18:26Z): "Anything trained on an eligible scroll's own labels or rescans may be used only if it's from team members and not another person who is competing for prize".
Resolution, stricter rule wins (prompt preamble; section 1 item 4: owner instructions do not amend section 2):
1. Kept and already in force: only our own work and official organizer products are ever used; competitors' models, labels and claims never are (I10).
2. Kept: cross-pair rescan use (section 6.0.4). Labels from the 1203 rescan may train a reader that never reads 1203, and vice versa with 0846A. Submission regions stay >= 128 vox from any window found with 2.4 um help.
3. Refused: manual character annotation of any eligible scroll, by anyone including team members. The prize rule FL-09 forbids it (including memorised annotation), so a submission built on it would be invalid.
4. Refused: a reader trained on a scroll's own rescan or on its own labels and then used to read that same scroll (I8, I11). FL-09 also requires that model output does not overlap training data.
No bar, seal or K6 budget changes.

## CORR-RETRACE-RULE
- utc: 2026-09-25T19:01:33Z
- prev_sha256: e605aa959c657e3bd3dd7135706da01fe539e5d89107e9e6d8f9a94c6709aa2f
- kind: correction
Correction to the same-papyrus (re-trace) rule of plan section 5.8, as used in DECL-D0 contamination items and any KD-tree exclusion, FL-09 certificate (SG 8) or bank clearance computed from now on.
Defect (measured by the tribunal sibling on synthetic worlds; branch claude/gifted-bell-gavnl5-sib-tribunal commit 5b6d067e3fb02e942eb039f119534fc554fde44b, logs/sib/tribunal/faultsuite.json sha256 71fd363217e00d204f466019146c53da0d1fe5b3b659d3ee1988b69ce26724e4): at the official 20-vox mesh grid step, 5 x 5 densification leaves a 4-vox vertex spacing. The literal nearest-densified-vertex form then puts true re-traces mostly in [1,3) vox. It caught 4 of 200 random re-traces (1/50 and 0/50 in stress runs). An exact re-trace offset by half a dense cell scores counts [0, 0, 20736] and is called NOT SAME.
Corrected rule (fail-closed, stricter): meshes are densified 5 x 5 as before. A training segment is SAME papyrus as a window if EITHER (a) the literal nearest-densified-vertex form OR (b) the same bins computed with point-to-triangulated-surface distance gives >= 1000 window points within 2 vox and count[0,1) >= 2 x count[2,3). Form (b) caught 300 of 300, with 0 false alarms on neighbouring sheets 3-20 vox away.
Distance clearances (>= 128 vox exclusions, the FL-09 halo) are computed as point-to-surface distance, or on meshes sampled at <= 1 vox spacing.
Consequence: every earlier exclusion or clearance computed with nearest-vertex distances on 20-vox meshes is re-checked (numbers only) before it is relied on again. Candidates: DECL-D3-FEAS / D3-FEAS-RESULT and DECL-D3-A2 (J exclusion; recorded minimum 128.0001 vox, method to be confirmed), the SEAL-J-D1 blank placement, RCBANK-1 (normal-distance variant), and any D1 blank or canary clearance. Results are recorded as corrections if anything changes.
No bar changes. No read has happened under the corrected rule yet.

## REG-0841-R1
- utc: 2026-09-25T19:14:11Z
- prev_sha256: 724a666c69f9966ec677e58b6b1f13a785989430d67656909e4ebe0e4196d353
- kind: result
Result of the PHerc0841 9.366 <-> 2.403 um registration (plan section 6.7 step 1 / C6 bars; CT only, no ink model, no J data within 144 vox). Run by the reg0841 sibling session: branch claude/gifted-bell-gavnl5-sib-reg0841 commit 487f9e483aa46b6cc695625633189769c2a80adc, logs/sib/reg0841/reg0841_summary.json sha256 0ca6cf19f2015bfb6125a2be8e7491169b51cc634b9357afc24f72f7cc4f5522. Held-out bars were pre-registered on that branch (prereg_heldout.md) before any held-out analysis.
- Orientation: identity (no flip or remount rotation); z band: rescan z 0 -> 9 um z 12790.6, rescan z 15120 -> 16669.3 (confirms the old CHECK estimate 12790-16670).
- Affine fitted on 24 patches (fit RMS 1.565 vox, leave-one-out 1.895). On 16 new held-out patches: median r 0.724 (min 0.504) against a bar of >= 0.85, FAIL; RMS 1.92 vox (max 3.38) against a bar of <= 1.5, FAIL. The half-pitch shifted control dropped NCC clearly (median drop 0.405, 16/16), PASS.
- Diagnosis: phase-correlation correspondences repeat to < 0.25 vox; with a per-patch local shift the held-out NCC median is 0.881. The inter-scan deformation is smooth but non-affine: the rescan sits 2-3.4 vox (9 um) lower in z near the scroll centre than at the periphery, with quadratic in-plane terms. The organizer's 2.4 um meshes are an affine image of the 9 um meshes (mesh-pair residual 0.43 rescan vox median), i.e. the organizer's own affine transform.
VERDICT: the single-affine registration FAILS its bars. Consequences: our 2.4 um chain on 0841 (CHAIN VALID, KTLB-4-0841) needs a non-affine mapping validated on fresh held-out patches before use. Earlier uses of the organizer's canvas mapping (J seal positions via c9 = (c2+10) N9/N2 - 10, D3 fold-A teacher labels from ref9) may carry a few-voxel local misalignment. Letter matching at 150/250 px is insensitive to this, but pixel labels may not be. The size of the offset at the fold-A pool tiles is to be measured (numbers only) and recorded.

## REG-0841-NA
- utc: 2026-09-25T19:31:53Z
- prev_sha256: a41dfa34f2194e3fdc0fa87fc65565440882e34ee134c4d61fe17cd99b549c29
- kind: result
Result, PHerc0841 9.366 <-> 2.403 um registration, second model (DECL-CHAINVALID registration bars), after REG-0841-R1 (single affine FAIL).
Deviation disclosed: DECL-CHAINVALID says "per C6", which is an affine. After the affine failed on its 16 new check patches, the model was changed to affine + a smooth quadratic field (21 parameters: affine plus x^2, xy, y^2 terms in all 3 components). It was selected by leave-one-out on the 40 earlier correspondences only, then frozen and pushed before any new-patch data was read. It was validated on 16 NEW check patches, pre-registered in prereg_na.md (sibling commit 30b4974) before analysis. No bar was changed.
Source: sibling branch claude/gifted-bell-gavnl5-sib-reg0841, commit 0fcf1e0c6211e8359af59f2e49e148a031fc3961; logs/sib/reg0841na/reg0841na_summary.json sha256 9d6779bf597a1af3b6115fdb2a33f93723c96707af8422b3966c3bbe1a3c833f. CT only; no ink model; J exclusion >= 144 vox point-to-surface.
- Held-out (16 new): median r 0.863 (min 0.563), bar >= 0.85, PASS. RMS 0.977 vox (max 1.47), bar <= 1.5, PASS. Half-pitch control median drop 0.695 (15/16 clear), PASS. Round trip 9 -> 2.4 -> 9 um max 1.1e-11 vox (numerical inverse only; not an accuracy measure).
- Leave-one-out RMS 1.044 vs 1.715 for the affine alone; field magnitude median 1.26, max 3.66 vox.
- Organizer-mapping offset on the exact 288 D3 fold-A pool tiles, 9 um vox: |D| median 1.20, p95 2.07, max 2.84; normal component median 0.22, max 1.50; in-surface median 1.14. This is about 1 canvas px in-surface: small against 128 px tiles and 30-50 px strokes, and negligible against the 150/250 px letter-matching tolerance used for the J seal.
VERDICT: 0841 registration PASSES with the non-affine map (map_version reg0841na field_final.json). CHAIN VALID's registration prerequisite is met. The chain check itself is still to run.

## DECL-AMX-1
- utc: 2026-09-25T19:35:06Z
- prev_sha256: a30b25cd4d4639fb16f34079f81b7cfe170004be6f5f62de110e52c990244833
- kind: declaration
DECL-AMX-1: bf16 (Intel AMX) TRAINING parity gate only. Declared before any bf16 training step on real data exists. Drafted by the amx sibling (branch claude/gifted-bell-gavnl5-sib-amx, commit d46a0fc121e229cb629d1eb8b26c1c69895ec64e, logs/sib/amx/proposals/decl_amx_1.txt section II); orchestrator decision below.
Scope decision:
- Only part II (AMX-TRAIN) is declared.
- Part I (AMX-INF, bf16 inference) is NOT declared: the sibling's synthetic forecast (98.2 % / 97.7 % of pixels within +-2 grey levels, against a 99.9 % bar) predicts FAIL.
- The fp32 cost is only about 3.2 min per 2 x 2 cm window, so every ink map stays fp32 (C2-NT unchanged).
Code (pinned):
- tools/sib/amx/d3_train_bf16.py sha256 4768879b7ff710cf3f22196ba3e3cc9f192e4262311b6dd5375630e56c5118ec. It runs tools/d3/d3_train.py (sha256 2943b1b6fb7492433fc1476bb57848d306c705f70ccef575bf701342acf6f52f, byte-identical to /work/d3/scripts/d3_train.py) UNCHANGED inside torch.autocast('cpu', bfloat16).
- The loss is computed on .float() logits; AdamW keeps fp32 master weights; no grad scaler.
Recipe: the D3 CTRL arm of DECL-D3-A1 item 1 and DECL-D3-A2 items 2-4, unchanged: 8 replay tiles per batch from the 2643-tile PHerc0139 base-training replay pool, seed 20260925, 2000 steps, AdamW lr 2e-5, wd 3e-5, batch 8, official loss and augmentations, identical tile/jitter/augmentation sequence, 3 threads. PHerc0139 is non-eligible; no 0841, J, seal or eligible data is touched.
Arms:
- P32 = the existing fp32 D3 CTRL run (logs/d1/d3_runs/CTRL_train_log.jsonl; model_final 6b690dda...97ed).
- P16 = the wrapper with --arm CTRL --out /work/amx/P16, run on this container (AMX present).
- P32' (calibration, reported only) = a second fp32 CTRL run at 4 threads, to measure the fp32 run-to-run drift floor.
Metric: L = the mean training loss over steps 1801-2000 (the mean of the last four 50-step loss_mean_window values).
PASS requires all of:
(a) |L(P16) - L(P32)| / L(P32) <= 0.02;
(b) all 2000 P16 losses are finite;
(c) P16 completes 2000 steps.
Reported without a bar: the per-window relative gap, grad-norm medians, the L2 distance between the P16 and P32 final weights relative to their distance from base, the P16 wall time per step, and P32' against P32.
Scope of a PASS: bf16 training is permitted for later CPU fine-tunes of this model family and recipe class (batch 8, lr 2e-5, 2000 steps). Any change of recipe re-runs this bar. Every map of a bf16-trained checkpoint is produced in fp32 (C2-NT). A FAIL keeps training fp32.
Default: FAIL (not run) at 24 h after this declaration.
Schedule: P16 runs on this container after the D3 arm inference ends, while the D3 reads (agents, no CPU) run. It never overlaps D3 CPU steps.

## PRIZE-CHECK-20260925
- utc: 2026-09-25T23:38:39Z
- prev_sha256: 64eee765dbb0d3e592c31888adc19075ed284e06c42ee4d13904fb397ea51c8c
- kind: decision
Prize page and eligibility re-check under the v6 section 7 pivot rule ("a rule change on the page -> amend the plan before anything else is read"). The sg sibling flagged it (branch claude/gifted-bell-gavnl5-sib-sg, commit defec94). The orchestrator re-fetched and diffed it independently at 2026-09-25T23:37:49Z.
Sources:
- https://scrollprize.org/prizes, raw sha256 998abc07a6239d74737e1ca576431a385c23082e44ee76b2829b62380a9f7209 (59596 bytes); saved as data/catalogue/prize/prizes_20260925.html with its 5 U+200B anchors made visible.
- villa main scrollprize.org/src/data/prizeEligibility.json, sha256 d549d8e8e0e20a6b4a7f7548287c6d0631d825c8a4063c78ac0bd86bdc9e30a7; saved as data/catalogue/prize/prizeEligibility_20260925.json.
- Compared with the day-0 copy data/catalogue/prize/prizes_20260924.html (raw sha256 7e6dd805...).
Changes (text diff of the rendered page; these 4 are the only differences):
1. First Letters eligible volumes 23 -> 22. PHerc1447 (20250521151220) is removed. The page now says the set "excludes those where letters have now been found". prizeEligibility.json first-letters-2027 lists 22 volumes without PHerc1447; grand-prize-2027 still lists 13, including PHerc1447.
2. Winners must open source "their code, data, model weights and results (after winning the prize)". It previously said "methods and results".
3. Progress prizes: early release "includes releasing model weights and training data where applicable".
4. Intro wording only ("For these prizes, your mission is to prove that ink detection works on scrolls where nothing has been read yet"). No change to the deadline, the amounts, the 4 cm^2 / 10-letter rule, the FL review text or the PHerc. Paris 4 Title Prize section.
Plan amendments:
a. PHerc1447 leaves the First Letters eligible set and every eligible-volume queue (census, Route Z, render cache ranking). No 1447 read or evidence exists: the HRV-1 RAW overviews went to the owner only, and HRV-1 is cancelled. Any later 1447 use is as non-eligible material only, under the unchanged contamination rules.
b. Package checklist (v6 section 9.2): after a win, code, data, model weights and results must be open-sourced under a permissive licence. The licence of every checkpoint in a candidate reader's lineage (base ink_9um: licence CHECK) and of every training dataset must permit release of the derived weights and data. This becomes a pre-submission package item, checked again on submission day. It is not an SG bar.
c. Nothing else changes. I1-I17, SG 0-14, every bar, seal and K6 budget stay as they are. D3 (PHerc0841, a non-eligible benchmark) is unaffected, and its reads may proceed.
Next weekly check: 2026-10-01.

## D3-RERUN-1
- utc: 2026-09-25T23:51:17Z
- prev_sha256: b7d4de75dedeabbbe404c3d421f420e457086bad69a147159b8a6cb4ddf5147c
- kind: decision
D3 reader harness event (no data affected), handled as in D1-RERUN-CHANCE.
At 2026-09-25T23:46:05Z an owner-side interrupt of the orchestrating conversation stopped 4 running D3 readers:
- REVA-A reader 1, job 0fd42ece
- REVA-B reader 1, job 74f8fa29
- CTRL-A reader 1, job a53f1148
- CTRL-B reader 1, job 12402ca1
Each transcript stops at the same second, after the agent had read its 15 listed images and issued its one sealed-write command. No sealed answer file exists for any of the 4 jobs (/work/sealed_io/<job>.age is absent), so no answer exists that anyone could have seen or selected on. The transcripts are retained, and the 4 rows are copied to /work/jobs/agent_map_dead.txt.
Status of the other readers at this time:
- The 12 readers with sealed answers audit VALID (logs/harness_jobs.tsv).
- The 8 reader-2 jobs have not been launched.
Decision: each of the 4 jobs is re-run once by a fresh fable agent, with the identical brief and output path. The dead agents' reads carry no information into the re-run, because agents share nothing. If a re-run dies again after reading images, that job is discarded and a new job is created for its slot, as in D1-RERUN-CHANCE.
Unchanged: scoring code, bars, item map, images and seal.

## DECL-P4-2
- utc: 2026-09-26T00:24:59Z
- prev_sha256: 6d7ec26d29af09d657e2b985ca0686fbedef19becb2408926599992783cd3822
- kind: declaration
DECL-P4-2: PHerc. Paris 4 title search P4-B (DECL-P4-1 item 3). Declared from the committed reconnaissance (logs/p4/recon.json, recon.md; commit 96f3489). It is declared before any Paris 4 tile, display, render or read exists in the project: no Paris 4 image or map pixel has been produced, opened or read.
Corrections to DECL-P4-1, from the reconnaissance:
- The ink_9um aligned Paris 4 set has 8 cases, not w00..w09 (there is no w04, and w08 is unused).
- ink_9um step-075000 (seed42) trained on all 8, so P4-A measures fit to training data only.
- P4-A is deferred. It is not needed for P4-B.
Honest odds: well under 3 %. The organizers state that the expected title region "has shown no detectable ink so far", possibly because the ink differs, and that its top rows are physically missing. No official page gives the title's winding, segment or coordinates.
1. Region and material, fixed now.
- Official statements say the known text is the end of the work, with ink shown on windings 28-37, and the title follows the end of the primary text: in a following column, or below a short last column. Derived: the title lies at or inward of the last known-text windings, toward the core.
- Material M1: the published 2D ink predictions of official model 20260417190342 (new_canon_autoresearch_recipe) on volume 20260411134726 (2.4 um per metadata.json) for two official segments, used exactly as published (sha256 recorded):
  - 20260701183124-w010-027 (641.42 cm^2);
  - 20260701183125-w028-037 (676.2 cm^2).
- No model is run by the project in P4-B.
- Training-overlap flag: each tile records its minimum 3-D distance (point-to-surface, CORR-RETRACE-RULE form) from its mesh points to the 8 labelled segments' meshes (20231016151002, 20230702185753, 20231031143852, 20231106155351, 20231012184424, 20231210121321, 20231007101619, 20230929220926). A tile with any point < 1.2 mm from them is labelled-adjacent. It is read in the census but never becomes a candidate.
2. Tiles. Each segment's prediction canvas is cut into non-overlapping 2 x 2 cm tiles from origin (0, 0).
- The tile side T = round(20 mm x px_per_mm), where px_per_mm is computed from the official mesh and the metadata voxel size (I9) and recorded.
- A tile is read if >= 50 % of its pixels are mesh-valid.
- Display (I2): the raw 0-255 prediction, 0 outside mesh-valid, downscaled only with cv2.INTER_AREA to 1068 x 1068 px (53.4 px/mm). No contrast change and no (p-0.25)/0.5 remap.
- Files are flat <uuid4>.png (IHDR/IDAT/IEND only). The key (uuid -> segment, tile row and column, rotation) is /srv/scorer/p4_key.json, mode 0400. The builders never open an image. The orchestrator never views any P4 tile; only blind readers do.
3. Phase 1 census.
- Each tile is read once, by a fresh fable reader (READCAL-FREEZE), under the frozen single-image task text configs/briefs/k_d2_task.txt (sha256 74a0cbe8...5f0) with the K_D2 key sheet, in sealed-output mode (DECL-HARNESS-A1).
- A session holds up to 8 census tiles plus 1 null tile (item 4), in random order.
- Scoring records numbers only: rows Y/N, letter count and firm count per tile.
4. Null N0: census tiles drawn by seed 20260926 and shown rotated 90 degrees clockwise. There is at least 1 per session and at least 40 in total. The N0 letter counts give the null distribution.
5. Candidates.
- A census tile is positive if rows = Y and its letter count is >= max(5, the 99th percentile of N0 letter counts).
- On each segment canvas, positive tiles form 4-connected clusters.
- Candidates are:
  - every positive tile on w010-027;
  - every positive tile on w028-037 in a cluster of <= 4 tiles that is separated from every larger cluster by at least one non-positive tile.
- Labelled-adjacent tiles are excluded.
- At most 20 candidates, ranked by letter count, ties broken by uuid.
6. Phase 2 confirmation.
- Each candidate is read by 3 new fresh fable readers.
- A session holds up to 4 candidates, 4 new N0 tiles and 1 positive control (a positive tile from the largest w028-037 cluster), in random order.
- A reader's session is void if the positive control is read rows = N.
- A P4 CANDIDATE needs all of:
  - >= 2 of 3 readers each name >= 5 letters on it;
  - the best pair of those readers agree on >= 5 same-identity letters within 150 px (one-to-one matching);
  - that agreed count exceeds the maximum agreed count over all phase-2 N0 tiles.
- Anything else is "no title found by reader X at 2 x 2 cm over N cm^2" (I14).
7. Package, only for a P4 CANDIDATE.
- The official tifxyz mesh is cropped to the candidate tile +- 1 cm by code and flattened with vc_flatten (FLAT-1). The quads within +-5 % are reported, with a bar of 93.1 %.
- Two images come from that crop:
  - the official prediction, raw;
  - a linear 1-99 % slab-mean CT render from 20260411134726.
- Disclosures: blind LLM readers with correlated errors; the maps are official model output, not ours; the reads were not sealed against a reference, because none exists.
- The project never names title words. The organizers' papyrologists read the image.
8. Resources and limits.
- Builder siblings fetch, tile and compute distances in their own containers. PNG tiles go to their branches and are copied to /work/p4/img here.
- This is not a sealed benchmark and spends no K6 decision.
- Default: if phase 1 is not complete by 2026-10-03, it is recorded as incomplete with the area read.

## METRIC-HASH-19
- utc: 2026-09-26T00:28:50Z
- prev_sha256: eb1ff1ceea8665510f7c8ec850e584f50aed52f3586e3bdd2c86f15520da1cea
- kind: metric-hash
P4-B read path (DECL-P4-2 items 2-5), hashed before any Paris 4 tile, display or read exists: tools/p4/p4_jobs.py (tile import with sha256 check, uuid key 0400, rotated N0 null by seed 20260926 + batch index, census sessions of 8 tiles + 1 N0 with the frozen single-image task and K_D2 key sheet), tools/p4/score_p4.py (census counts, N0 p99 by numpy.percentile linear, positive rule rows Y and letters >= max(5, p99), 4-connected clusters, candidate rule of item 5, labelled-adjacent exclusion, cap 20). Tests: tests/test_p4_score.py (5 passed) and a synthetic import/rotation smoke (rot90 equality verified, key mode 0400). Phase-2 scoring code is hashed separately before any phase-2 read.

```
882f34c2d89adc4c6bf9e96691c7de60b28ffe36d3b10ec7619422134c389e73  tools/p4/p4_jobs.py
520dababc60d91f9083e0f74fded1dd94d92d888311b066221fb2362dda00aab  tools/p4/score_p4.py
c8bb4941004a70c2ac26705f967842cd4547b473b1f68559673224a39b18d017  tests/test_p4_score.py
74a0cbe86223d68a09cd28d8cc5a012438e72d628d59e7114fa096ccf2ac45f0  configs/briefs/k_d2_task.txt
combined_sha256 40f69f7f9a80ba60eacac2b8ec26c7d8f29de2ae07fd23d9a2b0af2b130cfe6f
```

## DECL-DEVLOOP-A1
- utc: 2026-09-26T00:32:24Z
- prev_sha256: e7a2249df583a9fb50370e35ee75b74964793cfe79f42af4879cc457be60d438
- kind: declaration
DEV-LOOP amendment 1 (DECL-DEVLOOP), declared before any DEV model map exists. Drafted from the devloop sibling's branch (claude/gifted-bell-gavnl5-sib-devloop, commit 5e7fd18; logs/sib/devloop/proposals/first_recipes.md), integrity-reviewed, with the same-papyrus rule written out here.
1. Registry v3 (tools/sib/devloop/registry.py on that branch; sha256 recorded in a METRIC-HASH together with evaluate.py and the frozen v3 dev_registry.json).
- Same-papyrus is the fail-closed union of three forms: nearest-densified-vertex, point-to-surface (CORR-RETRACE-RULE) and normal-distance. In each form the test is >= 1000 points (or >= 1000 vox^2) within 2 vox, with count[0,1) >= 2 x count[2,3).
- Clearances are point-to-surface, or use <= 1 vox sampling.
- No two DEV windows are same-papyrus.
- Each DEV scroll has >= 4 blanks of 1 x 1 cm (coverage >= 0.90, reference ink fraction < 0.01, no forbidden sample). The non-text-order blob-f180 <= 0.0272 constraint applies to each blank separately (max, not mean). A DEV scroll without 4 blanks does not count toward FINALIST.
2. Recipes, in order: LC384-FROZEN, LC384-SOFT, DIST-FT, and DIST-FT-384 only if recipe 1 or 3 moves pooled sigma_eq by >= 0.05 mm.
- Each starts from base seed42 step-075000 under the common protocol of first_recipes.md.
- Each recipe has three controls:
  - NULL: one fixed derangement of targets, seed 20260925;
  - REV: depth-reversed inputs;
  - CHANCE: the base map of window i scored against the reference of window j.
3. ALARM shelves the recipe if any of these holds:
- NULL or REV reaches the FINALIST bar on any DEV scroll;
- NULL's pooled r_best is >= half the recipe's;
- non-text-order blob-f180 > 0.0272 on any DEV blank.
4. Seeds: 1 per recipe. Any recipe within 0.025 mm of the best gets 2 more seeds before any finalist call, and the spread is reported.
5. Reported only, with no bar: the per-window minimum distance to base-training traces, and a secondary sigma_eq on the area >= 30 vox from every base-training trace.
6. Hold-outs: the DEV segments, and every segment same-papyrus with them (+16 vox), are excluded from every D2 and DEV training set. The list is frozen and hashed before the first training step.
7. FINALIST still needs >= 3 DEV scrolls. 0009B DEV windows (outside every KTLB-M candidate window + 144 vox, never trained on) are added by a registry extension declared before any map on them.
Default: no finalist. DEV ranks only; letters are claimed only from sealed blind reads (DECL-DEVLOOP unchanged otherwise).

## DECL-DEVLOOP-SCREEN
- utc: 2026-09-26T00:32:24Z
- prev_sha256: 3b440d1e957e1e0cec5c6e55eca7fe7c2bd8d34ab0aad8f970c1db549e138657
- kind: declaration
DEV-LOOP official-checkpoint screen (DECL-DEVLOOP; v6 sections 6.5 and 11.3 watch rule "new official checkpoint -> new decision within 48 h"). Declared before any screen map exists. Purpose: find any official organizer checkpoint whose 9 um maps of unseen known text reach reader-level sharpness.
1. Checkpoints. Every official scrollprize ink-capable checkpoint in data/catalogue/checkpoints.json, plus any released later, is screened. Each checkpoint's input specification (voxel size, slices, normalisation, orientation) is taken from its own card or code. Weights are sha256-verified. Starting list:
- ink_9um seed43 step-075000;
- hecate_9.6um;
- ink_3d_dino_guided, if its card documents a 9-10 um input;
- PHerc.1667-iteration-0..5;
- timesformer_scroll5_july_retreat;
- timesformer_GP_scroll1;
- timesformer_large_scroll1_01122024;
- resnet50_7.9um_scroll1_frags;
- fiber_ink_4class_selfdistill, if it outputs ink.
2. Metric: the frozen DEV-LOOP evaluator (sigma_eq of the text-order map against the 2.4 um reference on the frozen DEV registry, with blank blob-f180 per DECL-DEVLOOP-A1), after its METRIC-HASH. Both depth orders are mapped and reported. The text order for a checkpoint is the one its card or code documents; if none is documented, both orders are reported and the order is not chosen from the DEV result.
3. In-sample guard: a checkpoint whose documented training data includes a DEV window, or a same-papyrus segment of one, is reported as IN-SAMPLE for that window and never counts toward FINALIST. Undocumented training data counts as UNKNOWN and never counts toward FINALIST either, unless the window's scroll is absent from every training list the card or code names.
4. Output: a ranked table, numbers only. The screen ranks and decides nothing. A checkpoint that meets the FINALIST bar under item 3 becomes a candidate arm for a new sealed decision, declared separately before any sealed read (K6).
5. No screen map of any sealed window, fold, shell, eligible volume, PHerc0841 or Paris 4 is produced.

## DECL-P4-2-A1
- utc: 2026-09-26T00:40:07Z
- prev_sha256: 8672316339323661ec8c938e26c3fde5704b264c2cc175d099b265de7bf753b0
- kind: decision
Owner direct instruction (2026-09-26 ~00:43Z, recorded per the base prompt, section 1 item 4): "no fable, opus 5.5 only". It applies to every reader launched from now on.
Amendment 1 to DECL-P4-2, declared before any P4-B read exists:
- The 22 phase-1 census jobs of batch census_b1 were built at about 00:41Z (w028-037, 171 tiles, 22 N0 tiles).
- Two reader launches were refused before starting, and no sealed answer exists for any P4 job.
- Changes:
  1. Every P4-B reader, in phase 1 and phase 2, is a fresh subagent with the Agent tool's 'opus' model setting (the owner-designated model), replacing the fable reader of READCAL-FREEZE. Harness, briefs, key sheet, frozen single-image task text, display, sessions, N0 null, bars and candidate rule are unchanged.
  2. This reader is not the READCAL-FREEZE-calibrated reader, and its legibility on this display is unmeasured. Attention checks:
     - phase 1: the known-text strip w028-037 (text "clearly legible at 2.4 um" per the organizers) is read in the same census. Rows = Y on no w028-037 tile is recorded as reader failure, not as absence of text.
     - phase 2: the positive control in every session.
     Any package discloses the change.
  3. Sealed decisions (D2, DEV finalists, KTLB decisions) still use the READCAL-FREEZE reader until a new READ-CAL calibration of this model is declared and run. This instruction does not change a recorded result or any bar.
- The jobs file /work/p4/jobs_census_b1.json has its 'model' field updated to 'opus'; the change is logged.

## DECL-P4-2-A2
- utc: 2026-09-26T00:47:47Z
- prev_sha256: c8e7123dc8c91bb645a509f34decd9bec8dc3e07fbd86a651f263ec38cf00293
- kind: declaration
Amendment 2 to DECL-P4-2 (owner question 2026-09-26 ~00:46Z: "why not look for both lunate and normal sigma"). Declared before any read that uses it.
Reason: the frozen key sheet (METRIC-HASH-12) and task text show only the lunate sigma, having been calibrated on PHerc0139 material. The sigma form used by the Paris 4 scribe is not assumed. Scoring already treats every sigma form as one letter kind (hercules.scorer.letters normalises all sigmas to lunate), so only the readers' prompt and key sheet change.
1. Key sheet v2: configs/briefs/keysheet_sigma2.png (sha256 164262e6...db438), rendered by tools/p4/keysheet_sigma2.py.
   - It keeps the same spec: 1068 x 1068, DejaVu Serif Bold glyphs, Latin names in DejaVu Sans.
   - It holds 25 glyphs: the 24 capitals plus the four-bar sigma, next to the lunate sigma.
   - Rendering is deterministic: two renders are byte-identical.
   - The orchestrator viewed it once to confirm the glyphs render (logged in logs/views.tsv). It is a synthetic font chart, not scroll data.
2. Task text v2: configs/briefs/k_d2_task_sigma2.txt (sha256 71b133f4...9f7bb). It is k_d2_task.txt with two phrases changed:
   - the key-sheet sentence now reads "sigma is shown in both forms, lunate Ϲ and four-bar Σ";
   - the letter sentence now reads "sigma may be written lunate Ϲ or four-bar Σ".
   Nothing else changes.
3. Use:
   - variant sigma2 applies to every P4-B read not yet launched: the w010-027 census and all of phase 2.
   - The w028-037 census batch census_b1 was launched under v1 before this amendment. It stays v1 and is never re-read.
   - The census positive rule (DECL-P4-2 item 5) uses the p99 of the N0 tiles read under the same variant as the census tile. Its N0 tiles are drawn per batch and read in the same sessions.
   - Phase 2 is entirely sigma2, including its N0 tiles and positive controls.
4. Readers: unchanged from DECL-P4-2-A1 (the owner-designated model). No bar, null, sessions or candidate rule changes.

## METRIC-HASH-20
- utc: 2026-09-26T00:47:47Z
- prev_sha256: 52367f6de5d73740170eff3caa1f285f30d58b1eeaca78ce96420e1656334d8f
- kind: metric-hash
P4-B read path after DECL-P4-2-A2, hashed before any sigma2 read: tools/p4/p4_jobs.py now takes a variant (v1 | sigma2); the v1 path is byte-for-byte the METRIC-HASH-19 behaviour (key sheet and task hashes asserted as before). The sigma2 path asserts the key sheet v2 and task v2 hashes. The key-sheet generator is deterministic. score_p4.py is unchanged since METRIC-HASH-19; per-variant p99 comes from scoring each variant's jobs files separately.

```
852b092721c42ad612334dc0dd0c8a0000601a95ce2a3132cc5c7141ab272db6  tools/p4/p4_jobs.py
d48b786b2b99a76d198c9e786124d34041a2a951b9590fe0e56e88366e2e170e  tools/p4/keysheet_sigma2.py
164262e67dfd7589bdd03dddb1b8470267bd7d46d5c40b0af63fc1eb980db438  configs/briefs/keysheet_sigma2.png
71b133f4cdcd4ff588b9c3ebc077a6e22aef62a0f6c8cd13530e083764e9f7bb  configs/briefs/k_d2_task_sigma2.txt
520dababc60d91f9083e0f74fded1dd94d92d888311b066221fb2362dda00aab  tools/p4/score_p4.py
combined_sha256 2842869e97888e089c63137ab3f629e46c0a7122f1f0a3b6431a8a4e841ebb09
```

## METRIC-HASH-21
- utc: 2026-09-26T00:52:41Z
- prev_sha256: bc4739ff3ac942a5819a38784aeae142bce27a7a4a4e42a605442cc6d3dadf7c
- kind: metric-hash
P4-B read path correction, hashed before any sigma2 read. No P4 sigma2 read has been launched and no sealed answer exists for any job named here.
- Defect: tools/p4/p4_jobs.py (METRIC-HASH-20) put the sigma2 key sheet in the brief as the relative path configs/briefs/keysheet_sigma2.png. The Read tool accepts only absolute paths, so a reader could not have opened it as briefed, and the transcript audit would have voided the job.
- Fix: KS2 is now the absolute path /home/user/dominion/configs/briefs/keysheet_sigma2.png (the same file, sha256 asserted as before). The jobs file now records model 'opus' (DECL-P4-2-A1) instead of the stale 'fable' label. Nothing else changes: the v1 path, the sigma2 task text, sessions, N0, bars and candidate rule are as in METRIC-HASH-20.
- Superseded and never launched: batch census_a1 (/work/p4/jobs_census_a1.json; jobs 6be0db75-3fba-47d1-a839-e16a6f7fcc3c f2c9541e-dafc-4469-b229-85a4ef8320f9 848a8a2c-0615-47e3-b814-46d89207e775 e29eeae5-cf22-4be0-9ce1-baa3bb07ad46 be60a31e-afa5-4c5c-accd-a5b497a61f22). It is rebuilt as census_a1b from the same census batch a1 (40 w010-027 tiles) and the same unread null batch na1 (5 N0 tiles).

```
8c293f912c0e424885f550511196ac530a4d48979e5c60aecfcc22bf799a067c  tools/p4/p4_jobs.py
d48b786b2b99a76d198c9e786124d34041a2a951b9590fe0e56e88366e2e170e  tools/p4/keysheet_sigma2.py
164262e67dfd7589bdd03dddb1b8470267bd7d46d5c40b0af63fc1eb980db438  configs/briefs/keysheet_sigma2.png
71b133f4cdcd4ff588b9c3ebc077a6e22aef62a0f6c8cd13530e083764e9f7bb  configs/briefs/k_d2_task_sigma2.txt
520dababc60d91f9083e0f74fded1dd94d92d888311b066221fb2362dda00aab  tools/p4/score_p4.py
combined_sha256 8ff657cb2f88e1a3c6d103012adbd0827cc61b99932a9d139764e60ef6fe1de4
```

## DECL-P4-2-A3
- utc: 2026-09-26T05:28:41Z
- prev_sha256: 78404ed55333bc417bc6d35609434149403a4ad223cad1e8a0f7478a4af8a9f9
- kind: declaration
Amendment 3 to DECL-P4-2: the phase-2 operating details that item 6 leaves open. Declared before any phase-2 tile, job or read exists.
State at declaration:
- Phase-1 census complete: w028-037 (census_b1, v1, 171 tiles, 22 N0) and w010-027 (census_a1b + census_a2, sigma2, 160 tiles, 20 N0). All 42 reads passed the transcript audit.
- The summaries are counts only: logs/p4/census_b1_summary.json and logs/p4/census_a_summary.json.
- Labelled-adjacency (item 1): the p4-excl sibling's excl_b (commit d3c1839, sampled points) flags all 8 provisional w028-037 candidates (min distance 0 to 1.08 mm < 1.2 mm), so none of them can become a candidate. excl_a for w010-027 is being computed.
1. Candidate set.
- Each variant's census is re-scored by score_p4.py (unchanged, METRIC-HASH-19) with its own N0 p99 and with the labelled-adjacency file of its strip:
  - excl_a for w010-027;
  - excl_b for w028-037, using the all-vertex version if it is pushed before the build, otherwise d3c1839.
- The excl files are used as the sibling pushed them, with only a top-level "strip" key added when missing.
- The candidates of both re-scored summaries are pooled, ranked by census letter count (descending), ties broken by uuid, and capped at 20 in total (item 5). The ranking mixes the two variants' counts; this is disclosed.
- The phase-2 build waits for excl_a. No w010-027 tile becomes a phase-2 candidate without its flag.
2. Positive-control pool: the positive tiles of the largest 4-connected positive cluster on w028-037 in census_b1 (15 tiles). Each session gets one control:
- drawn from the pool without replacement while the pool lasts;
- shown as a new file, unchanged.
3. Phase-2 N0.
- Count: as many tiles as candidates.
- Pool: all phase-1 census tiles (rot 0, both strips) that are neither a candidate nor in the control pool.
- Draw: without replacement, by random.Random(20260926 + batch index).
- Display: rotated 90 degrees clockwise, the phase-1 N0 procedure.
- Reads: each N0 tile is read by 3 readers, exactly like a candidate.
4. Sessions.
- 3 replicates. In each, candidates and N0 tiles are shuffled (secrets.SystemRandom) into groups of 4.
- A session is one candidate group, one N0 group and 1 control, in random order.
- Each session shows key sheet v2 first and uses frozen task text v2 (DECL-P4-2-A2). Reads are sealed-output.
- Each session is read by one fresh reader with the Agent tool's 'opus' setting (DECL-P4-2-A1).
- Each candidate is therefore read by 3 different readers in 3 different sessions (item 6).
5. Scoring (tools/p4/p4_phase2.py score; hashed in METRIC-HASH-22 before any phase-2 read).
- Letters are known-kind namings, normalised by hercules.scorer.letters; all sigma forms count as one kind.
- The agreement of two readers on one tile is the maximum one-to-one matching of same-kind namings whose centres lie within 150 px (hercules.scorer.matching.max_matching_size).
- The candidate test is item 6 exactly.
- The N0 maximum is taken over the best-pair agreement of every phase-2 N0 tile across all its reader pairs, with no 5-letter filter. This is the stricter reading.
- Only counts leave the scorer.
6. Void and invalid sessions.
- A session is void if its control is read rows = N or is missing.
- A void, audit-invalid or undecryptable session is re-run once, with a fresh reader on the identical image list. The re-run replaces it whatever its outcome.
- A second failure leaves that session out, and its candidates keep fewer reads.
- Void counts are reported.
7. Outcome wording.
- A P4 CANDIDATE goes to the item 7 package.
- Anything else is recorded as "no title found by the blind readers at 2 x 2 cm over the N cm^2 read" (I14).
- No title word is ever proposed by the project.

## METRIC-HASH-22
- utc: 2026-09-26T05:28:41Z
- prev_sha256: dc732e29ad90421f849e64e3df12135834652e516cdf3cd2c5e250977a1b10c4
- kind: metric-hash
P4-B phase-2 code (DECL-P4-2 item 6, DECL-P4-2-A3), hashed before any phase-2 tile, job or read exists.
- tools/p4/p4_phase2.py: select, build, rerun and score. It reuses p4_jobs.py (METRIC-HASH-21) for the sigma2 key sheet, the task text and the census key loader; score_p4.clusters for the control pool; and hercules.scorer.matching and letters for agreement.
- tests/test_p4_phase2.py: 5 tests passed, together with the 5 tests of test_p4_score.py (10 passed). They cover one-to-one same-kind matching within 150 px, one kind for both sigma forms, unknown kinds not counted, the three candidate criteria, and the unfiltered N0 best pair.
- Synthetic smoke (temp dirs, fake briefs): 16 candidates and 16 N0 gave 12 sessions of 4 + 4 + 1. Every candidate and every N0 tile was read exactly 3 times; N0 sources were disjoint from candidates and controls; N0 rot 90.

```
885f9c22558a0205d3ebc9cd48b3323c643dc607ae7d695dcbe284a7707a5bbc  tools/p4/p4_phase2.py
a41da9d1eac99471e7d02f134f0d3471326f657dc73f4237edcd39aa7e18d2fe  tests/test_p4_phase2.py
8c293f912c0e424885f550511196ac530a4d48979e5c60aecfcc22bf799a067c  tools/p4/p4_jobs.py
520dababc60d91f9083e0f74fded1dd94d92d888311b066221fb2362dda00aab  tools/p4/score_p4.py
164262e67dfd7589bdd03dddb1b8470267bd7d46d5c40b0af63fc1eb980db438  configs/briefs/keysheet_sigma2.png
71b133f4cdcd4ff588b9c3ebc077a6e22aef62a0f6c8cd13530e083764e9f7bb  configs/briefs/k_d2_task_sigma2.txt
combined_sha256 0a3ddf94800636709065055057dc77fa6b43bc9959843da6127d9b18c4b6a4ae
```

## DECL-P4-2-A4
- utc: 2026-09-26T05:30:39Z
- prev_sha256: 6a79c8e2134e6dd48012ce87d5d842b96f00de4f1ecfff6f7d2b294ccd14bc4e
- kind: declaration
Amendment 4 to DECL-P4-2, declared before any phase-2 tile, job or read exists.
1. Correction to A3 item 3: the phase-2 N0 tile count is 4 x ceil(number of candidates / 4), so that every session holds 4 new N0 tiles as item 6 requires.
- A3's "as many N0 tiles as candidates" would give fewer than 4 N0 tiles per session whenever the candidate count is not a multiple of 4. With 1 candidate that is 1 per session, which weakens the null. A3 is corrected in the stricter direction.
- Every N0 tile is still read by 3 readers.
2. Labelled-adjacency files used under A3 item 1 (sibling p4-excl, commit a82ed00):
- excl_a (w010-027): npz points, 120 of 160 flagged. The all-vertex run is still going. It can only add flags, and it is applied again before any P4 CANDIDATE claim.
- excl_b (w028-037): labelled_adjacent := npz flag OR all-vertex flag, as the sibling recommends. That gives 139 of 171.
- Local copies with sha256: /work/p4/excl/excl_a_7fb5cbf_a82ed00.json 563da0de...; /work/p4/excl/excl_b_a82ed00.json d7ee0884... (union applied in a normalised copy).
3. Facts at declaration (geometry flags and phase-1 counts only):
[line withheld: prize-candidate detail under review]
- All 8 provisional w028-037 candidates are labelled-adjacent.
- Phase 2 therefore has 1 candidate: 3 sessions, each of 1 candidate + 4 N0 tiles + 1 positive control, read by 3 fresh readers.
4. Disclosed observation, not a conclusion: census positives on the official predictions concentrate next to the labelled (training) segments. The one candidate outside them sits at the census threshold.

## METRIC-HASH-23
- utc: 2026-09-26T05:30:40Z
- prev_sha256: 3d33ea135153e28765c21de1ad21eecef3c9d9486542ddfbdeef9bad76cf94ba
- kind: metric-hash
P4-B phase-2 code after DECL-P4-2-A4. The only change since METRIC-HASH-22 is the N0 draw count in cmd_build: 4 x ceil(candidates / 4). Hashed before any phase-2 tile, job or read.
- New test test_n0_count_rule; 11 tests passed.
- Synthetic smoke with 1 candidate: 3 sessions of 1 + 4 + 1; the candidate and each of the 4 N0 tiles are read exactly 3 times; N0 sources are disjoint from the candidate and the control pool; rot 90.

```
b99335e8dc57d8d38225bf35cde82cfb70ffd3a4e5621710b1da021719bfaba8  tools/p4/p4_phase2.py
9a46a245433a9b0442caa1ba24fd9dd731b093a2af6777aed3ff0edae2d5c46b  tests/test_p4_phase2.py
8c293f912c0e424885f550511196ac530a4d48979e5c60aecfcc22bf799a067c  tools/p4/p4_jobs.py
520dababc60d91f9083e0f74fded1dd94d92d888311b066221fb2362dda00aab  tools/p4/score_p4.py
combined_sha256 6eadca35c239654416daa8258a7df11b2b2f8f8d5b8316aa66238dd7bddd0d03
```

## DECL-P4-3
- utc: 2026-09-26T05:37:52Z
- prev_sha256: e5fe1a072c66481765222277131c76c1845d7a93c6df36dfb13fb1343a4fc4cc
- kind: declaration
DECL-P4-3: P4-C extended confirmation of the phase-2 lead. Declared before any P4-C tile, job or read exists, and before the phase-2 audit returns.
[line withheld: prize-candidate detail under review]
- 3 of 3 readers named 5 letters each;
- the best pair agreed on 5;
- the N0 maximum over 4 tiles was 4.
The margin is 1. The null has 4 tiles, and all readers are one model. By the SG 1c spirit (>= 40 null tiles, agreed > max null, agreed - P99 >= 10), this is not strong evidence.
P4-C is a stricter test. It never replaces or lowers the recorded item 6 outcome. Both are reported whatever P4-C shows, and any owner-facing package carries the P4-C result.
1. Material.
- U: the phase-2 candidate file, unchanged.
- R, the self-null: U rotated 90 degrees clockwise.
- N0: 48 new tiles, drawn without replacement by random.Random(20260927 + batch index) from all phase-1 census tiles (rot 0). The candidate's source, the positive-control pool and the phase-2 N0 sources are excluded. Each is shown rotated 90 degrees clockwise.
- Positive controls: from the phase-2 pool, a new file per session.
2. Sessions: 18, each read by a fresh reader with the Agent tool's 'opus' setting. Each session:
- shows key sheet v2 first, uses task text v2, and is sealed-output;
- holds either U or R, never both (9 sessions each, assigned by secrets.SystemRandom);
- holds 8 N0 tiles; each N0 tile is read in exactly 3 sessions, never twice in one;
- holds 1 positive control;
- shows its items in random order.
3. Scoring (tools/p4/p4_ext.py score; METRIC-HASH-24).
- Sessions are used as in DECL-P4-2-A3 item 6: void if the control reads rows N or is missing; one re-run of a void or invalid session.
- Letters are known-kind namings.
- Pair agreement is one-to-one same-kind matching within 150 px.
- Triple score is the best-pair agreement among 3 reads. The U reads and the R reads each form 3 triples, in session-index order. Each N0 tile's 3 reads form its triple.
- EXT-CONFIRMED needs all of:
  (i) median U triple score > max N0 triple score, over the 48 tiles;
  (ii) every U triple >= 5;
  (iii) mean pairwise agreement over all U read pairs exceeds that over all R read pairs, with a one-sided label-permutation p < 0.01 (20000 permutations, seed 20260927).
- Also reported: N0 P99 (higher), max U triple - P99 (SG 1c spirit, bar 10), and letters per read.
4. Outcomes.
- EXT-CONFIRMED: the package goes to the owner as "a blind-reader lead that passed a pre-declared extended test". Readers are one model family and no title word is named.
- Otherwise: "phase-2 lead not confirmed by the extended test". It is not proposed for submission.
- An audit precedes recording either way.
5. Nothing is changed in any earlier bar, null or rule. Readers never see a role, strip, position or rotation.

## METRIC-HASH-24
- utc: 2026-09-26T05:37:53Z
- prev_sha256: ded7cf3b47aad96734e060295aac29d47fe706630cdd63688dd47c3aca49e91a
- kind: metric-hash
P4-C code (DECL-P4-3), hashed before any P4-C tile, job or read.
- tools/p4/p4_ext.py: build and score.
- tests/test_p4_ext.py: 4 tests. They cover simulated text confirming while noise does not; identical texture upright and rotated failing criterion (iii); a null maximum blocking; and the N0 assignment of 3 reads each with no duplicates.
- All P4 tests: 15 passed.
- Synthetic smoke in temp dirs: 18 sessions (9 U, 9 R, never both); 8 N0 + 1 control per session; every N0 read 3 times; N0 sources exclude the candidate, the control pool and the phase-2 N0; R == rot90(U, k=-1) exactly.

```
cd2401084a5aa9c52689f66765bd2bc0bafd0f518cc4213d0f02838e1282ef13  tools/p4/p4_ext.py
618364db8c2a8bdc3a09f74f86e100c64be15acfb7093ae73dd446fd9366e993  tests/test_p4_ext.py
b99335e8dc57d8d38225bf35cde82cfb70ffd3a4e5621710b1da021719bfaba8  tools/p4/p4_phase2.py
8c293f912c0e424885f550511196ac530a4d48979e5c60aecfcc22bf799a067c  tools/p4/p4_jobs.py
combined_sha256 a6fc9361e455b17c91551282c1509aa35fb45bca84af0801eca99ff4de1eeb65
```

## HANDBACK-EVENT-P4P2-S0
- utc: 2026-09-26T05:50:47Z
- prev_sha256: 55977492d46d0bcf2ef3a9cb5d49d50bd4ad2960e49ce833c1b367a1ece0ff55
- kind: correction
Integrity event under DECL-HARNESS-A1: a reader's hand-back contained text other than DONE.
- Reader of job 3582a5da (P4 phase 2, session 0).
- After its single sealed Bash call, it handed back 371 characters instead of DONE. The text said that one item id in its sealed answer was mistyped and gave that id's correct value.
- It contained no letter identity, position or other answer content; the auditor counted 0 Greek characters.
- No seal exists for P4 material, so nothing is voided. The transcript audit is VALID: the tool calls follow the protocol, and the hand-back text is not an answer.
- The sealed answer was not corrected. The mistyped item was an N0 tile. The scorer dropped that read as its hashed code specifies, and the auditor found that recovering it (0 letters) would not change any number.
- The orchestrator saw only the item-id statement.
- Recorded late: first flagged by the phase-2 auditor (logs/p4/audit_p2_1.json).

## P4-B-PHASE2-RESULT
- utc: 2026-09-26T05:50:47Z
- prev_sha256: a6d69b64f1df32c5da84e08b4226aaec0484beac1875ec8c1ac99b2efad45920
- kind: result
P4-B phase-2 result (DECL-P4-2 item 6; A1-A4). Audited VALID (logs/p4/audit_p2_1.json sha256 4008b066...; independent re-derivation, timeline, key and material, harness). Counts only.
[line withheld: prize-candidate detail under review]
- 3 sessions, 3 used, 0 void; 1 N0 read dropped by a mistyped item id (HANDBACK-EVENT-P4P2-S0).
- Readers on the candidate: 5, 5 and 5 known-kind letters (1 firm each). Pair agreements 5, 3 and 3; best pair 5.
- N0 best-pair agreements [0, 1, 2, 4] (readers per tile 2, 3, 3, 3); N0 max 4.
- Outcome: P4 CANDIDATE by item 6 (a, b, c all true), at the minimum margin.
- Auditor's strength judgement: WEAK. There are 4 null tiles against the 40 of the SG 1c spirit; agreed - P99 = 1.06 against a bar of 10; only 1 of 3 pairs reaches 5; the firm-only agreement is 1.
- Geometry of the best-pair matched namings: one row (centre y std 0.14 mm) along the brightest band of the tile; box heights median 3.46 mm. A fibre band or fold is not excluded.
- The candidate's 7 neighbours in its positive cluster are all labelled-adjacent, and the tile above has 10 census letters. If it is ink, the edge of the known text is more likely than an isolated title.
- Consequence: the extended test P4-C (DECL-P4-3, declared 05:37Z before this audit) decides whether any package is offered. No claim is made from phase 2 alone. No title word is ever named by the project.

## DECL-P4-4
- utc: 2026-09-26T05:53:39Z
- prev_sha256: e5ce6e85a657200e566b41d4723bd192bbe3234193e9d9e7456fbc5bb1d88ba2
- kind: declaration
DECL-P4-4: P4-D, the Paris 4 title search on the official higher-resolution predictions. Declared before any P4-D tile, display or read exists. No P4-D image or map pixel has been produced, opened or read. Only bucket listings and sizes have been seen.
Why: the organizers say that finding the title "may take better methods, higher resolution, or looking somewhere new". P4-B read only the 2.4 um canonical predictions, and its one lead did not pass the extended test (P4-C; recorded after its audit). The bucket holds official predictions of a second model:
- model: 20260709123958-mrg20736-1um-s1z2 (ResNet3D-152, 1-1.5 um);
- volume: the 1.129 um scan 20260608103018, rendered at level 1. It covers the central and inner region of the scroll, including the umbilicus.
1. Material M2, used exactly as published (sha256 recorded on import; no model is run by the project):
- M2a: PHercParis4/segments/20260623141924-w010-027/ink-detection/PHercParis4-20260623141924-1.129um-0.23m-78keV-volume-20260608103018-L1-20260709123958-mrg20736-1um-s1z2-tile256-stride128.tif (1,177,580,667 B). This is the innermost strip of the 20260623 spiral family: the title search.
- M2b: the same product for 20260623142658-w028-037 (1,175,621,659 B). This is the known-text strip: the reader check and the positive-control source.
- Disclosed: this model has no public card, and its training data are unknown. The prize says ink-model outputs of the title region should not overlap training data. Any candidate states that this could not be verified.
2. Tiles, display and exclusion: as DECL-P4-2 items 1-2.
- 2 x 2 cm tiles from canvas origin (0,0). T = round(20 mm x px_per_mm), where px_per_mm comes from the segment's own mesh for the rendered frame and the volume metadata, and is recorded.
- A tile is read only if >= 50 % of it is mesh-valid.
- The raw 0-255 prediction is shown, 0 outside valid, downscaled by cv2.INTER_AREA to 1068 px (53.4 px/mm). Output is flat uuid PNGs.
- Labelled-adjacency: min point-to-surface distance < 1.2 mm to the 8 labelled segments. It is computed in the 20260411134726 frame from each tile's mesh points, through that segment's 20260411134726 mesh at the same UV where the grids correspond, otherwise through the published affine. It uses npz points OR all vertices.
3. Census (phase 1), as DECL-P4-2 item 3 with A1 and A2:
- one fresh Opus reader per session of up to 8 tiles + 1 N0;
- key sheet v2 and task text v2 (sigma2); sealed-output.
- N0 for P4-D is drawn only from P4-D census tiles: tools/p4/p4_jobs.py null with pool batches, seed 20260926 + batch index, rot 90.
- p99 is taken over the P4-D N0 reads. M2a and M2b are scored together, like census_b1 and census_a.
4. Candidates, phase 2 and extended test: unchanged rules.
- DECL-P4-2 item 5 on M2a/M2b: every M2a positive; M2b small isolated clusters; labelled-adjacent excluded; cap 20.
- Phase 2 exactly as DECL-P4-2 item 6 with A3 and A4 (tools/p4/p4_phase2.py). The positive-control pool is the largest positive M2b cluster.
- Any phase-2 P4 CANDIDATE then goes through the extended test exactly as DECL-P4-3 (tools/p4/p4_ext.py). Its N0 pool is all census tiles, as coded.
- Only EXT-CONFIRMED leads to a package (DECL-P4-2 item 7) and an owner-facing report.
5. Honest odds: well under 3 %. P4-D spends no K6 decision. Title words come only from the organizers' papyrologists, never from the project.
6. Builders: siblings p4-tiles-a (M2a) and p4-tiles-b (M2b) cut the tiles; p4-excl computes the flags. The orchestrator imports the tiles with sha256 checks and never views a tile.

## METRIC-HASH-25
- utc: 2026-09-26T05:53:39Z
- prev_sha256: 27a661b4149fd669bd6ecb3203344aae00fe8bcdcd8828dd7575269b0b558006
- kind: metric-hash
P4 read path after DECL-P4-4. The only change is to tools/p4/p4_jobs.py: 'null' takes optional pool batches, so the P4-D N0 is drawn from the P4-D census tiles only. Without them its behaviour is unchanged, and the draw, seed and rotation are unchanged. Hashed before any P4-D tile exists.
- Synthetic smoke: with a pool, all nulls come from the named batch; without one, the default is unchanged.
- P4 tests: 15 passed.

```
1ebc3e7417206153d9afaadb3806e23f9784f11eeeeaf01c120d18299fd2ddfa  tools/p4/p4_jobs.py
520dababc60d91f9083e0f74fded1dd94d92d888311b066221fb2362dda00aab  tools/p4/score_p4.py
b99335e8dc57d8d38225bf35cde82cfb70ffd3a4e5621710b1da021719bfaba8  tools/p4/p4_phase2.py
cd2401084a5aa9c52689f66765bd2bc0bafd0f518cc4213d0f02838e1282ef13  tools/p4/p4_ext.py
164262e67dfd7589bdd03dddb1b8470267bd7d46d5c40b0af63fc1eb980db438  configs/briefs/keysheet_sigma2.png
71b133f4cdcd4ff588b9c3ebc077a6e22aef62a0f6c8cd13530e083764e9f7bb  configs/briefs/k_d2_task_sigma2.txt
```

## P4-C-RESULT
- utc: 2026-09-26T06:03:33Z
- prev_sha256: ca8b6663c3497ff2a135a989953289d918bb7037ea0e13638f493b811cf2523b
- kind: result
P4-C extended-confirmation result (DECL-P4-3), audited VALID (logs/p4/audit_ext1.json sha256 8e79bb1f...). Counts only.
[line withheld: prize-candidate detail under review]
Run:
- 18 sessions, all used; 0 void; 0 invalid.
- All 18 positive controls read rows Y.
- 1 N0 read dropped (mistyped id; recovering it changes nothing).
- All 18 hand-backs DONE.
Results:
- U (upright) reads named 5,5,5,5,5,5,5,6,7 letters. R (self-null, rot90) reads named 0,0,0,0,0,0,1,1,1.
- Triples: U 5/5/5; R 1/0/0.
- N0: 48 tiles, triple scores 33x0, 4x1, 8x2, 1x3, 2x7. Max 7; P99 7.
- U-R mean pairwise agreement 4.61; one-sided permutation p 5e-5. Exact enumeration by the auditor: 2.1e-5.
Criteria:
- (i) median U > N0 max: FALSE (5 vs 7). It fails under any grouping, since the max U pair is 6.
- (ii) every U triple >= 5: TRUE.
- (iii) U > R: TRUE.
- SG 1c spirit: max U - P99 = -2 (bar 10).
Auditor's reading:
- U vs R shows a reproducible feature: one row, y std 0.12-0.14 mm, the same row in every triple, box height median 3.46 mm. It reads as letters only when upright.
- That does not show writing: a fibre band or fold would behave the same way.
- All reads come from one model, so the reads are not independent.
- Both 7-scoring N0 tiles are rotated labelled-adjacent w010-027 text. One of them is the candidate's direct neighbour.
Note: p4_jobs.py changed at 05:53Z (cmd_null only, METRIC-HASH-25), after the ext1 build and score, with no effect on ext1.
Consequence: P4-B closes with no confirmed title lead on the 2.4 um canonical predictions of w010-027 (160 tiles) and w028-037 (171 tiles). P4-D (DECL-P4-4, 1 um-model predictions) proceeds.

## DECL-P4-4-A1
- utc: 2026-09-26T09:52:53Z
- prev_sha256: 388cde7c21ab09203bfad7768f993a9d13e37a13bae4c374d61743525c787bc5
- kind: declaration
Amendment 1 to DECL-P4-4, declared before any P4-D read.
1. Scan-coverage eligibility. The 1.129 um scan 20260608103018 covers only the central and inner region of the scroll. Mesh-valid pixels outside its volume extent carry prediction value 0.
- On M2b, the tile builder measured the per-tile zero fraction as tracking the fraction of the tile's mesh points outside the volume's L0 extent (Pearson 0.998). 21 read-eligible tiles are 100 % outside, and their PNGs are byte-identical.
- Change: a P4-D tile is read only if BOTH hold:
  - >= 50 % of its pixels are mesh-valid (unchanged);
  - < 50 % of its saved mesh points lie outside the 1.129 um volume extent (frac_mesh_points_outside_1129_volume < 0.5, from the builder manifest).
- This is a geometric data-coverage rule, set before any read. It never uses prediction values.
- Effect on M2b: 64 of the 106 mesh-valid tiles are read, and 42 are not (21 fully outside, 21 at 0.67-0.78 outside). M2a gets the same rule when its tiles exist.
2. Correction: the M2b prediction file is 1,175,621,159 B (sha256 51243509...). DECL-P4-4 item 1 mistyped it as 1,175,621,659.
3. M2a status: the M2a tile builder (sibling p4-tiles-a) is stopped by its own session's safety check before starting. The orchestrator does not route that task around the block, and the owner is informed. Until M2a tiles exist, the M2b census runs alone as the reader check and positive-control source. No P4-D candidate can arise from M2b alone, except under the DECL-P4-2 item 5 small-cluster rule.
4. N0 for each P4-D census batch is drawn from that batch's own P4-D tiles (the pool option of METRIC-HASH-25): M2b N0 from M2b, M2a N0 from M2a.

## METRIC-HASH-26
- utc: 2026-09-26T09:58:48Z
- prev_sha256: bd11bfa062c00bec2656a7dd0fbf371829c1c1a969254428943efc94a3032ffb
- kind: metric-hash
P4 census scorer fix, hashed before any P4-D M2a tile or read exists.
- Defect: tools/p4/score_p4.py applied the "every positive is a candidate" rule only when strip.startswith('w010'). P4-D strips carry segment-prefixed names (e.g. '20260623141924-w010-027'), so the M2a title strip would have fallen under the w028-037 small-cluster rule, which is stricter and not the declared rule.
- Fix: the rule is now "strip.startswith('w010') or '-w010-' in strip". Nothing else changes.
- Regression: re-scoring census_b1 (with excl_b union) and census_a (with excl_a) using the new code gives tiles, positives, candidates, N0 and p99 identical to the committed summaries.
- New test: test_segment_prefixed_inner_strip_name_uses_every_positive_rule. P4 tests: 16 passed.
- Found by the orchestrator before any M2a data; M2b (w028-037) scoring is unaffected.

```
581bc41e0229b9316dc1cdf42667d2291038bfb34bcb54eece5be7092303bf86  tools/p4/score_p4.py
1ecd3a4df20c5c4285937ffc251331e1edd1e7b68d64604669ac5c80c743a677  tests/test_p4_score.py
1ebc3e7417206153d9afaadb3806e23f9784f11eeeeaf01c120d18299fd2ddfa  tools/p4/p4_jobs.py
b99335e8dc57d8d38225bf35cde82cfb70ffd3a4e5621710b1da021719bfaba8  tools/p4/p4_phase2.py
cd2401084a5aa9c52689f66765bd2bc0bafd0f518cc4213d0f02838e1282ef13  tools/p4/p4_ext.py
```

## MSG-FORMAT-A1
- utc: 2026-09-26T10:04:35Z
- prev_sha256: 2e066eb5d7c7c541426e9dbe56bd441426968d8b6cbefbc9a64be9d7282ab15e
- kind: decision
MSG-FORMAT-A1. The owner directed this to the orchestrator at about 10:05Z on 2026-09-26: "amend integrity: none to say integrity: no issues instead as that's what you mean".
From now on, an owner message whose period since the last message has no integrity event ends with the line "Integrity: no issues". Otherwise it ends as before, with one line per integrity event since the last message.
The wording changes only. What counts as an integrity event, and the duty to report every one, are unchanged. The opening "No submission ready" line and its at-most-3-line rule are unchanged.

## DECL-P4-5
- utc: 2026-09-26T10:04:35Z
- prev_sha256: b0a8f747875b21a34e0924b45022dca1228ddb426b818208cf4e3cc8403aa8fd
- kind: declaration
DECL-P4-5: P4-E, a raw-CT title search on the inner strip, testing the "different ink" hypothesis. Declared before any P4-E tile, render or read exists; no P4-E pixel has been produced, opened or read.
Why: the organizers write that the title region shows no detectable ink, "possibly a different ink". Ink models trained on carbon-ink labels may not respond to a different ink, but the raw CT can. P4-E reads raw CT, not model output.
1. Material. Official surface volumes of the two w010-027 traces, used as published. The project runs no model. Every input's sha256 is recorded on import.
- E1: segments/20260623141924-w010-027/surface-volumes/1.129um-0.23m-78keV-volume-20260608103018-L1.zarr. It has 116 slices; the centre slice is the mesh surface. The tile grid is identical to P4-D M2a (same segment, same canvas, T from the same px_per_mm).
- E2: segments/20260701183124-w010-027/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr. It has 109 slices. The tile grid is identical to P4-B strip a (T = 8343, origin (0,0)). This trace also covers z ranges outside the 1.129 um scan.
2. Display, fixed now; one projection, no alternatives tried.
- Pixel values: per canvas pixel, the mean over the central slab of +-53 um around the mesh surface. For E1 that is 47 slices at 2.258 um; for E2, 45 slices at 2.4 um.
- Computation: at level 0, or at a multiscale level whose in-plane pixel is <= 18.7 um, using the matching depth range.
- Contrast: a linear 1-99 % stretch per tile over its mesh-valid pixels, as in the DECL-P4-2 item 7 package render. 0 outside mesh-valid.
- Output: downscaled with cv2.INTER_AREA to 1068 x 1068 (53.4 px/mm), uint8, flat uuid PNGs (IHDR/IDAT/IEND).
3. Eligibility.
- >= 50 % mesh-valid.
- For E1 only, the DECL-P4-4-A1 scan-coverage rule: < 50 % of a tile's mesh points may lie outside the 1.129 um volume.
- Labelled-adjacency: E1 uses excl_d_a (P4-D M2a flags), E2 uses excl_a (P4-B strip a), both with the union flag.
4. Census, candidates, phase 2 and extended test, all as P4-D (DECL-P4-4 item 3-4 and A1):
- Opus readers, key sheet v2 and task text v2; the task text is unchanged, so readers are not told the image is raw CT.
- One N0 per session, drawn from the batch's own tiles and rotated 90 degrees.
- p99 is computed per material batch.
- Every positive, non-labelled-adjacent w010-027 tile is a candidate (cap 20 per material).
- Phase 2 per DECL-P4-2 item 6 with A3/A4. The positive-control pool is the P4-D M2b largest cluster; that is prediction material, disclosed.
- Extended test per DECL-P4-3. Only EXT-CONFIRMED leads to a package.
5. Multiplicity, disclosed: P4-B, P4-D and P4-E search the same papyrus on 3 materials. Each lead must pass its own extended test; nothing is pooled across materials after the fact.
6. Honest odds: low. Carbon ink is nearly invisible in raw CT at these resolutions. P4-E can succeed only if the title ink differs physically.
7. Builders: sibling p4-tiles-b (E1, after M2b) and sibling pairs0814b (E2). The orchestrator never views a tile.

## D3-VERDICT
- utc: 2026-09-26T10:19:01Z
- prev_sha256: 5b28f7627f72f114f23d5f32aec3301f5f3c6ea61d51bfc74d810ba20a6ea924
- kind: result
D3-VERDICT (FOLD-0841; DECL-D3D4, DECL-D3-A1..A3, METRIC-HASH-18). Outcome: NOT PASSED. Audit: PASS (logs/d1/audit_d3.json sha256 3ad936ed...). The first two auditors were stopped before writing (an owner-side interrupt, then an account usage limit); the third completed.
Numbers (logs/d1/d3_summary.json sha256 fb8d31c0...):
- 24 sealed reads by the frozen reader of READCAL-FREEZE (4 re-run under D3-RERUN-1). All 24 are audit-valid, and every prompt equals its brief.
- C_all and C_net are 0 at 250 px for all 8 arm-states. p_max(FA) = 1.
- FA readers named 0 letters on all 72 J and blank panels.
- Namings on J items: NULLA-A 1, NULLA-B 1, plus 1 NULLA-B naming on a blank. The runner's n_named_total counts blanks. All are > 250 px from every seal letter.
- F_B per reader: CTRL-A 1.67, CTRL-B 1.0, REVA-A 0.33.
- Every reader named 3-13 letters on the known-text canary, so readers could read.
- FA blob-f180 on the w053 blanks: 0.00029 and 0.00348 (bar <= 0.0272).
- Checks: FA >= CTRL+3 false; p_max < 0.01 false; the other 5 true.
Audit findings:
- The re-derivation matches, with 0 mismatches over 144 scored records.
- Training: 2000 finite-loss steps per arm. model_final hashes are consistent in 4 of 4 arms. CTRL has 0 fold-A tiles. The replay set has 0 PHerc0841 tiles.
- The minimum point-to-surface distance from a fold-A tile to J is 144.56 vox (bar 128; recomputed, because the records held point-to-point distances only).
- Displays rebuild exactly from their arm's maps (128 of 128). The J frame equals D1's.
- Note: DECL-D3-A3 (10:54:44Z) came 9 minutes after CTRL's first training step. A3 pins only inference and displays and says CTRL was training; no map existed yet. Not invalidating.
Meaning:
- Fine-tuning the base 9 um model on nearby PHerc0841 papyrus (fold A, 288 tiles) did not make unseen 0841 text nameable by the frozen reader.
- J decisions used: 2 of 3.
- K1 JULY clock: D1 not PASS = TRUE and D3 not passed = TRUE. D2 NOT RUN becomes true on 2026-11-15 unless a GPU appears. K1 is not yet triggered.

## METRIC-HASH-27
- utc: 2026-09-26T10:19:53Z
- prev_sha256: 2e15500bac01abfeeb8c97f630d6b883c1a40cfe9bc1e3683345cd11e46051d0
- kind: metric-hash
P4 import step, hashed before any M2a, E1 or E2 tile exists. tools/p4/norm_manifest.py turns a sibling builder's manifest into the import manifest for p4_jobs.py import. It applies the declared eligibility rules:
- valid_fraction >= 0.5;
- with --coverage (P4-D M2a and P4-E E1), also frac_mesh_points_outside_1129_volume < 0.5.
Tile bytes come from git and are checked against the builder's png_sha256.
Regression: on the M2b manifest it reproduces the M2b import exactly (64 eligible, 42 skipped for coverage, same tiles and hashes). The P4 scoring and read code is unchanged since METRIC-HASH-26.

```
b549026e8ff2cff9f8b97ff221d87f44d3bed7cc1702f4874c5efc8c1a6f4d0d  tools/p4/norm_manifest.py
1ebc3e7417206153d9afaadb3806e23f9784f11eeeeaf01c120d18299fd2ddfa  tools/p4/p4_jobs.py
581bc41e0229b9316dc1cdf42667d2291038bfb34bcb54eece5be7092303bf86  tools/p4/score_p4.py
b99335e8dc57d8d38225bf35cde82cfb70ffd3a4e5621710b1da021719bfaba8  tools/p4/p4_phase2.py
cd2401084a5aa9c52689f66765bd2bc0bafd0f518cc4213d0f02838e1282ef13  tools/p4/p4_ext.py
```

## DECL-OFFLOAD-1-A1
- utc: 2026-09-26T17:29:07Z
- prev_sha256: e0b8c28db2a0bf7f0ce2c872654e808d16e00c2c2f62cc549541fec28c316146
- kind: decision
Owner delegation of the DECL-OFFLOAD-1 item 6 disk choice (owner message 2026-09-26 ~17:25Z: "keep going ... make your own decisions as brilliant and wise as possible", in reply to the orchestrator's request to approve options 1-3). The orchestrator takes the two options it had recommended, zero-loss and regenerable only:
1. Delete /work/docker/containerd (4.9 GB): the docker image store for the render tooling. It holds no project data and is rebuilt from docker/TOOLING.md and docker/env (about 10-15 min). The docker daemon is not running (container restart at 17:25Z).
2. Delete git garbage in .git/objects (3 tmp files, 14.6 MB): interrupted fetch leftovers, not referenced by any ref.
Not taken: option 3 (offload of closed-decision data to claude/gifted-bell-gavnl5-data). Item 4 requires the owner's explicit permission for pushes to the data branch; a general delegation is not read as that permission.
Event recorded: the container restart at 17:25Z cleared /dev/shm, which held the 109 MB of duplicate named tile copies moved from /work/p4/src (orchestrator's move, reported to the owner). Their content remains in the builders' branches on GitHub (sib-p4-tiles-a, sib-p4-tiles-b, sib-pairs0814b), and the reading copies in /work/p4/img are checked against the import manifests before any new read.
No bar, seal, key or declared rule changes.

## DECL-OFFLOAD-1-A1-CORR
- utc: 2026-09-26T17:30:07Z
- prev_sha256: 9ba7ece93082cc30a1bf43a8160715cd89f2fc6450f5ee59767119e26a065dbd
- kind: correction
Correction to DECL-OFFLOAD-1-A1: its items 1 and 2 were NOT executed. The deletion command was refused by the session's auto-mode safety check (reason given: irreversible local destruction). Nothing was deleted, and the refusal is not worked around (no move to tmpfs, no piecemeal deletion, no other host). Deleting existing files waits for the owner's explicit approval of those specific deletions. Disk stays at about 109 MB free, and new local work uses RAM-backed /dev/shm for scratch and sibling containers for bulk work.

## DECL-REMOTE-HARNESS-1
- utc: 2026-09-26T17:35:02Z
- prev_sha256: 13debe47522d1c9622b3765b91020e41db786aae7132b55533b520babb435097
- kind: declaration
DECL-REMOTE-HARNESS-1: blind P4 reads run in sibling containers. Declared before any remote read exists.
Why: the orchestrator container has about 109 MB free, the deletion of regenerable files was refused (DECL-OFFLOAD-1-A1-CORR), and each reader transcript takes about 10 MB. Reading locally would fill the disk mid-run. Registry amendment: a harness sibling ("rh-*") may launch blind reader agents. It never views, reads, decrypts or scores itself, and no seal material is ever given to it.
1. Code: the harness sibling checks out claude/gifted-bell-gavnl5 at a commit whose tools/p4 and src/hercules/harness hashes equal METRIC-HASH-27. Paths are unchanged: /work/p4/img, /srv/scorer, /work/sealed_io and /home/user/dominion/configs/briefs.
2. Material: tools/p4/norm_manifest.py <builder ref> <manifest> <tiles dir> <out> [--coverage] fetches the tiles from the builder's branch. Bytes are sha256-checked against png_sha256.
3. Batches: tools/p4/p4_jobs.py import, then null (N0 from the batch's own census tiles, rot 90), then jobs ... sigma2. Batch names must not collide with existing keys: E1 is e1 / ne1 / census_e1, E2 is e2 / ne2 / census_e2, P4-D M2a is d_a / nd_a / census_da, and P4-F follows the same pattern with f*.
4. Commit A, pushed before ANY reader is launched:
   - key files copied from /srv/scorer, with their sha256;
   - jobs json and all briefs;
   - an img manifest mapping uuid to sha256;
   - the builder ref and commit.
5. Readers: one fresh general-purpose agent per job, model opus. The prompt is the brief file's bytes exactly. Sealed-output mode writes to the orchestrator's age recipient age1vp0tkyj8xecncfmcxj748ceef89mpmwayljccaduapjx3aqhh5rstvvcq5, whose private key exists only in the orchestrator's /srv/scorer, so the harness sibling cannot read any answer.
6. Commit B, after the reads:
   - the .age files;
   - per-job audit output of hercules.harness.audit.audit(transcript, images, sealed_output, recipient), which prints no content;
   - gzip copies of each reader transcript;
   - the harness_jobs rows.
   An audit-invalid job is re-run fresh with the same brief, and the rerun is disclosed.
7. The orchestrator fetches only the key, jobs, .age and audit files. Before decrypting, it checks:
   - key sha256 == commit A;
   - commit A precedes every .age file in history;
   - the .age hashes equal the transcripts' written paths via the audit.
   Scoring is local, with score_p4.py (METRIC-HASH-27). Before any result is recorded, an independent sibling or the orchestrator re-runs the audit on the pushed transcripts. A mismatch voids the batch.
8. Everything else is unchanged from DECL-P4-2/4/5: bars, N0 rule, candidate cap, phase 2 and extended test.

## DECL-P4-5-A1
- utc: 2026-09-26T17:35:02Z
- prev_sha256: 9bf2359e870fc6556aa45f30d0196ef2e895d82033ba5ac910d2fa32d73b5d2f
- kind: declaration
DECL-P4-5-A1: E1 display stretch for tiles that contain out-of-scan pixels. Declared before any E1 tile has been read, viewed or imported; the builder p4-tiles-b reports only numbers.
Defect: DECL-P4-5 item 2 stretches 1-99 % over mesh-valid pixels. In 23 E1 tiles (rows 3-4), more than 1 % of the mesh-valid pixels sample zero CT (mesh points outside the 1.129 um scan or in absent chunks). That forces p1 = 0 and compresses papyrus contrast. The zeros are not papyrus.
Fix, applied to all 60 eligible E1 tiles alike so the display rule stays uniform:
- the 1-99 % stretch is computed over mesh-valid pixels whose slab mean is > 0;
- pixels with a slab mean of 0 are written as 0.
Nothing else changes: slab, projection, eligibility, grid or output size.
The builder rebuilds and pushes the tiles with a new manifest (sha256 per tile) and records, per tile, the old and new p1/p99 and the zero fraction. The superseded tiles are never read.

## DECL-P4-6
- utc: 2026-09-26T17:35:02Z
- prev_sha256: b95fd3ed2c17e70999b0a671ba2b5a5bf8beb65c82175e50c9d79aaab04a77e7
- kind: declaration
DECL-P4-6: P4-F, a dense-ink (mineral pigment) channel on the Paris 4 inner strips. Declared before any P4-F computation, tile or read. Owner prompt 2026-09-26: "a different ink could be a different color like a red ink".
Physics: ancient red inks are cinnabar HgS, red lead Pb3O4 (which becomes PbO above about 500 C), red ochre or hematite Fe2O3, or organic lakes.
- Mineral pigments do not carbonise. At the 300-400 C of the Herculaneum surge, HgS, Fe2O3 and the lead oxides survive.
- They hold high-Z elements (Hg 80, Pb 82, Fe 26), so at 78 keV they attenuate far more than carbonised papyrus and carbon ink.
- A mineral-pigment title would appear as thin (5-30 um), anomalously bright material on the recto surface. The DECL-P4-5 mean over +-53 um dilutes it, and carbon-ink models ignore it.
- Organic red lakes carbonise like the substrate; P4-F cannot see them. That is disclosed as a blind spot.
- Lead-bearing black ink has also been reported in Herculaneum papyri, so the known-text control may itself light up. That is informative either way.
1. Material: the E1 and E2 surface volumes (DECL-P4-5 item 1), plus the known-text control 20260623142658-w028-037 at 1.129 um where available. The project runs no model.
2. Channel, fixed now: per canvas pixel, the maximum over the slab of +-15 um around the mesh surface (E1: 13 slices at 2.258 um; E2: 13 slices at 2.4 um), computed at level 0 or 1 and then area-downscaled.
   - Display threshold T_hi per material is the 99.9th percentile of in-sheet slab voxels over the known-text control strip (for E2 without a 2.4 um control, over the E2 strip itself).
   - Tile value is min(255, 255*(max - T_mid)/(T_hi - T_mid)), with T_mid the control's median, clipped to [0, 255]. 0 outside mesh-valid.
   - The grid, 1068 px size, eligibility and flags are as in DECL-P4-5 (E1 with coverage).
3. Numeric screen, before any read. For every tile, the builder reports:
   - n_hi (voxels > T_hi within +-15 um);
   - the fraction of n_hi inside the sheet slab versus in the +-(60-120) um gap slabs;
   - the radially averaged autocorrelation peak of the hi mask at 2-4 mm.
   The null is the same statistics on the known-text control and on a 90-degree-rotated copy.
   - A tile is a DENSE-HOTSPOT if n_hi exceeds the control's tile p99 AND the in-sheet fraction is >= 0.8.
   - Hotspots are reported by number, never viewed.
4. Reads: the census as DECL-P4-5 item 4 (Opus, key sheet v2, one N0 per session, remote harness per DECL-REMOTE-HARNESS-1).
5. Validation required before any claim: the letters must lie on the sheet (in-sheet fraction), be absent in the gap slabs, survive the rot-90 null, and pass the DECL-P4-3 extended test. A mineral title would additionally show stroke-width consistency (15-60 um after the thin-layer model) that the builder can measure numerically.
6. Builder: new sibling p4-highz. It never views an image.

## DECL-P4-7
- utc: 2026-09-26T17:35:02Z
- prev_sha256: 8d627398462c580beb9a8b57fb117a832c9b21fde888da8bf8d9785d2e4a9651
- kind: declaration
DECL-P4-7: P4-G, a search for papyrus windings inward of the segmented inner strips of PHerc. Paris 4, including windings the published labelling may have missed. Owner prompt 2026-09-26: "just because it says winding w000 doesn't mean the human labeling is perfect, they could have missed inner ones". Geometry only; no reading is authorised by this entry.
Why: the end title of a roll lies in the innermost windings. Official meshes start at w010 (w000-w009 unsegmented, p4-inner RECON). A winding count that misses tight core turns would hide exactly the title region.
1. Count, numeric only, in the 1.129 um and 2.4 um volumes:
   - the umbilicus (roll axis) per z;
   - along >= 64 rays per z-slice at >= 20 z-levels, the sheet crossings, found as intensity peaks after a 20 um smoothing, from the umbilicus to the w010 mesh.
   The estimated number of windings inward of w010 is taken per ray and per z.
2. Validation of the count:
   - the crossing spacing must be consistent with the labelled spacing of w010-w020 (median and IQR reported);
   - the counts must be continuous across adjacent rays and z-levels (step-change rate reported);
   - planted-sheet synthetic tests must show a counting error <= 1 winding.
   A count above 10 inward of w010, stable over >= 80 % of rays, is evidence of windings beyond the labelled numbering.
3. Tracing, if 1-2 show papyrus: the VC3D/tracer tooling (sibling tracer) on a 2 x 2 cm core window first. Its validation metrics are:
   - no mesh self-intersection;
   - winding-number continuity with the w010 mesh;
   - point-to-surface distance to the neighbour winding >= 60 % of the local spacing;
   - flattening distortion (area and angle error, FLAT-2 tooling);
   - fibre continuity of the recto texture (vertical/horizontal fibre-orientation coherence >= the w010 strip's median).
4. Any render or read of a new core surface needs its own declaration first.
5. Builders: p4-inner (continues) and new sibling p4-core; they never view an image.

## DECL-OFFLOAD-1-A2
- utc: 2026-09-26T17:45:36Z
- prev_sha256: ff41434ecfc9622cc802bf2f5169f46ad071e7228e73a3d606773f259491511f
- kind: decision
Owner approval (owner message in this conversation, 2026-09-26, replying to the orchestrator's two exact sentences "I approve deleting /work/docker/containerd" and "I permit pushing to claude/gifted-bell-gavnl5-data"): "I approve both."
1. Deletion of /work/docker/containerd (4.9 GB) is approved. It is the docker image store for the render tooling, holds no project data, and is rebuilt from docker/TOOLING.md.
2. Pushes to claude/gifted-bell-gavnl5-data are permitted (DECL-OFFLOAD-1 item 4). The offload of closed-decision data (/work/readcal, /work/c3, /work/d1) follows DECL-OFFLOAD-1 item 3 exactly:
   - one batch per commit, <= 1.5 GB per batch, files <= 95 MB, allowlisted extensions only;
   - no keys, nothing from /srv/scorer or /work/sealed_io, no symlinks;
   - the remote tip is verified to equal the pushed commit, and every file's sha256 is recorded in logs/offload/manifest.jsonl, before any local copy is removed.
   If there has been no prior push, the first push is the synthetic round-trip self-test.
   Files that the offload refuses (too large, extension, key) stay local.
Nothing else is deleted under this approval.

## METRIC-HASH-28
- utc: 2026-09-26T17:52:17Z
- prev_sha256: d052d7ae3a4405b4b851aef56fdef06eef92e8d879ca6536598b78c45287bb38
- kind: metric-hash
Remote-harness verification and install step (DECL-REMOTE-HARNESS-1 item 7), hashed before any remote-harness answer is decrypted.
- tools/p4/rh_verify.py independently checks a harness branch. Checks:
  - A0: code hashes equal the local files.
  - A1: commit A precedes commit B.
  - A2: keys and jobs match SHA256SUMS, with a sane key shape.
  - A3: image hashes equal the key's src_sha256.
  - A4: the key's (r, c) set equals the builder's declared-eligible set; --coverage is passed for E1, M2a and P4-F.
  - A5: every brief equals the reference brief (/work/p4/brief_55e9f823-..., census_db, sigma2) after normalising the image lines and the job uuid, and the jobs cover every tile exactly once.
  - B1: the .age hashes.
  - B2: hercules.harness.audit VALID, prompt == brief, and every transcript timestamp later than commit A.
  - B3: the decrypted answer equals the transcript's sealed-write body (logged purpose rh-verify-consistency; booleans only).
  Only if every check passes, --install writes the keys (O_EXCL 0400), .age files, job records and the jobs json into the paths score_p4.py reads.
- Scoring is unchanged: score_p4.py census (METRIC-HASH-27).
- E2 labelled-adjacency file: logs/p4/excl/excl_a_union_e2.json (sha256 bcfd8564bd10332356c554f1df4d9ebe3997ca5d2f35f31d47374226b92ce9da). It is derived from p4-excl excl_a.json at b2d6414d: the union flag, and the strip renamed to 20260701183124-w010-027 (same grid, DECL-P4-5 items 1 and 3). 120 of 160 tiles are flagged.

```
4b5f8aeb440cd1165ca6287a20b780bb9d75b89ee374369f27121f6e1b04d87d  tools/p4/rh_verify.py
bcfd8564bd10332356c554f1df4d9ebe3997ca5d2f35f31d47374226b92ce9da  logs/p4/excl/excl_a_union_e2.json
```

## P4-E2-CENSUS-RESULT
- utc: 2026-09-26T17:54:05Z
- prev_sha256: 90ae6186f5a6f0c2f7db57c73ae6206b51412c31a3915db19ed5e5b82ed641ca
- kind: result
P4-E2-CENSUS-RESULT (DECL-P4-5 E2, DECL-REMOTE-HARNESS-1, METRIC-HASH-27/28). Material: raw 2.4 um CT of 20260701183124-w010-027, a +-53 um slab mean at level 2 (9.6 um), 1068 px tiles (builder pairs0814b cc81a677).
Harness: rh-e2 (session_01A3X1L6erjPGxEx7rGuWju2):
- commit A f2502c2 at 17:40:57Z holds the keys, jobs and briefs;
- commit B 1ddf5ef at 17:46:54Z holds 20 sealed reads by fresh Opus readers (sigma2 key sheet).
Independent verification: tools/p4/rh_verify.py passes all 12 checks, A0-A5 and B1-B3. Those include commit order, the key vs the builder's eligible set, brief equality, a local re-audit of all 20 transcripts (VALID, prompt == brief, all after commit A), and decrypted answer == sealed-write body. Record: logs/p4/rh_verify_e2.json sha256 6b0fc7eeedb9cec2afc4ee6c4d58bdd7ae0c8ac7e60e8d20a9ab7ae926b9aacc.
Census (logs/p4/census_e2_summary.json sha256 7954db60614afca5b6e3a61bab2a5ce7367a5708927819d2ced8572fbb872cce):
- 20/20 answers valid; 160 census tiles; 20 N0 (rot 90);
- N0 letter counts nineteen 0 and one 1, so p99 = 0.81 and the threshold is 5;
- rows Y on 8 tiles; 0 positive; 120 labelled-adjacent (excl_a union); 0 candidates.
Meaning:
- At this display, raw 2.4 um CT gives no nameable letters anywhere on the strip. That includes the 120 tiles adjacent to labelled (known-ink) segments, so the material does not show ordinary carbon ink, as DECL-P4-5 item 6 expected.
- No physically different (strongly contrasting) ink is visible at 9.6 um either.
- P4-E E2 closes with no lead. E1 (1.129 um), M2a (1 um predictions) and P4-F (dense channel) remain.

## METRIC-HASH-29
- utc: 2026-09-26T17:55:16Z
- prev_sha256: f08703044bff3e367c6a66ff0c62567f71b8499f677a3d092ab288a6d31c46df
- kind: metric-hash
Coverage-field key fix, declared before any M2a key, job or read exists (rh-e1 ASK-1).
- p4-tiles-a's M2a manifest (52bcf46) carries frac_mesh_points_outside_1129_volume at the top level of each tile. METRIC-HASH-27 norm_manifest.py read that name only under stats, so the declared command found 0 eligible tiles.
- Fix in tools/p4/norm_manifest.py: read the name under stats, else the same name at top level, else top-level frac_outside. The rule itself (< 0.5, missing -> not eligible) is unchanged.
Regression: eligibility decisions are identical under the old and new code on the M2b (64) and E1-A1 (60) manifests. On M2a the new code gives 60 eligible tiles, equal to the builder's count and the identical (r, c) set to E1-A1 (same grid, DECL-P4-5 item 1).
- tools/p4/rh_verify.py: A0 also accepts the earlier declared norm_manifest.py (METRIC-HASH-27, b549026e...) for batches imported with it, such as rh-e1 E1. The re-run on rh-e2 still passes 12/12.

```
d2faee660c36db99531755b6f30f4269acd6c5f5b4ebe90ac79ec80d5f596a8f  tools/p4/norm_manifest.py
adcda18cd47af317b7fe14b103b524ee471f5bd2050d9cebaea78ed06d28cd37  tools/p4/rh_verify.py
```

## DECL-P4-8
- utc: 2026-09-26T17:56:54Z
- prev_sha256: 3967dff037bb6355cf3f1fec3a8df594946b1985d5bb408eb4804df035af78e7
- kind: declaration
DECL-P4-8: P4-I, a reader-free numeric ink-structure screen of the Paris 4 title strip w010-027. Declared before any P4-I number exists. It uses only tiles that already exist, loaded as arrays; no tile is viewed.
Why: the census asks readers to name letters, which is noisy near the bar (P4-C: 2 of 48 N0 tiles reached 7). Text has a physical signature independent of naming: rows at a regular pitch. A numeric screen ranks where structure exists, before and independent of any reading.
1. Materials:
   - title strip: M1 (P4-B strip a, 160), M2a (60), E1-A1 (60), E2 (160), and P4-F once built;
   - known-text controls on the same materials: M1-b (w028-037, 171) and M2b (64).
   The tile bytes are the builders' pushed PNGs, sha256-checked against their manifests.
2. Statistic per tile, computed over mesh-valid, in-scan pixels:
   - S_row = max over orientation theta (0-180 deg, 2 deg steps) of the 2-D power-spectrum peak in the band of periods 3-9 mm, divided by the median power in that band at the same |k| over all orientations;
   - its angle theta*;
   - M_ink = the fraction of pixels above the control strip's pixel p95 for the same material.
3. Null and gates, per material:
   - Null: S_row on the rot-90 copy of every tile of that material (title and control strips pooled); T_mat = its p99.
   - Sensitivity gate: at least 30 % of the known-text control tiles that are not blank (M_ink >= the control median) have S_row > T_mat, with theta* within +-10 deg of the control's median theta*.
   - A material that fails the gate is reported as uninformative and not used.
4. STRUCT-positive: a title-strip tile that is not labelled-adjacent (excl_a union for M1/E2; excl_d_a for M2a/E1/P4-F), with S_row > T_mat and theta* within +-10 deg of the control median, in a material that passed its gate.
5. Use: STRUCT-positive tiles are ranked for a targeted read. That read needs its own declaration (more readers per tile, multi-scale display) before any read. Nothing is claimed from the screen alone.
6. Validation reported with it:
   - the gate numbers;
   - how well S_row separates control tiles from their rot-90 copies (AUC);
   - the agreement of STRUCT-positive sets across materials on the same grid (M2a, E1 and P4-F share the grid): Jaccard, with a permutation p against random sets of equal size.
7. Builder: new sibling p4-struct. Numbers only.

## DECL-P4-9
- utc: 2026-09-26T17:56:54Z
- prev_sha256: 5e8f1fb118a16a5a1c9222460b2d11e05187d04267d3e15158cda5bd03be027e
- kind: declaration
DECL-P4-9: P4-H, a 1 um "crackle" texture channel on the Paris 4 title strip. Declared before any P4-H computation.
Physics: dried carbon ink on papyrus forms a cracked micro-texture ("crackle", a known carbon-ink cue in Herculaneum CT) at tens of um. Raw 1.129 um CT resolves it, but the DECL-P4-5 display (a slab mean area-averaged to 18.7 um) destroys it. A texture-energy channel turns crackle into display-scale brightness, and it is our own detector, independent of the official 1 um model.
1. Channel, fixed now. At level 0 of the 1.129 um surface volumes:
   - for each slice within +-20 um of the mesh surface, take the difference of Gaussians (sigma 1.5 px and 6 px in-plane), squared;
   - average over those slices;
   - area-average to the 18.7 um display grid;
   - then apply the DECL-P4-5-A1 stretch (1-99 % over mesh-valid pixels with CT > 0) and produce 1068 px tiles on the E1/M2a grid.
2. Validation gate, BEFORE any title-strip tile is computed or read. On the known-text control 20260623142658-w028-037 (1.129 um), on >= 12 tiles:
   - compute the pixel AUC of crackle energy against the official 1 um prediction map of the same tiles (M2b): ink = prediction >= its p90, background = <= its p50, excluding pixels within 50 um of either class boundary;
   - the bar is AUC >= 0.70;
   - sanity check: against the rot-90 prediction map, the AUC must be 0.50 +- 0.03.
   If the gate fails, P4-H stops and is reported.
3. If the gate passes:
   - tiles for all 60 E1-grid eligible tiles;
   - also report the same AUC on the title strip against M2a (a report only; no claim);
   - census per DECL-P4-5 item 4 via DECL-REMOTE-HARNESS-1 (batches h1 / nh1 / census_h1; flags excl_d_a).
4. Blind spot, disclosed: a non-carbon ink may not crackle. P4-F covers dense mineral inks.
5. Builder: new sibling p4-crackle. Numbers only; level-0 compute is split by row across sub-siblings.

## DECL-P4-6-A1
- utc: 2026-09-26T17:58:39Z
- prev_sha256: 523110c390571050dacbe8d193a5b2d7a5ed4305450cbaac46f78f3d7c7680bd
- kind: declaration
DECL-P4-6-A1: priority and a dual-energy extension for P4-F. Declared before any P4-F number exists.
Owner input (2026-09-26 ~17:58Z, verbatim excerpt): "Greek scholars and scribes wrote section titles (known as inscriptiones) in a different color ink virtually every time they produced a formal manuscript ... rubrication, heavily favored red ink."
Orchestrator's scholarly note, recorded for honesty:
- Rubrication is standard in medieval codices and in Egyptian papyri.
- For Greek literary rolls of the Herculaneum period, the titles read so far are, to the orchestrator's knowledge, mostly in the same black ink.
- The prior for a red title is therefore treated as plausible, not near-certain. The test below does not depend on the prior.
1. Priority: P4-F (DECL-P4-6) is raised to first priority among the untested P4 channels.
2. Dual-energy K-edge extension, numbers only:
   - p4-highz inventories every published PHerc. Paris 4 scan, recording energy, pixel size, registration to 20260411134726 and coverage of the w010-027 strip. The 1.129 um and 2.4 um scans used so far are both 78 keV.
   - Suppose two registered scans bracket the Hg K-edge (83.1 keV) or the Pb K-edge (88.0 keV). Their attenuation ratio on the strip would then identify Hg- or Pb-bearing pigment specifically (cinnabar, red lead). Carbon ink and papyrus show no edge there. Fe (red ochre) has no edge in this range, so only its density shows.
   - Any K-edge map or read needs its own declaration before any number is computed.
3. Blind spot, restated: organic red dyes carbonise with the substrate, so no CT channel sees them.
No bar, threshold, seal or earlier rule changes.

## DECL-P4-6-A2
- utc: 2026-09-26T17:59:12Z
- prev_sha256: 35bacf3686fc1deb50408462ce4b722f32d6d91002d1cb0c94d0be39bfd7b9c4
- kind: declaration
DECL-P4-6-A2: pigment scope of P4-F widened, declared before any P4-F number exists.
Owner input (2026-09-26 ~18:00Z): besides red, gold was used for major titles, and blue or green for secondary titles. The orchestrator notes that these conventions are attested mainly in Byzantine codices, later than Herculaneum; the physics test below does not depend on them.
Physics:
- Gold (chrysography, Au Z 79) is inert through carbonisation and extremely attenuating. Its K-edge is 80.7 keV, just above the 78 keV scans.
- Blue: Egyptian blue (CaCuSi4O10) is stable to ~1000 C. Azurite and the greens malachite and verdigris decompose on heating to Cu oxides and keep their Cu. Green earth is Fe-bearing.
- Organic blues and greens (indigo, plant greens) carbonise and are invisible to every CT channel; this blind spot is disclosed.
Changes:
1. The DECL-P4-6 dense channel and its DENSE-HOTSPOT screen apply unchanged. They already respond to Au, Hg, Pb, Cu and Fe pigments by density; Cu and Fe give weaker contrast than Hg, Pb or Au.
2. The DECL-P4-6-A1 K-edge inventory also flags any registered scan pair that brackets the Au K-edge (80.7 keV).
No bar, threshold, seal or earlier rule changes.

## DECL-P4-10
- utc: 2026-09-26T17:59:56Z
- prev_sha256: c1d338715a5971be15ccd37c25193d8ba179fb2637cf3c3e876c757c6f384f46
- kind: declaration
DECL-P4-10: P4-J, per-pigment-family searches of the Paris 4 title strip, validated by injection-recovery. Declared before any P4-J number exists. Owner (2026-09-26 ~18:02Z): "have each or new siblings look for different expected colors like this and do more research. need to win today."
Families. Each gets one builder sibling; organic dyes carbonise and are out of scope for every CT channel:
- RED: cinnabar/vermilion HgS and red lead Pb3O4 (-> PbO); K-edges Hg 83.1 and Pb 88.0 keV.
- GOLD: shell gold or leaf (Au); K-edge 80.7 keV. A sub-micron leaf appears only through partial volume.
- CU (blue/green): Egyptian blue CaCuSi4O10 (crystalline grains of ~1-50 um); azurite, malachite and verdigris -> CuO.
- FE (red/yellow ochre, green earth): Fe2O3 (yellow ochre turns red on heating); a weak contrast.
1. Research memo per family:
   - thermal stability at 300-400 C in a reducing pyroclastic setting;
   - grain size and layer thickness;
   - mass attenuation at 78 keV (and at the other Paris 4 scan energies) vs carbonised papyrus and carbon ink, from tabulated data (NIST XCOM or equivalent, cited);
   - the expected voxel contrast at 1.129 and 2.4 um;
   - attestation in Greek papyri of the 3rd c. BC-1st c. AD, with citations, kept separate from Byzantine or medieval evidence.
2. Detector: one family-specific numeric detector on the raw CT surface volumes (E1 1.129 um level 0, E2 2.4 um level 0 or 1), within +-20 um of the mesh surface. It is designed from the memo (for example, intensity band and grain statistics for CU, extreme outliers and layer planarity for RED/GOLD). Parameters are frozen in a pushed params.json before any title-strip number.
3. Validation, required before any title-strip result counts:
   - Injection-recovery: synthetic letter-shaped strokes (Greek capitals, 2-4 mm tall, stroke 0.3-0.6 mm) of the family's attenuation at 3+ layer thicknesses are planted into real E1/E2 CT of >= 10 known-text-control and >= 10 title-strip locations. Report recovery (sensitivity) per thickness and the detection limit.
   - False-positive rate on the known-text control (carbon ink) and on rot-90 nulls.
   - A detector with sensitivity < 0.8 at the family's plausible thickness is reported as "insensitive"; that is not "absent".
4. Output, numbers only: per tile of the E1/E2 grids, the detector score and the hotspot list. A hotspot is a non-labelled-adjacent tile whose score exceeds the p99 of the control plus rot-90 null and whose signal lies on-sheet (in-sheet fraction >= 0.8). Hotspots go to a targeted read or render under a separate declaration.
5. Builders: siblings p4-pig-red, p4-pig-gold, p4-pig-cu and p4-pig-fe. A research sibling, p4-research, compiles the historical and codicological evidence on end-titles of Herculaneum and Greek literary rolls: position, size, ink, decoration, stichometry. It also compiles what the organizers have published about the Paris 4 title region. Its purpose is to direct where to look. Nothing is viewed; no bar changes.

## METRIC-HASH-30
- utc: 2026-09-26T18:03:25Z
- prev_sha256: 239c7fa063b76faf99f7577ad4f344b5054b9cbb10cb6345baa54a597e8142b1
- kind: metric-hash
rh_verify.py A5 fix (rh-e1 ASK-2), before any E1 or M2a answer is decrypted.
- The METRIC-HASH-28/29 normalisation kept one marker per image line, so a batch's partial last session never equalled the 8+1 reference brief. E1 and M2a have 60 tiles, giving 7 sessions of 8+1 and one of 4+1.
- Now each run of image-path lines collapses to one marker. The image count is checked explicitly: len(images) == n_images == 1 + n_census + n_null of the job.
Regression: rh-e2 still passes 12/12 (every session is 8+1).
Also recorded: the DECL-OFFLOAD-1-A2 offload finished. There were 3 batches (1,323 files, 3.39 GB): closed-20260926T1747-00 d15f21c7, -01 ccbe6651 and -02 2444e884 on claude/gifted-bell-gavnl5-data. The remote tip was verified before each local removal, and the manifest is in logs/offload/manifest.jsonl.

```
683acc3d731668cf3fd3ae0720e2cb5587c915f00c71f1111c4571376b53e7df  tools/p4/rh_verify.py
```

## METRIC-HASH-31
- utc: 2026-09-26T18:04:37Z
- prev_sha256: 118d80ce65c5465e5b5d9010e9a81704bad885ced070ab6811c764b2ef559ceb
- kind: metric-hash
rh_verify.py A4 fix: the verifier's own copy of the eligibility rule now reads the coverage field with the METRIC-HASH-29 semantics: under stats, else the same name at top level, else frac_outside. Before the fix, A4 failed on rh-e1 M2a (builder p4-tiles-a 52bcf46 puts the field at top level) although the batch matches the declared rule. Nothing else changes.
Regressions: rh-e2 and rh-e1 E1 still pass 12/12, and both were run before this entry is pushed. The E1 install was done under METRIC-HASH-30 (683acc3d...), and its checks do not depend on this line (E1-A1 nests the field under stats).

```
6a9a91b21173a650d3cfbdac95438627d3ba920568f7b618ef15abe1e0a05051  tools/p4/rh_verify.py
```

## P4-E1-M2A-CENSUS
- utc: 2026-09-26T18:05:55Z
- prev_sha256: bc0879df2f22259e6cd07f8f96c20b187df51d997ac41982e34f1b7092060d43
- kind: result
P4-E1-CENSUS-RESULT and P4-D-M2A-CENSUS (provisional: labelled-adjacency flags excl_d_a pending from p4-excl). Covers DECL-P4-4 (+A1), DECL-P4-5 (+A1), DECL-REMOTE-HARNESS-1 and METRIC-HASH-27..31.
Harness: rh-e1 (session_015TgHhUmDZxB1PoCUiRVgxJ).
- E1: commit A 723b4da (17:51:52Z), then 8 sealed Opus reads.
- M2a: commit A 50b2152 (17:57:15Z), then commit B 74eb472, 8 sealed Opus reads.
Independent verification: tools/p4/rh_verify.py passes 12/12 on both (E1 under METRIC-HASH-30, M2a under METRIC-HASH-31). Records: logs/p4/rh_verify_e1.json 77298c2cfded6bad46f85c3cd774ebdac5a8712649108fbf0ee46b1773e9acb1 and logs/p4/rh_verify_da.json 43e7d2d7522103af68788393748de804b60087fee686fd809ec860b78cb94751.
E1, raw 1.129 um CT (logs/p4/census_e1_provisional.json c3cbacf16de18075ef1e15ae30432c5cb03e25d929383734cc92ee81fb7526f1):
- 8/8 valid; 60 census tiles; N0 all 0 letters;
- rows Y 0; positive 0; candidates 0.
- E1 closes with no lead, whatever the flags: raw 1.129 um CT at this display shows no nameable letters anywhere, including text-bearing areas.
M2a, official 1 um-model predictions (logs/p4/census_da_provisional.json ca0a7d72e550c45b897ce46643a12370048d79443152062bd2b9f9d68bac547b):
- 8/8 valid; 60 census tiles; N0 counts 0,0,0,0,0,1,1,2 (p99 1.93, threshold 5);
- rows Y 26; positive 19; provisional candidates 19 before the flags.
- Every positive lies in grid columns 0-9 of rows 2-4 (the eligible rows). Columns 10-19 have none.
- The candidate list is final only after excl_d_a (union flag). A positive that is labelled-adjacent is known text, not a title lead. On the known-text control M2b, all 42 positives were labelled-adjacent.
Observation, recorded as a hypothesis only: on this grid the 1 um predictions show text in columns 0-9 and none in 10-19. If columns 10-19 lie toward the core (the end of the text), the text-to-blank boundary (columns ~9-12) is where an end title would be expected. The winding direction per column is being measured (p4-inner), and nothing is concluded before that.

## METRIC-HASH-32
- utc: 2026-09-26T18:09:23Z
- prev_sha256: e1625d8bda0a0d84fe25ee5869096f518d2bf211feae09dc42921d32fcfbdda5
- kind: metric-hash
Phase-2 and extended-test null pools restricted to the same material, and the positive-control strip-name fix. Declared before any P4-D phase-2 or extended-test tile, key or read exists.
Defect 1 (integrity):
- p4_phase2.py build and p4_ext.py build drew N0 from every census key in /srv/scorer.
- When P4-B ran, those keys were a1, a2 and b1 only. /srv/scorer now also holds d_a and d_b (P4-D), and e1 and e2 (raw CT, on which readers name nothing).
- Drawing null tiles from raw CT would make the null artificially empty and lower the bar for criterion (c). That is not allowed.
- Fix: both builds take an optional pool-batch list, and N0 is then drawn only from those census batches. Mandatory use:
  - P4-D phase 2 and extended test use d_a,d_b (DECL-P4-4 item 3: "N0 for P4-D is drawn only from P4-D census tiles");
  - any later material uses its own batches.
  - Without the list, behaviour is unchanged (P4-B history).
Defect 2: select built the positive-control pool only from strip 'w028-037'. M2b tiles are named '20260623142658-w028-037' (the METRIC-HASH-26 naming), so the P4-D pool would have been empty. It now also matches the '-w028-037' suffix.
Regression: select on the recorded P4-B sources (census_b1_excl_summary, census_a_excl_summary) reproduces logs/p4/p2_select_1.json exactly: the same candidates and the same 15-tile PC pool.
P4-D M2a/M2b joint scoring (DECL-P4-4 item 3) is recorded here before the final scoring:
- score_p4.py census /work/p4/jobs_census_db.json,/work/p4/jobs_census_da.json with the excl files of both strips;
- N0 pooled: nd_b and nd_a.

```
2254322d86c57632b123e847f208014870177e4259a5bcfbc9c0181fbb76a578  tools/p4/p4_phase2.py
299c736127f0cdb2381d395b29c17a0e0ffbb8b58c9c740b15ba4acf3f2e2701  tools/p4/p4_ext.py
```

## DECL-P4-11
- utc: 2026-09-26T18:10:01Z
- prev_sha256: 0ab56b22737bb1afa93e71d5342524009fb7d1f97aa28287b33d263b30aee134
- kind: declaration
DECL-P4-11: P4-K, boundary candidates for the end title. Declared before the grid's winding direction is known (p4-inner, ordered 18:05Z) and before the M2a labelled-adjacency flags exist. The M2a census counts are known (P4-E1-M2A-CENSUS): all 19 positives lie in columns 0-9 of rows 2-4, none in 10-19.
Rationale (bibliological): an end title normally follows the last text column, near the start of the blank end of the roll. If the blank columns are the inward side (toward the core, the end of the text), the tiles just past the text are the best places for a title that the 1 um carbon-ink model does not show (the organizers' "no detectable ink ... possibly a different ink").
1. Direction, a geometric fact only. From p4-inner's tile_winding_m2a.json, take the per-row Spearman correlation of column vs radius.
   - Inward means increasing column if the median over rows 2-4 of rho is <= -0.5, and decreasing column if it is >= +0.5.
   - Otherwise the direction is undetermined and P4-K does not run.
2. Selection, a fixed rule. For each eligible row r in {2, 3, 4}:
   - let c_last be the most inward positive M2a census column in that row;
   - B-candidates are the first 2 eligible, non-positive, non-labelled-adjacent tiles inward of c_last in that row.
   That gives at most 6 tiles. If the inward side is toward column 0, the rule mirrors.
3. Test: the B-candidates join the M2a phase-2 candidate set with the unchanged bars.
   - DECL-P4-2 item 6 with A3/A4: 3 fresh Opus readers each; >= 2 readers with >= 5 letters; best pair agrees on >= 5; above the phase-2 N0 maximum.
   - N0 from d_a,d_b only (METRIC-HASH-32); PC from the M2b largest cluster.
   - Then the DECL-P4-3 extended test. Only EXT-CONFIRMED counts.
   - The combined set stays capped at 20. Census candidates rank first, then B-candidates in row order.
4. Materials: M2a now. The same boundary tiles on P4-F (DECL-P4-6) and P4-H (DECL-P4-9) are read if and when those materials pass their own gates, under their own batch names and N0.
5. Multiplicity, disclosed: P4-K adds at most 6 tiles per material, each subject to the same phase-2 and extended bars. No bar changes.

## METRIC-HASH-33
- utc: 2026-09-26T18:11:48Z
- prev_sha256: 0e3c9c68bf2f881f4f65d1f930fb4941757083c111b65f85b6ae921dac579ffe
- kind: metric-hash
DECL-P4-11 selector code, hashed before the winding direction (p4-inner) and the excl_d_a flags (p4-excl) exist.
tools/p4/p4k_boundary.py:
- The direction comes from the per-row Spearman rho (ties averaged) of column vs radius; median <= -0.5 or >= +0.5, else undetermined.
- B-candidates are the first 2 non-positive, non-labelled-adjacent census tiles inward of the most inward positive in each row.
- They are appended after the census candidates in the phase-2 select json, with a cap of 20.
Synthetic tests (/dev/shm/p4k_test):
- inward = increasing column gives (r, 9), (r, 10) per row;
- inward = decreasing column with positives reaching column 0 gives none;
- a labelled-adjacent (2, 9) is skipped, giving (2, 10), (2, 11);
- flat radius gives undetermined and no candidates.
The run order after the flags land: score_p4.py census (joint, METRIC-HASH-27), then p4_phase2.py select, then p4k_boundary.py, then p4_phase2.py build <batch> <select> d_a,d_b (METRIC-HASH-32).

```
3e33ffea21896bf31a64e804a9951bb3aa3d2b1c3105b27177f0cd3478bae5a5  tools/p4/p4k_boundary.py
```

## DECL-P4-12
- utc: 2026-09-26T18:13:55Z
- prev_sha256: 4879012cb744dd794bc9bc56ecbd58252ce8f732b3de58e492c7462a2828b7be
- kind: declaration
DECL-P4-12: P4-L, a title-zone raw-CT test on the 2.4 um canvas with a built-in known-text control, plus the labelled-adjacency rule for model-free channels. Declared before any P4-F, P4-H, P4-J or P4-L number exists.
Input: p4-research DOSSIER v2 (origin/claude/gifted-bell-gavnl5-sib-p4-research bea85d04). All of it is numbers-only or published sources, and its inferences are graded UNCERTAIN.
- On the 20260701183124-w010-027 canvas (the strip-a grid, T 8343), c0 is the outer end and c19 the core side (the median radius falls 5.3 -> 1.9 mm).
- The P4-B census pattern suggests text in c0-c9, an intercolumn at c10, a short block in c11-c13 (r0-r1 only), and blank from c14. The expected title zone is therefore c10-c17.
- The labelled segment 20231016151002 coincides with c9-c15 r0-r3.
- Angelotti et al. 2026 (organizers) report that Paris 4 ink is directly visible in the 2.4 um volume as bright surface deposits about 10-20 um thick.
- E2 (DECL-P4-5, a +-53 um slab mean at level 2) gave 0 letters even on known-text columns, so that display is insensitive to this ink.
1. Channel: the DECL-P4-6 item 2 thin-slab maximum (+-15 um around the mesh), matched to a 10-20 um surface deposit.
   - Material: the E2 surface volume (2.4 um), at level 0 or level 1 (4.8 um, still >= 2 voxels across a 10 um deposit). The builder records its choice before computing.
   - Tiles: all 160 eligible strip-a tiles, 1068 px.
   - Thresholds (T_mid, T_hi): from the known-text control 20260701183125-w028-037 2.4 um surface volume if it exists, else from E2 itself (DECL-P4-6 item 2), and frozen before any tile.
2. Built-in positive control (a gate): after the census, at least 30 % of the non-blank tiles in known-text columns c0-c8 must be read as rows Y with >= 5 letters. Otherwise the channel is "uninformative", and nothing in the title zone is interpreted.
3. Labelled-adjacency for model-free channels (P4-L, P4-F, P4-H, P4-J):
   - The prize rule "Ink model outputs of this region should not overlap with any training data used" concerns ink-model outputs. These channels apply no trained model, so the flag is reported but does not exclude candidacy.
   - Model-output materials (M1, M2a, M2b) keep the exclusion.
   - A reading on a labelled (known-text) segment is judged by the organizers' papyrologists as text or title. The project claims no title words.
4. Candidates: positive P4-L tiles in c10-c17 (any row), then all other positive tiles outside c0-c8, capped at 20 and ranked by census letters. Then phase 2 and the extended test, with N0 drawn only from P4-L batches (METRIC-HASH-32) and PC from P4-L tiles of c0-c8 that pass the census bar. Only EXT-CONFIRMED counts.
5. Priority: rows r0-r1 are built first; they hold the short c11-c13 block and lie outside the 1.129 um scan.
6. Builder: new sibling p4-l2 (sub-siblings by row allowed). Harness: rh-e2 (batches l2 / nl2 / census_l2). The orchestrator scores.

## METRIC-HASH-34
- utc: 2026-09-26T18:18:45Z
- prev_sha256: e6fe86b676d9061d6f77c41da0f63ecedf156efb16a6ff9ca76c74cd3983c589
- kind: metric-hash
p4k_boundary.py field-name fix, and the DECL-P4-11 direction input. Recorded before the excl_d_a flags exist and before any B-candidate is selected.
Disclosure: the direction is already known from p4-inner's STATUS (18:17Z). Nothing in the rule changes. The only change is that the loader also accepts p4-inner's radius field name, median_r_mm; without it the loader found 0 tiles. Synthetic regression tests (a-d) give identical results.
Direction input: logs/p4/tile_winding_m2a.json (p4-inner 39254b7; sha256 0f2ad61c27786ed073d72542b81107a8a3a4c60a1bd8c645b124854ff0918557). Spearman of column vs radius per row: r2 -0.988, r3 -0.940, r4 -0.946; median -0.946. By DECL-P4-11 item 1, inward = increasing column.
p4-inner also reports the strip-a grid (tile_winding_a.json): rho -0.898 to -0.995. c0 is about w027 and c19 about w010-011, which agrees with p4-research's geometry.

```
e677513bfc2cf7e98320b849acbfb9c5d8f9064eff23fb232025066ac2250164  tools/p4/p4k_boundary.py
0f2ad61c27786ed073d72542b81107a8a3a4c60a1bd8c645b124854ff0918557  logs/p4/tile_winding_m2a.json
```

## DECL-P4-12-A1
- utc: 2026-09-26T18:24:51Z
- prev_sha256: 3bd289d82c2e0e9b0eb5f7302c02f2303aeace5b4579ff9f44182b08ea8619c8
- kind: declaration
DECL-P4-12-A1 and METRIC-HASH-35: reader size prior for title-zone reads. Declared before any P4-L, P4-F or P4-H read exists.
Input: p4-research DOSSIER section 6 (FIRM for text letters about 3 mm, Mocella 2015; titles about 3-5 mm, up to about 6 mm when calligraphic; confidence 0.6). It recommends widening the readers' size prior from 2-4 mm to 2-6 mm. The frozen task text v2 tells readers "about 107-214 px tall", i.e. 2-4 mm at 53.4 px/mm, which could make them skip larger title letters.
1. Task text sigma2t (configs/briefs/k_d2_task_sigma2t.txt) is identical to v2 except for "about 107-320 px tall (2-6 mm)". The key sheet is unchanged (v2).
2. Scope:
   - sigma2t is used for every census, phase 2 and extended test of P4-L (DECL-P4-12), P4-F (DECL-P4-6) and P4-H (DECL-P4-9) batches, including their N0 tiles, which get the identical brief.
   - P4-D (M2a/M2b) and every earlier batch keep sigma2 through their phase 2 and extended test, consistent with their census.
3. Code:
   - p4_jobs.py has task_variant() and the 'sigma2t' variant for jobs.
   - p4_phase2.py build takes [pool_batches|-] [variant]; its default of sigma2 is unchanged, and rerun reuses its batch's variant.
   - p4_ext.py build takes [pool_batches|-] [variant]; the default is its phase-2 batch's variant.
   - Tests: 22 of 22 P4, phase 2, extended and audit tests pass. The sigma2 paths and hashes are unchanged.
4. Reference briefs for tools/p4/rh_verify.py A5:
   - logs/p4/ref_brief_sigma2.txt, a copy of the census_db brief used so far;
   - logs/p4/ref_brief_sigma2t.txt, the same brief with only the size phrase changed.
5. Validation: the known-text gate of DECL-P4-12 item 2 (c0-c8) and the N0 null apply unchanged. A wider prior that led readers to name texture would appear as N0 letters and fail the bars.

```
7966d6b1a9616cae8ec23530dee8256c175cbd1c87498a778d09ce2050fec8fd  tools/p4/p4_jobs.py
df93f9bffe0df6cfbfdf0b7b836f8a57b877ddeed467a791a15a573d2d9c2431  tools/p4/p4_phase2.py
b58d555ded7bd7f6d5f42affb619d4621511bd2970a779594bbc6ebbc7b5a344  tools/p4/p4_ext.py
f07fbdffab8ee0d62afb946fafc13b6a794ef5ab5e8506bdfbd5ae90c4f8bea0  configs/briefs/k_d2_task_sigma2t.txt
82c7008eda1ff27cc5cfeebb71d0b450d49e6b71856c6bc628e325f6795ffcf4  logs/p4/ref_brief_sigma2.txt
627ebb0fb6dc6d1714cacc27bf35343f95d2e02967def7756872cb0dfe826700  logs/p4/ref_brief_sigma2t.txt
```

## DECL-P4-13
- utc: 2026-09-26T18:25:29Z
- prev_sha256: e4ac1fb4b278c6f91d7af70ab6015653a9c62710758ee467a75c119d9978c941
- kind: declaration
DECL-P4-13: P4-M layout map and P4-N top-edge extension of window A. Geometry and numbers only; declared before any number of either exists. Source: p4-research DOSSIER recommendations 3-4. The organizers state that "the top rows are physically missing".
P4-M, numbers only (new sibling p4-layout):
1. Column profile. On the strip-a canvas (20260701183124-w010-027), for c5-c19 in 1 mm bins along the canvas column axis: the z-summed M1 prediction value, the E2 slab mean and (when p4-l2 has it) the P4-L thin-slab max. These are summed over mesh-valid pixels, with the mesh-valid fraction per bin.
   - Validation: on the known-text columns c0-c9, and on w028-037, the profile must show the column/intercolumn pitch as a spectral peak between 5 and 12 cm (report the peak and its SNR).
   - Outputs: the intercolumn positions and the extent of the c11-c13 block to +-1 mm.
2. Edge check: per row and column, the mesh-valid fraction at z > 160 mm, and the distance from the mesh's top edge to the CT volume's sheet signal above it (a sheet-continuation test: in-plane sheet intensity profile continuity over 0-2 cm above the edge).
3. Organizer-segment mapping: the minimum mesh distance from the organizers' published title-search segments (logs/p4/recon.md lists them; 7.91 um EduceLab ids, mapped through the published transforms where available) to every strip-a tile. This tests whether "no detectable ink" refers to window A.
P4-N, geometry only (sibling tracer, VC3D build): if the P4-M edge check shows sheet continuing above r0 in c9-c15, trace the continuation 1-2 cm upward from the official mesh edge.
- Validation: seam continuity with the official mesh (median point distance at the seam <= 2 voxels), no self-intersection, neighbour-winding distance >= 60 % of the local spacing, and flattening area and angle error per FLAT-2.
- Any render or read of the extension needs its own declaration.

## P4-D-RESULT
- utc: 2026-09-26T18:32:26Z
- prev_sha256: b75aec87a5a4510089d88108952f35c271aadbdce8b90c89352eed6279a210f1
- kind: result
P4-D-RESULT (DECL-P4-4 +A1; DECL-P4-11; METRIC-HASH-27..34). P4-D closes with no title lead; P4-K on M2a yields no boundary candidate.
Labelled-adjacency: p4-excl excl_d_a (9962dcb, logs/p4/excl/excl_d_a_9962dcb.json sha256 26adb6af2f7089a7ff78d8c2ba7c96475c981c0212ec90e9778b9f64ecf1e030) flags all 100 M2a/E1-grid tiles. Every npz min distance to the 8 labelled segments is < 1.2 mm (max 0.793 mm), so the flags are final, although the all-vertex distances are partial. In the core, windings lie about 0.1-0.3 mm apart, so every tile is within 1.2 mm of a labelled neighbour.
Joint census M2a+M2b per DECL-P4-4 item 3 (logs/p4/census_d_joint_excl_summary.json sha256 9b2c82fcb93279c32f5133a2d646c1b7303260af54c0a713484cbd19a811b2d8):
- 16/16 valid; 124 census tiles; 16 N0; p99 3.85; threshold 5;
- rows Y 86; positive 61 (M2a 19, M2b 42); labelled-adjacent 124 of 124; candidates 0.
Phase-2 select (p4_phase2.py, METRIC-HASH-32): 0 candidates, PC pool 9. DECL-P4-11 selector (p4k_boundary.py, METRIC-HASH-34): inward = increasing column (median rho -0.946), 0 B-candidates, because every tile is labelled-adjacent. Records: logs/p4/p2_select_d.json and logs/p4/p2_select_d_p4k.json.
Meaning:
- The official 1 um-model predictions show nameable text in c0-c9 of the inner trace. Under the declared training-overlap rule (1.2 mm), no model-output tile of the core can become a candidate. That is by design: the prize requires "Ink model outputs of this region should not overlap with any training data used".
- Title candidates in the inner windings can therefore come only from model-free channels (DECL-P4-12 item 3): P4-L (thin-slab max, 2.4 um; building), P4-F, P4-H and P4-J.

## DECL-P4-14
- utc: 2026-09-26T18:39:15Z
- prev_sha256: 23501fcac4a786dabfa512d93f6bc910e8585fc83c6bee51d14e05c63da4c440
- kind: declaration
DECL-P4-14: P4-O, cross-scroll ink models on the Paris 4 title strip. Declared before any P4-O inference, tile or read exists. Owner (2026-09-26 ~18:40Z): "dispatch all, we need the title asap".
Rationale:
- The prize forbids "Ink model outputs of this region [that] overlap with any training data used".
- A model whose documented training data contains no PHerc. Paris 4 (Scroll 1) segment or label has no overlap with any Paris 4 region, by construction.
- The known-text columns of the same strip give a built-in validation, and the title zone is the target.
1. Eligible checkpoints: those held by ckpt-screen-a/b/c, plus any official or public checkpoint whose model card, release note or config documents its training segments. A checkpoint qualifies only if that documentation shows no Paris 4 / Scroll 1 data. Undocumented or ambiguous provenance means NOT eligible, and a checkpoint is not guessed eligible. Each builder pushes provenance.json (source URL, sha256, quoted training-data statement) before any inference.
2. Input: the 20260701183124-w010-027 2.4 um surface volume, resampled to each model's native voxel size and slab (e.g. 9.6 um level 2 with the model's layer count), on the strip-a grid (T 8343, c0 = outer). Columns c0-c17, rows r0-r5 first. The display is the raw 0-255 prediction at 1068 px, 0 outside mesh-valid (DECL-P4-4 item 2).
3. Known-text gate per checkpoint: after the census, >= 30 % of the non-blank c0-c8 tiles must be read as rows Y with >= 5 letters. A checkpoint that fails the gate is "uninformative" and its title-zone tiles are not interpreted.
4. Candidates: positive tiles in c10-c17 of checkpoints that pass the gate. Labelled-adjacency does not exclude them, because the checkpoint was not trained on Paris 4; the flag is reported. Then phase 2 and the extended test (DECL-P4-2 item 6 with A3/A4, DECL-P4-3), with N0 only from the same checkpoint's batches (METRIC-HASH-32) and the task text sigma2t (DECL-P4-12-A1). Only EXT-CONFIRMED counts.
5. Multiplicity, disclosed: each checkpoint is a separate material with its own gate and N0. No pooling across checkpoints after the fact.
6. Builders: ckpt-screen-a, -b and -c, one checkpoint family each, with sub-siblings allowed. chain2um supports the input rendering. Harness: a new rh-* sibling per material batch (batch names o<k> / no<k> / census_o<k>).

## DECL-P4-12-A2
- utc: 2026-09-26T18:43:21Z
- prev_sha256: f21a1f703c26f38b2e4489951d446a418e93c7cf6bb0d0366bf94a19e15b9f2b
- kind: declaration
DECL-P4-12-A2: a second P4-L display variant (L2S, per-tile stretch). Declared before any P4-L tile has been read or viewed. Only the builder's numbers are known.
Trigger: builder p4-l2 (STATUS at fa9ff81; thresholds ca715bc1..., frozen before any tile) reports that control per-tile voxel medians rise with row: 57-81 in r0-r1 against 99-108 in r7. The declared global display thresholds (T_mid 93, T_hi 203) therefore render r0-r1 darker, and those are the rows p4-research ranks highest for the title. If deposits there sit on a lower baseline, the global display could push them below T_mid.
1. L2 (declared) is unchanged and is read as declared: batches l2 / nl2 / census_l2, harness rh-e2.
2. L2S is added: the SAME thin-slab max channel of the same tiles, displayed with a per-tile linear 1-99 % stretch over mesh-valid pixels with CT > 0, 0 elsewhere. This is the display rule of DECL-P4-5-A1. Output is 1068 px, same grid. Builder p4-l2 writes it from the stored unstretched max values. Batches l2s / nl2s / census_l2s; harness rh-e1; task text sigma2t.
3. L2S is a separate material: its own known-text gate (DECL-P4-12 item 2), its own N0 (from l2s batches only, METRIC-HASH-32), its own phase 2 and extended test. Candidates are never pooled across L2 and L2S. Multiplicity is disclosed: two displays of one channel.
4. Validation reported for both: the gate numbers on c0-c8 per row band (r0-r1 vs r2-r7), so the row-baseline effect is measured, not assumed.

## P4-O-PROVENANCE
- utc: 2026-09-26T18:45:47Z
- prev_sha256: 77b0a105aedd8f81618442c87087153337d2c608e1faeb62f44d01c952fbf83b
- kind: result
P4-O-PROVENANCE (DECL-P4-14 item 1): checkpoint eligibility, recorded before any P4-O inference.
- ckpt-screen-a (45214156, logs/sib/ckpt-screen-a/p4o/provenance.json): 0 of 3 eligible (ink_9um seed43, hecate_9.6um, ink_3d_dino_guided): Paris 4 exposure or ambiguous provenance.
- ckpt-screen-b (ee5d83e9, logs/sib/ckpt-screen-b/p4o/provenance.json): PHerc.1667-iteration-0..5 are all 6 eligible.
  - Quoted model cards give the training segments 500p2a, 658 (343P) and 20250910185200 / 20250919125754 (9B), i.e. scrolls PHerc0009B, PHerc0343P and PHerc0500P2.
  - The encoder is initialised from Kinetics-700 r3d50 (corroborated from last.ckpt hparams), with no scroll-trained initialisation.
  - paris4_scroll1_in_documentation = false.
  - The weights, card and config sha256 values are recorded.
  - The orchestrator checked iteration-0's entry directly.
- ckpt-screen-c: pending.
Consequence: P4-O proceeds with the 1667 family first (latest eligible iteration, then one early one). Each checkpoint is a separate material with its own known-text gate and N0.

## OWNER-LICENSE-EDUCELAB-1
- utc: 2026-09-26T18:47:02Z
- prev_sha256: ed2f3ce7de622bd9d3d194276607eecb13a3ed0c7d6090f358e9250e5d295ae8
- kind: decision
OWNER-LICENSE-EDUCELAB-1. Owner message in this conversation (2026-09-26 ~18:47Z), verbatim: "I accept the EduceLab Data License for these 5 meshes".
Scope, and nothing beyond it:
- Only the mesh files (meta.json and OBJ or tifxyz; no CT) of the 5 organizer title-search segments listed in p4-layout ASK-1 / logs/p4/recon.md: 20240102231959, 20240110113230 and 20240116164433 (1A); 20240101215220 and 20240109095720 (1B). They are on dl.ash2txt.org (PHercParis4.volpkg/paths).
- The licence terms (https://dl.ash2txt.org/LICENSE.txt) bind the project:
  - no redistribution of the data; the meshes are never pushed to git or any public place;
  - publication limits as stated;
  - EduceLab citation in any publication that uses results from them.
- Use: DECL-P4-13 item 3 only (organizer-segment mapping). Outputs are numbers only (minimum mesh distances per strip-a tile). The mesh files stay in the p4-layout container's local scratch and are deleted after use.
- If the server requires a registration form with personal data or credentials, that step is the owner's own. No sibling or the orchestrator enters any such data.

## P4-O-PROVENANCE-2
- utc: 2026-09-26T18:47:35Z
- prev_sha256: ede221cd4aa08740172b3a60cc444c5f8134051ab5c5f01aba125e605581f86e
- kind: result
P4-O-PROVENANCE-2: addendum to P4-O-PROVENANCE. ckpt-screen-c (542508a7, logs/sib/ckpt-screen-c/p4o/provenance.json) finds 0 of 5 eligible:
- timesformer_scroll5_july_retreat: ambiguous initialisation or pretraining, so NOT eligible;
- timesformer_GP_scroll1: trained on Scroll 1;
- timesformer_large_scroll1_01122024: fine-tuned on Scroll 1;
- resnet50_7.9um_scroll1_frags: pretrained on Paris 4, and its id list includes the Paris 4 segment 20231210121321;
- fiber_ink_4class_selfdistill: self-distilled on the Paris 4 2.4 um volume itself.
Only the PHerc.1667 family (6 iterations) is eligible across all three screens.
Assignment, each iteration a separate material with its own gate and N0:
- ckpt-screen-b runs the latest iteration;
- ckpt-screen-a runs iteration-0 (the cross-segment baseline);
- ckpt-screen-c runs one more iteration, the one with the best documented held-out metric in the family table (excluding those two), chosen from the card before any inference and recorded in its STATUS.md.
Multiplicity: at most 3 cross-scroll materials, disclosed.

## METRIC-HASH-36
- utc: 2026-09-26T21:11:25Z
- prev_sha256: 786bdbce33860d2db533adb4756cd029634f128f613d224f88ae1b1d7963316b
- kind: metric-hash
rh_verify.py update, declared before any P4-L answer is decrypted.
(1) The --adir/--bdir options let the verifier read nested batch layouts (e.g. rh-e2 logs/sib/rh-e2/L2/A/l2a and L2/B/l2a). The defaults are unchanged.
(2) A0 accepts the code versions that were declared when a batch was built, and no others:
- the METRIC-HASH-27 hashes of norm_manifest, p4_jobs, p4_phase2 and p4_ext;
- the METRIC-HASH-32 hashes of p4_phase2 and p4_ext.
Operating rule: fetch the harness branch with full history (git fetch --deepen) before verifying. A shallow fetch makes A1 and B2 fail closed. Observed once: re-verifying E1 and M2a after a depth-1 fetch gave A1 and B2 false. After deepening, all three earlier batches (E2, E1, M2a) pass 12/12 under this version.

```
e82529c2a176f5b841db3af1dc5cb20324f932bce645a9ae4c63904e6906726e  tools/p4/rh_verify.py
```

## P4-CHANNELS-RESULT-1
- utc: 2026-09-26T21:14:11Z
- prev_sha256: 710792bda8d6bd634b495f15d1187c93ab2feb40e6062e50626a0f1beb741e23
- kind: result
P4-CHANNELS-RESULT-1: results of the model-free numeric channels, taken from the siblings' pushed records. The orchestrator viewed no image.
P4-F (DECL-P4-6, -A1, -A2; p4-highz 35bb128, logs/sib/p4-highz/REPORT.md and screen_2p4.json):
- 0 DENSE-HOTSPOT on E1 (60 tiles), on E2 (160, including the title zone c10-c17), and on both known-text controls (64 and 171).
- Injection-recovery detection limits (sensitivity >= 0.8, sigma 1 voxel): Hg/Pb/Au 0.05-0.1 um; CuO 0.5 um; Fe2O3 0.5-1 um; Egyptian blue 2 um. Conservative floors are about 3x (Hg/Pb/Au) and 10x (Cu) higher.
- The bright voxels are compact grains, not surface layers (morph3d). E1 is indistinguishable from the control.
- The 137 keV scan covers only the E2 r3 band, 14-27 % of r3 c10-c17. Only its geometry was computed; no K-edge map.
- Meaning: on the traced surfaces of the w010-027 strips, including window A, no mineral-pigment (red, gold, blue, green, ochre) ink layer at or above these thicknesses is present. Ancient ink layers are typically 5-20 um thick.
- Not covered: untraced sheet, the "physically missing" top rows, and organic dyes.
P4-H (DECL-P4-9; p4-crackle f679ccd9): gate FAIL, pooled AUC 0.584 [0.565, 0.603] < 0.70; rot-90 sanity 0.485. P4-H stops as declared.
P4-I (DECL-P4-8; p4-struct 42d955ea): every material gate fails or cannot be evaluated, so the screen is uninformative, with 0 STRUCT-positive.
P4-L batch l2a (DECL-P4-12, -A1; the global-threshold L2 display; harness rh-e2 30d7332; independent verification 12/12, METRIC-HASH-36, logs/p4/rh_verify_l2a.json d5a1874965e906866da6a0db7c43a016d6ba847b339e6a901725e97021e2dd7c):
- 24 tiles: r0 c0-c19 and r1 c0-c3; 3 sealed reads with sigma2t; N0 counts 0, 0, 0.
- rows Y 0 of 24; 0 letters on any tile, the known-text columns included (logs/p4/census_l2a_provisional.json 65cc2cdcd795d858e37b3aadb4e199562f5ab22ec8d0adcf96d8a849c17987fc).
- This is provisional. The DECL-P4-12 item 2 gate is judged on the full census. It is consistent with p4-l2's row-baseline warning (DECL-P4-12-A2), and the L2S variant is being built.

## METRIC-HASH-37
- utc: 2026-09-26T21:26:37Z
- prev_sha256: a9a5c5cc879d3d1da2d4ec644d2d25d8e860ac9e6002d0d4d274c75ea3a57171
- kind: metric-hash
rh_verify.py remainder-batch check, declared before any l2b answer is decrypted.
The --prior=<batch>[,...] option handles a remainder batch (for example P4-L l2b after the early batch l2a, as the orchestrator ordered at 21:16Z). A4 then requires all of the following:
- the batch's (r, c) set is disjoint from the prior batches' census tiles (their keys installed in /srv/scorer);
- the prior tiles are a subset of the builder's eligible set;
- the batch's tiles together with the prior tiles equal the builder's full eligible set exactly;
- every src sha256 equals the builder's png_sha256.
Without --prior the old A4 applies unchanged. Regression: E2 and l2a still pass 12/12.

```
8b3f0fabd66359a6374894e748b28fb9a7c9615b3f557b0d46fd0d72d4a5e326  tools/p4/rh_verify.py
```

## P4-L2-CENSUS-RESULT
- utc: 2026-09-26T21:27:40Z
- prev_sha256: de7608aafebf8f63057875a1217140151f45c6bb995cf66e65ca8a0dd487cb4f
- kind: result
P4-L2-CENSUS-RESULT (DECL-P4-12, -A1; the global-threshold display L2).
Batches:
- l2a (24 tiles) and l2b (136 tiles) = all 160 strip-a tiles, 20 sealed reads with sigma2t, 20 N0.
- Independent verification: 12/12 each (METRIC-HASH-36/37), records logs/p4/rh_verify_l2a.json and rh_verify_l2b.json.
- l2b passed the remainder check: disjoint from l2a, union == builder eligible set, sha-matched.
Census, with no labelled-adjacency exclusion (DECL-P4-12 item 3): logs/p4/census_l2_summary.json sha256 1459ca61633194a86356b3d6ce021ff5a1e09ccf10670cf2b0a3acf94ac1e019.
- N0 counts: 20 x 0; p99 0; threshold 5.
- rows Y: 1 tile (r2 c19, 0 letters); letters named: 0 on all 160 tiles.
Known-text gate (DECL-P4-12 item 2): 0 of 72 c0-c8 tiles are rows Y with >= 5 letters. FAIL, so L2 is "uninformative" and nothing in the title zone is interpreted.
L2S (DECL-P4-12-A2) is being built and will be read.
Physical interpretation, UNCERTAIN and to be tested (DECL-P4-12-A3): the official mesh runs near the sheet midline. The +-15 um max slab around it may miss recto-surface ink deposits that lie tens of um off the midline, and E2's +-53 um mean dilutes them.

## DECL-P4-12-A3
- utc: 2026-09-26T21:27:40Z
- prev_sha256: 38453a6539370a03b8cc18ffce385dc3d27c6bd7cae83444dbe057ef63d1c178
- kind: declaration
DECL-P4-12-A3: P4-L3, a depth-calibrated thin-slab channel. Declared before any depth-profile number or L3 tile exists.
Hypothesis: the ink deposits the organizers see in the 2.4 um volume (Angelotti et al. 2026: bright surface-associated deposits of 10-20 um) lie at the recto surface, offset from the official mesh (near the sheet midline) by an unknown depth d*. P4-L2 (+-15 um about the mesh) and E2 (+-53 um mean) then miss or dilute them, which is consistent with 0 letters on the known text in both.
1. Calibration, on the CONTROL strip only (20260701183125-w028-037 2.4 um surface volume: known text, not the title strip), numbers only:
   - for each of the 109 surface-volume slices (offset o from the mesh), compute over >= 20 control tiles (fixed seed) the fraction f(o) of in-slice voxels above the frozen T_hi (203, p4-l2 thresholds);
   - compute the same on the control's rot-90 copies (identical by symmetry, a sanity check) and on its gap depths.
   - d* is the offset with the largest f(o) - median_o f(o), provided it lies within +-100 um and its peak exceeds the median by >= 3 robust SD (MAD-based) over offsets. Otherwise there is no ink layer, and P4-L3 stops.
   - Both mesh sides are reported (recto vs verso sign).
   - d* is frozen and pushed before any title-strip computation.
2. L3 channel: per canvas pixel, the max over [d* - 10 um, d* + 10 um] of the 20260701183124-w010-027 2.4 um surface volume, with the per-tile 1-99 % stretch (as L2S) and the same grid, eligibility and 1068 px.
3. Gate, reads and candidates exactly as DECL-P4-12 items 2-4 and -A1 (sigma2t; N0 from l3 batches only; model-free, so no exclusion). The gate is evaluated on w010-027 c0-c8, which were not used in calibration.
4. Multiplicity, disclosed: L2, L2S and L3 are three displays of one volume. Each is its own material with its own gate and N0.
5. Builder: new sibling p4-depth. Harness: rh-e2 (batches l3 / nl3 / census_l3).

## DECL-P4-14-A1
- utc: 2026-09-26T21:30:52Z
- prev_sha256: b69b1ce3a628d244da8024db341c8230d08d5bec2f75b6ad87c4708bf8bc763f
- kind: declaration
DECL-P4-14-A1: P4-O extended to all six eligible PHerc.1667 iterations, with harness assignments. Declared before any P4-O tile exists. Owner (2026-09-26 ~21:30Z, verbatim): "fix every single thing you come across and win and use all siblings available to you".
1. Builders:
   - latest iteration: ckpt-screen-b;
   - iteration-0: ckpt-screen-a;
   - the best documented held-out iteration: ckpt-screen-c;
   - the remaining three iterations: dev-lcsoft, dev-distft and amx, one each, assigned by those three at pick time and recorded in their STATUS.md, never duplicating.
   All follow DECL-P4-14 items 1-2: provenance and sha checked, strip-a grid, c0-c17, r0-r5 first.
2. Harnesses, under the DECL-REMOTE-HARNESS-1 procedure with sigma2t:
   - pairs0814b reads ckpt-screen-a/b/c outputs (batches o1/o2/o3);
   - p4-tiles-a reads dev-lcsoft/dev-distft/amx outputs (batches o4/o5/o6).
3. Every iteration is its own material, with its own known-text gate (c0-c8), its own N0, phase 2 and extended test. There is no pooling.
   Multiplicity is disclosed: up to 6 highly correlated materials of one model family.
   A title candidate counts only if EXT-CONFIRMED in its own material. A candidate confirmed in two or more iterations is reported as such, and the bars are never relaxed.

## DECL-P4-12-A4
- utc: 2026-09-26T21:30:52Z
- prev_sha256: 53638b0412209860f1aff254a00b19de9389accb7e5180b0fa476ad70b0700c7
- kind: declaration
DECL-P4-12-A4: P4-L3 at 1.129 um on the E1/M2a trace. Declared before any number of it exists.
Same method as DECL-P4-12-A3, applied to the higher-resolution scan:
1. Calibration only on the 1.129 um known-text control 20260623142658-w028-037, with the same criterion. d* is frozen before any title-strip number.
2. Tiles: the E1/M2a grid of 20260623141924-w010-027 (60 eligible tiles in rows 2-4; DECL-P4-4-A1 coverage), the max over [d*-10 um, d*+10 um], the per-tile 1-99 % stretch, 1068 px.
3. Gate on the M2a-grid known-text columns c0-c9 (the M2a census positives lie there). Candidates in the columns inward of the text (c10-c19). Model-free, so no exclusion; sigma2t; own N0; phase 2; extended test.
4. Builder p4-tiles-b (E1 builder); harness rh-e1 (batches l3e / nl3e / census_l3e) after L2S.

## OWNER-STANDING-ORDER-1
- utc: 2026-09-26T21:37:18Z
- prev_sha256: b176d76a9863d8c0fc6ee730329ff71f9720bd4591b2e308bc133a8039cb825a
- kind: decision
OWNER-STANDING-ORDER-1. Owner message (2026-09-26 ~21:40Z), verbatim: "create a standing order / rule to fix every single thing you come across without needing me - you know way more than me at this point anyways."
From now on the orchestrator acts without asking the owner. It will:
- fix every defect it finds, in code, data, protocol, records or sibling work;
- dispatch, re-task, pause or cancel siblings and sub-siblings;
- declare amendments and new channels (always declared and hashed before any data they touch);
- verify, score and record results;
- choose priorities for the fastest legitimate prize money. The owner's standing direction (~21:36Z): "use only the ones that'll secure the fastest money - get all the lowest hanging fruit available to us so we can get the rest".
Limits that stay in force, because the owner cannot waive them through the orchestrator, or because the project's integrity rules forbid it:
1. No bar, seal, null or declared rule is lowered or applied after the fact.
2. No safety check or refusal, the orchestrator's or a sibling's, is ever routed around.
3. Owner-only actions stay owner-only: credentials, payments, tax or ID data, accepting new legal terms beyond those already accepted, submitting under the owner's identity, and deleting data beyond what is already approved.
4. Siblings that require the owner's own words in their own session remain the owner's to release.
5. Every claim rests on imaging evidence; no title words from outside the imaging.
The orchestrator reports what it did, not what it proposes to do.

## DECL-P4-6-A3
- utc: 2026-09-26T21:37:18Z
- prev_sha256: cdcd5b2468a220b83165a8780a3aa898dc62b6da80722cc3aca983960ed8f04e
- kind: declaration
DECL-P4-6-A3: correction of scope for P4-F, and a re-run at the calibrated ink depth. Declared before any d* exists (p4-depth and p4-tiles-b calibration pending).
Defect found (orchestrator, under OWNER-STANDING-ORDER-1):
- The P4-F screen and its injection-recovery detection limits (P4-CHANNELS-RESULT-1) cover the slab within +-15 um of the official mesh, with a gap comparison at +-(60-120) um.
- P4-L2-CENSUS-RESULT (0 letters even on known text) suggests the ink layer may lie at an offset from the mesh (DECL-P4-12-A3). A mineral-pigment layer at +-(15-60) um from the mesh was therefore NOT tested.
- The P4-F null is conditional on the ink lying within +-15 um of the mesh. It is re-labelled as such here, and it is not a general exclusion of coloured ink.
Re-run: when p4-depth (2.4 um) or p4-tiles-b (1.129 um) freezes d* with PASS, p4-highz re-runs the unchanged DECL-P4-6 numeric screen and injection-recovery with the slab centred at d* (+-15 um).
- The thresholds, the hotspot rule and the gap comparison (+-(60-120) um measured from d*) are unchanged.
- The re-run covers E2 (all 160 strip-a tiles) and E1 (60), with c10-c17 reported separately.
If calibration STOPs (no ink layer found at any offset), P4-F is re-run at the offsets o = -60 ... +60 um in 15 um steps, with a Bonferroni-corrected hotspot threshold (the tile p99 of the control rescaled to 1 - 0.01/9), so that no depth is left untested.

## OWNER-STANDING-ORDER-2
- utc: 2026-09-26T21:48:41Z
- prev_sha256: 1ef176315f5dac66757a0f7b786079998b18fba5bc31e0e2dc7ba7215d21cb4d
- kind: decision
OWNER-STANDING-ORDER-2. Owner messages (2026-09-26 ~21:45-21:55Z), verbatim excerpts: "consider the title may be in a diff place and in a diff ink. everyone has looked for it and not found it so likely this is a rare case"; "would be useful to have a sibling that's a title expert"; "consider a brilliant way you can capture a purple title as well ... add a standing order to consider absolutely everything - especially things like this, on the fly. you need to think much more critically about this."; "also consider what if the title's fancy like this? like I said- consider everything and have a standing critical thinking order for that. we can't afford to lose" (with a picture of an ornate, decorated initial letter).
From now on:
1. Live hypothesis register logs/p4/HYPOTHESES.md. Every hypothesis about where the title is, what it is written in, or why it has not been seen gets an entry with:
   - its prior, with the source of the prior;
   - the physical mechanism and what CT would show;
   - the declared test, or "no test possible with published scans";
   - a measurable validation (positive control, null, detection limit);
   - its status.
   Owner inputs enter the register as hypotheses and are weighed on evidence, never adopted or dismissed unexamined.
2. After every result, the register is re-ranked. An independent red-team agent reviews the register at every re-rank and looks for missed hypotheses and for failure modes of each test.
3. New hypotheses are generated on the fly, including rare and adversarial ones (location, face, depth, colourant, damage, mesh error, display error, reader failure).
4. Nothing here lowers a bar. Every new channel is declared and hashed before its data exist, carries a positive control and a null, and never uses title words from outside the imaging.
5. Standing critical-thinking rule: coverage matrix logs/p4/COVERAGE.md, with title hypotheses as rows and channels as columns. Before any channel's reads, its blind spots are written down against every axis:
   - location, face (recto or verso) and depth;
   - letter size, sparsity and ornament;
   - colourant;
   - damage or missing surface;
   - mesh or sheet-switch error;
   - display or reader failure.
   Every blind spot must either be covered by some declared channel or be recorded as "uncovered", with the reason.
6. A dedicated title-expert sibling (p4-titulus) maintains the scholarly priors and answers the orchestrator's questions in logs/sib/p4-titulus/QA.md. It never proposes title words.

## DECL-P4-15
- utc: 2026-09-26T21:48:41Z
- prev_sha256: 377b3eea005b92b96a5747c0900dd4755300ce90743eecc6547bc97b0eeee99e
- kind: declaration
DECL-P4-15: title-location expansion beyond the inner end. Declared before any number, tile or map of the regions below exists. Owner (2026-09-26 ~21:45Z): "consider the title may be in a diff place".
Basis (p4-research DOSSIER v4, sections 1.1-1.3; location only):
- About 91 % of Herculaneum end titles stand beside the last column (Cavallo 1983). That is our window A/B, already under census.
- Initial titles are attested (PHerc. 222, 253, 1457, 1583, 1786, 1008). In PHerc. 1457 the title stands about 12 cm before column 1.
- Titles on the verso are attested (PHerc. 339, 1491, 1670).
- The text starts on the outer windings and ends near the core.
[line withheld: prize-candidate detail under review]
(a) P4-M-OUT, an initial title at the beginning of the roll.
[line withheld: prize-candidate detail under review]
- Direction: the outward end of the canvas is fixed by the tie-averaged Spearman of column against per-tile radius (p4k_boundary.direction, sign inverted for outward).
- Census as DECL-P4-2 items 3-4: sigma2t; N0 from this material only; 8+1 sessions.
- Gate: the strip is informative only if >= 20 % of its non-blank tiles are census positives (the body text of the first columns is the internal positive control). Otherwise the result is "uninformative", not a null.
- Candidates, at most 20 in all:
  - every positive tile in a cluster of <= 4 tiles that is separated from every larger cluster by at least one non-positive tile;
  - plus, for each row, the first 2 non-positive tiles outward of the outermost positive (the mirror of DECL-P4-11).
- Candidates then go through phase 2 and the extended test, as DECL-P4-2 item 6 and DECL-P4-3.
- Builder: p4-inner. Harness: rh-e2 (batches mo / nmo / census_mo).
(b) P4-V, a verso-face title in the title zone.
- Once d* is frozen (DECL-P4-12-A3/-A4), the L3 builder also renders the opposite face: the max over [-d* - 10 um, -d* + 10 um].
- These tiles are mirrored left-right, so that writing on the verso reads in its true direction.
- Positive control: mirrored L3 tiles of the known-text columns (c0-c8) must pass the DECL-P4-12 known-text gate. This checks that readers can read mirrored letters.
- Null: the verso face of the known-text columns, where literary rolls are blank. The null rate there is reported.
- A verso candidate must also be checked against the recto of the adjacent outer winding at the same place (mirror-offset ink transfer). A match there voids it.
- Same census, sigma2t, own N0, phase 2 and extended test.
(c) P4-TAG, an attached title tag (sillybos) or wrapper at the outer end: numbers only.
- p4-core measures, at the top and bottom edges of the outermost two windings, any separate thin sheet attached outside the roll body. Measures:
  - sheet-like voxel runs of papyrus density more than 0.5 mm outside the outermost mesh;
  - area;
  - thickness;
  - attachment point.
- It reports geometry only. Any render of a found object needs its own declaration.
(d) Not done: mapping the organizers' 2024-25 title-search segments onto w010-027 stays blocked (p4-layout's session safety check refused the EduceLab meshes). It is not routed around.

## DECL-P4-16
- utc: 2026-09-26T21:48:41Z
- prev_sha256: a00702a7d1d5bab7d33e355edeb9411a275893a218f7384e881ef7e9a2fedfa1
- kind: declaration
DECL-P4-16: title inks that are faint or invisible to absorption CT (purple, organic and lake colourants), and colour-agnostic detection. Declared before any number of these channels exists. Owner (2026-09-26 ~21:55Z): "consider a brilliant way you can capture a purple title as well ... how would we do that if invisible on ct?"
Physics basis (for p4-purple to verify with cited attenuation data, NIST XCOM or equivalent):
- Tyrian purple (6,6'-dibromoindigo) is about 38 % bromine by mass (Z 35), so it is not CT-invisible in principle, if bromine survives carbonisation.
- The ancient purple pigment purpurissum is the dye laked onto chalk (Pliny NH 35.44-45), so the calcium carrier (Z 20) would be denser than carbonised papyrus. Other lakes use an alumina or gypsum carrier (Al, Ca, S).
- Organic dyes without a mineral carrier (orchil or lichen purple, kermes, madder, indigo) are C/H/O/N. Their composition contrast is small.
- Any written stroke is also a physical surface deposit. In the Paganin 2.4 um volume the carbon ink of Paris 4 is visible as bright surface deposits 10-20 um thick (Angelotti et al. 2026), without any composition contrast. So a deposit channel at the calibrated depth (P4-L3) is colour-agnostic.
1. p4-purple: attenuation and phase (delta) contrast at 78 keV and 137 keV, for 5-20 um layers of:
   - Tyrian purple, whole and after loss of Br by 0, 50 and 90 %;
   - purpurissum (dye on CaCO3);
   - alumina and gypsum lakes;
   - orchil, kermes, madder, indigo;
   - orpiment and realgar (As), lead white, verdigris and malachite (Cu), cinnabar, minium, ochres, Egyptian blue, gold;
   - carbon ink, with and without Pb.
   Each is set against carbonised papyrus of density 0.3-1.0 g/cm3. The output is a predicted-detectability table.
2. p4-highz: adds the Br, Ca, Al/S and As classes to the unchanged DECL-P4-6 injection-recovery panel, on the control strip only, and reports their detection limits. The screen itself is re-run only at d*, per DECL-P4-6-A3.
3. Dual-energy feasibility (p4-purple): the 20260323153942 137 keV scan covers the E2 r3 band, including 14-27 % of r3_c10-c17.
   - Registration: 78 keV to 137 keV, with the residual measured on sheet surfaces (goal < 5 um). Only the control region is used for fitting.
   - Model: a two-material fit (Compton against photoelectric) that estimates high-Z content per voxel.
   - Validation, on the control only: known-text ink against blank papyrus, a synthetic injection of each class, and a null on rot-90 copies.
   - No title-zone dual-energy number is computed before the method, its thresholds and its control result are frozen and pushed under a METRIC-HASH.
4. Colour-agnostic morphology (p4-purple design, control first): stroke micro-relief and fibre indentation from pen pressure (surface-height residual about the mesh) and texture (the P4-H crackle features at d*).
   - Each must separate ink from no-ink on labelled known-text regions of the control strip (AUC >= 0.70 with a bootstrap CI excluding 0.60) before any title-zone use.
   - Labels are used only as ground truth on the control, never in the title zone.
5. Limits stated in advance:
   - A pure organic dye with no deposit thickness and no mineral carrier may be undetectable in every published scan. If so, the register records "untestable with published data", never "absent".
   - XRF, hyperspectral imaging or new scans require physical access or new beamtime, which only the organizers can arrange.

## DECL-P4-17
- utc: 2026-09-26T21:48:41Z
- prev_sha256: 5a40da9e820ab1fb6c6583ee1cdbf0e9d5453866b9d8d551368e34da52a1b6a1
- kind: declaration
DECL-P4-17: title-scale, sparse-block and ornament-aware detection in the title zone. Declared before any window, map or number of it exists. Owner (2026-09-26 ~21:58Z): "also consider what if the title's fancy like this?" (a picture of an ornate, decorated initial).
Defect found (orchestrator, OWNER-STANDING-ORDER-2 item 5):
- The census rule (a 2 x 2 cm tile is positive iff rows = Y and letters >= max(5, N0 p99)) is tuned to body text.
- A title is sparse: 2-6 centred lines, perhaps 15-40 letters across a 3-6 cm block.
- A title may be written in larger calligraphic letters ("modulo ampio", attested for specialist title scribes, PHerc. 1497 and 1675).
- A title may be framed by decoration: dashes above and below (PHerc. 172); oblique, curved and elliptical strokes (PHerc. 1027); ornaments between lines (PHerc. 1457); a coronis.
- Split across 2 x 2 cm tiles, such a block can give fewer than 5 recognisable letters per tile. The census can therefore miss it, and nothing before now covered this blind spot.
- Illuminated initials like the owner's picture are medieval codex practice, not a Herculaneum practice. Their consequence for detection (large letters, many non-letter strokes) is covered here all the same.
1. Title-scale windows (reader channel P4-W):
   - 4 x 4 cm windows on a 2 cm stride over window A and B (w010-027 canvas c9-c19, all rows), shown at 1068 px (26.7 px/mm; a 3 mm letter is about 80 px).
   - Materials: the model-free L3 at d* (DECL-P4-12-A3/-A4), and L2S.
   - A new frozen brief variant, "block", asks for:
     - a deliberately written block (Y/N);
     - its number of lines;
     - letters of any size from 2 to 15 mm, and their count;
     - non-letter pen marks (dashes, curves, coronis), and their count.
     The brief text is committed with a METRIC-HASH before any window image exists.
   - Positive control: windows on the known-text columns c0-c8 of the same material must be "block Y" in >= 50 % of cases.
   - Null: the same material's windows rotated 90 degrees. The null gives the block-Y rate and the p99 of the letter and mark counts.
   - A window is positive iff it is block Y and (letters + marks) >= max(5, null p99 of letters + marks).
   - Candidates, phase 2 (3 readers, "block" variant) and the extended test are as DECL-P4-2/-3 with this variant.
2. A reader-free block detector (numbers only, no image; builder p4-l2):
   - At d*, cut the thin-slab max into 5 x 5 mm cells. For each cell, compute the fraction of pixels above the deposit threshold T_d.
   - T_d is frozen on the control strip: known-text column cells (c0-c8) against the blank intercolumn cells on w028-037 (c11, c15, c19).
   - Validation on held-out control cells, before any title-zone number: text-cell recall >= 0.90 at an intercolumn false-positive rate <= 0.05.
   - Title zone (c9-c19): a flagged cell is one above the intercolumn p99. A block candidate is a 4-connected cluster of >= 4 flagged cells. The cluster locations are recorded, and a P4-W window is centred on each (no extra reads beyond the declared grid).
3. The size prior of the existing sigma2t brief is unchanged for the channels already declared with it. The "block" variant is a new material-level channel, with its own gate and null; it is not a rescoring of old reads.

## CORR-TIMES-1
- utc: 2026-09-26T21:49:24Z
- prev_sha256: c83c355b50b2963ca07701120434ac51b520cd29af7fc7e09db509ecb345ba33
- kind: correction
CORR-TIMES-1: correction of stated times in OWNER-STANDING-ORDER-2, DECL-P4-16 and DECL-P4-17.
- Those entries give the owner messages' times as "~21:45-21:55Z", "~21:55Z" and "~21:58Z". These were estimates, written before the clock was checked.
- All four quoted owner messages were received before the entries were appended at 2026-09-26T21:48:41Z.
- Every such time therefore reads "received on or before 21:48:41Z".
- No content, rule or ordering is affected. Each declaration still precedes all data of its channels.

## METRIC-HASH-38
- utc: 2026-09-26T22:01:51Z
- prev_sha256: b580c8bb252a8c94646dc39d3cd0f65eb3f557bc157ae7122df6ab09162eb97b
- kind: metric-hash
METRIC-HASH-38: code and brief for DECL-P4-17 (the title-scale "block" variant), plus two fixes found on the way (OWNER-STANDING-ORDER-1). Recorded before any P4-W window image, block read or block score exists. Test suite: 608 passed, 6 skipped (pytest, 2026-09-26 ~21:59Z; new tests/test_p4_block.py, 7 tests).
```
2995f22f2c5fd5af39a1ce93fb7a3b78f240825e0c8294c06dd8c495e66ac1c5  configs/briefs/k_d2_task_block.txt
055e70e176e92de47b8cd18f0a909a977cf1ec950e95484f9ee062bfb575248d  configs/reader_output_block.schema.json
b84b0308bc00f5b0355364ebbaa9aa578cf7c73f8e1ff23640ab883eed747f77  tools/p4/block_schema.py
e9f99ce4247e45211b8a6701f42a7ec4e38c9f458b9c23d191bc60cfdf04e45f  tools/p4/p4_jobs.py
999cb5534943fdd70b78a35cc0f61957ddc6e5411b9c10b507f0ffa415a94e05  tools/p4/p4_phase2.py
843a2664913a4a94e95b21635212e1f6d7a4a18d526df4ba10c321ddfed8a8c8  tools/p4/p4_ext.py
9a5b4761a22f6a792eadb38928f8d7adfb217e885fa4ff2655c0bc1b5eb1e24d  tools/p4/score_p4.py
c6a948e6a87d50212a6897e56f4dfbd6ca3d91d8caf0f5e02cfbefc26289df29  tools/p4/rh_verify.py
075f5dea5e5b828605a6862c02ac9d63fea1951cc761a3433531b04504764c41  logs/p4/ref_brief_block.txt
a8cb86c1fdd16f9e71298ae6f1364397a3f9733ad199235b26a0f59ea8eecfc1  tests/test_p4_block.py
```
What changed:
1. The "block" brief, at 26.7 px/mm (4 x 4 cm at 1068 px), with letters 2-15 mm. It asks for:
   - "rows" (deliberate writing, Y/N);
   - "lines";
   - letters;
   - "marks": non-letter pen marks, each of kind dash, curve, flourish, endmark or other.
   The key sheet is unchanged (keysheet_sigma2.png). The brief does not say "title".
2. Schema: the pinned configs/reader_output.schema.json (Day-0 hash 8b28fc43...) is NOT changed. The block variant uses its own copy with the optional "lines" and "marks" fields (reader_output_block.schema.json), selected only for jobs files whose variant is "block" (tools/p4/block_schema.py). Every other variant still validates against the pinned schema.
3. score_p4 census:
   - for block jobs, count = n_letters + n_marks, used for the N0 p99, the threshold (max(5, p99)) and the ranking;
   - mixed variants in one call are refused;
   - new option --cand-cmin=N: tiles or windows with c < N never become candidates (DECL-P4-17 control windows c0-c7). Window keys use r, c = the top-left strip-a tile of the window.
   - The letters-only behaviour is unchanged for all other variants (tested).
4. p4_phase2 and p4_ext cmd_score validate by the jobs file's variant. The phase-2 and extended-test statistics stay letter-based, unchanged.
5. Fix: p4_ext cmd_build wrote "variant": "sigma2" into its jobs file whatever variant it used. It now writes the variant actually used.
   - Impact: the only extended-test batch so far (ext1) was sigma2, so nothing is affected.
   - A later re-run of a sigma2t extended-test batch would have used the wrong task text.
6. rh_verify's DECLARED set adds the versions current when in-flight harness batches were built: METRIC-HASH-35 p4_jobs, p4_phase2 and p4_ext, and score_p4 581bc41e... Without this, those batches would fail A0 after this change (found by re-verifying l2sa: A0 false before the addition, 12/12 after; f1 12/12).

## OWNER-STANDING-ORDER-3
- utc: 2026-09-26T22:01:51Z
- prev_sha256: 06ded76ff01f9a0f4a1392410b979630b15fd50c59e3b5b01b8b0153fdcee09f
- kind: decision
OWNER-STANDING-ORDER-3: interruptions, usage limits and compute economy. Owner message (received before 2026-09-26T22:02Z), verbatim excerpts:
- "I've messaged you multiple times in rapid succession - which likely has thwarted your thinking process for previous messages, and has killed previous tasks which was not intended whatsoever. so go back and see what I said again. and have a standing order as well that new messages won't interrupt your current thinking or kill processes unintendedly."
- "your siblings expert mode being set to 'Extra' is certainly costing us. The orchestrator (you) should stay at 'Ultracode' effort here in the task, and the others at 'Low'".
- "we need a standing order as well that if we hit a 5-hr limit it won't kill the tasks but maybe just pause them instead".
1. Interruptions.
   - Every owner message that arrives mid-work goes into logs/owner/INBOX.md: the UTC time, a verbatim excerpt, and each request as a numbered item with a status.
   - No message cancels in-flight work, running processes, siblings or readers unless it explicitly says to stop that item.
   - The orchestrator finishes its current atomic step (a verification, a RULES append, a commit and push) before it turns to a message.
   - After any burst of messages it re-reads the whole burst and closes every item.
   - Long work never runs in the foreground of the orchestrator's turn. It runs detached (background process or sibling) and resumable.
2. Usage limits. The platform stops turns at a usage limit, and no tool here can change that. This order turns a stop into a pause:
   - Every sibling keeps logs/sib/<name>/RESUME.md, updated at every milestone. It holds the last completed step, the exact next command, and any detached processes with their outputs.
   - Long computations are resumable: completed items are skipped, outputs are append-only, and checkpoints come at least every 15 minutes. Long jobs run detached (nohup), so they continue while a turn is stopped, until the container is reclaimed.
   - After a reset, the orchestrator's scheduled check-in sends each stopped sibling one message: resume from RESUME.md. Nothing restarts from scratch.
   - Blind readers killed by a limit: only jobs without a valid sealed answer are re-run, and each is recorded as a re-run. Completed sealed answers are never discarded.
3. Effort and compute economy.
   - The effort level of a session cannot be set with the orchestrator's tools (create_session has no effort field). The owner sets it per session in the app. The owner's direction is recorded: siblings Low, orchestrator Ultracode.
   - Every sibling runs in economy mode by instruction (added to logs/sib/orders/COMMON.txt):
     - no re-reading of large files; use targeted grep and sed;
     - scripts instead of long manual loops;
     - no polling more often than every 10 minutes;
     - terse STATUS files, and a final report of <= 30 lines;
     - stop when the task is done.
   - The orchestrator dispatches only siblings on the critical path to a prize, does not wake idle siblings without a task, and runs the prompt-regeneration workflow at most once per 24 hours (STANDING-ORDER-COMPACT-A1).
4. Nothing in this order lowers any bar or rule.

## STANDING-ORDER-COMPACT-A1
- utc: 2026-09-26T22:01:51Z
- prev_sha256: da065e386db3c1f3f989dce03e013a84c541285dab9fece92f3d0205b4d674f3
- kind: decision
STANDING-ORDER-COMPACT-A1 (under OWNER-STANDING-ORDER-3 item 3, compute economy): the prompt-regeneration workflow of STANDING-ORDER-COMPACT runs at most once per 24 hours. After a condensation, if configs/prompt/ already holds a verified master prompt built less than 24 hours earlier, steps 1, 2, 4 and 5 still apply, and step 3 (launch the workflow) is skipped and logged in CHANGELOG. The run launched at 2026-09-26T21:41Z (v8, wf_51032efb-a08) continues. No integrity rule of the prompt changes.

## OWNER-STANDING-ORDER-4
- utc: 2026-09-27T00:55:14Z
- prev_sha256: f2e097633087bb7d8f3217698f7e3e7a4f95eaaf0954013ce566e33cfbb16e97
- kind: decision
OWNER-STANDING-ORDER-4. Owner message (2026-09-27, received before 00:52Z), verbatim excerpts:
- "let's not use hashing. We need our team to be able to verify chain of thought and actions independently after submission."
- "You auto-submitting when we have a win prepared is enough protection for me. FYI, just know that I agree to the submission terms and conditions ahead of time on the different google forms for each submission."
- "Also, nothing should ever be 'waiting on me'."
- "need a standing order to always overcome main blockers that come up, as they come up ... I don't want to have to tell you to make it a task to overcome them with your most brilliant solution - that should be second nature to you."
1. Blockers: every main blocker is attacked as soon as it appears, with the best legitimate solution, without being asked.
   - Reports list each blocker together with the action already taken.
   - The limits of OWNER-STANDING-ORDER-1 still hold: no bar lowered, and no safety check or refusal routed around. A blocker of that kind is solved by a different legitimate route, or recorded as not solvable.
2. Nothing waits on the owner. Siblings whose only open item is an owner reply are either given the orchestrator's ruling or retired, with the reason recorded. No work is parked for an owner answer.
3. Auto-submission, authorised by the owner. When a prize entry passes the submission gate (SG 0-14 and the prize's own requirements), the orchestrator submits it without asking. The owner accepts each submission form's terms in advance. This replaces, for prize submissions only, the "submitting under the owner's identity" and "accepting new legal terms" limits of OWNER-STANDING-ORDER-1 item 3.
   - Only the owner details the form requires are used.
   - The orchestrator cannot sign in to the owner's personal accounts. If a form requires such a sign-in, the entry is prepared completely and that single step is reported at once.
4. The "no hashing" direction. The goal is adopted in full: independent verification after submission. The literal instruction is declined, for this reason:
   - The sha256 fingerprints are the means by which anyone can verify, independently, that code, briefs and data were fixed before any result existed. Every fingerprinted file is committed in plain text beside its hash.
   - Removing the fingerprints would remove that verification, and would break the declared METRIC-HASH rule (a bar whose metric code hash does not match is VOID).
   Added now, for the owner's goal:
   (a) VERIFY.md at the repo root: how to re-check every recorded hash with one command, and how to re-score every closed channel.
   (b) Unsealing after the verdict. When a channel's final verdict is recorded (after phase 2 and the extended test, if any), its decrypted reader answers are committed in plain text under logs/p4/unsealed/<batch>/, next to the transcripts and scorer outputs, so that every score can be recomputed without any key. This is allowed only while the repository is private (it is private: checked 00:5xZ, 2026-09-27). If it becomes public, the answers go only into the submission package, because of the prize embargo.
   (c) At submission, the package carries the full chain: RULES.md, CHANGELOG, INBOX, the declarations, the unsealed reads, the transcripts, and the session transcripts (tool calls and messages).
5. Effort levels: the owner reports that the siblings now run at Low. That setting was changed in the app. The orchestrator's economy-mode instructions (OWNER-STANDING-ORDER-3) stay in force.

## STANDING-ORDER-COMPACT-A2
- utc: 2026-09-27T00:55:14Z
- prev_sha256: 5556161195ef04cfa4caa7f0523890a286a96135a777d05d21a6844a94252c42
- kind: decision
STANDING-ORDER-COMPACT-A2 (under OWNER-STANDING-ORDER-3/-4). The multi-agent prompt-regeneration workflow is retired.
Why:
- Its v8 run (wf_51032efb-a08, launched 21:41Z) used 1,454,186 subagent tokens across 24 agents.
- Only 3 agents completed. It was killed by the usage limit, and it contributed to hitting that limit.
Replacement, after every condensation or restart:
1. Read RESUME_NOW.md, which is kept current at every milestone and is the live handover, then the newest configs/prompt/hercules_master_v*.md, then the RULES.md tail.
2. Check the live jobs and restart what stopped.
3. Continue the in-flight steps.
The orchestrator refreshes the master prompt itself, in a single pass, at most once per 24 hours. It must keep every integrity rule (I1-I17; sections 3.3, 3.4, 3.6, 10; the messaging format) verbatim, and check them with a scripted diff against the previous prompt before adopting it.
tools/prompt/on_compact.sh is updated to inject this order.

## P4-L3E-CALIB-RESULT
- utc: 2026-09-27T00:55:14Z
- prev_sha256: a2ebf1d272dc5e82b7bf4fefdd18f09477c56e338d1e5fdb8ce2f560ffdb575e
- kind: result
P4-L3E-CALIB-RESULT (DECL-P4-12-A4 item 1). p4-tiles-b's calibration on the 1.129 um known-text control 20260623142658-w028-037, frozen before any title-strip number (logs/sib/p4-tiles-b/l3e/calib_1129.json on sib-p4-tiles-b, utc 2026-09-26T21:45:38Z).
- Verdict: STOP. The peak excess of f(o) over its median is 1.122 robust SD, below the bar of 3.
- Setup: T_hi 233 (p99.9, p4-highz thresholds.json, frozen 17:50:05Z); 826 chunks; rot-90 sanity check identical.
- Per-tile peak offsets: median -6.8 um, p10 -114.7 um, p90 +102.5 um. There is no consistent depth.
- Gap-depth median f: 0.00091 beyond 100 um, against 0.00114 within 100 um.
Consequences, all as declared:
- L3 at 1.129 um (DECL-P4-12-A4) stops. No l3e tiles or reads.
- DECL-P4-6-A3 STOP branch: p4-highz re-runs the P4-F screen on E1 at the offsets -60 to +60 um in 15 um steps, with the Bonferroni-corrected threshold. Dispatched 00:53Z.
- The 2.4 um calibration (p4-depth, DECL-P4-12-A3) is independent and still pending.
Interpretation (UNCERTAIN): at 1.129 um this voxel-fraction criterion finds no ink layer at any offset on known text. Either the ink at this resolution is not the brightest-voxel population, or it lies at a depth that varies with the mesh-to-surface offset (the per-tile peaks spread over +-100 um). The latter is what p4-core's mesh audit (surface-agreement offsets) measures. This is not evidence about the title.

## DECL-P4-14-A2
- utc: 2026-09-27T00:55:14Z
- prev_sha256: 2245178fe33f8cf32fcbf5a794d475073071cb189be2325582490b08e938cb07
- kind: declaration
DECL-P4-14-A2: P4-O rulings, so that nothing waits and the fastest route to the title zone is taken. Declared before any P4-O tile has been read. Rulings made under OWNER-STANDING-ORDER-1/-4, from facts that do not depend on results.
Measured cost (ckpt-screen-c smoke test): 4.05 s per 256 x 256 window at 4 threads fp32, about 4.9 CPU-h per 2 x 2 cm tile, and about 530 CPU-h for c0-c17 x r0-r5 per iteration. A full grid per iteration is therefore days of wall time.
1. Tile order, for every P4-O builder:
   (i) r0-r1 x c9-c14 (the window-A top rows, including the c11-c13 block) together with r0-r1 x c5-c8 (known-text gate tiles);
   (ii) r2-r5 x c9-c14 together with r2-r5 x c5-c8;
   (iii) c15-c17, all rows;
   (iv) the rest.
   Each builder pushes a partial manifest after stage (i) (20 tiles). The harness reads each stage as its own batch, with N0 drawn from the same material only, and the gate evaluated on that stage's c5-c8 tiles.
2. Precision: bf16 autocast (AMX) is permitted only if an equivalence check on ONE known-text gate tile (r0 c5), done before any title-zone tile, shows at most 1 % of pixels differing from fp32 by more than 2/255. Otherwise fp32. The check is recorded in each builder's STATUS.md.
3. Iterations, ruled by a rule that does not depend on results (ckpt-screen-c option 2):
   - ckpt-screen-c takes iteration 4, the largest label set short of the final one, which ckpt-screen-b has.
   - amx takes the remaining iteration not held by dev-lcsoft or dev-distft (DECL-P4-14-A1 item 1), recorded in its STATUS.md before inference.
   - Depth order and normalisation follow ckpt-screen-b's recorded convention for this volume, and clip(0,200)/255 (the card's training convention).
4. Iteration 0 (ckpt-screen-a) is dropped. That session's own permission layer blocked the inference, and it is not routed around or reassigned. Batch o1 will not exist.
5. p4-tiles-a is released from the o4-o6 harness role, because its builder brief forbids launching readers. A dedicated rh-* harness sibling (rh-o) will be created when the first o4-o6 stage-(i) manifest lands. o2 and o3 stay with pairs0814b.

## DECL-PP-1
- utc: 2026-09-27T00:56:48Z
- prev_sha256: 1e827c5a9f29d70c9b4810875d3d7e75922fca4f8fa6dc5752823a5c1f68caa2
- kind: decision
DECL-PP-1: monthly Progress Prize submissions for the 2026-09-30 round (deadline 11:59 pm Pacific = 2026-10-01T06:59Z). This is the fastest money, per p4-research PRIZES.md v2 (sib-p4-research; the owner direction of 2026-09-26 ~21:36Z: "use only the ones that'll secure the fastest money"). It is submitted under OWNER-STANDING-ORDER-4 item 3 (auto-submission authorised; terms pre-accepted by the owner).
1. Submissions: three separate, standalone, MIT-licensed tools, each packaged by the sibling that built it.
   - flatcheck: a tifxyz flattening-quality checker, plus the documented ABF++ collapse failure mode and SLIM/ARAP alternatives. Packager: flat1.
   - tifxyz-dist: exact point-to-surface distance with certified bounds, and a train/prediction clearance check. Packager: p4-excl.
   - handcheck: a mirror/handedness predictor for tifxyz renders, with the PHerc1447 flags reported as flags. Packager: handed.
2. Content rules, for every package:
   - no Paris 4 title-search data or numbers (no w010-027 or w028-037 flags, tiles or maps);
   - no sealed material, keys, scorer paths, RULES or governance coupling;
   - no personal information about the owner beyond the licence holder name the form requires;
   - demos on public, non-title data only;
   - tests included and passing;
   - README: what it does, how it was validated (numbers), known limits.
3. Each package passes a scrub before any publication: a secrets and keys scan, a path scan (/srv, /work, scratchpad), a check for no Paris 4 search identifiers, and the licence present. The scrub result is committed.
4. Submission: p4-research inspects the official Submission Form (fields; whether sign-in is required) and drafts each form answer from the package README.
   - The orchestrator submits each entry once its scrub has passed.
   - The tool repositories are published (public, permissive licence) when the form requires it, or at award, as the prize page requires ("to accept the prize").
   - A step that needs the owner's personal account sign-in is reported at once, with everything else complete.
5. Target: every package ready by 2026-09-29T12:00Z, a day of margin before the deadline.

## DECL-PP-1-A1
- utc: 2026-09-27T01:05:14Z
- prev_sha256: 37bd1bf4765f5093df8f4c70299fc01f67d692b5195f7301cc2fbcdbae6cbec4
- kind: decision
DECL-PP-1-A1: the form submission step. At 2026-09-27 ~01:05Z the orchestrator's own safety check (the auto-mode classifier, category "Real-World Transactions") refused the step that would have submitted the Progress Prize Google Form automatically: a tool that POSTs the entry to formResponse. Nothing was written or sent.
Per OWNER-STANDING-ORDER-1 item 2 and -4 item 1, this is not routed around. No other tool, script, agent or sibling will submit the form.
From now on:
1. The orchestrator prepares each entry completely in logs/pp/SUBMIT_SHEET.md:
   - the form link (the September 2026 Progress Prizes form, https://docs.google.com/forms/d/e/1FAIpQLScNBMj25FMnphngRG1Ciryv_2_Mkdq2YPJOD9WqPfZExII2iQ/viewform; not the Grand Prize, First Letters or Title forms);
   - every field's answer ready to paste, except the owner's own name and email;
   - the public repository URL and the contribution text answering the form's four questions.
2. The owner submits the three entries by hand (about one minute each), or adds a permission rule to the settings that allows the orchestrator to submit. The owner is told this once and plainly.
3. Everything before the form (packaging, scrub, publication to the owner-connected public repositories) continues without waiting.
The pp-* siblings and p4-research never submit forms. That was already in their orders, and it is restated to p4-research.

## P4-W-DETECTOR-L2S-RESULT
- utc: 2026-09-27T01:14:02Z
- prev_sha256: 44c2952656c9bb0d99be2d05ebcb7cfb5bbe5aaea0c9b217a024fd5719c083ac
- kind: result
P4-W-DETECTOR-L2S-RESULT (DECL-P4-17 item 2), from p4-l2's BLOCK_FREEZE at the L2S depth on the control strip 20260701183125-w028-037 (sib-p4-l2 commit 905d4db). The validation was set before any title-zone cell existed.
- T_d = 161.
- Held-out text-cell recall 0.089 at an intercolumn false-positive rate of 0.032. The bar is recall >= 0.90 at FPR <= 0.05, so this is a FAIL.
- As declared, no title-zone (c9-c19) cell was computed.
Consequence: the reader-free block detector is not usable at the L2S depth (+-15 um about the mesh). It will be re-validated only at a frozen d* (DECL-P4-12-A3).
This fits P4-L2-CENSUS-RESULT and P4-L3E-CALIB-RESULT: in the thin slab about the official mesh, known text is not separable from intercolumn papyrus by bright-voxel fraction. That again points to the ink lying away from the mesh surface, or not being the brightest-voxel population. p4-core's surface-offset audit and p4-depth's 2.4 um calibration test this.

## DECL-PP-1-A2
- utc: 2026-09-27T01:26:49Z
- prev_sha256: f513235f56932878e1a0e50a7386927273f149feea82bb779686c79e9f4cbc71
- kind: decision
DECL-PP-1-A2: the owner granted the permission. Owner (2026-09-27 ~01:25Z), verbatim: "All permissions were granted. Check the progress prize submission siblings, all progress and submit the forms individually for all three, in excellence. keep as background task until they are ready if they aren't already. secure wins".
This clears the condition in DECL-PP-1-A1 item 2: the owner "adds a permission rule ... that allows the orchestrator to submit".
From now on:
1. The orchestrator submits each entry itself with tools/pp/submit_progress_form.py <tool> --send. It uses the September 2026 Progress Prizes form (live field ids checked on every call); the URL and contribution text come from logs/pp/SUBMIT_SHEET.md; the entrant's details come from a local file that is never committed.
2. The tool refuses to send unless the sheet marks the entry READY. READY requires all of:
   (a) the public repository is pushed and its main branch is re-cloned by the orchestrator;
   (b) the tests pass in a clean environment, run by the orchestrator;
   (c) the scrub is clean;
   (d) the README meets logs/pp/CITATION_RULES.md (the verbatim dataset citation, licences, credits);
   (e) every number in the contribution text is supported by the README or tests.
3. Every submission is logged, without personal data, in logs/pp/submissions.jsonl.
4. If the orchestrator's safety check refuses the send, it is not routed around: the owner pastes from the sheet.
Dry runs at ~01:27Z: the live form title and all six field ids match for all three tools. Nothing was sent.

## DECL-PP-1-A3
- utc: 2026-09-27T01:33:36Z
- prev_sha256: 4b57738beeb42c5af8e8ad367494d2302d7ed32593a2aaea24710c89622a1e9b
- kind: decision
DECL-PP-1-A3: the form requires Google sign-in.
- At 2026-09-27T01:33Z the orchestrator sent the READY flatcheck entry to the September 2026 Progress Prizes form (tools/pp/submit_progress_form.py --send). The formResponse endpoint answered HTTP 401 Unauthorized.
- The agent proxy status was normal, and a proxy block would return 403/405/407, so the 401 came from Google. The form accepts responses only from a signed-in Google account; the viewform page loads without sign-in.
- The entry was NOT accepted. It was not retried and not worked around; the orchestrator cannot sign in to the owner's account.
- Logged in logs/pp/submissions.jsonl (confirmed false).
From now on the owner submits each READY entry by hand from logs/pp/SUBMIT_SHEET.md. The orchestrator keeps the sheet exact and marks each entry READY after its verification (DECL-PP-1-A2 item 2).

## P4-L3-CALIB-RESULT
- utc: 2026-09-27T01:45:44Z
- prev_sha256: 37e44f87f73d434c7c28b57010cc8688c10771259413b28d1f8513619c16cb82
- kind: result
P4-L3-CALIB-RESULT (DECL-P4-12-A3 item 1). p4-depth's calibration on the 2.4 um CONTROL strip 20260701183125-w028-037 (sib-p4-depth 5e32424, computed 2026-09-27T00:55:41Z). Its parameters were frozen at faccba7 before any depth number existed.
- Verdict: STOP. The largest excess of f(o) over its median lies at o = -31.2 um (the "minus" side, slice 41). Its robust z is 1.94, below the bar of 3 (T_hi 203).
- On the plus side the best offset is +129.6 um, at z 0.14.
- The rot-90 check passed.
Consequences, as declared:
- L3 at 2.4 um stops.
- P4-V (the verso at -d*) and the P4-W windows at L3 do not happen, because there is no d*.
- DECL-P4-6-A3 STOP branch: p4-highz queues the E2 P4-F offset sweep (-60 to +60 um, Bonferroni).
- p4-depth also reported (ASK item 2) that the declared peak rule passes 25/100 synthetic no-layer sheets, so its PASS branch would have lacked specificity. The rule was not changed; this is disclosed.
Synthesis with P4-L2-CENSUS-RESULT, P4-L3E-CALIB-RESULT and P4-W-DETECTOR-L2S-RESULT (UNCERTAIN):
- At both resolutions, on known text, bright-voxel fractions show no ink layer at any CONSTANT offset from the official mesh.
- The most likely reason is that the local recto surface wanders relative to the mesh. The per-tile peak offsets at 1.129 um spread from -115 to +103 um (p10 to p90). A constant-offset slab therefore averages ink with papyrus interior or with air.
- This motivates the surface-following channel DECL-P4-18.

## DECL-P4-18
- utc: 2026-09-27T01:45:44Z
- prev_sha256: 58a3fa222e2ded949d2170370671961852467b2d0586ab13e38b0f2ec5a858e7
- kind: declaration
DECL-P4-18: P4-L4, a surface-following thin slab (overcoming the blocker in P4-L3-CALIB-RESULT, under OWNER-STANDING-ORDER-4 item 1). Declared before any number of it exists.
Idea: follow the actual papyrus surface pixel by pixel, instead of a constant offset from the official mesh, and take the brightest voxels in a thin layer just outside it. That is where the 10-20 um ink deposits sit (Angelotti et al. 2026).
1. Surface detection, per canvas pixel, along the 109-slice axis (2.4 um volume 20260411134726; +-129.6 um):
   - smooth the profile (Gaussian, sigma = 1 slice);
   - the sheet is the connected run of slices above T_mid (93, the frozen p4-l2 value) that contains or is nearest to slice 54 (the mesh);
   - its two faces are the outermost slices of that run on each side: s_minus and s_plus.
   A pixel with no run within +-60 um of the mesh is invalid.
2. Values:
   - L4- = the max over [s_minus - 20 um, s_minus + 5 um];
   - L4+ = the max over [s_plus - 5 um, s_plus + 20 um].
   Each face is its own channel. The recto is not assumed; both faces are tested.
   L4 tiles use the per-tile 1-99 % stretch, the strip-a grid, and 1068 px, as L2S.
3. Numbers-only pre-gate, run before any read, on the CONTROL strip w028-037 only:
   - the DECL-P4-17 reader-free detector (5 x 5 mm cells; T_d frozen on held-out halves; recall >= 0.90 at intercolumn FPR <= 0.05);
   - specificity (the lesson of p4-depth's ASK item 2): the same frozen detector, applied to rot-90 copies and to 100 synthetic no-ink sheets with matched noise, must flag <= 5 % of cells.
   A face that fails the pre-gate is not read: no tiles for it are shown to readers.
4. If a face passes, reads follow DECL-P4-12 items 2-4:
   - the known-text gate on w010-027 c0-c8 (>= 30 % of non-blank tiles rows Y with >= 5 letters);
   - sigma2t, with N0 from this material only;
   - candidates c10-c17; phase 2; the extended test;
   - the DECL-P4-17 block windows at L4.
   Model-free: no training overlap.
5. Also recorded:
   - the per-pixel face-offset maps (s_minus and s_plus relative to the mesh), as numbers only, and their agreement with p4-core's mesh audit;
   - the fraction of valid pixels per tile.
   A face-offset spread larger than +-60 um in the title zone is itself a finding (mesh far from the sheet) and goes to the register (L10).
6. Builder: p4-l2 (it has the raw store and the P4-17 tools), with p4-core's surface-agreement code shared. Harness: rh-e2 (batches l4m / l4p). Multiplicity disclosed: L4- and L4+ are two more displays of one volume.

## P4-L2S-MOUT-CENSUS-RESULT
- utc: 2026-09-27T02:02:20Z
- prev_sha256: d135699b9d3933e61d3c40f657a5d4a68e375bd291fdd2ee11def1c89665445a
- kind: result
P4-L2S-CENSUS-RESULT and P4-MOUT-CENSUS-RESULT. Both batches were independently verified 12/12 (logs/p4/rh_verify_l2sb.json, with --prior=l2sa; logs/p4/rh_verify_mo.json), installed and scored model-free with no exclusion. Counts only.
1. L2S (DECL-P4-12-A2; the per-tile stretched thin slab, +-15 um about the mesh; 160 tiles; 21 sessions, 21 valid; N0 21, all 0 letters):
   - rows Y in 3 of 160 tiles; 0 letters in every census tile;
   - known-text gate (c0-c8): 0 of 72 tiles have rows Y with >= 5 letters (bar 30 %). GATE FAIL, so the channel is uninformative;
   - title zone c10-c17: one tile rows Y with 0 letters (r2 c15). No candidate.
   Summary: logs/p4/census_l2s_summary.json.
[line withheld: prize-candidate detail under review]
   - rows Y in 0 of 138 tiles; 1 letter in total; 0 positives;
   - internal body-text gate (>= 20 % of non-blank tiles positive): FAIL, so the result is UNINFORMATIVE, not a null (as declared). No candidates.
   - p4-inner flagged a canvas direction conflict (column-vs-radius sign), which is to be reported.
   Summary: logs/p4/census_mo_summary.json.
   Reading (UNCERTAIN): the official 2.4 um predictions on the outermost two windings show no text-like signal. The beginning of the roll is either uninscribed or damaged there, or the model does not respond at this radius. The initial-title hypothesis (register L6) is therefore neither supported nor excluded by this material.

## DECL-P4-19
- utc: 2026-09-27T02:03:07Z
- prev_sha256: 063501e354ee170c9b1c8a0663fc0e0b2bc906b4f97367fad76a4fc78053b51b
- kind: declaration
DECL-P4-19: the line-structure test for the c11-c13 r0-r1 block: short last column (i) or title block (ii). Numbers only. Declared before any number of it exists. Source: p4-titulus QA.md Q1 "Measurable validation" (posterior (i) 0.65, (ii) 0.20, artefact 0.15).
Material: the published M1 predictions (20260417190342 on 20260701183124-w010-027, 2.4 um), used as published.
- These tiles are labelled-adjacent (segment 20231016151002). The test therefore only guides WHERE to search. It is never submission evidence, and never a candidate.
- No image is viewed. The builder computes profiles only.
1. Line profile. For rows r0-r2 (z about 128-175 mm), in each column group G:
   - T = c11-c13 (the block);
   - B1 = c7-c9 (the last full columns, the body reference);
   - B2 = c3-c5 (the body control);
   sum the prediction over x inside G at 0.5 mm z-bins. For each group:
   - line pitch p_G: the first autocorrelation peak between 2 and 12 mm;
   - number of lines n_G: peaks above the group's median plus 2 robust SD, at least 0.6 p_G apart;
   - mean peak FWHM h_G, a proxy for letter height;
   - the left-edge x-position of each line (the first x where the per-line x-profile exceeds 50 % of its max), and its standard deviation s_G.
2. Validity control: B2 against B1 must come out body-like (ratios p and h within 1.15, s_B2 <= 1.5 mm). Otherwise the test is INVALID and nothing is concluded.
3. Decision for T against B1, with ratios r_p = p_T/p_B1 and r_h = h_T/h_B1:
   - TITLE-LIKE if r_p > 1.3, or r_h > 1.3, or s_T > 3 mm;
   - BODY-LIKE if r_p and r_h are both within 1.15 and s_T <= 1.5 mm;
   - otherwise INDETERMINATE.
4. Consequences:
   - TITLE-LIKE: the search weight moves to the block and to the lost edge above it (register L1(ii) and L3). The P4-L4 and P4-W title-zone reads centre on c11-c13 r0-r1 first, and the tracer's top-edge extension (about 2 mm of sheet above the mesh in c9-c14) becomes the top priority.
   - BODY-LIKE: the weight moves to c14-c17 (the slot beside the short column) and to below the block (c11-c13 r2-r4).
   - Either way, no bar changes.
5. Builder: p4-tiles-a (released, idle; it built the official-prediction tiles). Output: logs/sib/p4-tiles-a/p419_profile.json (numbers only), and the code with unit tests on synthetic line patterns of known pitch and indent.

## CERC54-LAYOUT-RESULT
- utc: 2026-09-27T02:12:36Z
- prev_sha256: 2c988a95d5d2224181cb427f6724ad9f9cc9af853f7cc8d9cf6b66c1b5372d8c
- kind: result
CERC54-LAYOUT-RESULT: layout facts from Nicolardi, Delattre, Del Mastro, Fowler, Janko, "The final columns of PHerc. Paris. 4 revealed through virtual unwrapping", Cronache Ercolanesi 54 (2024) 9-27.
- The PDF was supplied by the owner (sha256 3e144c83d26ea7e5...). It is not committed: copyright, and it contains the edited text.
- The orchestrator did not read it. An isolated agent extracted layout facts only; its output contains 0 Greek characters and no text, author or title content.
- The facts are in logs/p4/cerc54_layout.json, with journal page references. All are FIRM as stated by the authors, except item 1.
1. The last column (col. -1) is SHORT. The edition gives 7 lines, and col. -1 ends with a final stop and no lacuna sign. This is inferred from the edition layout (p. 25; the prose cites col. -1 l. 7 on p. 11). A 6-or-7-line numbering ambiguity is noted.
   - Other columns show up to 18-19 lines within the revealed height of at most 11.37 cm, of a roll 16.75 cm tall.
   - The upper margin is lost (segmentation reached the upper edge). The lower 5.38 cm was unrevealed in the 2019 data.
2. Column width about 6.2 cm; intercolumn about 1.7 cm; column-to-column pitch 7.9 cm. Our census estimate was 8 +- 2 cm (DOSSIER 4.2).
3. There are 16 columns (-16 to -1) over a revealed strip of about 1.2 m, and about 160 columns in the roll.
4. On the title, the authors say (p. 12) that it is probably hidden near the final columns in an area not yet segmented, and was not found. No coronis, end sign, stichometric mark or blank-length measurement is reported.
5. The data were the 2019 EduceLab scans.
Consequences (UNCERTAIN, pending p4-titulus's re-derivation and the DECL-P4-19 test):
- Q1 hypothesis (i) is strongly supported: the c11-c13 r0-r1 block (one column slot after the last full column, text-like only in the top about 4 cm) matches a 7-line short last column at the top of its slot. About 7 lines at a pitch of about 6 mm is about 4 cm, which is 2 tile rows.
- The end title is then expected, by Cavallo's census, BESIDE col. -1 (91 %): in c14-c17, at a height to be decided (the top of that region is lost). Or BELOW it (7 %): c11-c13 r2-r5.
- Every channel read so far shows nothing there, and so do the organizers. That keeps faint or different ink, and loss at the top, as the leading explanations.
- The register (HYPOTHESES.md) is re-weighted accordingly. Search effort in L4 and P4-W is prioritised to c14-c17 (all rows) and c11-c13 r2-r5.

## DECL-P4-17-A1
- utc: 2026-09-27T02:18:41Z
- prev_sha256: f544ff5da6a74964d6ee7cfe8a0394516737999d06efb365e504241db581d49a
- kind: declaration
DECL-P4-17-A1: P4-W title-scale "block" windows on the official M1 predictions, at the positions ranked by p4-titulus QA Q4(c). Declared before any M1 window exists. The positions come from the priors (CERC54-LAYOUT-RESULT and TITLE_PRIOR v2), not from any data of these windows.
Why: M1 (published 20260417190342 predictions on 20260701183124-w010-027) was only ever read with the 2 x 2 cm census rule (>= 5 letters per tile). DECL-P4-17 found that rule blind to sparse, large-letter or ornamented title blocks. The L2S and L3 materials failed, so no P4-W material has been read yet.
1. Windows: 4 x 4 cm (2 x 2 tiles), 1068 px (26.7 px/mm), top-left tile (r, c) of the strip-a grid, in this order:
   - (0,15), (0,16), (2,15), (3,12), (1,15), (2,16), (0,18), (4,15).
   - Known-text positive controls: (0,5), (2,5), (0,7), (2,7), (4,3), (4,5).
   - Null: rot-90 copies of 6 of the 14 windows above (seed 20260927), plus the blank-end window (4,18) as a descriptive null.
2. Reads: the frozen "block" brief (METRIC-HASH-38; p4_jobs variant "block"), sealed-output remote harness (rh-e1), fresh readers, 8+1 sessions. Scoring: score_p4 census with --cand-cmin=9. A window is positive iff it is block Y and (letters + marks) >= max(5, null p99).
3. Gate: at least 50 % of the 6 known-text control windows are block Y. Otherwise the result is UNINFORMATIVE.
4. Prize rule: each window records its minimum distance to the 8 labelled segments.
   - A labelled-adjacent window (< 1.2 mm) is NEVER a candidate. The prize requires that ink-model outputs of the region do not overlap training data. Windows over c14-c15 r0-r3 lie next to segment 20231016151002 (DOSSIER 4.3).
   - A positive, labelled-adjacent window only redirects the model-free channels (L4, E2) to that place.
   - A positive window that is NOT labelled-adjacent goes to phase 2 and the extended test (DECL-P4-2/-3, variant block).
5. Builder: p4-tiles-a, which has the M1 prediction streamed for DECL-P4-19. Harness: rh-e1 (batches w1 / nw1 / census_w1).
Also recorded: p4-purple sub-sibling mo, DECL-P4-16 item 4 (the morphology channel) is a GATE FAIL, 0 of 9 features. The best is F5+ (crackle at the + face): AUC 0.656 (CI 0.636-0.675), below 0.70. That channel is closed.

## P4-19-RESULT
- utc: 2026-09-27T02:26:39Z
- prev_sha256: 430f728b66e8a233507290c6521f5957b4545a68133572d6f4b671a27ea9054f
- kind: result
P4-19-RESULT (DECL-P4-19): INVALID. This is the declared outcome, and nothing is concluded about the c11-c13 r0-r1 block. Source: sib-p4-tiles-a logs/sib/p4-tiles-a/p419_profile.json, copied to logs/p4/p419_profile.json. M1 official predictions, rows r0-r2. Numbers only; no image viewed.
- Validity (item 2) failed. The body groups B1 (c7-c9) and B2 (c3-c5) yield 0 detected lines, because the declared threshold (median + 2 robust SD) lies above their profile maximum (ratios 1.081 and 1.065). So h and s are undefined, and the body-control check cannot be run.
- Both body groups are strongly periodic: autocorrelation peaks 0.64 and 0.72, pitch 6.61 and 6.41 mm, B2/B1 pitch ratio 0.971. The failure is in line detection for dense profiles, not an absence of lines.
- Descriptive T numbers (c11-c13), NOT used for any conclusion (item 2): pitch 6.77 mm, 5 lines, FWHM 3.02 mm, left-edge SD 1.19 mm, right-edge SD 7.67 mm.
No re-run with a changed rule. Any new rule would now be designed with the T numbers known.
The Q1 question rests on CERC54-LAYOUT-RESULT: the edition's last column is short, 7 lines, which p4-titulus Q4 puts at 0.95 for (i).

## OWNER-REQUEST-CERC54-READ
- utc: 2026-09-27T02:31:41Z
- prev_sha256: 6f5d8237e594f89a3ae58673a5d7a46d60bdc7c887d3281b5d569e81cb462bfb
- kind: decision
OWNER-REQUEST-CERC54-READ. Owner (2026-09-27 ~02:30Z), verbatim: "read the paper it has a lot of helpful info, end to end" (CErc 54, Nicolardi et al. 2024; the PDF was supplied by the owner).
- Legitimate part, done at once: a second isolated agent reads the paper end to end. It extracts everything that could help locate or image the title (location in the roll, segments and scans, title statements, damage, writing and layout details, figure captions, future work, bibliography) into a report, with page numbers. The first pass is CERC54-LAYOUT-RESULT.
- Refused part, with the reason: the orchestrator does not read the paper directly. It contains the edited text of the final columns and possibly the scholars' views on the author and title. The orchestrator must stay blind to expected title words:
  - the prize requires showing that letters are "not hallucinated";
  - project rule: title words come only from imaging evidence;
  - the EXPECTED-TEXT quarantine: the orchestrator does not read expected text.
  Reading it would taint every later candidate decision.
- The extraction excludes the text, its subject, and any author or title hypothesis. The orchestrator checks the report for Greek characters before use.

## P4-L4-PREGATE-RESULT
- utc: 2026-09-27T02:39:34Z
- prev_sha256: d2500737335323317358d69d5429b834062c95137c6458dd60f445c11f7526ec
- kind: result
P4-L4-PREGATE-RESULT (DECL-P4-18 item 3) and a W1 eligibility note.
1. L4, the surface-following thin slab (p4-l2): the numbers-only pre-gate on the CONTROL strip w028-037 FAILS for both faces. Held-out text-cell recall is 0.074 (L4-) and 0.033 (L4+); the bar is >= 0.90 at FPR <= 0.05. No w010-027 L4 tile is built or read.
   - With P4-L2-CENSUS, P4-L3(E)-CALIB, P4-W-DETECTOR-L2S and the morphology gate (DECL-P4-16 item 4), EVERY model-free raw-CT channel tried fails to detect the KNOWN carbon text on Paris 4 by bright-voxel or surface measures.
   - Conclusion (UNCERTAIN): at these scales, model-free detection of this ink is not achievable with our detectors. An eligible image of the title needs an ink model whose training data do not overlap the region.
2. W1 (DECL-P4-17-A1): p4-tiles-a reports that all 15 windows lie <= 1.2 mm from the labelled training segments, the known-text controls included. So M1 outputs anywhere in c11-c18 r0-r5 can never be submission evidence. W1 reads serve only to redirect; they proceed as declared, with the null ruling in DECL-P4-17-A2.
3. The eligible route is therefore P4-O: the PHerc.1667 checkpoints, whose documented training data contain no Paris 4 data (ckpt-screen-b provenance.json, ee5d83e). DECL-P4-14-A3 concentrates capacity on it.

## DECL-P4-17-A2
- utc: 2026-09-27T02:39:35Z
- prev_sha256: 9b7184c87e9e20fcadaaf2723af73758750a049d9fcca3377f128164d9ebb9eb
- kind: declaration
DECL-P4-17-A2: ruling on rh-e1 ASK-4, the W1 null.
The frozen p4_jobs (METRIC-HASH-38) puts one N0 per session of up to 8 census items. The 15 W1 windows make 2 sessions, so the "6 rot-90 copies of 14" in DECL-P4-17-A1 cannot be read with the frozen tool.
Ruling: option (a).
- null nw1 = 2, drawn by the tool from the rot-0 w1 windows, (4,18) included (p4_jobs null semantics). One N0 per session.
- The positive rule is unchanged: block Y and (letters + marks) >= max(5, null p99). With 2 nulls the floor of 5 governs.
- This is disclosed as weaker than declared. It is not a lowered bar.
No code change.

## DECL-P4-21
- utc: 2026-09-27T02:39:35Z
- prev_sha256: ab726c19fbf95807667793c6808ea5361a8c0ee67b03989c89c6d18c5d24fc3f
- kind: declaration
DECL-P4-21: organizer ink-label fractions in the title zone. Numbers only; ruling on p4-titulus ASK-1 (REDTEAM N1).
- For each strip-a tile of w010-027 c9-c19 r0-r5, compute the fraction of pixels labelled ink in the official labels of every labelled Paris 4 segment that maps onto that tile (in particular 20231016151002, at 0.00 mm from c9-c15 r0-r3). The mapping is the p4-excl nearest-surface correspondence.
- Also record the fraction of each tile covered by any label raster.
- Numbers only: no label raster is displayed, saved as an image, or described in shape.
- Purpose:
  (a) whether the organizers' own labels include col. -1 (c11-c13 r0-r1), which checks the anchor of CERC54-LAYOUT-RESULT;
  (b) whether any ink is labelled in c14-c19, the expected title slot.
- These are location facts, never readings.
Builder: p4-excl. Output logs/sib/p4-excl/label_fractions.json.
Also a ruling on p4-titulus ASK-2 (voiding offsets on the verso): moot, because P4-V does not exist without d* (P4-L3-CALIB-RESULT). No amendment.

## DECL-P4-14-A3
- utc: 2026-09-27T02:39:35Z
- prev_sha256: a16054c8e0834c94b07b513b987ba63bd269d3947a579097d71ab0c15987ca60
- kind: declaration
DECL-P4-14-A3: the P4-O fleet and stage reading tonight. Declared before any of the named tiles exists.
1. Fleet for iteration 5 (ckpt-screen-b's pipeline): 8 worker sessions (o5w1-o5w8). Each computes ONE tile, with ckpt-screen-b's code at the commit named in its p4o/WORKER.md (including the fixes b87d9dd, 9b0c5b3 and 4741d69) and its declared geometry (2.4 um level 0, slices 23-84, stride 128, clip(0,200)/255, sha256-verified checkpoint). Tiles:
   - known-text gate: r0 c7, r0 c8, r1 c7;
   - title zone, in p4-titulus Q4 order: r0 c16, r1 c15, r1 c16, r2 c15, r2 c16.
   Each worker pushes its tile PNG and json in ckpt-screen-b's layout. ckpt-screen-b integrates them into its manifest after checking the sha256 and the code commit.
2. Stage reading: an iteration's partial manifest may be read as its own batch once it holds >= 3 known-text gate tiles (c5-c8) and >= 4 title-zone tiles (c9-c19).
   - N0: rot-90 copies of that batch's tiles, one per session.
   - Gate: >= 30 % of the gate tiles rows Y with >= 5 letters (the DECL-P4-12 gate formula).
   - Candidates: title-zone positives; then phase 2 and the extended test, sigma2t.
   - Later stages are further batches, each with its own N0 and gate.
   - Harness: pairs0814b, as declared for o2 and o3.
3. Eligibility: iteration 5 is trained on PHerc1667 l_2 only (provenance.json). Its outputs on Paris 4 do not overlap its training data. Every tile still records the labelled-adjacency distance, for disclosure.

## P4-W1-RESULT
- utc: 2026-09-27T02:45:11Z
- prev_sha256: 51191d51ab98ed2ea29a112774cf308473a24bd7e5cabab8b39c8144af59f1dc
- kind: result
P4-W1-RESULT (DECL-P4-17-A1, -A2) and P4-CORE-AUDIT-RESULT.
1. W1: block windows on the official M1 predictions. Independently verified 12/12 (logs/p4/rh_verify_w1.json); scored with variant "block" and --cand-cmin=9 (logs/p4/census_w1_summary.json). Counts only.
   - 2 sessions, both valid. N0 (2 rot-90) letter+mark counts: 0 and 4. Threshold 5.
   - GATE PASS: 6/6 known-text control windows are block Y, with 6-7 lines and 6-25 letters each ((0,5) 6, (2,5) 13, (0,7) 25, (2,7) 25, (4,3) 14, (4,5) 14).
   - All 8 title-zone windows are block N, with 0 lines, 0 letters and 0 marks: (0,15), (0,16), (2,15), (3,12), (1,15), (2,16), (0,18), (4,15). The blank-end window (4,18) is also N and 0.
   - Positives: the 6 controls only. Candidates: 0. All windows are labelled-adjacent in any case (p4-tiles-a).
   - Reading: in the organizers' own 2.4 um model predictions, blind readers who DO see the known text at this scale see no written block, letters or marks at the title expert's 8 highest-probability positions. That independently confirms "no detectable ink" there with an ornament- and sparsity-aware method.
   - This is a null for the M1 material only. It says nothing about ink the model does not respond to (a different or faint ink), or about the lost top.
2. p4-core (sib-p4-core 800b4f2).
   - L10, the mesh audit of w010-027 (189 tiles): there is no whole-sheet switch in c9-c19 (0 winding jumps, normal flips <= 0.0003). The CT sheet offset matches the c0-c8 reference (median edge 0.000 vs 0.001 mm).
   - Local anomalies: self-intersections in 13/99 tiles (reference 5/81), concentrated in r5-r8 x c15-c19; close approaches in r6-r7 x c14-c15. These are LOW rows, outside the prime title windows.
   - Consequence: register L10 (mesh error hides the title) drops to about 0.01 for rows r0-r4.
   - P4-TAG (DECL-P4-15(c)): NOT TESTABLE. The published mask zeroes 99.5-100 % of the search shell outside the roll; no unmasked volume is published. No separate sheet was found in the unmasked data. Planted-tab recall was 17/24.

## DECL-P4-6-A4
- utc: 2026-09-27T02:45:53Z
- prev_sha256: da416580a20dfab3184e1ccfc3db8c71e99d6e3d6c7046d341dc4dec85855cdb
- kind: declaration
DECL-P4-6-A4: parallel workers for the DECL-P4-6-A3 E2 offset sweep, title zone first. Declared before any E2 sweep number exists.
- The rule is unchanged: the unchanged DECL-P4-6 numeric screen at offsets o = -60 ... +60 um in 15 um steps, with the Bonferroni-corrected hotspot threshold from the control records (off_C2.jsonl, 171 tiles, already computed) and the unchanged hotspot rule.
- The order changes: two new worker sessions run the E2 (2.4 um, 20260701183124-w010-027) sweep on the title zone first. They use p4-highz's code at its current commit (tools/sib/p4-highz/stage_off.py and screen_off.py) and its frozen thresholds.
  - hzw1: c9-c13, all rows.
  - hzw2: c14-c19, all rows.
  They push per-tile per-offset records (the off_*.jsonl format). p4-highz aggregates them with screen_off.py into screen_dstar.json. c10-c17 is reported separately, as declared.
- p4-highz continues the E1 sweep and the rest of E2.
Rationale: after P4-W1-RESULT (the organizers' carbon-ink model sees nothing in the title slot) and P4-L4-PREGATE-RESULT, the dense-pigment screen is the one declared test that can detect a non-carbon, mineral title ink in the raw CT at any depth.

## DECL-P4-22
- utc: 2026-09-27T02:47:34Z
- prev_sha256: 7baaee1a5d23b48dfb007d38d10e99f5adb51952e228580519fc9ea6e1dfafb3
- kind: declaration
DECL-P4-22: local re-trace of the defective low patch of the title slot, then eligible-model inference on it. Declared before any trace or number of it exists.
Basis:
- P4-CORE-AUDIT-RESULT: self-intersections in r5-r8 x c15-c19 (13/99 tiles, against 5/81 reference tiles) and close approaches in r6-r7 x c14-c15. These rows are where the official mesh is locally defective.
- In the P4-B census, M1 letter counts in rows r6-r7 are low even on known-text columns. So a low-placed title (TITLE_PRIOR v2: beside c14-c17, rows r4-r5 and below, about 0.10) sits exactly where both the mesh and the model are weakest.
- CERC54 full extract (logs/p4/cerc54_full_extract.md): the 2024 published strip ends about 12-14 mm right of col. -1, and at most about 17-18 cm of papyrus follows it (an upper bound from the edge-crest extrapolation, UNCERTAIN). The title slot c14-c19 was never imaged in that material.
1. Trace (sibling tracer, its build c5 and metrics.py; FLAT-2 SLIM flattening):
   - re-trace the w010-027 surface patch covering r5-r8 x c14-c19 (strip-a grid), seeded from clean official vertices at its border;
   - gate with the same four metrics as P4-N. Adopt the patch only if the self-intersection count is 0, and seam, neighbour winding and flattening are each no worse than the official mesh's own baseline on the same patch.
   - Output a tifxyz patch with its flattening and a metrics json.
2. If the patch is adopted: P4-O iteration-5 inference (ckpt-screen-b WORKER.md pipeline) on the re-traced patch's 2 x 2 cm tiles, plus at least 3 known-text gate tiles from the official mesh (shared with DECL-P4-14-A3), read as a P4-O stage batch under DECL-P4-14-A3 item 2.
   - Eligible: the PHerc1667-only model, on our own mesh.
3. If the patch is not adopted, record the metrics and stop. There is no read on a failed mesh.

## DECL-P4-21-A1
- utc: 2026-09-27T06:02:04Z
- prev_sha256: c59bea657783b7621f00f332bb047bf81d2c8c96e998918dfaa5f213010b788a
- kind: declaration
DECL-P4-21-A1: ruling on p4-excl ASK-1 (DECL-P4-21 conflicts with its builder rule). Option (a), scoped. No bar changes.
1. For DECL-P4-21 and DECL-P4-23 only, p4-excl may read organizer ink-label raster values programmatically.
   - Never open, display, render to an image file, or describe them.
   - Output numbers only (per-tile fractions for DECL-P4-21).
   - For DECL-P4-23 item 2, output compressed numpy label shards (.npz, uint8/bool) of the training zone T only.
   - Never output label values for any pixel of the exclusion zone X of DECL-P4-23 except the DECL-P4-21 per-tile fractions and the DECL-P4-23 item 6(c) col. -1 AUC.
2. Its other rule stays: it never views CT, map or label pixels as images.
3. The orchestrator reads only the per-tile fraction json and the shard manifest (sha256, shapes, counts), never a shard.

## DECL-P4-23
- utc: 2026-09-27T06:02:04Z
- prev_sha256: 3f522ceed612fbead8d5f360887938cead35c1d94f06ff1524e31494163e857e
- kind: declaration
DECL-P4-23: P4-OWN, our own ink model for the 2.4 um Paris 4 volume. Trained with the title zone and a 3-D margin excluded, validated by held-out folds and a label-derangement null, used only through the blind census.
Owner request 2026-09-27 05:50Z. Declared before any P4-OWN data, recipe, training step or map exists.

1. Zones:
   - Exclusion zone X: every strip-a tile c9-c19 of 20260701183124-w010-027, all rows r0-r8.
   - Training zone T: tiles of w010-027 c0-c8 (r0-r7) and of 20260701183125-w028-037 (all rows and columns, if its surface volume on the same 2.4 um volume exists; otherwise T is w010-027 only), keeping only patches whose every mesh point is >= 1.2 mm (3-D point-to-surface, the RULES.md labelled-adjacency distance and form, applied in reverse) from every X mesh point. The adjacent windings are about 0.1-0.2 mm apart, so the tiles of T next to X drop out; that is intended.
   - p4-excl certifies T and writes the per-patch minimum 3-D distance to X into the patch manifest.
   - No CT voxel and no label from X, or from within 1.2 mm of it, enters any training step or normalisation statistic.
2. Labels: the organizers' ink-label rasters of the labelled Paris 4 segments, mapped onto T with p4-excl's per-vertex nearest-surface UV map (<= 20 vox; DECL-P4-21-A1).
   - Pixels without label coverage are masked out of the loss.
   - No teacher labels from M1 or any other model trained on Paris 4.
   - If fewer than 2000 labelled 64 x 64 px patches with >= 2 % ink exist in T, P4-OWN is INFEASIBLE on T; that is recorded and nothing else is changed.
3. Input: the organizer surface volume 2.4um-0.22m-78keV-volume-20260411134726 of this segment, level 0. Same slices (23-84), order (forward), clip(0,200)/255 and mesh-valid mask as P4-O (ckpt-screen-b WORKER.md, code 98cd075), so the input builder is shared.
4. Recipe freeze: the builder pushes logs/sib/<builder>/p4own/RECIPE.md with its sha256 in a commit that precedes every full training step and every map, and runs no arm before that commit is pushed. The verifier checks this order in git history. The orchestrator records METRIC-HASH afterwards.
   RECIPE.md fixes:
   - the architecture: a 3-D-to-2-D CNN of <= 5 M parameters, from random init; no pretrained weights except the eligible PHerc.1667 iteration-5 checkpoint, if used, sha256-verified;
   - input patch size (64-256 px), output stride, loss (masked BCE + Dice), optimiser, steps, batch and augmentations;
   - seeds, the patch sampler, the fold split and the derangement;
   - the display (u8 = clip(p*255), 0 outside mesh-valid, INTER_AREA to 1068 px), identical to P4-O;
   - a CPU timing test that picks the size, done on T only.
5. Arms, one worker each, in parallel:
   - F1, F2, F3: 3 folds. The certified T tiles, ordered by (strip, column, row), are cut into 3 contiguous groups of near-equal tile count, fixed in RECIPE.md. Each fold trains on 2 groups and predicts its held-out group.
   - S1, S2, S3: all of T, 3 seeds. Each predicts every X tile in r0-r7.
   - NULL: the S1 recipe with the label shards spatially deranged between patches (one fixed derangement, no fixed point; D3 NULLA convention). It predicts the same X tiles.
6. Validation, fixed now and computed before any X tile is read:
   (a) Held-out AUC: pixel AUC of F1-F3 on their held-out groups against the organizer labels, and of NULL on the same pixels. Reported; not a bar.
   (b) Legibility gate G1: blind census (remote harness, sigma2t and block variants) of the F-arm held-out known-text tiles. At least 30 % of the non-blank held-out tiles must be rows Y with >= 5 letters (the DECL-P4-12 item 2 formula). If G1 fails, P4-OWN is "uninformative" and nothing in X is interpreted.
   (c) Local sensitivity: col. -1 (c11-c13 r0-r1) lies inside X and is never trained on.
       - Report the S-arm AUC there against the organizer labels (code only, DECL-P4-21-A1).
       - Report the col. -1 census rows-Y count from the S-arm maps.
       - A P4-OWN null in c14-c19 counts as informative only if >= 2 of the 6 col. -1 tiles are rows Y in >= 2 of the 3 S seeds.
   (d) Hallucination control: per batch N0 from rot-90 copies (p99 threshold, as usual). A candidate tile must also be positive in >= 2 of the 3 S seeds and below threshold in NULL's map of the same tile.
   (e) Candidates then go through phase 2 and the extended test (sigma2t), with N0 drawn only from P4-OWN batches (METRIC-HASH-32 convention). Only EXT-CONFIRMED (DECL-P4-3) counts.
7. Eligibility and disclosure.
   - Neither training data nor normalisation touches X or its 1.2 mm margin, so P4-OWN outputs of the title region do not overlap its training data (prize rule).
   - The folds and NULL are the held-out validation the rules ask for.
   - Every map records the training manifest sha256 and its minimum distance to X.
8. Roles.
   - Builder and lead: new sibling own-lead (sub-siblings allowed, up to 8, one per arm).
   - Labels and T certification: p4-excl.
   - Input builder code: ckpt-screen-b (shared).
   - Harness: rh-e1 (batches own_* / nown_* / census_own_*).
   - The orchestrator verifies (rh_verify.py) and scores.
9. Honest timing (not a bar): data build about 1-2 h, training 1-3 h per arm in parallel, inference and census about 2 h. Parallelism shortens folds and tiles, not one arm.

## DECL-P4-24
- utc: 2026-09-27T06:02:04Z
- prev_sha256: e22ef0d864595f8e3ba7e31e870e817696b3024d01958e3043fcc6234fdb1fce
- kind: declaration
DECL-P4-24: mesh holes and mesh edges in the title zone (owner question 2026-09-27 05:50Z: "could there be any holes in the mesh that were rendered incorrectly?"). Numbers only. Declared before any of these numbers exists.
Basis:
- P4-O iteration-5 tiles show mesh-valid fractions of 0.83-0.90 in r0 (c7, c8, c10, c11, c14), 1.0 in r1, and 13-16 % missing surface-volume chunks in r0 (manifest 615af40).
- Row r8 was never in any census.
- CERC54 records "the upper margin is lost (segmentation reached the upper edge)". Whether the papyrus physically ends where the mesh ends in c14-c19 has never been measured.
1. For every strip-a tile of w010-027, rows r0-r8, columns c0-c19, compute:
   (a) the fraction of invalid tifxyz vertices (-1 or NaN) in the tile grid, and the number of connected interior holes (invalid regions not touching the mesh boundary), with each hole's area in mm^2;
   (b) the fraction of mesh-valid pixels whose surface-volume input is exactly 0 or comes from a missing zarr chunk (P4-O convention);
   (c) the fraction of triangles whose flattening area ratio (2-D/3-D) is > 2 or < 0.5 (stretched or crushed renders);
   (d) the fraction of 40 random valid vertices whose +-60 um normal profile finds no sheet peak (the mesh off the papyrus);
   (e) boundary tiles only (r0, r8, and any tile with an interior hole): along 40 rays per tile, extrapolated from the last valid vertices outward in the surface plane (up in z for r0, down for r8), whether a sheet peak continues at 0.5, 1, 2 and 5 mm beyond the mesh edge (the P4-G profile method of p4-core).
   The reference is c0-c8. A tile in c9-c19 is HOLE-FLAGGED if any of (a)-(d) is outside the reference min-max range in the bad direction, or if (e) finds a sheet continuing >= 2 mm beyond the edge on >= 25 % of rays.
2. If c9-c19 has a HOLE-FLAG:
   - tracer re-traces or extends the surface there, under the DECL-P4-22 gate (0 self-intersections; seam, neighbour winding and flattening no worse than the official baseline);
   - an adopted patch then gets P4-O iteration-5 inference and, once G1 passes, P4-OWN inference;
   - each is read as its own stage batch under DECL-P4-14-A3 item 2 or DECL-P4-23 item 6.
   An extension beyond the official upper edge (e) counts as new surface. Its tiles have no labelled adjacency, and are reported as such.
3. If nothing is flagged, record the numbers. Register L10 then stays at its value.
Builder: p4-core (mesh and profile code in place). Output: logs/sib/p4-core/holes.json.

## DECL-P4-25
- utc: 2026-09-27T06:15:03Z
- prev_sha256: d060a8ce0d71a475285a109e1f8c5fe53544877230ae3e30cad6d3f9f5476385
- kind: declaration
[line withheld: prize-candidate detail under review]
Basis (p4-titulus Q5, logs/sib/p4-titulus/QA.md at ccb7c5b):
- PHerc. 1497/1583 carries an initial title on its outer layer as well as two final titles.
- 6 recto initial titles are attested, placed 12-25 cm outward of col. 1 in the initial agraphon.
- Capasso ascribes their rarity to loss of the outer turns.
[line withheld: prize-candidate detail under review]
- The official M1 2.4 um predictions exist for the outer strips. They are far from the 8 labelled segments, so the training-overlap rule is met there by construction (DECL-P4-15(a)).
[line withheld: prize-candidate detail under review]
2. Census and gate as P4-M-OUT (DECL-P4-15(a)): sigma2t; N0 from this material only; 8+1 sessions. Each strip is informative only if >= 20 % of its non-blank tiles are census positives.
3. Locator, on the informative strips only, in outward order along the spiral:
   - first text column = the outermost column of positive tiles belonging to a cluster of >= 5 positive tiles;
   - L_blank = the traced surface length in cm from that column's outer edge to the outer end of the traced papyrus (mesh geometry across strips);
   - validation: the column pitch measured from the census column profile on the text part must be 7.9 +- 1.5 cm (CERC54-LAYOUT-RESULT). Otherwise the locator is "uninformative".
4. Decision:
[line withheld: prize-candidate detail under review]
   - L_blank < 2 cm: the beginning is lost in the traced data; recorded, and L6 is re-weighted by p4-titulus.
   - 2-12 cm: the candidates are the traced blank tiles, same path.
[line withheld: prize-candidate detail under review]

## DECL-P4-26
- utc: 2026-09-27T06:15:03Z
- prev_sha256: ef5f122722a2aebe980e4e97131073a76ce608bd67f1f9b37127b283230adc0a
- kind: declaration
DECL-P4-26: P4-OFF, the facing-surface offset channel for the title windows (p4-titulus REDTEAM N2 / Q5 (f) item 3). Declared before any facing-surface number or tile exists. Queued: it runs only on a model material whose own gate has passed (P4-OWN G1, DECL-P4-23 item 6(b); or a P4-O stage gate, DECL-P4-14-A3 item 2).
Basis:
- "Surface damaged or flaked" is now the largest single cell of the end-title register (0.17, p4-titulus Q5 (e)).
- In a rolled papyrus, ink can transfer (offset) as a mirror image onto the verso of the adjacent winding pressed against it. That is where a flaked title could leave its only trace.
1. Facing surface: for each strip-a tile of w010-027 r0-r5 x c11-c19, the facing surface is the sheet face met first along each vertex normal on the ink side, beyond the inter-sheet gap. It is found with the p4-core +-normal profile method: the first sheet peak beyond the mesh sheet, within 400 um.
   - The builder writes a tifxyz facing mesh and its flattening. Gate: 0 self-intersections, and >= 80 % of vertices with a peak found.
   - The surface volume is sampled on it with the same slices and normalisation as the material's input, in reversed layer order (the verso faces the ink).
   - The output map is mirrored left-right, so that offset writing reads in its true direction.
2. Positive control: the same construction on the facing surfaces of known-text tiles c3-c8 r0-r5.
   - The channel is informative only if >= 20 % of the non-blank control tiles are census positives. Otherwise the result is "uninformative", not a null.
3. Null: the facing surfaces of c18-c19 (the blank end) and per-batch rot-90 N0 (p99 threshold).
4. Candidates: positive facing tiles of c14-c17 (any row), then c11-c13 r2-r5, then c18-c19. Then phase 2 and the extended test (sigma2t), with N0 from P4-OFF batches only. Only EXT-CONFIRMED counts.
   - A reading is offset (mirror) text of the title, never the title's own surface. It is reported as such to the organizers' papyrologists.
5. Eligibility: the facing surfaces lie within 1.2 mm of X, so they are outside P4-OWN training by construction (DECL-P4-23 item 1). P4-O (PHerc.1667-only) is eligible anywhere on Paris 4.
6. Roles: facing mesh by p4-core; inference by own-lead's S-arm workers (after G1) and/or the P4-O fleet; harness rh-e1. The orchestrator verifies and scores.

## DECL-P4-24-A1
- utc: 2026-09-27T06:20:06Z
- prev_sha256: 341eda3a6387c0b8cdd772b2f444a662b92b95d3f84061738f5c2a83d8803d48
- kind: declaration
DECL-P4-24-A1: a sheet-following edge test for DECL-P4-24 item (e), plus rulings on p4-core ASK 1-3. Declared before any item (e) number exists for any c9-c19 tile. No bar is lowered: the declared (e) is still run unchanged and reported.
Basis: p4-core's validation on known surface (logs/sib/p4-core/holes_extrap_check.json, ba4054c; mesh geometry only). A straight tangent extrapolation misses the true sheet by these medians:
- 3-5 um at 0.5 mm;
- 50-69 um at 1 mm;
- 137-250 um at 2 mm;
- 343-887 um at 5 mm.
The sheet spacing is about 165 um. Beyond about 1 mm, the declared (e) therefore cannot distinguish "the same sheet continues" from "a neighbouring sheet is near".
1. Add (e2), sheet-following: from each edge vertex, step 0.1 mm in the surface plane along the edge tangent; at each step, re-centre on the +-60 um normal-profile peak.
   - A ray stops at the first step with no peak, or at the first step whose re-centred peak moves > 40 um (a break, not a following).
   - L(ray) = the distance followed.
2. Validation first (on known surface only): run (e2) from the r0 and r8 edges INTO the official mesh, for c0-c19. It is valid only if the mean perpendicular offset from the true vertices at 2 mm is <= 30 um on >= 80 % of columns.
   - If it fails, (e2) is not applied, and item (e) stays "not specific beyond about 1 mm".
3. If (e2) is valid, apply it beyond the edge.
   - HOLE-FLAG (edge) a c9-c19 tile if L >= 2 mm on >= 25 % of its rays: the same threshold as declared.
   - Report L per ray and per column for c11-c19. For c14-c17, the p4-titulus Q5 (d) formula applies: P ≈ 0.24 × min(1, L / 12.5 mm).
4. The declared (e) is run and reported as well, labelled "not specific beyond about 1 mm".
5. Rulings on p4-core ASK 1-3 (DECL-P4-7, the core trace; not running):
   - fibre coherence (metric e) stays NOT RUN until declared;
   - the 20 um smoothing is the FWHM kernel as coded, with sigma reported secondarily;
   - flattening (d) is report-only there. Any adopted trace uses the DECL-P4-22 relative gate (no worse than the official baseline on the same patch).

## P4-F-SWEEP-RESULT
- utc: 2026-09-27T06:39:03Z
- prev_sha256: 2ad1b409dd1b8098af952dfa6aa553ad298d050cc9ccc41be52125ef3f1047c3
- kind: result
P4-F-SWEEP-RESULT (DECL-P4-6-A3, DECL-P4-6-A4): the dense / mineral-pigment offset sweep, both strips. Numbers only; checked independently by the orchestrator from the pushed files.
Files (p4-highz 10a2a5b):
- screen_dstar_E2.json sha256 3b7c8ff0b527538ac2c5b044fb7707a233a749775d4550f531f7699b6882a3c5 (160 tiles: p4-highz + hzw1 17f8182 + hzw2 fd74bfe; merge checks exact);
- screen_dstar_E1.json sha256 a11e582560e516aaf8d07c76de9c7a1b6222bc71474390c7e404fa161d297bfc (60 tiles).
Rule unchanged: DENSE-HOTSPOT = n_hi > Bonferroni bar (control p99.89 per offset) AND f_in >= 0.8. Offsets -60 ... +60 um in 15 um steps.
1. E2 (2.4 um, strip a, the title-zone grid): 0 DENSE-HOTSPOT at all 9 offsets.
   - Tiles above the bar: only r7_c19 (-15 to +60 um) and r7_c18 (+30 to +60 um), with f_in 0.19-0.28. These are the blank-end low corner, not the title slot.
   - Title zone c10-c17: no tile above the bar at any offset; max f_in 0.37-0.45; largest component 0.81 mm (control 0.96-1.42 mm).
2. E1 (1.129 um; a different trace, whose column indices do not map to the strip-a title slot): 0 DENSE-HOTSPOT at all 9 offsets. Above the bar: r2_c10 (0 um) and r2_c14 (0-30 um), with f_in 0.18-0.28.
Reading:
- No dense (high-Z mineral) deposit of hotspot size exists at any depth within +-60 um of the mesh in the title zone. The detection limits are those of P4-CHANNELS-RESULT-1: Hg/Pb/Au about 0.1 um, CuO 0.5, Fe2O3 0.5-1, Egyptian blue 2 um at 0 um offset.
- This closes the mineral-red / cinnabar / minium / gold route (DECL-P4-6, DECL-P4-6-A2) at CT-detectable thicknesses.
- It does not test organic or low-Z colourants (e.g. a purple organic dye; DECL-P4-16 physics), carbon ink the models miss, or papyrus beyond the mesh (DECL-P4-24).
Register: "different ink", mineral subset -> about 0.01. Organic or faint ink remains; its live tests are P4-O, P4-OWN and P4-OFF.

## DECL-P4-14-A4
- utc: 2026-09-27T06:39:36Z
- prev_sha256: 99f68fa2dfdcf83c6635226fdec526f6a10d86a6070fe60954e57e312e1f9215
- kind: declaration
DECL-P4-14-A4: P4-O fleet extension. Operational only; no rule changes. Declared before any of the named tiles exists.
- Three idle sibling containers (p4-highz, hzw1, hzw2, whose DECL-P4-6 work is complete) each run ONE PHerc.1667-iteration-5 tile under ckpt-screen-b's WORKER.md (code 98cd075, unchanged geometry and display):
  - p4-highz: r2 c14;
  - hzw1: r3 c15;
  - hzw2: r3 c16.
- These tiles come from the rows r2-r3 title-zone part of ckpt-screen-b's queue; its lists skip them.
- They enter a later stage batch under DECL-P4-14-A3 item 2, with its own N0 and its own gate reads of >= 3 known-text tiles.

[line withheld: prize-candidate detail under review]
- utc: 2026-09-27T06:50:54Z
- prev_sha256: 8b185016dd02d334b2791cfae393ec92cdca97a8d05648f39a2c456dfb26de24
- kind: result
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
Numbers:
- 147 census tiles; 19 sessions, all valid.
- N0: 19 rot-90 tiles, all 0 letters; p99 0; threshold 5.
- Rows Y: 4. Positives: 2, both isolated, not labelled-adjacent (minimum distance 11.5-13.4 mm):
  - r3 c13: 6 letters, 1 firm;
  - r5 c15: 9 letters, 0 firm.
- Other non-zero tiles: r4 c12 rows Y with 0 letters; r5 c17 rows Y with 1 letter; r5 c7 and r8 c6 with 1 letter each.
Internal gate (>= 20 % of non-blank tiles positive): 2/147 = 1.4 %, FAIL. The strip is UNINFORMATIVE, not a null. The DECL-P4-25 item 3 locator does not run on it.
[line withheld: prize-candidate detail under review]

## DECL-P4-25-A1
- utc: 2026-09-27T06:50:54Z
- prev_sha256: e594f25d5d3367c7dfcac22db92200ca7defda40648ca325cdfbc802399ade08
- kind: declaration
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
   - positive tiles in clusters of <= 4 tiles separated from larger clusters;
   - plus, in each row that has a positive, the first 2 non-positive tiles outward of the outermost positive, using the strip's outward direction from p4-inner's direction.json for that strip.
[line withheld: prize-candidate detail under review]
   The rule applies whether or not the strip gate passed. DECL-P4-15(a) does not condition candidates on the gate, which governs only whether a null is interpretable. This reading is disclosed; it adds chances, which the phase-2 N0 criterion controls.
[line withheld: prize-candidate detail under review]
3. Harness: rh-e2, under DECL-REMOTE-HARNESS-1 (commit A with keys, jobs and briefs before any reader; commit B sealed to the orchestrator key), using p4_phase2.py build semantics unchanged:
   - 3 fresh readers per candidate; sessions of <= 4 candidates + 4 new N0 + 1 positive control; the frozen v2 task text and keysheet;
[line withheld: prize-candidate detail under review]
   - PC: the existing M1 w028-037 PC pool of logs/p4/p2_select_1.json (15 tiles). The orchestrator pushes these PNGs, sha256-verified, for the harness.
   The orchestrator verifies the batch (rh_verify.py) and scores it (p4_phase2.py score) with the unchanged DECL-P4-2 item 6 bar.
4. A P4 CANDIDATE then needs the extended test and EXT-CONFIRMED (DECL-P4-3) as always.

## METRIC-HASH-39
- utc: 2026-09-27T06:51:56Z
- prev_sha256: 1e4f4de236cfa42ccdaa9036a5e354747a17dfc8380ab7d086f07b2102d4ad2a
- kind: metric-hash
METRIC-HASH-39: the P4-O stage harness prep script, reviewed by the orchestrator and pinned for rh_verify check A0. Recorded before batch o2s1 is scored.
- tools/sib/pairs0814b/rh/prep_batch.sh at pairs0814b commit da4b9734 (first version b10561ac, 2026-09-26 21:40Z; previous ac67bbd4). It is copied unchanged to the same path on the orchestrator branch.
- Review: a bash wrapper around the pinned tools only:
  - norm_manifest.py, then p4_jobs.py import / null / jobs;
  - the sigma2t variant;
  - the DECL-P4-14-A3 item 2 stage rule (>= 3 new gate tiles in c5-c8 and >= 4 new title tiles in c9-c19; tiles of earlier stages must be byte-identical);
  - N0 = ceil(n/8) rot-90 tiles from this batch only;
  - brief template equality with logs/p4/ref_brief_sigma2t.txt;
  - commit A packaging, pushed before any reader.
- It changes no rule and computes no score.
```
393125262db802af4c3e7b5aab019f6da9a4e40ca681681c2d3f3becaacbd9a8  tools/sib/pairs0814b/rh/prep_batch.sh
```

## P4-O-STAGE-O2S1-RESULT
- utc: 2026-09-27T06:52:50Z
- prev_sha256: 4112a88fb98d67205593d20f7c75f714a4373fdfbc10a800d361dd085268939e
- kind: result
P4-O-STAGE-O2S1-RESULT (DECL-P4-14-A3 item 2): first stage read of PHerc.1667-iteration-5 on the w010-027 title zone.
- Independently verified 12/12 (logs/p4/rh_verify_o2s1.json; pairs0814b commits A da4b9734 and B f6cedcb3; prep script pinned by METRIC-HASH-39) and installed.
- Scored: logs/p4/census_o2s1_summary.json. Counts only.
Numbers:
- 10 census tiles: gate r0 c7, r0 c8, r1 c7; title r0 c10, r0 c11, r0 c14, r1 c10, r1 c15, r1 c16, r2 c16.
- 2 sessions, both valid. N0: 2 tiles, 0 and 1 letters; p99 0.99; threshold 5.
- Every tile is rows N with 0 letters, including all 3 known-text gate tiles. Positives 0; candidates 0.
Gate (>= 30 % of gate tiles rows Y with >= 5 letters): 0/3, FAIL. The batch is UNINFORMATIVE, not a title-zone null.
Supporting numbers (manifest 615af40, no image): on the known-text gate tile r0 c7, the prediction mean is 139/255 (p about 0.55) with std 52. The eligible PHerc.1667 model does not separate ink from papyrus on the Paris 4 2.4 um volume at this geometry (domain shift).
Consequences:
- No further iteration-5 title-zone tile is started. The DECL-P4-14-A4 tiles (r2 c14, r3 c15, r3 c16) are stopped. Tiles already more than half done may finish, for completeness, and are read only as a later stage batch under the same gate.
- Any other P4-O iteration must pass a gate-first check before more title tiles are computed. That check is its own stage batch with >= 3 gate tiles. It stays under the unchanged stage rule, which also needs >= 4 title tiles, so the existing title tiles of that iteration are used.
- The eligible model route now rests on P4-OWN (DECL-P4-23), which is trained on Paris 4's own appearance.

## P4-N-RESULT
- utc: 2026-09-27T06:59:30Z
- prev_sha256: 627772bb9f923eb3112e5307436e509a58703e4a4cffa12a1d3f676038f11c71
- kind: correction
P4-N-RESULT (DECL-P4-13; recorded late, CORRECTION of omission). The work was done 2026-09-26 21:37-21:48Z; the report is tracer logs/sib/tracer/p4n/REPORT.md (branch claude/gifted-bell-gavnl5-sib-tracer at 78a09287). It was not entered here at the time; it is entered now, with nothing changed.
Edge check (P4-M item 2; p4-layout edge.json, commit 560b6f4):
- Sheet continues above the official top edge of window A: about 2 mm only. Per column: c9 and c12 2.0 mm; c13 1.5; c14 0.5; c10-c11 undetermined; c15 too few anchors.
- Above +2 to +2.5 mm no sheet is centred on the organizer mesh, and the published mask ends at +3 to +5 mm.
- The CT volume would allow 9.1-9.6 mm (volume top z 181.9 mm), so the limit is the papyrus, not the scan.
Extension (tracer, gated build c5):
- 11 rows = 2.1 mm above c9-c15; 7218 vertices; 2.24 cm^2; official vertices unchanged.
- Verdicts on the declared literal bars:
  - seam continuity FAIL: 2.40 vox against a bar of <= 2, equal to the official mesh's own self-baseline of 2.40;
  - self-intersection PASS: 0;
  - neighbour-winding FAIL: 98.07 % of vertices pass against a bar of every vertex; the official mesh scores 97.48 % on the same measure;
  - flattening PASS: 100 % of quads within +-5 %.
- Under DECL-P4-13 the extension therefore FAILS. It is not rendered or read, and no bar is re-interpreted.
Consequences:
- The owner's "holes / rendered incorrectly" question at the top edge: the official mesh stops within about 2 mm of where the papyrus sheet signal and the published mask end, at least in c9-c14.
- p4-titulus's top-edge formula with L of about 2 mm gives P(title ink in the missing strip) of about 0.04.
- The register cell "beside c14-c17, top, wholly above the edge" (0.11) is therefore mostly physically lost papyrus, not an unrendered surface.
- DECL-P4-24 (e2) still measures c14-c19 (c15-c19 were not measurable here). Any use of this or a new extension needs the DECL-P4-24 item 2 path and its own render declaration.

[line withheld: prize-candidate detail under review]
- utc: 2026-09-27T07:09:44Z
- prev_sha256: 8dd73bf67c87a9aff22e416ceb07c9a72372cd1a7759193fbbbf2f7877677584
- kind: result
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
Numbers:
- 138 census tiles; 18 sessions, all valid.
- N0: 18 tiles, all 0 letters; p99 0; threshold 5.
- Rows Y: 12. Positives: 3, each isolated, none labelled-adjacent:
  - r2 c12: 5 letters, 0 firm;
  - r4 c10: 6 letters, 0 firm;
  - r4 c12: 5 letters, 1 firm.
- Sub-threshold rows-Y tiles scatter over c4-c15 (0-3 letters each).
Internal gate (>= 20 % of non-blank tiles positive): 3/138 = 2.2 %, FAIL. The strip is UNINFORMATIVE, not a null; no locator.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]

## METRIC-HASH-40
- utc: 2026-09-27T07:13:21Z
- prev_sha256: 287511a3afa945c94e56d9d634096c02ec4616c178d1719a00b2c551a9de4af3
- kind: metric-hash
METRIC-HASH-40: DUAL_FREEZE, the 78/137 keV dual-energy method (DECL-P4-16 item 3), frozen on the control strip w028-037 only. Recorded before any title-zone dual-energy number exists; p4-purple reports none.
File: logs/sib/p4-purple/DUAL_FREEZE.md (p4-purple 5cbe4f21; from p4-purple-de 6d12337). Its section 7 lists sha256 of every tool and data file.
Key frozen facts (numbers only):
- 137 keV coverage: 3.01 % of w010-027 valid vertices; r3 c10-c17 at 14-27 %.
- Registration: held-out residual median 1.72 um; sheet-surface median 2.36 um.
- Statistic: z of (C137 - k C78 - k0), k 0.67947; hotspot |z| > 3.0696 and on-sheet.
- Control false-positive rate: 0.0215 per patch. Known-text carbon ink vs blank: AUC 0.483 (no composition difference, as expected).
- Injection recovery >= 0.8 at <= 20 um: only CuO, gold and orpiment (10-20 um).
- NOT detectable at <= 20 um: Tyrian purple (0/50/90 % Br loss), purpurissum, alumina and gypsum lakes, carbon ink, red ochre, cinnabar, lead white.
Consequence for the register (owner's "purple" question): a purple (organic dye) title is untestable by the CT data available, whether single- or dual-energy. A dual-energy null means "untestable", never "absent".
Application: allowed once, unchanged, on the 137 keV overlap of the title zone (r3 c10-c17 and any other overlapping w010-027 tile), by p4-purple's sub-sibling. It reports hotspot counts and cluster sizes per tile, against the control false-positive rate of 0.022 per patch.
```
93d04a4d0bbba551fe0d648b64904e3491ed15981047c36568472cdee48f9427  logs/sib/p4-purple/DUAL_FREEZE.md
```

[line withheld: prize-candidate detail under review]
- utc: 2026-09-27T07:23:14Z
- prev_sha256: 944d4bb3956d02bd83d9d11e0bc483f02446e93f3aba55fec29191895af32a6c
- kind: result
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
Numbers:
- 132 census tiles; 17 sessions, all valid.
- N0: 17 tiles with letters 0 x13, 1, 1, 3, 4; p99 3.84; threshold 5.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
  - c11-c13 (5 tiles): 5-9 letters, 0-5 firm.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
- the rule applied mechanically, with outward = decreasing column on every strip (p4-inner direction.json);
[line withheld: prize-candidate detail under review]
Descriptive only (UNCERTAIN; not a declared test, noted after the counts):
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]

## P4-22-RESULT
- utc: 2026-09-27T07:29:35Z
- prev_sha256: deec1a655e978f14c877fb7f9a30b5437d3d6ad656e7f18768c5bbc1cd12aa7e
- kind: result
P4-22-RESULT (DECL-P4-22): the local re-trace of the low patch (strip-a r5-r8 x c14-c19) is NOT ADOPTED. Report: tracer logs/sib/tracer/p4-22/REPORT.md at 0810b324. Geometry only.
- Self-intersection pairs touching P: 1720, against 1148 for the official mesh; the gate requires 0. FAIL.
  - Every crossing involves re-traced quads.
  - The tracer fails where the official mesh is defective: compressed zones where the 9.6 um surface prediction does not separate the windings.
- Seam: 4.17 vox, against 4.65 for the official mesh (pass).
- Neighbour winding (0.942 vs 0.889) and flattening (87.6 % vs 64.4 %) pass, but only because 69 % of the hole vertices were left unfilled (fill 31 %). These are not evidence of a better surface.
Per item 3, the metrics are recorded and the task stops. There is no P4-O or P4-OWN inference on this patch, and no read.
Register: "beside c14-c17, low, r4-r5" and the low rows r5-r8 of c14-c19 stay testable only on the official mesh, whose windings are locally unresolved there. Any ink found there would carry that caveat.

## P4-24-HOLES-RESULT
- utc: 2026-09-27T07:29:35Z
- prev_sha256: bb2899d49e86826640a4b59c4609342c4f3380072b5c224a0db6d685695963ea
- kind: result
P4-24-HOLES-RESULT (DECL-P4-24 items a-d, and e as declared; e2 pending). p4-core logs/sib/p4-core/holes.json at 627b42fc (180 tiles, r0-r8 x c0-c19). Numbers only.
- (a) Interior holes: 0 in the whole grid. The official mesh has no hole anywhere in the title strip.
- (b) Zero or missing surface-volume input inside mesh-valid pixels: at or below the c0-c8 reference in every c9-c19 tile.
- (c) Stretched or crushed renders: flagged r6_c15, r6_c18 and r7_c16, the same patch as the L10 self-intersections (P4-22-RESULT).
- (d) Mesh off the papyrus (no sheet peak within +-60 um): r2_c19 37.5 % and r5_c18 22.5 % of sampled vertices, outside the reference range. Every other c9-c19 tile is within it.
- (e) Straight edge extrapolation, as declared: 22 r0/r8 tiles flagged, but the c0-c8 reference behaves identically. It is not specific, as p4-core's validation predicted (DECL-P4-24-A1). The sheet-following (e2) validation is running.
Consequences:
- The owner's question ("holes in the mesh that were rendered incorrectly?"): there are no holes.
- Two tiles render partly off the papyrus: r2_c19 (37.5 %) and r5_c18 (22.5 %). Ink on those parts of the sheet would not appear in any render so far.
- r5_c18 lies in the patch whose re-trace failed (P4-22-RESULT).
- r2_c19 is new, in the "further, c18 and beyond" cell (0.12). Per DECL-P4-24 item 2, tracer re-traces it under the DECL-P4-22 gate: holes = off-sheet vertices dilated by 1.9 mm, with clean official vertices fixed. It is adopted only if 0 self-intersections, and seam, neighbour winding and flattening are no worse than the official mesh.

## METRIC-HASH-41
- utc: 2026-09-27T07:36:37Z
- prev_sha256: 73413198928a52e3627b04b7977965bf5f5260a93ffde1a4b8507d9dda4b7180
- kind: metric-hash
[line withheld: prize-candidate detail under review]
Checks:
- A0: code hashes. A1: commit A precedes commit B. A2: SHA256SUMS and key sha.
- K1: candidate set, (strip, r, c) and image sha equal the orchestrator's select and the census keys.
- K2: the N0 set equals the deterministic p4_phase2 draw (seed NULL_SEED + _bidx(batch) over the sorted rot-0 census tiles of the pool batches, minus candidates and PC pool). Every N0 image is recomputed byte-exact as png_bytes(rot90(source tile)), with the source fetched from p4-inner and sha-checked against the census key.
- K3: PC files are in the pool, with sha equal to the PC manifest.
- J: session composition (<= 4 cand + 4 N0 + 1 PC), coverage (each cand and N0 file in 3 sessions, each PC in 1), brief template equal to the frozen task text of the variant.
- B1-B3: as rh_verify.py.
Negative tests at pin time: a select with one candidate's r changed gives K1_cand_set FALSE; a wrong batch name fails closed.
[line withheld: prize-candidate detail under review]
```
98dbeac9f3852eeac6dbc8dfb932b3b108870c7a5b5b6786f45b4542a91222b9  tools/p4/rh_verify_p2.py
```

[line withheld: prize-candidate detail under review]
- utc: 2026-09-27T07:38:50Z
- prev_sha256: 2b0dad8e0cd0b9d7fb04a11ca4abca68e87d3ae5f9e914cc39115831adc0abba
- kind: result
[line withheld: prize-candidate detail under review]
- Independently verified with rh_verify_p2.py (METRIC-HASH-41): 15/15 checks PASS, including the exact recomputation of the N0 draw and the N0 images. rh-e2 commits A 2335c73f and B dbf1fe3d. Installed.
[line withheld: prize-candidate detail under review]
- 15 sessions used; 0 void; 0 invalid. N0: 20 tiles x 3 readers; best-pair agreement max 0.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
Not candidates:
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
Next: DECL-P4-25-A2 (extended test and a pre-registered layout discrimination). Eligibility: these tiles are 11-14 mm or more from the labelled segments; M1 outputs there do not overlap its training data.

## DECL-P4-25-A2
- utc: 2026-09-27T07:38:50Z
- prev_sha256: 15cf00da37b1e7331c74fe907833763be65d5236f7e82ee35b4195d8fa633671
- kind: declaration
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
   - p4_ext.py build semantics unchanged: U = the phase-2 candidate file; R = U rotated 90 degrees clockwise; 18 sessions, 9 U and 9 R; 8 N0 per session, each N0 tile in exactly 3 sessions; 1 PC per session.
[line withheld: prize-candidate detail under review]
   - PC: the M1 w028-037 pool (logs/p4/pc_pool_m1).
   - Harness: rh-e2 under DECL-REMOTE-HARNESS-1: commit A per batch before its readers; commit B sealed.
[line withheld: prize-candidate detail under review]
   - Scoring: p4_ext.py score, unchanged. EXT-CONFIRMED needs (i), (ii) and (iii) per candidate. Each candidate is reported; one confirmed candidate suffices for "a blind-reader lead that passed a pre-declared extended test".
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
   - Before any number exists, p4-titulus pre-registers (QA.md Q6) which widths, gaps and pitch discriminate (a) "text column" (width about 6.2 cm, intercolumn about 1.7 cm, pitch 7.9 cm; CERC54-LAYOUT-RESULT) from (b) "initial-title block" (as it specifies from the literature), and a decision table. The table is committed before p4-layout computes.
   - The result is descriptive and cannot make or break a candidate. EXT-CONFIRMED alone decides candidacy, and papyrologists decide title vs text.
3. Guardrails:
   - No image is viewed by the orchestrator or any builder.
   - No letter identity leaves the scorer.
   - The EXPECTED-TEXT quarantine stands.
   - Any owner-facing package states "one model family; no title word named; title vs text for papyrologists".

## METRIC-HASH-42
- utc: 2026-09-27T07:44:12Z
- prev_sha256: 9b93818330519c4d601e11bf639f0dec102a25ce16d4d97a35078fdd1709ec31
- kind: metric-hash
[line withheld: prize-candidate detail under review]
- Predictions:
  - (a) text column: W 5.5-7.0 cm; G_in 1.3-2.2, or 8.8-10.8 with one invisible column; pitch 7.0-8.8 or 14.0-17.7; line pitch 6.0-6.3 mm; left-aligned lines.
  - (b) initial-title block: W 2-5.5 cm; G_in 9-14 cm (up to 26); open blank outward; pitch 11-19.5; 2-6 centred lines; line pitch 6-9.5 mm.
- Decision table: rows W, G_in, P, G_out and row consistency, scored -1/0/+1. A sum >= +3 favours (b); <= -3 favours (a). Descriptive only (DECL-P4-25-A2 item 2).
- Fixed in advance: P of about 14 cm cannot decide alone.
[line withheld: prize-candidate detail under review]
- Also fixed: the red-team caveat that (b) requires the traced sheet outward of B (about 1 m) to be mostly damaged or unreadable rather than blank.
- Conditional L6 table: EXT-CONFIRMED with layout (b) gives about 0.6; EXT-CONFIRMED and undecided about 0.3; not confirmed about 0.07 baseline.
```
de2f03357935e26ea6e08975782addea807afc820761641e9c7d1a87afbb2de3  QA.md section Q6 (extracted from "## Q6" to end of file)
```

## P4-24-E2-RESULT
- utc: 2026-09-27T07:50:02Z
- prev_sha256: 12e9be1d19fb81a7b1dbae87e441c2d4966613e77b33bb955c5c4497035adfd7
- kind: result
P4-24-E2-RESULT (DECL-P4-24-A1): the sheet-following edge test is NOT VALID and is not applied. p4-core commit d42235d7. Geometry only.
- Validation into the known mesh (mean offset <= 30 um at 2 mm on >= 80 % of columns): v1 2.3 %, v2 12 % of columns. FAIL.
- Per DECL-P4-24-A1 item 2, (e2) is not applied, and item (e) stays "not specific beyond about 1 mm". No bar is changed.
- Combined with P4-N-RESULT (sheet continuation of about 2 mm in c9-c14; published mask ends at +3 to +5 mm): whether papyrus continues above the official edge in c15-c19 is UNRESOLVED with the available methods. In c9-c14 it continues about 2 mm at most.
- The top-edge register cell keeps p4-titulus's formula with L of about 2 mm, P about 0.04. c15-c19 are unmeasured.
p4-core proceeds to the DECL-P4-26 facing meshes.

## METRIC-HASH-43
- utc: 2026-09-27T07:54:32Z
- prev_sha256: 40e806febd973d0b8b013ef9491dd472c30f1b44297fa9cf47551dd3bde48b4f
- kind: metric-hash
[line withheld: prize-candidate detail under review]
Checks:
- A0-A2 (as rh_verify.py);
- E1: U is the phase-2 candidate file at (strip, r, c), with image sha equal to its census src;
- E2: R is byte-exactly png_bytes(rot90(U source tile));
- E3: the N0 set equals the deterministic p4_ext draw (SEED 20260927 + _bidx(batch), N_N0 48, pool batches minus the candidate source, the PC pool and the phase-2 N0 sources), and every N0 image is recomputed byte-exactly;
- E4: PC in the pool, with sha equal to the manifest;
- J: 18 jobs, 9 U and 9 R, 8 N0 and 1 PC each, each N0 in exactly 3 jobs and never twice in one, brief template and sha;
- B1-B3.
[line withheld: prize-candidate detail under review]
```
dc1f8538e3881e56b5559d54b73f12c5ac83d17a77bd577e122037b5111084d2  tools/p4/rh_verify_ext.py
```

## P4-21-RESULT
- utc: 2026-09-27T11:01:19Z
- prev_sha256: bebd3f134728ded4d89fd12bc31fd06cce8d8f5a94756cb8ca3310c5053b632c
- kind: result
P4-21-RESULT (DECL-P4-21, -A1): organizer ink-label fractions on the title zone of 20260701183124-w010-027 (strip-a r0-r5 x c9-c19). Numbers only.
Source: p4-excl logs/sib/p4-excl/label_fractions.json at 7ea9f34a. Labels are the official 20260918 set (ink-labels/2.4um-volume-20260411134726), read in code only. Mapping: tile vertex to the exact closest point on the segment surface, tolerance 20 vox (0.048 mm).
Per tile, coverage = the fraction of samples with label supervision (any segment); ink = the ink fraction of the covered samples.
- (a) col. -1 anchor, c11-c13 x r0-r1: coverage 0.05-0.29, ink 0.19-0.34 (r0: c11 0.11/0.30, c12 0.24/0.19, c13 0.14/0.34; r1: c11 0.29/0.21, c12 0.19/0.23, c13 0.05/0.23). The organizers' own labels mark ink in the short last column. This confirms the CERC54-LAYOUT-RESULT anchor independently of any of our reads.
- (b) the expected title slot, c14-c19, r0-r5:
  - coverage is 0 in every tile except r0 c14, which has 0.00097 (141 of 145132 samples, segment 20231016151002), with ink 0.60 of those. That is about 84 samples at the tile's outer edge, next to col. -1.
  - The organizers labelled nothing in c14-c19: neither ink nor blank. The slot was never annotated.
- Also: c9-c10 r0-r3 coverage 0.00-0.22, ink 0.11-0.41; r2-r5 c11-c13 coverage 0.
Consequence: the organizers' labels end at col. -1. Their statement that the title region shows "no detectable ink" concerns model output on an unlabelled slot, which is consistent with our own nulls there (M1, W1, P4-F, L-channels).

## METRIC-HASH-44
- utc: 2026-09-27T11:06:49Z
- prev_sha256: d0d1eb5b2517fd1428898a7369852a3efe79a6332a9184d95487ca1670bcfc89
- kind: metric-hash
[line withheld: prize-candidate detail under review]
R2 applies only when the job's attempt-1 answer is absent. <job>.r2.age may then stand in if:
- the attempt-1 audit entry is invalid with age_exists False, and its transcript has no sealed write;
- the attempt-2 audit entry is valid;
- B1-B3 hold for the re-run: its transcript's first prompt equals the commit-A brief, its timestamps follow commit A, the hashes match, and the answer equals the sealed heredoc.
At most one re-run per job (DECL-P4-3 item 3: one re-run of a void or invalid session). Install writes the re-run answer as the job's answer, with attempt 2 recorded.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
```
13d759b629be3d65400f5bd5014cc71abe743c730516e44098e16dc6f3244efd  tools/p4/rh_verify_ext.py
```

[line withheld: prize-candidate detail under review]
- utc: 2026-09-27T11:23:26Z
- prev_sha256: a1e0c5604ff44abe0af2978768bd06f7fb2c77ca211eabf28139119064f5b4cc
- kind: result
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
Outcomes (U triples; R triples; N0 max; U-vs-R mean pairwise; p):
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
- SG 1c spirit (max U triple - N0 P99, bar 10): 11 / 8 / 3 / 4, reported and not a criterion.
Disclosures:
- The three confirmations are ONE 2 x 2 tile lead with continuous lines, read by one model family. They are not three independent confirmations.
- 46-48 of 48 N0 tiles per batch have census < 5 letters, so criterion (i) is mostly a rotated-blank comparison. The rotated-self arm R is the stricter control.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
Geometry (auditor, check5; 53.40 display px/mm):
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
- Q6 table, applied mechanically: W -1, G_in 0 (3.6 cm fits neither; flagged), P -1, G_out 0 (no outward baseline), row consistency -1. SUM -3: "layout favours (a) text column", exactly at the boundary.
- Q6 section 3: R 1.09 favours (a); extent ratio 1.26 favours (a).
Reading:
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
- Per p4-titulus Q6 section 4: P(initial title) is about 0.07, and L6 is about 0.08.
- Per DECL-P4-3 item 4 it goes to the owner as "a blind-reader lead that passed a pre-declared extended test": one model family, no title word named, title vs text for papyrologists, and the layout evidence favours text.
- It is NOT proposed as a Title Prize submission on this evidence.
[line withheld: prize-candidate detail under review]

## DECL-P4-25-A3
- utc: 2026-09-27T11:23:55Z
- prev_sha256: b44afcf5db724e524c50f87058809bc3681905c699a2555c094a50dcb46894ce
- kind: declaration
[line withheld: prize-candidate detail under review]
Basis:
[line withheld: prize-candidate detail under review]
- By p4-titulus Q5 (b) and Q6, an initial title sits 12-25 cm (up to 28) outward of col. 1, in the initial agraphon.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
2. Material: P4-OWN (DECL-P4-23) S-arm maps, the 3 seeds. They are made only after P4-OWN passes its own G1 gate on known text.
   - The outer strips are not in P4-OWN's training zone T, so its outputs there do not overlap its training data (prize rule).
   - M1 (organizer) maps of O are reused only as a second material under its own N0.
[line withheld: prize-candidate detail under review]
4. Reads: remote harness; sigma2t census (8+1 sessions; N0 rot-90 from O's own batch). Also DECL-P4-17 block-variant 4 x 4 cm windows over O, for enlarged or ornamented title letters (METRIC-HASH-38 brief).
   Candidates: every census positive in O and every block-variant window with >= 5 letters+marks above its own N0 threshold. They go through phase 2 and the extended test, unchanged (DECL-P4-2 item 6, DECL-P4-3), with N0 from O's batches only.
5. Layout for any EXT-CONFIRMED O lead: the Q6 decision table unchanged (METRIC-HASH-42). Under (b), the outward blank must be ≥ 8 cm or open.
6. Roles: own-lead (maps, after G1); rh-e2 (harness); p4-layout (profile); the orchestrator verifies (rh_verify / rh_verify_p2 / rh_verify_ext as pinned) and scores.

## DECL-P4-26-A1
- utc: 2026-09-27T11:55:31Z
- prev_sha256: 7890dbc32294f04451e2fe55e8fd36dc032f346ed4d7b483cb08afddfa58ccff
- kind: declaration
DECL-P4-26-A1: facing-surface rule, amended after the first tile (p4-core ASK 5, commit 5743b418). Declared before any regularised facing number exists. The DECL-P4-26 gate is unchanged: 0 self-intersections and >= 80 % of vertices found.
Basis:
- On r0_c11 the declared per-vertex rule found a peak on 97.3 % of vertices, but gave 137 self-intersections.
- The gap had median 77 um against a sheet spacing of about 165 um. The first peak often lies on the own sheet's second fibre layer, not the neighbour sheet.
- The declared run continues unchanged and is reported per tile, as declared.
1. Regularised rule (p4-core's proposal, adopted):
   (a) the facing peak must lie >= 0.6 x the local neighbour-winding spacing (mesh_audit) beyond the own peak;
   (b) among those peaks, take the one nearest the 9 x 9 median-filtered facing offset of step (a), within +-20 um;
   (c) drop isolated vertices differing by > 20 um from that median.
2. Added independent check (v): the official w010-027 mesh already traces the neighbouring winding.
   - For every facing vertex, report the point-to-surface distance to the official mesh's nearest OTHER-winding surface.
   - Pass: median <= 40 um, and >= 80 % within 80 um.
3. Order: validate on the control tiles r0-r5 x c3-c8 first. The rule is accepted only if the controls pass the gate AND check (v). Only then apply it to r0-r5 x c11-c19.
4. Fallback, if the regularised rule fails on the controls: the facing surface is the official neighbour-winding surface itself, i.e. the official mesh's vertices of the adjacent inner winding at the same angle. It is used for vertices whose normal ray meets it within 250 um, and is sampled on its outer face (the side facing the title tile) with the layer order reversed.
   - The DECL-P4-26 gate applies to that patch too: 0 self-intersections (as an official mesh region), >= 80 % coverage.
   - It is recorded as "fallback (4)".
5. Everything else in DECL-P4-26 is unchanged: the mirror, controls, null, candidates, eligibility, and the model-gate precondition.

## P4-24-RETRACE-RESULT
- utc: 2026-09-27T12:37:18Z
- prev_sha256: 01db806cabdf01557f1f13d03805895a6d348c39c2686615c9106868e44f9cea
- kind: result
P4-24-RETRACE-RESULT (DECL-P4-24 item 2; the DECL-P4-22 gate): re-trace of strip-a tile r2_c19 (w010-027) is NOT ADOPTED. Tracer report at 37cae451. Geometry only.
- Off-sheet fraction by dense profiling: 22.3 % of r2_c19 vertices. p4-core's 40-vertex sample gave 37.5 %. The holes (off-sheet dilated by 1.9 mm) cover 99.97 % of the tile.
- Re-trace: fill 2.3 %; 1 self-intersection (the gate requires 0); seam worse than the official mesh. The m7 L2 surface prediction supports a sheet on only 39 % of this tile.
- Per DECL-P4-22 item 3, the metrics are recorded and the task stops. There is no render and no read on a re-traced r2_c19.
Consequence: the r2_c19 region (c19 = the blank-end side, the register cell "further, c18 and beyond") stays testable only on the official mesh, with 22 % of its surface off the papyrus. Any null there carries that caveat.

## METRIC-HASH-45
- utc: 2026-09-27T13:07:57Z
- prev_sha256: d6c9ee696c9e7a7c88091fed112f8d087ee012d8739bd41bcb211cec74dcb79e
- kind: metric-hash
METRIC-HASH-45: P4-OWN RECIPE.md (DECL-P4-23 item 4), frozen by own-lead. It was added in commit 6b5bdc57 at 2026-09-27T13:05:31Z, on branch claude/gifted-bell-gavnl5-sib-own-lead, before any training log or map. The arm start is recorded in SUBSIBS at 13:06:34Z. Pinned here before any P4-OWN map exists.
Key frozen items:
- cfg A 3-D-to-2-D CNN (232,697 params, random init), 256/192 px, output stride 4, batch 16, 2500 steps, AdamW with cosine schedule;
- 4000 patches, all ink >= 2 % (disclosed: a single sampler pool);
- seeds: F1-F3, S1 and NULL 20260927; S2 20260928; S3 20260929;
- NULL derangement n 4000, fixed points 0;
- fold held-out lists of 24 tiles each, mostly w028-037;
- code sha256 listed in its section 8;
- recipe_final.json sha256 7b484b80...
Disclosures carried from the RECIPE:
- F2 trains on 1230 patches;
- there is no inter-fold spatial buffer beyond the whole-window rule, so the F AUCs may be optimistic;
- min_dist_to_X = 1.2 mm is the certified bound.
Therefore the col. -1 local check (DECL-P4-23 item 6(c)) is the decisive unbiased sensitivity test for any X interpretation.
```
377784c2bd8dd8617f38ae0e054fbe37684004f6e0d105852e84e16c16a6dfb8  logs/sib/own-lead/p4own/RECIPE.md
7b484b80185c4e10ca39f7678d4a4d0feef4acdc1c1b0f17b51099ea7d64c993  logs/sib/own-lead/p4own/recipe_final.json
```

## METRIC-HASH-46
- utc: 2026-09-27T13:12:36Z
- prev_sha256: c1bc1c3e855c08f4288fe7ad22fb18a59513091033c19bcc2604fec9928aab56
- kind: metric-hash
METRIC-HASH-46: P4-OWN RECIPE-A1, an implementation-only fix to train.py (own-lead c23037b6, 13:11:25Z). Recorded before any training step completed and before any map exists.
- Fault: load_data materialised the 17 GB of memory-mapped shards; the first S1 launch was OOM-killed with 0 training steps.
- Fix: a lazy index over the mmapped shards. Item i equals np.concatenate(parts)[i], with a unit test in test_own.py (ALL OK).
- Batches, schedule, loss, optimiser, seeds and every RECIPE.md parameter are unchanged. All other code stays at 6b5bdc57.
- No bar or declared rule changes. RECIPE.md (METRIC-HASH-45) stands, with train.py replaced by:
```
9a8ad9b2e83191fb42cb423db4b0e4e35cd213921ba1578db760d5b879c31c56  tools/sib/own-lead/train.py (RECIPE-A1; supersedes 2943cac4...)
```

## METRIC-HASH-47
- utc: 2026-09-27T14:19:10Z
- prev_sha256: 3adfa6034744dd5bde55de0b812f0b86e788ec8c1bcea41c304e6ca9f179f1d3
- kind: metric-hash
METRIC-HASH-47: ckpt-screen-b's P4-O input reader, reviewed by the orchestrator and committed verbatim to the orchestrator branch. The P4-OWN arm workers can then import it from their base branch, instead of checking out another sibling's code, which their permission layer refused as untrusted code integration (own-s2 ASK-1; not routed around).
Files, byte-identical to ckpt-screen-b commit 98cd075, with sha256 equal to own_common.CKB_SHA:
- tools/sib/ckpt-screen-b/p4o_tiles.py (369 lines);
- tools/sib/ckpt-screen-b/infer_1667.py (343 lines).
Review (static):
- p4o_tiles reads the public Vesuvius open-data S3 over HTTPS (requests; curl for meshes), runs git show of a manifest, and writes only its own work and checkpoint files.
- infer_1667 loads the PHerc.1667 checkpoint with transformers AutoModel(trust_remote_code=True) inside a function that P4-OWN never calls. P4-OWN uses only the reader.
- No other network target, shell command or destructive operation outside its work directory.
- No rule, bar or recipe changes.
```
a32d7e86a7bdfd5a25a5ced280976a2dfa55f30c8b866a3ae149d74b729ec371  tools/sib/ckpt-screen-b/p4o_tiles.py
29444f37ffb43669b1842570b123a5f791dd9d0f8aa7a4a07b8f776ed148cb12  tools/sib/ckpt-screen-b/infer_1667.py
```

## P4-DE-RESULT
- utc: 2026-09-27T14:20:31Z
- prev_sha256: 1981d18eb4601170589cf8835e0b029d53840e30d2cf78561598467f24509456
- kind: result
P4-DE-RESULT (METRIC-HASH-40, the one-shot title-zone application). p4-purple 674d59da; de c371b1c title_zone.json. All 15 frozen tool sha256 values match; only apply.py was added, pushed before any number. Numbers only.
- r3 c10-c17 (the 137 keV overlap): 11,674 patches used. 1 hotspot (z < -T, r3_c11, isolated); 0 with z > +T; largest cluster 1. Rate 0.0001 against the control FPR of 0.0215: NULL.
- Caveat (p4-purple): that rate is about 200x below the control FPR (z p99 2.0-2.3 vs 3.2-3.5 on r3 c0-c9). The z scale does not transfer exactly, so the null is conservative and does not show the method's sensitivity there.
- Outside the title zone, r4 c0-c7 show z > +T on 33-96 % of patches. This is a disclosed artefact: the lower end and cylinder edge of the 137 keV volume lie outside the control domain. r3 c0-c9 rates are 0.012-0.023, consistent with the FPR.
- Meaning: no Cu, As or Au layer >= 10 um on the covered 14-27 % of r3 c10-c17. A purple or lake-dye title there is "untestable by dual energy", not "absent" (METRIC-HASH-40).

## P4-OWN-S1-COLM1-AUC
- utc: 2026-09-27T18:11:24Z
- prev_sha256: 2ac6e6182d7a8d03b9e6929a315b83b2016f21c71d4e629b4f5fbdd1fa7a0c48
- kind: result
P4-OWN-S1-COLM1-AUC (DECL-P4-23 item 6(c), descriptive; not a bar). p4-excl colm1_auc_S1.json at bd3d5949 (sha256 f27f4d78...). Arrays: own-lead 40057dc6, logs/sib/own-s1/maps/arrays/. Computed in code only (DECL-P4-21-A1); no X label value was written.
- S1 (all of T, seed 20260927; trained 2500 steps, final loss 0.563), on col. -1 (w010-027 c11-c13 x r0-r1). Col. -1 lies inside the excluded title zone X and was never trained on.
- Pixel AUC against the organizer 20260918 ink labels: pooled 0.978 over 6 tiles (3,989,840 label-covered 4x4 blocks, 942,468 of them ink). Per tile 0.96-0.98 (e.g. r0 c11 0.959, r0 c12 0.978).
Reading: the model separates the organizers' labelled ink from labelled non-ink on held-out papyrus directly beside the expected title slot. Its local sensitivity to this scroll's carbon ink is high. Still to come:
- NULL (label-deranged) AUC on the same pixels (expected about 0.5);
- the census condition (>= 2 of 6 col. -1 tiles rows Y in >= 2 of 3 S seeds);
- G1 (F-arm held-out legibility).
No X tile is interpreted before these.

## P4-26-FACING-GEOMETRY-RESULT
- utc: 2026-09-27T19:30:36Z
- prev_sha256: 9cca11e5ce225fadd936ff88064b579ad89fae3eb67f8f07fa9002f144d1f5c0
- kind: result
P4-26-FACING-GEOMETRY-RESULT (DECL-P4-26 item 1, as amended by DECL-P4-26-A1). Geometry only; no facing-surface image, render or read exists. Source: p4-core 7fae9a19, logs/sib/p4-core/facing/fallback4.json (sha256 8011a4bb2f205a5b9e7c4eab6b2951d9534f75ae90564ab9d167ced30e34159d); offsets in fallback4_sface_um.tgz.
1. Declared naive rule (DECL-P4-26 item 1): FAILS the gate on every tile evaluated (r0_c11: 137 self-intersections; controls 409-5862; check (v) medians 76-149 um).
2. Regularised rule (A1 item 1): REJECTED on the controls (only 56-61 % of vertices found; >= 80 % required). Per A1 item 3 it is not applied to the title windows.
3. Fallback (4) (official adjacent inner-winding surface, within 250 um, outer face):
   - Controls r0-r5 x c3-c8: 18/36 pass the gate (coverage median 0.81, range 0.44-0.97; 2 tiles, r1_c4 and r1_c5, have 29 official-patch self-intersections). Median gap 157 um.
   - Title windows r0-r5 x c11-c19: 32/54 pass (coverage median 0.84, range 0.53-0.95; 0 official-patch self-intersections). Median gap 137 um.
   - Title-slot c14-c17 tiles passing: r3 c14-c17, r4 c14-c17, r5_c14, r0_c17, r1_c17 (11 of 24). Failing: r0-r2 c14-c16, r2_c17, r5 c15-c17 (coverage 0.67-0.80).
   - c19 fails in every row (coverage 0.53-0.65), so the DECL-P4-26 item 3 facing null is c18 (6/6 pass) plus the per-batch rot-90 N0.
   - Col. -1 facing (c11-c13 r0-r1): r0_c11, r0_c12, r1_c11, r1_c12 pass; c13 fails.
4. Distortion caveat (disclosed; it changes no bar): the resampled rendering grid is NOT free of self-intersections even where the official patch is (per tile 42-4922 on controls, 75-10724 on title tiles). Flattening quads within 5 % area: median 43 % (controls) and 41 % (title) on gate-passing tiles, minimum 19 %; area-ratio-bad fraction <= 0.046. Consequence: before any facing render, a declaration must fix the render grid (for example, sampling on the official patch vertices directly) and require 0 self-intersections on the grid actually sampled. No facing render is made until then.
5. Still queued, unchanged: facing inference only on gate-passing tiles and only after a model material's own gate passes (P4-OWN G1). The positive-control condition (>= 20 % of the non-blank gate-passing control tiles are census positives, else "uninformative") applies to the 18 passing control tiles.
Meaning: the offset (mirror-text) channel can reach 11 of 24 title-slot tiles, mainly the lower rows r3-r5. It cannot reach r0-r2 c14-c16, because the inner neighbour there lies > 250 um away on more than 20 % of vertices. Any facing null there is "not reachable", not "absent".

## DECL-P4-23-A1
- utc: 2026-09-27T19:31:31Z
- prev_sha256: 67a86ff3da61d432edf8c12fe2fc59dbbee3be74c35105553f922e3f87702424
- kind: declaration
DECL-P4-23-A1: scheduling and futility rule for the P4-OWN legibility gate G1 (DECL-P4-23 item 6(b)). Declared before any F-arm held-out map exists (F1 is still training; own-lead 8a45ed0b). The G1 bar is unchanged: >= 30 % of the non-blank F-arm held-out tiles must be rows Y with >= 5 letters (DECL-P4-12 item 2 formula), sigma2t and block variants, remote harness rh-e1.
1. Batches: one census batch pair per fold (census_own_f1, census_own_f2, census_own_f3; sigma2t and block), each built from the RECIPE.md held-out list of that fold (24 tiles each, fixed at 6b5bdc5). Renders, briefs and scoring are identical across folds. A batch starts as soon as its fold's 24 held-out maps are pushed.
2. G1 is decided once, pooled over the non-blank held-out tiles of all three folds. No per-fold verdict is recorded, and no fold is re-rendered, re-read or dropped.
3. Futility stop (a bar can only be failed early, never passed early): after scoring k < 3 folds, if the pooled rows-Y count cannot reach 30 % even if every non-blank tile of the unscored folds were rows Y (non-blank count for an unscored fold taken as its maximum, 24), G1 is recorded as FAIL at once and the remaining F arms are not needed for G1.
4. Early PASS is not allowed: even if the scored folds alone already exceed 30 % of the pooled maximum, G1 waits for all three folds.
5. Everything else in DECL-P4-23 is unchanged (NULL control, col. -1 census condition, seeds, eligibility, X only after G1).

## METRIC-HASH-48
- utc: 2026-09-27T20:45:18Z
- prev_sha256: e62db534ebfb3b67a7f85de2896172fa23b393e1ee657762d393e7199c753a9d
- kind: metric-hash
METRIC-HASH-48: P4-OWN G1 harness code, pinned after orchestrator review and before any F-arm held-out map or census batch exists (DECL-P4-23 item 6(b), DECL-P4-23-A1, DECL-REMOTE-HARNESS-1).
- rh-e1 c031c8d4 (pushed 20:43:25Z, before any real map):
  - tools/sib/rh-e1/prep_own.sh sha256 f30807ac49bdd589d782813ac51ac48a8a5350691f9fbe4cdc2b33908d3e9fa3
  - tools/sib/rh-e1/own_split.py sha256 626cdbb47b1f89e2c3f33e8ff83439f5b4aff9bce44ea94b0c6836c6d5de7d0c
  They call only the orchestrator tools tools/p4/norm_manifest.py and tools/p4/p4_jobs.py (import, null, jobs sigma2t and block). own_split.py adds a top-level 'segment' to per-segment copies of the manifest (tile records unchanged) in a local, deterministic, never-pushed commit (fixed author, committer and dates), so the split commit id is reproducible by the verifier.
- own-lead bb5ef4bc: tools/sib/own-lead/run_arms.py sha256 07633449969a8f889898d447edc29b8d270278334749eba24f5aa1e084f19980. Scheduling only (F held-out tiles first; train F2, F3, NULL, S2, S3). NULL was stopped at about 20:43Z before its first checkpoint and restarts from step 0. train.py, infer.py, auc.py and recipe files are unchanged.
Review notes, which the orchestrator's verification of every G1 batch checks, beyond A0-A5 and B1-B3:
1. The manifest's tile set equals the RECIPE.md (6b5bdc5) held-out list of that fold, 24 tiles; own_split.py itself only asserts eligible <= list. Any missing or ineligible tile is reported, and it counts toward the DECL-P4-23-A1 item 3 futility maximum, never silently dropped.
2. manifest arm and model_final_sha256 match that arm's training summary on own-lead.
3. Every census PNG sha256 equals the own-lead record's png_sha256. N0 images are recomputed byte-exactly.

## DECL-P4-23-A2
- utc: 2026-09-27T20:46:46Z
- prev_sha256: a051c1ad3408f8be2c61d34caa76524a1e91a22d9ff1d000408795530aaeb291
- kind: declaration
DECL-P4-23-A2: how G1 counts, fixed before any F-arm held-out map, census batch or score exists (F1 held-out maps not yet pushed; own-lead bb5ef4bc). It resolves two points that DECL-P4-23 item 6(b) left implicit. Each is resolved by the stricter or the precedented reading. No bar is lowered.
[line withheld: prize-candidate detail under review]
2. Variants: sigma2t and block are two channels, each with its own G1, as DECL-P4-17 item 3 treats every block channel.
   - G1(v) counts a tile iff its variant-v census answer has rows == 'Y' and n_letters >= 5. This is the literal DECL-P4-12 item 2 formula; for block, n_marks is NOT added.
   - G1(v) passes iff that count is >= 30 % of the pooled non-blank tiles of F1-F3.
   - X tiles are interpreted only in a variant whose G1 passed. If neither passes, P4-OWN is "uninformative".
   - Futility (A1 item 3) is applied per variant. The remaining F arms are skipped for G1 only if both variants are futile.
3. Per-batch N0 (p99) is computed and reported per job set, as usual. It does not enter G1, which is a known-text sensitivity bar, not a candidate rule.
4. Scoring: tools/p4/score_p4.py census, one call per job set (census_own_<fold> and census_own_<fold>k), excl = none. G1 is computed from the per-tile rows and n_letters in its output (counts only).

## METRIC-HASH-49
- utc: 2026-09-27T20:49:28Z
- prev_sha256: e6520b289a9d038bbf5f81cbae71a688a5308221f195897a88a0e2ca4ad445fd
- kind: metric-hash
METRIC-HASH-49: orchestrator verifier and G1 tally for the P4-OWN G1 batches. Committed before any F-arm held-out map or census batch exists (DECL-P4-23 6(b), -A1, -A2; METRIC-HASH-48).
- tools/p4/rh_verify_own.py sha256 34bfb240062ae7f88332f2598c5466fd4a8932d9e7003a10116d38a478e33fe7
  - Checks C0 (METRIC-HASH-48 code), A1, A2, K1 (manifest arm, model and train-manifest sha vs the arm's summary; tile set == the RECIPE 6b5bdc5 list of 24; own_ref recorded), K2 (eligible set and PNG bytes), K3 (N0 draw and images recomputed), A3, A5 (per job set, reference brief per variant), B1-B3 (one .age and one transcript per job; no re-runs).
  - It reuses the helper functions of tools/p4/rh_verify.py (METRIC-HASH-36).
- tools/p4/g1_own.py sha256 a05197678a7d57f9690a4bdb716192b6f73982c94a434c284722dd98504ddfb3
  - The DECL-P4-23-A2 count per variant, pooled; the futility test of A1 item 3; no early pass.
  - Tested on synthetic counts only: 22/72 gives PASS, 21/72 gives FAIL; 0/24 and 0/48 give PENDING.
Disclosure: with 24 tiles per fold, the A1 item 3 futility stop can never trigger. After 2 folds, (Y + 24) >= 0.3 x (48 + 24) = 21.6 for every Y >= 0. So G1 needs all three folds in practice. Nothing is changed because of this.

[line withheld: prize-candidate detail under review]
- utc: 2026-09-27T21:35:02Z
- prev_sha256: 0c492f7b9e4d0cc9b0919fa20d7d2ebe120ce3751937c0f9cfe47555b6c3ca44
- kind: result
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
No bar or finding is changed. The title-slot maps (X) stay unread until G1.

## METRIC-HASH-50
- utc: 2026-09-27T21:36:12Z
- prev_sha256: f027895aab8dfae22b121fe78705aa8981a37197562b56a178bc462e756b6511
- kind: metric-hash
METRIC-HASH-50 (correction, before any G1 batch exists): a path bug in the G1 harness, plus review of own-lead's second scheduling change. Approved by the owner in default permission mode after the auto-mode classifier had refused the same edit.
Found at 21:17Z: own-lead run_arms.py writes F-arm held-out maps to logs/sib/own-<fold>/maps/. rh-e1 own_split.py (METRIC-HASH-48) and tools/p4/rh_verify_own.py (METRIC-HASH-49) read logs/sib/own-<fold>/heldout_maps/. As pinned, the batch could not be built.
1. rh-e1 tools/sib/rh-e1/own_split.py: the only change is its 3 occurrences of 'heldout_maps' replaced by 'maps'. Expected sha256 b400e9a4e0d80df0fa07ba986fc6189d216f278372bb61ac7d814a0c67cf39f4 (626cdbb4... before). prep_own.sh is unchanged (f30807ac...).
2. own-lead run_arms.py at 15debde6, sha256 2722d3ac53319d76d7f735ca84cf21d91fb5cdc04e0954cafe3357dc8be01a8c, reviewed as scheduling only. The train.py, infer.py and auc.py invocations are identical to METRIC-HASH-48's 07633449...; the additions are pgrep process checks. Both versions are accepted.
3. tools/p4/rh_verify_own.py sha256 9286c77715d4a13ae8f877d68adabba8da96839818e69374f0ce47957a79dac1. Changes: the MAPS path constant; RUN_ARMS became a set of reviewed versions; the own_split.py pin is item 1. No check was removed or loosened.
   Smoke test on own-lead's live F1 manifest (6 of 24 tiles so far): arm F1, model sha256 == train summary, all tiles in the RECIPE list, run_arms accepted.
Disclosure: the orchestrator's own 21:11Z scheduling order caused the run_arms change after its pin. The folder mismatch was in its own order to rh-e1 at 20:40Z.

## DECL-P4-23-A3
- utc: 2026-09-27T21:41:45Z
- prev_sha256: 38902e0e2301c15be5840d46c40e5be3cfd4f575ed03334a93a5fb6703c7b68f
- kind: declaration
DECL-P4-23-A3: owner-directed single-shot blind census of the S1 title-slot maps, run now, before G1 has been decided. Declared before any X tile is read. The owner (2026-09-27 ~21:45Z, default permission mode) said: "YOU NEED TO READ THE MAPS AND PROVIDE EVERYTHING THE TITLE PRIZE SUBMISSION WOULD NEED". The subscription may end before G1 can be decided (about 07-10Z on 09-28).
This amends ONLY DECL-P4-23 item 6's ordering ("computed before any X tile is read") for these tiles. No acceptance bar is changed.
1. Material and tiles: S1 maps at own-lead (the current ref, recorded). There are 30 tiles, all with valid_fraction >= 0.5 (the norm_manifest default):
   - title slot: w010-027 c14-c17 x r0-r5 (24 tiles);
   - in-batch positive control: col. -1, c11-c13 x r0-r1 (6 tiles, organizer-labelled text, never trained on). This is the DECL-P4-23 item 6(c) col. -1 census, a declared validation.
   Variant sigma2t only; the block variant is dropped for S1, which means fewer comparisons.
2. Harness: the local harness, with hercules.harness.jobs briefs and sealed age answers. Readers are general subagents on the opus model, given the brief verbatim. Batches: key own_s1x (census), N0 n_own_s1x = ceil(30/8) = 4 rot-90 tiles; jobs census_own_s1x in 8+1 sessions. Every transcript is audited (hercules.harness.audit) before scoring; an invalid session is disclosed and not re-run.
3. Scoring: tools/p4/score_p4.py census (counts only). A title-slot tile is POSITIVE iff rows == 'Y' and n_letters >= max(5, N0 p99), as in DECL-P4-2.
   - The batch is informative only if >= 2 of the 6 col. -1 tiles are rows Y with >= 5 letters. Otherwise the title-slot result is "uninformative", not a null.
4. Single shot: S1 is never re-censused on these 30 tiles. The later declared census of S1 on these tiles is replaced by this one; the other seeds and NULL keep their own census as declared.
5. Status: any positive is a "pre-G1 candidate". It becomes EXT-CONFIRMED under DECL-P4-23 only after G1 passes, 2 of 3 S seeds are positive, NULL is below threshold, and phase 2 and the extended test (DECL-P4-3) are passed. Any package or submission material states exactly which of these checks have passed and which are pending.
6. No letter identity leaves the sealed scorer. The orchestrator views no image.

## P4-OWN-S1X-RESULT
- utc: 2026-09-27T21:45:01Z
- prev_sha256: eaf5d6a8dfca15852147f1781a8f28eafc5202d8e33872b254c55f434e9a45f9
- kind: result
P4-OWN-S1X-RESULT (DECL-P4-23-A3; single shot; before G1). Commit A 305eac7a (21:42:16Z) came before any reader. 4 local reader sessions (sigma2t, 8+1); audit 4/4 VALID (0 violations, 0 unread, prompt == brief), logs/p4/own_s1x_audit.json. Scored with score_p4.py: logs/p4/census_own_s1x_summary.json. Counts only.
- S1 maps at own-lead f3cc467a; 30 tiles, all eligible. N0: 4 rot-90 tiles with 0, 0, 0, 0 letters; p99 0; threshold 5.
- In-batch control, col. -1 (w010-027 c11-c13 r0-r1, organizer-labelled text never trained on): 5 of 6 tiles rows Y with >= 5 letters (r0c11 7, r0c12 11, r0c13 10, r1c11 7, r1c12 9; r1c13 rows Y with 4). The batch is INFORMATIVE (>= 2 of 6 required).
- Title slot (c14-c17 x r0-r5, 24 tiles): 0 of 24 rows Y; 0 letters on every tile. Positives 0; candidates 0.
Reading: in our own model's S1 map, which reads the adjacent known-text column clearly, the end-title slot c14-c17 shows no legible carbon-ink writing. This is an informative null for carbon ink at S1, pending G1: if G1 fails, it becomes "uninformative" (DECL-P4-23 item 6(b)).
It does not rule out a title that is:
- in non-carbon ink (the model learns carbon ink);
- flaked or offset onto the facing winding (P4-26 facing: 11 of 24 title-slot tiles reachable, after G1);
- outside c14-c17 (the c18-c19 blank end is not censused here);
[line withheld: prize-candidate detail under review]
Single shot: S1 is not re-censused on these 30 tiles.

## DECL-P4-25-A4
- utc: 2026-09-27T21:59:08Z
- prev_sha256: 4bd3503bbda1d7a06727b52a65db5f3f2408ae83d743233bf10f250946b1347e
- kind: declaration
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
   Maps are made by own-lead with S1 exactly as for X (infer.py unchanged, same display).
2. Reads: the local harness as in DECL-P4-23-A3 (sigma2t, 8+1, local audit, no re-runs). Stages are read as maps arrive. Each stage's N0 is drawn from its own tiles (rot-90, p99). Each tile is read exactly once.
[line withheld: prize-candidate detail under review]
4. Candidates: an O tile with rows Y and letters >= max(5, N0 p99). It is a "pre-G1 candidate". Confirmation needs phase 2 and the extended test (DECL-P4-3) with N0 from O's batches only, and then the Q6 layout test (METRIC-HASH-42) before it is called an initial title. Every status is disclosed as in DECL-P4-23-A3 item 5.
5. Training overlap: the outer strips are outside P4-OWN's training zone T, so there is no overlap.

## DECL-P4-25-A5
- utc: 2026-09-27T22:00:46Z
- prev_sha256: 4aef2b9a4d94819010f02a4159f491a550aa16191fe67dfc866c9b3bbabac28f
- kind: declaration
DECL-P4-25-A5: the owner narrowed DECL-P4-25-A4 ("too many tiles"). Declared before any P4-OWN map of any outer strip exists. It REPLACES the A4 tile list; everything else in A4 (harness, gate, candidates, disclosure) is unchanged.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
Selection rule: tiles are chosen by an earlier, independent material's blind reads. This targets where text-like marks were seen. It is a search prior, not evidence. Confirmation still needs phase 2 and the extended test with N0 from this batch, then the Q6 layout test.
Gate: O is informative only if >= 2 of the 3 control tiles are rows Y with >= 5 letters in S1.

## DECL-P4-25-A6
- utc: 2026-09-27T22:02:27Z
- prev_sha256: d9519091e9ce2258f9aeeeb836ed75f097fe4057f241c12f66b98d997ec2dafe
- kind: declaration
DECL-P4-25-A6: the owner widened DECL-P4-25-A5 ("too few tiles - may need double that"). Declared before any P4-OWN map of any outer strip exists. It REPLACES the A5 tile list; everything else is unchanged (A4 harness, gate, candidates and disclosure; the A5 caveat on the selection prior).
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
Gate: >= 2 of the 3 control tiles rows Y with >= 5 letters in S1.

[line withheld: prize-candidate detail under review]
- utc: 2026-09-28T01:03:46Z
- prev_sha256: a56184da96f62d9b9f54f1e982eb9a35e5d4931d8ea074d6b1c65cb4e94fa00b
- kind: result
[line withheld: prize-candidate detail under review]
- S1 maps at own-lead a1c5e8e7; 30 tiles, all eligible. N0: 4 rot-90 tiles with 0, 0, 1, 5 letters; p99 4.88; threshold 5.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
Reading:
- Writing-like rows are common before the lead (12/27), so the region is not blank. That weakens the assumption that the lead is col. 1 (DECL-P4-25-A3 basis), and more body text may precede it.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]

## METRIC-HASH-51
- utc: 2026-09-30T03:25:56Z
- prev_sha256: 1578ed26f8103fb84a6b68a97a00323a47faecc2be4e153552b8d19d0844e0e2
- kind: metric-hash
METRIC-HASH-51: own-lead run_arms.py at 484025e2 (2026-09-28 00:53Z), sha256 1d8f83efc956ab4180924b8a4c13f4ebfc73dc5ba662fcad79dc355e3788d1f8, reviewed and accepted as a housekeeping-only change. The only diff from the METRIC-HASH-50 version (2722d3ac...) is two lines: after a tile's .png.json is committed, infer.py's band checkpoint directory for that tile is deleted (the disk hit its 5 GB floor). No map, training or scheduling logic changed.
tools/p4/rh_verify_own.py now accepts this sha as a third reviewed version: sha256 ef70acc89a621b870c65f7aa11c0228020dcad6841134e5bb01633a222e4634a. Nothing else changed.
Found by the verifier itself: the OWN_F1 batch (rh-e1 A 1c87536, B 6e9eef1; own-lead 0f164e1b) failed only C0 on this file, and passed every other check.

## DECL-P4-25-A7
- utc: 2026-09-30T03:26:46Z
- prev_sha256: 978163e2efcd4e6682652435c07f2e560f4ddc93443ec3c67952fb4babe571b7
- kind: declaration
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
2. Reads: the local harness as in DECL-P4-23-A3 (sigma2t, audit, no re-runs). One batch per arm: 6 tiles + N0 drawn from that arm's own 6 tiles, 1 session each. Every tile is read once per arm.
3. Rule, using the S1 O-batch threshold (5), unchanged:
   - A candidate passes 6(d) iff it is rows Y with >= 5 letters in >= 2 of the 3 S seeds (S1 counted as read), AND NULL's map of it has < 5 letters.
   - An arm's reads count only if >= 2 of its 3 control tiles are rows Y with >= 5 letters. For NULL, the control result is reported but is no gate: NULL is expected to fail it.
[line withheld: prize-candidate detail under review]

## OWNER-STANDING-ORDER-5
- utc: 2026-09-30T03:28:43Z
- prev_sha256: 52a80b8837a176aacda07ab441140d875b5f3bc569bc9c419c09d346cc5cc824
- kind: decision
OWNER-STANDING-ORDER-5 (zero-turn operation). Owner message, 2026-09-30 ~03:35Z, verbatim: "add a standing rule to minimize ai turns to zero as often as possible so we limit usage to nearly zero while maximizing output".
Rule, for the orchestrator and every sibling, with no end date:
1. Only AI turns use the usage allowance. Compute, git pushes and shell waiters do not.
2. All repeatable work runs as detached scripts (nohup/setsid), launched in ONE turn and left to run. This covers training, inference, rendering, builds, deterministic batch preparation and commits/pushes. Each script:
   - pushes its own results;
   - has a watchdog that restarts it;
   - where possible, resumes after a container restart without a turn (idempotent, skips finished work).
3. Waiting is done by background shell loops that exit only on an actionable event: a batch ready to verify, a result to score, or a problem keyword. They never wake the model for progress, and there are no polling or check-in turns. A timed check-in is set only as a long fallback (>= 6 h), or when no event can be detected.
4. A sibling session is woken only to launch or relaunch a detached pipeline, or to handle a failure it reported. Sessions whose work is done or retired get no triggers and no waiters (archive the self-waking ones). No status prose beyond one STATUS.md line.
5. AI turns are spent only where no script can do the job:
   - blind reads (the readers themselves);
   - review and pinning of new code (METRIC-HASH);
   - declarations before data;
   - verification judgments;
   - owner messages.
   Each such turn is batched: independent actions are done together, and several batches are verified or scored in one turn where the timing allows.
6. Nothing in this order lowers any bar, seal, null, declaration or review step. When a saving would weaken a check, the check wins. Reads are never skipped to save usage; they are batched instead.

