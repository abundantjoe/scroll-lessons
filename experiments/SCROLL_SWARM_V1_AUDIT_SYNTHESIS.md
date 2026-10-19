# Scroll Swarm v1 — Evidence Audit and Scroll Factory Transfer Brief

**Prepared:** 2026-10-19  
**Purpose:** Preserve the most decision-relevant findings from the uploaded `MASTER_LESSONS.md` and the accessible `abundantjoe/scroll-swarm` repository before designing Scroll Factory agents.  
**Scope:** Retrospective analysis only. This document does not modify Scroll Swarm, validate a new surface, or claim a prize discovery.

## 1. Executive conclusion

The prior work generated a great deal of useful engineering knowledge, but it did **not** establish a winning First Letters pipeline. The repository's own October 15 release summary states that no letters or candidate had been found on an unread eligible scroll. Its central diagnosis is that both geometry and ink/readability failed: surfaces did not consistently remain on one physical sheet, and public ink models did not produce letter-legible output on new bulk scans.

That result does not mean the scrolls are blank, the challenge is impossible, or every old technique is useless. It means the team's negative results are limited by the demonstrated sensitivity and validity of the specific geometry, renderer, model, and reader pipelines. A null from an invalid surface or an insensitive model is not evidence of absence.

**The strongest design principle for Scroll Factory is to make every handoff evidence-bearing and recoverable:** a downstream agent receives only a durable, hashed, validated artifact with explicit physical coordinates, source lineage, configuration, and limitations. It must not infer validity from a filename, job marker, nominal area, model probability, or upstream agent's statement alone.

## 2. Sources reviewed and review limits

### 2.1 `MASTER_LESSONS.md`

I inspected the file's structure and full lesson records in numbered ranges, including each lesson's title, stated trap, stated fix, and evidence label; the golden rules; the retraction section; the open-problem section; the timeline/experiment register; and the operations lessons. The document describes itself as about 168,246 words and reports 656 lessons classified by its authors as 404 VERIFIED, 216 MEASURED, and 36 INFERENCE, plus 256 retracted claims and 93 open problems.

Those labels describe the source document's classification. They do not independently prove that each claim is true. In particular:

- **VERIFIED** means the lesson authors say there is a recorded test, control, independent audit, or exact reproduction. The test may still have limited scope or a blind spot.
- **MEASURED** means a number was recorded, not that the number settles the larger scientific claim.
- **INFERENCE** is a reasoned but untested conclusion.
- **RETRACTED** claims must not be reused as facts. Use the specified correction and inspect its source if the claim matters to a new decision.

### 2.2 `scroll-swarm`

I inspected repository metadata, the `main` branch tree, the available branch inventory, and the repository's branch-audit/errata records. I reviewed the 53-row experiment ledger, state of work, scroll triage, decisions, release results, reproduction guide, lessons, usage-optimization log, compute policy, context-recovery guide, and relevant release/branch records. The repository describes a release audit covering 31 pre-survey worker branches and eight survey branches.

The repository is approximately 515 MB by GitHub's reported size and includes many derived binary artifacts and experiment outputs. I did not download and visually open every binary image, mesh, volume, and log from every branch individually. The findings below use the comprehensive lesson/experiment indexes and recorded branch audit, with that limitation made explicit rather than implying a byte-by-byte independent audit of every artifact.

The evidence cutoff for the repository's stated experiment results is principally October 15, 2026. Any rule, data inventory, eligibility statement, or external tool behavior must be re-verified before future execution or submission.

## 3. Current result state reported by Scroll Swarm v1

The repository's experiment ledger contains **53 experiments: 50 COMPLETED, 2 FAILED, and 1 BLOCKED**. “Completed” means the experiment reached its recorded terminal status; it does not mean the hypothesis succeeded or a prize condition was met.

The headline results reported in `docs/release/RESULTS.md` are:

