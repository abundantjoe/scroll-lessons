Provenance: Project HERCULES | owner the owner | [id removed]

# RESUME dev-lcsoft (P4-O PHerc.1667-iteration-1, DECL-P4-14-A1/-A2)
After a container restart, from the repo root:
1. Rebuild the environment if /opt/hv-ink or /work/lcsoft/pylib* is missing:
   - run `bash tools/sib/dev-lcsoft/setup_py.sh`;
   - then `/opt/hv-ink/bin/python -m pip install -q --target /work/lcsoft/pylib_tf transformers==4.57.6`;
   - then `/opt/hv-ink/bin/python -m pip install -q --target /work/lcsoft/pylib_cv opencv-python-headless==4.12.0.88 --no-deps`.
2. Refetch the weights and cards if /work/ckpt/PHerc.1667-iteration-1 or /work/cards is missing: `python3 tools/sib/dev-lcsoft/p4o_fetch_it.py 1`. This verifies the sha256 and git oids.
3. `git fetch origin claude/gifted-bell-gavnl5-sib-pairs0814b`. The builder reads its e2 grid and manifest by git ref.
4. Relaunch the driver, detached. It resumes and skips finished tiles:
   `setsid nohup tools/sib/dev-lcsoft/p4o_drive.sh 1 $(tr -d '|' < TILES) > /work/lcsoft/drive_it1.log 2>&1 < /dev/null &`
   The tile order is TILES = the A2 order written in STATUS.md, regenerated with:
   - S1 = r0-r1 x c5..c14;
   - S2 = r2-r5 x c5..c14;
   - S3 = r0-r5 x c15..c17;
   - S4 = r0-r5 x c0..c4.
5. An interrupted tile restarts from scratch (about 3 h lost). Finished tiles are committed and pushed by the driver.
Never view a tile. Write only under logs/sib/dev-lcsoft/ and tools/sib/dev-lcsoft/.
