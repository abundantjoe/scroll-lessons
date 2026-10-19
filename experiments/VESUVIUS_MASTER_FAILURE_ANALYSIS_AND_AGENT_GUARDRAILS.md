# VESUVIUS MASTER FAILURE ANALYSIS & AGENT GUARDRAILS
## A source-grounded synthesis for Scroll Swarm, the Scroll Factory, and future Megara development

**Prepared:** 19 October 2026  
**Primary sources:** `abundantjoe/scroll-lessons` (`main`), especially `MASTER_LESSONS.md`, `worlds-first/README.md`, experiment branch READMEs and linked worker code; the attached `RUTHLESS VESUVIUS PROMPT PREAMBLE.txt`.  
**Purpose:** Turn the failures already observed into executable preflight gates, explicit agent contracts, and a reproducible route from CT volume → verified surface → valid patch → calibrated ink map → defensible letters.

> **Mission standard:** Recover verifiable, previously unreadable writing. Do not reward output volume, plausible-looking textures, surface area, or model complexity unless they survive the checks below and improve the chance of genuine letters.

---

# 1. Executive findings

## 1.1 The central diagnosis

The strongest lesson from the prior work is that **the pipeline spent expensive ink-model and reader effort on surfaces that had not earned the right to be treated as papyrus surfaces**. Several separate errors then compounded:

1. **Wrong or unverified geometry:** surfaces could be smooth, large, self-intersection-free, and aligned with a radial direction while still jumping between windings or cutting across sheets at cracks.
2. **Invalid or partial image coverage:** several inspected PNGs show a large black canvas with only a thin edge, diagonal band, small island, or narrow strip of visible signal. A PNG with the expected dimensions is not necessarily a full physical patch.
3. **Blank render margins:** all-zero rows entering patch normalization and blending can create false bands or suppress real ink.
4. **Insufficient positive controls:** runs with a failed or insensitive known-text control produced nulls that were not informative. A model output is not validated simply because inference completed.
5. **Model/domain mismatch:** public models that detect signal on a known/training scroll may be blind to a new scan or may produce patterns that readers cannot use.
6. **Ambiguous provenance and labels:** a worker/branch name is not the same thing as the actual target scroll, volume, or surface. Historical branches processed more than one target scroll. Output paths alone must never be treated as the ground-truth manifest.
7. **Forward/reverse confusion:** the meaning of “forward” and “reverse” changes with the render frame and normal flipping. A pair of maps is not two independent confirmations and should not clutter the human-facing deliverable.
8. **Visual QA was sometimes explicitly prohibited:** one historical FL-4 brief instructed its worker to use “numbers only” and never open or describe any image, tile, or CT pixel. That can be useful for a sealed numeric worker, but it leaves no place for the independent visual QA needed to detect catastrophic geometry and rendering failures.

These are not isolated cosmetic issues. They can invalidate every downstream result while allowing the pipeline to appear busy and technically successful.

## 1.2 What I actually inspected

I read the attached execution preamble and the repository's `worlds-first/README.md`, inspected the repository tree, read relevant portions of `MASTER_LESSONS.md`, and followed selected output paths into experiment-branch READMEs, manifests, scripts, and run logs.

I visually inspected **23 representative PNGs** across multiple scroll folders and output types, including forward/reverse examples, sparse/partial tiles, and a Paris 4 pool image. This is a representative visual audit, **not** a claim that I manually blind-read every image in the repository. The repository contains thousands of images, and the historical worker instructions and available source records make a genuinely blinded, item-by-item reading/scoring exercise distinct from visual QA. No letters are claimed in this document.

Representative visual observations:

- Multiple eligible-scroll examples have most of the 1068 × 1068 canvas black, with the visible signal confined to an edge, corner, narrow strip, or diagonal band.
- Some visible surface masks have stair-stepped borders and discontinuous islands. These should trigger coverage/continuity review, not be passed downstream because a PNG exists.
- A PHerc0490A example has separated dark islands and long disconnected slivers rather than a clearly continuous full tile.
- A PHerc0268 `gold_preview.png` is a thin one-dimensional diagnostic plot, not a papyrus tile. This illustrates why image type must be validated from metadata and dimensions/content, not inferred from `.png`.
- A Paris 4 pool image contains writing-like high-contrast shapes. That is only a visual observation; it is not a verified reading or proof that any particular pipeline recovered letters.
- Forward/reverse examples can share essentially the same partial geometric mask while their displayed texture differs. They should not be shown as an unexplained pair to the main reader.

## 1.3 Repository inventory

The `worlds-first/README.md` lists **3,892 images** across 18 scroll folders. The current recursive tree contains **3,971 image assets total**: 3,916 PNGs and 55 JPEGs. The additional 79 assets are in the `hercules` and `megara` helper/review material rather than the 18 scroll folders. The repository README correctly describes the published renders as **model outputs, not readings**, and states that no letters are claimed.

The 18-folder counts listed in the repository are:

| Folder | Images |
|---|---:|
| PHerc0175a | 128 |
| PHerc0175b | 171 |
| PHerc0191 | 215 |
| PHerc0211 | 258 |
| PHerc0257 | 229 |
| PHerc0268 | 535 |
| PHerc0306b | 27 |
| PHerc0483a | 41 |
| PHerc0483b | 186 |
| PHerc0490a | 133 |
| PHerc0490b | 35 |
| PHerc0800 | 83 |
| PHerc0813 | 89 |
| PHerc0846a | 203 |
| PHerc0846b | 43 |
| PHerc1203 | 44 |
| PHerc1545 | 215 |
| PHercParis4 | 1,257 |
| **Total in the 18 scroll folders** | **3,892** |

The tree also contains paths with `forward` and `reverse` in their names. A path count is not a count of valid, matched pairs: each pair must be matched by target volume, patch bounds, render frame, model, and run ID.

**Critical scope note:** PHercParis4 is a distinct special/title-search target and must not be casually treated as one of the First Letters eligible scrolls. Eligibility is prize- and date-specific and must be read from current official rules and a verified eligibility manifest.

---

# 2. Source-grounded evidence and concrete examples

This section separates direct source findings from the visual audit and the design recommendations derived from them.

## 2.1 Surfaces passed numeric gates while jumping between sheets

`MASTER_LESSONS.md` lesson L101 records a particularly decisive failure:

- A real PHerc0268 8.64 µm, 2 × 2 cm patch passed the radial-normal numeric gate (median \|cos\| = 0.928; 75% above 0.8).
- It also passed the other numeric bars used at the time.
- Raw-CT cross-sections then showed the surface holding a layer between cracks and jumping layers at cracks.
- A “fraction on predicted papyrus” statistic could not distinguish a good surface from a jumped surface: the values were 0.676 for both the good and jumped surfaces, and 0.628 for a surface cutting across windings.
- The lesson explicitly records that a full day of compute was lost before the cross-section inspection.

