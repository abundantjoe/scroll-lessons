# Progress Prize submission (October 2026)

**Title:** Dominion, result 1: blank render margins silently corrupt ink inference on thin strips. Measured on a
positive control, partly mitigated by a margin fill, and packaged as a check (stripqc)

**Category:** tools and methods for ink detection (validation and quality control)

## Google Form answers

Form: the October 2026 Progress Prizes form, linked from https://scrollprize.org/prizes. It needs a signed-in Google
account, so the entrant submits it by hand. Deadline: 31 October 2026, 23:59 Pacific.

| field | answer |
|---|---|
| Email | the entrant's |
| Full name | the entrant's |
| Discord username | the entrant's (optional) |
| Team description | Individual: one owner directing AI research agents (Claude Code), which ran the experiments and wrote the code and text; the release's code, tests and committed results are in the linked repository; the working history stays private. |
| URL | the public release repository (see the note below) |
| What is your contribution? | the text below, pasted as-is |
| Terms and Conditions | Yes, I agree |

**Note on the URL:** submit the public release repository, which holds only this release as one commit; the working
repository stays private.

**What is your contribution?** (generated from the committed JSON by `scripts/write_tables.py`)

<!-- BEGIN:form -->
Dominion is the record of 175 experiments, run on 116 experiment branches, a research log and related repositories, on finding ink inside carbonized Herculaneum scrolls. This release maps them with their outcomes (103 in full, 72 only counted for confidentiality) and packages the finding that survived validation: blank render margins silently corrupt villa ink inference on thin strips. We measure the damage on a public positive control, give a partial fix, and ship a kit (stripqc) to check your own runs.

(1) Scroll data: PHerc0343 (volume 20250521140437, 8.64 µm, 116 keV) as the positive control, with Erwin Nieuwlaar's public First Letters segment and letter boxes (MIT); PHerc0268 (volume 20251110183117, 8.64 µm, 116 keV), aggregate numbers only. Models: the organizers' ink_9um (seeds 42 and 43) and Erwin Nieuwlaar's dense_native. Renderer and inference: ScrollPrize/villa 41701aa. Dataset: Vesuvius Challenge - CT Scans of Herculaneum Papyri (Angelotti et al.), CC BY-NC 4.0.

(2) vc_render_tifxyz renders of thin surface strips (fit-derived strips, ring patches, tile crops) carry all-zero rows at their edges, because border mesh nodes have no normal. villa's ink inference skips patches that are entirely empty but normalises partly blank ones with their zeros, and that code is unchanged on villa main as of 14 Oct 2026. The defect is silent: villa raises no warning, and nothing in its output marks the affected edge rows.

(3) Results on real data: on the positive control (13 known letters, d = +1), 13-row strips cut as mass runs cut them lowered the share of strong-ink pixels in the letter boxes from 15.38 % to 7.46 % (recall 0.386 [0.257, 0.493], letter-bootstrap 95 % CI); a pre-registered test failed them. Reflect-filling the margin for the ink models (stripqc.fill, exploratory) raised it to 14.43 % (box AUC 0.703, full context 0.709) but recovered only 0.646 [0.499, 0.768] of the full-context strong pixels and about doubled the strong pixels outside the letters, so it is a partial fix. On PHerc0268 the same margins painted false ink bands in about 2/3 of the strips of a 56-strip mass run; inside the strips the ink proxy at the same rows was 0.163 vs 0.049 by blank-margin class, and the fill lowered strong ink 2.96-623.9× and removed the bands in 5 of 7 strips. Why the sign differs between the two scrolls is not explained. A blind-read protocol with hidden positives and negatives reached reader AUC 0.875-0.900, but colour alone reaches 0.975, so it shows calibration to colour, not letter recognition. No letters are claimed.

