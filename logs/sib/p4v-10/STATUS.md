# p4v-10 status (RULES.md DECL-P4-26-A2; tools/p4/BRIEF_VERSO.md)
Provenance: Project HERCULES | [id removed]
Numbers only: no map, tile or CT image opened, displayed or described.

- 2026-09-30T23:32:33Z START. Code (unchanged, from origin/claude/gifted-bell-gavnl5-sib-own-lead and origin/claude/gifted-bell-gavnl5):
  infer_verso.py a1bd1f248cc6b49263f9a01dd7041b1123864f571b129fad643779c4ccb92b90
  infer.py 36a64e1ac07eea859bb586a484300ace048e732420167f9bf77516befaccdf2e
  own_common.py ddf9077087a85a7bce44139b6ea56e6ea1dbed37353c30e3a25af58ba1daf3b9
  ckpt-screen-b p4o_tiles.py a32d7e86a7bdfd5a25a5ced280976a2dfa55f30c8b866a3ae149d74b729ec371 (98cd075 content via fc5442c; 98cd075 not in shallow clone)
  BRIEF_VERSO.md 377fa35570892e26222f057de60306b4f1b4c204c08d5b4c0ffae5a6f376af22, verso_assign.json f3364896476b5ab8f1ef2218236877067852f93ef44718b95e3a866955941d6a
  model_final.pth bfa9f7a62097374b93e87c7b406a9c3eba6b77dca3d9f79c10300fa0114daea5 (= bfa9f7a6..., verified)
  env /opt/ckb: python 3.11, torch 2.14.1+cpu, zarr<3, pillow
- Tiles (new.p4v-10, verso = forward list): w010-027 0,1; 6,2; 3,4; 0,6; 6,7. Lanes A (pos 0,2,4) and B (pos 1,3).
- 2026-09-30T23:40:55Z REPRO PASS: w010-027 r0c11 forward png_sha256 6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102 (file 6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102) vs own-lead 6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102
- 2026-09-30T23:48:32Z verso 20260701183124-w010-027_r0_c1 lane A png_sha256 6c1bcbdf688495826fd0cf65059166416e7f867c3237566226399e4c76bd893c
- 2026-09-30T23:48:34Z verso 20260701183124-w010-027_r6_c2 lane B png_sha256 9057e6a5653a41c783a575443aa8c4d473a611c226e0a5445d1c91b64d3bbcde
- 2026-09-30T23:56:07Z fwd_x 20260701183124-w010-027_r0_c1 lane A png_sha256 809a9c126a47bc7b47b9edfc75a11ca3998e9a4a13680679b9ca8fc36b6f93ea
- 2026-09-30T23:56:27Z fwd_x 20260701183124-w010-027_r6_c2 lane B png_sha256 a4fa8b3ea94a64be036341ea6a6fcc81fd9616d8b349dc111d51d8e56bfcea65
- 2026-10-01T00:03:35Z verso 20260701183124-w010-027_r0_c6 lane B png_sha256 5fc5c1fa3cbcd184d3075d55f37ce0705cf1feb0d8d4f7ee70dc1209c73ff879
- 2026-10-01T00:03:37Z verso 20260701183124-w010-027_r3_c4 lane A png_sha256 8aae867b84c20f725a2a8a88a70263ea141a64dcafd45564da4bb696280dbeef
- 2026-10-01T00:10:44Z fwd_x 20260701183124-w010-027_r0_c6 lane B png_sha256 564720bc4f24355f8d91eb662b336f03c6061d15bfd8f530a6509b12b30e93da
- 2026-10-01T00:11:15Z fwd_x 20260701183124-w010-027_r3_c4 lane A png_sha256 c9594e36322da82f096b494f1950bc66fb24afb4e017331e78cd84a783a8c5a4
- 2026-10-01T00:20:27Z verso 20260701183124-w010-027_r6_c7 lane A png_sha256 ad7d82f12d5d9e26ee391bc14c6260c179ca9e0ca7108264f175d89ebc9ad903
- 2026-10-01T00:29:25Z fwd_x 20260701183124-w010-027_r6_c7 lane A png_sha256 5ee9134e9080ec1dca2056a6f404e5b4d0dd89f0556d71776a62ec298c7d3eb6
- 2026-10-01T00:29:27Z END: verso 5/5, forward 5/5 pushed
