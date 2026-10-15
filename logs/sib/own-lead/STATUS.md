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
Labels landed (p4-excl 7ea9f34, 229 x4 shards). FEASIBILITY (DECL-P4-23 item 2): 45,262 ink 64-px cells >= 2 % (labelled 143,474); bar 2000 -> FEASIBLE (p4own/feasibility.json).
Now: full patch build (256/192, cap 4000) running detached (restarted 11:58Z after a container restart killed the first run at ~11:35Z; no shards had been written) -> finalize_recipe -> RECIPE.md push -> 7 arm workers.
Blockers: none.
