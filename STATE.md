# STATE.md — current state (read this first)

Updated: 2026-10-15 — **PUBLIC RELEASE prepared (Progress Prize, October 2026 cycle).** The judge-facing entry point
is `README.md`. This file keeps the project's working state; everything below the release section is the record as
it stood at the 2026-09-19 pause and is superseded where the release section says so.

## Release, 2026-10-15

**No submission ready for First Letters; no letter has been seen on any eligible scroll; no PROMISING CANDIDATE has
ever been produced on one.**

What the release established (RULES.md, entries of 2026-10-15):
1. **R-REPRO PASS.** The w040 control re-created from public data in a fresh container: Gate A 0.99659 / 0.49633,
   frozen rule 71 valid / 7 flagged / [4, 2, 1] from both code paths, and both prediction maps **byte-identical** to
   the September files. `records/release/repro_2026-10-15/`. The committed `scripts/reproduce_control.sh` then ran end
   to end from an empty directory: both prediction maps byte-identical, the same Gate A, R-CTRL55 and reader results,
   and every JSON file identical to the resume-mode run except for file paths (R-REPRO addendum,
   `records/release/e2e_2026-10-15/`).
2. **w040 is a training-set sheet** (villa's training config names it; the model card says "plus 5 native 9.362 µm
   segments from PHerc. 0139"). Every statement below that calls it "unmemorised"
   or concludes that "the corpus negatives are real negatives" is superseded (`docs/SUPERSEDED_CLAIMS.md`, item 1).
3. **R-HELDOUT: TRANSFERS / PASS.** On three labelled segments of PHerc0841 (outside the training set) pixel AUC is
   0.8393 forward / 0.5486 reverse, but the frozen unit screen flags 1 of 60 units (1 of 15 text-bearing, 0 of the 7
   most-inked); the reader calls them NOT ESTABLISHED, NOT ESTABLISHED, BLANK. The eligible
   negatives (1/113, 0/190) are not significantly below that rate (exploratory p = 0.575, 0.24; against the declared
   text-unit rate 1/15, p = 0.221, 0.0732): **they are not evidence of absent ink** (INFERENCE).
   `records/release/heldout_2026-10-15/`.
4. The published VC3D `:edge` image is still the 2026-05-13 build and rejects `--flip-normals`
   (`records/release/edge_image_check_2026-10-15.md`).
5. Fixed at release: `disk_guard.sh` keep-list (never matched), portable paths, `imagecodecs` pin; a recording error
   in the R-HELDOUT entry itself was corrected by an appended line.

**What would move the project from here, in order of evidence** (none of it run; each needs its own declared bars):
a unit screen re-calibrated on HELD-OUT known text (smaller units or a lower margin bar, chosen on PHerc0841 and
validated on another unseen labelled scroll such as PHerc0009B or PHerc0500P2) before any eligible scroll is re-read;
then the 2.4 µm route on PHerc1203 (R-2UM-SCOPE).

**Operations:** the four hourly Routines remain DISABLED; nothing runs. The September data root does not exist in the
release container; the release's own inputs were re-downloaded and are checksummed in `records/release/`.

---

# Record as of the 2026-09-19 pause (superseded where the release section above says so)

Updated: 2026-09-19 17:33 UTC — **PAUSED at the owner's request until Wednesday (model usage).**

## Claim status
**No submission ready.** (2026-09-18) No PROMISING CANDIDATE exists. No letter has been seen in any eligible scroll by this or any previous session.

Corpus so far: **119 reads on 5 eligible volumes** (PHerc0826, PHerc0358, PHerc1203, PHerc1447, PHerc0800) - 80 VOID by R-CREST, 24 BLANK, 15 NOT ESTABLISHED, **0 PROMISING CANDIDATE**; 135.1 cm² of surface actually read (VOID charts are vetoed before the model runs). Across every read on record exactly **three** 0.5 cm² units have ever been flagged, all on PHerc0826, none adjacent to another; rule 5.5 needs three adjacent flagged units.

**Why the corpus reads blank, established 2026-09-18 and not a guess.** The forward level of our reads is TEXT-like (median 0.394 plain, against the w028 control's text 0.4328 and blank 0.2832) while the forward-minus-reverse margin is BLANK-like (median +0.002, against text +0.1492). The stored Gate B numbers say which of the two possible causes it is: on OUR OWN render of the w040 mesh the plain call gives mean 0.7561 on labelled ink and 0.2880 on the same pixels reversed - margin **+0.4681** - against -0.0039 on blank. The chain trace -> our render -> 5.1 -> rule 5.5 preserves the asymmetry it rests on, so the low margins are a physical statement about those surfaces, not a pipeline artefact, and the frozen +0.08 bar is about a sixth of a fully inked pixel's margin. The limiting factor is AREA and BREADTH, not the reader (RULES, "The corpus margin is not a pipeline artefact").

**Where the corpus actually is, measured 2026-09-18 (RULES R-RADIAL).** The reads are overwhelmingly OUTER WRAPS. Inner half of the radius: 62 of 70 reads VOID (89 %), 35.8 cm² ever read. Outer half: 20 of 51 VOID, 99.3 cm². On PHerc0826, where the crest test has real dynamic range, 15 of 16 inner traces are VOID and 17 of 18 outer traces readable. The seeds run outer -> inner and the density gate prefers sparse (edge) neighbourhoods, so coverage was pushed outward - and outer wraps are the most damaged and least likely to carry legible text. R-INTERIOR then showed the interior is NOT unresolved (the CT shows a wrap every 449 µm and the surface prediction tracks it), so the failure is the tracer keeping to one sheet across a 5 cm² patch. **The limiting factor is interior geometry, not area and not breadth**, and R-SMALL is the test of the fix.

**Two gates were found to be discarding canvas, and both are now handled by measurement rather than by taste.**
1. The QC CT-mask zero-fraction bar sits inside a dense continuum (histogram over 151 patches, 0.1 bins: 67, 1, 13, 18, 14 | 18, 5, 8, 5, 2), not a gap, and it gates render COST only. A second arm was added (RULES, declared before the run): a patch also proceeds when in-mask area `(1 - zero_frac) * area_cm2 >= 1.5 cm²`. Strict widening, 24 surfaces unblocked, arm recorded on every ledger line.
2. R-CREST rejects nearly everything the TEAM publishes: PHerc1203 21 of 22 at ratios 1.03-1.20, PHerc1447 28 of 32 at 1.00-1.02, eleven of those from the team's own published renders. The per-slice profiles show why - PHerc1203's team surfaces carry a real, centred crest of only 4-6 % (102 -> 107 -> 101) and PHerc1447's are flat at 90.4 across all 28 slices, while a PHerc0826 trace runs 37 -> 106 -> 37. Where wraps touch there is no air gap to dip into, so a correct reading surface has no crest and the test has no dynamic range. **R-CREST-POWER** (RULES, population and decision rule fixed before any data) is reading the 12 largest-area VOID surfaces with the veto off, 160.2 cm², under their own ledger keys.

## PAUSED 2026-09-19 17:33 UTC — read this first on resume

**Paused at the owner's request until Wednesday (model usage).** No submission ready; no PROMISING CANDIDATE has
ever been produced.

**What was stopped, and what was not.** All four hourly supervisor Routines are **DISABLED, not deleted**
(`trig_01B98K6Tux8hbFkpvM1dGNm6` :05, `trig_01Dcw6a55SSd5nGZMFdBYh96` :20, `trig_014TnoTGq7BWi6Lf5a1w7PVX` :35,
`trig_01S5jJ13wvnRmkuBu59wo3Mo` :50) — re-enable them to resume automatic operation. The session monitor is
stopped. The container's own jobs were left alone and die with the container; **every one is idempotent and resumes
from disk**.

**THE ONE THING TO DO ON RESUME:** `bash scripts/supervisor.sh`. It restarts dockerd, the read loops and the
R-CREST-POWER queue, and its `stale_proxy` check handles the proxy variables that go stale across a restart.

**Where R-CREST-POWER phase 1 stopped: 11 of 12 complete, member 12 mid-inference.**
- Complete: **150.67 cm2 on-sheet, 190 valid units, 0 flagged** in either depth order, tripwire never fired.
  Margins median +0.0020, range -0.0485 to +0.0597; nothing within three quarters of the +0.08 bar.
- Member 12 is `PHerc1447|team_z_dbg_gen_00289`. Its read directory will hold a partial forward map; the queue redoes
  it from scratch and `sweep_partial_reads.py` removes the leftover once it is 6 h old. **Nothing to clean by hand.**
- **The phase-1 VERDICT is not yet called** and must not be called on 11 of 12. The decision rule fixed on
  2026-09-18 is unchanged.

**Everything else is closed.** R-SMALL-2 FAILED (2 readable of 40, 5.0 per cent). G-GP parts 4-6 complete and the
consensus threshold knob is closed. **G-OWN PASSED** — our tracer finds ink on known text at 142.7 per cent of the
team mesh's signal on the same papyrus, so the pipeline is sound and the corpus negatives are real negatives.
R-DEFICIT, R-BLANK (+ part 2), R-ORIENT, R-SHAPE, R-COVER9 (corrected), R-YIELD and R-EYE are all recorded.

**The binding constraint as it stands:** contiguous, fully-on-sheet valid units on canvas that carries ink. The
per-surface ceiling is 9 valid units unless the crest veto is lifted, which is what R-CREST-POWER is testing. The
only untried lever is the 2.4 um rescan of **PHerc1203** (R-2UM-SCOPE), which would be declared with its own bars
before any of it runs.

## What 2026-09-19 established, and it renames the binding constraint (RULES R-DEFICIT, R-BLANK, R-ORIENT, R-SHAPE, R-COVER9, G-OWN)

**Still no submission ready. No PROMISING CANDIDATE. No letter seen in any eligible scroll.**

1. **The corpus reads like control papyrus with NO ink on it, and nothing like control papyrus with ink.**
   Orientation-free (|margin|, since our traces' sheet orientation is unknown): corpus **0.0122**, control
   labelled-blank **0.0134**, control labelled-inked **0.0438**. Unit flag rate 1 of 113 against the control's
   7 of 71, Fisher exact one-sided **p = 0.0058**.
2. **No scanner domain gap is available as an excuse.** The w040 control is PHerc0139 at
   `9.362 um / 1.2 m / 113 keV` - the same scan configuration as PHerc0826, PHerc0358 and PHerc1203. Renderer
   byte-verified (G-B), crest centring matched (weighted mean slice 13.19 against the control's 12).
3. **Orientation was a real confound and it was tested, not waved away.** The signed margin distribution is
   symmetric (50.8 % positive, 15 of 31 surfaces negative) - but the depth-swap tripwire has never fired in 52
   reads and nothing reaches the bar backwards, so the deficit survives orientation correction unchanged.
4. **THE BINDING CONSTRAINT IS CONTIGUOUS FULLY-ON-SHEET CANVAS PER SURFACE, not total area.** From the actual
   recorded per-surface unit layouts, our whole corpus expects **0.079 candidates even if every unit of it were
   as inked as the known-text control** (a lower bound; ~0.5 after the control's own clustering excess). Ten of
   31 surfaces cannot hold a 4-connected triple at any flag rate. Median 4 valid units per surface, best 9.
   **A qualifying candidate is roughly a one-in-five event per 35 cm2 of clean contiguous KNOWN-TEXT canvas** -
   that is the scale of the gap, and no number of small surfaces closes it.
5. **Our consensus surfaces are ragged, filling barely half their own bounding grid** (0.476, 0.495) where the
   control fills 0.862 and a small single trace 0.905. Two explanations were tested and both failed (a level-4
   CT proxy; node spacing), and that is how an earlier wrong reading of mine - "half off the papyrus" - was
   caught and withdrawn.
6. **G-OWN, running now, closes the one gap in the validation chain.** Gate A validated the model on known text,
   Gate B the renderer, Gate C the calibration, R-CTRL55 the frozen rule - **every component except the tracer
   this project built on top of.** G-OWN runs our own tracer on PHerc0139, seeded on the w040 mesh cell whose
   0.5 cm2 neighbourhood carries 19.65 % labelled ink, bars fixed before launch: PASS |margin| >= +0.0128,
   COLLAPSE <= +0.0042. G-GP part 6 (density, not area) is queued behind it.

**Three of my own errors were caught and recorded today**: R-DEFICIT's cluster arithmetic (wrong by 20x),
R-COVER9's reading (withdrawn), and a `rblank2` distance bound that was not the bound its declaration promised.
A fourth was a defect, not an error of reasoning: **R-SMALL-2's traces had a tracer and no reader**, so its
readable-fraction bar could never have been evaluated however long it ran; both `_rs2` read loops are now up.

## Environment (measured, not assumed)
| item | master prompt assumes | this container has |
|---|---|---|
| GPU | one or more NVIDIA | none (`nvidia-smi` absent; torch.cuda False) |
| CPU | many cores | 4 cores |
| RAM | >= 32 GB for the 2.4 µm runner | 15 GB, no swap |
| disk | large | ~30 GB writable |
| Docker | available | no daemon at start; `dockerd` started manually (works; `--network host` required; proxy env + CA bundle must be passed into containers) |
| network | direct | all HTTPS via a policy proxy; S3 open data, Hugging Face, PyPI, torch index reachable; github.com blocked for raw HTTPS but `git clone` works |
| Python | >= 3.14 | 3.14.0rc2 via uv; torch 2.14.0+cpu |

Consequences: 9 µm inference runs on CPU (throughput to be measured, RULES T-CPU); the 2.4 µm route (5.7 GB stacks, 32 GB RAM runner, ResNet-152 3D on CPU) is very likely infeasible here and will be stated as such with numbers; tracers run in the VC3D container on 4 cores.

## Done (2026-09-16/17)
- Environment: no GPU, 4 cores, 15 GB RAM. Docker daemon started by hand; the container is torn down after ~25 min idle and a worker restart moves the egress proxy: `scripts/supervisor.sh` (run by four Routines 15 min apart) resumes every loop idempotently and restarts loops holding a stale `HTTPS_PROXY`.
- VC3D tools rebuilt from villa 5ab585f (published image stale). Controls, models, labels fetched. 89+ tests pass under `scripts/tests/`.
- **Gate A PASS** (full w040 plain fwd 0.99659 / rev 0.49633), **Gate B PASS** (render vs team stack Pearson 0.999999; through the model 0.99680 plain / 0.99024 TTA), **Gate C PASS** (w028 pooled plain fwd 0.99982 / rev 0.53058), **J-w028 plain judge** 0.7842 fwd / 0.4902 rev (reference 0.784 / 0.49), **R-5.5 self-test PASS**, **P-DRY PASS**.
- Rule 5.5 implementation notes recorded (mask-only grid origin, conservative combination of both tilings); R-CREST (render crest ratio ≥ 1.20) declared and in force.
- Coverage of PHerc0826 (rank 1 in our survey): 27 charts = 16 VOID by R-CREST, 6 BLANK, 5 NOT ESTABLISHED, **0 PROMISING CANDIDATE**; 34.1 cm² on-sheet read (15.5 cm² in valid 0.5 cm² units). The 40 middle/inner seeds are skipped (every trace there cross-cut the sheets); 6 outer seeds remain, then PHerc0358.
- CONTROL-2UM scaled to CPU (RULES B-2UM/T-2UM): the villa 2 µm runner works in a Python 3.13 venv; smoke calibration on w028 (768², forward) Pearson 0.934 / AUC 0.979 against the team map. The first rescan trace (L2 prediction, inner seed) **cross-cuts the sheets** (R-CREST-CT crest 1.043) and is not rendered; R-CREST-CT (CT crest pre-check, `scripts/ct_at_points.py`) declared and calibrated on 9 µm traces (1.35 / 1.37 PASS vs 1.03 VOID).
- Public record: villa issues #1739 (rescan admissibility unanswered), #1813 (2 µm window centring), #1751 (prize page diff); HF org listing; 2 µm training set not stated publicly.

## Where this stands (2026-09-18 19:05 UTC) — the blocker is now measured, and it is patch density

**141 reads, 0 PROMISING CANDIDATE.** Everything below is in RULES.md with its bar written before the run.

**What has been ruled out as the cause.**
- *The reader.* Gate B ink margin +0.4681 on our own render of a known-text mesh (AUC 0.99680); G-B-43 +0.4581 on an
  independent checkpoint. R-FLIP: 0 tripwire firings over the whole corpus. R-ROWS: the ink map carries no 2–4 mm row
  periodicity even where the text is known and detected at AUC 0.997, so the frozen levels cannot be rescued by row
  structure.
- *Six hand-rolled geometry proxies*, all failed, none retuned: R-NORMAL, R-NORMMAG, R-INTERIOR, R-PHASE, R-WRAP,
  R-ROWS. Three failed for one physical reason: a scroll sheet is a spiral, so the surface that genuinely holds to it
  is the one that MOVES, and no scalar spread statistic separates that from a surface that cuts across.
- *The growth budget.* **R-SMALL FAILED** at 20.0 % readable against its declared 30 % bar (baseline 5.6 %), and G-GP
  part 1 found no difference in mesh roughness between 40 and 60 generations. Two independent refutations of the same
  idea. R-SMALL nonetheless produced the only interior surface matching the known-text reference (fibre weave, on-sheet
  CT std 45.4 vs 43.1) and one of the corpus's two flagged units; both are ledgered and neither rescues the bar.
- *Flattening.* `vc_flatten` is INEFFECTIVE (G-GP part 2): at a matched physical baseline it makes 3D sag worse
  (64.6 → 84.6 µm) while improving UV anisotropy. The literal declared test would have passed it on a node-density
  artefact; the stricter matched-baseline test stands.

**What the cause actually is, measured today.**
1. **R-CROSS** (the team's own `vc_tifxyz_selfcross`, which we had never built): our median trace contains **1246
   transverse self-intersections, 262.61 per cm²** — places where the surface passes through itself, which a papyrus
   sheet cannot do. The w040 known-text control is at **1.42/cm²**; the team's median published segment on the same
   scrolls is at **0.00**. The declared gate was NOT admitted (1.87x against a 2.0x bar) and gates nothing; the
   descriptive number is the finding.
2. **G-GP part 3**: the team's published segments carry
   `vc_grow_seg_from_segments_params {consensus_default_th: 6, ...}` — they are **consensus surfaces grown from a
   directory of patches**, not single greedy traces. A six-fold consensus cannot fold through itself. We have run only
   stage 1, for 141 reads.
3. **The precondition, and the real blocker**: stage 2 needs six patches agreeing on the same sheet. Measured
   (`scripts/patch_agreement.py`, 24-voxel cells, an upper bound): PHerc0826's 66 patches reach six-fold agreement over
   **1.15 cm²** and never exceed 7 anywhere; PHerc0358's 43 reach **0.09 cm²**. Against a 4 cm² prize area. The
   arithmetic is simple: seeds are placed 320 voxels apart and the wrap spacing is 48 voxels, so two seeds can be six
   wraps apart. **We have been spreading traces out when we needed to stack them up.**

**The question that was settled on the night of 2026-09-19, and what it costs us.**
The reader had never been run end to end against known text on a sheet the model did not memorise. It has now been.
**R-CTRL55**: the frozen rule 5.5, unchanged, on the w040 known-text control's full 40.60 cm² canvas flags **7 of 71
valid units**, cluster sizes **[4, 2, 1]** — a four-unit **PROMISING CANDIDATE** — and every flagged unit the labeller
examined is **36-70 % ink** where examined; not one is demonstrably blank. Two independent code paths agree on all four
numbers. **The instrument works, so every BLANK and NOT ESTABLISHED on record is a real negative.**
It also prices the problem: **one candidate per 40.60 cm² of text-bearing sheet**, against the **~23 cm²** of
geometrically sound interior canvas the project has ever read. **Canvas area on sound, contiguous geometry is the
binding constraint** — not the reader, not the render path, not the depth test, not geometry quality.
Two things were disproved on the way, both recorded: **R-SYM** (control anchor r = −0.0088; 0 of 9 corpus reads are
depth-symmetric, so the reverse map is *not* a copy of the forward map) and **R-SENS** arm 1's area-mixture floor of
26.1 % ink coverage, which the halo effect voids as a bound — the control fires at a third of it.
Two of my own errors were caught and corrected in RULES: a sensitivity curve drawn from whole-unit ink fractions on a
mask whose median per-unit coverage is zero (withdrawn), and a `unit_origin` tuple passed where `evaluate()` wanted the
string `"auto"`, which silently tiled from (0, 0) while the log claimed otherwise (fixed; caught only by cross-checking
against `read_chart.py` on the same maps).

**The night of 2026-09-19, in order, with two of my own results withdrawn.**
1. The 5.162 cm² consensus surface — 26 sources, zero self-intersections, p90 sag 5.11 µm — read **NOT ESTABLISHED**,
   0 flagged of 2 valid units, at a forward level *above* the known-TEXT units that calibrated rule 5.5 and a twentieth
   of their margin. That forced the rest.
2. **R-SYM**: the reverse map is not a copy of the forward map (control anchor r = −0.0088; 0 of 9 corpus reads
   depth-symmetric). So a mean *could* in principle cancel a localised signal.
3. **R-SENS**: its declared empirical arm is empty — no 0.5 cm² window on either control is 90 % supervised — and its
   analytic floor of 26.1 % ink per unit is void as a bound, because a convolutional reader responds in a halo.
4. **R-CTRL55**, the decisive one: the frozen rule 5.5, unchanged, on the w040 known-text control's full 40.60 cm²
   canvas flags **7 of 71 valid units, clusters [4, 2, 1]** — a four-unit **PROMISING CANDIDATE** — and every flagged
   unit the labeller examined is **36-70 % ink**. **The chain fires end to end on real Herculaneum text on a sheet the
   model did not memorise, so every corpus negative on record is a real negative.**
5. **R-POP**: the margin is monotone in ink content on the control (+0.0131 → +0.0220 → +0.0398 → +0.0989 by how much
   text is in the unit) and our surfaces sit at **+0.0014**. IQR ratio 0.967 rules out a compressed spread.
6. **R-DEPTH was ADMITTED and is WITHDRAWN.** Its HIGH reverse map was 25 % written — one quadrant — and the unwritten
   zeros were scored as model output. An audit of all 55 map pairs on disk finds exactly that one suspect and nothing
   else; the guard now lives in `read_chart.py` and in `rdepth.sh`, with no flag to switch it off. HIGH is re-running.
7. Also withdrawn: a sensitivity curve drawn from whole-unit ink fractions on a mask whose median per-unit coverage is
   zero. Also fixed: a `unit_origin` tuple passed where `evaluate()` wanted `"auto"`, and protocol 9's step 6 looking
   for candidates in `patches/<scroll>` — which would have failed on any candidate the campaign can actually produce.

**What this leaves as the binding constraint, priced.** One PROMISING CANDIDATE per **40.60 cm²** of text-bearing
sheet, against the **~23 cm²** of geometrically sound interior canvas the project has ever read. Not the reader, not
the render path, not the depth test, not geometry quality — **canvas area**. And it matters *where*: R-RADIAL shows
every readable surface on record sits at r/R 0.49-0.96 (the abraded outer band) while everything at r/R < 0.57 went
VOID. The concentrated campaign has moved our canvas to **r/R 0.606**, the only method that has gone inward.
**Every published team segment across all 23 eligible volumes is now held** — there is no free canvas left.

**Two declared experiments resolved, and a third declared as its pre-written successor.**
- **R-SMALL FAILS.** Nineteen 40-generation interior traces, all resolved: 11 VOID, 4 QC FAIL, 1 QC UNREADABLE,
  2 BLANK, 1 NOT ESTABLISHED. Readable **3 of 19 = 15.8 %** (or 3 of the 14 reaching a read = 21.4 %) against a bar of
  **≥ 30 %** and a 60-generation baseline of 5.6 %. The gain is real — 2.8-fold — and the bar, set before any trace
  precisely so a gain of that size would not carry it, is not moved. **The budget goes back to 60, as declared.**
- **R-CREST is not hiding recoverable canvas.** Of 469.7 cm² vetoed by the crest check, **463.6 cm² fails on the
  ratio** (values clustered at 1.00-1.11 — flat profiles, where a shifted window changes nothing) and only 6.0 cm²
  has a real peak outside the central band, both of those at slice 0, the render's edge.
- **R-SMALL-2 declared**, exactly as it was pre-written on 2026-09-18 before R-SMALL's numbers existed: interior seeds
  regenerated at a density cap of **0.30** instead of 0.20, the **newly admitted band only**, the same 40-generation
  budget, the same bar form (≥ 30 % readable over ≥ 15 traces against 5.6 %) judged on the stricter all-traces
  denominator. If it fails, the pre-written conclusion is recorded as the finding: interior geometry is not
  recoverable on this box with the published tooling and priors.

**Three more defects found and fixed tonight, none of which touched a recorded result.**
1. Seven scripts passed seven different `HERCULES_INFER_LOCK` paths, so up to eight inferences could share four cores.
   Both reverse-pass truncations happened under that load. A **global cap of 2** now applies to every caller, and
   `infer_slot.sh` covers the scripts that call inference directly; dataloader workers drop 3 → 2.
2. `rbest2.sh` passed a patches **directory** (`PHerc0826_small`) as `--scroll` and crashed on every member of its
   declared population. Fixed there and pre-emptively in `rdepth_part2.sh`.
3. The seed cache keyed files by chunk name alone, so regenerating two scrolls' seeds through one cache gave the
   second scroll **the first one's 90 seeds**, with the correct URL in the header. Caught because two scrolls cannot
   give identical numbers; the historical seed files were then checked and have **zero overlap**, so no trace on
   record was seeded from the wrong volume. Cache entries are now namespaced by source URL.

**What is running now.**
1. **G-GP part 5**: 33 of 60 second-generation traces. Six-fold agreement 5.62 cm² at 30 traces. **Bar G-GP-5:
   ≥ 10 cm² on-sheet at ≤ 1.42 crossings/cm² and p90 sag ≤ 9.93 µm** — the w040 control's own rates. The consensus
   build is armed to fire automatically when the queue finishes, and **G-GP part 5b** builds the same sources at
   threshold 4 (9.26 cm² of agreement against 5.62) and reads it **only if** it meets those same geometry bars; the
   gate is automated, takes the worst surface rather than a pooled average, and reproduces part 4's numbers exactly.
2. **R-DEPTH is COMPLETE and FAILED; depth offset is CLOSED.** On sound maps M(HIGH) is 0.39948 against the centre's
   0.46808 — the centre window is best and the response is broad (retained ratio 0.6619), so the reads at offset 0
   lose nothing and **part 2 is not owed and will not be run**. The earlier ADMITTED verdict came from a
   quarter-written reverse map whose unwritten zeros read M(HIGH) as 0.60594; **the artefact had inverted the
   verdict.** R-CTRL55-W agrees on the same maps: HIGH-WORSE, screening stays at offset 0.
3. **R-SMALL-2** seeds regenerating with the fixed seeder; it starts when part 5 releases a trace slot.
4. R-CREST-POWER phase 1 and CONTROL-2UM: paused by marker, resumable, declarations untouched.

**Ready before it is needed:** `protocol9.sh` has a `P9_DRY=1` rehearsal (15 inputs checked, every command printed),
and `review_sheets/reference/CONTROL_w040_rule55_PROMISING_CANDIDATE_cluster.png` is the visual standard a real
candidate has to match — the control's own four-unit cluster, forward beside reverse, unenhanced.

**Throughput fix on record:** the disk guard was pruning normal grids under a live tracer, a ~4x tax on interior traces
(269/333 s before, median 1052 s over the 14 after). Fixed with the check on the fix declared in advance.


## Where every declared bar stands (snapshot, container clock 2026-09-19 04:10 UTC)

This table is DERIVED from RULES.md and governs nothing; where it and the prose in RULES disagree, RULES is right.
It exists because the record is now 2000 lines and one bar (R-DEPTH) was admitted, withdrawn and then failed.

| bar | status | the number that decided it |
|---|---|---|
| **Gate A** | PASSED | w040 native stack, AUC 0.99659 forward / 0.49633 reverse |
| **Gate B** | PASSED | our own render of the w040 crop, +0.4681 ink margin |
| **Gate C + w028 judge** | PASSED | reference numbers matched; its label AUC measures memorisation |
| **G-B-43** | PASSED | seed43 admitted as a confirmatory FILTER, +0.4581 |
| **P-DRY** | PASSED in kind | 2 declared failures; its package predates the CT-crop fix and now also fails for that, which is the verifier working |
| **R-5.5 self-test** | PASSED | w028: text 5/5 flagged, blank 0/8 |
| **R-CTRL55** | **CTRL55-STRONG** | 7 flagged of 71 valid over 40.60 cm²; clusters [4, 2, 1]; a PROMISING CANDIDATE on known text |
| **R-CTRL55-W** | **HIGH-WORSE** | CENTRE flags 1 unit, HIGH flags 0; screening stays at offset 0 |
| **R-SYM** | **DS-SPLIT** (usable) | control anchor r = −0.0088; corpus 0.115–0.578; 0 of 9 depth-symmetric |
| **R-POP** | **POP-SHIFT −0.0210**, POP-NARROW ruled out | IQR ratio 0.967; the control's own margin is monotone in ink content |
| **R-SENS** | arm 2 EMPTY, arm 1 void as a bound | no 0.5 cm² window on either control is 90 % supervised; the halo breaks the mixture model |
| **R-DEPTH** | **FAILED — depth offset CLOSED** | M(HIGH) 0.39948 < M(CENTRE) 0.46808; gain −0.06860, retained 0.6619. Part 2 not owed |
| **R-SMALL** | **FAILED** | 3 readable of 19 = 15.8 % against a 30 % bar; budget back to 60 |
| **R-SMALL-2** | DECLARED, armed | 80 interior seeds in the newly admitted density band; bar ≥ 30 % over ≥ 15 traces |
| **R-CROSS** | NOT ADMITTED as a gate | our median trace 262.61 sites/cm² against the control's 1.42; used as a measurement |
| **R-CREST** | STANDS, and discards nothing readable | 463.6 cm² of 469.7 fails on the RATIO (1.00–1.11), not on crest position |
| **R-CREST-POWER** | PAUSED by marker | declaration and populations untouched |
| **R-BEST / R-BEST-2** | running | populations declared; all reads so far clean negatives |
| **G-GP parts 1–3** | recorded | the team's segments are consensus surfaces; ours were stage 1 only |
| **G-GP part 4** | milestones 1 and 2 MET | 5.162 cm², 0 self-intersections, p90 sag 5.11 µm — read NOT ESTABLISHED |
| **G-GP part 5** | running | 41 of 60 traces; bar ≥ 10 cm² at the control's own crossing rate and sag |
| **G-GP part 5b** | DECLARED, armed | threshold 4 read only if it meets the same geometry bars |
| **R-NORMAL, R-NORMMAG, R-INTERIOR, R-PHASE, R-WRAP, R-ROWS** | FAILED their own bars | recorded as unusable indicators; they gate nothing |
| **CONTROL-2UM** | BLOCKED | needs a sheet-following PHerc0846A rescan trace that does not exist |

## Blockers
- No GPU: full-canvas gates may take many hours on 4 cores; partial (crop) results are labelled as such and never substitute for the full bars.
- 2.4 µm runner memory: 15 GB RAM vs the documented >= 32 GB requirement (works at 1 cm² with tile 256, ~2.3 GB RSS).
- Rescan admissibility (issue #1739) and the 2 µm training set are unanswered publicly; any 2.4 µm result on PHerc0846A is labelled accordingly.