1. **Renderer reproducibility can be excellent when the correct invocation and orientation are used.** One official surface-render reproduction reached correlation around 0.999997 and 99.649% exact voxels; without the required normal flip, the same comparison was badly wrong. That is a software parity result, not a surface-quality result.
2. **The production 2.4 µm reader could reproduce an organizer map on known text when the required recipe and context margin were used.** The earlier margin-less attempts failed their declared fidelity gates because of the harness/input context, not because the underlying official reader was intrinsically incapable of reproducing its reference.
3. **The spiral fitter is expensive on the measured CPU-only workers.** Reduced-loss CPU fitting was about 1.68 seconds per step; with official tracks, reported cost was about 17.2–21.7 seconds per step on a 1,000-slice window. A 4,000-slice window exceeded the measured memory limit before step 0. The 30,000-step recipe was estimated at roughly a week to ten days per container. A successful process launch did not validate its geometry.
4. **The official surface tracer required normal-grid data for repeatable sheet-following.** Grid runs agreed to a measured median of about 10 µm; no-grid runs diverged by hundreds to over a thousand micrometers and visibly crossed layering. The no-grid path was faster but scientifically unreliable for surface construction.
5. **Raster-canvas area is not true physical mesh area.** PHerc0800 canvas area overstated true area by roughly 1.9–2.1× in the measured segment set. The three largest raw PHerc1203 meshes self-intersected; none was both crossing-free and at least 4 cm².
6. **A numeric sheet-continuity gate is only a screen.** The recorded held-out controls discriminated the small tested set, but ramps of about 1 mm or more could evade the gate, and the gate did not identify which of several parallel sheets was traced. Cross-sectional CT inspection remained necessary.
7. **The bulk `ink_9um` model showed pixel-level signal on known text but not dependable reading.** Held-out known-text AUCs were reported around 0.742 (9.366 µm) and 0.781 (8.64 µm), with broad confidence intervals. Those are scan-specific calibration results, not evidence that the output is legible or transfers to every scroll.
8. **Bulk blind-reading tests did not pass their pre-registered positive-control criteria.** EXP-0051 found no adequate size/criterion cell for reader recognition of known text in the tested bulk figures. EXP-0052's pre-registered A1/A2 tests failed. Because the positive controls failed, these experiments cannot establish that unread target regions contain no writing, nor do they establish a universal limit on bulk-scan methods.
9. **The 21-scroll growth screen was technically selective, not a universal solution.** The recorded summary says 5 of 21 eligible scrolls yielded a bulk surface of at least 4 cm² passing the then-binding gate; 9 failed at pre-check/early blocks and 4 remained unresolved. The bulk surveys of PHerc1203 and PHerc0846A inked 13 surfaces and produced zero candidates under the specific detector and decision protocol.
10. **No result in the release qualifies as a letter discovery.** FLOOR, NOT CANDIDATE, INDETERMINATE, failed positive control, invalid geometry, and no-data are distinct states and must remain distinct.

### Important experiment clusters

- **EXP-0000–0005:** Environment/data inventory, CPU ink smoke test, robustness screen, CPU spiral-fit measurements, VC3D render parity, and the prohibitive cost of spiral fits with tracks.
- **EXP-0006–0014:** Growth of existing PHerc0800 segments, calibrated ink controls, failed expansion to a sufficiently large verified area, raw PHerc1203 mesh survey, seeded growth, and normal-grid ablation. The normal-grid ablation is among the most transferable findings.
- **EXP-0016–0034:** More growth, mesh identity/orientation gates, layered-surface triage, multiple scroll-specific growth trials, and first patch-factory surveys. Some promising ranking/area metrics failed once checked against papyrus identity or cross-sections.
- **EXP-0035–0042:** Scan-type ink calibration and targeted PHerc1203/PHerc0846A patch work. Findings differ by resolution and model; do not blend them into a single “ink detector works” statement.
- **EXP-0043–0048:** Production-reader fidelity tests, context-margin correction, blind-read field-size calibration, centring tests, and surface re-centring. Context-free input could fail reader parity even when the interior matched; centring was not the general explanation for weak bulk ink output.
- **EXP-0049–0052:** Bulk surveys and blind-read/legibility controls. They did not produce a qualifying candidate, and their own failed controls limit any general claim about absence of ink.

