# What we got wrong, and how we fixed it (33 lessons)

These are the traps we fell into while searching a hard, unread scroll (PHerc0268) for first letters with public
ink models. Many teams run the same tools, so we expect the same traps.

Each lesson has four parts:
- **Trap:** what went wrong.
- **Evidence:** a file in this repository, or a commit in the project's private working repository. Private evidence is
  marked as such; it cannot be opened from here.
- **Fix:** what to do instead.
- **Label:** VERIFIED, MEASURED, or INFERENCE.

## A. Measurement and science

**1. Comparing a number with a bar from a different pipeline stage.**
- **Trap:** we compared a raw spiral-fit "phase lock" with a published bar (2.46). That bar is measured after snapping
  and flattening.
- **Evidence:** private, project log correction (commit `3acd36e1c` in the project's private working history).
- **Fix:** compare like with like, at the same stage. For a raw fit, test on-sheet geometry directly:
  - mesh normal vs the structure-tensor normal;
  - CT layer-profile peak at the surface;
  - render texture: continuous fibres vs arch patterns.
- **Label:** VERIFIED (record).

**2. Calibration set contaminated across scrolls.**
- **Trap:** a renderer-calibration pool contained a sample from another scroll (PHerc1203).
- **Evidence:** private PoC notes, withdrawn calibration.
- **Fix:** audit every calibration and validation set for scroll identity before use.
- **Label:** VERIFIED (record).

**3. An ink image that averaged both faces and stretched each image on its own.**
- **Trap:** averaging forward and reverse maps mixes recto and verso, and a per-image contrast stretch turns noise into
  "ink".
- **Evidence:** private v0 image, withdrawn. The fixed-scale display used here reproduces Erwin Nieuwlaar's letters
  (fig. 3).
- **Fix:**
  - use only the face you read (reverse maps with outward normals);
  - display on a FIXED absolute scale, p 0.40 → 0.70 (METHODS §7, [`scripts/pipeline/overlay.py`](../scripts/pipeline/overlay.py));
  - validate every display change on a positive control.
- **Label:** VERIFIED.

**4. Squeezed renders.**
- **Trap:** we assumed 20 vox column spacing on meshes whose real spacing was larger, so text would have been
  compressed sideways.
- **Evidence:** private record.
- **Fix:**
  - resample columns to the render scale before rendering;
  - check the render aspect against the mesh arc length.
- **Label:** VERIFIED (record).

**5. Picking depth from a global profile peak.**
- **Trap:** a per-strip "band-matched depth" field used the global CT-profile peak, which picked a neighbouring sheet in
  18 of 50 strips.
- **Evidence:** private audit of the strip stats.
- **Fix:** use the local peak around the expected layer, check it per tile, and report the depth error.
- **Label:** MEASURED (private).

**6. Mapping pixels with the wrong orientation.**
- **Trap:** we assumed the ink overlays were flipped into reading orientation; only the panels were. A 3-D seam test
  then reported r = −0.20, where the truth was +0.43, and we reported the wrong number first.
- **Evidence:** private record; the corrected seam tool is [`stripqc/seam.py`](../stripqc/seam.py).
- **Fix:**
  - trace each artifact's code path (who writes it, which flips) before mapping pixels to 3-D;
  - use a discriminative orientation check. Our validity-mask agreement gave 0.80 for all four flips, which proves
    nothing.
- **Label:** VERIFIED (record).

**7. A biased null distribution.**
- **Trap:** non-wrapped column shifts drop pixels, so every shift has a different n, and neighbouring shifts are
  correlated. The null was too wide and gave p = 0.09.
- **Evidence:** private record; `stripqc.seam.circular_null_r` and its test.
- **Fix:** circular shifts over the full sample (equal n), and report the effective number of independent shifts.
  Done correctly: p ≈ 0.01-0.03.
- **Label:** VERIFIED.

**8. A metric never calibrated.**
- **Trap:** a "stroke vs blob energy" index scored the control letters 0.28 and a known-negative strip 0.62. Worse,
  we deleted the script, so the claim could not be audited.
- **Evidence:** none survives, which is exactly the failure.
- **Fix:**
  - calibrate every metric on a known positive AND a known negative before using it;
  - keep failed tools and their outputs.
- **Label:** VERIFIED (record).

**9. Generalising geometry from one example.**
- **Trap:** we wrote "every strip is 2.25 mm, one letter tall". In fact:
  - of the 56 mass-run strips, 40 are 240/260 px renders (about 1.8 mm of valid height) and 16 are 380/400 px renders
    (about 2.9 mm);
  - the control's letter boxes are 1.985-4.882 mm tall (median 2.887 mm; 9 of 18 are taller than 2.9 mm), and their ink
    cores about 1.1-1.8 mm (SUPERSEDED_CLAIMS S7).
- **Evidence:** strip heights from
  [`natural_experiment_PHerc0268.json`](../results/margin_artifact/natural_experiment_PHerc0268.json)
  (`row_profile_mean_alpha`, n_strips per height); box heights from Erwin Nieuwlaar's letter-box file (sha256 in
  [`docs/inputs.sha256`](inputs.sha256)); ink cores from a private measurement.
