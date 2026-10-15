Provenance: Project HERCULES | owner the owner | [id removed]

# o5w4 status (DECL-P4-14-A3): PHerc.1667-iteration-5, 20260701183124-w010-027 r0 c16

- 2026-09-27: started. ckpt-screen-b p4o/WORKER.md not present yet (ckpt-screen-b head a1190c5); polling every 5 min up to 30 min, then fallback to the documented RESUME.md / SUBSIBS.md command at the latest ckpt-screen-b commit.
- Env /opt/ckb (SPECS.json wrapper.env) building; iteration-5 cards fetched (git oid ok); model.safetensors downloading for sha256 verification.
- Note: r0 c16 is also in S1's list in p4o/SUBSIBS.md; this worker computes it per DECL-P4-14-A3 as assigned.
- 02:42Z WORKER.md found (ckpt-screen-b 6aa0345). Code: ckpt-screen-b 98cd07501bbd3ec4dd0d1f09bf6101389f458080, detached worktree /work/o5w4/cb. sha256 verified = WORKER.md: p4o_tiles.py a32d7e86…c371, infer_1667.py 29444f37…cb12, fetch.py e5a3cb8f…1860.
- Checkpoint model.safetensors sha256 9920d4338e51d38b241cbf48392610be0519e4e19c2e9d987ccfc2e78bd3301b, 333531996 B (fetch.py verified vs catalogue; = WORKER.md). Cards git-oid ok.
- Env /opt/ckb: python 3.11.15, torch 2.14.0+cpu, transformers 4.57.6, zarr 2.18.7, numpy 2.4.6, opencv 5.0.0; no torchvision/timm. Disclosure: s3fs/fsspec also installed (unused by the builder).
- 02:43Z launched: p4o_tiles.py --iteration 5 --tiles "0,16", OMP 4, P4O_WORK=/work/o5w4/p4o. Order forward (only order for it5). Outputs keep WORKER.md naming/layout, rooted at logs/sib/o5w4/p4o/ (i.e. logs/sib/o5w4/p4o/PHerc.1667-iteration-5/{tiles/…png,.png.json,run_<pid>.log} and logs/sib/o5w4/p4o/fleet/o5w4.json) per the orchestrator's "under logs/sib/o5w4/".
- 2026-09-27T03:13Z progress: worker alive; in-tile checkpoint {"n": 215, "utc": "2026-09-27T02:59:48Z"}; last log: {"tile": "20260701183124-w010-027_r0_c16.png", "windows": 3389, "eta_h": 3.11, "log_utc": "2026-09-27T02:43:35Z"}
- 2026-09-27T03:43Z progress: worker alive; in-tile checkpoint {"n": 648, "utc": "2026-09-27T03:30:00Z"}; last log: {"tile": "20260701183124-w010-027_r0_c16.png", "windows": 3389, "eta_h": 3.11, "log_utc": "2026-09-27T02:43:35Z"}
- 2026-09-27T04:13Z progress: worker alive; in-tile checkpoint {"n": 1091, "utc": "2026-09-27T04:00:11Z"}; last log: {"tile": "20260701183124-w010-027_r0_c16.png", "windows": 3389, "eta_h": 3.11, "log_utc": "2026-09-27T02:43:35Z"}
- 2026-09-27T04:43Z progress: worker alive; in-tile checkpoint {"n": 1535, "utc": "2026-09-27T04:30:23Z"}; last log: {"tile": "20260701183124-w010-027_r0_c16.png", "windows": 3389, "eta_h": 3.11, "log_utc": "2026-09-27T02:43:35Z"}
- 2026-09-27T05:13Z progress: worker alive; in-tile checkpoint {"n": 1981, "utc": "2026-09-27T05:00:34Z"}; last log: {"tile": "20260701183124-w010-027_r0_c16.png", "windows": 3389, "eta_h": 3.11, "log_utc": "2026-09-27T02:43:35Z"}
- 2026-09-27T05:43Z progress: worker alive; in-tile checkpoint {"n": 2422, "utc": "2026-09-27T05:30:48Z"}; last log: {"tile": "20260701183124-w010-027_r0_c16.png", "windows": 3389, "eta_h": 3.11, "log_utc": "2026-09-27T02:43:35Z"}
- 2026-09-27T06:13Z progress: worker alive; in-tile checkpoint {"n": 2869, "utc": "2026-09-27T06:01:03Z"}; last log: {"tile": "20260701183124-w010-027_r0_c16.png", "windows": 3389, "eta_h": 3.11, "log_utc": "2026-09-27T02:43:35Z"}
- 2026-09-27T06:43Z progress: worker alive; in-tile checkpoint {"n": 3304, "utc": "2026-09-27T06:31:17Z"}; last log: {"file": "tiles/20260701183124-w010-027_r0_c16.png", "r": 0, "c": 16, "png_sha256": "2bcb73c2974991c471126d8d229c9cebdf20689150276490608ee6099dd26aa5", "png_bytes": 371660, "png_chunks": ["IDAT", "IEND", "IHDR"], "valid_fraction": 0.8049704270410581, "canvas_rows": [0, 8343], "canvas_cols": [133488,
- 06:37Z DONE. it5 r0 c16: png_sha256 2bcb73c2974991c471126d8d229c9cebdf20689150276490608ee6099dd26aa5 (re-verified), 3389 windows, 14014 s (3.89 h). valid_fraction 0.80497 = e2 manifest; nonzero outside valid 0; coverage_of_valid 0.986; input norm mean 0.277 (training scale 0.22-0.30); chunks read 3772, missing 851.
- Records: logs/sib/o5w4/o5w4_tile_r0_c16.json (tile, code commit, checkpoint sha256, order, start/end utc, runtime); fleet record logs/sib/o5w4/p4o/fleet/o5w4.json. Tile never viewed. Worker stopped.