## 4. Cross-cutting lessons that matter most for Scroll Factory

### 4.1 Geometry validity precedes stitching and ink

A mesh can have a large nominal area, zero self-intersections, high forward/backward consistency, a good radial metric, and local tangency to a predicted normal field while still following the wrong sheet or jumping at cracks. No single cheap statistic in the record consistently certified sheet identity on crushed scrolls.

Carry forward:

- Use the official normal grids when the actual tracer implementation requires them.
- Measure the actual volume's metadata, scan protocol, coordinate frame, handedness, axis, pitch, and surface scale; never inherit another scroll's defaults without validation.
- Check CT occupancy and no-data coverage inside the mesh-valid area.
- Inspect cross-sections in multiple locations, especially around cracks, overlaps, steep bends, and seams.
- Test geometric gates on known positive and known negative cases, including a displaced or wrong-sheet control.
- Record the limits of each gate. “Passed the screen” is not the same as “certified continuous papyrus surface.”

### 4.2 Independent windows/tiles do not automatically stitch

The documented PHerc0268 spiral-window experiments reported seams of 8–56 voxels and winding indices that disagreed by 3–15 sheets. The prescribed lesson was to match windings by geometry in overlapping regions and check offset-chain closure, or use a globally coherent fit—not concatenate by local winding index.

This is a direct warning for the new one-cm² → four-cm² factory. **Small jobs are good for compute isolation and durable checkpointing, but independently reconstructed tiles cannot be assumed to be a coherent surface.** Before stitching, each input needs a stable mapping into the same volume/physical coordinate system and evidence that it belongs to the same physical sheet. The stitcher needs overlap/seam validation, not just four files with areas that sum to 4 cm².

If a coherent global surface cannot be established, preserve the tiles as separate candidates or components. Do not fabricate continuity by interpolating gaps or joining nearby-but-distinct windings.

### 4.3 A weaving image is not automatically a continuous physical surface

An atlas or working mosaic can be useful for monitoring progress, but patches from different or uncertain sheets cannot be made into one physical mesh merely by arranging their PNGs. The weave should represent accepted patch components, their physical positions, and explicit gaps/unknown coverage. Only claim continuous surface continuity where the geometry and coordinate mappings demonstrate it.

The full-resolution mesh/render should be versioned and durably stored. A root-level preview plus a manifest/pointer is safer than repeatedly overwriting the only copy of a huge PNG or mesh.

### 4.4 Ink inference must have same-pipeline positive controls

Every model/checkpoint and inference recipe needs a positive-control gate on known text of an appropriate scan protocol/material, using the same rendering, depth order, context, scaling, and display/inference code planned for the target. Check checkpoint training data and label proximity first. A public checkpoint can be blind on a new scroll; a good AUC can coexist with maps that readers cannot read.

A failed gate means the target null is uninformative and the target read should not proceed. A passing known-text gate validates only the tested material/conditions; it does not validate geometry or prove target letters.

Where the current plan uses the bulk `ink_9um` route, remember that Scroll Swarm v1's bulk reader positive controls failed. Do not blindly reuse its old thresholds or call its nulls evidence that a region is blank. The user intends to revisit the ink agent/model, so treat this as the baseline problem to solve rather than a final answer about which model to use.

### 4.5 Preprocessing and validity masks can manufacture or suppress ink

The lessons document several high-impact issues:

