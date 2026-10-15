# Changelog

## 1.0.0 — 2026-10-15 — public release

- **`inkeval` toolkit** (`pip install -e .`): pixel AUC, stroke test, local stroke test L, crop-level bootstrap, paired bootstrap,
  cross-crop label-swap null, rank-mean ensemble, PNG + JSON export in segment coordinates, CLI (`inkeval judge|ensemble|bootstrap|null|export|demo`),
  a bundled real example and 18 tests (15 run anywhere; 3 need the research data). `scripts/check_toolkit_records.py` compares the toolkit
  with the published judge, stroke and L records of E, v8, GP-R1, v7 and the team model on the 7 evaluation and 6 C1 crops (65 of 65
  method–crop records, 0 failures: `results/toolkit_vs_records.json`).
- **Confirmation test C1** on six untouched labelled windows, pre-registered before any window was chosen, frozen weights: prediction held — E 0.830 [0.800, 0.856] pixel, 0.928 [0.905, 0.947] stroke, ahead of v7 on 6/6 crops; v8 alone 0.774 / 0.881 (below the bars).
- **Release statistics**: crop-level bootstrap CIs (11 detectors on the evaluation set, 6 on C1), paired differences (10 comparisons on
  the evaluation set, 6 on C1) and a label-swap negative control.
- **Post-hoc analyses**, labelled as such: D3 (ensembling vs smoothing in E) and N1 (null for the reading-run agreement statistic).
- **Reproducibility**: input manifest (the 12 downloaded label and overview images verified against the public sources by SHA-256; the
  streamed surface volumes pinned by versioned URL and metadata hash), locked environment, released weights with SHA-256,
  a check that regenerates v8, GP-R1 and E from the released weights (bit for bit on all 7 evaluation crops, on the release machine), a check of pre-registration order in git, run logs.
- **Documentation**: README, METHODS, RESULTS, LESSONS, REPRODUCE, SUPERSEDED_CLAIMS, SUBMISSION, data notice and citation.
- **Fixes found while preparing the release**: the bundled example was excluded by `.gitignore` (`data/` → `/data/`); the drivers in `scripts/` no
  longer `cd` to an absolute path (the archived ones still do); figure captions are computed from the results and truncated; the D3 like-for-like interval is now produced by
  committed code; the D3 script docstring misattributed the upsampling (v8 is bilinear, GP-R1 nearest-neighbour).
- **Reorganisation**: lab notebook to `docs/RULES.md`; superseded documents and scripts to `archive/` (moved with history); reading-run
  evidence to `docs/figures/`; regenerable E1 feature banks removed from the working tree (kept in history).

## Research log (2026-09-16 → 2026-09-19)

The full record is the lab notebook [`docs/RULES.md`](docs/RULES.md) (append-only except commit 10d098e, which corrected two heading
times) and `git log`. In brief:

- 2026-09-16: repository created; environment inventory; topography paper logged; crop rule and gate bars declared. Large-σ Gaussians
  replaced by triple box filters (approximately the same variance) after a 28-CPU-minute residual; distance transforms replaced by disc dilations and
  intermediates freed after two out-of-memory kills (15 GB RAM, one 8337² chart peaked at 12.3 GB). Jobs serialised.
- 2026-09-17: papyrus-subtraction route (v0.1–v0.2) at chance on w028; Scroll 1 gate declared against papyrologically read text; label
  registration; hand-built depth-template and ridge methods (v1–v3) fail the bars; first U-Net (v5) memorises its single crop.
- 2026-09-18: judge mask J; stroke test and local stroke test L; E1 exploration; blank-veto incident (every negative removed from 7 of the 8 training crops) and fix;
  v6b, v6c control, v7, v8 (first to clear both bars on the 7-crop mean), Grand-Prize-style baseline GP-R1, ensemble E; reading run R1 on unread papyrus.
- 2026-09-19: reading run R2.