- **Fix:** measure every instance before generalising.
- **Label:** MEASURED (ink cores: private).

**10. Treating a narrow pass as a certificate.**
- **Trap:** 20-row control strips passed the "sees ink" rule narrowly, at d = +1 on one scroll. We first treated that pass as certifying the 20-row geometry beyond the control.
- **Evidence:** [RESULTS](RESULTS.md) (Z20 recall and CI).
- **Fix:** a passed sensitivity bar sizes what that geometry shows on the control, at that depth and sheet contrast; it
  does not carry over to another scroll, depth or contrast without a control run there.
- **Label:** VERIFIED.

**11. The blank-margin bug.**
- **Trap:** the main finding of this release. Partly blank inference patches create false bands on one scroll and
  roughly halve real ink on another (fig. 1-4).
- **Evidence:** [RESULTS](RESULTS.md) §1-3, [`results/`](../results).
- **Fix:**
  - reflect-fill the blank margin for the ink models only (`stripqc.fill`, `RENDER_FILL=reflect`);
  - before ANY mass run, put a known positive through the IDENTICAL geometry. We did that only after inking 56 strips.
- **Label:** VERIFIED / MEASURED.

**12. Ranking by a metric the artifact dominates.**
- **Trap:** we ranked strips by their fraction of p > 0.55, and edge bands dominated it.
- **Evidence:** [`results/margin_artifact/fill_test_PHerc0268_aggregate.json`](../results/margin_artifact/fill_test_PHerc0268_aggregate.json):
  the strong fraction fell 2.96-623.9× once the margin was filled.
- **Fix:** rank only on metrics shown to be artifact-free (after the fill, face-specific, above the floor measured on a displaced copy).
- **Label:** MEASURED.

**13. Using ink p > 0 as validity.**
- **Trap:** villa ink maps are non-zero over the blank margin (about p = 0.31).
- **Evidence:** METHODS §4; `stripqc.score.load_arm` and `tests/test_margins_patchgrid.py`.
- **Fix:** take validity from the CT (render / ctlayers > 0).
- **Label:** VERIFIED.

**14. Published meshes out of register with their images.**
- **Trap:** our pipeline published the untrimmed source mesh while the render used a trimmed copy, so 12 published
  meshes were one node row off.
- **Evidence:** private fix (registration script, PHerc0268 repository commit `9c80b1f`).
- **Fix:** store exactly the mesh that was rendered, and record the crop offsets.
- **Label:** VERIFIED (record).

**15. Treating winding indices as comparable across independent fits.**
- **Trap:** in adjacent fit units, the same winding number lay 55-236 vox apart (p5-p95), about 3-15 sheets.
- **Evidence:** private audit; `stripqc.seam.coincident_fraction`.
- **Fix:** match surfaces by 3-D geometry (points within about 4 vox), never by index.
- **Label:** MEASURED (private).

**16. Reading seam agreement as proof of ink.**
- **Trap:** the ink-model maps of two independent meshes agreed at the same 3-D points (r 0.43-0.50, p ≈ 0.01-0.03 by direction).
  The agreement persisted under the margin fill but failed face specificity, so it is a CT response, not ink (private record; METHODS §9).
- **Evidence:** `stripqc.seam` docstring; private record.
- **Fix:** agreement validates the pixel-to-3-D mapping and shows a reproducible CT response. Both maps read the same
  CT, so it cannot certify ink; that needs face specificity and a displaced negative control.
- **Label:** INFERENCE.

**17. An uncalibrated blind read.**
- **Trap:** blind readers missed both hidden positive controls: maximum confidence 0.35, and 1 of 6 positive reads
  marked letter-like. Read #1 had no hidden negatives, and one control had been downscaled without adjusting the stated
  glyph size.
- **Evidence:** [`results/blind_read/read1_uncalibrated_controls.json`](../results/blind_read/read1_uncalibrated_controls.json).
- **Fix:** hidden positives AND colour-matched hidden negatives in the SAME format, per-reader AUC, and a colour-only
  baseline before reading anything into the unknowns. Read #2 used same-format positives and negatives and reached
  AUC 0.875-0.900 (fig. 5), but colour alone reaches 0.975 on the same control strips and its negatives were not colour-matched,
  so it shows calibration to colour, not letter recognition
  ([`colour_baseline.json`](../results/blind_read/colour_baseline.json)).
