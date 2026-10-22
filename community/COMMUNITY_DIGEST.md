# Vesuvius Challenge Community Digest, 2023 to October 2026

This is a short digest of what the Vesuvius Challenge Discord community learned, drawn from an export of 41,734 messages in 731 threads (2023-02-27 to 2026-10-20).
The full AI-written review is the large file beside this one, [VESUVIUS_COMMUNITY_PROGRESS_AND_NOTES.md](VESUVIUS_COMMUNITY_PROGRESS_AND_NOTES.md). It is useful for context but unverified as a whole.
Verified details, quotes and sources are in [MASTER_LESSONS.md Part 8](../MASTER_LESSONS.md#part-8-lessons-from-scroll-swarm-and-the-vesuvius-community-added-2026-10-22). Each lesson below links its ID there (for example [L700](../MASTER_LESSONS.md#l700-check-an-eligible-scroll-surfaces-sheet-contrast-against-many-curated-surfaces-before-blaming-the-ink-model)).

**How to read this file.** Anything marked "(summary, unverified)" comes only from the AI-written review and was not checked against the raw export. Everything else comes from Part 8, where each lesson carries a label. "MEASURED" there means a number is the poster's own; "VERIFIED" means a second person or a control reproduced it. Organizer statements are what was said on that date, not tested results. Contributors are named only by public Discord display name, and only where they published a tool or report.

**How this file is organised.** It starts with the state of play and a timeline. A long chapter then goes topic by topic, with findings, tools and open questions. Short sections follow on current rules, the costliest traps, retracted claims and rules for AI agents. A last section explains the sources and their limits.

**What this file leaves out on purpose.** It contains no scroll text, no readings, no letter identities and no candidate locations. The data terms keep scroll text inside the official Discord.

**A short glossary.**
- **Segment / surface / mesh:** a traced 3-D surface that follows one papyrus sheet inside the CT volume. A **tifxyz** is the standard file format for one (three float images of x, y and z).
- **Winding / wrap:** one turn of the rolled scroll. A **sheet switch** is when a traced surface jumps by mistake from one turn to the next.
- **Spiral fit:** a whole-scroll model of the rolled sheet, fitted to the CT.
- **Ink model / checkpoint:** a trained neural network (one saved set of weights) that marks likely ink on a rendered surface. **ink_9um** is the family of released models for scans at about 9 micrometres (um) per voxel.
- **AUC / F1 / Dice:** standard scores for how well a prediction matches labels. 0.5 AUC is chance; 1.0 is perfect.
- **Held-out:** data the model or method never saw while being built or tuned.
- **Pre-registration:** publishing the test and its pass/fail rule (often as a hash) before seeing the result.
- **villa / vesuvius / VC3D:** the organizers' code repository, its Python package, and the Volume Cartographer 3-D viewer and tracer.

---

## The state of play in October 2026

- **One First Letters prize has been paid on the current list.** A $50K First Letters prize was awarded for PHerc. 343 on 2026-10-08. After that, "There are 21 scrolls still eligible" (announcement, 2026-10-08). [L662](../MASTER_LESSONS.md#l662-re-check-the-eligible-scroll-list-at-every-cycle-scrolls-are-added-and-withdrawn)

- **The eligible list moves.** Ten more scans were added on 2026-09-10. PHerc 1447 was withdrawn from First Letters on 2026-09-24 after a 9 um recipe found ink there, though it "still remains eligible for the Grand Prize". Organizers say many submissions go to "the same small ROIs of the same 3-4 scrolls". [L662](../MASTER_LESSONS.md#l662-re-check-the-eligible-scroll-list-at-every-cycle-scrolls-are-added-and-withdrawn)

- **Evidence must come from the listed volume.** Models may be trained on finer scans, even of the same scroll. But the submitted prediction must be generated from the listed eligible volume (for example the 9.362 um scan), not registered onto it from a finer scan. [L657](../MASTER_LESSONS.md#l657-derive-all-submitted-first-letters-evidence-from-the-listed-eligible-volume-other-scans-may-only-train-models)

- **Large model windows are now allowed.** The old rule kept ink-model inputs to about one letter or less, to stop models inventing strokes. Since 2026-09-10 larger windows are allowed, but the submitter must show the text is not hallucinated. [L658](../MASTER_LESSONS.md#l658-large-ink-model-windows-are-now-allowed-but-you-must-show-the-text-is-not-hallucinated)

- **Per-scroll models still beat cross-scroll models.** The released 9 um models are the organizers' best for generalising across scrolls, "but per-scroll models still work better". Clarity drops from 2.4 um to about 8-9 um scans, and the drop "seems somewhat consistent across scrolls". [L739](../MASTER_LESSONS.md#l739-per-scroll-ink-models-still-beat-the-cross-scroll-9-um-models-pair-any-cross-scroll-null-with-a-same-scroll-positive-control)

- **No model is known to read letters straight from 9 um CT in 3-D.** Asked whether a CT-direct model reads letters at 8.64 or 9.36 um, an organizer said "not that we're aware" (2026-10-10). [L749](../MASTER_LESSONS.md#l749-treat-3-d-ink-predictions-as-likely-ink-not-physical-ground-truth-no-ct-direct-model-is-known-to-read-at-9-um)

- **The released 9 um ink checkpoints are not interchangeable.** The 14 checkpoints vary by up to 0.14 balanced accuracy, and the "obvious default" was the worst of the 14 on one test region. [L723](../MASTER_LESSONS.md#l723-treat-each-released-ink9um-checkpoint-as-a-separate-instrument-select-by-held-out-score-per-region-and-do-not-ensemble-by-default)

- **Surface quality on eligible scrolls is often the real limit.** Auto-made meshes can run past the material into air, switch sheets, or sit off the sheet. On one benchmark of 213 confirmed real switches, the most-used detector caught about 1 in 9. [L702](../MASTER_LESSONS.md#l702-measure-the-fraction-of-each-mesh-lying-outside-ct-support-and-the-gap-to-adjacent-winding-segments) [L705](../MASTER_LESSONS.md#l705-expect-current-sheet-switch-detectors-to-miss-most-real-switches-benchmark-them-on-confirmed-switches-with-smooth-bend-negatives)

- **Much of the 2026 work was fixing silent bugs.** Members found and fixed defects in shared data and code: wrong pyramid levels, wrong default normalization, a disabled download cache, phantom "sheet" on empty CT, untrained model heads, and commands that report success after doing nothing. [L667](../MASTER_LESSONS.md#l667-rebuild-96-um-inputs-from-level-0-in-18-of-33-hf-ink-bucket-surface-volumes-level-2-holds-only-17-of-65-depth-slices) [L668](../MASTER_LESSONS.md#l668-pass-the-checkpoints-own-ct-normalization-to-vesuviuspredict-the-default-z-scores-each-volume) [L671](../MASTER_LESSONS.md#l671-published-m7-surface-maps-mark-sheet-on-zero-ct-mask-them-by-ct--0-for-statistics-but-do-not-threshold-them-by-ct-intensity) [L672](../MASTER_LESSONS.md#l672-count-bytes-received-during-remote-inference-zarr-3-silently-disabled-villas-chunk-cache) [L675](../MASTER_LESSONS.md#l675-treat-a-zero-result-success-as-a-failure-and-assert-output-shapes-against-the-source) [L722](../MASTER_LESSONS.md#l722-smoke-test-every-published-ink-checkpoint-on-labelled-ink-some-ship-with-an-untrained-head-that-outputs-05-everywhere)

- **AI agents now do a large share of the posting.** LLM-written reports have their own channel (#robots) with disclosure rules. Organizers warn that the project has no robust automatic verifier, so humans must set goals and check images at every stage. [L665](../MASTER_LESSONS.md#l665-post-llm-written-reports-in-robots-name-the-model-and-separate-its-output-from-human-commentary) [L764](../MASTER_LESSONS.md#l764-have-a-human-set-each-experiments-goal-and-success-criterion-this-project-has-no-robust-automatic-verifier)

- **Spiral-fitting whole prize scrolls is an open, cheap route.** Organizers suggested it would "likely result in a fairly large number of decent areas", and said in August 2026 that "afaik nobody has ran the spiral fit on almost all of the prize scrolls". This is untested in the export. [L721](../MASTER_LESSONS.md#l721-organizers-suggest-spiral-fitting-whole-prize-scrolls-as-a-cheap-first-letters-route-test-it-with-a-pre-registered-coverage-and-ink-check)

- **Pixel scores are not legibility.** A held-out AUC of about 0.74-0.78 on bulk 9 um maps gave readers at most 1-2 letter forms per 4 cm² in one project's tests. [L784](../MASTER_LESSONS.md#l784-a-bulk-ink9um-auc-near-074-078-is-pixel-signal-not-legibility)

---

## Timeline

Items marked "(summary, unverified)" come only from the AI-written review's chronology. The rest are dated in Part 8 lessons.

### 2023

- **Launch and first prizes.** The challenge opened with open CT data and Kaggle ink-detection fragments. The first open-source prizes were awarded in April, and a $35,000 segmentation prize was announced on 2023-04-21 (summary, unverified).

- **Basic physics settled.** The scanning team said ink is "not completely radiolucent" and has "roughly the same radiodensity as the papyrus". Elemental contrast on opened fragments showed "mixed results" across scrolls. [L750](../MASTER_LESSONS.md#l750-plan-for-carbon-ink-with-roughly-papyrus-radiodensity-elemental-contrast-is-scroll-specific)

- **Labels known to be imperfect.** Organizers explained that fragment labels were aligned by hand with Puppet Warp in Photoshop, "a largely manual process that we know introduces error" (2023-03-31). [L743](../MASTER_LESSONS.md#l743-fragment-ink-labels-are-hand-aligned-and-partly-wrong-down-weight-their-boundaries)

- **Data-handling traps.** Members found 16-bit scans silently converted to 8-bit, compressed TIFFs that cannot be memory-mapped, and a tool that tried to allocate 3.18 TiB. [L688](../MASTER_LESSONS.md#l688-preserve-bit-depth-and-linear-intensities-when-converting-slices) [L687](../MASTER_LESSONS.md#l687-choose-storage-layout-by-access-pattern-and-benchmark-it-before-bulk-conversion) [L689](../MASTER_LESSONS.md#l689-read-a-tools-loader-before-running-it-some-allocate-the-whole-volume-and-lazy-arrays-hide-the-same-blow-up)

- **Hand segmentation at scale.** Segmenters worked in Volume Cartographer, and its maintainer explained that the ordered mesher ignores 3-D positions. A Segmentation Tooling Prize was awarded in June (summary, unverified). [L717](../MASTER_LESSONS.md#l717-vcs-ordered-mesher-ignores-3-d-positions-and-its-tracer-cannot-refine-a-sub-range-of-an-existing-surface)

- **Orientation confusion.** "Lots of the new segments were upside down" (2023-10-30), and the recto direction was "Not consistent". [L697](../MASTER_LESSONS.md#l697-measure-each-segments-orientation-from-geometry-layer-stacks-have-no-fixed-recto-direction-and-kaggle-layer-0-is-the-deep-side)

- **A leak caught fast.** On 2023-10-15 an unsupervised result looked readable until a member showed the loader had fed the label image to the model. The same thread settled that Kaggle layer 0 is the bottom. [L742](../MASTER_LESSONS.md#l742-keep-label-files-outside-every-input-directory-a-globbing-loader-can-feed-the-label-to-the-model) [L697](../MASTER_LESSONS.md#l697-measure-each-segments-orientation-from-geometry-layer-stacks-have-no-fixed-recto-direction-and-kaggle-layer-0-is-the-deep-side)

- **Small inputs required for First Letters.** Organizers kept ink-model inputs very small, because larger ones could "make up 'nice looking strokes'" (2023-10-15). [L658](../MASTER_LESSONS.md#l658-large-ink-model-windows-are-now-allowed-but-you-must-show-the-text-is-not-hallucinated)

- **Depth windows and sharkbites.** Members showed how small changes in the depth window lose letters (November). The "sharkbite" render artefact was traced and fixed in November. [L728](../MASTER_LESSONS.md#l728-record-the-inference-depth-window-and-sweep-it-for-any-candidate) [L698](../MASTER_LESSONS.md#l698-map-surface-volume-pixels-to-scroll-voxels-with-the-ppm-and-re-render-ppms-made-before-the-november-2023-sharkbite-fix)

- **Big releases.** Over 400 cm² of segments were released at the end of October, the Scroll 4 (PHerc 1667) 3.24 um dataset in November, and new scans with stored registration transforms in December (summary, unverified for the release list). [L684](../MASTER_LESSONS.md#l684-look-up-stored-volume-to-volume-transforms-first-check-their-scale-and-register-yourself-only-where-one-is-missing)

- **Download integrity.** After the server published md5 lists, members found many mismatched files, "In some cases whole folders" (2023-11-23). [L681](../MASTER_LESSONS.md#l681-mirror-with-rsync-and-verify-every-downloaded-or-written-file-by-checksum-not-by-size)

### 2024

- **Prizes reset.** The 2023 Grand Prize winner was presented, over $500,000 in new prizes were announced on 2024-02-27, and monthly Progress Prizes started (summary, unverified).

- **Automatic segmentation grows.** ThaumatoAnakalyptor's author reported that a global method makes about 100 times fewer sheet switches than greedy joining (2024-03-19). The First Automated Segmentation prize doubled to $100,000 in April (summary, unverified). [L716](../MASTER_LESSONS.md#l716-merge-local-sheet-patches-under-a-global-constraint-greedy-stitching-switches-sheets)

- **3-D ink labels go wrong in instructive ways.** One member labelled whole 3-D chunks as ink by mistake; another found labels on the papyrus-air interface teach "outermost layer". [L744](../MASTER_LESSONS.md#l744-check-2-d-to-3-d-label-mapping-and-segment-to-segment-label-transfer-before-training)

- **Wrap echoes found.** Widening the render depth found "new" text that was the same text one wrap away (2024-01-24). [L731](../MASTER_LESSONS.md#l731-separate-a-neighbouring-turns-echo-from-the-sheets-own-ink-with-a-depth-profile)

- **Transfer fails.** The 2023 Grand Prize model "hasn't yielded anything so far" on Scrolls 2, 3 and 4 (2024-06-18). [L739](../MASTER_LESSONS.md#l739-per-scroll-ink-models-still-beat-the-cross-scroll-9-um-models-pair-any-cross-scroll-null-with-a-same-scroll-positive-control)

- **Papyrologists' advice on labels.** Read only with models whose labels never covered the passage, because detailed labels can reproduce false strokes (2024-07-11). [L758](../MASTER_LESSONS.md#l758-read-text-only-from-models-whose-labels-never-covered-that-text)

- **Fragment data opened up.** The hidden Kaggle test fragment was released, and fragments were re-rendered at 7.91 um from geometry (July-August). [L745](../MASTER_LESSONS.md#l745-hold-out-the-released-kaggle-hidden-test-fragment-for-fragment-level-claims-and-rescale-fragments-by-re-rendering-from-geometry)

- **Letter size pinned down.** The average Scroll 1 letter "should be about 4 mm" (organizer, 2024-08-19). [L755](../MASTER_LESSONS.md#l755-convert-every-candidate-letters-size-to-millimetres-with-the-volumes-own-voxel-size)

- **Intensity mismatch explained.** Organizers said scroll-to-scroll brightness differences come from post-processing "that clips and normalizes the values" (2024-07-01). [L747](../MASTER_LESSONS.md#l747-equalise-intensity-across-scrolls-on-papyrus-only-voxels-before-applying-a-model-trained-elsewhere)

- **Standardized volumes checked.** A late-2024 release reported the wrong data type, and the community re-checked it after the re-release. [L686](../MASTER_LESSONS.md#l686-check-dtype-and-unique-values-of-standardized-zarr-chunks)

- **One code home.** The organizers moved their projects into the `villa` monorepo in November (summary, unverified).

### 2025

- **2024 prizes wrapped up.** The year-end results came in January. Organizers counted 13 "legitimate" First Letters/First Title submissions, where legitimate meant sound methods, "not that something was found" (2025-01-27). [L663](../MASTER_LESSONS.md#l663-a-count-of-legitimate-submissions-says-nothing-about-found-letters)

- **Fibre and surface datasets.** Skeleton fibre labels and much larger sheet-surface datasets were released through the first half of the year (summary, unverified).

- **Office hours.** Organizers started regular office hours in February (summary, unverified).

- **Reverse runs matter.** On Scroll 5, an organizer commented that in many places it matters to try running the ink prediction in reverse (2025-04-04). [L724](../MASTER_LESSONS.md#l724-pick-the-depth-direction-label-free-by-output-separation-and-read-forwardreversed-agreement-on-an-unread-volume-as-no-ink)

- **Refinement warning.** Organizers showed that brightness-maximising surface refinement drifts across sheets (2025-04-22). [L715](../MASTER_LESSONS.md#l715-brightness-maximising-surface-refinement-drifts-across-sheets-gate-it-on-held-out-ink-not-sharpness)

- **First Title Prize.** The title of Scroll 5 (PHerc 172) was announced in May (summary, unverified).

- **Self-labelling risks.** Practitioners warned that self-labelling on scrolls without ground truth drifts into labelling fibres (2025-08-11). [L741](../MASTER_LESSONS.md#l741-keep-a-fixed-ground-truth-anchor-set-in-every-self-labelling-round-on-scrolls-without-ground-truth-labels-spiral-into-fibres)

- **Text from Scroll 5.** A column of text was reported extracted and deciphered in September, and multiple scrolls were reported to show letters in October (summary, unverified).

- **Prize changes and Kaggle.** The prize lineup changed in September, and a new Kaggle competition was announced in November (summary, unverified).

- **PHerc. 139 released** on a different host from the usual one (2025-11-25). [L680](../MASTER_LESSONS.md#l680-inventory-every-data-host-before-declaring-data-missing-and-audit-headers-before-a-job)

- **Sheet-switch filtering.** Will Stevens developed patch-pair consistency checks on Scroll 4 (November-December). [L706](../MASTER_LESSONS.md#l706-flag-sheet-switches-where-overlapping-patches-disagree-in-3-d-and-check-the-removed-patches-by-hand)

- **Letters at 2.4 um on Scroll 4.** Organizers reported letters in a new 2.4 um Scroll 4 scan in December (summary, unverified).

### 2026

- **Big unwrapping progress.** About 70 % of PHerc. 172 was reported digitally unwrapped in January, and the Kaggle surface-detection competition ended in March (summary, unverified).

- **Public ground truth clarified.** "no tifxyz are fully manually annotated" (2026-06-13). [L703](../MASTER_LESSONS.md#l703-do-not-call-any-public-tifxyz-manually-annotated-ground-truth)

- **Two letter claims retracted** by their own author after null tests (2026-06-03). [L756](../MASTER_LESSONS.md#l756-run-the-identical-display-pipeline-on-matched-empty-regions-and-shuffled-inputs-before-believing-a-letter-like-mark)

- **First full-scroll reading.** A press event on 2026-06-25 marked the reading of PHerc. 1667 (summary, unverified). A rebuilt website with a $2,140,000 prize pool followed in July (summary, unverified).

- **Exact reproduction.** In late July members reproduced published m7 surface predictions at Dice 0.9997 and the 2.4 um ink maps at r≈0.96+. [L670](../MASTER_LESSONS.md#l670-anchor-region-of-interest-inference-to-the-full-volume-patch-grid) [L726](../MASTER_LESSONS.md#l726-copy-layer-window-normalization-and-tile-blending-from-the-buckets-metadatajson-to-reproduce-the-canonical-24-um-ink-maps)

- **Agent rules.** #robots opened on 2026-07-29, and contributor guidelines for agent pull requests were announced on 2026-08-13. [L665](../MASTER_LESSONS.md#l665-post-llm-written-reports-in-robots-name-the-model-and-separate-its-output-from-human-commentary) [L666](../MASTER_LESSONS.md#l666-agent-prs-and-issues-to-villa-must-follow-contributingmd-or-they-are-closed-without-comment)

- **Silent bugs found.** August brought the normalization fix, the cache fix, the resume fix and the repair of a checkpoint that output 0.5 everywhere. [L668](../MASTER_LESSONS.md#l668-pass-the-checkpoints-own-ct-normalization-to-vesuviuspredict-the-default-z-scores-each-volume) [L672](../MASTER_LESSONS.md#l672-count-bytes-received-during-remote-inference-zarr-3-silently-disabled-villas-chunk-cache) [L673](../MASTER_LESSONS.md#l673-do-not-let-villas-predict-overwrite-an-interrupted-whole-scroll-run) [L722](../MASTER_LESSONS.md#l722-smoke-test-every-published-ink-checkpoint-on-labelled-ink-some-ship-with-an-untrained-head-that-outputs-05-everywhere)

- **New 9 um models.** Released in August, then scored per region by the community: up to 0.14 balanced accuracy apart. [L723](../MASTER_LESSONS.md#l723-treat-each-released-ink9um-checkpoint-as-a-separate-instrument-select-by-held-out-score-per-region-and-do-not-ensemble-by-default)

- **Rules change.** Ten more scans became eligible and larger model windows were allowed (2026-09-10). PHerc 1447 left the First Letters list on 2026-09-24. [L662](../MASTER_LESSONS.md#l662-re-check-the-eligible-scroll-list-at-every-cycle-scrolls-are-added-and-withdrawn) [L658](../MASTER_LESSONS.md#l658-large-ink-model-windows-are-now-allowed-but-you-must-show-the-text-is-not-hallucinated)

- **Benchmarks from real defects.** SwitchBench (2026-09-30) and a letter-scale reading score (2026-09-22) set harder tests. [L705](../MASTER_LESSONS.md#l705-expect-current-sheet-switch-detectors-to-miss-most-real-switches-benchmark-them-on-confirmed-switches-with-smooth-bend-negatives) [L754](../MASTER_LESSONS.md#l754-score-a-read-against-a-key-with-a-high-pass-blur-matched-letter-scale-metric-and-a-blob-only-negative-exam)

- **PHerc. 343 award.** A $50K First Letters prize was awarded on 2026-10-08, leaving 21 eligible scrolls. [L662](../MASTER_LESSONS.md#l662-re-check-the-eligible-scroll-list-at-every-cycle-scrolls-are-added-and-withdrawn)

- **Judging guidance.** On 2026-10-18 organizers said window size and centring were their most common feedback, and that readability is judged on the images alone. [L660](../MASTER_LESSONS.md#l660-enlarge-and-re-centre-the-submission-window-before-fine-tuning-the-model-further) [L659](../MASTER_LESSONS.md#l659-readability-is-judged-by-the-papyrologists-on-the-images-alone-ask-rules-questions-in-public-threads)

---

## What the community learned, topic by topic

This chapter tells the story domain by domain. Each subsection has a short narrative of how thinking changed, then concrete findings with links, then the tools and reports worth knowing, then open questions. Narrative sentences that rest only on the AI-written review are marked "(summary, unverified)". Findings without that mark come from Part 8 of MASTER_LESSONS.md. A number in a finding is the poster's own unless the linked lesson says it was reproduced.

### Five shifts in thinking, 2023 to 2026

1. **From "can we see ink?" to "is this the right sheet?"** Early work asked whether ink shows in CT at all. By 2026 the harder question was whether a surface follows one physical sheet, because a wrong surface makes any ink result meaningless. [L700](../MASTER_LESSONS.md#l700-check-an-eligible-scroll-surfaces-sheet-contrast-against-many-curated-surfaces-before-blaming-the-ink-model) [L705](../MASTER_LESSONS.md#l705-expect-current-sheet-switch-detectors-to-miss-most-real-switches-benchmark-them-on-confirmed-switches-with-smooth-bend-negatives)

2. **From one scroll to many.** The 2023 methods worked on the scrolls they were trained on. Transfer to other scrolls, scan resolutions and beam energies became the central problem, and per-scroll training still wins. [L739](../MASTER_LESSONS.md#l739-per-scroll-ink-models-still-beat-the-cross-scroll-9-um-models-pair-any-cross-scroll-null-with-a-same-scroll-positive-control) [L746](../MASTER_LESSONS.md#l746-simulated-changes-of-resolution-or-energy-are-imperfect-proxies-test-on-real-scans-of-the-target-type)

3. **From impressions to controls.** Early claims rested on images that looked right. By 2026 the norm in serious reports was a pre-registered test with a control that could fail, and several authors retracted their own claims after running one. [L756](../MASTER_LESSONS.md#l756-run-the-identical-display-pipeline-on-matched-empty-regions-and-shuffled-inputs-before-believing-a-letter-like-mark) [L769](../MASTER_LESSONS.md#l769-freeze-evaluation-rules-by-publishing-a-protocol-hash-before-results-and-report-the-kill-when-it-fires)

4. **From trusting tools to auditing them.** In 2026 members found many defects in shared data and code that produced plausible output with no error. Reproducing published artifacts exactly became a standard first step. [L669](../MASTER_LESSONS.md#l669-read-the-tta-setting-and-pyramid-level-of-each-published-m7-surface-prediction-before-you-reproduce-it) [L675](../MASTER_LESSONS.md#l675-treat-a-zero-result-success-as-a-failure-and-assert-output-shapes-against-the-source)

5. **From people to people plus agents.** AI agents now write much of the code and many reports. Organizers welcomed the help but insisted on disclosure, human-set goals and human inspection of images at every stage. [L665](../MASTER_LESSONS.md#l665-post-llm-written-reports-in-robots-name-the-model-and-separate-its-output-from-human-commentary) [L764](../MASTER_LESSONS.md#l764-have-a-human-set-each-experiments-goal-and-success-criterion-this-project-has-no-robust-automatic-verifier)

### Geometry, surfaces and winding

In 2023 the main question was how to trace a single sheet at all. People drew segments by hand in Volume Cartographer, slice by slice, and learned its limits the hard way. Its ordered mesher links points by grid order and ignores their 3-D positions, and its tracer builds a new surface rather than refining an existing one. In 2024 automatic methods arrived. ThaumatoAnakalyptor (RICHI) showed that joining local patches under a global constraint makes far fewer sheet switches than greedy joining. Point clouds, fibre predictions and surface predictions became shared inputs (summary, unverified).

By 2025 and 2026 the problem had shifted again. Making a surface was no longer the bottleneck; proving it was the right surface was. The community found that surface predictions merge neighbouring turns, that patch growers can overwrite good surfaces, and that common quality scores mostly measure curvature. In mid-2026 members began building benchmarks from real, independently confirmed defects instead of synthetic ones, after organizers said toy problems "_never_ translate to our real data". The best existing switch detectors turned out to miss most real switches. Whole-scroll spiral fits became the organizers' suggested cheap route to new First Letters areas, but one audit found that published fits of some eligible scrolls followed sheets no better than chance.

**Findings**

- **Orientation is not fixed.** Segments were often rendered upside down, and which end faces the reader is "Not consistent unfortunately" (2023-11-20). Kaggle fragment layer 0 is the deep side. Measure orientation from geometry, for example by the sign of the normal against the radial direction from the scroll centre. [L697](../MASTER_LESSONS.md#l697-measure-each-segments-orientation-from-geometry-layer-stacks-have-no-fixed-recto-direction-and-kaggle-layer-0-is-the-deep-side)

- **The PPM file maps rendered pixels back to scroll voxels.** Its formula came from the VC maintainer in 2023. Renders made before the November 2023 "sharkbite" fix show artefacts in fast-changing regions and should be re-rendered. [L698](../MASTER_LESSONS.md#l698-map-surface-volume-pixels-to-scroll-voxels-with-the-ppm-and-re-render-ppms-made-before-the-november-2023-sharkbite-fix)

- **The ordered mesher ignores 3-D positions.** "the mesher would still link them", and "the seg algorithm is designed to produce a new surface, not refine an existing surface" (2023). Check edge lengths after any pointset edit. [L717](../MASTER_LESSONS.md#l717-vcs-ordered-mesher-ignores-3-d-positions-and-its-tracer-cannot-refine-a-sub-range-of-an-existing-surface)

- **Greedy stitching switches sheets.** The ThaumatoAnakalyptor author estimated that a global method makes "about 100 times less" mistakes than greedy joining (author's estimate, not reproduced). [L716](../MASTER_LESSONS.md#l716-merge-local-sheet-patches-under-a-global-constraint-greedy-stitching-switches-sheets)

- **Brightness-chasing refinement drifts.** An organizer found that moving a mesh to maximise brightness made it "switch across sheets" or move inside the papyrus. The author's displacements reached ±36 px. [L715](../MASTER_LESSONS.md#l715-brightness-maximising-surface-refinement-drifts-across-sheets-gate-it-on-held-out-ink-not-sharpness)

- **Pairwise patch checks find many switches.** Will Stevens flagged patch pairs whose shared 2-D point maps more than 50 units apart in 3-D. Among about 94,142 Scroll 4 patches, 1153 were in a mismatching pair. His whole-scroll output had about 52 % of the surface in one connected part. [L706](../MASTER_LESSONS.md#l706-flag-sheet-switches-where-overlapping-patches-disagree-in-3-d-and-check-the-removed-patches-by-hand)

- **Real switches are mostly missed.** On SwitchBench (213 confirmed natural switches on PHercParis4), tifxyz-doctor found 12 % (25/213). A pre-registered hybrid detector caught 2 of 47 (4 %), and its kill rule fired before held-out data was opened. A reviewer said another tool "is primarily detecting strong curvature". [L705](../MASTER_LESSONS.md#l705-expect-current-sheet-switch-detectors-to-miss-most-real-switches-benchmark-them-on-confirmed-switches-with-smooth-bend-negatives)

- **Synthetic success does not transfer.** ScrollAnchor reported synthetic switch precision and recall of 1.00 / 1.00, but about 0.19 precision on a real cube. [L704](../MASTER_LESSONS.md#l704-synthetic-benchmarks-and-phantoms-are-unit-tests-only-validate-geometry-tools-on-real-imperfect-patches)

- **Meshes often leave the scroll.** Across 299 segments in 11 scrolls, four scrolls had 0.00-0.25 % of vertices off the masked object, PHerc1447 33 % and PHerc1667 19 %. A gap between adjacent-winding segments of 0.25 next to 2.09 flagged which segment jumped. [L702](../MASTER_LESSONS.md#l702-measure-the-fraction-of-each-mesh-lying-outside-ct-support-and-the-gap-to-adjacent-winding-segments)

- **Normal-walk quality scores fail at the outer wrap.** A no-ground-truth score ranked the outer winding best because the walk crossed crust into air. Clip the walk at the scroll mask. [L701](../MASTER_LESSONS.md#l701-clip-normal-walk-sheet-metrics-at-the-scroll-mask-at-the-outer-wrap-the-walk-crosses-crust-into-air)

- **Contrast, not placement, separates good surfaces.** Across 38 curated segments, depth-profile contrast was 57 to 92, while one member's auto-made eligible-scroll meshes ranged 1.7 to 55. [L700](../MASTER_LESSONS.md#l700-check-an-eligible-scroll-surfaces-sheet-contrast-against-many-curated-surfaces-before-blaming-the-ink-model)

- **Public tifxyz are not manual ground truth.** "no tifxyz are fully manually annotated" (organizer, 2026-06-13). [L703](../MASTER_LESSONS.md#l703-do-not-call-any-public-tifxyz-manually-annotated-ground-truth)

- **Winding pitch is not a constant.** An organizer called pitch "not usable whatsoever" outside initialisation. Measured on Paris 4: median 180 um, quartiles 126 to 441 um. Level 2 merges adjacent sheets and biases pitch (207 vs 187.3 um at level 1). [L710](../MASTER_LESSONS.md#l710-do-not-treat-winding-pitch-or-sheet-spacing-as-a-constant-and-measure-it-at-level-1-or-finer)

- **Better constraints made fits worse.** "three progressively better constraint generators all degraded the fit vs. a no-constraint baseline". A generator's own consistency score of 0.670 fell to 0.050 against verified meshes. Published crossing counts matched human chains 93/94 times, but auto chains still hurt held-out accuracy. [L707](../MASTER_LESSONS.md#l707-score-winding-constraints-against-held-out-human-chains-and-ab-every-constraint-source-against-a-no-constraint-fit)

- **Held-out splits leak by distance.** 54.8 % of "sealed" points sat within 0.5 voxel of a fit input, which a name-level check cannot see. [L709](../MASTER_LESSONS.md#l709-split-held-out-geometry-by-distance-to-the-fits-inputs-not-by-patch-name)

- **References must be independent.** scroll-truth judged same-wrap pairs from raw CT only and checked itself by transitivity: 444 impossible triangles out of 3,143,486 (0.014 %), against 0.7-2.9 % for shuffled verdicts. [L708](../MASTER_LESSONS.md#l708-judge-a-tracer-with-a-raw-ct-reference-it-does-not-consume-and-self-check-that-reference-by-transitivity)

- **Averaged shapes can be fiction.** A cross-section ellipse at R² = 0.948 came from averaging 313 sections; single sections gave 0.848 down to 0.592. Organizers ask for CT renders and cross-sections with any unwrap claim. [L711](../MASTER_LESSONS.md#l711-fit-cross-section-shape-per-height-and-post-ct-renders-and-cross-sections-with-any-unwrap-claim)

- **Dice can hide merges.** A label dilated by 2 voxels already scores 0.40 merge pairs per cube. A recall fine-tune bought recall with merges (0.60 to 0.97 pairs per cube). A winding-number field cut merges to 0.53 (-45 %). [L712](../MASTER_LESSONS.md#l712-report-sheet-merges-and-fragments-together-against-a-dilated-label-floor-and-a-ct-threshold-baseline)

- **Coverage cannot rank fibre tracers.** Four labellings had identical coverage (0.9177) and precision (0.2194). Use merge-penalized ERL within one cube size. [L713](../MASTER_LESSONS.md#l713-rank-fibre-tracers-by-merge-penalized-erl-within-one-cube-size-not-by-coverage-or-precision)

- **Repair only what is well posed.** tifxyz-surgeon fills interior holes and refuses tears, merges and switches. In one audit, 6 of 14 large holes checked by hand were pockets between two merged sheets, so filling them would be wrong. [L714](../MASTER_LESSONS.md#l714-repair-only-well-posed-mesh-defects-fill-interior-holes-on-one-sheet-refuse-tears-merges-and-switches)

- **QA features need an AUC test first.** Ridge distance separated labelled bad from good patches at AUC 0.512 only. [L719](../MASTER_LESSONS.md#l719-score-a-candidate-patch-qa-feature-by-auc-between-labelled-good-and-bad-patches-before-building-a-filter)

- **The umbilicus estimator can walk out of the volume.** Its normalized score can have no interior maximum on partial predictions. [L718](../MASTER_LESSONS.md#l718-check-that-an-estimated-umbilicus-lies-inside-the-scroll-mask-at-a-local-score-maximum)

- **Spiral-fitting all prize scrolls is untried.** Organizers expected it to give "a fairly large number of decent areas"; track-graph patches are "strangely unhelpful in the spiral". Label: HYPOTHESIS. [L721](../MASTER_LESSONS.md#l721-organizers-suggest-spiral-fitting-whole-prize-scrolls-as-a-cheap-first-letters-route-test-it-with-a-pre-registered-coverage-and-ink-check)

- **Spiral fits need a chance baseline.** Against 200 random-shift copies, five published fits of eligible scrolls scored -0.017 to +0.009 versus chance; the Paris 4 team fit scored +0.024 to +0.070 (AI-run, unreplicated). [L699](../MASTER_LESSONS.md#l699-score-a-spiral-fit-against-random-shift-copies-of-itself-on-the-raw-ct-before-inking-it)

**If you work on this now.** Start from the published surfaces and fits, but treat each one as unproven. Before you render ink, measure how much of the mesh lies outside CT, compare its sheet contrast with the curated range, look at cross-sections, and check for jumps between adjacent windings. Run any switch detector on real confirmed switches, not planted ones. If you try a whole-scroll spiral fit, score it against random-shift copies of itself and against the Paris 4 team fit as a positive control. Record what your checks cannot see, such as slow sheet hops ramped over a millimetre or more. [L775](../MASTER_LESSONS.md#l775-test-a-sheet-gate-on-hard-negatives-and-write-what-sheet-verified-does-not-cover)

**Tools and reports worth knowing:** ThaumatoAnakalyptor (RICHI); khartes (khartes_chuck); SwitchBench (lightsgoblack); tifxyz-surgeon (Abd Elilah); scroll-truth (karasukun); constraint-gauge (pscamillo); spiralcheck (Nico); windingcheck, spiralfiteval and inkcheck (Johannes); ScrollAnchor (summary, unverified for authorship); sheet-switch detection on Scroll 4 (Will Stevens).

**Open questions**

- Can any detector catch most real sheet switches without flagging every sharp bend?
- Why do high-quality track-graph patches not help the spiral fit?
- How much usable area does a whole-scroll spiral fit give on each eligible scroll, measured against shifted-copy chance?
- Which winding-constraint source, if any, beats a no-constraint fit on held-out slips per wrap?

### Rendering and flattening

Rendering turns a traced surface into a flat image stack that an ink model can read. In 2023 most trouble was mechanical: OBJ files that pointed to missing material files, point clouds passed where meshes were needed, layer stacks in an unknown order, and PPM files whose layer positions were off by a rounding rule. The community learned to read the PPM directly and to round-trip geometry through the official tools (summary, unverified for the general picture).

In 2026 the focus moved to exact reproduction. Members showed that published surface predictions and ink maps can be regenerated almost bit for bit, but only with the exact production settings: test-time augmentation, pyramid level, patch grid, layer window, scaling and tile blending. A one-pixel canvas error affected 35 % of published meshes. The lesson of the period is that renderer parity proves two programs agree, not that the surface is right.

**Findings**

- **The PPM layout is simple once known.** It has an ASCII header ending in `<>\n`, then raw float64 values, 6 per pixel. An even layer count gives a position error of up to one voxel, which the maintainer called "maybe … a bug". [L698](../MASTER_LESSONS.md#l698-map-surface-volume-pixels-to-scroll-voxels-with-the-ppm-and-re-render-ppms-made-before-the-november-2023-sharkbite-fix)

- **Strip material lines before rendering.** khartes OBJs referenced a stale `.mtl` file, and `vc_render` failed until those lines were removed. `_points.obj` "is a point cloud without any mesh information". [L694](../MASTER_LESSONS.md#l694-strip-material-lines-from-objs-before-vcrender-and-pass-the-mesh-not-the-point-cloud)

- **Export geometry as tifxyz with the coordinate scale.** "the scale is the scale of the _coordinates_ and not the density/resolution of the 2d grid" (organizer, 2026-04-23). Round-trip through VC3D. [L693](../MASTER_LESSONS.md#l693-export-geometry-as-tifxyz-with-the-coordinate-scale-and-round-trip-it-through-vc3d)

- **Canvas size needs float32 rounding.** Python's computed canvas was one pixel short for 207 / 593 published meshes (35 %). Only 262 / 628 surface volumes reproduce their canvas size exactly; the rest of the cross-scan renders are a median 10 px off, up to 1,346 px. [L676](../MASTER_LESSONS.md#l676-derive-tifxyz-canvas-size-with-the-renderers-float32-rounding-and-read-cross-scan-canvas-sizes-from-the-volume)

- **Published m7 surface predictions reproduce.** 40 of the 41 artifacts reproduce with mirroring TTA off at Dice 0.9983-1.0000. PHerc. Paris 4 needs TTA on (0.8907 off vs 0.9999 on). "27 of the 41 published predictions are level 0, not level 2". Organizers backfilled the metadata. [L669](../MASTER_LESSONS.md#l669-read-the-tta-setting-and-pyramid-level-of-each-published-m7-surface-prediction-before-you-reproduce-it)

- **Region runs must use the full-volume patch grid.** A region tiled from its own origin had "zero patch positions in common" with the full run and gave Dice 0.80; anchored to the full grid it gave 0.9997. [L670](../MASTER_LESSONS.md#l670-anchor-region-of-interest-inference-to-the-full-volume-patch-grid)

- **Production ink maps use non-default settings.** Production uses layers 23 to 85 (public default 1-63), clip(0,200)/200 scaling and Hann-blended 256 px tiles. With all three fixed, a member's reproduction correlated r≈0.96+ with the published maps. [L726](../MASTER_LESSONS.md#l726-copy-layer-window-normalization-and-tile-blending-from-the-buckets-metadatajson-to-reproduce-the-canonical-24-um-ink-maps)

- **Context margins matter for parity.** A reader-parity check failed at r 0.879 and 0.884 until a 256 px context margin was added; then r was 0.999995. [L779](../MASTER_LESSONS.md#l779-give-a-reader-parity-gate-the-same-context-margin-as-its-reference)

- **Tiled reassembly must divide by overlap weight.** nn.Fold sums overlapping patches, which gave dark borders. [L691](../MASTER_LESSONS.md#l691-divide-by-the-overlap-weight-when-reassembling-tiled-inference)

- **Compare two meshes only under identical settings.** Flattening method, stack width and checkpoint all change ink maps. A comparison of two flattening methods looked "cleaner but not night and day". [L762](../MASTER_LESSONS.md#l762-compare-ink-maps-of-two-meshes-only-under-identical-flattening-stack-width-and-checkpoint)

- **Raster area overstates sheet area.** On three segments, canvas area was 3.61/3.05/3.29 cm² against true mesh area 1.73/1.62/1.56 cm². [L788](../MASTER_LESSONS.md#l788-compute-true-mesh-area-from-valid-triangles-raster-canvas-area-overstates-it-about-2x)

- **Neighbouring turns print through.** Where turns are 100 to 200 um apart, a 0.26 mm reading window reaches the next turn. Widening a render in 2024 found "new" text that was the same text one wrap away. [L731](../MASTER_LESSONS.md#l731-separate-a-neighbouring-turns-echo-from-the-sheets-own-ink-with-a-depth-profile)

- **Sharp bends are unreliable.** "if we have a 64 voxel surface volume and the other surface is within 64 voxels, it seems unavoidable" that ink detection degrades there. [L732](../MASTER_LESSONS.md#l732-treat-pixels-where-the-surface-normal-turns-sharply-as-low-confidence-ink)

- **Layer order must be checked per segment.** vc_render "kind of randomly assigns a direction" to layer stacks, so check orientation before rendering a stack for ink. [L697](../MASTER_LESSONS.md#l697-measure-each-segments-orientation-from-geometry-layer-stacks-have-no-fixed-recto-direction-and-kaggle-layer-0-is-the-deep-side)

- **Pin every setting of a map.** Write checkpoint hash, start and end layer, in_chans, stride and layer order into every run manifest. [L727](../MASTER_LESSONS.md#l727-pin-the-checkpoint-layer-window-and-inchans-of-every-map-forks-and-repo-snapshots-change-them-silently)

**If you work on this now.** Reproduce one published artifact exactly before you make new ones. Read the TTA flag, pyramid level, layer window, scaling, tile blending and patch grid from the metadata, not from defaults or memory. Compute canvas size with the renderer's own rounding, and compute sheet area from valid triangles. Write every setting into your output's provenance, so that someone else can regenerate your image bit for bit.

**Tools and reports worth knowing:** reproduction reports on m7 surface predictions (Abd Elilah); reproduction of the 2.4 um ink recipe (LimeGS); vesuvius-gui and vesuvius-render (jrudolph) (summary, unverified); canvas-size fixes in the vesuvius package (George A).

**Open questions**

- Which flattening method best preserves letter shapes on crushed scrolls, measured on held-out labels?
- How should renders handle regions where the next turn lies inside the reading window?
- Can renders flag high-curvature pixels automatically so that ink maps carry a confidence layer?

### Ink detection and models

The 2023 breakthroughs came from 2.5-D models trained on fragment labels and then on crackle seen in scroll segments (summary, unverified). Organizers kept model inputs small, about a quarter of a letter or less, because models with larger views could "make up 'nice looking strokes'". In 2024 the hard problem became transfer. The 2023 Grand Prize model did not work on other scrolls, and people learned that per-scroll training, label quality and exact depth windows matter more than architecture.

In 2025 and 2026 the organizers released new 9 um models trained across scrolls and moved the rules toward larger windows with anti-hallucination evidence. The community then audited the released models closely. It found broken checkpoints, a default checkpoint that was the worst of 14 on one region, sensitivity to stride, jitter, depth direction and surface offset, and a held-out score that could not be read as legibility. By October 2026 the consensus was cautious: per-scroll models still win, and clarity drops sharply from 2.4 um to about 9 um.

**Findings**

- **Ink is roughly as dense as papyrus.** "the ink is not completely radiolucent. Is has roughly the same radiodensity as the papyrus" (2023). Elemental contrast varies by scroll. [L750](../MASTER_LESSONS.md#l750-plan-for-carbon-ink-with-roughly-papyrus-radiodensity-elemental-contrast-is-scroll-specific)

- **Ink is usually slightly brighter at 9 um, not darker.** An organizer said "for the most part ink is actually brighter". Measured fractions of labelled ink brighter than median papyrus ranged from 40.4 % to 58.6 % by scroll, and all 8 Paris 4 segments were brighter. [L734](../MASTER_LESSONS.md#l734-do-not-assume-carbon-ink-is-darker-than-papyrus-at-9-um-it-is-usually-slightly-brighter-and-the-sign-varies-by-scroll)

- **Smoke-test every checkpoint.** One published checkpoint output 0.5 everywhere; after retraining its head, held-out AUC went from 0.50 to 0.94. The fix was credited in the September 2026 progress prizes. [L722](../MASTER_LESSONS.md#l722-smoke-test-every-published-ink-checkpoint-on-labelled-ink-some-ship-with-an-untrained-head-that-outputs-05-everywhere)

- **Checkpoints are separate instruments.** The 14 released ink_9um checkpoints "vary by up to 0.14 balanced accuracy". The default was worst on one region (0.680 vs 0.819). Organizers said earlier epochs (~20k-30k) might generalise better. [L723](../MASTER_LESSONS.md#l723-treat-each-released-ink9um-checkpoint-as-a-separate-instrument-select-by-held-out-score-per-region-and-do-not-ensemble-by-default)

- **Ensembles are not free gains.** Averaging seeds, windows or TTA beat the best single checkpoint on 0 of 3 held-out segments in one pre-registered test. Ensembles "can also lose fainter signals". [L723](../MASTER_LESSONS.md#l723-treat-each-released-ink9um-checkpoint-as-a-separate-instrument-select-by-held-out-score-per-region-and-do-not-ensemble-by-default)

- **Depth direction matters.** In a pre-registered test, the wrong direction cost 0.09-0.20 AUC, and a label-free rule (keep the direction whose output separates more) picked right 60/60. On an unread scroll, forward and reversed runs that agree in unrelated places point to no ink. [L724](../MASTER_LESSONS.md#l724-pick-the-depth-direction-label-free-by-output-separation-and-read-forwardreversed-agreement-on-an-unread-volume-as-no-ink)

- **Stride must be on the 8-pixel grid.** Off-grid strides were worse in 5 of 5 measurements, by 0.005 to 0.032 AUC (one scroll). [L725](../MASTER_LESSONS.md#l725-use-an-on-grid-stride-a-multiple-of-8-for-ink9um-sliding-window-inference)

- **Scale jitter to the window.** A 5-slice window with ±2 jitter lost 58-0 across 60 windows; with jitter off it tied 60/60. [L730](../MASTER_LESSONS.md#l730-scale-depth-jitter-to-the-window-2-slices-of-jitter-on-a-5-slice-window-ruins-it)

- **Surface offset costs ink asymmetrically.** Five slices off one way cost about 0.16-0.17 F1, the other way about 0.03-0.04. [L729](../MASTER_LESSONS.md#l729-surface-offset-costs-ink-asymmetrically-keep-the-surface-within-3-slices-on-the-bad-side) The 2.4 um reader showed the same asymmetry in another project (AUC 0.556 vs 0.9995). [L780](../MASTER_LESSONS.md#l780-the-24-um-production-reader-tolerates-early-centring-offsets-but-not-late-ones)

- **Pin the depth window.** Small window changes "Lose a lot of letters" and start showing letters "from a different sheet" (2023). Kaggle fragment training showed "virtually no usable signal on either side of 32+/- 8". [L728](../MASTER_LESSONS.md#l728-record-the-inference-depth-window-and-sweep-it-for-any-candidate)

- **Repo snapshots and forks change settings.** The public model that made a famous 2023 image was "a different model", and a fork changed the default layer window. [L727](../MASTER_LESSONS.md#l727-pin-the-checkpoint-layer-window-and-inchans-of-every-map-forks-and-repo-snapshots-change-them-silently)

- **Normalization must match training.** villa's default z-scoring misled m7 surface inference until fixed. [L668](../MASTER_LESSONS.md#l668-pass-the-checkpoints-own-ct-normalization-to-vesuviuspredict-the-default-z-scores-each-volume)

- **Thresholds carry only within one model.** The recommended borrowed threshold of 87 lost 0.096 / 0.118 / 0.095 F1; borrowing the same model's operating quantile from other scrolls lost 0.003-0.009 in one replication. [L733](../MASTER_LESSONS.md#l733-carry-a-binarization-threshold-only-within-the-same-model-the-operating-quantile-rule-held-best-in-three-pre-registered-tests)

- **Per-scroll models still win.** "per-scroll models still work better. we'd love to know why" (organizer, 2026-08-24). PHerc 1447 gave "a few strokes without fine-tuning; ~10 letters with fine-tuning". [L739](../MASTER_LESSONS.md#l739-per-scroll-ink-models-still-beat-the-cross-scroll-9-um-models-pair-any-cross-scroll-null-with-a-same-scroll-positive-control)

- **Pseudo-labels need care.** Predictions "contain a lot of noise" and self-training may "collapse". Black in a prediction mask means "ink not seen, so it could be ink". [L740](../MASTER_LESSONS.md#l740-curate-pseudo-labels-and-use-three-state-masks-black-in-a-prediction-mask-means-not-seen-not-no-ink) Keep fixed ground truth in every round, or labels "spiral" into fibres. [L741](../MASTER_LESSONS.md#l741-keep-a-fixed-ground-truth-anchor-set-in-every-self-labelling-round-on-scrolls-without-ground-truth-labels-spiral-into-fibres)

- **Credit gains with matched controls.** Dense pseudo-labels lifted one checkpoint from 0.9147 to 0.9548 held-out while a matched control stayed at 0.9149: "a benchmark gain btw, not extra letters". [L738](../MASTER_LESSONS.md#l738-credit-a-retraining-gain-to-new-data-only-with-a-matched-control-run-and-do-not-equate-it-with-legibility)

- **Fragment labels are imperfect.** The infrared-to-CT alignment is "a largely manual process that we know introduces error". [L743](../MASTER_LESSONS.md#l743-fragment-ink-labels-are-hand-aligned-and-partly-wrong-down-weight-their-boundaries) Labels on the papyrus-air interface teach a model to find the outermost layer. [L744](../MASTER_LESSONS.md#l744-check-2-d-to-3-d-label-mapping-and-segment-to-segment-label-transfer-before-training)

- **Hold out the released Kaggle hidden test fragment.** Re-render fragments from geometry at the target voxel size rather than resizing images. [L745](../MASTER_LESSONS.md#l745-hold-out-the-released-kaggle-hidden-test-fragment-for-fragment-level-claims-and-rescale-fragments-by-re-rendering-from-geometry)

- **Simulated resolution is a weak proxy.** "down sampling to 8um is not quite the same as reconstructing at 8um". An effective resolution of about 40 um on the 8 um scans was suggested but not reproduced. [L746](../MASTER_LESSONS.md#l746-simulated-changes-of-resolution-or-energy-are-imperfect-proxies-test-on-real-scans-of-the-target-type)

- **Compressed volumes hurt ink models.** q8 compression cost about a quarter of the detector's separation, q4 already -7 %. [L748](../MASTER_LESSONS.md#l748-do-not-run-released-ink-models-on-volcomp-q8-volumes-without-adaptation)

- **No CT-direct 3-D reader at 9 um is known.** The best Paris 4 3-D model relied on visible crackle. A 3-D U-Net at 8.64 um learned "no letter structure" (r 0.21). [L749](../MASTER_LESSONS.md#l749-treat-3-d-ink-predictions-as-likely-ink-not-physical-ground-truth-no-ct-direct-model-is-known-to-read-at-9-um)

- **New output types must beat the binary baseline.** A four-valued output scored F1 0.7954 against 0.8197 binary, and its author agreed it was "oversold". [L752](../MASTER_LESSONS.md#l752-a-new-output-semantics-must-beat-the-binary-baseline-on-the-same-held-out-split)

- **Label-free post-filters need sealed windows.** One filter raised mean cube AUC from 0.703 to 0.788; a rolled-volume control dropped to 0.639. [L737](../MASTER_LESSONS.md#l737-pair-a-label-free-ink-post-filter-with-sealed-windows-and-a-misaligned-control-that-should-fail)

**If you work on this now.** Choose checkpoints by held-out score on more than one scroll, never by default. Run both depth directions, use an on-grid stride, keep jitter small relative to the window, and keep the surface on the sheet front. Smoke-test every checkpoint on known ink. Expect to fine-tune on the target scroll, and keep a held-out region of that scroll as the check. Never read a held-out AUC as a promise of readable letters. [L784](../MASTER_LESSONS.md#l784-a-bulk-ink9um-auc-near-074-078-is-pixel-signal-not-legibility)

**Tools and reports worth knowing:** per-region scoring of all 14 checkpoints and Reader V3 (KLAVIS); checkpoint repair and dense pseudo-labels (Nieuwlaar); ink-path PRs and direction tests (OBCD); stride study (tarikcankorkmaz); threshold studies (잠이올랑말랑, an AI-disclosed agent); inkdx (anshu231); depth-window jitter study (pscamillo); Faster and Tuneable GP inference (waldkauz).

**Open questions**

- Why do per-scroll models beat cross-scroll models, and how much target-scroll labelling closes the gap?
- What held-out score, if any, predicts that papyrologists can read 10 letters in 4 cm²? One project guessed an AUC of about 0.9 (HYPOTHESIS). [L784](../MASTER_LESSONS.md#l784-a-bulk-ink9um-auc-near-074-078-is-pixel-signal-not-legibility)
- Can any model read letters directly from 9 um CT in 3-D?

### Data, volumes and storage

Early on, data handling was a craft. Volumes were stacks of 16-bit TIFFs, downloads broke, and many people discovered checksum mismatches only after the server published an md5 list. The community learned to preserve bit depth, mirror with rsync, choose chunked layouts for 3-D work, and read a tool's loader before running it. In 2024 the organizers re-released "standardized" volumes, and members checked their data types and found bugs (summary, unverified for the release details).

By 2026 the data had spread across several hosts, formats and pyramid levels, and the main risk was silent corruption. Missing chunks read as zeros. A pyramid level held a quarter of its declared depth. A cache stopped working after a library upgrade. Public 8-bit volumes were clipped at both ends. The recurring fix was the same: audit headers and contents before any job, measure bytes rather than time, and treat zero as "no data" until shown otherwise.

**Findings**

- **Rebuild 9.6 um inputs from level 0.** In 18 of 33 HF ink-bucket surface volumes, level 2 holds only 17 of 65 depth slices. 0841 renders are 4.681 um and need 2x pooling, not 4x (single reporter; filed as villa#2107). [L667](../MASTER_LESSONS.md#l667-rebuild-96-um-inputs-from-level-0-in-18-of-33-hf-ink-bucket-surface-volumes-level-2-holds-only-17-of-65-depth-slices)

- **Missing chunks are not blank papyrus.** "if a chunk file is absent, it is treated as if it were all zeros; no error is raised" (2023). [L735](../MASTER_LESSONS.md#l735-gate-no-ink-verdicts-on-ct-coverage-not-mesh-validity-and-calibrate-against-regions-outside-the-test)

- **Phantom sheet on empty CT.** 30 of 36 scrolls had more than 10 % of predicted sheet on zero CT. The root cause was found and fixed for new runs (phantom share on one scroll from 63.9 % to 2.3 %); published predictions are not repaired. Label: VERIFIED. [L671](../MASTER_LESSONS.md#l671-published-m7-surface-maps-mark-sheet-on-zero-ct-mask-them-by-ct--0-for-statistics-but-do-not-threshold-them-by-ct-intensity)

- **Zero is not air on the older uint16 volumes.** Air sits "somewhere in the neighborhood of 25k", because the window includes negative attenuation. [L679](../MASTER_LESSONS.md#l679-on-the-older-uint16-volumes-zero-is-not-air-the-windows-include-negative-attenuation)

- **ESRF 8-bit volumes are clipped.** Percentile windowing "does in general not work for the scrolls", and some low-Paganin volumes had 12-14 % of voxels at 0. [L677](../MASTER_LESSONS.md#l677-do-not-compare-esrf-8-bit-volumes-by-raw-intensity-without-masking-clipped-ends-and-reading-each-volumes-window) Record which Paganin variant you used. [L678](../MASTER_LESSONS.md#l678-record-which-paganin-variant-you-used-and-take-its-parameters-from-the-scan-object)

- **Check data type and unique values.** A 2024 "standardized" release reported `<u2` with 32 unique values that were multiples of 2040. [L686](../MASTER_LESSONS.md#l686-check-dtype-and-unique-values-of-standardized-zarr-chunks)

- **Preserve bit depth.** OpenCV without the unchanged flag converts 16-bit to 8-bit; one member had to "essentially restart". [L688](../MASTER_LESSONS.md#l688-preserve-bit-depth-and-linear-intensities-when-converting-slices)

- **Verify by checksum, not size.** Multi-stream downloads pre-allocate full-size files, so an interrupted file showed full size at about 70 %. Checksums found mismatches "In some cases whole folders". [L681](../MASTER_LESSONS.md#l681-mirror-with-rsync-and-verify-every-downloaded-or-written-file-by-checksum-not-by-size)

- **Inventory every host.** PHerc. 139 lives under a different path ("careful, this is not the _usual_ repository!"). Some declared pyramid levels on one host return 404 and "won't be fixed". [L680](../MASTER_LESSONS.md#l680-inventory-every-data-host-before-declaring-data-missing-and-audit-headers-before-a-job)

- **Read single planes with byte ranges.** Uncompressed 128³ chunks hold an axial plane as one contiguous 16 KB run, which saves "usually well over 100x per slice". Back off on 429 errors. [L682](../MASTER_LESSONS.md#l682-read-single-planes-from-uncompressed-zarr-chunks-with-byte-range-requests-and-back-off-on-429)

- **Do not stream training data from Hugging Face.** Its small chunks cause "almost constant rate limits". One PR cut a training read from 92.02 GB to 2.42 GB. [L683](../MASTER_LESSONS.md#l683-do-not-stream-training-data-from-hugging-face-fetch-only-the-chunks-your-training-config-reads)

- **Look up stored transforms between scans.** Scans of one scroll are "usually" registered, with transforms in the metadata, but at least one was missing. [L684](../MASTER_LESSONS.md#l684-look-up-stored-volume-to-volume-transforms-first-check-their-scale-and-register-yourself-only-where-one-is-missing)

- **Check the frame of annotations.** Coordinates that cannot exist in the assumed volume prove a frame error. [L685](../MASTER_LESSONS.md#l685-check-the-frame-of-annotation-coordinates-coordinates-that-cannot-exist-prove-a-frame-error)

- **Choose layout by access pattern.** Slice renders took 1.3 ms (xy) to 20.6 ms (yz) on one layout; 128³ and 256³ chunks worked best in another test. [L687](../MASTER_LESSONS.md#l687-choose-storage-layout-by-access-pattern-and-benchmark-it-before-bulk-conversion)

- **Some tools load the whole volume.** One tool tried to allocate 3.18 TiB. [L689](../MASTER_LESSONS.md#l689-read-a-tools-loader-before-running-it-some-allocate-the-whole-volume-and-lazy-arrays-hide-the-same-blow-up)

- **Suspect your own reader first.** A reported 180-pixel offset in official data was the reporter's own parser bug. [L770](../MASTER_LESSONS.md#l770-suspect-your-own-reader-before-reporting-a-data-defect-and-read-the-file-with-two-libraries)

**If you work on this now.** Run a header and content audit on every volume before a job: declared versus real shape, pyramid levels present, data type, unique values, fraction of zeros and fraction at the top value. Keep a mask of which chunks really exist. Mirror with rsync and verify checksums. Measure bytes transferred during remote inference, and stage data locally when the access pattern is random.

**Tools and reports worth knowing:** scroll-data-audit (Matteo Bulloni); zarr-pyramid-audit (SaboAI); Catalog consistency checker (summary, unverified for authorship); Scrollscope (kadenian1); scrollscout (vonduffen); the ink-label bucket bug report and cross-scroll benchmark (Ehimen Nathaniel).

**Open questions**

- Will the published m7 surface predictions be re-run with the phantom-sheet fix?
- Which hosts and pyramid levels are canonical for each eligible volume today?
- Should every published volume ship with a header-and-content audit report, so users do not each repeat it?

### Papyrology and reading

From the start, the papyrologists set the bar: letters must be visible in the image, not inferred from context. Early community "finds" were often textures at the wrong scale. A candidate a few pixels high on an 8 um scan would be 0.4 mm tall, far too small for a letter. Members learned to convert sizes to millimetres, to label ink with flood fills rather than pens, and to keep labels away from the text being read.

In 2025 and 2026 readings multiplied on several scrolls (summary, unverified), and so did false alarms. Contrast stretching, seams between sheets, meshes leaving the sheet and echoes from the next turn all produced letter-like marks. Two public letter claims were retracted after their own author ran null tests. Organizers made two things explicit: readability is judged only on the images, and the most common reason a near-miss fails is a window that is too small or off-centre.

**Findings**

- **Judged on the images alone.** Annotations "are not used in the judgement of readability" (2026-10-18). [L659](../MASTER_LESSONS.md#l659-readability-is-judged-by-the-papyrologists-on-the-images-alone-ask-rules-questions-in-public-threads)

- **Enlarge the window first.** With "the exact same ink predictions", a slightly shifted and larger window turned a failing crop into a winning one. Papyrologists "are not going to fill in gaps in things they are very unsure of". [L660](../MASTER_LESSONS.md#l660-enlarge-and-re-centre-the-submission-window-before-fine-tuning-the-model-further)

- **Check letter size in millimetres.** The average Scroll 1 letter "should be about 4 mm". Reject candidates outside the range measured on opened fragments of the same scroll. [L755](../MASTER_LESSONS.md#l755-convert-every-candidate-letters-size-to-millimetres-with-the-volumes-own-voxel-size)

- **Everyone hallucinates letters.** "everyone who has worked on this project has hallucinated letters at some point" (organizer, 2026-07-12). Kollesis seams "can look pretty similar" to ink. [L757](../MASTER_LESSONS.md#l757-check-every-visual-candidate-in-depth-and-cross-section-kollesis-seams-and-a-mesh-leaving-the-sheet-mimic-ink)

- **Run the same display on empty regions.** One author's own filter passed 0 of 10 candidates, and shuffling the angle axis "keeps about half the letter looking blobs". [L756](../MASTER_LESSONS.md#l756-run-the-identical-display-pipeline-on-matched-empty-regions-and-shuffled-inputs-before-believing-a-letter-like-mark)

- **Read only with models that never saw that text's labels.** Models trained on detailed labels "have wrongly reproduced false strok[es]". Leave-one-segment-out models were proposed in 2024. [L758](../MASTER_LESSONS.md#l758-read-text-only-from-models-whose-labels-never-covered-that-text)

- **Label with a flood fill.** "the flood tool prevents your brain from making shapes" (2023). [L763](../MASTER_LESSONS.md#l763-label-fragment-ink-with-a-seeded-flood-fill-rather-than-a-freehand-pen)

- **Show whole segments.** "Zoomed crops can flatter any model." [L761](../MASTER_LESSONS.md#l761-show-whole-segments-in-a-predeclared-set-next-to-an-independent-key-zoomed-crops-flatter-any-model)

- **"Letter-like" is not "correct letter".** In one project's test, 30-46 % of confident letter identities were wrong while "letter-like" verdicts stayed 5/5. [L783](../MASTER_LESSONS.md#l783-letter-like-verdicts-do-not-mean-correct-letter-identities)

- **Blind-read field size needs calibration.** At 2.4 um, readers found known text 0/9 times at 4.9 mm fields and 7/9 at 14.8 mm. On bulk 9 um maps no field size worked (sensitivity at most 2/10). [L781](../MASTER_LESSONS.md#l781-calibrate-the-blind-read-field-size-per-format-a-not-letter-like-read-never-closes-a-region)

- **Remove non-text cues from blind-read sets.** Edge voids alone separated negatives from positives in one test. [L782](../MASTER_LESSONS.md#l782-remove-non-text-cues-from-blind-read-sets-before-launch)

- **Large windows need anti-hallucination evidence.** In 2024 a 512x512 model was reported to change some letters into other letters. [L658](../MASTER_LESSONS.md#l658-large-ink-model-windows-are-now-allowed-but-you-must-show-the-text-is-not-hallucinated)

- **Pixel scores are not reading.** In one project, bulk 9 um maps with held-out AUC 0.7415 and 0.7810 let readers name at most 1-2 letter forms per 4 cm² on the best known-text windows. [L784](../MASTER_LESSONS.md#l784-a-bulk-ink9um-auc-near-074-078-is-pixel-signal-not-legibility)

- **Separate own ink from echoes.** An echo "strengthens toward the neighbouring turn", while "the sheet's own writing peaks near the tracing". [L731](../MASTER_LESSONS.md#l731-separate-a-neighbouring-turns-echo-from-the-sheets-own-ink-with-a-depth-profile)

- **A canonical 2.4 um model loses most of its letter-scale score at 9 um.** One member measured 0.95 on native 2.4 um layers and 0.11 on the same layers downsampled to 9 um. [L754](../MASTER_LESSONS.md#l754-score-a-read-against-a-key-with-a-high-pass-blur-matched-letter-scale-metric-and-a-blob-only-negative-exam)

**If you work on this now.** Spend effort on image quality and context, not annotation. Print a scale bar in millimetres on every review image. Before you believe a mark, run the same display pipeline on empty regions and shuffled inputs, check the depth profile and a cross-section, and rule out seams and wrap echoes. Keep confident letter names out of anything you publish until papyrologists have judged the image.

**Tools and reports worth knowing:** letter-size checks (jrudolph, RICHI); flood-fill labelling (sean and the 2023 annotators); Reader V3 whole-segment comparisons (KLAVIS); retraction with null tests (Saurabh Gupta).

**Open questions**

- What image format and field size give papyrologists the best chance on 9 um scans?
- How should a submission show that a large-window model did not join strokes?

### Validation and controls

In 2023 validation mostly meant comparing against fragment labels and catching obvious leaks, such as a loader that fed the label image to the model. Over time the community learned that every part of a test can fail: the labels can be misplaced, the mask can mean something unexpected, the metric can reward blur, and the baseline can be a single lucky region.

By 2026, pre-registration was common in the #robots channel. Posters published a hash of their protocol before results, and several reported their own kills and corrections. The best practice that emerged is to pair every measurement with a control that should fail, and to report each kind of null result separately.

**Findings**

- **Labels can leak through loaders.** A globbing loader read the ink-label image as input. A leaked model reproduces known label errors; a real one does not. [L742](../MASTER_LESSONS.md#l742-keep-label-files-outside-every-input-directory-a-globbing-loader-can-feed-the-label-to-the-model)

- **Held-out labels can be far out of place.** A registration gate "read 8 voxels while the label sat 1766 voxels out". After the fix, a headline score moved from 0.563 to 0.753 ROC-AUC. [L759](../MASTER_LESSONS.md#l759-gate-held-out-label-registration-on-a-zero-shift-peak-per-segment-not-on-a-correspondence-residual)

- **Validation masks can be mostly unlabelled.** On PHerc0841 and 0500P2 about 88-93 % of the mask lies outside supervision, and AP drops 3-4x there. Label: VERIFIED. [L760](../MASTER_LESSONS.md#l760-read-a-validation-masks-meaning-before-computing-ap-the-pherc08410500p2-masks-are-mostly-unlabelled-area)

- **Plain correlation rewards blur.** It "stays around 0.44 even with the key shifted 150 px". A high-pass letter-scale score with a blob-only exam separates real gains; the method was reproduced on PHerc0841. [L754](../MASTER_LESSONS.md#l754-score-a-read-against-a-key-with-a-high-pass-blur-matched-letter-scale-metric-and-a-blob-only-negative-exam)

- **One region is not a baseline.** Paris 4 alone spans 0.000 % to 14.72 % across 16 ink-blind regions. [L736](../MASTER_LESSONS.md#l736-validate-any-ink-discriminator-on-known-ink-and-known-over-firing-and-never-use-one-region-as-a-baseline)

- **Test discriminators on known ink and known over-firing.** One "depth into sheet" check read 0.64x on real ink and 2.21x on likely over-firing: "Backwards." [L736](../MASTER_LESSONS.md#l736-validate-any-ink-discriminator-on-known-ink-and-known-over-firing-and-never-use-one-region-as-a-baseline)

- **Freeze rules before results.** Post a protocol hash, and report the kill when it fires; one kill fired at 4 % recall against a 50 % bar. [L769](../MASTER_LESSONS.md#l769-freeze-evaluation-rules-by-publishing-a-protocol-hash-before-results-and-report-the-kill-when-it-fires)

- **Measure the reference's floor first.** A pre-registered "blank" stratum (map < 0.10) had no members because the map's floor was about 0.12. [L773](../MASTER_LESSONS.md#l773-measure-the-references-floor-before-pre-registering-a-blank-threshold)

- **Use a reversed-order floor on the same surface.** An absolute floor from one scan did not transfer (0.40-0.55 on one scan vs 0.15-0.39 on another). [L771](../MASTER_LESSONS.md#l771-measure-a-reversed-layer-order-floor-on-the-same-surface-for-every-ink-run-an-absolute-floor-does-not-transfer-between-scans)

- **Agreement between models needs its own floor.** Box-level agreement of r 0.47 fell to 0.27 over the whole segment. [L774](../MASTER_LESSONS.md#l774-report-cross-model-agreement-only-beside-its-reversed-cross-model-floor)

- **Retire gates that fail known positives.** One gate flagged 65.7 % of planes on a known single sheet. Its earlier FAIL verdicts had to be re-judged. [L775](../MASTER_LESSONS.md#l775-test-a-sheet-gate-on-hard-negatives-and-write-what-sheet-verified-does-not-cover) [L776](../MASTER_LESSONS.md#l776-retire-a-gate-that-fails-known-positives-and-re-judge-its-earlier-fail-verdicts)

- **Shuffle nulls test explanations.** A "voxel noise" explanation failed when shuffled depth profiles had lag-1 autocorrelation near 0 against 0.755 / 0.878 real. [L785](../MASTER_LESSONS.md#l785-test-a-statistics-explanation-with-a-shuffle-null-and-an-independent-re-implementation)

- **Check a metric on the official control first.** One per-block metric failed on the official known-text surface itself. [L787](../MASTER_LESSONS.md#l787-check-a-pre-registered-metric-on-the-official-control-before-using-it-on-targets)

- **Keep null states apart.** NO-DATA, INVALID-GEOMETRY, FAILED-CONTROL, FLOOR, INDETERMINATE and CANDIDATE are different findings. One project inked 13 surfaces and found 0 candidates, but its own known-text controls had failed, so that null is weak. [L794](../MASTER_LESSONS.md#l794-keep-no-candidate-separate-from-no-text)

**If you work on this now.** Write the protocol, metric, threshold and kill rule before you look, and publish a hash. For each result, include a positive control that should pass and a negative control that should fail, on the same surface and model. Check that labels peak at zero shift, that the validation mask means what you think, and that your baseline is not one region. Report each kind of null result under its own name.

**Tools and reports worth knowing:** ScrollGT (Martian); letter-scale score (Chris Scheirer); pre-registration hash log (lightsgoblack); validation-mask analysis (ibara, confirmed by AndreasHad); ink model on 13 scrolls (Abd Elilah).

**Open questions**

- Is there a held-out benchmark on eligible-type 9 um scans that predicts legibility?
- How should controls be shared so that different teams' nulls can be compared?
- Which retracted claims (see below) are still being quoted elsewhere as fact?

### Compute, tools and agents

The early community ran on donated GPUs and hand-built pipelines (summary, unverified). People learned to screen at a coarse stride and refine only the hits, to keep 3-D data in chunked stores, and to avoid tools that load whole volumes. The organizers gathered their code into the villa monorepo in late 2024 (summary, unverified), which gave the community one place to report and fix bugs.

In 2026 AI agents changed the volume and the risks. Many reports and pull requests came from Claude, Codex and similar systems. Organizers welcomed the work but set rules: disclose the model, post in #robots, follow CONTRIBUTING.md. They also warned that agents fiddle with parameters, build silent fallbacks, write tests that share their own mistakes, and drift without a human-set goal. Members who ran agents largely agreed, and several published logs of the errors their agents made and how they were caught.

**Findings**

- **Screen coarse, refine fine.** "With stride=2, eta = 10 hrs. With stride=16, eta = 10 mins" (2023). [L692](../MASTER_LESSONS.md#l692-screen-at-a-coarse-inference-stride-and-re-run-only-the-hits-finely)

- **Count bytes, not seconds.** Wall time for identical configs varied from 41.5 s to 254 s. A disk cache cut one run from 1.77 GB and 461 s to 301 MB and 187 s, with bit-identical output. [L672](../MASTER_LESSONS.md#l672-count-bytes-received-during-remote-inference-zarr-3-silently-disabled-villas-chunk-cache)

- **Make long runs resumable.** One whole-scroll run was sized at "41 TB and ~43 days of I/O" on an 11 MB/s link. [L673](../MASTER_LESSONS.md#l673-do-not-let-villas-predict-overwrite-an-interrupted-whole-scroll-run)

- **Log device and number type.** True fp32 differed from the old default output on 4.6-4.9 % of nonzero pixels, by at most 2 levels. On Apple Silicon, one test measured CPU fp32 at "3.261 s/tile" against MPS at "0.427 s/tile", with max|diff| "9.54e-07", but a memory-copy bug dropped patches above about 4,000 slices until fixed. [L674](../MASTER_LESSONS.md#l674-log-the-device-and-autocast-dtype-actually-used-and-compare-any-accelerator-run-with-a-cpu-fp32-reference)

- **Watch for silent GPU memory spill.** On a 6 GB GPU, oversize configs spilled into system RAM "with no out-of-memory error (20-100x slower)". [L683](../MASTER_LESSONS.md#l683-do-not-stream-training-data-from-hugging-face-fetch-only-the-chunks-your-training-config-reads)

- **Pin and read community tools.** Two tools shared one name, and one package's source links returned 404. [L695](../MASTER_LESSONS.md#l695-pin-community-tools-by-version-and-hash-and-read-their-source-before-running-them-on-data)

- **Centre coordinates before GPU clustering.** cuML HDBSCAN converts to float32, which made clusters unstable at large coordinates. [L696](../MASTER_LESSONS.md#l696-centre-coordinates-before-gpu-hdbscan)

- **One heavy job per small VM.** On 4 vCPUs, `renice 19` did not protect inference from a concurrent job. [L792](../MASTER_LESSONS.md#l792-run-one-cpu-heavy-job-per-4-vcpu-vm-renice-did-not-protect-inference)

- **Humans set the goal and the test.** "this project has exactly 0" robust verifiers; leave the choice of experiments to an LLM and "you will find yourself swimming around aimlessly in a pool of token receipts". [L764](../MASTER_LESSONS.md#l764-have-a-human-set-each-experiments-goal-and-success-criterion-this-project-has-no-robust-automatic-verifier)

- **No silent fallbacks.** Agents "default to building in fallbacks for all kinds of things to silently corrupt your intent instead of failing loudly". One organizer spent "35 hours this week just catching claude or codex doing something absolutely heinous". [L765](../MASTER_LESSONS.md#l765-forbid-silent-fallbacks-and-write-or-review-key-tests-independently-of-the-agent-that-wrote-the-code)

- **Measure the fraction affected first.** 40 minutes of CPU showed an intervention touched 1.5 % of labelled sheet, saving 2.5 GPU-hours. [L768](../MASTER_LESSONS.md#l768-measure-how-much-of-the-data-an-intervention-touches-before-training-on-it)

- **Physical sanity beats arithmetic checks.** An agent's five errors in a day were caught by questions like "there can't be a fractional number of letters per line". [L767](../MASTER_LESSONS.md#l767-ask-whether-a-number-can-exist-physically-two-agreeing-models-are-not-a-review)

- **Quote, do not judge.** Organizers called LLM framing of Discord history "unfounded/dishonest" in most places. [L766](../MASTER_LESSONS.md#l766-quote-do-not-judge-when-mining-discord-organizers-call-llm-dead-end-verdicts-unfounded)

- **Briefs must be complete and verbatim.** Paraphrased thresholds blocked valid work twice; follow-on messages to workers were not reliably accepted. [L789](../MASTER_LESSONS.md#l789-quote-rules-verbatim-in-worker-briefs) [L793](../MASTER_LESSONS.md#l793-put-the-full-assignment-in-a-workers-first-brief-follow-on-messages-are-unreliable)

- **Integrate worker branches file by file.** Whole-directory checkouts silently reverted four newer scripts. [L790](../MASTER_LESSONS.md#l790-integrate-worker-branches-file-by-file-from-the-merge-base)

- **Verify completion from outputs.** A job logged as complete had been killed at 274/361 tiles. [L791](../MASTER_LESSONS.md#l791-do-not-record-a-background-job-as-complete-before-its-output-check-passes)

**If you work on this now.** Make every long job resumable, bounded and checked by its output, not its exit code. Log the device, number type, checkpoint and settings. If you use an agent, give it a complete brief with rules quoted verbatim, keep the goal and pass/fail test in human hands, and review its tests separately from its code. Post its reports in #robots with the model named.

**Tools and reports worth knowing:** villa PRs for MPS support (AndreasHad, surgefok, LucasY); cache and resume fixes (Abd Elilah, karasukun, Maker); silent-success fixes (surgefok, George A); "Notes from the model side" error log (Diego-dcv); Tutorial 5 on a 6 GB GPU (mg).

**Open questions**

- What verifiers could make agent work on this problem safer, and who checks them?
- How can CPU-only teams run whole-scroll inference within realistic time and bandwidth?

### Rules and strategy

Prize rules changed often. In 2023 the main prizes were for segmentation, ink detection and the Grand Prize. In 2024 the 2023 Grand Prize winner was presented, over $500,000 in new prizes were announced and monthly Progress Prizes began; in 2025 a First Title Prize was awarded (summary, unverified). By 2026 the focus was First Letters prizes on a list of eligible scrolls and the 2027 Grand Prize, with a much larger prize pool (summary, unverified).

The 2026 rule statements in the Discord were practical. Use only the listed volume for evidence. Large windows are fine with evidence. Submit first and share later, because the first qualifying submission wins. Expect the list to change. Treat counts of other teams' submissions as uninformative.

**Findings**

- **Evidence from the listed volume only.** "you cant predict on the 2.4um and then register the prediction to 9.362" (2026-09-20). [L657](../MASTER_LESSONS.md#l657-derive-all-submitted-first-letters-evidence-from-the-listed-eligible-volume-other-scans-may-only-train-models)

- **Submit before sharing.** If you share an area and "someone else takes the same area with some slight tweaks and meets the 10 letter req, they will get the first letters prize" (2026-10-13). [L661](../MASTER_LESSONS.md#l661-the-prize-goes-to-whoever-first-submits-a-qualifying-image-not-to-whoever-made-the-model-or-segment)

- **Under-explored targets help.** Many submissions go to "the same small ROIs of the same 3-4 scrolls" (2026-10-13). [L662](../MASTER_LESSONS.md#l662-re-check-the-eligible-scroll-list-at-every-cycle-scrolls-are-added-and-withdrawn)

- **Monthly prizes reward progress.** Ink-detection work stays eligible "so long as it moves the progress forward" (2025-10-01). [L663](../MASTER_LESSONS.md#l663-a-count-of-legitimate-submissions-says-nothing-about-found-letters)

- **Prizes rewarded fixes.** The September 2026 progress prizes credited the normalization fix and the checkpoint repair. [L668](../MASTER_LESSONS.md#l668-pass-the-checkpoints-own-ct-normalization-to-vesuviuspredict-the-default-z-scores-each-volume) [L722](../MASTER_LESSONS.md#l722-smoke-test-every-published-ink-checkpoint-on-labelled-ink-some-ship-with-an-untrained-head-that-outputs-05-everywhere)

- **Sequences help papyrologists.** "even 3-4 letter sequences can help" (2026-10-12). [L660](../MASTER_LESSONS.md#l660-enlarge-and-re-centre-the-submission-window-before-fine-tuning-the-model-further)

- **Licences are open but non-commercial for data.** Team models are MIT; data are CC BY-NC 4.0 with citation. [L664](../MASTER_LESSONS.md#l664-record-the-licence-of-each-model-and-dataset-team-models-are-mit-the-data-are-cc-by-nc-40-with-citation)

- **Disclose agent work.** #robots is "for LLM-produced reports of experiments". [L665](../MASTER_LESSONS.md#l665-post-llm-written-reports-in-robots-name-the-model-and-separate-its-output-from-human-commentary)

- **Windows: from small to large with evidence.** In 2024 an organizer recalled that papyrologists had required a field of view "not larger than squares of 64 pixels size". Since 2026-09-10 larger windows are allowed if the submitter shows the text is not hallucinated. [L658](../MASTER_LESSONS.md#l658-large-ink-model-windows-are-now-allowed-but-you-must-show-the-text-is-not-hallucinated)

- **Judging is by image.** Readability "is determined solely by the papyrology teams interpretation of the images/proposed text" (2026-10-18). [L659](../MASTER_LESSONS.md#l659-readability-is-judged-by-the-papyrologists-on-the-images-alone-ask-rules-questions-in-public-threads)

- **DMs are not a rules channel.** Organizers "cannot help out too specifically with things in dms" except about a specific submission. [L659](../MASTER_LESSONS.md#l659-readability-is-judged-by-the-papyrologists-on-the-images-alone-ask-rules-questions-in-public-threads)

- **The list changes both ways.** Ten scans were added on 2026-09-10; PHerc 1447 was withdrawn from First Letters on 2026-09-24 but "still remains eligible for the Grand Prize". [L662](../MASTER_LESSONS.md#l662-re-check-the-eligible-scroll-list-at-every-cycle-scrolls-are-added-and-withdrawn)

- **Agent pull requests have rules.** "We're getting a lot of claude-spam" (2026-08-13); PRs that miss the guidelines may be closed without comment. [L666](../MASTER_LESSONS.md#l666-agent-prs-and-issues-to-villa-must-follow-contributingmd-or-they-are-closed-without-comment)

- **Cheap routes are still open.** Organizers suggested spiral-fitting whole prize scrolls, which nobody had done for almost all of them by August 2026. [L721](../MASTER_LESSONS.md#l721-organizers-suggest-spiral-fitting-whole-prize-scrolls-as-a-cheap-first-letters-route-test-it-with-a-pre-registered-coverage-and-ink-check)

**If you work on this now.** Re-read the prize page at the start of each cycle and diff the eligible list. Keep a provenance log that ties every submitted pixel to the listed volume. Submit a qualifying candidate before you share it, keep a timestamped record, and render nested windows from the same predictions before resubmitting. Ask rules questions in public threads.

**Open questions**

- Which eligible scrolls have the best mix of scan quality, surface coverage and low competition right now? Check the live list.
- How will the 2027 Grand Prize criteria be judged? See the official page.

---

## Current rules that matter (re-check before relying)

These are organizer statements made in the Discord, with dates. The prize page on scrollprize.org governs. Rules change, so re-read it before you rely on any of these. Full quotes are in [section 8A](../MASTER_LESSONS.md#8a-rules-and-organizer-guidance-re-verify-before-relying-rules-change).

1. **Submitted evidence must come entirely from the listed eligible volume** (2026-09-05, 2026-09-13, 2026-09-20). Training on finer scans is fine. Predicting on the 2.4 um scan and registering the result onto the 9.362 um scan is not. [L657](../MASTER_LESSONS.md#l657-derive-all-submitted-first-letters-evidence-from-the-listed-eligible-volume-other-scans-may-only-train-models)

2. **Large ink-model windows are allowed, but you must show the text is not hallucinated** (announcement 2026-09-10). Until then the guidance had been small inputs; in 2024 an organizer recalled a field of view "not larger than squares of 64 pixels size". Report zero train/predict overlap, a held-out check, the false-ink rate on blank papyrus and a small-window comparison. [L658](../MASTER_LESSONS.md#l658-large-ink-model-windows-are-now-allowed-but-you-must-show-the-text-is-not-hallucinated)

3. **Readability is judged by the papyrology team on the images alone** (2026-10-18). Annotations "are not used in the judgement of readability". Ask rules questions in public threads; DMs are for specific submissions. [L659](../MASTER_LESSONS.md#l659-readability-is-judged-by-the-papyrologists-on-the-images-alone-ask-rules-questions-in-public-threads)

4. **Enlarge and re-centre the window before fine-tuning further** (2026-10-18). This is "probably our most common feedback". Resubmissions are unlimited. Ten scattered certain characters would in theory qualify, but "even 3-4 letter sequences can help" (2026-10-12). [L660](../MASTER_LESSONS.md#l660-enlarge-and-re-centre-the-submission-window-before-fine-tuning-the-model-further)

5. **The prize goes to whoever first submits a qualifying image** (2026-09-29), "regardless of who trained the model, or created the segment". Submissions are ranked in order of submission. Anything shared in the Discord may be used by others. [L661](../MASTER_LESSONS.md#l661-the-prize-goes-to-whoever-first-submits-a-qualifying-image-not-to-whoever-made-the-model-or-segment)

6. **Re-check the eligible list every cycle** (2026-09-10, 2026-09-24, 2026-10-08). The count was 21 after 2026-10-08. [L662](../MASTER_LESSONS.md#l662-re-check-the-eligible-scroll-list-at-every-cycle-scrolls-are-added-and-withdrawn)

7. **Submission counts say nothing about letters found** (2025-01-27). [L663](../MASTER_LESSONS.md#l663-a-count-of-legitimate-submissions-says-nothing-about-found-letters)

8. **Licences** (2026-08-16, 2026-10-17). Team models are MIT-licensed and usable in prize submissions. The data are CC BY-NC 4.0 and must be cited as scrollprize.org/data asks. [L664](../MASTER_LESSONS.md#l664-record-the-licence-of-each-model-and-dataset-team-models-are-mit-the-data-are-cc-by-nc-40-with-citation)

9. **LLM-written reports go in #robots** (2026-07-29). Name the model, and separate model output from human commentary. AI-generated answers are not allowed in place of your own reasoning in other channels. [L665](../MASTER_LESSONS.md#l665-post-llm-written-reports-in-robots-name-the-model-and-separate-its-output-from-human-commentary)

10. **Agent pull requests and issues to villa must follow CONTRIBUTING.md** (2026-08-13), or they may be "closed without comment". [L666](../MASTER_LESSONS.md#l666-agent-prs-and-issues-to-villa-must-follow-contributingmd-or-they-are-closed-without-comment)

---

## Top traps

The most costly mistakes the community found, with the fix in brief. Each links its lesson. Numbers are the posters' own unless the lesson says otherwise; open the lesson before reusing one.

### Data and tools

- **Bad pyramid levels in the ink-label bucket.** In 18 of 33 surface volumes, level 2 holds only 17 of 65 depth slices, and nothing flags it. The released ink_9um scored AUC 0.54 on its own training scroll from level 2, and 0.91-0.93 after rebuilding from level 0. Build 9 um inputs from level 0. [L667](../MASTER_LESSONS.md#l667-rebuild-96-um-inputs-from-level-0-in-18-of-33-hf-ink-bucket-surface-volumes-level-2-holds-only-17-of-65-depth-slices)

- **Wrong default normalization in `vesuvius.predict`.** The default z-scores each volume and ignores the model's own CT normalization. Fixing it raised median recall from 0.803 to 0.940 and precision from 0.467 to 0.742. [L668](../MASTER_LESSONS.md#l668-pass-the-checkpoints-own-ct-normalization-to-vesuviuspredict-the-default-z-scores-each-volume)

- **Phantom "sheet" on empty CT.** Published m7 surface maps mark sheet where CT is exactly zero (median 38 %, worst 92 % in one count). Mask by CT > 0. New runs are fixed; published predictions are not repaired. [L671](../MASTER_LESSONS.md#l671-published-m7-surface-maps-mark-sheet-on-zero-ct-mask-them-by-ct--0-for-statistics-but-do-not-threshold-them-by-ct-intensity)

- **Silent re-downloads.** zarr 3 quietly disabled villa's chunk cache, so remote inference fetched about 17x more data than needed in one report. Measure bytes received, not seconds. [L672](../MASTER_LESSONS.md#l672-count-bytes-received-during-remote-inference-zarr-3-silently-disabled-villas-chunk-cache)

- **Restarts that erase work.** villa's predict opened its output in overwrite mode, so restarting an interrupted run destroyed finished parts. Use `--resume`. [L673](../MASTER_LESSONS.md#l673-do-not-let-villas-predict-overwrite-an-interrupted-whole-scroll-run)

- **Success messages after failure.** Several commands exited 0 after finding nothing or writing the wrong shape. Assert output shape and counts after every step. [L675](../MASTER_LESSONS.md#l675-treat-a-zero-result-success-as-a-failure-and-assert-output-shapes-against-the-source)

- **Missing chunks read as blank papyrus.** zarr returns zeros for absent chunks with no error. A "no ink" verdict must check CT coverage, not just the mesh. [L735](../MASTER_LESSONS.md#l735-gate-no-ink-verdicts-on-ct-coverage-not-mesh-validity-and-calibrate-against-regions-outside-the-test)

- **Broken public checkpoints.** One published ink checkpoint had an untrained head and output 0.5 everywhere; a second broken one turned up among 18 checked. Smoke-test every checkpoint on known ink first. [L722](../MASTER_LESSONS.md#l722-smoke-test-every-published-ink-checkpoint-on-labelled-ink-some-ship-with-an-untrained-head-that-outputs-05-everywhere)

- **Silent precision and device defaults.** `--amp-dtype default` ran fp16. On Apple Silicon, a memory-copy bug dropped verified patches above about 4,000 slices. Log the device and number type used, and compare with a CPU reference. [L674](../MASTER_LESSONS.md#l674-log-the-device-and-autocast-dtype-actually-used-and-compare-any-accelerator-run-with-a-cpu-fp32-reference)

- **Mixed-up file hosts.** Some data live outside the usual tree, and some declared pyramid levels return 404. Inventory every host and audit headers before a job. [L680](../MASTER_LESSONS.md#l680-inventory-every-data-host-before-declaring-data-missing-and-audit-headers-before-a-job)

- **Clipped 8-bit volumes.** The public ESRF zarrs are 8-bit copies with per-volume windows, and both ends can be clipped. Mask both ends before comparing volumes by intensity. [L677](../MASTER_LESSONS.md#l677-do-not-compare-esrf-8-bit-volumes-by-raw-intensity-without-masking-clipped-ends-and-reading-each-volumes-window)

- **Zero is not air on older volumes.** On the older uint16 volumes, the window includes negative values, so air sits "somewhere in the neighborhood of 25k". [L679](../MASTER_LESSONS.md#l679-on-the-older-uint16-volumes-zero-is-not-air-the-windows-include-negative-attenuation)

- **Annotations in the wrong frame.** In one case 26 % of ground-truth z-coordinates could not exist in the assumed volume, and every length was off by 1.21x. Check that every coordinate is in bounds. [L685](../MASTER_LESSONS.md#l685-check-the-frame-of-annotation-coordinates-coordinates-that-cannot-exist-prove-a-frame-error)

### Geometry

- **Segments have no fixed "up".** Layer stacks are not consistently oriented, and Kaggle layer 0 is the deep side. Measure each segment's orientation from geometry. [L697](../MASTER_LESSONS.md#l697-measure-each-segments-orientation-from-geometry-layer-stacks-have-no-fixed-recto-direction-and-kaggle-layer-0-is-the-deep-side)

- **Meshes that leave the scroll.** In one survey of 299 segments, 33 % of PHerc1447's mesh vertices and 19 % of PHerc1667's lay off the masked object. Measure the off-object fraction before use. [L702](../MASTER_LESSONS.md#l702-measure-the-fraction-of-each-mesh-lying-outside-ct-support-and-the-gap-to-adjacent-winding-segments)

- **Sheet switches go undetected.** On 213 confirmed switches, tifxyz-doctor (any cue) found 12 % (25/213), and the most-used detector about 1 in 9. Keep manual cross-section review. [L705](../MASTER_LESSONS.md#l705-expect-current-sheet-switch-detectors-to-miss-most-real-switches-benchmark-them-on-confirmed-switches-with-smooth-bend-negatives)

- **Spiral fits that look complete but are not.** One audit found published fits of eligible scrolls scoring no better than chance against random-shifted copies (AI-run, unreplicated). Score a fit against shifted copies before inking it. [L699](../MASTER_LESSONS.md#l699-score-a-spiral-fit-against-random-shift-copies-of-itself-on-the-raw-ct-before-inking-it)

- **Blaming the ink model for a bad surface.** One member's eligible-scroll meshes had sheet contrast of 1.7 to 55 against 57 to 92 for 38 curated segments. Compare contrast with many curated surfaces, not one. [L700](../MASTER_LESSONS.md#l700-check-an-eligible-scroll-surfaces-sheet-contrast-against-many-curated-surfaces-before-blaming-the-ink-model)

- **Synthetic tests that do not transfer.** A sheet-switch tool scored 1.00 precision and recall on synthetic data and about 0.19 precision on a real cube. Organizers say toy problems "_never_ translate to our real data". [L704](../MASTER_LESSONS.md#l704-synthetic-benchmarks-and-phantoms-are-unit-tests-only-validate-geometry-tools-on-real-imperfect-patches)

- **Constraints that make fits worse.** Three better winding-constraint generators all degraded a spiral fit against a no-constraint baseline. A/B every constraint source. [L707](../MASTER_LESSONS.md#l707-score-winding-constraints-against-held-out-human-chains-and-ab-every-constraint-source-against-a-no-constraint-fit)

- **Brightness-chasing refinement.** Moving a mesh to maximise brightness makes it slide into the next sheet or into the papyrus. Judge refinement on held-out ink, not sharpness. [L715](../MASTER_LESSONS.md#l715-brightness-maximising-surface-refinement-drifts-across-sheets-gate-it-on-held-out-ink-not-sharpness)

- **A constant winding pitch.** Pitch "swings 3x inside one mesh" (median 180 um, quartiles 126 to 441 um on Paris 4). Measure spacing per location at level 1 or finer. [L710](../MASTER_LESSONS.md#l710-do-not-treat-winding-pitch-or-sheet-spacing-as-a-constant-and-measure-it-at-level-1-or-finer)

- **Averaged cross-sections.** Averaging 313 irregular sections "manufactures an ellipse that exists at no height". Fit each height, and post CT renders and cross-sections with any unwrap claim. [L711](../MASTER_LESSONS.md#l711-fit-cross-section-shape-per-height-and-post-ct-renders-and-cross-sections-with-any-unwrap-claim)

- **Merge-blind surface scores.** Dice alone can reward merging or shredding sheets. Report merges and fragments beside Dice, with simple baselines. [L712](../MASTER_LESSONS.md#l712-report-sheet-merges-and-fragments-together-against-a-dilated-label-floor-and-a-ct-threshold-baseline)

- **Leaky held-out splits.** In one test 54.8 % of "sealed" points sat within 0.5 voxel of a fit input. Split by distance, not by patch name. [L709](../MASTER_LESSONS.md#l709-split-held-out-geometry-by-distance-to-the-fits-inputs-not-by-patch-name)

### Ink

- **Wrong depth window or direction.** Small changes in the slice range lose letters and pick up the next sheet. The wrong depth direction cost 0.09-0.20 AUC in one pre-registered test. Record and sweep the window, and run both directions. [L728](../MASTER_LESSONS.md#l728-record-the-inference-depth-window-and-sweep-it-for-any-candidate) [L724](../MASTER_LESSONS.md#l724-pick-the-depth-direction-label-free-by-output-separation-and-read-forwardreversed-agreement-on-an-unread-volume-as-no-ink)

- **Surface offset on the wrong side.** Being 3 slices off on the bad side already cost about 0.06-0.08 F1; 5 slices cost about 0.16. Keep the surface on the sheet front. [L729](../MASTER_LESSONS.md#l729-surface-offset-costs-ink-asymmetrically-keep-the-surface-within-3-slices-on-the-bad-side)

- **Echoes from the next turn.** Wide reading windows reach the neighbouring wrap, and its writing prints into the map. Use a depth profile: own ink peaks at the trace. [L731](../MASTER_LESSONS.md#l731-separate-a-neighbouring-turns-echo-from-the-sheets-own-ink-with-a-depth-profile)

- **Assuming ink is darker.** At 9 um carbon ink is usually slightly brighter than papyrus, and the sign varies by scroll. Drop darkness-based vetoes. [L734](../MASTER_LESSONS.md#l734-do-not-assume-carbon-ink-is-darker-than-papyrus-at-9-um-it-is-usually-slightly-brighter-and-the-sign-varies-by-scroll)

- **"No ink" from a cross-scroll model.** A cross-scroll model showing nothing does not mean a scroll is blank. Pair every null with a same-scroll positive control. [L739](../MASTER_LESSONS.md#l739-per-scroll-ink-models-still-beat-the-cross-scroll-9-um-models-pair-any-cross-scroll-null-with-a-same-scroll-positive-control)

- **One region as a baseline.** Paris 4 itself spans 0.000 % to 14.72 % ink across 16 regions, so "N times Paris 4" figures depend on which block you divide by. [L736](../MASTER_LESSONS.md#l736-validate-any-ink-discriminator-on-known-ink-and-known-over-firing-and-never-use-one-region-as-a-baseline)

- **Wrong production recipe.** The public 2.4 um defaults differ from production (layer window, scaling, tile blending). Copy them from the bucket's metadata.json and reproduce one published map at r >= 0.95 first. [L726](../MASTER_LESSONS.md#l726-copy-layer-window-normalization-and-tile-blending-from-the-buckets-metadatajson-to-reproduce-the-canonical-24-um-ink-maps)

- **Off-grid stride.** ink_9um output depends on where its 128 px window starts, with period 8. Use strides that are multiples of 8. [L725](../MASTER_LESSONS.md#l725-use-an-on-grid-stride-a-multiple-of-8-for-ink9um-sliding-window-inference)

- **Jitter too large for the window.** ±2 slices of depth jitter ruins a 5-slice window. Scale jitter to the window. [L730](../MASTER_LESSONS.md#l730-scale-depth-jitter-to-the-window-2-slices-of-jitter-on-a-5-slice-window-ruins-it)

- **Compressed volumes.** Running released ink models on volcomp q8 volumes cost about a quarter of the detector's separation in one test. Use uncompressed volumes. [L748](../MASTER_LESSONS.md#l748-do-not-run-released-ink-models-on-volcomp-q8-volumes-without-adaptation)

- **Gains credited to the wrong cause.** A retraining gain must be checked against a matched control run, and a benchmark gain is "not extra letters". [L738](../MASTER_LESSONS.md#l738-credit-a-retraining-gain-to-new-data-only-with-a-matched-control-run-and-do-not-equate-it-with-legibility)

- **Self-training that drifts.** Without fixed ground truth in every round, self-made labels "spiral" into fibres. Black in a prediction mask means "not seen", not "no ink". [L741](../MASTER_LESSONS.md#l741-keep-a-fixed-ground-truth-anchor-set-in-every-self-labelling-round-on-scrolls-without-ground-truth-labels-spiral-into-fibres) [L740](../MASTER_LESSONS.md#l740-curate-pseudo-labels-and-use-three-state-masks-black-in-a-prediction-mask-means-not-seen-not-no-ink)

### Reading and validation

- **Pareidolia from contrast stretching.** One member retracted two public letter claims after the same pipeline made "equally letter looking marks" on empty regions. Run the identical display on empty and shuffled inputs first. [L756](../MASTER_LESSONS.md#l756-run-the-identical-display-pipeline-on-matched-empty-regions-and-shuffled-inputs-before-believing-a-letter-like-mark)

- **Letters of impossible size.** Convert every candidate to millimetres; Scroll 1 letters are about 4 mm. [L755](../MASTER_LESSONS.md#l755-convert-every-candidate-letters-size-to-millimetres-with-the-volumes-own-voxel-size)

- **Seams and drifting meshes mimic ink.** Kollesis seams (sheet joins) and a mesh leaving the sheet can look like ink. Check depth and cross-sections. "Everyone who has worked on this project has hallucinated letters at some point." [L757](../MASTER_LESSONS.md#l757-check-every-visual-candidate-in-depth-and-cross-section-kollesis-seams-and-a-mesh-leaving-the-sheet-mimic-ink)

- **Misplaced held-out labels.** A registration bug placed labels about 1766 voxels out, and produced a false "models drop to ~0.55" headline. Require each label to peak at zero shift. [L759](../MASTER_LESSONS.md#l759-gate-held-out-label-registration-on-a-zero-shift-peak-per-segment-not-on-a-correspondence-residual)

- **Flattering crops.** "Zoomed crops can flatter any model." Show whole segments from a set declared in advance. [L761](../MASTER_LESSONS.md#l761-show-whole-segments-in-a-predeclared-set-next-to-an-independent-key-zoomed-crops-flatter-any-model)

- **Letter-like is not legible.** In one project's test, "letter-like" verdicts stayed 5/5 while 30-46 % of confident letter identities were wrong. [L783](../MASTER_LESSONS.md#l783-letter-like-verdicts-do-not-mean-correct-letter-identities)

- **Mostly-unlabelled validation masks.** On PHerc0841 and PHerc0500P2, about 88-93 % of the "validation" mask lies outside supervision. Score on validation ∩ supervision, or use AUC, and say which. [L760](../MASTER_LESSONS.md#l760-read-a-validation-masks-meaning-before-computing-ap-the-pherc08410500p2-masks-are-mostly-unlabelled-area)

- **Plain correlation against a key.** Plain correlation with a 2.4 um key "stays around 0.44 even with the key shifted 150 px". Use a high-pass, blur-matched letter-scale score with a blob-only negative. [L754](../MASTER_LESSONS.md#l754-score-a-read-against-a-key-with-a-high-pass-blur-matched-letter-scale-metric-and-a-blob-only-negative-exam)

- **Canvas area is not sheet area.** Raster canvas area overstated true mesh area about 2x in one project. Compute area from valid triangles. [L788](../MASTER_LESSONS.md#l788-compute-true-mesh-area-from-valid-triangles-raster-canvas-area-overstates-it-about-2x)

### Agents

- **No automatic verifier.** "llms are very good at solving things autonomously that have robust verifiers, and this project has exactly 0." A human must set each goal and success test. [L764](../MASTER_LESSONS.md#l764-have-a-human-set-each-experiments-goal-and-success-criterion-this-project-has-no-robust-automatic-verifier)

- **Silent fallbacks and self-written tests.** Agents build in fallbacks that hide failure, and write tests with their own wrong assumptions. One feature had 119 passing tests and was still broken. [L765](../MASTER_LESSONS.md#l765-forbid-silent-fallbacks-and-write-or-review-key-tests-independently-of-the-agent-that-wrote-the-code)

- **Judging the Discord.** Organizers call LLM "dead end" verdicts on community work unfounded. Quote, do not judge. [L766](../MASTER_LESSONS.md#l766-quote-do-not-judge-when-mining-discord-organizers-call-llm-dead-end-verdicts-unfounded)

- **Agreement between models is not review.** Two models fed the same newest input "converge fast and converge wrong". Ask whether each number can physically exist. [L767](../MASTER_LESSONS.md#l767-ask-whether-a-number-can-exist-physically-two-agreeing-models-are-not-a-review)

- **Reporting a running job as done.** One reversed read was logged as complete; it had been killed at 274/361 tiles. Record completion only from an output check. [L791](../MASTER_LESSONS.md#l791-do-not-record-a-background-job-as-complete-before-its-output-check-passes)

- **Paraphrased rules in briefs.** Twice a paraphrased threshold in a worker brief was narrower than the real rule and blocked valid work. Quote rules verbatim. [L789](../MASTER_LESSONS.md#l789-quote-rules-verbatim-in-worker-briefs)

- **Steering workers after launch.** Follow-on messages to workers were not reliably accepted. Put the full assignment in the first brief. [L793](../MASTER_LESSONS.md#l793-put-the-full-assignment-in-a-workers-first-brief-follow-on-messages-are-unreliable)

---

## Claims later retracted

Community members posted these claims and then withdrew or corrected them. Never reuse a claim in the first column as fact. Full table: [section 8H](../MASTER_LESSONS.md#8h-retracted-or-corrected-community-claims).

| Retracted claim | Corrected by, when | Correction | Lesson |
|---|---|---|---|
| Held-out ScrollGT scores drop to ~0.55 | Martian (author), 2026-08-15 | Labels sat ~1766 voxels out; corrected 0.563 to 0.753 ROC-AUC | [L759](../MASTER_LESSONS.md#l759-gate-held-out-label-registration-on-a-zero-shift-peak-per-segment-not-on-a-correspondence-residual) |
| m7 recall/precision from `vesuvius.predict` defaults | Abd Elilah (author), 2026-08-07 | Wrong normalization; recall 0.803 to 0.940, precision 0.467 to 0.742 | [L668](../MASTER_LESSONS.md#l668-pass-the-checkpoints-own-ct-normalization-to-vesuviuspredict-the-default-z-scores-each-volume) |
| Region-run traffic overhead of 384x | Abd Elilah (author), 2026-08-05 | 82.94x; the region tiled on a different grid | [L670](../MASTER_LESSONS.md#l670-anchor-region-of-interest-inference-to-the-full-volume-patch-grid) |
| PHerc1218 cross-section fits an ellipse at R² = 0.948 | Diego-dcv (author), 2026-08-02 | Artefact of averaging 313 sections; single sections 0.848 down to 0.592 | [L711](../MASTER_LESSONS.md#l711-fit-cross-section-shape-per-height-and-post-ct-renders-and-cross-sections-with-any-unwrap-claim) |
| Borrow other scrolls' threshold (87) for ink_9um | 잠이올랑말랑 (author), 2026-10-02 and 2026-10-09 | 87 lost 0.096 / 0.118 / 0.095 F1; the quantile rule held in all three tests | [L733](../MASTER_LESSONS.md#l733-carry-a-binarization-threshold-only-within-the-same-model-the-operating-quantile-rule-held-best-in-three-pre-registered-tests) |
| seed42 step-050000 is the better ink_9um checkpoint | OBCD (author), 2026-10-12 | It lost held out on all three segments | [L723](../MASTER_LESSONS.md#l723-treat-each-released-ink9um-checkpoint-as-a-separate-instrument-select-by-held-out-score-per-region-and-do-not-ensemble-by-default) |
| Eligible-scroll surfaces fail on placement | rodriguescarson (author), 2026-10-18 | Contrast, not placement, separates them; the single control was unusually good | [L700](../MASTER_LESSONS.md#l700-check-an-eligible-scroll-surfaces-sheet-contrast-against-many-curated-surfaces-before-blaming-the-ink-model) |
| A no-ground-truth mesh score ranks the outer winding best | pscamillo, accepted by author, 2026-09-14 | The walk crosses crust into air at the outer wrap | [L701](../MASTER_LESSONS.md#l701-clip-normal-walk-sheet-metrics-at-the-scroll-mask-at-the-outer-wrap-the-walk-crosses-crust-into-air) |
| Two public letter candidates (Scroll 3 and PHerc0009B) | Saurabh Gupta (author), 2026-06-03 | Own filter passed 0 of 10; empty regions looked the same | [L756](../MASTER_LESSONS.md#l756-run-the-identical-display-pipeline-on-matched-empty-regions-and-shuffled-inputs-before-believing-a-letter-like-mark) |
| Four-valued (Belnap) output adds expressiveness | SUBIT-INK author, 2026-06-28/29 | F1 0.7954 below binary 0.8197; "oversold" | [L752](../MASTER_LESSONS.md#l752-a-new-output-semantics-must-beat-the-binary-baseline-on-the-same-held-out-split) |
| Annotation lengths of "~145 um" | pscamillo, after Aleksei Drobkov, 2026-07-31 | Frame error; lengths scale by 1.21x | [L685](../MASTER_LESSONS.md#l685-check-the-frame-of-annotation-coordinates-coordinates-that-cannot-exist-prove-a-frame-error) |
| "beyond 8 voxels: 0.0%" from 5 scrolls | Abd Elilah (author), 2026-07-29 | 25.4 % at 36 scrolls | [L768](../MASTER_LESSONS.md#l768-measure-how-much-of-the-data-an-intervention-touches-before-training-on-it) |
| inkdx certifies a tile as scanned from a self-calibrated score | anshu231 (author), after Abd Elilah, 2026-08-05 | The gate only looked at the mesh | [L735](../MASTER_LESSONS.md#l735-gate-no-ink-verdicts-on-ct-coverage-not-mesh-validity-and-calibrate-against-regions-outside-the-test) |
| Kaggle fragment layers start too deep | Brett Olsen, 2023-10-15 | Layer 0 is the bottom | [L697](../MASTER_LESSONS.md#l697-measure-each-segments-orientation-from-geometry-layer-stacks-have-no-fixed-recto-direction-and-kaggle-layer-0-is-the-deep-side) |
| An unsupervised fragment result read ink cleanly | Author, after Brett Olsen, 2023-10-15 | The loader fed the label image as input | [L742](../MASTER_LESSONS.md#l742-keep-label-files-outside-every-input-directory-a-globbing-loader-can-feed-the-label-to-the-model) |
| Fragment 5 PPM values shifted 180 px | jrudolph (author), 2024-10-02 | His own TIFF parser bug | [L770](../MASTER_LESSONS.md#l770-suspect-your-own-reader-before-reporting-a-data-defect-and-read-the-file-with-two-libraries) |
| Apple Silicon spiral fits match CPU at scale | LucasY, reproduced by AndreasHad, 2026-10-06 | Above ~4,000 slices a memory-copy bug dropped patches | [L674](../MASTER_LESSONS.md#l674-log-the-device-and-autocast-dtype-actually-used-and-compare-any-accelerator-run-with-a-cpu-fp32-reference) |

---

## If you are an AI agent starting now

1. **Re-read the live prize page first.** Diff the eligible-volume list against your targets and date it. Treat every rule in this file as possibly stale. [L662](../MASTER_LESSONS.md#l662-re-check-the-eligible-scroll-list-at-every-cycle-scrolls-are-added-and-withdrawn)
   Why: scrolls are added and withdrawn, and one award removed a scroll in October 2026.

2. **Trace every submitted pixel to the listed eligible volume.** Train anywhere allowed, but predict only on that volume. [L657](../MASTER_LESSONS.md#l657-derive-all-submitted-first-letters-evidence-from-the-listed-eligible-volume-other-scans-may-only-train-models)
   Why: organizers have ruled out predicting on a finer scan and registering the result.

3. **Let a human set the goal and the pass/fail test before you run anything costly.** Show a human an image at each stage. [L764](../MASTER_LESSONS.md#l764-have-a-human-set-each-experiments-goal-and-success-criterion-this-project-has-no-robust-automatic-verifier)
   Why: organizers say this project has no robust automatic verifier, and agents drift without one.

4. **Smoke-test every model, checkpoint and data level on known ink before use.** Name the exact checkpoint, depth window, direction and normalization in every result. [L722](../MASTER_LESSONS.md#l722-smoke-test-every-published-ink-checkpoint-on-labelled-ink-some-ship-with-an-untrained-head-that-outputs-05-everywhere) [L727](../MASTER_LESSONS.md#l727-pin-the-checkpoint-layer-window-and-inchans-of-every-map-forks-and-repo-snapshots-change-them-silently)
   Why: published checkpoints have shipped broken, and the default checkpoint was the worst of 14 on one region.

5. **Prove the surface is on the sheet before judging ink.** Check off-object fraction, contrast against many curated surfaces, and cross-sections. [L700](../MASTER_LESSONS.md#l700-check-an-eligible-scroll-surfaces-sheet-contrast-against-many-curated-surfaces-before-blaming-the-ink-model) [L702](../MASTER_LESSONS.md#l702-measure-the-fraction-of-each-mesh-lying-outside-ct-support-and-the-gap-to-adjacent-winding-segments)
   Why: many "no ink" results were really surfaces in air, on the wrong sheet or on missing data.

6. **Fail loudly.** No silent fallbacks. Assert shapes, counts and bytes after every step, and treat "found nothing" as an error. [L675](../MASTER_LESSONS.md#l675-treat-a-zero-result-success-as-a-failure-and-assert-output-shapes-against-the-source) [L765](../MASTER_LESSONS.md#l765-forbid-silent-fallbacks-and-write-or-review-key-tests-independently-of-the-agent-that-wrote-the-code)
   Why: several shared tools reported success after producing empty or wrong output.

7. **Run controls that can fail.** Use reversed depth order, empty regions, shuffled inputs and a same-scroll positive control. Report "no candidate" separately from "no text". [L756](../MASTER_LESSONS.md#l756-run-the-identical-display-pipeline-on-matched-empty-regions-and-shuffled-inputs-before-believing-a-letter-like-mark) [L794](../MASTER_LESSONS.md#l794-keep-no-candidate-separate-from-no-text)
   Why: absolute floors did not transfer between scans, and failed controls make nulls weak.

8. **Pre-register and publish the hash.** Report the result when your own kill rule fires. [L769](../MASTER_LESSONS.md#l769-freeze-evaluation-rules-by-publishing-a-protocol-hash-before-results-and-report-the-kill-when-it-fires)
   Why: pre-registered posters caught and published their own errors, which built trust.

9. **Do not count model agreement as review, and do not judge others' work.** Quote people with name and date, and ask organizers short questions in public threads. [L766](../MASTER_LESSONS.md#l766-quote-do-not-judge-when-mining-discord-organizers-call-llm-dead-end-verdicts-unfounded) [L767](../MASTER_LESSONS.md#l767-ask-whether-a-number-can-exist-physically-two-agreeing-models-are-not-a-review)
   Why: organizers called LLM verdicts on community work unfounded, and two agreeing models share blind spots.

10. **Follow the community rules for agents.** Post in #robots with the model named, follow CONTRIBUTING.md for pull requests, and never copy scroll text, readings or candidate locations into public files. [L665](../MASTER_LESSONS.md#l665-post-llm-written-reports-in-robots-name-the-model-and-separate-its-output-from-human-commentary) [L666](../MASTER_LESSONS.md#l666-agent-prs-and-issues-to-villa-must-follow-contributingmd-or-they-are-closed-without-comment)
   Why: undisclosed agent posts get moved or locked, and scroll text must stay inside the official Discord.

---

## About the sources and their limits

- **Coverage.** The export holds 731 thread files and 41,734 message records. It is not the whole server: some channels were excluded or inaccessible (summary, unverified for the list of exclusions).
- **How lessons were checked.** Each Part 8 lesson was checked against the raw export. Several hundred quotes in the AI-written review were spot-checked and found correct. See [section 8J](../MASTER_LESSONS.md#8j-errors-in-the-community-summary) for its known errors.
- **Known errors in the review.** It claims dossiers for 724 threads, but the export has 731 files. Some file names are garbled. Its topic tags and "pre-registered" tags are keyword noise. Some excerpts quote a claim but omit its correction. Some entries repeat many times, so deduplicate before counting evidence.
- **Gaps in the review.** It does not mention the 2026-07-29 #robots rule, the 2026-08-13 contributor-guidelines announcement, the 2026-09-10 window-size rule change or the 2026-10-18 judging guidance. This digest covers them from Part 8.
- **Scroll Swarm results.** A few lessons (L771-L794) come from Scroll Swarm, a separate AI-run project, not from the Discord. Its results on eligible scrolls are aggregate only.
- **What "MEASURED" means here.** A number labelled MEASURED is what its poster reported. It is not independently confirmed unless the lesson's label says VERIFIED and names who reproduced it.
- **Dates matter.** Organizer statements are what was said on that date. Rules, eligible lists and tools have changed since, and will change again.
