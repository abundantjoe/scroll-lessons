Provenance: Project HERCULES | owner the owner | [id removed]

# p4-excl STATUS (2026-09-26T19:57Z)

| file | strip | tiles | flagged, npz points | flagged, all vertices | labelled_adjacent | state |
|---|---|---|---|---|---|---|
| excl_a.json | w010-027 (P4-B) | 160 | 120 | 120 | union 120 | v2 final |
| excl_b.json | w028-037 (P4-B) | 171 | 138 | 139 | union 139 | v2 final |
| excl_d_b.json | 20260623142658-w028-037 (P4-D, M2b) | 106 | 106 | 106 | 106 (union) | final |
| excl_d_a.json | 20260623141924-w010-027 (P4-D M2a = E1 grid) | 100 | 100 | 100 | 100 (union) | final |
| tile_w010-027_r6_c4_allvertex.json | w010-027 r6_c4 | 1 | - | 4.967 mm | false | final |

Flag changes, npz -> all vertices: w028-037 r6_c15 (1.342 -> 1.188 mm, becomes adjacent). No other changes in any strip. The only unflagged tile below 1.30 mm (w028-037 r6_c7, 1.254 mm) is certified >= 1.24695 mm by dense sampling.
Rule: labelled_adjacent = min_mm < 1.2; exact point-to-triangulated-surface distance (CORR-RETRACE-RULE form b).

## DECL-P4-21 / DECL-P4-23 (2026-09-27T10:57Z)
- label_fractions.json: 66 strip-a tiles (w010-027 r0-r5 c9-c19); per segment and any-segment coverage and ink fractions. Col. -1 (c11-c13 r0-r1) any-segment coverage 0.051-0.289, ink of covered 0.191-0.340. c14-c19: coverage <= 0.000972, ink of tile <= 0.000579.
- p4own/T_cert.json + T_mask_*.npz: T certified; independent check all pass (T_cert_check.json).
- p4own/labels/ + labels.json: 229 T shards (x4, n_sub 1), 37166343 covered px, 9404274 ink px; never any X pixel.
- p4own/colm1_auc_S1.json: col. -1 pixel AUC of S1 = 0.9781 pooled (per tile 0.959-0.987; covered 4.9-28 % of blocks). S2 = 0.9769 pooled (per tile 0.963-0.986; colm1_auc_S2.json). Pending: S3, NULL (same code).


## S1 map helper (DECL-P4-25-A10 / -A10-A1; BRIEF_S1MAP.md sha256 23209537578c5c5a3e676038bddc4b47b8bb1c1dc81abbd26f956b1425b5c17e; assignment v2 sha256 4f77b04dc55a837a973a97f8f7d4e816c049a7f05ae90ba4f916c9468d0eeab0)
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
2026-09-30T18:38:33Z end: all assigned tiles processed
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
2026-09-30T19:03:13Z end: all assigned tiles processed
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
2026-09-30T22:57:14Z DECL-P4-23 item 6(c) col. -1 pixel AUC (same 3,989,840 covered x4 px, 942,468 ink): S1 0.9781, S2 0.9769, NULL (label-deranged) 0.5335 (per tile 0.502-0.566). The control is near chance, so the S-arm AUCs reflect learned ink, not a pipeline artefact. S3 arrays not yet present.
2026-09-30T23:28:25Z Verso job start (DECL-P4-26-A2, -E1; BRIEF_VERSO sha256 377fa355...; verso_assign sha256 f3364896...). infer_verso.py a1bd1f248cc6b49263f9a01dd7041b1123864f571b129fad643779c4ccb92b90; infer.py 36a64e1ac07eea859bb586a484300ace048e732420167f9bf77516befaccdf2e; own_common.py ddf9077087a85a7bce44139b6ea56e6ea1dbed37353c30e3a25af58ba1daf3b9. List: 8 verso (w010-027 3,14 8,15 4,17 0,19 5,20 1,10 6,11 2,13), forward 8,15 and 5,20.
2026-09-30T23:33:03Z verso S1 map 20260701183124-w010-027_r8_c15 (lane B)
2026-09-30T23:35:27Z fwd S1 map 20260701183124-w010-027_r8_c15 (lane B)
2026-09-30T23:37:09Z verso S1 map 20260701183124-w010-027_r3_c14 (lane A)
2026-09-30T23:42:40Z verso S1 map 20260701183124-w010-027_r4_c17 (lane B)
2026-09-30T23:43:31Z verso S1 map 20260701183124-w010-027_r0_c19 (lane A)
2026-09-30T23:44:30Z verso S1 map 20260701183124-w010-027_r5_c20 (lane B)
2026-09-30T23:46:18Z fwd S1 map 20260701183124-w010-027_r5_c20 (lane B)
2026-09-30T23:50:55Z verso S1 map 20260701183124-w010-027_r1_c10 (lane A)
2026-09-30T23:53:51Z verso S1 map 20260701183124-w010-027_r6_c11 (lane B)
2026-09-30T23:58:59Z verso S1 map 20260701183124-w010-027_r2_c13 (lane A)
2026-09-30T23:59:01Z verso list processed (see lanes); failures after retry: 0
2026-10-01T00:26:51Z Verso EXTRA list start (DECL-P4-26-A2-E2; verso_assign_x sha256 a3a7083d...; extra.p4-excl): verso w010-027 3,6 6,12 1,11 5,9; forward 3,6 and 5,9. Same code (infer_verso a1bd1f24, infer 36a64e1a, own_common ddf90770), model bfa9f7a6, options.
2026-10-01T00:34:44Z verso S1 map 20260701183124-w010-027_r3_c6 (lane A)
2026-10-01T00:36:07Z verso S1 map 20260701183124-w010-027_r6_c12 (lane B)
2026-10-01T00:42:17Z fwd S1 map 20260701183124-w010-027_r3_c6 (lane A)
2026-10-01T00:43:40Z verso S1 map 20260701183124-w010-027_r1_c11 (lane B)
2026-10-01T00:50:56Z verso S1 map 20260701183124-w010-027_r5_c9 (lane A)
2026-10-01T00:59:39Z fwd S1 map 20260701183124-w010-027_r5_c9 (lane A)
2026-10-01T00:59:41Z verso list processed (see lanes); failures after retry: 0
2026-10-01T01:03:55Z Verso EXTRA2 (DECL-P4-26-A2-E3; verso_assign_x2 sha256 f11f3f79...; extra.p4-excl): verso w010-027 3,17; no forward. Same code, model, options.
2026-10-01T01:17:44Z verso S1 map 20260701183124-w010-027_r3_c17 (lane A)
2026-10-01T01:17:47Z verso list processed (see lanes); failures after retry: 0
