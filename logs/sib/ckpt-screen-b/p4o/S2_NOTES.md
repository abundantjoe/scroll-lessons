Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-b P4-O sub-sibling S2 notes

Assignment (SUBSIBS.md): iteration-5, row r1 c10 c11 c12 c13 c0 c1 c2 c3 c4, then row r3 in the same column order.

## Setup checks (all passed)
- Card files at commit 6288ba60: README.md, config.json, configuration_inkdetection.py and modeling_inkdetection.py. All four match their git blob oid.
- model.safetensors: 333531996 bytes, sha256 9920d4338e51d38b241cbf48392610be0519e4e19c2e9d987ccfc2e78bd3301b. This equals the catalogue LFS sha256.
- Builder start record: channels_last layout check max |logit diff| 4.17e-07.

## Bug report: p4o_tiles.py peak memory exceeds a 13.36 GiB container (not modified here)
- Event: run pid 621 (run_621.log) was OOM-killed by the memory cgroup during tile r1_c10. The kill happened after the stack read and before inference. Kernel record: anon-rss 13955908 kB, limit 14345912320 B, no swap.
- Cause (arithmetic from the code, run_tile):
  - `img` from read_stack is (Hp, Wp, 62) uint8. For Hp = Wp = pad256(8343 + 2*128) = 8704, that is 4.70 GB.
  - The next line computes norm_mean as `np.clip(img[:H, :W][m_reg], 0, 200).mean()`. The boolean index makes a copy of up to 4.58 GB (62 B per valid px). np.clip then makes a second copy of the same size.
  - The transient peak is therefore about 14 GB. This is only a logged statistic.
- Mitigation used, with no code change: a 16 GiB swapfile, `swapon /work/swapfile`. The cgroup has an unlimited memory+swap limit, so the transient peak spills to swap. The inputs, code and outputs are unchanged.
- Suggested fix for the parent, not applied here: compute norm_mean without the full copies, for example by accumulating per row band. The result is the same value.
- Relaunched as pid 907 at 2026-09-26 ~21:28Z. run_621.log is kept as the record of the killed attempt; it has no tile output.
- Retry pid 907 passed the peak: VmHWM about 13 GiB, then 5.4 GiB resident during inference. Swap in use at the check: 0 GiB (the peak fit narrowly).

## Bug report 2: p4o_tiles.py crashes after every finished tile (not modified here)
- Event: run pid 907 finished r1_c10 and wrote tiles/*_r1_c10.png and .png.json. It then exited with `TypeError: dict() got multiple values for keyword argument 'utc'`.
- Cause: `run_tile` builds `rec` with a `utc=` key and then calls `log(rec)`. `log` itself does `dict(utc=utc(), **rec)`.
- Effect on outputs: none. The png and png.json are both written before `log(rec)`. The png file sha256 equals png_sha256 in its json (1a7407fc...d3b3). The final record is missing from run_907.log, but it is in the png.json.
- Other workers: every worker using the builder stops after its first tile.
- Workaround, with no code change: the driver starts the same command again after each tile. Finished tiles are skipped (`skip` record), and a new run_<pid>.log is written per invocation. The driver continues only when a new png.json appeared and the log shows this exact TypeError. Any other failure stops it.
- Suggested fix for the parent: `log({k: v for k, v in rec.items() if k != 'utc'})`, or rename the key.
- Container restart around 2026-09-27T01:00Z: /work (venv, weights, mesh cache, full-res arrays) survived, and swap was re-enabled. r1_c11 was restarted at 01:02:48Z.

## Builder update from the parent (scheduled parent routine, 2026-09-27T01:00Z)
- The parent fixed bug 2 in b87d9dd. Its head (fd13b7e) also adds 15-min resumable checkpoints inside each tile.
- tools/sib/ckpt-screen-b/p4o_tiles.py and infer_1667.py were checked out unchanged from origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-b (fd13b7e). Both are byte-identical to parent head (git blob oids match).
- Both files are needed: head p4o_tiles.py calls card_tiling(state=, ckpt_fn=), which only head infer_1667.py accepts.
- Run 432 (old code, r1_c11) had run for about 1 min and was stopped; it produced no tile output. Relaunched with the parent code; the worker command and tile list are unchanged.

## Builder update 2 from the parent (routine at 2026-09-27T01:35Z): bounded read_stack, 4741d69
- p4o_tiles.py and infer_1667.py were checked out unchanged from the parent (4741d69). Their blob oids equal the parent's.
- Worker 710 (r1_c11) had already passed read_stack. It was stopped right after a fresh 15-min checkpoint and relaunched on the new code. It resumes from the checkpoint, so the loss is under a minute plus the stack re-read.

## Builder update 3 from the parent (DECL-P4-14-A3, routine at 2026-09-27T02:48Z): 98cd075
- tools/sib/ckpt-screen-b/ was checked out unchanged from the parent (98cd075). The directory now also contains the parent's p4o_merge.sh.
- The new norm_mean fixes bug report 1 (the 2 x 4.6 GB copies). My own check agrees the value is identical: sum <= 4.6e9 * 200 < 2^53, so the old float64 mean was also an exact integer sum.
- The worker was stopped right after a fresh 15-min checkpoint of r1_c11 and relaunched through driver v3 with the same r1 tile list (r1_c10 is skipped because it is done).

## Container stall/restart, 2026-09-27 about 02:55Z to 07:00Z
- Worker 3110 resumed r1_c11 at window 2293 (02:55:13Z) and then wrote no further checkpoint and no error.
- At 07:00Z the container showed a fresh boot (uptime 0 min), and no worker or driver was running.
- The checkpoint from 02:53:56Z (n=2293) was intact, so no computed windows were lost; about 4 h of wall time was.
- 07:01Z: swap re-enabled; driver v3 relaunched with the same r1 command. r1_c11 resumed at window 2293 (07:03:54Z).
- The builder is unchanged: p4o_tiles.py and infer_1667.py equal the parent head 03b536a.
- Check-ins are now about every 90 min, so a silent restart costs at most that much time.
