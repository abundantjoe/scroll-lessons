# rh-e1 STATUS
Provenance: Project HERCULES | owner the owner | [id removed]

Updated: 2026-09-30 ~03:50Z.

## State: E1, M2a verified by the orchestrator; F1, l2sa, l2sb DONE (audit VALID; l2sb awaits orchestrator verify with --prior=l2sa). P4-H closed (gate FAIL). No harness job pending
### E1 (raw 1.129 um CT; DECL-P4-5 / -A1), logs/sib/rh-e1/{A,B}
- Builder p4-tiles-b @ 8687bf44 (e1a1). norm_manifest (METRIC-HASH-27) --coverage: 60 eligible, 0 skipped.
- Keys e1 (60) f03b5a0b...b741, ne1 (8 N0) db4ab202...f2a. 8 jobs (7 x 8+1, 1 x 4+1), sigma2.
- COMMIT A 723b4da (17:51:52Z), before any reader. COMMIT B f2f9ede (17:54:27Z).
- 8 opus readers: audit 8/8 VALID, 0 violations, 0 unread, prompt == brief 8/8, 0 reruns; every hand-back was DONE only.
- Schema files for rh_verify added LATER (09a62d5), derived only from commit-A files; no commit-A file changed.
### M2a (P4-D official 1 um predictions; DECL-P4-4 / -A1), logs/sib/rh-e1/M2a/{A,B}
- Builder p4-tiles-a @ 52bcf465. norm_manifest METRIC-HASH-29 (d2faee66) --coverage: 60 eligible, 40 coverage-skipped.
- Keys d_a (60) 5b0881a5...6adc, nd_a (8 N0, seed 20358758) fca87f44...45af. 8 jobs (7 x 8+1, 1 x 4+1), sigma2.
- COMMIT A 50b2152 (17:57:15Z, SHA256SUMS + builder_ref.json included), before any reader. COMMIT B 74eb472 (18:00:16Z, B/age layout).
- 8 opus readers: audit 8/8 VALID, 0 violations, 0 unread, prompt == brief 8/8, 0 reruns; every hand-back was DONE only.
### F1 (P4-F dense channel on E1; DECL-P4-6, sigma2t per DECL-P4-12-A1), logs/sib/rh-e1/F1/{A,B}
- Builder p4-highz @ 35e7c393 (f1/manifest.json; level 0, 2.258 um). norm_manifest (METRIC-HASH-29) --coverage: 60 eligible, 0 skipped, 60 unique PNG.
- Keys f1 (60) 16e93ba4...045e, nf1 (8 N0, seed 20275563) 114b67ab...6b83. 8 jobs (7 x 8+1, 1 x 4+1), variant sigma2t (p4_jobs 7966d6b1, task f07fbdff).
- COMMIT A 3155e73 (18:42:22Z), before any reader. COMMIT B f067b2b (18:44:46Z, B/age).
- 8 opus readers: audit 8/8 VALID, 0 violations, 0 unread, prompt == brief 8/8, 0 reruns; every hand-back was DONE only.
- Key-free rh_verify dry run vs logs/p4/ref_brief_sigma2t.txt: A0-A5 (8/8 briefs exact), B1, B2 all true.
### L2S early batch l2sa (P4-L per-tile stretch, DECL-P4-12-A2, sigma2t), logs/sib/rh-e1/L2S/{A,B}
- Builder p4-l2 @ 61669732 (partial manifest, used as committed): 41 tiles = all 40 eligible r0-r1 + r2_c0. No --coverage (2.4 um strip a).
- Keys l2sa (41) afbb3f6b...5282, nl2sa (6 N0, seed 20291915) 0c5ac22e...d8e9. 6 jobs (5 x 8+1, 1 x 1+1).
- COMMIT A 69cfae2, before any reader. COMMIT B 7d011e2 (B/age).
- 6 opus readers: audit 6/6 VALID, 0 violations, 0 unread, prompt == brief 6/6, 0 reruns; every hand-back was DONE only.
- Key-free rh_verify dry run vs ref_brief_sigma2t: A0-A5 (6/6 exact), B1, B2 true.
### L2S remainder l2sb (ASK-3 ruling; rh_verify --prior=l2sa), logs/sib/rh-e1/L2Sb/{A,B}
- FULL manifest p4-l2 @ 8056aa09 (160/160 eligible, partial=false), normalised, minus exactly the 41 l2sa (r, c) (all present, sha-matched) = 119 tiles; disjoint, union == 160.
- Keys l2sb (119) 0d5eb064...c1e3, nl2sb (15 N0 from l2sb, seed 20341658) 1f68b27e...78b0. 15 jobs (14 x 8+1, 1 x 7+1), sigma2t; p4_jobs e9f99ce4 (METRIC-HASH-38; sigma2t path unchanged).
- COMMIT A b02b521 (removed list, full + filtered manifest sha), before any reader. COMMIT B 3446390 (B/age).
- 15 opus readers: audit 15/15 VALID, 0 violations, 0 unread, prompt == brief 15/15, 0 reruns; every hand-back was DONE only.
- Key-free rh_verify dry run with prior l2sa: A0-A5 (15/15 briefs exact), A4 remainder check, B1, B2 true.
### W1 block windows (DECL-P4-17-A1, -A2 ruling on ASK-4), logs/sib/rh-e1/W1/{A,B}
- Builder p4-tiles-a @ b59df7ec: 15 M1 windows (8 title, 6 control, 1 blank-end), all eligible; no --coverage. All 15 labelled-adjacent (redirection only).
- Keys w1 (15) a8a6bebd...8dff, nw1 (2 N0, tool seed 20296918; A2 option a) f3237d43...17cf. 2 jobs (8+1, 7+1), variant block (k_d2_task_block 2995f22f).
- COMMIT A 24327b7, before any reader. COMMIT B f336908 (B/age).
- 2 opus readers: audit 2/2 VALID, 0 violations, 0 unread, prompt == brief 2/2, 0 reruns; hand-backs DONE only.
- Key-free rh_verify dry run vs ref_brief_block: A0-A5 (2/2 exact), B1, B2 true.
### OWN_F1 (P4-OWN G1 fold F1; DECL-P4-23 6(b), -A1, METRIC-HASH-48/50), logs/sib/rh-e1/OWN_F1/{A,B}
- Builder own-lead @ 0f164e1b (own-f1/maps, arm F1, model 1b1621e8...): 24 tiles, all eligible and all in the RECIPE F1 list; prep_own.sh f30807ac + own_split.py b400e9a4.
- Keys own_f1a (20, w028-037) 9e95920d..., own_f1b (4, w010-027) 26fcd385..., n_own_f1 (3 N0) 66af8263.... Jobs census_own_f1 (sigma2t, 3 x 8+1) and census_own_f1k (block, 3 x 8+1) over the same keys.
- COMMIT A 1c87536, before any reader. COMMIT B 6e9eef1 (B/sigma2t, B/block).
- 6 opus readers: audit 6/6 VALID, 0 violations, 0 unread, prompt == brief 6/6, 0 reruns; hand-backs DONE only.
### OWN_F2 / OWN_F3 (P4-OWN G1 folds F2, F3), logs/sib/rh-e1/OWN_F{2,3}/{A,B}
- Builder own-lead @ c4006fe3: F2 and F3 24 tiles each, all eligible, all w028-037 (no own_f*b batch); prep_own.sh f30807ac + own_split.py b400e9a4.
- Keys own_f2a 4e9f9ff5... / n_own_f2 6d3ca319...; own_f3a ae07b1fa... / n_own_f3 8aa7c4b8.... Jobs census_own_f{2,3} (sigma2t, 3 x 8+1) and census_own_f{2,3}k (block, 3 x 8+1).
- COMMIT A 7ad130e (both folds), before any reader. COMMIT B: F2 a4e1822, F3 (this push).
- 12 opus readers: audit 12/12 VALID, 0 violations, 0 unread, prompt == brief, 0 reruns; hand-backs DONE only.
### Dry run of the rh_verify checks that need no key (both batches)
- A0-A4, B1, B2 true. A5: 7/8 briefs exact; the partial 4+1 brief passes only with <IMG> runs collapsed (ASK-2).