- Zero-valued render margins entered patch normalization/blending, producing bright bands in some outputs and suppressing genuine signal in others.
- Model output can be nonzero outside render-valid pixels; use an explicit valid-pixel mask derived from actual CT/render coverage, not `p > 0`.
- Fixed global display thresholds or per-image auto-stretch can hide signal or turn noise into visually persuasive structure.
- A model's official depth ordering is determined by matching a known-text control, not by assuming what “forward”, “reverse”, or “outer” means.
- A one-layer shift or missing context margin can change reader fidelity materially.
- The exact mesh used for rendering must be the one recorded/published, with crop offsets preserved.
- Padding or margin-fill can restore sensitivity but can increase false positives; measure both positive recall and the no-ink/off-letter floor.

For the future Ink Agent, keep separate artifacts for original patch, valid mask, prepared model input, raw model output, calibrated display, and final interpretation. Every transformation must be recorded and repeatable.

### 4.6 Metrics require appropriate controls and independent units

Pixel counts are not independent observations when pixels are spatially correlated. Use tile/letter/block/strip-level resampling or other justified units and report effective sample size. Compare each score to a bar measured with the same metric, mask, resolution, and pipeline stage. A metric selected after seeing the target is exploratory, not confirmatory.

For every gate:

- Verify that the positive and negative cases exist in the batch.
- Verify that both classes and sufficient spatial coverage exist before training or scoring.
- Confirm the metric itself passes on its reference/control.
- Include a negative/control that actually tests the failure mode of concern.
- Freeze source code, parameters, data lists, and decision thresholds before looking at deciding target data where a confirmatory claim is planned.
- Keep failed and superseded numbers rather than overwriting them.

### 4.7 Distinguish missing data from blank papyrus

A missing S3/zarr chunk can render as zero or blank and masquerade as a negative. Some public volumes are masked or truncated. Some tiles lie outside scan coverage. A blank-looking output must first pass input completeness and coverage checks. Record NO-DATA/INVALID separately from BLANK/NO-SIGNAL.

### 4.8 Compute and session operations

The lessons strongly support the low-turn approach, but also correct some common assumptions about cloud sessions:

- Full worker assignments should be included at launch; follow-on messages are not reliably accepted.
- Prefer one well-designed detached/bounded command per compute job and push/checkpoint each completed unit. Minimize AI-directed status chatter and polling.
- Long jobs can die when a session idles; the recorded harness killed background jobs at two hours. Do not assume a process survives the session/container.
- A “sent” message is not delivered, and an accepted job description is not evidence the job ran.
- Session count is not compute. Sessions share account usage limits and may contend for resources; more sessions can burn budget rather than increase useful throughput.
- The recorded environment was about 4 vCPU, 15 GB RAM, ~30–31 GB disk, no GPU. Measure each new worker; don't treat this as a guarantee for future managed agents.
- Avoid concurrent CPU-heavy jobs on the same 4-vCPU VM. Estimate data transfer, normal-grid footprint, memory, and disk before dispatch.
- Every waiting task needs a deadline and fallback; never let dependent agents idle for hours because an upstream artifact is missing.
- Workers must return a status file, counts, pinned code/config hashes, output references, and verified completion status.
- Smoke-test every new script on a small crop before launching a fleet. A zero-work loop or missing dependency must not report success.

### 4.9 Durable artifacts, manifests, and Git discipline

The strongest direct transfer to `Scroll-Repo` is:

- Use GitHub for code, manifests, indexes, documentation, task state, schemas, and small reports; use authorized durable artifact storage for large meshes, renders, arrays, checkpoints, and tile data.
- The source data bucket and derived-artifact location must be separate and explicitly configured.
- Upload outputs immediately after the atomic unit completes, verify the uploaded object by checksum where possible, then mark the job complete.
- Each artifact needs a stable ID, source/parent IDs, source/config hashes, physical extent, coordinate frame, code/model version, checksum, storage URI, validation state, and producer job ID.
- Cache keys must include the source identity as well as the item/region; file existence alone is not a valid cache hit.
- A completion marker is a claim to verify, not proof that every chunk exists.
- Do not suppress tool errors inside a gate. Missing output must be an ERROR, not a failed scientific test or a silent rejection.
- Do not overwrite cited results. Write immutable versioned outputs and promote a new “current” pointer only after validation.
- Check `.gitignore`, LFS configuration, and actual remote contents; a local file or `git add` command does not prove the binary was committed or uploaded.
- Avoid whole-directory checkout from older worker branches; it can silently revert newer files. Integrate only the intended files after diffing against the merge base and validating manifests.

