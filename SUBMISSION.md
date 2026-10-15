# Progress Prize submission: text for the Google Form

Paste each field as written. Every number below also appears in `README.md`, whose headline table gives each
result's evidence link and the commit that introduced it.

---

## Title

hercules: falsifiable ink reads, and a pre-registered held-out test showing a training-calibrated 0.5 cm² unit screen almost never fires on known text from a scroll the model never saw

## Summary (≤ 200 words)

hercules is a CPU-only quality-control toolkit for ink-detection reads on Vesuvius Challenge segments.

- Every read is paired with the same model on the same pixels in reversed depth order, as a matched negative
  control.
- Truncated prediction maps are refused, and a tripwire catches mirrored surfaces.
- Layout-aware power says whether a null result could have been anything else.

On real data, a truncated map turned a FAILED test into ADMITTED (margin 0.60594 against the true 0.39948); the
guard built in response refused the next one. A near-textureless render gave forward 0.4522 but margin +0.0003.
The published VC3D image the docs call up to date rejects the ink tutorial's `--flip-normals`.

The known-text control was re-created from public data in a fresh container; its maps are byte-identical to
September's. That control proved to be a training-set sheet. So we ran a pre-registered test on three labelled
segments of PHerc0841, a scroll the model never saw. Pixel AUC transfers (0.8393), yet the 0.5 cm² screen flags 1
of 60 units. The eligible-scroll negatives (1/113, 0/190) are not significantly below it, nor below the declared
text-unit rate 1/15 (exploratory p ≥ 0.07), so we infer they are not evidence of absent ink.

## What is novel

- **A matched negative control on every read.** villa's `infer --direction both` already writes the reversed-depth-order
  map; hercules makes it mandatory for every read and judges every verdict on forward − reverse, never on forward
  probability alone. On held-out known text
  (PHerc0841) the reverse order scores AUC 0.5486 against forward 0.8393 (0.49633 against 0.99659 on the
  training-set sheet w040).
- **A refusal layer for broken model output.** A truncated forward/reverse pair is detected with relative footprint
  and coverage tests and cannot be scored. A first version with an absolute bar flagged 19 sound maps, so the bar
  was made relative.
- **Layout-aware power for nulls.** This computes the probability that a surface's actual valid-unit layout could
  yield a candidate at all. It replaced a density estimate (1.59 expected candidates) that was about 20× (1.59 / 0.079 = 20.13 on the printed values) too
  optimistic: the layout-aware value is 0.079, a lower bound; a rough, uncomputed scaling for clustering puts it near 0.5.
- **A pre-registered held-out test of the public `ink_9um` model at the unit level** on an unseen scroll.
  It shows that the model's pixel signal transfers (AUC 0.8393 / reverse 0.5486) but a training-calibrated
  0.5 cm² screen almost never fires on that text (1 of 15 text-bearing units; 0 of the 7 most-inked, a post-hoc
  subset).
- **A fully audited record.** Bars were written in the notebook before results. The exceptions (four declarations
  committed together with their results, and R-REPRO's bars, declared after its inference started but before any
  output) are listed in SUPERSEDED_CLAIMS. 10 of 10 hand-written p-values were recomputed by code. There is a
  bit-for-bit fresh-container reproduction from public data, and every retracted claim and notebook rule break is
  listed.

## How others use it

```bash
git clone --depth 1 https://github.com/abundantjoe/hercules && cd hercules
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt   # Python >= 3.12
bash examples/quickstart.sh                                          # ~16 s, real known text, 10 checks
python scripts/map_integrity.py --pair pred.tif pred_reverse.tif --render-dir <dir with render.zarr>   # footprint and coverage tests; without --render-dir, no coverage test
python scripts/read_chart.py render.zarr pred.tif pred_reverse.tif --um <um/px> --out read/ --key '<scroll>|<surface>|<depth offset>|<ckpt+TTA>|both' --ledger read/LEDGER.md
python scripts/cluster_power.py --read-stats read/read_stats.json   # could this surface yield a candidate?
python scripts/rheldout.py seg1/ seg2/ seg3/ --um <um/px> --json heldout.json   # held-out known-text test on labelled segments (pixel AUC for any maps; rule 5.5's bars were set for ink_9um)
```

