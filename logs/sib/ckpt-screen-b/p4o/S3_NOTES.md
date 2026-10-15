Provenance: Project HERCULES | owner the owner | [id removed]

# S3 notes (iteration-5, r1 then r3: c14 c15 c16 c17 c5 c6 c7 c8 c9)

- 2026-09-26T21:22Z setup: cards and model.safetensors for iteration-5 verified against data/catalogue/checkpoints.json (weights sha256 9920d433...301b, 333531996 bytes).
- 2026-09-26T21:23Z first run (pid 646, run_646.log) started r1 c14 (4356 windows); the process was killed (exit 137) at 21:25:04Z, before any window output. No tile was written. Cause not established from the logs: no OOM entry in the kernel log; 15 GB RAM, process at ~0.5 GB when last sampled. Most likely the process was reaped together with the launching shell; relaunched detached (setsid).
- 2026-09-27T01:0xZ parent instruction: builder log() crash (duplicate utc key, parent b87d9dd). Synced tools/sib/ckpt-screen-b/p4o_tiles.py AND infer_1667.py from origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-b (fd13b7e) - both files are needed, since the current p4o_tiles.py passes state/ckpt_fn to infer_1667.card_tiling (15-min resumable checkpoints). Synced bytes: p4o_tiles.py sha256 199937ad6ef3e1b9ebce5a439633d232281eaf9d6ca4cdb198aae2342762fdaf, infer_1667.py sha256 29444f37ffb43669b1842570b123a5f791dd9d0f8aa7a4a07b8f776ed148cb12. No local edits to either file.
- 2026-09-27T01:04Z relaunch (run_3386.log) with the synced builder: killed again (exit 137) ~100 s after start, same point (after the tile-start log line, inside read_stack).
- 2026-09-27T01:08Z diagnostic run (run_3596.log, tile 1,14 only) with an RSS/cgroup sampler every 5 s (S3_mem_trace_r1c14.txt): RSS rises ~200 MB/s from 1.4 GB to 13.2 GB during read_stack (no further log line) and the process is killed. Primary evidence: this container's memory cgroup limit is 14,345,912,320 bytes, memory.max_usage_in_bytes = the limit, memory.oom_control oom_kill = 3 (one per attempt), failcnt 2164. So all three S3 deaths are cgroup OOM kills, not the log() bug and not the shell.

## BUG (builder, not fixed here: S3 may not modify tools/sib/ckpt-screen-b/*.py)
p4o_tiles.read_stack peak memory exceeds a 14.3 GB cgroup on r1 c14 (4,624 level-0 chunk jobs, all within the array). Two holders: the (8704, 8704, 62) uint8 image = 4.70 GB, and `ex.map(get_chunk, jobs)` which submits all 4,624 jobs at once, so fetched chunks (62 x 128 x 128 = 1.02 MB each, plus requests-side copies) accumulate ahead of the in-order consumer; upper bound 4.70 GB of payload alone. The measured peak (>13.2 GB RSS) is above img + payload, so response-side copies add several GB more; the exact split was not measured. Parent tile r0 c10 (3,945 chunks read, 611 missing) completed on the parent's container; whether it has a larger limit is not known to S3.
Proposed patch (output-identical: same job order, same chunk records hash, same image bytes): bound the in-flight work in read_stack, e.g.

    B = 256
    with cf.ThreadPoolExecutor(24) as ex:
        for i in range(0, len(jobs), B):
            part = jobs[i:i + B]
            for (cy, cx), (d, rec) in zip(part, ex.map(lambda j: get_chunk(*j), part)):
                ...  # loop body unchanged