**Implication:** area, self-intersection, radial-normal, and CT occupancy checks are useful screens, but none can certify sheet identity on its own. Surface QC must include raw CT cross-sections at multiple heights/positions and explicit checks for layer jumps at cracks.

Source: [MASTER_LESSONS.md — L101](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md#l101-numeric-surface-gates-are-blind-to-layer-jumps-on-crushed-scrolls-look-at-cross-sections)

## 2.2 Grows without the required structural guidance were data-independent

The master lessons state that grows without the organizer normal grids ignored the CT and could produce nearly identical areas across different seeds, cut across windings, and make the FL-1/FL-2/FL-3 and FL-4 nulls void when paired with an insensitive positive-control gate. The recorded signature included repeated FL-2 areas around 26.5–31.1 cm² and nearly identical FL-4 squares around 11.665 cm².

The `sib-fl-pherc0191` branch README also states that the PHerc0268 FL-4 outputs from that worker were declared VOID because the grower ran without normal grids and cut across windings. The same README records a `run.sh` bug in which a global loop variable overwrote the segment path, allowing a later segment to render a stale or wrong `tifxyz`.

**Implication:** the pipeline must validate not only the geometry but also the identity of the exact input artifact that was rendered. A plausible-looking result can be generated from the wrong segment even when the process exits successfully.

Sources:
- [MASTER_LESSONS.md — L100](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md#l100-grows-without-normal-grids-are-data-independent-know-the-failure-signatures)
- [PHerc0191 worker branch README](https://github.com/abundantjoe/scroll-lessons/blob/sib-fl-pherc0191/README.md)

## 2.3 On-sheet occupancy is necessary but not enough

L097 records bad surfaces with low on-sheet and in-CT-mask fractions. For PHerc0306B, only 0.227 of segment vertices lay on the surface prediction; support at normal offset zero (0.167) was lower than support at +16 voxels (0.233). For PHerc0846B, the median on-sheet fraction was 0.1955 and median CT-mask occupancy was 0.413.

The recommended check is to sample hundreds of mesh vertices, compare CT support at zero offset against displaced offsets (including ±4 to ±16 voxels where appropriate to the scan), measure the in-scroll CT-mask fraction, and reject tiles that are not physically on papyrus.

But L101 proves that even a surface with respectable numeric values can jump layers at cracks. The cross-section gate remains mandatory.

Source: [MASTER_LESSONS.md — L097](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md#l097-test-sheet-following-with-an-off-sheet-control-and-ct-mask-occupancy-before-rendering)

## 2.4 The legacy tiler admitted partial tiles by design

The historical FL-4 `fl4.py` states that it cuts **2 × 2 cm tiles** from the full render canvas. It resamples mesh-vertex validity to the canvas with nearest-neighbor interpolation and keeps a tile when `valid_fraction >= 0.5`. The manifest records `valid_fraction`, but this alone does not prove that the physical surface follows one sheet, that the render contains no blank-margin artifact, or that the full nominal area represents a continuous patch.

The same code writes the configured `SCROLL`, volume, model, model hash, render chain, and tile coordinates to the manifest. That is useful provenance, but a manifest that repeats a wrong environment value can still be internally consistent. Future agents must cross-check declared values against the actual source artifact, volume metadata, source path/ID, and hashes.

**Implication for the new Scroll Factory:** do not copy the legacy 2 × 2 cm tiler unchanged for the planned 1 cm² surface jobs. The new factory needs a physically defined **10 mm × 10 mm** surface tile with explicit 3-D bounds and coverage. Four such tiles form a 20 mm × 20 mm / 4 cm² patch only if their physical placement, orientation, winding identity, and overlap/seams are validated.

Sources:
- [PHerc0191 worker branch README](https://github.com/abundantjoe/scroll-lessons/blob/sib-fl-pherc0191/README.md)
- [p4v-15 `fl4.py`](https://github.com/abundantjoe/scroll-lessons/blob/sib-p4v-15/tools/sib/p4v-15/fl4/fl4.py)
- [p4v-15 `run.sh`](https://github.com/abundantjoe/scroll-lessons/blob/sib-p4v-15/tools/sib/p4v-15/fl4/run.sh)

## 2.5 Blank render margins corrupt ink inference

L249 documents that `vc_render_tifxyz` can leave all-zero rows at the edges of thin strips. The villa ink model normalizes partly blank patches with those zeros included. This produced false orange bands on PHerc0268 and roughly halved real ink on a PHerc0343 control.

Recorded results include:

- 13-row strips with blank margins: recall 0.386 on the control.
- Reflect-filled strips: recall 0.646, which is an improvement but still below the strict predeclared recall bar of 0.7.
- In a 7-strip fill test, the strong-ink fraction fell by factors of 2.96–623.9×, and the bands disappeared in 5/7 strips.
- The fill also increased off-letter strong pixels in the control (about 0.67% to 1.35% in one comparison).

Therefore reflection fill is a **mitigation, not a cure**. The proper fix is mask-aware inference/normalization where possible, explicit render-valid masks, measurement of the renderer’s actual blank margins, and a positive control in the exact target geometry.

Sources:
- [MASTER_LESSONS.md — L249](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md#l249-the-blank-margin-bug-partly-blank-inference-patches-create-or-suppress-ink)
- [Dominion release README / stripqc](https://github.com/abundantjoe/scroll-lessons/blob/dominion-release/README.md)

## 2.6 Forward/reverse names do not identify the writing direction

L135 shows that the same text order can be called FORWARD on a `--flip-normals` render and REVERSE on an unflipped render. On the PHerc0139 2.4 µm control, the correct flipped render reproduced the organizer surface-volume slices with pooled Pearson correlation around 0.999997–0.999998. The official FORWARD order then reproduced the organizer ink map at r = 0.999986, while official REVERSE on that same render did not. On the unflipped render, the direction label changed.

L234 and L244 add that implausible ink fractions, uniform speckle, and forward/reverse disagreement can void maps, but agreement itself does not validate ink. L244 records forward/reverse agreement at r = 0.982 even though held-out AUC was only 0.58.

**Implication:** “forward” and “reverse” are execution parameters, not meaningful final user-facing labels. Calibrate the render frame and depth order on known text. Keep alternatives internally for audit, but show the main reader only one selected, calibrated final image per patch.

Sources:
- [MASTER_LESSONS.md — L135](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md#l135-name-the-depth-order-by-the-render-frame-never-by-the-word-reverse)
- [MASTER_LESSONS.md — L234](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md#l234-implausible-ink-fractions-and-forwardreverse-disagreement-are-void-signatures)
- [MASTER_LESSONS.md — L244](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md#l244-forwardreverse-agreement-is-not-ink-validation)

## 2.7 Known-text controls are mandatory before interpreting targets

The master lessons record a cross-scroll checkpoint that was blind on Paris 4: all three known-text gate tiles returned no letters, so the target batch was stopped before interpretation. A separate lesson records public 9 µm maps with pixel AUC around 0.73 on unseen PHerc0841 text, yet 18 calibrated readers named zero letters. Pixel discrimination is not the same as letter legibility.

The same exact pipeline—including render geometry, mask handling, patch shape, model checkpoint, and display scaling—must pass a known-text control before target tiles can be read. If the positive control fails, target nulls are **uninformative**, not evidence of no writing.

Sources:
- [MASTER_LESSONS.md — L176](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md#l176-a-cross-scroll-ink-model-can-be-completely-blind-on-a-new-scroll-gate-it-on-that-scrolls-known-text-first)
- [MASTER_LESSONS.md — L256](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md#l256-push-a-known-letters-control-through-the-identical-pipeline-before-reading-any-null)
- [MASTER_LESSONS.md — L196](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md#l196-the-base-9-um-model-detects-unseen-scroll-ink-at-pixel-level-auc-073-but-its-maps-are-not-letter-legible)

## 2.8 Provenance errors can survive successful execution

The PHerc0191 worker README documents a `run.sh` variable-overwrite bug that could send a stale or wrong `tifxyz` into rendering. The p4v-15 code also shows why source-of-truth manifests matter: tile outputs inherit scroll/volume/model values from environment variables, and the tile writer records the configured scroll. The code does not make an image correct merely by giving it a manifest.

In the `worlds-first` tree, the top-level scroll folder is sometimes the **worker's primary assignment**, while nested subfolders show that the same worker also processed another target (for example, PHerc0268 FL-4 outputs nested under some workers' primary-scroll folders). This is documented cross-scroll work, not proof that every such file is wrong. It does prove that **the top-level folder and worker name cannot be used as the only target-scroll label**.

An automated path audit found numerous image paths whose actual target identifier in a nested segment/filename differs from the top-level folder. Those are not automatically errors; each must be classified against the branch README, job manifest, actual source volume, and output hash. Do not blindly relocate them or infer target identity from a folder name.

I did **not** establish a specific Paris-4-source substitution as fact from the representative samples alone. Treat the user-reported Paris 4 mislabel as a required forensic check: resolve each suspect PNG through its exact code path, `FL_SCROLL`/`FL_VOLUME` values, CT and surface URLs, tile manifest, and checksums before labelling it confirmed.

Sources:
- [PHerc0191 worker branch README](https://github.com/abundantjoe/scroll-lessons/blob/sib-fl-pherc0191/README.md)
- [p4v-15 `fl4.py`](https://github.com/abundantjoe/scroll-lessons/blob/sib-p4v-15/tools/sib/p4v-15/fl4/fl4.py)
- [p4v-15 `run.sh`](https://github.com/abundantjoe/scroll-lessons/blob/sib-p4v-15/tools/sib/p4v-15/fl4/run.sh)
- [worlds-first README](https://github.com/abundantjoe/scroll-lessons/blob/main/worlds-first/README.md)

## 2.9 The historical workflow sometimes forbade visual inspection

The p4v-15 FL-4 worker brief says: “Numbers only: never open, view or describe any image, tile or CT pixel.” The intent was to constrain the worker and avoid unplanned interpretation. But if every compute worker follows that instruction and no independent QA role views the output, catastrophic visual defects can survive to publication.

**New policy:** compute workers may be forbidden from interpreting letters or altering a declared experiment, but an independent Surface-QA/Render-QA role must inspect the geometry and image validity before the ink model or blind reader is authorized to proceed. Visual QA is not the same as claiming a reading.

Source: [p4v-15 FL-4 brief](https://github.com/abundantjoe/scroll-lessons/blob/sib-p4v-15/tools/sib/p4v-15/fl4/BRIEF_FL4.md)

## 2.10 Megara provides a useful evaluation lesson, not a promise of transfer

The `megara` branch reports an ensemble trained on hand labels that reached pixel AUC 0.876 and stroke AUC 0.935 on seven held-out crops, and 0.830 / 0.928 on six confirmation crops that had not been touched by the study. The README explicitly says this does **not yet read unread papyrus**. The result demonstrates the value of controlled evaluation and a confirmation set; it does not establish that the same model transfers to unread scrolls or to different resolutions.

Any future Megara master model should inherit the evaluation discipline, not the assumption that a high known-text score guarantees discovery.

Source: [Megara README](https://github.com/abundantjoe/scroll-lessons/tree/megara)

---

# 3. Non-negotiable anti-hallucination and artifact-integrity rules

These rules should be inserted into the Scroll Swarm master prompt and enforced by code wherever possible. They are written as machine-checkable requirements, not merely advice.

## 3.1 Every artifact has one canonical identity

Every tile/patch manifest must separately record:

- `target_scroll_id` — the scroll physically represented by the CT being processed.
- `target_volume_id` — exact volume ID from that scroll's metadata.
- `worker_id` and `worker_assignment_scroll` — who produced it and the assignment under which it ran. These are not substitutes for `target_scroll_id`.
- `source_ct_uri`, `source_ct_sha256` or an immutable source identifier, and `source_surface_uri`/hash.
- `surface_artifact_id`, `segment_id`, `patch_id`, and exact 3-D bounds.
- voxel size and units, coordinate frame, axis convention, handedness, transform/registration version, render frame, and `--flip-normals` state.
- surface-fit method, parameters, iteration count, normal-grid provenance, seed, and run ID.
- render-valid mask and CT-mask provenance.
- model name, checkpoint hash, training-data statement, inference settings, and whether the target scroll/region overlaps training data.
- output hash, parent artifact hashes, QC results, QC tool versions, and status.

**Hard fail:** if the manifest's target scroll/volume disagrees with the actual input volume, surface metadata, nested source path, or verified job definition, mark the artifact `PROVENANCE_FAIL`. Do not try to repair it by renaming the PNG. Regenerate only after the source mapping is fixed.

## 3.2 File paths are not evidence

A file named `PHerc0490a_*` is not proof it was rendered from PHerc0490A. A branch named `sib-fl-pherc0191` is not proof every output in that branch belongs to PHerc0191. A checkpoint trained on PHercParis4 is not proof that the tile itself is from Paris 4, and it is not proof that the model can read the target.

Validate target identity from the actual volume URI, metadata, source hash, manifest, and execution log. Compare those fields independently. Never infer identity from a single string.

## 3.3 No silent fallback

If normal grids, CT chunks, metadata, volume IDs, model weights, render masks, or coordinate transforms are missing, do not silently substitute a default, a stale file, a centroid guess, or a different scroll's artifact. Emit a machine-readable `BLOCKED` or `PROVENANCE_FAIL` record with the exact missing dependency.

A job with an empty work list is not complete. A shell wrapper that runs successfully is not proof that the required Python, GPU, data, or model step ran. Completion markers are written only after checking all required outputs and their hashes.

## 3.4 Status vocabulary

Every stage must end in one of the following statuses:

- `PASS` — all declared gates passed.
- `FAIL` — a test ran and failed.
- `VOID` — the result cannot be interpreted because a prerequisite failed (e.g. surface invalid or positive control insensitive).
- `INCONCLUSIVE` — the declared experiment ran but evidence did not discriminate the alternatives.
- `BLOCKED` — required data, permission, dependency, or compute was unavailable.
- `NOT_RUN` — no attempt was made.

Never convert `VOID`, `BLOCKED`, or `NOT_RUN` into a null result. Never label an experiment `PASS` merely because the command exited zero.

---

# 4. The Scroll Factory's mandatory gates

**No expensive stage may run until its prerequisites pass.** The orchestrator must stop the chain immediately when a gate fails.

## Gate 0 — Target, eligibility, and data identity

Before surface fitting:

1. Verify current prize eligibility from current official rules; store the source URL, retrieval date, and relevant rule excerpt.
2. Resolve exact scroll ID, volume ID, voxel size, scan protocol, dimensions, axis conventions, coordinate frame, missing chunks, and source hashes from the volume's own metadata.
3. Confirm the selected volume actually contains the requested physical region and the planned tile bounds fit inside the scan.
4. Check the requested 10 mm × 10 mm tile coordinates against the physical coordinate frame. Do not assume that pixels, voxels, millimetres, and centimetres are interchangeable.
5. Record the expected target identity in a signed/hashed job manifest before launching workers.

**Stop conditions:** unknown target volume, stale/ambiguous metadata, missing required CT chunks, invalid bounds, unknown coordinate transforms, or unresolved eligibility where it affects the planned claim.

## Gate 1 — Surface construction and sheet identity

Before rendering or ink inference:

1. Use the verified surface prediction and required normal grids. Do not use a data-independent grower because it produces enough area.
2. Confirm the fit's input artifacts and parameters; preserve the original fit and any alternative candidates.
3. Measure mesh area, valid vertices/quads, self-intersections, local orientation, CT-mask occupancy, and support along the local normal.
4. Sample hundreds of vertices (or an appropriately powered sample) and compare support at the proposed surface against displaced offsets. Freeze thresholds on positive/on-sheet and negative/off-sheet controls before screening unknown targets.
5. Inspect the surface overlaid on **raw CT cross-sections at multiple positions/heights**, especially cracks, folds, crushed interior, and apparent layer transitions.
6. Require sheet identity to remain coherent. A surface that jumps between windings, crosses the papyrus, follows a crack rim, runs through air, or leaves the scan is rejected.
7. Check adjacent fits and nearby seeds for suspiciously identical geometry/area or data-independent growth.
8. Write a QA montage and numerical report; do not send a surface directly from the grower to the ink model.

**A smooth mesh is not a correct mesh. A large mesh is not a useful mesh. A single numeric score cannot replace cross-sections.**

**Stop conditions:** missing normal grids, off-sheet controls that score as well as on-sheet, low CT occupancy, support peak displaced away from zero, visible layer jumps, unverified sheet identity, or suspiciously identical grown surfaces.

## Gate 2 — Physical tile geometry and coverage

Each surface tile must represent a **physical 10 mm × 10 mm region**, not merely a square PNG.

Required measurements:

- physical bounds in millimetres and corresponding coordinates in the source volume;
- actual surface area and projected area;
- valid surface fraction;
- CT-mask occupancy and render-valid fraction;
- pixel-to-physical scale;
- number and location of disconnected valid components;
- bounding box of valid pixels;
- largest connected component / total valid area;
- row/column coverage profile;
- whether any valid area is only a thin strip or corner sliver;
- whether the tile crosses a crack, sheet boundary, fold, or volume edge.

Thresholds must be predeclared and validated against examples. Do not use the legacy `valid_fraction >= 0.5` rule as a universal acceptance threshold. Fifty percent valid pixels can still produce a misleading image, and vertex validity alone does not prove sheet-following.

**Hard fail:** a supposed 10 mm × 10 mm surface tile is actually a cross-section, a narrow strip, an isolated fragment, a disconnected collection of islands, a mostly blank canvas, or a projection of multiple windings. Mark it `VOID_SURFACE_OR_COVERAGE`; do not run ink inference.

### Visual QA checklist for each tile

- Does the rendered texture occupy the intended physical area?
- Is the visible region continuous and plausibly papyrus-like?
- Are there large black/zero margins or unexplained blank rows?
- Is the visible area a thin diagonal line or edge strip rather than a patch?
- Are there stair-stepped boundaries that reflect missing surface cells?
- Does the surface jump across a fold/crack or appear to mix layers?
- Does the tile have the expected scale and orientation?
- Does its mask agree with its physical coordinates and render-valid mask?

The reviewer is not asked to read letters at this gate. The reviewer is asked whether the image is a valid, well-defined patch at all.

## Gate 3 — Rendering validity and blank-margin QC

1. Render with the verified official renderer and pinned version/configuration.
2. Confirm the output corresponds to the intended surface and source volume; hash the render and its manifest.
3. Compare with an organizer reference product where one exists. For the known reproduction chain, the lessons use a very high correlation gate (around `r > 0.99`); choose the exact metric/bar for the specific reference and freeze it before target runs.
4. Compute a `render_valid_mask` from actual render validity/CT availability, not from ink probability (`p > 0` is not a valid mask).
5. Measure blank margins for the actual renderer version and surface geometry. Re-measure after any renderer upgrade.
6. Mask invalid pixels before display and scoring. Never allow model outputs on pixels without rendered data to create apparent differences.
7. Use mask-aware patch normalization where possible. If reflection fill is used, mark it as a mitigation and report the no-ink floor and off-letter false-positive rate.
8. Check ink intensity as a function of distance from the valid-render edge. A band locked to a fixed margin is an artifact warning.
9. Retain the original unfilled render and mask. Never overwrite the raw evidence with a filled or enhanced image.

**Stop conditions:** unknown renderer margins, missing render-valid mask, a failed reproduction gate, invalid pixels displayed as model output, or an edge-locked ink band that has not been resolved.

## Gate 4 — Model provenance and positive control

Before target inference:

1. Record the checkpoint SHA-256, architecture, code revision, training data, label provenance, resolution, inference settings, and licensing/eligibility implications.
2. Determine whether the target scroll/region is represented in training data or near a training label. For First Letters, enforce a certified 3-D exclusion margin around the search region where required.
3. Run a known-text positive control from the same scan/scroll family through the **identical** render → mask → normalization → inference pipeline.
4. Run a no-ink/off-sheet/displaced negative control, matched as closely as possible for geometry and rendering.
5. Check the reference's own score under the proposed metric before choosing a pass threshold.
6. Report letter/stroke legibility and downstream performance where available; do not substitute pixel AUC for readability.
7. If the positive control fails, stop target inference and mark the batch `VOID_CONTROL_FAIL`. Do not publish target nulls.

A model that is excellent on its training scroll can be blind on a new scan. “Inference completed” is not a positive control.

## Gate 5 — Ink-map sanity and canonical display

Before reader time:

1. Mask outputs outside render-valid pixels.
2. Use a fixed, absolute display scale across tiles. Do not auto-stretch every tile independently.
3. Record ink fraction, score distribution, saturation, spatial uniformity, edge-distance profile, and spatial autocorrelation.
4. Predeclare plausible ink-fraction and map-structure ranges based on controls. Extremely high fractions (historically 46–59% on some maps), uniform speckle, or no plausible row/letter-scale structure are void signatures, not evidence of exceptionally dense writing.
5. Compare the candidate against its displaced/off-sheet negative and rotated/shifted nulls.
6. Check face specificity where the pipeline can sample both physical faces. Agreement between two maps that read the same CT does not independently certify ink.
7. Run forward/reverse only as a calibration/diagnostic comparison. Use the known-text control to determine the valid order for that render frame. Never treat agreement as proof of ink.
8. Keep alternatives in an internal audit area. Publish only one canonical selected image to the main reading surface.

**Stop conditions:** control failure, invalid pixel support, implausible map statistics, edge artifact, no face specificity where required, or no advantage over the negative control.

## Gate 6 — Blind reading and calibration

1. Prepare target tiles, hidden known-text positives, colour/texture-matched negatives, and a sufficiently large null set in the same display format.
2. Freeze keys and briefs before readers begin; do not let the reader or scoring harness see answers.
3. Ensure the reader sees only the canonical image for each patch. Do not expose forward/reverse pairs, filenames that leak target context, model names, or candidate hints.
4. Audit transcripts and ensure each image was actually inspected.
5. Calibrate every reader on the hidden positives and negatives. If calibration fails, the reader's target outcomes are uninformative.
6. Use a meaningful null distribution; the prior lessons warn that tiny null sets can manufacture leads.
7. Preserve uncertain alternatives and do not promote a plausible glyph into a letter without evidence.
8. Independent review must trace proposed letters back to the original CT and surface, not merely to the same model-enhanced image that suggested them.

A negative read only means something if the geometry, render, model, and reader all passed their gates.

## Gate 7 — Stitching and the 4 cm² patch

Four 1 cm² siblings make a 4 cm² patch **only if they form one coherent physical region**.

Before stitching:

- all four tiles must pass Gates 0–6 as applicable;
- confirm common target scroll, volume, coordinate frame, surface identity, orientation, and physical face;
- verify adjacency, overlap, scale, and orientation from physical coordinates, not filename order;
- detect duplicate, missing, swapped, mirrored, rotated, or overlapping cells;
- check that no tile crosses a winding boundary or discontinuity;
- validate seams in both the 2-D image and the underlying 3-D surface;
- ensure stitching has not introduced interpolation artifacts or changed intensity scale;
- compute the exact stitched physical bounds and confirm 20 mm × 20 mm = 4 cm²;
- preserve per-tile lineage and hashes in the stitched manifest.

Mechanical stitching can be correct while the underlying surfaces are wrong. A continuous-looking 2-D image is not proof that the 3-D points belong to one sheet.

## Gate 8 — Weave integration

The Weaving Agent may consume only `PASS` artifacts with valid manifests. It must:

1. reject unmanifested PNGs, mismatched hashes, duplicate patch IDs, incompatible coordinate frames, and any `VOID`/`BLOCKED` tile;
2. stitch in physical coordinates and declared adjacency, never by directory listing or lexical filename order;
3. preserve holes as holes rather than silently filling missing data;
4. write a new versioned weave build and manifest;
5. run coverage, seam, continuity, orientation, and provenance checks before promoting it;
6. update the root-level working weave snapshot only after the build passes;
7. keep the prior accepted snapshot and versioned build for rollback;
8. show a coverage map and explicit unprocessed/invalid regions.

---

# 5. Recommended policy for front/back and forward/reverse

These are related but different concepts and must not be conflated.

## 5.1 Forward/reverse is a render-order issue

The word “reverse” does not reliably identify the physical reading face or the correct text order. The label depends on the render frame and whether normals/slices were flipped. A known-text calibration must decide which order reproduces the trusted reference for the current render configuration.

**Rule:** internally test the necessary directions on a known-text control; write the selected calibrated order into the manifest as a concrete statement of render frame, flip state, and layer order. Do not name the final image merely `forward.png` or `reverse.png`.

## 5.2 Front/back is a physical-face hypothesis

Recto/verso (or front/back) refers to physical sides of a papyrus sheet. Do not average the two faces. The lessons specifically warn against averaging recto and verso maps or stretching each map independently.

Recommended handling:

- Keep each physical face as a separate internal hypothesis with its own surface normal, offset, provenance, and control result.
- If the known-text control identifies a reading face reliably for the relevant scan family and geometry, use that face as the default for the main reading output.
- If face identity is not established, run a predeclared, paired face test using known positive and negative controls; keep the human reader blind to which face/model produced each candidate.
- If evidence does not discriminate, set `FACE_UNRESOLVED`; do not manufacture certainty or discard the alternative.
- The main `final/` folder contains **one selected canonical image per patch**. Alternative face maps and direction diagnostics stay in a clearly separated `qc/alternatives/` area and never appear as duplicate main tiles.

This meets the user's “final output only” preference without destroying information needed to audit the physical-face decision.

Source: [MASTER_LESSONS.md — L158](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md#l158-never-average-recto-and-verso-maps-or-stretch-each-ink-image-on-its-own)

---

# 6. Canonical artifact layout and naming

The repo should distinguish **actual target scroll** from **worker identity** and **experiment lineage**. Use the target scroll as the primary storage root.

Recommended example layout:

```text
Scroll-Repo/
  <TARGET_SCROLL_ID>/
    scroll.json
    volumes/
      <VOLUME_ID>/
        volume.json
        surface_tiles_1cm2/
        patches_4cm2/
        inked_patches_4cm2/
        qc/
          surfaces/
          renders/
          models/
          controls/
          alternatives/
        weave/
          manifests/
          builds/
          coverage/
        final/
        logs/
        reports/
```

Use flat stage folders, not one directory per tile. Each artifact gets a stable ID and a manifest.

Suggested names:

- Surface tile: `<SCROLL>_<VOLUME>_<PATCH_ID>_surface_1cm2.<format>`
- Stitched patch: `<SCROLL>_<VOLUME>_<PATCH_ID>_surface_4cm2.<format>`
- Canonical ink output: `<SCROLL>_<VOLUME>_<PATCH_ID>_ink_final.png`
- Internal alternatives: `<PATCH_ID>_faceA_orderX_qc.png`, `<PATCH_ID>_faceB_orderY_qc.png` with a manifest that records the physical meaning; never use ambiguous names alone.
- Weave snapshot: `<SCROLL>_<VOLUME_TOKEN>_working_weave.png` plus mesh and JSON manifest.

Example filenames are not data. Generate the real IDs only from the verified inventory.

## 6.1 Minimum tile manifest

```json
{
  "schema_version": "1.0",
  "artifact_id": "stable-id",
  "status": "PASS",
  "target_scroll_id": "verified-scroll-id",
  "target_volume_id": "verified-volume-id",
  "worker_id": "worker-or-agent-id",
  "worker_assignment_scroll": "assignment-id-or-scroll",
  "patch_id": "stable-physical-patch-id",
  "physical_bounds_mm": {
    "u_min": 0.0,
    "u_max": 10.0,
    "v_min": 0.0,
    "v_max": 10.0
  },
  "source": {
    "ct_uri": "immutable-source-reference",
    "ct_sha256": "sha256",
    "surface_uri": "immutable-surface-reference",
    "surface_sha256": "sha256"
  },
  "geometry": {
    "coordinate_frame": "declared-frame",
    "axis_convention": "declared-axes",
    "handedness": "declared-handedness",
    "voxel_size_um": [0.0, 0.0, 0.0],
    "surface_method": "method-and-version",
    "normal_grid_source": "verified-source",
    "surface_fit_config_sha256": "sha256",
    "cross_section_qc": "PASS",
    "sheet_identity_qc": "PASS",
    "ct_mask_occupancy": 0.0,
    "on_sheet_fraction": 0.0,
    "displaced_control_result": "PASS"
  },
  "render": {
    "renderer": "name-and-version",
    "render_frame": "declared-frame",
    "flip_normals": false,
    "layer_order": "control-calibrated-order",
    "render_valid_mask_sha256": "sha256",
    "blank_margin_rows": {"top": 0, "bottom": 0},
    "valid_fraction": 0.0,
    "coverage_components": 1
  },
  "ink": {
    "model_id": "name",
    "checkpoint_sha256": "sha256",
    "code_revision": "git-sha",
    "training_data_statement": "verified-source",
    "target_training_overlap_qc": "PASS",
    "positive_control_id": "control-id",
    "positive_control_status": "PASS",
    "negative_control_id": "control-id",
    "negative_control_status": "PASS",
    "physical_face": "A|B|UNRESOLVED",
    "canonical_display": true,
    "display_scale": "fixed-declared-scale"
  },
  "outputs": {
    "canonical_png": "path-or-object-uri",
    "canonical_png_sha256": "sha256",
    "alternatives_manifest": "path-or-object-uri"
  },
  "lineage": {
    "parent_artifact_ids": [],
    "job_id": "job-id",
    "run_id": "run-id",
    "code_sha": "git-sha",
    "config_sha256": "sha256"
  },
  "qc": {
    "provenance": "PASS",
    "surface": "PASS",
    "coverage": "PASS",
    "render": "PASS",
    "ink_model": "PASS",
    "human_reading_ready": true,
    "reasons": []
  }
}
```

This is a schema example, not a claim that any current artifact has these values. Production schemas must validate required fields and units, reject placeholders, and distinguish missing values from measured zeroes.

---

# 7. Agent contracts

## 7.1 Kerrigan — orchestrator

Kerrigan's job is to dispatch work and protect the evidence chain, not to treat worker confidence as truth.

Kerrigan must:

1. read the source-of-truth scroll/volume inventory and current project state before scheduling;
2. create a job declaration with hypothesis, input IDs/hashes, expected output, acceptance gates, budget, timeout, and stop condition;
3. verify prerequisites before launching the next stage;
4. route each artifact using `target_scroll_id` and `target_volume_id`, not worker branch or parent folder;
5. assign independent work only where it resolves a distinct uncertainty;
6. keep jobs resumable and outputs durable; use atomic writes and checksums;
7. prevent duplicate watchdogs/processes on the same working directory;
8. stop a batch as soon as a shared positive control fails;
9. label every result `PASS`, `FAIL`, `VOID`, `INCONCLUSIVE`, `BLOCKED`, or `NOT_RUN`;
10. maintain an append-only experiment ledger and a human-readable report of decisions;
11. update the weave only from accepted artifacts;
12. never tell the owner a task succeeded before the relevant tests actually pass.

**Resource rule:** run a cheap, informative validation sample before scaling. Do not launch 100 workers to produce 100 copies of an invalid surface or model failure.

## 7.2 Computation Swarm — surface worker

Inputs: verified scroll/volume, coordinate frame, surface prediction, required normal grids, seed/region bounds, fitting recipe, QC thresholds, resource budget.

Must return:

- the raw surface artifact and all parameters/config hashes;
- source hashes and exact volume identity;
- physical area, bounds, valid fraction, self-intersection report, on-sheet/CT occupancy, displaced control;
- cross-section montage at multiple positions and a short machine-readable QC report;
- explicit status and stop reason.

Must not return “PASS” based only on area, smoothness, no self-intersections, or a radial-normal score. A surface fails if sheet identity is uncertain or if it jumps between windings at cracks.

## 7.3 Surface/Render QA — independent validator

This role must be separate from the worker that generated the surface. It should not change the surface or tune parameters to make a tile pass.

Must inspect:

- raw CT cross-sections with the surface overlaid;
- physical sheet continuity and layer identity;
- CT support at zero and displaced offsets;
- render-valid mask, blank margins, actual coverage, disconnected regions, scale, and physical bounds;
- the expected tile type versus the actual output.

It can use vision and numeric checks together. It does not claim letters; it determines whether the artifact is a valid substrate for inference.

## 7.4 Stitching Agent

Input only accepted 1 cm² surface tiles with manifests.

Must check target identity, volume, coordinate frame, physical adjacency, common sheet identity, orientation, overlap, gaps, and seam quality. It must never stitch based only on filenames or row/column order. It emits one stitched 4 cm² patch plus a lineage manifest. If the four tiles do not represent one continuous 20 mm × 20 mm physical region, status is `VOID_STITCH_GEOMETRY`.

## 7.5 Ink Agent

Input only a surface/render artifact that passed the earlier gates, the exact positive/negative controls, the model card, and the frozen inference config.

Must:

- check checkpoint provenance and target overlap;
- run the positive control before target tiles;
- use the correct render-valid mask and margin handling;
- keep the fixed display scale;
- write canonical output plus internal alternatives and a complete manifest;
- report model score statistics, ink fraction, edge-distance profile, control scores, and negative-control results;
- stop the batch if controls fail;
- label the image `MODEL OUTPUT` until the independent reading/validation stage earns a stronger label.

The Ink Agent must not change its model, normalization, threshold, or display scale after seeing target results without declaring a new experiment. Any such change must rerun the same controls.

## 7.6 Weaving Agent

Input only accepted canonical patches.

Must update a versioned physical weave, preserve holes, validate seams and coordinates, and produce one root-level working weave per target volume only after all integration checks pass. It must never choose among unvalidated forward/reverse alternatives on visual preference alone.

## 7.7 Blind Reader / Reading Evaluator

The reader must receive a randomized set of canonical images containing hidden known positives and matched negatives. It should not see source IDs, model names, direction labels, branch names, or candidate hints. The harness must audit which images were seen and seal answers before scoring.

A failed calibration invalidates target reads. A positive read must be traced back through the exact patch manifest to the source volume and physical surface.

---

# 8. Megara: research plan for a much stronger master ink model

Megara should be developed after the pipeline can consistently produce valid, well-registered, fully masked surface patches. Otherwise the model will learn or amplify geometry and rendering artifacts.

## 8.1 First establish the target task

Separate at least four tasks:

1. **Ink detection:** probability that a valid surface location carries ink-related signal.
2. **Ink localization/segmentation:** pixel- or voxel-level map of ink-like strokes.
3. **Letter-scale legibility:** whether a human can distinguish stroke structure from texture/noise.
4. **Reading verification:** whether proposed characters can be independently defended.

A model can score well on the first task and fail the latter three. Evaluate each separately.

## 8.2 Establish a trustworthy benchmark before architecture search

- Build a provenance-complete corpus of known-text positive patches and matched no-ink negatives.
- Split by physical region/segment and, where possible, by scroll—not random adjacent pixels—so near-duplicate surface texture cannot leak across train and test.
- Keep a locked confirmation set untouched by architecture/model selection.
- Use the exact same masks, display scale, and coordinate conventions for all baselines.
- Include label-swap, displaced-surface, blank-margin, rotation/flip, and spatial-layout controls.
- Measure pixel AUC, stroke-level metrics, crop-level uncertainty, legibility/readability, false-positive floor, and performance on the untouched confirmation set.
- Keep a clear ledger of any training labels close to the target region and enforce the required 3-D exclusion zone for prize candidates.
- Never use an image as a negative merely because a model or reader did not detect ink in it.

## 8.3 Candidate model families

Investigate, do not assume, the value of:

- a strong 2-D U-Net baseline on flattened surfaces;
- 3-D-to-2-D architectures that can use local volumetric context;
- DINOv3-style pretrained visual features where the implementation, checkpoint provenance, license, input scale, and suitability are verified;
- volume-aware/self-supervised 3-D representations, potentially including DINO-like objectives adapted to the CT modality;
- carefully calibrated ensembles of complementary models;
- multi-scale/context-aware methods that preserve letter-scale details while using larger spatial context.

“State of the art” is not itself a reason to adopt a model. Each candidate must beat a declared baseline on a controlled held-out benchmark and then pass the target scan's known-text gate. Do not silently substitute a model or checkpoint whose training data are unknown.

## 8.4 Training rules

- No training/validation/test leakage across adjacent crops, repeated meshes, retraced surfaces, or overlapping physical regions.
- No pseudo-labeling loop in which a model teaches its own mistakes back to itself without independently verified labels.
- No target-region tuning on a prize candidate unless the rules permit it and the protocol records the consequences.
- Keep original CT, raw rendered signal, valid masks, and every model output separately; enhancements must not replace evidence.
- Normalize only over valid pixels. Make the mask part of the model input or the loss where appropriate.
- Record the model's no-ink floor on displaced/off-sheet controls and blank-margin controls.
- Test robustness to voxel size, scan protocol, surface curvature, thin strips, missing CT, and varying ink/texture contrast.
- Prefer an ensemble only if its confirmation performance and error analysis justify it; model agreement alone is not independent proof because models can share data, biases, and the same geometry errors.

## 8.5 Megara acceptance gate

A model is not promoted to production until it:

1. reproduces its declared baseline;
2. passes held-out known-text performance bars chosen from the reference's own score;
3. passes a separate confirmation set;
4. has an acceptable false-positive floor on no-ink/displaced controls;
5. demonstrates useful stroke-level and reader-level gains, not just pixel AUC;
6. passes the same-scan positive control on each target domain;
7. has documented training provenance, exclusions, license, checkpoint hash, inference settings, and limitations;
8. has a tested rollback path to the prior validated model.

If it fails, preserve the result and diagnose whether the failure is labels, model capacity, resolution, domain shift, geometry, rendering, normalization, or evaluation. Do not keep training merely because compute remains.

---

# 9. Reproducibility, compute, and token-efficiency rules

The old lessons are clear that process failures can be as damaging as model failures. Build these protections into the prompts and code.

- Every expensive job must be resumable from durable checkpoints. Do not rely on RAM disks or temporary session directories.
- Use one launcher per working directory; prevent concurrent watchdogs from corrupting renders or inference outputs.
- Check actual concurrency, memory, disk, permissions, GPU availability, and time limits before estimating fleet capacity.
- Run the smallest experiment that can falsify the current hypothesis. Scale only after its gates pass.
- Use singular, well-specified commands when they safely complete the job; avoid redundant conversational polling.
- Do not remove integrity checkpoints merely to reduce turns.
- Keep raw outputs, logs, manifests, environment versions, command lines, code hashes, and output hashes.
- Make writes atomic. A partial or interrupted file must never be mistaken for a completed artifact.
- Write `ALL_DONE`/completion markers only after verifying every required output and checksum.
- If a job is restarted, skip verified completed artifacts rather than recomputing them; detect partial outputs explicitly.
- Never change a fixed seed plan, model, tile size, normalization, threshold, or optimization schedule without a declared experiment change.
- Before a large fleet, test the entire input → output → manifest → restart → recovery path on one small job.
- If a dependency is unavailable, mark the job `BLOCKED`; do not substitute another tool or scroll without declaring the change.

---

# 10. Implementation sequence for the next master prompt

The next Claude Code master prompt should execute this sequence rather than launching the entire factory at once.

## Phase A — Audit and quarantine legacy artifacts

1. Inventory every existing tile, patch, image, mesh, manifest, render, and code path.
2. Resolve each image's actual target scroll, volume, source surface, model, direction, and physical bounds from the original job code/logs/manifests.
3. Compare the top-level folder, nested target path, filename, manifest, actual source URI, and hashes. Flag all disagreements.
4. Identify outputs generated without normal grids, with unverified sheet identity, with failed/insensitive controls, with blank margins, or with the wrong/stale `tifxyz`.
5. Mark suspect outputs `LEGACY_UNVERIFIED`, `VOID`, or `PROVENANCE_FAIL`; do not silently promote them to the new weave.
6. Preserve them as historical artifacts for learning, but prevent downstream agents from treating them as valid input by default.

## Phase B — Implement cheap preflight checks first

Build tests for:

- schema and required manifest fields;
- scroll/volume identity consistency;
- physical dimensions and coordinate units;
- source/checkpoint hashes;
- tile coverage, connected components, blank margins, and edge bands;
- surface on-sheet and displaced controls;
- cross-section montage generation;
- render reproduction against known references;
- positive-control pass/fail handling;
- canonical direction selection;
- stitch adjacency and seam consistency;
- restart/idempotency and completion-marker integrity.

These checks should run before expensive ink inference and should fail closed.

## Phase C — Prove one end-to-end tile

Choose one representative region with a known-text positive control in the same scan family. Demonstrate:

1. verified volume and metadata;
2. valid surface with cross-section QA;
3. one physically correct 10 mm × 10 mm surface tile;
4. valid render and mask with no unhandled blank margins;
5. known-text control pass;
6. target ink inference with a negative control;
7. one canonical final PNG and manifest;
8. successful recovery in a fresh session from the durable repository/artifact store.

Only after this succeeds should the same recipe be multiplied across sibling tiles.

## Phase D — Prove four-tile stitching

Use four adjacent accepted 1 cm² tiles on the same sheet. Confirm exact 4 cm² physical bounds, orientation, overlap, seams, and lineage. Compare against a direct larger render where possible. If the stitched output is not demonstrably equivalent or better, fix the stitcher before launching the factory.

## Phase E — Scale with gates and stop rules

- Start a small number of independent workers.
- Measure real runtime, memory, output quality, and failure rates.
- Expand only if the gate-pass rate and validated downstream value justify the cost.
- Automatically halt a batch if a shared control or provenance gate fails.
- Keep the weave and job registry current after each validated increment.

## Phase F — Train Megara against a locked benchmark

Do not begin a large architecture sweep until Phases A–E provide trustworthy inputs and a reliable benchmark. Then run the Megara plan in Section 8 with preregistered comparisons and a locked confirmation set.

---

# 11. Required completion report from Claude Code

At the end of any implementation or batch, Claude Code must report:

1. **What actually ran** — exact commands, code revision, job IDs, inputs, and outputs.
2. **What was visually inspected** — exact artifact IDs/paths; never imply that all outputs were inspected if only a sample was.
3. **Gate results** — counts of PASS, FAIL, VOID, INCONCLUSIVE, BLOCKED, and NOT_RUN at each stage.
4. **Provenance failures** — target scroll/volume mismatches, stale files, unknown hashes, missing masks, or ambiguous source paths.
5. **Geometry failures** — off-sheet fractions, cross-section findings, layer jumps, disconnected patches, and failed displaced controls.
6. **Render/ink failures** — blank margins, edge-locked bands, implausible ink fractions, positive-control metrics, negative-control floor, and fixed-scale diagnostics.
7. **Reader calibration** — hidden positive/negative performance and whether any target read is interpretable.
8. **Resource use** — elapsed time, CPU/GPU, peak memory, disk, retries, and estimated cost where measurable.
9. **Durable artifacts** — exact repository paths, object URIs, hashes, manifests, and rollback point.
10. **What remains uncertain** — separate observed facts, model predictions, hypotheses, preliminary visual impressions, and validated readings.
11. **Next action** — the smallest experiment with the greatest expected information value.

A checklist completed is not the same thing as a scientific result. The evidence decides what may be claimed.

---

# 12. Immediate conclusions

1. **Do not scale the existing image-generation pattern blindly.** The visual samples and source lessons show that many outputs can look like tiles while representing only a thin strip, partial mask, or invalid surface.
2. **Make sheet identity and raw-CT cross-sections a mandatory gate before ink inference.** The previous numeric surface gates were demonstrably insufficient.
3. **Make target-volume provenance executable.** Worker name, top-level folder, filename, and environment variables can disagree or describe different roles. Cross-check them against the actual source volume and immutable hashes.
4. **Treat blank-margin handling as a first-class pipeline stage.** Mask invalid pixels, test the exact renderer, and report both positive-control recall and false-positive floor. Reflection fill is not a universal fix.
5. **Require a known-text positive control before interpreting any target tile.** Failed controls void the target result; they do not establish absence of writing.
6. **Use one canonical final image per patch.** Keep physical-face alternatives and render-order diagnostics internally; do not show unexplained forward/reverse pairs to the main reader.
7. **Do not let the ink model inherit bad geometry.** Surface validation, render validation, model validation, and reader calibration are separate gates.
8. **Train Megara only against locked, leak-resistant evaluation and real target-domain controls.** Modern architectures—including DINO-style features and 3-D encoders—are candidates to test, not shortcuts around data quality.
9. **Preserve the failures as durable institutional memory.** Every rejected artifact should carry a reason code and a reproducible trail so the swarm does not rediscover the same mistake.
10. **Do not claim a letter, discovery, or prize-ready result until the chain from source CT to independent verification is intact.**

---

# 13. Primary repository references

- [Ruthless Vesuvius execution preamble — attached source file](RUTHLESS%20VESUVIUS%20PROMPT%20PREAMBLE.txt)
- [Scroll Lessons repository README](https://github.com/abundantjoe/scroll-lessons/blob/main/README.md)
- [worlds-first README and image inventory](https://github.com/abundantjoe/scroll-lessons/blob/main/worlds-first/README.md)
- [MASTER_LESSONS.md — complete lesson record](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md)
- [Experiment index](https://github.com/abundantjoe/scroll-lessons/blob/main/experiments/README.md)
- [PHerc0191 First Letters worker branch README](https://github.com/abundantjoe/scroll-lessons/blob/sib-fl-pherc0191/README.md)
- [p4v-15 worker branch README](https://github.com/abundantjoe/scroll-lessons/blob/sib-p4v-15/README.md)
- [p4v-15 FL-4 tiler implementation](https://github.com/abundantjoe/scroll-lessons/blob/sib-p4v-15/tools/sib/p4v-15/fl4/fl4.py)
- [p4v-15 FL-4 launcher](https://github.com/abundantjoe/scroll-lessons/blob/sib-p4v-15/tools/sib/p4v-15/fl4/run.sh)
- [p4v-15 FL-4 worker brief](https://github.com/abundantjoe/scroll-lessons/blob/sib-p4v-15/tools/sib/p4v-15/fl4/BRIEF_FL4.md)
- [Dominion release and stripqc findings](https://github.com/abundantjoe/scroll-lessons/blob/dominion-release/README.md)
- [Megara model-evaluation repository snapshot](https://github.com/abundantjoe/scroll-lessons/tree/megara)

## Evidence discipline for future updates

When new evidence changes a conclusion, update this document with a dated entry. Preserve the prior claim, mark it `SUPERSEDED` or `RETRACTED` as appropriate, and link the code, artifact, test, and run that changed the conclusion. Never silently rewrite history to make the project look cleaner than it was.