## Next
- Standing by for harness orders.

## Blockers
None. ASK-5 notes open.

## S1 map helper (DECL-P4-25-A10, -A10-A1; BRIEF_S1MAP.md 23209537, assign 4f77b04d)
- infer.py sha256 36a64e1ac07eea859bb586a484300ace048e732420167f9bf77516befaccdf2e; own_common.py f8850058e53e29ddab177d0a1aac85dece6391360e3b2679b7d98fc36ab0eb8e; ckpt-screen-b @ 98cd075.
[line withheld: prize-candidate detail under review]
- 2026-09-30T17:55:27Z start: environment built (/opt/ckb), waiting for the S1 model on own-lead.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]

[line withheld: prize-candidate detail under review]
- own_common.py (own-lead a2a7ff6) sha256 9faed7aec465085e0e99201cdc2de6ec7fe80cfbaf97499b188243e0b7695e3d; infer.py 36a64e1a (unchanged); model bfa9f7a6; --threads 2 per lane; fresh staging dirs stage_PA / stage_PB; the r8_c11 infer checkpoint was cleared so the repro tile is recomputed.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]

[line withheld: prize-candidate detail under review]
- 2026-09-30T21:04:46Z own_common.py sha256 ddf9077087a85a7bce44139b6ea56e6ea1dbed37353c30e3a25af58ba1daf3b9 (own-lead 058d5f7); infer.py 36a64e1a unchanged; model bfa9f7a6.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]