### 4.10 Reproducibility and honest reporting

The lessons repeatedly correct overclaims: numbers were rounded outward, files were claimed before they existed, missing inputs were reported as gate failures, model agreement was treated as ground truth, and typed timestamps were treated as proof of preregistration. The permanent standard should be:

- Verify every number against the artifact that produced it.
- Store exact source/output hashes and report exactly what was verified.
- Separate VERIFIED FACT, MEASURED, INFERENCE, HYPOTHESIS, UNKNOWN, FAILED, VOID, and BLOCKED.
- Label independent reproductions accurately; same-stack deterministic reruns are reproducibility checks, not necessarily independent reproduction.
- Keep one immutable record per run and preserve all superseded claims with explicit corrections.
- Do not declare a discovery, submission, publication, or worker completion before the real event occurred.

## 5. Scroll Swarm repository audit findings

### 5.1 Branch/control-plane inconsistency

The repository's current GitHub metadata reports visibility `public`, while its own project state and release plan say the full control-plane repository should remain private and a deny-by-default curated export should be created for public release. The repository's default `main` tree contains only `LICENSE`; the bulk of the work and release material is on `claude/friendly-clarke-prs3al` and worker branches. This means a reviewer who opens the default branch will not see the actual research state, and the current public visibility conflicts with the repository's own written confidentiality plan.

**Recommended action:** Since the review phase is now complete, make the control-plane repository private unless there is a deliberate, rules-checked reason not to. Then verify branch visibility and public artifacts; do not assume changing the default branch or deleting a visible file erases already exposed history. Keep any future public release as an explicitly curated, founder-approved export after a confidentiality and license scrub.

This is an operational risk assessment based on the current repo metadata and its own policy files; no repository visibility changes were made in this review.

### 5.2 The working branch has useful evidence that `main` lacks

The control-plane branch includes a canonical state, decisions, scroll triage, experiment ledger, record errata, release results, reproduction guide, lessons, compute policy, context recovery, usage optimization log, and a curated public-export plan. Its state report says the current best candidate is **none** and that an experiment freeze was in force on October 15, 2026. Those are historical project-state records, not a substitute for checking current official rules or the founder's current direction.

The release-authored branch audit says the worker reports/results were checked and integrated into the release branch at the non-binary-file level, while some binary output differences and local-only artifacts remained. The record also documents manifest timestamp mismatches, missing/empty checksums, stale manifests, and a case where a “REPRO FAIL” was actually a setup error. Those records are exactly why the new artifact registry must independently verify files.

### 5.3 Public release vs. internal research

The project designed a deny-by-default public export and withheld certain text/reader-return content pending permission. Because the GitHub repository itself is public and working/worker branches exist, do not assume that “not exported from the release folder” means “not publicly reachable.” Review the actual branch history and accessible artifact locations.

## 6. Implications for the planned Scroll Factory

The revised agentic workflow can improve reliability and scale, but it must not repeat the old core failure: multiplying invalid surface candidates and running more inference over them.

### Kerrigan: orchestrator

- Use one canonical job registry and one artifact registry, not separate mutable truths across many markdown files.
- Assign fully specified, one-turn-friendly jobs with exact input IDs, coordinates, code/config hashes, output schema, budget, and acceptance criteria.
- Do not dispatch an expensive child stage until its prerequisite stage has a verified durable artifact and a passed gate.
- Batch deterministic operations and minimize polling, but keep validation and state transitions explicit.
- Use an aggregate status view and event-driven completion when supported; do not repeatedly wake the model to ask whether a process is still running.
- Reconcile existing jobs before retrying; track FAILED vs VOID vs BLOCKED distinctly.

