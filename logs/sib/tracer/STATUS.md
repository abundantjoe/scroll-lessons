Provenance: Project HERCULES | owner the owner | [id removed]

# STATUS sib/tracer (2026-09-26T18:46:54Z)

T0: DONE up to declaration; awaiting orchestrator (unchanged).
P4-N (DECL-P4-13), geometry only, no image viewed:
- Headroom finding: the official w010-027 top edge in c9-c15 is at z 172.3-172.8 mm, and volume 20260411134726 ends at z = 75783 vox = 181.9 mm. At most about 9.2 mm of upward extension is possible, not 1-2 cm.
- Built: c5 (c4 + gate_fix_resume_points, default off; the T0 presets are unaffected), local m7-L2 crop (882 chunks, sha256 manifest), normal grids, seed patches (real, holdout), metrics.py (seam, selfcross, neighbour winding, FLAT-2 SLIM, holdout recovery).
- Official mesh vs m7 L2: 92 % of vertices within 1.5 L2 vox of the prediction, 98 % within 3.
- DONE: P4-N extension (2.1 mm, c9-c15), see p4n/REPORT.md. Per-metric verdicts: seam FAIL (2.40, equal to the official self-baseline), self-intersection PASS, neighbour winding FAIL (98.1 %, official 97.5 %), flattening PASS.
- No jobs running.
2026-09-30T03:58:13Z FL PHerc0175A (DECL-FL-1): pipeline launched (tools/sib/fl-pherc0175a/pipeline.sh --loop; no organizer segments, auto-grow 4 at m7 L1); P4 work complete.
2026-09-30T05:17:35Z FL PHerc0175A: DONE, 0 tiles (4 auto-grown segments 0.0-0.30 cm2 < 16 cm2 at m7 L1; see logs/sib/fl-pherc0175a/REPORT.md)
2026-09-30T17:55:13Z S1 map helper (DECL-P4-25-A10-A1) start: brief sha256 23209537578c5c5a..., assign 4f77b04dc55a837a...; infer.py 36a64e1ac07eea859bb586a484300ace048e732420167f9bf77516befaccdf2e, own_common.py f8850058e53e29ddab177d0a1aac85dece6391360e3b2679b7d98fc36ab0eb8e; 6 tiles (repro 1, pool 1, rest 4)
2026-09-30T18:04:49Z S1 map env: added pillow to /opt/ckb (own_common.display_png imports hercules.display.builder -> PIL; not in the brief's package list); both lanes relaunched
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
2026-09-30T18:20:40Z S1 maps: all 6 assigned tiles pushed (tracer)
[line withheld: prize-candidate detail under review]
2026-09-30T18:22:42Z S1 maps extra (DECL-P4-25-A10-A2, assign v3 sha256 1115aada660fd1bc...): 4 tiles, 4,7 first
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
2026-09-30T18:38:32Z S1 maps: all 10 assigned tiles pushed (tracer)
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
2026-09-30T18:54:12Z S1 maps: all 2 assigned tiles pushed (tracer)
2026-09-30T18:54:46Z S1 duplicates pushed; both byte-identical to own-lead's (r3_c6 6c4b21599133fb2e..., r2_c6 3dd9773d110b1206...). Done; no waiters remain.
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
[line withheld: prize-candidate detail under review]
2026-09-30T23:28:45Z verso maps (DECL-P4-26-A2) start: brief 377fa35570892e26..., infer_verso.py a1bd1f248cc6b49263f9a01dd7041b1123864f571b129fad643779c4ccb92b90, infer.py 36a64e1ac07eea859bb586a484300ace048e732420167f9bf77516befaccdf2e, own_common.py ddf9077087a85a7bce44139b6ea56e6ea1dbed37353c30e3a25af58ba1daf3b9; 8 verso + 3 forward
2026-09-30T23:30:00Z verso: first launch failed before inference (own_common.load_valid needs origin/...-sib-pairs0814b e2 manifest for w010-027; branch fetched); relaunched
2026-09-30T23:32:22Z verso: 2nd launch lane B read the w010-027 mesh while lane A was still downloading it (x.tif sha mismatch, same dir); after lane A's download the mesh sha is c304cdfd... = e2 manifest; runner restarted with both lanes
2026-09-30T23:39:06Z verso map 20260701183124-w010-027_r0_c14 pushed (lane B, png sha256 25eea68443c91012...)
2026-09-30T23:39:08Z verso map 20260701183124-w010-027_r5_c15 pushed (lane A, png sha256 da44f7d68319f3e1...)
2026-09-30T23:47:18Z verso map 20260701183124-w010-027_r6_c18 pushed (lane A, png sha256 c63e54a3c2e187d9...)
2026-09-30T23:47:20Z verso map 20260701183124-w010-027_r1_c17 pushed (lane B, png sha256 77232cb6640876f9...)
2026-09-30T23:49:45Z verso map 20260701183124-w010-027_r2_c20 pushed (lane A, png sha256 50a695adf7d4deb0...)
2026-09-30T23:52:33Z forward map 20260701183124-w010-027_r2_c20 pushed (lane A, png sha256 48a84663d38cd9ac...)
2026-09-30T23:55:50Z verso map 20260701183124-w010-027_r7_c9 pushed (lane B, png sha256 2fba68f5e1fe7a7a...)
2026-10-01T00:00:56Z verso map 20260701183124-w010-027_r3_c11 pushed (lane A, png sha256 e40498feaa35c425...)
2026-10-01T00:03:28Z verso map 20260701183124-w010-027_r8_c12 pushed (lane A, png sha256 6b96609683d1b282...)
2026-10-01T00:04:14Z forward map 20260701183124-w010-027_r7_c9 pushed (lane B, png sha256 d17f45c98d64c38d...)
2026-10-01T00:06:14Z forward map 20260701183124-w010-027_r8_c12 pushed (lane A, png sha256 3df4e0be1dccbfc3...)
2026-10-01T00:06:16Z verso maps: all 8 verso tiles and their forward maps pushed (tracer)
2026-10-01T00:26:37Z verso extra (DECL-P4-26-A2-E2, verso_assign_x.json extra.tracer): 4 verso + 2 forward
2026-10-01T00:35:05Z verso map 20260701183124-w010-027_r5_c12 pushed (lane A, png sha256 7910def52f3cd986...)
2026-10-01T00:35:07Z verso map 20260701183124-w010-027_r6_c4 pushed (lane B, png sha256 bfd6dd7333c55913...)
2026-10-01T00:42:56Z verso map 20260701183124-w010-027_r0_c11 pushed (lane A, png sha256 d77f7557b46ef8d0...)
2026-10-01T00:43:36Z forward map 20260701183124-w010-027_r6_c4 pushed (lane B, png sha256 9263ade62b3269db...)
2026-10-01T00:52:46Z verso map 20260701183124-w010-027_r4_c9 pushed (lane A, png sha256 1bf3412085adf7d3...)
2026-10-01T01:01:55Z forward map 20260701183124-w010-027_r4_c9 pushed (lane A, png sha256 d95ffb88ada5ec18...)
2026-10-01T01:01:57Z verso maps: all 4 verso tiles and their forward maps pushed (tracer)
2026-10-01T02:13:09Z housekeeping for FL2: deleted regenerable scratch /work/own/infer + infer_verso (S1/verso inference checkpoints; all maps pushed), /work/ng1203 (PHerc1203 normal-grid band copy for the undeclared T0; re-syncable from S3), uv cache
