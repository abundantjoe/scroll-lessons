Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-fe sub-siblings

The work splits by scan family, not by rows. The frozen detector (params.json, 4a927a1) runs as two independent
pipelines: the 1.129 um family (C + E1) here, and the 2.4 um family (C2 + E2) in one sub-sibling. Measured cost here:
about 50 s per injection location and about 570 range requests/s. Two containers halve the wall time. Rows are not
split further, because each family's level-0/1 fetch takes about 10-20 min in one container.

| # | session id | branch | exact task |
|---|---|---|---|
| 1 | session_015A2r6XhvSPDPgraM4kZgbV (created 18:30:57Z) | claude/gifted-bell-gavnl5-sib-p4-pig-fe-e2 | From origin/claude/gifted-bell-gavnl5-sib-p4-pig-fe at or after the params freeze 4a927a1: pip install numpy opencv-python-headless scipy requests tifffile; then `python tools/sib/p4-pig-fe/run_family.py C2 E2 <scratch> claude/gifted-bell-gavnl5-sib-p4-pig-fe-e2 12` from the repo root, on its own branch. It pushes logs/sib/p4-pig-fe/24/{scores_C2.json, injection_C2.json, injection_E2.json, scores_E2.json, run_log.jsonl} and a STATUS line in logs/sib/p4-pig-fe/24/STATUS.md. No code or parameter change; numbers only; no image is viewed; no further siblings. |
| 2 | session_018eReurS57jSousvTQonfcp (created 18:30:58Z) | claude/gifted-bell-gavnl5-sib-p4-pig-fe-e1 | From origin/claude/gifted-bell-gavnl5-sib-p4-pig-fe at or after 4a927a1: pip install numpy opencv-python-headless scipy requests tifffile; from the repo root run `python tools/sib/p4-pig-fe/strip.py maps E1 <scratch>` and then `python tools/sib/p4-pig-fe/strip.py score E1 <scratch> logs/sib/p4-pig-fe/1129/scores_E1_raw.json --sigma0 1.0`, so z = raw r. The parent divides by the control sigma0. Push that file on its own branch, with a STATUS line in logs/sib/p4-pig-fe/1129/STATUS_E1.md. No code or parameter change; numbers only; no image is viewed; no further siblings. |

Measured before creation: one control row at level 0 takes 5.3 min in this container and is CPU-bound (4 cores). Splitting the families and the E1 maps across containers is therefore materially faster.

Note: the rows (branch and exact task) were pushed before creation (3f2bb55, 566dcea). Session ids cannot be known before creation, so they were filled in immediately after it.