- **Label:** MEASURED.

**18. Evaluating metrics at fixed rows near the strip edges.**
- **Trap:** the margin artifact sits at fixed rows inside the strip edges, so any metric or threshold evaluated there
  inherits it.
- **Evidence:** the band rows of the natural experiment and the band/middle ratios before and after the fill
  ([`results/margin_artifact/`](../results/margin_artifact/), fig. 1-2).
- **Fix:** check the margin geometry (`stripqc.margins`) before computing any metric or threshold near a strip edge.
- **Label:** MEASURED.

**19. A pre-registration that quoted already computed numbers.**
- **Trap:** the declaration of the PHerc0268 margin-fill test (RESULTS §3) was labelled "before any data" but quoted
  exploratory control results that had already been computed.
- **Evidence:** private record; the S14 note in [SUPERSEDED_CLAIMS](SUPERSEDED_CLAIMS.md). DECL-FL-STRIP, the only
  declaration in [`docs/prereg/`](prereg/), quotes no control numbers.
- **Fix:**
  - state exactly which data a "before any data" declaration precedes;
  - label every non-declared analysis as exploratory.
- **Label:** VERIFIED (record).

**20. Reporting before verifying.**
- **Trap:** we retracted four quantitative claims in one day, and later reported a message as delivered when it had
  not been.
- **Evidence:** [SUPERSEDED_CLAIMS](SUPERSEDED_CLAIMS.md).
- **Fix:** verify against the artifact, label every result, and never round a reported range outward or a claim upward (S11).
- **Label:** VERIFIED.

**21. Strips too short for the task.**
- **Trap:**
  - fleet z windows of 2-3 mm gave strips about one letter tall;
  - 13-row strips halve real ink (pre-registered recall 0.39 in the original run);
  - the First Letters bar needs ≥ 10 legible letters in 4 cm².
- **Evidence:** [RESULTS](RESULTS.md).
- **Fix:** stitch one sheet across fit units by geometry (seam ≤ 2 vox, ≥ 1 cm tall) before inking, and fill the
  margins.
- **Label:** MEASURED.

## B. Operations (what cost us days)

**22. Ephemeral storage.**
- **Trap:** container recycles wiped RAM-disk state twice and killed jobs.
- **Fix:** keep state on disk, make every job resumable, and push each result as it is produced.

**23. Missing prerequisites.**
- **Trap:** a daemon failed to start because a log directory was missing.
- **Fix:** create every prerequisite inside the job.

**24. A cache that only grew.**
- **Trap:** a local CT mirror reached 9.4 GB on a 16 GB RAM disk and caused out-of-memory kills.
- **Fix:** cap and trim the mirror (`bi_mirror.py --cap-gb`), delete finished work dirs, and watch RAM.

**25. `pkill -f` matched its own shell.**
- **Fix:** anchor patterns (`pkill -f "^bash /path/to/job.sh"`). `pgrep -fc` counts itself too.

**26. Editing a running bash script corrupts the run.**
- **Fix:** write a new file and rename it over the old one; running instances keep the old inode.

**27. Safety or permission blocks.**
- **Fix:** never work around them; use a safer construct or ask.

**28. Disk nearly full.**
- **Fix:** check `df` before cloning or writing anything large. Background jobs share the disk.

**29. A scorer that crashed on a missing input.**
- **Trap:** a synthetic-data test caught it before the real run. NaN from a near-zero standard deviation also produced
  invalid JSON.
- **Fix:** test every scorer on synthetic data with known answers, and guard against NaN
  (`tests/test_score.py::test_constant_map_gives_none_not_nan`).

**30. Watchers that silently expire.**
- **Fix:** re-arm long-running monitors, and have the job log every terminal state, failures included.

**31. Parallel agent fleets.**
- **Trap:** a fleet of sibling sessions (118 registered 25 Sep-2 Oct and 52 more on 9 Oct; experiment map) burned a large compute and usage budget. Many workers asked for confirmation instead of
  acting.
- **Fix:**
  - prefer ONE detached command per compute job, which pushes its own results;
  - no supervising turns;
  - get the design right before launch.

**32. Evidence with every image.**
- **Trap:** stakeholders rightly asked for every patch to be shown as produced, ink painted on the fibres at a fixed
  scale, with measurable validation for each claim.
- **Fix:** build that into the pipeline (overlay, panel and stats per surface) instead of curating afterwards.

**33. "Sent" is not "delivered".**
- **Trap:** a scheduled-message trigger aimed at an existing session started a NEW session. We reported success from the
  API response alone.
- **Fix:** verify delivery at the destination before reporting it.