and optionally `del r` / copy only the needed slab. Validation: rerun r1 c14 read_stack with the sampler (peak RSS should be ~img + <0.5 GB), and compare chunk_records_sha256 and the tile png_sha256 against any worker that completes the same tile unpatched.
Status: S3 is blocked on r1 until the parent ships a builder fix (or runs S3's tiles on a larger container). No tile was produced by S3; nothing viewed.

## CORRECTION (2026-09-27T01:45Z): the OOM is NOT in read_stack; my earlier attribution was wrong
- 01:37Z relaunch with the bounded read_stack (parent 4741d69, p4o_tiles.py sha256 1ccf5760...bbd): killed again (exit 137; cgroup oom_kill counter 0 -> 1), peak sampled RSS 13,386,604 kB (S3_mem_trace_r1c14_batched.txt). The batching is harmless (output-identical) but did not fix it.
- Stage-by-stage diagnostic (scratch script importing the unmodified builder, r1 c14, numbers only): after load_valid 59 MB; after canvas_mask 130 MB; after read_stack 4,633 MB RSS (high-water 4,674 MB), img 4.697 GB; mask true px 73,942,801 (r1 c14 is ~100% mesh-valid). Then `img[:H, :W][m_reg]` (first step of the norm_mean line in run_tile) alone takes RSS to 9,005 MB (high-water 10,133 MB): a 4.584 GB boolean-index copy. The same line's `np.clip(...)` makes a second 4.58 GB copy -> ~13.8 GB + model/torch > the 14.3 GB cgroup. That matches the kill point (after the tile-start line, before any window) and the measured peak. Tiles with lower valid fraction (e.g. r0 c10, 0.855) stay just under the limit, which is why they completed elsewhere.
- BUG location: p4o_tiles.run_tile, line `norm_mean = float(np.clip(img[:H, :W][m_reg], 0, 200).mean() / 255.0) if m_reg.any() else None`.
- Proposed fix, bit-identical value (not applied; S3 may not modify the builder). np.mean of the uint8 selection accumulates in float64; every partial sum is an integer <= 200 * 7.4e7 * 62 < 2^53, so it equals the exact integer sum, and the result is the same correctly rounded sum/n. A row-blocked exact integer sum therefore reproduces it bit for bit without the copies:

      if m_reg.any():
          s = 0
          for a in range(0, H, 512):
              blk = np.minimum(img[a:min(a + 512, H), :W], 200)     # uint8; clip(0,200) == minimum(.,200) for uint8
              s += int(blk[m_reg[a:a + 512]].sum(dtype=np.int64))
          norm_mean = float(np.float64(s) / np.float64(int(m_reg.sum()) * img.shape[2]) / 255.0)   # 62 slices per px
      else:
          norm_mean = None

  Validation: on a small tile, assert the new norm_mean == the old expression exactly (==, not isclose); on r1 c14, sampled peak RSS should stay near img (4.7 GB) + <0.3 GB before inference.
- S3 is blocked again until this fix is on the parent branch. Nothing viewed; no tile produced.
- Patch check (2026-09-27T01:50Z, synthetic random uint8 arrays only, 3 shapes up to 8599 x 1200 x 62 with a 97% random mask): old expression == patched value exactly in 3/3. The first draft of the patch divided by the pixel count instead of pixel count x 62 slices and failed this check; the divisor above is the corrected one.

## 2026-09-27 runs with parent 98cd075 (masked_norm_mean)
- 02:49Z r1 relaunch (run_446.log), list "1,14;1,17;1,5;1,6;1,8;1,9" (DECL-P4-14-A3). Sampled RSS through read_stack, norm_mean and the start of inference (8 min, S3_mem_trace_r1c14_98cd075.txt): peak sampled 6,711,760 kB, VmHWM 6,818,616 kB (was >13.2 GB and OOM before the fix); the process was alive and inferring at 02:57Z. The OOM is resolved.
- The container was then reclaimed and restored at 06:50:21Z with its disk as of ~02:57Z: the r1 c14 process was gone, with no tile and no resume checkpoint (the first 15-min checkpoint falls after the restore point). About 4 h of CPU lost. Pattern: the container survived while a harness-tracked background task was running (21:23-01:00Z) and was reclaimed in the gaps without one (~01:40Z and ~02:57Z). Mitigation: the driver now runs as a harness-tracked background task for its whole life.
- 06:50Z DECL-P4-14-A4: r3 list is now "3,14;3,17;3,5;3,6;3,7;3,8;3,9" (r3 c15, c16 taken by other workers).

## 2026-09-27T07:01Z stop (orchestrator ruling P4-O-STAGE-O2S1-RESULT, RULES.md on origin/claude/gifted-bell-gavnl5; parent STATUS.md 07:00Z)
- Ruling: iteration-5 failed its known-text gate; start no new tile; finish only a tile more than half done.
- S3 state at the ruling: r1 c14 (pid 476, run_476.log) about 9 min into a ~4 h tile (4,356 windows), no resume checkpoint written yet, so done fraction < 0.1, far below 0.5. Worker and driver killed at ~07:02Z. No new tile started.
- Outcome: S3 produced 0 tiles for iteration-5 (no tiles/*.png or *.png.json on this branch; S3_progress.jsonl never created). Losses: 3 cgroup OOM kills (builder bugs, both fixed upstream: 4741d69, 98cd075) and 1 container reclaim/restore (~4 h of CPU). No manifest.json written (parent's task).
- Integrity: no issues. No tile, map, PNG or CT pixels were opened, viewed or described (numbers and hashes only; the only arrays inspected were synthetic random test arrays); no seal, *.age or /srv/scorer touched; no weights or .npy in git; writes only under logs/sib/ckpt-screen-b/ and tools/sib/ckpt-screen-b/ (the tools files are byte copies of the parent's commits, no local edits); pushed only to claude/gifted-bell-gavnl5-sib-ckpt-screen-b-s3.
