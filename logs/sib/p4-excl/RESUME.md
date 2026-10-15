Provenance: Project HERCULES | owner the owner | [id removed]

# p4-excl RESUME (2026-09-27T10:57Z)
Done and pushed: excl_a/excl_b/excl_d_a/excl_d_b, dense r6_c7, r6_c4, grid equality, label_fractions.json (DECL-P4-21), p4own/T_cert (DECL-P4-23 item 1), p4own/labels (item 2).
Open: DECL-P4-23 item 6(c) col. -1 (c11-c13 r0-r1) pixel AUC of own-s1/s2/s3 prediction arrays against the organizer labels (code only), output p4own/colm1_auc.json. Needs: the S-arm arrays on branches claude/gifted-bell-gavnl5-sib-own-s*; mapping via tools/sib/p4-excl/uvmap.py + label_frac.py logic (X label values used only for this AUC).
Scratch (container, not committed): /tmp/claude-0/p4excl (compact meshes struct/, strip meshes, label zarr level 0 in labels/). If lost: tools/sib/p4-excl/fetch.sh + build.py, downloads.jsonl lists every source with sha256.
Not pursued: pp/tifxyz-dist packaging (blocked by the permission system; drafts kept outside the repo, superseded per orchestrator).
