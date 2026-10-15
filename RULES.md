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

