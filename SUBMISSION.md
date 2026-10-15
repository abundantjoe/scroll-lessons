# Progress Prize submission — text for the Google Form

Copy each block into the matching form field. Every measured number below is in [`docs/RESULTS.md`](docs/RESULTS.md),
[`docs/METHODS.md`](docs/METHODS.md), [`docs/REPRODUCE.md`](docs/REPRODUCE.md) or the generated [`results/FACTS.md`](results/FACTS.md);
those documents name the committed source files.
**Before submitting, the repository must be public** (it is private at the time of writing; changing that is the owner's decision).

---

## Title

inkeval — honest, reproducible evaluation for ink detection, with a pre-registered Scroll 1 study and a confirmation test on untouched crops

## Summary (≤ 200 words)

inkeval is a small, tested Python toolkit for judging ink-detection maps against hand-labelled Herculaneum text: pixel AUC; a
stroke-level AUC that stays defined when hand labels merge words; a local test that stops regional brightness passing for letters;
crop-level bootstrap intervals; a cross-crop label-swap null; rank ensembling; PNG + JSON export. It matches all 65 published judge
records checked (5 methods × 13 crops); the released weights regenerate the v8, GP-R1 and E evaluation maps bit-identically on the release machine.
The study, on 2.4 µm Scroll 1 CT, was pre-registered: every method declared in a git-tracked notebook before it ran.
A CPU-only ensemble of a 2-D U-Net and a Grand-Prize-style 3-D→2-D network, trained only on hand labels, reaches pixel AUC 0.876 and
stroke AUC 0.935 on 7 held-out crops (best hand-built physics: 0.668). A confirmation test declared before any window was chosen held
on 6 untouched crops (0.830 / 0.928), while a single U-Net that had passed did not. We also publish what went wrong — a veto leaving
7 of 8 training crops without negatives, single-crop AUCs of 0.69 from layout alone — as 84 lessons and 76 superseded claims, each traced to a
commit.

## What is novel

- **Tests that stay defined and separate letters from layout.** A stroke-level AUC (0.25 mm disks inside strokes vs blank disks) that is
  defined where component-based letter tests are not (the letter test was undefined on 2 of 7 crops here and swung with the mask), and a
  local test L that compares each stroke only with blank papyrus within 1.5 mm, so brightness that varies over more than about 1.5 mm cannot pass for letters.
- **A measured null instead of an assumed 0.5.** Scoring each crop against another crop's labels shows single crops reach AUC 0.69 from
  spatial layout alone; the toolkit makes this negative control one command.
- **Pre-registration with a confirmation set.** 13 methods were declared in a git-tracked notebook before they were run
  (the last six, v7, v6b, v6c, v8, GP-R1 and E, were judged once per crop set; the earlier seven were re-judged, all alike, when the
  judge mask changed); because the evaluation set was nonetheless reused across the sequence, a confirmation test on 6 untouched crops was declared before any
  window was chosen, and its result is reported as-is: E reaches 0.830 [0.800, 0.856] pixel and 0.928 [0.905, 0.947] stroke AUC and beats the best hand-built method on 6 of 6 crops (prediction held), while v8 alone falls to 0.774 / 0.881.
- **Attributions measured, not assumed.** A no-teacher control prices the team-model veto (+0.018 pixel AUC, 7/7 crops); a post-hoc
  decomposition separates ensembling from smoothing and finds the architectures tied at 19.2 µm under equal post-processing; and
  "detection is not legibility" is measured on unread papyrus with its own (post-hoc) null.
- **Full provenance.** Results are reported with the committed file or commit they come from; retracted claims are indexed with the
  reason.

## How others can use it

```bash
git clone https://github.com/abundantjoe/megara && cd megara && python3 -m venv .venv && . .venv/bin/activate && pip install -e .
inkeval demo                                                     # 2.5 s, real held-out Scroll 1 crops, with a negative control
inkeval judge --score pred.npy --label label.png --mask mask.png --pitch-um 2.4   # pixel AUC, stroke AUC, local L
inkeval bootstrap per_crop.csv --column my_method                 # crop-level 95 % interval
inkeval null --scores a.npy b.npy --labels la.png lb.png --masks ma.png mb.png      # label-swap negative control
inkeval ensemble --scores m1.npy m2.npy --mask mask.npy -o ens.npy                  # rank-mean ensemble
inkeval export --score ens.npy --mask mask.npy -o pred.png --segment 20231005123336 --y0 12400 --x0 23560   # PNG + JSON sidecar (segment, canvas origin)
```
Use it to report any ink detector with crop-level intervals, the stroke and local tests next to pixel AUC, and a label-swap null. The
released v8 and GP-R1 weights, the research pipeline and six reproduction levels (2.5 s to a full rebuild from public data, with checksums
and runtimes) let others reproduce or extend the Scroll 1 study.

## Measured impact

All on real Scroll 1 data (PHerc. Paris. 4, 2.4 µm) unless stated; means over crops with 95 % crop-level bootstrap intervals, truncated:
- **Before → after:** best hand-built physics (v7) 0.668 → ensemble E 0.876 pixel AUC on 7 held-out crops (+0.207 [0.171, 0.257], 7/7
  crops; stroke +0.222 [0.163, 0.296]); on 6 untouched confirmation crops 0.618 → 0.830 (+0.212 [0.188, 0.234], 6/6).
- **Confirmation:** the pre-registered prediction held on untouched crops. E's pixel AUC there is 0.0456 lower than on the evaluation
  set (two-sample CI −0.0885 to −0.0055; interval method chosen post-hoc) and the positive control's 0.0297 lower (post-hoc), so most of the drop looks like harder
  windows; the remaining 0.0159 is consistent with the cost of reusing the evaluation set, which 6 + 7 crops cannot separate from
  noise (INFERENCE).
- **Controls:** positive control (team model) 0.929 / 0.899 on the two sets; negative control (label swap) for E on the evaluation set
  mean 0.517, but single crops up to 0.694 from layout alone, so we read any single-crop AUC below ≈ 0.70 as no evidence of ink
  detection (INFERENCE).
- **Attributions measured:** team-model vetoing of training negatives is worth +0.018 [0.008, 0.028] (7/7 crops, no-teacher control);
  ensembling +0.024 to +0.028 vs smoothing +0.008 to +0.012 within E (smoothing alone adds +0.029 to GP-R1); architecture at 19.2 µm
  a tie under equal post-processing (+0.009 [−0.019, 0.033]); these two are post-hoc (D3).
- **Bugs found, with evidence and fixes:** a declared veto that left 7 of the 8 training crops without negatives (a training run
  invalidated, not reported as a result); per-crop label misregistration caught by the positive control (a shift of about 1 mm on
  one evaluation crop: 1.024 mm in the check that found it, 1.033 mm as applied; three training crops sit at the 1.536 mm search limit); a letter test undefined where hand
  labels merge words; chunk deletions that silently removed about two-fifths of two w028 calibration crops (PHerc. 1667).
- **Reproducibility:** on the release machine the released weights regenerate v8, GP-R1 and E bit for bit on all 7 evaluation crops;
  the toolkit reproduces 65 of 65 published judge records (5 methods × 13 crops; pixel AUC to the identical float, stroke and L to the
  4 decimals stored); the 12 downloaded label and overview images are byte-identical to their public sources (the CT surface volumes,
  streamed per crop, are pinned by versioned URL and the SHA-256 of their metadata).
- **Detection is not legibility:** on unread papyrus E agrees with the team model at AUC 0.793–0.886 per window, above a post-hoc
  swapped-window null (N1, max 0.652), yet no legible character appears — and none is claimed.

## Links

- Repository (code, weights, results, docs): https://github.com/abundantjoe/megara
- Quick start and tool usage: https://github.com/abundantjoe/megara#quick-start-5-minutes
- Results, pre-registered vs exploratory, with CIs and nulls: https://github.com/abundantjoe/megara/blob/main/docs/RESULTS.md
- Lessons with evidence: https://github.com/abundantjoe/megara/blob/main/docs/LESSONS.md
- Retracted and corrected claims: https://github.com/abundantjoe/megara/blob/main/docs/SUPERSEDED_CLAIMS.md
- Reproduction, levels 0–5, with checksums and runtimes: https://github.com/abundantjoe/megara/blob/main/docs/REPRODUCE.md
- Lab notebook (declarations before results in commit order; three exceptions listed in RESULTS §1): https://github.com/abundantjoe/megara/blob/main/docs/RULES.md
