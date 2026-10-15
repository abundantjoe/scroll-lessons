Provenance: Project HERCULES | owner the owner | [id removed]
# p4-purple-de RESUME
Scratch: $S = scratchpad/de/w (sites/*.npz, labels/, pred.tif, blk/). Tools: tools/sib/p4-purple/de/.
Done: A (inventory, overlap), A-1 fence, B2 registration (registration.json).
Order (PROTOCOL B4): sites.py (resumable? no: rerun redraws same rng; sites.json lists done) -> analyze.py fit ->
commit fit.json -> labels.py (all sites) -> analyze.py validate -> DUAL_FREEZE.md, REPORT.md (<= 30 lines), stop.
Fence: never read 137 keV at w010-027 (dcommon.fence*, D_f 146 vox).
2026-09-27 07:33Z: METRIC-HASH-40 verified; APPLY.md pushed; apply.py running as 3 detached workers
(python3 tools/sib/p4-purple/de/apply.py $S w 3, w = 0..2; resumable per block in $S/apply/b_*.json; 1781 blocks).
When all blocks exist: python3 apply.py $S summarise -> title_zone.json; STATUS 5-line summary; integrity line.
Perf fix (07:31Z, identical output): fast 1-D chunk-key enumeration (as sites.py); 4 blocks were done before it.
