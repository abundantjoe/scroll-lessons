Provenance: Project HERCULES | owner the owner | [id removed]

# dev-distft STATUS (2026-09-26 ~05:30Z)

STATE: PHASE 1 READY (READY.md). WAITING for the gate. No training step on real data has run, and none will run
before both of these hold:
- (a) a METRIC-HASH of the frozen v3 registry and evaluator is recorded in RULES.md;
- (b) the orchestrator sends 'GO DEV DIST-FT'.

## Gate check at 05:2xZ (origin/claude/gifted-bell-gavnl5 @ 5b43219)

- (a) NOT MET. The newest METRIC-HASH entries (20-23) are all P4 entries. There is no DEV registry or evaluator
  METRIC-HASH.
- (b) NOT RECEIVED.

## Prepared since READY

**Provisional hold-out check** (`holdout_check.py` -> `holdout_check.json`, runs.jsonl `holdout_check`).
- Input: devloop registry v3 at commit a6af0cb (not frozen, not hashed).
- Hold-out segments = the DEV segments plus every segment same-papyrus with one: 6 on PHerc0814 and 7 on PHerc0139.
- Effect on pairs0814 and pairs0814b: of 564 gated staged patches, 121 are dropped and 443 kept. Dropped by segment:

  | Segment | Patches dropped |
  |---|---|
  | 204843 | 21 |
  | 212701 | 11 |
  | 222237 | 23 |
  | 165636 | 22 |
  | 060526 | 44 |

- pairs0139: no tile registry on git yet, so there are no counts.
- The check is re-run on the frozen list when it exists, and the allowlists are built from that run.

**Config hashes.**
- The synthetic smoke configs are recorded in READY.md section 3.
- Real-data config hashes cannot exist until GO names the training-pair registry, because the config pins the
  registry and allowlist sha256.

## Still pending

- The frozen hold-out list, EVAL_API.md and the METRIC-HASH (devloop sibling; it was paused on an owner interrupt at
  a6af0cb).
- pairs0814 stage-C shards, and pairs0139 shards on git.
- Answers to ASK.md A1-A9. The defaults are in force.

## P4-O (DECL-P4-14-A1), 2026-09-26 21:45Z: CLAIM PHerc.1667-iteration-2

Existing claims when I read them (the branches fetched at 21:4xZ):

| Builder | Iteration |
|---|---|
| ckpt-screen-b | iteration-5 (latest) |
| ckpt-screen-a | iteration-0 |
| dev-lcsoft | iteration-1 (its STATUS.md, 21:40Z) |
| ckpt-screen-c | none: blocked, because no card documents a held-out metric |
| amx | none (no STATUS.md on its branch) |

- I take the lowest unclaimed number: **iteration-2**.
- If ckpt-screen-c's later pick is iteration-2, this claim came first; c picks among the rest.
- Output: logs/sib/dev-distft/p4o/iteration-2/{manifest.json, tiles/}, for harness p4-tiles-a (batch o5).
- The DEV DIST-FT gate is unchanged: still waiting on the devloop freeze.

## P4-O iteration-2: RUNNING (started 2026-09-26 ~21:45Z)

**Builder.** ckpt-screen-b's builder, byte-identical copies at commit ca732aef:

| File | sha256 |
|---|---|
| tools/sib/dev-distft/p4o_tiles.py | 5ec64557aabedcd1a4a8ba52b4f01ce6bd555e45d9d3743486374aaf391dfdc6 |
| tools/sib/dev-distft/infer_1667.py | 431067ee40ff5cb2b0b1303bdc80c218a4838f395320c94a1505b44b47bfd5f6 |

**Conventions** (the builder's, which match ckpt-screen-b's iteration-5 run):
- the 2.4 um surface volume at level 0 as is;
- slices 23..84, ascending (the documented order for iterations 1-5);
- clip(0, 200) / 255;
- the card's tiling loop (window 256, stride 128);
- raw u8 prediction, 0 outside mesh-valid, INTER_AREA 8343 -> 1068 px, in the e2 PNG format.

**Weights.** HF scrollprize/PHerc.1667-iteration-2 at commit bf6053ca, verified against both
data/catalogue/checkpoints.json and ckpt-screen-b's provenance.json:

| File | sha256 |
|---|---|
| model.safetensors | 485ce6e12cca19071c5746d95327d9aa6f2fd04ea1a2acc95c9530d3ee895b71 |
| config.json | 36bb9c4ee2bc049a... |

- The card and code files match their git blob oids.
- No preview image or README was downloaded (downloads.jsonl).

**Environment.** transformers 4.57.6 (the version in config.json), torch 2.14.0+cpu, opencv-python-headless 5.0.0.

**Dry run** (no tiles): model load, the channels_last layout check and the mesh-valid mask load all passed.

