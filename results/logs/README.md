# Run logs

Standard output of the original runs, copied verbatim from the machine they ran on (`/tmp/*.log`; 2026-09-17/18, and 2026-10-15 for `c1.log`) so that runtimes and
training traces cited in the documentation are traceable. Hardware: 4 vCPU Intel Xeon @ 2.10 GHz, 15 GB RAM, no GPU.

| log | run | notes |
|---|---|---|
| `s1seg1b.log`, `s1seg2.log` | preparation and judging of the 7 evaluation crops under mask J | per-crop timestamps |
| `s1prep.log` | preparation of the extra-segment training crops | |
| `s1v6.log` | the original v6 run | **invalid** (all-positive training data, incident 3) |
| `fixveto.log` | rebuild of the training-segment classes with the quantile veto | |
| `v7fit.log` | the first v7 fit, which failed because the declared veto left no negatives (undefined AUC; incident 3) | |
| `v7v6b.log` | v7 fit + judging, then v6b training (12 000 steps, 11 981 s) | |
| `v6c.log` | v6c training (12 000 steps, 12 137 s) | control |
| `v8.log` | v8 crop extension, preparation, training (12 000 steps, 11 458 s) and judging | |
| `gpr1.log` | GP-R1 training (4 000 steps, 8 334 s) and judging | overlapped the R1 run on the same CPUs |
| `e.log` | ensemble E judging | |
| `r1.log` | reading run R1 on unread windows | |
| `stroke.log`, `local_stroke*.log` | stroke test and local stroke test L | |
| `c1.log` | confirmation test C1 (2026-10-15) | |
