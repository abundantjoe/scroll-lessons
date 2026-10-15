# own-lead STATUS (DECL-P4-23, P4-OWN)
Updated: 2026-09-27 ~11:05Z (step 1 DONE; RECIPE draft; waiting on label shards)
State: step 1 complete. Tools: tools/sib/own-lead/{own_common,build_patches,train,infer,auc,timing,test_own}.py.
Synthetic unit tests: ALL OK (AUC exact vs brute force with ties; derangement no fixed point; 3 contiguous near-equal fold groups; straddling patches excluded from F arms; label shard overlapping X refused; patches never touch X or uncertified cells; shards byte-deterministic; resume after kill bit-identical (max weight diff 0.0); windowed inference = whole-image inference (diff 0.0) at HALO 160).
Fact: w028-037 2.4 um surface volume EXISTS (109 x 71600 x 174640) -> T includes w028-037.

## Timing test (DECL-P4-23 item 4; T only: w010-027 r4 c2, random labels; 4 vCPU fp32; logs/sib/own-lead/p4own/timing.json)
| cfg | params | RF radius | train s/step B16 P128 / P192 / P256 | infer min/tile (compute, halo 160) |
|---|---|---|---|---|
| A (8,16,32; head 32, dil 1-8) | 232,697 | 151 px | 0.50 / 1.41 / 2.70 | 1.7 |
| B (8,24,48; head 48) | 550,937 | 159 px | 0.96 / 2.84 / 5.28 | 3.4 |
S3 read 40.5 MB/s (132 chunks, 0 missing).
End-to-end tile (T tile w010-027 r4 c2, valid 1.0, random weights, output discarded, no map written): 4.89 min incl. S3 reads, peak RSS 3.75 GB, 0 missing chunks -> well under the 20 min bar.
(An earlier run was INVALID: two timing processes contended for the CPU; discarded.)
Pick (to be frozen in RECIPE.md): cfg A, input 256 px, loss core 192 px (margin 32), output stride 4, batch 16, 2500 steps
= ~2.1 h/arm incl. loading; tile inference ~5 min (WIN 1024, HALO 160). Cap 4000 stored patches (4.06 MB each).

p4-excl T certification landed (a4ea355, independent check all pass): 229 T tiles with certified px (w010-027: 40, c0-c4 mostly;
w028-037: 189). NOTE w028-037 tile size is 8301 px (not 8343): code made per-segment (tests ALL OK).
Geometry-only count (logs/sib/own-lead/p4own/geocount.json): fully certified 256-px windows (core 192) with core mesh-valid >= 50 %:
w010-027 2,485; w028-037 192,654 (217 tiles). Labels will restrict this; the 4000-patch cap (ink-first) will likely bind.
Labels: p4-excl label_shards.py written to our x4 interface (7584660); label shards not yet pushed.
RECIPE_DRAFT.md + recipe.json pushed (everything fixed except label-dependent counts/hashes/F tile lists). Fold groups frozen
from the 229 certified T tiles (77/76/76); train.py now reads them from recipe.json (tests ALL OK).
Labels landed (p4-excl 7ea9f34). FEASIBLE: 45,262 ink 64-px cells (bar 2000).
Build: 4000 patches, 17.04 GB, build_manifest sha256 c567393d... RECIPE.md FROZEN at 6b5bdc5, sha256 377784c2bd8dd8617f38ae0e054fbe37684004f6e0d105852e84e16c16a6dfb8 (pushed before any training step).

## Arms (started 13:05Z)
| arm | where | state | steps | ETA | held-out AUC | tiles pushed |
|---|---|---|---|---|---|---|
| S1 | own-lead | trained 16:20Z (loss 0.563); predicting X (col. -1 first; ~7.9 min/tile at 2 threads; 88 tiles ~12 h) | 2500/2500 | X done ~04:30Z | - | 2 @16:38Z |
| F1 NULL S2 F2 F3 S3 | own-lead (fallback, orchestrator 15:02Z: the six workers are blocked on owner permission for cross-branch checkout; ASKs on their branches) | F1 training since 16:21Z; others queued (run_arms.py) | F1 175/2500 @16:41Z | ~4.5 h train/arm at 2 threads (F1 ~20:50Z) | - | 0 |
Note: RECIPE-A1 (c23037b) = train.py lazy shard loader; the first S1 launch was OOM-killed at data loading (0 steps). Recipe unchanged.
Blockers: none.

Concurrency check (orchestrator 15:02Z): 2+2 threads, F1 train 6.42 s/step (4-thread alone 4.45 -> 0.69) + S1 infer ~7.9 min/tile (alone 4.9 -> 0.62): combined 1.31x sequential -> kept concurrent.

Reorder (orchestrator 20:39Z, DECL-P4-23-A1 scheduling; G1 is the critical path): run_arms.py edited only (sha256 07633449969a8f889898d447edc29b8d270278334749eba24f5aa1e084f19980).
- Predictor: per-tile priority F1 held-out -> F2/F3 held-out (once trained) -> rest of S1 X -> NULL -> S2 -> S3; AUC right after each F arm's 24 tiles.
- Trainer: F2, F3, NULL, S2, S3. F1 trained 20:37Z (loss 0.569).
- NULL had started at 20:37:11Z and was stopped at ~20:43Z before its first 15-min checkpoint (no checkpoint to keep); it restarts from step 0 after F3 (deterministic schedule).
- The S1 tile in progress at 20:40Z was allowed to finish; the new driver commits it.