It takes standard inputs: OME-Zarr surface volumes, tifxyz meshes, and the forward/reverse TIFFs from
`vesuvius.ink_detection.inference.infer --direction both`. The analysis tools run on CPU and were run with
Python 3.13.16; re-running the model (villa) needs Python 3.14. The test suite has 3 data-dependent integration
tests, which skip without the public data. `scripts/reproduce_control.sh` re-creates the known-text control from
public data (inference 5958 s on 4 cores in R-REPRO, the same call run before the script existed; 5526 s, with other
work on the box, when the script ran end to end). `docs/` holds METHODS (every parameter), RESULTS (pre-registered
vs exploratory, with intervals), LESSONS (37), REPRODUCE (versions, checksums, commands) and SUPERSEDED_CLAIMS.

## Measured impact (real data)

- **Held-out known text, PHerc0841 (pre-registered):** pixel AUC **0.8393** forward / **0.5486** reverse; frozen
  rule **1 of 60** units flagged (exact 95 % CI 0.0004–0.0894), 1 of 15 text-bearing units. The reader calls the
  three segments NOT ESTABLISHED, NOT ESTABLISHED and BLANK. No supervised-blank unit exists on these segments, so
  the false-positive rate on an unseen scroll is unmeasured.
- **Eligible scrolls:** 1 flagged of 113 units (corpus) and 0 of 190 (11 team surfaces of PHerc1203 and PHerc1447).
  Against the training-set rate 7/71 this looks like a deficit (p = 0.0058, 8.81 × 10⁻⁵). Against the held-out rate
  over all valid units, 1/60, it is not significantly lower (exploratory, computed after the result: p = 0.575, 0.24).
  The declared reference was the held-out rate on text-bearing units, 1 of 15; against it the counts are not
  significantly lower either (p = 0.221, 0.0732; scripts/release_stats.py).
- **Truncated map:** R-DEPTH went ADMITTED (M 0.60594) on a truncated map → withdrawn after a second test read every
  reverse unit as 0.0000 → FAILED on the complete map (true M 0.39948). The guard built in response refused a second
  truncated map (coverage 0.9404) before scoring.
- **Near-textureless render:** forward 0.4522, above the known-text level, with margin +0.0003, so not flagged.
- **Mirrored surface on known text:** 0 flagged forward, 2 when swapped; the tripwire fired.
- **Stale published VC3D image (still the May build on 2026-10-15; not yet reported upstream):** `:edge` is the 2026-05-13 build (villa 1e3f4c0). It
  rejects `--flip-normals`; its smoke render matched the team stack only reversed, at Pearson 0.42–0.82. The rebuilt
  binary gives a minimum Pearson of 0.999999 (six decimals) over the 28 slices.
- **Reproducibility:** the w040 control re-created from public data gave Gate A 0.99659 / 0.49633 and 7/71 with
  clusters [4, 2, 1]. Both prediction maps were byte-identical to September's, and stayed so when the committed
  `scripts/reproduce_control.sh` ran end to end from an empty directory (fetch, inference and every check).

## Links

- Repository: https://github.com/abundantjoe/hercules (branch `main`)
- Start here: https://github.com/abundantjoe/hercules/blob/main/README.md (headline table with
  evidence links) and https://github.com/abundantjoe/hercules/blob/main/examples/quickstart.sh
- Held-out test: declaration https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3231, result
  https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3296, records
  https://github.com/abundantjoe/hercules/tree/7925b3a/records/release/heldout_2026-10-15
- Fresh-container reproduction: https://github.com/abundantjoe/hercules/blob/main/docs/REPRODUCE.md
  and https://github.com/abundantjoe/hercules/tree/eed0fac/records/release/repro_2026-10-15
- Stale-image evidence: https://github.com/abundantjoe/hercules/blob/96431a4/records/release/edge_image_check_2026-10-15.md (two readings corrected by the section appended at its end)
- Every retraction: https://github.com/abundantjoe/hercules/blob/main/docs/SUPERSEDED_CLAIMS.md ·
  Lessons: https://github.com/abundantjoe/hercules/blob/main/docs/LESSONS.md
- License: MIT (code); data CC BY-NC 4.0
  (https://github.com/abundantjoe/hercules/blob/main/DATA_NOTICE.md)
