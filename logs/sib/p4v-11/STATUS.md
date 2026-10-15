# p4v-11 STATUS (RULES.md DECL-P4-26-A2, brief tools/p4/BRIEF_VERSO.md sha256 377fa355...)
Provenance: Project HERCULES | [id removed]

- 2026-09-30T23:32:23Z start. Code sha256: infer_verso.py a1bd1f248cc6b49263f9a01dd7041b1123864f571b129fad643779c4ccb92b90; infer.py 36a64e1ac07eea859bb586a484300ace048e732420167f9bf77516befaccdf2e; own_common.py ddf9077087a85a7bce44139b6ea56e6ea1dbed37353c30e3a25af58ba1daf3b9; ckpt-screen-b @98cd075. verso_assign.json f3364896476b5ab8f1ef2218236877067852f93ef44718b95e3a866955941d6a.
- model_final.pth sha256 bfa9f7a62097374b93e87c7b406a9c3eba6b77dca3d9f79c10300fa0114daea5 (verified); summary.json 43e781fea9710a31c37188129271b133221a7126fed47720c32362971173881c. /opt/ckb: torch 2.14.1+cpu, zarr 2.18.7, pillow.
[line withheld: prize-candidate detail under review]
- 2026-09-30T23:32:39Z SETUP ERROR, not a repro result: infer.py stopped before inference because origin/claude/gifted-bell-gavnl5-sib-pairs0814b was not fetched (git show exit 128); no map was produced. Retracted by the next line.
- 2026-10-01T00:14:56Z correction: the line above replaces an earlier automatic 'REPRO FAIL (infer.py error)' that the runner wrote for this setup error (commit e9b5aaf). The repro gate had not run; it runs now after fetching pairs0814b, devloop and ckpt-screen-b-s1..s3.
- 2026-10-01T00:24:55Z REPRO PASS: forward 20260701183124-w010-027_r0_c11 png_sha256 6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102 (file 6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102) vs own-lead 6954db7da54cb2bb818842042b789c974bd908fc446a4902de4ee70d6f534102
- 2026-10-01T00:34:43Z verso 20260701183124-w010-027_r1_c1 lane A png_sha256/order bba3d933d1687cfc5df8107255db214558fc9d440e65dd5b8619497735fe1f87 reverse
- 2026-10-01T00:34:43Z verso 20260701183124-w010-027_r7_c2 lane B png_sha256/order 63cf32f4c2a008b15118d239dbce52c03246deaad88861db8d4b2f1d3c3f8bf5 reverse
- 2026-10-01T00:44:35Z fwd_x 20260701183124-w010-027_r7_c2 lane B png_sha256/order 11d14af3e6ce28ec17d165d17e3ca5fab4bb929d6f71199ea55ff690a8d8fb77 forward
- 2026-10-01T00:44:36Z fwd_x 20260701183124-w010-027_r1_c1 lane A png_sha256/order c2b190c0c2665f4da5224fae4bfb88590b4ece67695e4a59fc81fe8e9bc31791 forward
- 2026-10-01T00:54:24Z verso 20260701183124-w010-027_r4_c4 lane A png_sha256/order 8650b3d08e789feecd249fdce6f838f35208182e1d01c94b3e2db1f6876e99ab reverse
- 2026-10-01T00:54:25Z verso 20260701183124-w010-027_r1_c6 lane B png_sha256/order f462a0e8ba3d076a69f4e10703c3b3f10ba30b35f6ffc37f8adcb0c15d74f789 reverse
- 2026-10-01T01:04:19Z fwd_x 20260701183124-w010-027_r4_c4 lane A png_sha256/order 495208990f65058a6ee91ebdc4f364be110cdb11688324d23748e392bc83ca10 forward
- 2026-10-01T01:04:21Z fwd_x 20260701183124-w010-027_r1_c6 lane B png_sha256/order bd4d020edc9d513ae96339a18c4f8b9277a9b6125c3670aebbe5fd5d46fbed70 forward
- 2026-10-01T01:16:11Z verso 20260701183124-w010-027_r7_c7 lane A png_sha256/order 1acaf82f3b8601a8653ac82bd53809ccfd676fb98bfdecdd04c0c533b0d6f4ae reverse
- 2026-10-01T01:27:56Z fwd_x 20260701183124-w010-027_r7_c7 lane A png_sha256/order 351aa0a9a80d7ef87e0c9437cb0ba2ffcb1ad7b497da7e983a23c35a42212b06 forward
- 2026-10-01T01:27:58Z lanes finished
