Provenance: Project HERCULES | owner the owner | [id removed]

# p4-tiles-a RESUME (DECL-P4-19 line-structure test)

To resume from a fresh container:
1. `pip install opencv-python-headless tifffile imagecodecs pillow numpy`
2. `tools/sib/p4-tiles-a/fetch_p419.sh <dir> <dir>/downloads.jsonl` (M1 prediction + 2.4 um z.tif; check sha256 against logs/sib/p4-tiles-a/downloads.jsonl)
3. `python3 tools/sib/p4-tiles-a/test_p419_profile.py` (9 synthetic tests must pass)
4. `python3 tools/sib/p4-tiles-a/p419_profile.py <dir>/<prediction>.tif <dir>/z.tif logs/sib/p4-tiles-a/p419_profile.json`
5. Commit and push to claude/gifted-bell-gavnl5-sib-p4-tiles-a; delete <dir>.
Never view an image. Numbers only.
