Provenance: Project HERCULES | owner the owner | [id removed]

# RESUME (sib/tracer)

Current task: none. DECL-P4-24 item 2 is DONE (NOT ADOPTED, see p4-24/REPORT.md). DECL-P4-22 is DONE (NOT ADOPTED). T0 is still waiting on its declaration.

Pipeline (each step skips work that is already done):
1. `bash /work/scripts/p422_prep.sh` (log /work/logs/p422_prep.log; prints PREPDONE at the end):
   - local m7-L2 crop -> /work/p422/m7l2_local.zarr (frame.json holds the origin);
   - official patch -> /work/p422/official.tifxyz;
   - normal grids -> /work/p422/ng;
   - defects and holes -> /work/p422/resume.tifxyz and holes.npy (summary in p4-22/holes.json).
2. Trace: `run22.py` (to be written) resumes c5 L15 + gate_fix_resume_points from resume.tifxyz, with about 15 generations to fill the holes.
3. Evaluate: `eval22.py` (to be written) compares the hybrid and the official mesh on P with metrics22.py; the adoption rule is in its docstring. Push the tifxyz, flattening, metrics.json and REPORT.md.

Environment notes:
- After a container restart dockerd must be started again: `nohup dockerd --data-root /home/user/work/docker &`.
- P4-N is DONE (p4n/REPORT.md). T0 is still waiting on its declaration.

## 2026-09-30
- Current task: DECL-FL-1 First Letters screen for PHerc0175A.
  - Relaunch: `setsid nohup bash tools/sib/fl-pherc0175a/pipeline.sh --loop > /work/logs/fl175a.log 2>&1 &` (idempotent; markers are in /work/fl175a/state).
- Disk housekeeping (04:20Z): deleted the regenerable local copies of public S3 data from the finished P4-22 and P4-24 tasks, which freed 4.8 GB. These were /work/p422 and /work/p424 m7l2_local.zarr and their generated ng/. Run outputs and all pushed results are kept. Regenerate with `P4_CFG=... prep22.py fetch` plus vc_gen_normalgrids.