### Computation Swarm: 1 cm² tile outputs

Before coding, define what “surface tile” means: raw source/fiber evidence, a predicted surface, a grown mesh, or another representation. These are not interchangeable.

Each tile must contain a physical bounding box, volume coordinate frame, valid/data-coverage mask, source references, resolution/voxel metadata, exact method/config/model version, checksum, and validation measurements. If the chosen method uses normal grids or other shared priors, tile computation must use the required inputs.

Tiling is an execution/persistence unit; it is not permission to fit arbitrary independent local surfaces that have no shared coordinate or sheet identity.

### Stitching Agent: four 1 cm² tiles into a nominal 4 cm² patch

Require more than area arithmetic. Verify actual measured area after boundary overlap, completeness, physical adjacency, coordinate alignment, same-sheet identity, orientation, overlap seam residuals, mesh validity, and cross-sectional support. Reject or quarantine seams that show layer jumps. Store the contributing source tile IDs and exact transformations.

A nominal 20 mm × 20 mm square can be the intended target, but the qualifying physical-area rule and exact geometry must be checked against current official rules. The output may have incomplete or irregular coverage; it must declare that rather than silently padding holes.

### Ink Agent

Consume only accepted four-square-centimeter patches. Keep original patch, valid mask, model-input tensor/render, raw prediction, visualization, and decision report as separate artifacts. Require a same-material known-text positive control under identical preprocessing and depth-order rules; require appropriate negatives; use predeclared model- and scan-specific thresholds; report a failed control as uninformative rather than “no ink.” The new ink architecture is intentionally left open for the user's forthcoming design changes.

### Weaving Agent

Consume accepted inked-patch artifacts, but keep spatial identity and physical provenance. It may create a working atlas/mosaic of known patch components; it must not claim one continuous physical sheet if patches have not passed continuity and alignment gates. Show gaps as gaps. Version the whole weave; store large images/meshes in durable storage, keep a pointer/manifest and suitable preview at the scroll root, and atomically update the root pointer only after the next build validates.

### Scroll-Repo / durable storage

- GitHub `Scroll-Repo` should hold the scroll/volume skeleton, schemas, flat stage manifests, job registry/indexes, validation code, and concise human-readable summaries.
- AWS should hold the actual large derived artifacts in an authorized, separate output bucket/prefix. Keep original source prefixes read-only.
- One flat artifact directory per stage is reasonable. Do not make a folder per tile. Use unique artifact IDs and manifests to catalogue many flat outputs.
- A job cannot be COMPLETED until the output exists, its manifest validates, its durable upload is verified, and a fresh process can resolve the artifact by ID.
- Preserve old weave builds. Never rely on a mutable working PNG/mesh as the only copy of the research state.

## 7. Things that must not be carried forward as settled facts

1. **No-winner state is not “no text exists.”** The prior model/geometry pipeline did not produce a candidate; many nulls were bounded or uninformative.
2. **“VERIFIED” in the lessons document does not mean universal.** Read the scan, surface, metric, and control scope on each lesson.
3. **AUC, correlation, seed agreement, and image appearance are not legibility.** Pixel detection, reader perception, correct transcription, and prize qualification are distinct levels.
4. **A passing numeric geometry gate does not prove sheet identity.** Known controls and cross-sections are mandatory until a stronger gate is independently demonstrated.
5. **A stitched image is not proof of a stitched mesh.** Tile boundary agreement must be tested in 3-D/physical coordinates.
6. **The old D-0036 bulk-only instruction and other choices are dated project decisions.** They should be treated as historical unless the founder confirms that they remain in force for the new factory. Never silently import the old work's scope into the new design.
7. **All old thresholds are method-specific until revalidated.** This includes growth gates, ink Δr/ΔIoU cutoffs, reader acceptance bars, and rendering thresholds.
8. **The 21-scroll count and other eligibility facts are date-scoped.** Re-fetch the official prize rules and scan catalogue before any new survey or submission.
9. **The repository's “public release” plan cannot be assumed to match current GitHub exposure.** Verify actual visibility and contents.
10. **Parallelism is not a result.** The lesson set documents hundreds of sessions burning usage, shared account limits, idle kills, disk failures, and large setup costs. Scale only proven independent work.