## Verso maps (DECL-P4-26-A2, -A2-E1; BRIEF_VERSO.md 377fa355, verso_assign f3364896)
- infer_verso.py a1bd1f248cc6b49263f9a01dd7041b1123864f571b129fad643779c4ccb92b90; infer.py 36a64e1ac07eea859bb586a484300ace048e732420167f9bf77516befaccdf2e; own_common.py ddf9077087a85a7bce44139b6ea56e6ea1dbed37353c30e3a25af58ba1daf3b9; model bfa9f7a6; --threads 2 per lane.
- 2026-09-30T23:28:52Z start. Lane A: 2,14; 3,17; 4,20 (+fwd); 5,11. Lane B: 7,15; 8,18 (+fwd); 0,10; 1,13 (list order kept per lane).
- 2026-10-01T01:06Z lanes A/B died at 23:30Z on their first verso tile (own_common reads the w010-027 strip-a grid via git show origin/claude/gifted-bell-gavnl5-sib-pairs0814b, a ref not fetched here); fetched it, restarted both lanes on the full list (same order, code and options); 0 maps had been written.
- 2026-10-01T01:12:09Z verso map 20260701183124-w010-027_r2_c14 lane A png_sha256 e154fba01b55e829791447cafe2cbb6fb648b072dbec02c5d78c41c368715dd0
- 2026-10-01T01:13:05Z verso map 20260701183124-w010-027_r7_c15 lane B png_sha256 9aa805c4b0c29f2e9491c68aada042506fb8d96f70781ba1d0bd3c571c0e2edd
- 2026-10-01T01:15:32Z verso map 20260701183124-w010-027_r8_c18 lane B png_sha256 d4c0e8424ead24d49579a8f11b58807325d398dc95a361433072b7fe5838cdf4
- 2026-10-01T01:18:06Z fwd_x map 20260701183124-w010-027_r8_c18 lane B png_sha256 b690213d27090cac82c50413355bac8d568d065c65aec6a6db22b55cef6daa08
- 2026-10-01T01:19:26Z verso map 20260701183124-w010-027_r3_c17 lane A png_sha256 4254baf023dffb921aad9de8f1953228211baf92d71d95e42458db332704bd7c
- 2026-10-01T01:22:09Z verso map 20260701183124-w010-027_r4_c20 lane A png_sha256 d036befbfefae43d1d6e1f08bce846cc199d8eb8a2e73a01605edbdf6ce21b35
- 2026-10-01T01:24:55Z fwd_x map 20260701183124-w010-027_r4_c20 lane A png_sha256 6304638bd81fcdbe789bd2067f1cbd294625f5ebbf6ed5be06c81c14de4ccdb0
- 2026-10-01T01:24:58Z verso map 20260701183124-w010-027_r0_c10 lane B png_sha256 19a932f360dc155f3046498d8389a6593691dbec2781a46a985bc94a3f6dc7d4
- 2026-10-01T01:32:33Z verso map 20260701183124-w010-027_r5_c11 lane A png_sha256 394fd214785765a6c51feddbf393dc653d4e89b79498e7273f19ffd82b53b5da
- 2026-10-01T01:32:36Z verso map 20260701183124-w010-027_r1_c13 lane B png_sha256 a0093cd8dda35e26ce845ff807a4931d61cb16f80af7e9d389fb563d8d762593
