# Archive

Superseded material, kept because the lab notebook ([`docs/RULES.md`](../docs/RULES.md)) and the lessons
([`docs/LESSONS.md`](../docs/LESSONS.md)) cite it. Nothing here is needed to use the toolkit or to reproduce the release's headline
results. Files were moved here with `git mv` at the release, so `git log --follow <file>` shows their full history, and every commit hash
cited in the documentation still resolves.

| path | what it is | why archived |
|---|---|---|
| `docs/STATE_2026-09-17.md` | the project status page as of 2026-09-17 ("No submission ready") | superseded by the release README |
| `docs/METHOD_v0.2_papyrus_subtraction.md` | specification of the papyrus-subtraction route (v0.1/v0.1b/v0.2) | the route measured at chance; see RESULTS.md |
| `docs/report_2026-09-17.md` | interim report | superseded; several numbers changed under mask J |
| `docs/reproduce_2026-09-18.md` | first reproducibility note | replaced by [`docs/REPRODUCE.md`](../docs/REPRODUCE.md) |
| `review_sheets/` | 2026-09-17 review images of segment 1 | superseded by [`docs/figures/`](../docs/figures) |
| `scripts/` (top level) | w028 calibration gates (`gate_eval.py`, `select_crops_w028.py`, `run_w028_crops.sh`, …), papyrus-subtraction extras (`inpaint_net.py`, `v03p_hp.py`, `v03f_sample.py`), diagnostics D1/D1b/D1c/D2, and every superseded driver (`run_s1*.sh`, `run_v03*.sh`, `run_d*.sh`, …) | superseded methods and orchestration |
| `scripts/explore/` | the E1 exploration (2026-09-18): probes for seven of the eight hypotheses declared in [`docs/RULES.md`](../docs/RULES.md) (prefixes `mf`, `fb`, `tf`, `es`, `au`, `ca`, `hr`; `hr` holds only a registration step), with its outputs in [`stats/explore/`](../stats/explore) | exploratory; its findings are summarised in RESULTS.md and LESSONS.md |

The archived drivers call scripts by their original paths (`scripts/<name>`). To run them unchanged, check out the commit before the
release reorganisation (see the "release reorganisation" commit in `git log`, and use its parent).

The E1 feature banks (`stats/explore/fb_bank/*.npz`, 181 MB) were removed from the working tree at the release; they remain in history at
commit `cdc291e` and are regenerable with `archive/scripts/explore/`.
