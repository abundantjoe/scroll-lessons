# p4v-15 STATUS (RULES.md DECL-P4-26-A2, tools/p4/BRIEF_VERSO.md sha256 377fa355...)
Provenance: Project HERCULES | [id removed]

- 2026-09-30T23:32:29Z start. Code sha256: infer_verso.py a1bd1f248cc6b49263f9a01dd7041b1123864f571b129fad643779c4ccb92b90; infer.py 36a64e1ac07eea859bb586a484300ace048e732420167f9bf77516befaccdf2e; own_common.py ddf9077087a85a7bce44139b6ea56e6ea1dbed37353c30e3a25af58ba1daf3b9; ckpt-screen-b p4o_tiles.py a32d7e86... infer_1667.py 29444f37... (equal to own_common CKB_SHA pins for 98cd075; files taken from origin/claude/gifted-bell-gavnl5 because 98cd075 is absent from the shallow clone). verso_assign.json f3364896... Model model_final.pth sha256 bfa9f7a62097374b93e87c7b406a9c3eba6b77dca3d9f79c10300fa0114daea5 (verified), summary.json 43e781fe... Env /opt/ckb py3.11 (torch cpu, numpy, opencv-python-headless, tifffile, imagecodecs, zarr<3, requests, scipy, pillow). Tiles new.p4v-15: w010-027 r5c1, r2c3, r8c4, r5c6, r2c8 (verso+forward each). Lanes: A = r5c1, r8c4, r2c8; B = r2c3, r5c6.
- 2026-10-01T00:18:22Z REPRO PASS: forward 20260701183124-w010-027:0,11 png_sha256 6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102 (own-lead 6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102)
- 2026-10-01T00:26:17Z lane A verso 20260701183124-w010-027_r5_c1 png_sha256 46394c2c6ad019c8e6bd0d76b202fe9fd8932aad996971b3917cfc8ab491ccad
- 2026-10-01T00:26:25Z lane B verso 20260701183124-w010-027_r2_c3 png_sha256 ff5413f882e0ae2ae233e5a97e8650f6c7f90462942bb9199c7d79444fdf74b6
- 2026-10-01T00:34:07Z lane B forward 20260701183124-w010-027_r2_c3 png_sha256 d2593c275d80005ba2671e7b9f37d3b70b17d6684fd42acae3ebbcef83ee9887
- 2026-10-01T00:34:09Z lane A forward 20260701183124-w010-027_r5_c1 png_sha256 5a869c27578ec28c92821334b634801060cd5f0caab83ebddb993079aea5c496
- 2026-10-01T00:36:43Z lane A verso 20260701183124-w010-027_r8_c4 png_sha256 d8755997e2ef3c74b0d825506f0c19a67fe74ba4c10874a5bdf311b10f6b3250
- 2026-10-01T00:39:05Z lane A forward 20260701183124-w010-027_r8_c4 png_sha256 f7cdc27e0ec9094ce36d35f5949bd1ad94489d0f01a6dcb8bb9e13db20cd2376
- 2026-10-01T00:41:49Z lane B verso 20260701183124-w010-027_r5_c6 png_sha256 0e688b327391cfb712d92cac12e9227e059ce01aa89f139fc2f9bf7cb759cb7b
- 2026-10-01T00:46:48Z lane A verso 20260701183124-w010-027_r2_c8 png_sha256 34f7fb3813570ded33c5b649ade1787a7d99a7b4b23bd50a88c425ded13c2b03
- 2026-10-01T00:49:39Z lane B forward 20260701183124-w010-027_r5_c6 png_sha256 427f95f19ca7d5ae0d24850eee09c1ac23a44927367ec9e903bb4bd19a712128
- 2026-10-01T00:57:54Z lane A forward 20260701183124-w010-027_r2_c8 png_sha256 8e47449d30f115b73b3ad69356f965ef7e1e0063f5ffe73c888ac5343293100c
- 2026-10-01T00:57:56Z end: all 10 maps pushed (5 verso + 5 forward)