(4) Evidence: a pip-installable package with 27 synthetic tests; scripts/reproduce.sh reruns the control's d = +1 arms (all but the exploratory X13) from public data in one command (1.6 GB of downloads, 71 min on 4 CPU cores); compared with the committed original run (RESULTS §2), 22 of 22 of its values match at the stored precision and all 5 thresholded pre-registered decisions are identical; the sha256 of all 29 maps; a letter-box shift check; every number in the README's result tables generated from committed JSON. Also: the experiment map (verdict and key numbers of every published experiment), 33 lessons, and the retracted claims of the work behind them. Code MIT; results CC BY-NC 4.0. Run by AI research agents (Claude) directed by one owner; the d = +1 positive-control numbers (all arms but X13) are reproduced by the scripts in this repository, the X13, d = -2 and strip-middle values come from the committed original run, and the other numbers (PHerc0268 aggregates, blind-read scores, experiment map) are committed as JSON from the private working record.
<!-- END:form -->

## Summary (≤ 200 words)

<!-- BEGIN:summary -->
Ink models in villa normalise each 128 px patch over all of its voxels, and thin strips rendered by vc_render_tifxyz carry all-zero rows at their edges, so every edge patch is normalised with zeros. On a public positive control (PHerc0343, Erwin Nieuwlaar's First Letters segment, 13 letters), 13-row strips cut as mass runs cut them lowered the share of strong-ink pixels in the letter boxes from 15.38 % to 7.46 % (recall 0.386 [0.257, 0.493]); a pre-registered test failed them. Reflect-filling the margin for the ink models (exploratory) raised it to 14.43 %, but recovered only 0.646 [0.499, 0.768] of the full-context strong pixels and doubled those outside the letters (1.35 % vs 0.67 %). On the unread PHerc0268 the blank margins instead painted false bands (ink proxy 0.163 vs 0.049 by margin class at the same rows); the fill lowered strong ink 2.96-623.9× and removed the bands in 5 of 7 strips. Why the sign differs is open. We release the fill, a diagnostic kit, a positive-control-first protocol, a hidden-control blind-read protocol (reader AUC 0.875-0.900, colour alone reaches 0.975), 33 lessons and a rerun with fresh data. No letters are claimed.
<!-- END:summary -->

## What is new

- **A defect, measured.** Thin surface strips rendered by `vc_render_tifxyz` carry all-zero rows at their edges,
  because border mesh nodes have no normal. villa's ink inference skips patches that are entirely empty, but it
  normalises partly blank patches with their zeros included. We show what this does to known letters, with
  letter-bootstrap CIs, pre-registered decision rules, and a displaced negative control. The ink inference is unchanged
  on villa `main` as of 14 Oct 2026 (`5432721`), so any render that still carries blank margins is exposed; the
  renderer has changed since `41701aa`, and we have not rechecked its blank margin there.
- **A one-call partial fix** (`stripqc.fill`): reflect-fill the blank margin for the ink models only, and score on
  the original render. Tested on the positive control (exploratory, not pre-registered), where it restores the in-box
  strong fraction but misses the stricter recall bar and about doubles strong pixels outside the letters, and on 7 of the
  real strips where the artifact was found.
- **A positive-control-first protocol.** Cut a public segment with known letters into exactly the geometry of your
  mass run before trusting any map from that geometry.
- **A blind-read protocol with hidden controls.** Readers see hidden positives and hidden negatives in the same format
  as the unknowns. Our first read, without negatives, missed both hidden positives. Our second reached reader AUC
  0.875-0.900, but colour alone reaches 0.975 on the same control strips: the protocol and its colour baseline are reported
  as a caution, not as evidence that readers recognise letters.
- **33 lessons** (evidence pointers for lessons 1-21, many of them to private records, except lesson 8, whose
  evidence did not survive; lessons 22-33 are operational), and the retracted claims of the work behind them.

## How others use it

- `pip install -e .` then `python -m stripqc.fill render.zarr render_fill.zarr` before villa ink inference on a strip,
  ring patch or tile crop, after running the positive control in your geometry. Score on the original render's
  CT-valid pixels.
- `stripqc.margins` and `stripqc.patchgrid` tell you how much of a given render the blank margins reach.
- `scripts/reproduce.sh` reruns the positive control's d = +1 arms (all but the original run's exploratory X13) in one
  command (checksums, weights, then `scripts/control_strips/run.sh`): 1.05 GB of CT and 0.55 GB of weights, CPU only,
  71 min on 4 cores. Edit the arm rows (Z13, Z20) in `scripts/control_strips/make_arms.py`, `score_arms.py` and
  `box_shift_check.py` to test your own strip geometry, or `MODELS` in both `scripts/pipeline/batch_ink.sh` and
  `scripts/pipeline/bi_common.py` (checkpoints as `$CKPT/<name>.pth`; `overlay.py` reads the list from `bi_common.py`)
  for other models.
