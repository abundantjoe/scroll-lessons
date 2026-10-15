Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-fe family 24 (C2 control + E2 title strip) — sub-sibling e2

STATUS: running — stages 1, 2a done; run 1 crashed at start of stage 2b (E2 injection); rerun (run 2) started 2026-09-26T18:50:09Z
Command: `python tools/sib/p4-pig-fe/run_family.py C2 E2 /tmp/fe24 claude/gifted-bell-gavnl5-sib-p4-pig-fe-e2 12`
Base: origin/claude/gifted-bell-gavnl5-sib-p4-pig-fe @ 654a7b7 (params frozen, no code/parameter change).

## Stage 1 — C2 control (scores_C2.json)
- maps: 191240 chunks fetched, 11032 absent (404), 484.7 s; 9x21 tiles, scale 2
- positions: 182,432,734; r median 2.921
- sigma0 = 2.21971 (1.4826*MAD of r, control eligible tiles)
- theta = 13.8444 (p99 of control z ∪ z_rot90)
- eligible control tiles: 188; leave-one-out FP 2/188 = 0.0106
- observation (not acted on): rot90_max_abs_diff_z = 0.0 — z and z_rot90 identical on every eligible tile,
  so the "∪ z_rot90" in theta adds no independent sample (effectively p99 of 188 values duplicated). Flagged for the parent.

## Stage 2a — injection-recovery on C2 (injection_C2.json, seed 303)
Detected = planted z > theta. Per-thickness recovery (12 locations, 14 tried):

- C2: n_loc=12 tried=14 baseline z max=8.814 baseline detected=0
| regime | R | t_um | detected | det&in-sheet | median dz |
|---|---|---|---|---|---|
| lean_rho_e | 3.1 | 2 | 0/12 | 0/12 | -0.002 |
| lean_rho_e | 3.1 | 5 | 0/12 | 0/12 | -0.013 |
| lean_rho_e | 3.1 | 10 | 0/12 | 0/12 | -0.034 |
| lean_rho_e | 3.1 | 20 | 0/12 | 0/12 | -0.013 |
| standard_mu | 10.9 | 2 | 0/12 | 0/12 | +0.127 |
| standard_mu | 10.9 | 5 | 0/12 | 0/12 | +2.242 |
| standard_mu | 10.9 | 10 | 12/12 | 7/12 | +10.635 |
| standard_mu | 10.9 | 20 | 12/12 | 12/12 | +29.356 |
| standard_rho_e | 4.5 | 2 | 0/12 | 0/12 | +0.025 |
| standard_rho_e | 4.5 | 5 | 0/12 | 0/12 | +0.034 |
| standard_rho_e | 4.5 | 10 | 0/12 | 0/12 | +0.368 |
| standard_rho_e | 4.5 | 20 | 0/12 | 0/12 | +4.728 |

## Crash 1 (run 1, at start of stage 2b — E2 injection)
```
  File "tools/sib/p4-pig-fe/run_family.py", line 71, in main
    inject.main(mat, scr, nloc, SEEDS[mat], ip, theta, sigma0)
  File "tools/sib/p4-pig-fe/inject.py", line 150, in main
    g = strip.geometry(name, scr, P)
  File "tools/sib/p4-pig-fe/strip.py", line 44, in geometry
    man = json.loads(fe.git_show(pm["eligible_from"]["ref"], pm["eligible_from"]["path"]))
  File "tools/sib/p4-pig-fe/fe.py", line 171, in git_show
subprocess.CalledProcessError: Command '['git', 'show', 'origin/claude/gifted-bell-gavnl5-sib-pairs0814b:logs/sib/pairs0814b/e2/manifest.json']' returned non-zero exit status 128.
fatal: invalid object name 'origin/claude/gifted-bell-gavnl5-sib-pairs0814b'.
```
Cause: environment, not code — this container's clone had no remote-tracking ref for that branch (single-branch fetch).
Action (no code or parameter change): `git fetch origin <b>:refs/remotes/origin/<b>` for the two refs the frozen
code/params name — sib-pairs0814b @ cc81a67, sib-p4-tiles-b @ 8687bf4 — then reran the identical command (resumes).
Note for the parent: the result depends on those branch tips as of fetch time; the refs are not pinned to a sha in params.json.
