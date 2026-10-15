Provenance: Project HERCULES | owner the owner | [id removed]

# o5w5 status (DECL-P4-14-A3)

Task: one PHerc.1667-iteration-5 P4-O tile, strip 20260701183124-w010-027, r1 c15 (title zone; e2-eligible, valid_fraction 1.0).
Pipeline: ckpt-screen-b p4o/WORKER.md at 6aa0345, code commit 98cd075 (tools/sib/ckpt-screen-b/ checked out from it, not re-committed here).
- sha256 verified: p4o_tiles.py a32d7e86...c371, infer_1667.py 29444f37...b12, fetch.py e5a3cb8f...860 (all match WORKER.md).
- Checkpoint model.safetensors sha256 9920d4338e51d38b241cbf48392610be0519e4e19c2e9d987ccfc2e78bd3301b, 333,531,996 bytes: fetch.py catalogue check verified=true and independent sha256sum match. Card/code files git-oid ok.
- Order: forward only (slices 23-84 ascending, reverse_layers False) as WORKER.md prescribes; layout max |logit diff| 4.17e-7.
- Started 2026-09-27T02:42:45Z (process start log 02:43:10Z), 4356 windows, builder ETA 3.99 h, 4 threads.
- Layout: WORKER.md's layout re-rooted under logs/sib/o5w5/ as instructed: p4o/PHerc.1667-iteration-5/{tiles/<file>.png, tiles/<file>.png.json, run_<pid>.log}, p4o/fleet/o5w5.json; plus o5w5_r1_c15.json (tile, code commit, ckpt sha256, orders, start/end utc, runtime). progress.jsonl = 30-min progress checkpoints.
- Note: SUBSIBS.md assigns r1 c15 also to S3; the orchestrator assigned it here. Output should be bit-comparable (png_sha256) with S3's if both finish.
- No tile/PNG/CT pixel was opened or viewed.

## DONE 2026-09-27T05:40:46Z
Tile done; outputs, fleet/o5w5.json and o5w5_r1_c15.json pushed.