- `stripqc.geometry.displace` makes the displaced negative-control copy of any segment. `stripqc.blindread` does the reader
  bookkeeping.

## Measured impact

<!-- BEGIN:headline -->
| PHerc0343 positive control (13 known letters), d = +1 | full context (same pixels) | 13-row strip, blank margins (as usual) | same strip, margin reflect-filled (exploratory) | negative control: moved 8 vox outward (plain / filled, exploratory; conservative, RESULTS §1) |
|---|---|---|---|---|
| strong ink (p > 0.55) inside the letter boxes | 15.38 % | 7.46 % | **14.43 %** | 0.32 % / 1.38 % |
| recall of the full-context strong ink [95 % CI, 13 letters] | 1 | 0.386 [0.257, 0.493] | **0.646 [0.499, 0.768]** | 0.002 / 0.032 |
| box AUC (letter boxes vs the rest, rank-based) | 0.709 | 0.670 | **0.703** | 0.479 / 0.528 |
| strong ink outside the letter boxes | 0.67 % | 0.50 % | 1.35 % | 0.29 % / 0.39 % |
<!-- END:headline -->

On the unread scroll PHerc0268 (aggregate numbers only, no images), the blank margins produced false ink bands in about
2/3 of the strips of a 56-strip mass run. The fill removed them in 5 of 7 re-inked strips. See
[docs/RESULTS.md §3](docs/RESULTS.md#3-the-same-artifact-on-real-unread-data-pherc0268-aggregate-numbers-only).

**No letters are claimed on any scroll.**

## Limitations

- **Opposite signs, unexplained.** On the positive control the blank margins suppressed ink and created no edge bands
  (the pre-registered band test at d = +1 was negative; at the mass-run depth d = −2 the edge band was also below full
  context). On PHerc0268 they created
  bands. Which step turns the zeros into the artifact (normalisation, InstanceNorm or the convolutions) is not isolated.
- **One positive control:** PHerc0343, one segment, 13 letters in scope, three 9 µm models; only d = +1 validated.
- **The fill is a partial, exploratory fix:** recall 0.646 [0.499, 0.768] against the 0.7 bar, and about twice the
  full-context strong pixels outside the letters. The +8 vox displaced copy is a conservative negative, not an
  ink-free input.
- **Blind readers were AI agents**, and colour alone separates the hidden controls better than they do.
- **The rerun** reused the software stack and a local copy of the segment repository; CT and weights were fresh. It
  shows determinism with fresh inputs, not an independent reproduction.
- **PHerc0268 evidence is aggregate only** and cannot be recomputed from the release.
- **Renderer:** the blank margin is verified at villa `41701aa` only.

## Links

- Repository: `github.com/abundantjoe/dominion-release`
- [README](README.md) · [Methods](docs/METHODS.md) · [Results](docs/RESULTS.md) · [Reproduce](docs/REPRODUCE.md) ·
  [Lessons](docs/LESSONS.md) · [Superseded claims](docs/SUPERSEDED_CLAIMS.md)
- Positive-control data: Erwin Nieuwlaar, `github.com/Nieuwlaar/pherc343-first-letters` (commit `e8370f1`, MIT).
  Scroll data: Vesuvius Challenge - CT Scans of Herculaneum Papyri (Angelotti et al.), CC BY-NC 4.0
  ([DATA_LICENSE.md](DATA_LICENSE.md)).
