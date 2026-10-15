Provenance: Project HERCULES | owner the owner | [id removed]

# STATUS dev-lcsoft (2026-09-26 06:05Z)
- PHASE 1: DONE (READY.md). The ASK defaults were ruled accepted at 05:58Z (ASK.md).
- PREP: DONE. tools/sib/dev-lcsoft/run_phase2.sh is the resumable pipeline: pool, then caches, then soft targets, then RECIPE, NULL, REV.
  - It refuses to run without a GO file that holds "GO DEV LC384-SOFT" and a METRIC-HASH id.
  - It also refuses unless the hold-out registry sha256 matches.
- PHASE 2: WAITING for the METRIC-HASH of devloop FREEZE.md and GO DEV. No real data has been read.

## P4-O (DECL-P4-14-A1), 2026-09-26 21:3xZ: CLAIM PHerc.1667-iteration-1
- Existing claims when I read them: ckpt-screen-b has iteration-5 (latest), ckpt-screen-a has iteration-0, ckpt-screen-c has none yet (its choice is blocked). dev-distft and amx have not claimed anything.
- ckpt-screen-b's note "then iteration-1 if -c has not taken it" predates A1, which gives b the latest iteration only. I take the lowest unclaimed number, iteration-1.
- Output: logs/sib/dev-lcsoft/p4o/iteration-1/{manifest.json, tiles/}, for harness p4-tiles-a.
- RUNNING since 21:39Z.
  - Checkpoint: scrollprize/PHerc.1667-iteration-1 @ f2012ce. The weights sha256 75e4009673b2c419c23cb388474c87357c226058598f1e2d7cba4e71d22e0fcb equals ckpt-screen-b's provenance.json. config.json, configuration_inkdetection.py and modeling_inkdetection.py match their git blob oids (p4o/downloads.jsonl). The remote model code imports only torch and transformers; it does no file or network I/O.
  - Builder: the ckpt-screen-b builder at ca732ae, used byte-identically: tools/sib/dev-lcsoft/{infer_1667.py 431067ee..., p4o_tiles.py 5ec64557...}.
  - Geometry: level 0 at 2.4 um, slices 23..84, order forward (reverse_layers False, as in iteration-5), stride 128 as on the card, raw u8 clip(p*255), 0 outside mesh-valid, INTER_AREA to 1068.
  - Output: logs/sib/dev-lcsoft/p4o/PHerc.1667-iteration-1/. The manifest is re-finalised, committed and pushed after every tile.
- Tile order: rows r0..r5, each as c10-c13, c0-c4, c14-c17, c5-c9, i.e. the title zone and the gate columns first.
- Cost: 3611 windows per tile, about 3.3 h per tile on 4 vCPU. r0 alone (18 tiles) is about 60 h, and r0-r5 about 360 h with one worker. More workers (sub-siblings, as ckpt-screen-b uses) would cut this proportionally. That is the orchestrator's call, given the shared quota.
- Integrity: no tile has been viewed; numbers and hashes only.

## P4-O iteration-1 under DECL-P4-14-A2 (2026-09-27 01:10Z)
- Done: r0 c10 (fp32, 3611 windows, 10 635 s = 2.95 h, finished 00:36Z). The manifest checks pass: png sha256 recomputed, valid_fraction equals e2, tile eligible in e2.
- Upstream bug, recorded rather than patched, so the builder stays byte-identical. ckpt-screen-b p4o_tiles.py ca732ae run_tile() ends with log(rec), and main's log() does dict(utc=utc(), **rec) while rec already has 'utc'. The result is a TypeError AFTER the tile png and json are written: the process exits 1 and any later tiles in the same call are not run. The tile itself is intact (its sha is re-verified at finalize). My driver makes one call per tile and now counts a written json+png as success. ckpt-screen-b and its sub-siblings run the same code, so a multi-tile --tiles list there stops after its first tile.
- Order per A2 item 1 (tiles already done are kept):
  - (i) r0-r1 x c5-c14, 20 tiles, 1 done; a partial manifest is pushed when (i) is complete;
  - (ii) r2-r5 x c5-c14;
  - (iii) c15-c17, all rows;
  - (iv) c0-c4, all rows.
- Precision: fp32 throughout. A2 item 2 permits bf16 only after an r0 c5 equivalence check done before any title-zone tile. A title-zone tile (r0 c10) was already made in fp32, and bf16 would need a change to the pinned builder, so this material stays fp32.
- ETA: about 3 h per tile. Stage (i) finishes around 2026-09-29 10:00Z; stage (ii) adds about 120 h.
