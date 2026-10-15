Provenance: Project HERCULES | owner the owner | [id removed]

# o5w2 status
Task: RULES.md DECL-P4-14-A3. One PHerc.1667 iteration-5 P4-O tile, 20260701183124-w010-027 r0 c8 (known-text gate).
- 02:42Z: WORKER.md appeared at ckpt-screen-b 6aa0345, so it was used directly and the fallback was not needed. Code commit 98cd075; the sha256 of p4o_tiles.py, infer_1667.py and fetch.py all match WORKER.md. The base tree's src/hercules and data/catalogue are identical to 98cd075.
- Checkpoint model.safetensors sha256 9920d4338e51d38b241cbf48392610be0519e4e19c2e9d987ccfc2e78bd3301b (333,531,996 B) matches WORKER.md, the catalogue and provenance.json. Card/code files are git-oid OK.
- 02:42:56Z: tile r0 c8 started: 3614 windows, ETA 3.31 h, 4 threads, order forward (slices 23-84), the only order for iteration-5.
- Outputs: WORKER.md section 4 layout, rebased under logs/sib/o5w2/p4o/ as ordered: PHerc.1667-iteration-5/tiles/<png, png.json>, run_<pid>.log, fleet/o5w2.json; plus logs/sib/o5w2/o5w2_tile.json. progress.log is pushed every ~30 min.
- 05:14:49Z: DONE. Tile r0 c8 finished in one uninterrupted run (no resume): 3614 windows, 2.531 h wall. Order forward only.
  - png_sha256 0a0b11242f53ca40024bb6ddb8a49c5e9e69e2129bb8a62712aa9552eccb6c5d, re-verified after the copy; PNG chunks IHDR/IDAT/IEND only.
  - valid_fraction 0.85633. coverage_of_valid 0.98584: about 1.4 % of mesh-valid px get no window, because the card loop skips any window that touches a non-valid px. They are written as 0 in the u8 output. Disclosed; not changed.
  - chunks read 3951, missing 605 (404 = outside the array).
  - Outputs: logs/sib/o5w2/p4o/PHerc.1667-iteration-5/{tiles/*.png, tiles/*.png.json, run_783.log}, p4o/fleet/o5w2.json, o5w2_tile.json.
  - No tile or image was opened. Worker stopped.