## 8. Highest-priority operating rules to transfer into future agent prompts

1. Recover state from repository/artifact registry before acting.
2. Check current eligibility, licensing, scan metadata, and input availability.
3. Use one full, bounded initial brief per worker; verify selected model and supported launch mechanism.
4. Batch deterministic steps into a single well-structured command/script where safe; avoid unnecessary AI turns and polling.
5. Smoke-test the exact driver on one small, known case before dispatching a fleet.
6. Validate the actual geometry before rendering/inking; fail closed on invalid, missing, or ambiguous inputs.
7. Require same-pipeline positive and negative controls before interpreting a model output.
8. Predefine thresholds, code/config hashes, and stopping criteria; record deviations and post-hoc work explicitly.
9. Save every completed unit to durable storage and update manifests immediately; verify checksums and lineage.
10. Never treat empty output, missing chunks, zero seed count, failed dependency, or empty hashes as a scientific negative.
11. Never overwrite a cited result. Use immutable versions plus a validated current pointer.
12. Audit the model's documented training data and calculate the target region's separation from training labels before claiming independent generalization.
13. Distinguish NO-DATA, INVALID-GEOMETRY, FAILED-CONTROL, MODEL-NULL, INDETERMINATE, and BLANK.
14. Report only what the measured evidence supports, including limitations and false-positive controls.
15. Keep the project-wide status and reproducibility path clear on the default branch, and produce a monthly, independently reproducible progress record.

## 9. Open design questions to resolve before the agent system prompts

These are decisions, not assumptions:

1. What exact representation does the Computation Swarm produce for a “1 cm² surface tile”: raw CT/fiber features, surface prediction, grown mesh, or some combination?
2. What is the canonical 3-D coordinate frame and physical scale for every output? How will tiles from one volume share transforms and sheet identity?
3. How are tile overlap and seam regions defined, and which validated metric rejects a join that crosses onto a neighbouring winding?
4. Is the goal of `working_weave` a physical 3-D continuous mesh, a 2-D atlas of separately validated patches, or both? They should be separate outputs if their invariants differ.
5. Which current ink model and scan level are intended, what exact inference recipe is supported, and what known-text gate will qualify it? This remains intentionally unresolved pending the user's ink-model discussion.
6. What is the authorized durable AWS output bucket/prefix, retention policy, checksum method, and GitHub metadata boundary?
7. What are the current official First Letters area and evidence requirements, and what material/model use remains permitted?
8. Which exact status transitions allow Kerrigan to dispatch Stitching, Ink, and Weaving without accepting stale, duplicate, partial, or invalid artifacts?

## 10. Bottom line

The old system's highest-value contribution is not a winning model or a universal surface algorithm. It is the accumulated map of failure modes, calibrated controls, reproducible tools, and mistakes that must not be repeated.

The new factory should use small units for scheduling and recovery, durable artifact storage for survival across ephemeral sessions, and explicit contracts for handoffs. But its scientific pipeline must remain globally coherent where sheet identity depends on neighboring geometry, and its ink model must demonstrate sensitivity on appropriate known text before a target null is interpreted.

The correct goal is: **many inexpensive, traceable attempts; a strict geometry gate; a validated ink gate; a recoverable weave; and no claim stronger than the evidence.**
