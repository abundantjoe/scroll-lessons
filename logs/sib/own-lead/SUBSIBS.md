Provenance: Project HERCULES | owner the owner | [id removed]

# own-lead sub-siblings (DECL-P4-23 item 5). Recorded before any of them starts.
Frozen recipe: logs/sib/own-lead/p4own/RECIPE.md at commit 6b5bdc5 (sha256 377784c2bd8dd8617f38ae0e054fbe37684004f6e0d105852e84e16c16a6dfb8).
Model opus 5.5, same environment and repo. Sub-siblings may not create further sessions. Instructions: logs/sib/own-lead/p4own/WORKER.md.

| arm | session | branch | exact task |
|---|---|---|---|
| F1 | session_017e6QPfNKLtD4qVCn3hhPCQ | claude/gifted-bell-gavnl5-sib-own-f1 | rebuild + verify data; train F1; predict its 24 held-out tiles (RECIPE sec. 8, in order); held-out AUC with auc.py |
| F2 | session_01Nw78zAJaDFgL5Gpv3KoBwX | claude/gifted-bell-gavnl5-sib-own-f2 | same for F2 |
| F3 | session_01RmxTpkfueiv3XMMKZaDh5s | claude/gifted-bell-gavnl5-sib-own-f3 | same for F3 |
| S2 | session_014TJRngPm5FJBrWfgHMhsy5 | claude/gifted-bell-gavnl5-sib-own-s2 | rebuild + verify; train S2; predict X tiles r0-r7 x c9-c19 in the declared order; npz for col. -1 |
| S3 | session_015gFGMBXyTF6MzAnckcbLFh | claude/gifted-bell-gavnl5-sib-own-s3 | same for S3 |
| NULL | session_01B9qK5dgoo6tVRg7BiWrt5m | claude/gifted-bell-gavnl5-sib-own-null | same for NULL (deranged labels, derangement sha in RECIPE sec. 8) |
| S1 | own-lead itself (this session) | claude/gifted-bell-gavnl5-sib-own-lead (maps under logs/sib/own-s1/) | train S1 on the lead's verified data (started 13:05Z, pid 5708); then predict X tiles as S2 |