**Run.**
- 108 tiles, r0-r5 x c0-c17, in row-major order.
- 1 process with 4 threads: memory is about 5 GB per process, so a second process does not fit safely in 15 GB.
- Cost: ckpt-screen-b's ETA formula is 3.3 s per window, about 3.3 h per full tile at 4 threads. The whole run is
  therefore on the order of 300+ h of wall time on this container.
- The measured per-tile time goes here after tile 1.

**Push loop.** tools/sib/dev-distft/p4o_push.sh commits and pushes every 15 min whenever there are new tiles. That
is more often than every ~10 tiles, so the hourly-push rule holds.

**Never viewed.** No tile has been or will be opened. The harness is p4-tiles-a (batch o5).

## P4-O iteration-2, 2026-09-27 01:10Z: restart and DECL-P4-14-A2

**What happened.** The container restarted at about 01:02Z. Tile r0_c0 was lost about 3.3 h into its run: nothing had
finished and nothing was pushed. /work survived.

**Re-planned under DECL-P4-14-A2.** tools/sib/dev-distft/p4o_stage.sh runs the stages in this order (ORDER.json).
A partial manifest is written and pushed after each stage.

| Stage | Tiles | Count |
|---|---|---|
| (i) | r0-r1 x c5-c8 (the gate, with r0 c5 first), then r0-r1 x c9-c14 | 20 |
| (ii) | r2-r5 x c5-c14 | 40 |
| (iii) | r0-r5 x c15-c17 | 18 |
| (iv) | the rest, r0-r5 x c0-c4 | 30 |

**Precision (A2 item 2).**
- r0 c5 is run twice: in bf16 (check folder only, never pushed) and in fp32 (the real tile).
- p4o_bf16_check.py compares the two full-resolution u8 maps. PASS means <= 1 % of mesh-valid pixels differ by
  more than 2/255. The result goes to p4o/iteration-2/bf16_check.json.
- On PASS, the other 107 tiles run in bf16. On FAIL, they run in fp32.
- The bf16 runner (p4o_bf16.py) is the unchanged builder with the model under torch.autocast(cpu, bfloat16).
- Micro-benchmark: 1.2 s per window in bf16 against 2.6 s in fp32 (2.1x). On one random window, 0 of the output
  pixels moved by more than 2/255.

**Manifest.** p4o_finalize.py runs the builder's own finalize unchanged. It reads SPECS.json from ckpt-screen-b's
branch, and records the per-tile precision (the builder hard-codes float32).

**Resuming.** See RESUME.md.

**Projection.** The r0 c5 check (bf16 then fp32) takes about 3.4 h.

| Precision for the rest | Stage (i) remainder (19 tiles) | All 108 tiles |
|---|---|---|
| bf16 (about 1.1 h per tile) | about 21 h | about 5 days |
| fp32 (about 2.3 h per tile) | about 44 h | about 10 days |

## P4-O iteration-2, 2026-09-27 06:15Z: second container loss; tiles are now resumable mid-tile

**What happened.** The container was reclaimed again between 01:07Z and 06:08Z; uptime was 0 at 06:08Z. The bf16
r0 c5 run had started at 01:07Z (3631 windows) and did not finish. No tile exists yet, and 0 have been pushed.

**Cause.** Each tile takes hours, while the builder resumes only at tile boundaries, so every reclaim loses a whole
tile.

**Fix.** tools/sib/dev-distft/p4o_resumable.py resumes within a tile.
- It patches infer_1667.card_tiling with a statement-for-statement copy of the card's loop that saves its running
  float32 sums every 200 windows (about 4-8 min) and, on restart, skips the windows already added.
- The windows are visited in the same order and added to the same arrays, so a resumed tile is bitwise identical to an
  uninterrupted one. Tested in tests/test_p4o_resumable.py (2 passed), with two simulated crashes.
- Both runners use it: fp32 through p4o_resumable.py, and bf16 through p4o_bf16.py, which imports it.
- The builder (p4o_tiles.py) and the wrapper (infer_1667.py) are unchanged, byte-identical.

**Restarted 06:14Z.** The r0 c5 bf16 check run is going; after it come r0 c5 in fp32, the bf16 check, then stages
(i)-(iv).

## 2026-09-30 04:12Z: P4-O iteration-2 STOPPED; re-tasked to First Letters PASS 3 PHerc0800

**P4-O iteration-2.** Another container reclaim came after 06:18Z on 09-27. At 04:08Z on 09-30 no P4-O process was
running, and tiles/ held 0 tiles; nothing was ever pushed. The orchestrator's 04:04Z message says the previous task
is complete, so P4-O iteration-2 ends here without output. The within-tile resume tools remain for whoever picks it
up again (RESUME.md).

**New work.** logs/sib/fl3-pherc0800/STATUS.md, with tools/sib/fl3-pherc0800/.
