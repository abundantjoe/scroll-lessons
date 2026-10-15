# p4v-07 STATUS (RULES.md DECL-P4-26-A2, tools/p4/BRIEF_VERSO.md sha256 377fa35570892e26222f057de60306b4f1b4c204c08d5b4c0ffae5a6f376af22)
Provenance: Project HERCULES | [id removed]

2026-09-30T23:29:40Z start. Code unchanged: infer_verso.py a1bd1f248cc6b49263f9a01dd7041b1123864f571b129fad643779c4ccb92b90, infer.py 36a64e1ac07eea859bb586a484300ace048e732420167f9bf77516befaccdf2e, own_common.py ddf9077087a85a7bce44139b6ea56e6ea1dbed37353c30e3a25af58ba1daf3b9; ckpt-screen-b p4o_tiles.py a32d7e86... infer_1667.py 29444f37... (= 98cd075 pins). model_final.pth sha256 bfa9f7a62097374b93e87c7b406a9c3eba6b77dca3d9f79c10300fa0114daea5 (verified), summary.json 43e781fea9710a31c37188129271b133221a7126fed47720c32362971173881c. Env /opt/ckb py3.11 torch cpu 2.14.1+cpu, zarr 2.18.7, pillow.
Tiles (new.p4v-07): verso+forward 6,0; 3,2; 0,4; 6,5; 3,7 (w010-027). Lane A: 6,0 / 0,4 / 3,7. Lane B: 3,2 / 6,5.
2026-09-30T23:29:56Z REPRO FAIL: 20260701183124-w010-027:0,11 forward png_sha256  (file ) vs own-lead 6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102
2026-09-30T23:31:32Z VOID the REPRO FAIL line above: my driver bug. infer.py stopped before making any map (git ref origin/claude/gifted-bell-gavnl5-sib-pairs0814b not fetched), and the driver logged an empty hash as FAIL. No repro map existed. The gate is re-run below, and only the REPRO line after this one counts.
2026-09-30T23:41:01Z repro forward map 20260701183124-w010-027_r0_c11 png_sha256=6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102
2026-09-30T23:41:04Z REPRO PASS (gate): 20260701183124-w010-027:0,11 forward png_sha256 6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102 (file 6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102) vs own-lead 6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102
2026-09-30T23:48:48Z verso map 20260701183124-w010-027_r6_c0 png_sha256=c63b2d81c76d99f553ba6a15711cfaec4c7caf44408ebca4eba95068485e3dfc
2026-09-30T23:49:55Z verso map 20260701183124-w010-027_r3_c2 png_sha256=32c538c14f81fb0e0e2e43946121e61d4009b0f976c98bcdc4c859d9ff654e4a
2026-09-30T23:56:35Z forward map 20260701183124-w010-027_r6_c0 png_sha256=24d6a23fb0f1488438f6e127faaeb5c7faf6a0c016f70889426cf14df6e82706
2026-09-30T23:58:53Z forward map 20260701183124-w010-027_r3_c2 png_sha256=517bfa5e39f8fb044ac19915d2537c05f0b1e9d1428a57f01c8aecdf84d4c8f6
2026-10-01T00:05:43Z verso map 20260701183124-w010-027_r0_c4 png_sha256=57c3d15432ef99a44b5fd4a6cbc2076b14b45752fda9ab6cc5b4386a06bb32b7
2026-10-01T00:07:49Z verso map 20260701183124-w010-027_r6_c5 png_sha256=3fd2e96d4ff06edbe77403b2dc0e608bcf1d29a4285f08ad462842d6883be4eb
2026-10-01T00:14:54Z forward map 20260701183124-w010-027_r0_c4 png_sha256=4e6a43d7b9b8cce0b5e83a9bcfc835c9bf2d24d9a0609403fd6eb137718679f3
2026-10-01T00:16:59Z forward map 20260701183124-w010-027_r6_c5 png_sha256=61f4b4555378738bfbb9777960ed215132e0ac7317a03d83378aef70922c95bc
2026-10-01T00:25:12Z verso map 20260701183124-w010-027_r3_c7 png_sha256=d552873899ea30bac543c307fff5251ba10f1b870a05fc93b0c633b98bdeb849
2026-10-01T00:35:39Z forward map 20260701183124-w010-027_r3_c7 png_sha256=ed17871697e358e1e0ea753829d62282eac005e5749df4b8dab31a7fb5b9db5f
2026-10-01T00:36:40Z end: all 5 verso + 5 forward maps pushed (verso records order=reverse; every png_sha256 equals its file hash). Code, model and lists unchanged (no diff against the source branches).
2026-10-01T01:03:30Z extra (DECL-P4-26-A2-E3, verso_assign_x2.json f11f3f79... at 9174af5f): extra.p4v-07 = verso+forward 7,6, lane A. Code/model hashes re-checked unchanged.
2026-10-01T01:13:24Z verso map 20260701183124-w010-027_r7_c6 png_sha256=8c8111e2d6d610169ec6af49836a2cb8f260d6078113d34dc546eb886cf84fec
2026-10-01T01:22:49Z forward map 20260701183124-w010-027_r7_c6 png_sha256=99d03188f37a70d8df6c98530256f550dcc3c9fb00407e43a61c0a93e7823309
2026-10-01T01:23:44Z end extra: 7,6 verso + forward pushed (verso order=reverse; png_sha256 = file hash for both). All p4v-07 lists complete.