Reschedule (orchestrator 21:11Z, wall-clock priority): run_arms.py only (sha256 2722d3ac53319d76d7f735ca84cf21d91fb5cdc04e0954cafe3357dc8be01a8c). Two 2-thread slots, one priority queue:
- F1 held-out 24 + AUC -> F2 train (running, adopted) -> F3 train concurrently (RAM rule: MemAvailable >= peak train RSS + 2 GB; at 21:15Z F2 VmHWM 7.4 GB (anon 1.85 GB, rest shared mmap), available 12.2 GB -> passes) -> F2/F3 held-out + AUCs -> S2 + NULL train concurrently -> S3 train
  -> S2/NULL title slot (col. -1 + c14-c17 r0-r5, 30 each) -> NULL 72 held-out + AUCs -> c11-c13 r2-r5 -> c18-c19 -> rest -> S3 maps -> remaining S1 X (idle slots).
- Status at 21:15Z: F1 held-out 4/24 pushed; F2 step ~300/2500; S1 X 32/88 pushed (paused).

FINAL SHOT (orchestrator 22:03Z, DECL-P4-25-A6): F2 paused at 22:06Z (checkpoint 21:57Z kept; resumes); predictor stopped after its current F1 tile.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
run_arms.py (00:58Z): deletes infer.py's band checkpoint after each committed tile (disk hit the 5 GB floor at 00:53Z; 73 stale checkpoints = 4.7 GB removed). sha256 1d8f83efc956ab4180924b8a4c13f4ebfc73dc5ba662fcad79dc355e3788d1f8.
[line withheld: prize-candidate detail under review]

## Progress 2026-09-28 13:50Z (after a container restart at ~13:48Z; scheduler relaunched, all steps resume)
| arm | trained | maps pushed | held-out pixel AUC (auc.py) |
|---|---|---|---|
| F1 | yes | 24/24 held-out | 0.9418 (ink px 22.7 M, bg 47.1 M) |
| F2 | yes | 24/24 held-out | 0.9415 (86.8 M / 264.3 M) |
| F3 | yes | 24/24 held-out | 0.9401 (23.8 M / 90.5 M) |
[line withheld: prize-candidate detail under review]
| NULL | yes | 0 (next: title slot 30, then 72 held-out + AUCs) | pending |
| S2 | yes (13:47Z) | 0 (next: title slot 30) | - |
| S3 | training (restarted from step 0 at 13:48Z restart; no checkpoint yet) | 0 | - |
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
2026-09-30 04:22Z: harness-tracked background waiter started (exits when /work/own/ALL_DONE exists or the watchdog dies); scheduler unchanged since the 04:16Z relaunch.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
2026-09-30 17:38Z (orchestrator 17:31Z, throughput only): run_O2/run_O3 replaced by run_Olanes.sh = remaining A8 pool then A9 rest maps, 2 lanes x 2 threads, file order by alternate tiles; per-lane staging, move + manifest rebuild (infer.py itself) + commit + push under git.lock; PAUSE held until both lanes finish, then watchdog resumes the queue. infer.py/run_arms.py unchanged.
2026-09-30 17:58Z (DECL-P4-25-A10, -A10-A1): S1 model published at logs/sib/own-s1/model/ (sha256 bfa9f7a6...; commit 65aa79f). run_Olanes.sh narrowed to own-lead's v2 assignment (s1map_assign.json sha256 4f77b04d...): pool idx 0-15 + rest idx 0-9 (26 tiles); helpers make the rest. Lanes restarted (2 x 2 threads); queue resumes after.
2026-09-30 17:57Z: correction - 65aa79f held only summary.json (*.pth is gitignored); model_final.pth force-added in 054ec4e, remote copy sha256 bfa9f7a6... verified.
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
2026-09-30 22:47Z: container restart (~22:41Z). Found an S3 read outage ~21:38Z: chunk reads failed for 6 Q, 4 A8/A9 and the S3+NULL seed maps (FAILED, nothing wrong pushed); the chain then fell through to the scheduler. S3 reachable again (206); relaunched run_Qlanes (failed Q tiles), run_Olanes (held on HOLD_O), run_seedP (S3, NULL r8c14) - all resumable; tracked wait re-armed.
2026-09-30 23:35Z (DECL-P4-26-A2): VERSO job first: run_verso.sh makes own-lead's 80 verso S1 maps (verso_assign.json sha256 f3364896..., wrapper infer_verso.py sha256 a1bd1f24..., infer.py ddf-era code unchanged, own_common sha256 ddf90770...) into logs/sib/own-s1/verso/tiles/, 2 lanes x 2 threads; Q lanes paused (resume after), seedP continues. CT chunks are not cached by the reader, so ~5 min/tile, not seconds.
[line withheld: prize-candidate detail under review]
