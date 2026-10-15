Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal REAL-TRIB-1: real-data gate for the pre-read checks (before first use in a batch)

Why: all TRIBUNAL numbers so far come from synthetic worlds. There the independent reference and
the delivered render agree at NCC >= 0.97. The smallest clean slice-lag margin shrinks as the
CT texture gets smoother:

| texture sigma | min slice margin | min depth margin | min mirror margin |
|---|---|---|---|
| 1 vox | 0.114 | 0.773 | 0.828 |
| 2 vox | 0.085 | 0.603 | 0.716 |
| 3 vox | 0.076 | 0.597 | 0.607 |

The thresholds are 0.02 / 0.02 / 0.05. Real 9 um CT may correlate more strongly slice to slice.

Material: official `vc_render_tifxyz` renders that already exist under the validated C2-NT chain
on NON-eligible, non-sealed papyrus (e.g. the PHerc0139 C3 crops, w044/w040), CT stacks only.
No ink map, nothing within 144 vox of J, and no read.

Procedure (code only, no viewing): for >= 10 windows, run `preread_gate` on the clean record, then
re-run it with each planted fault. The faults are an 8 px offset re-render, stack reversal,
left-right and up-down flip, a +-1-slice re-render (`--slice-step` offset render or a +-1 vox
normal-displaced mesh), a wrong voxel size, and a re-trace (an official re-trace pair from RCBANK-1,
e.g. w023/w024).

Bars: clean records 100 % pass; every fault 100 % caught by its own check. Record the distribution
of clean margins and fix thresholds at <= 1/3 of the smallest clean margin. If any clean record
fails, or a margin is < 3 x its threshold, the thresholds are re-declared before use. They are
never lowered after a read.

Cost: CPU only. About 0.5-2 s per check on a 256 px crop, plus one block read of about 300^3 vox
per window.
