Provenance: Project HERCULES | owner the owner | [id removed]
# fl-pherc0191 RESUME (DECL-FL-1, PHerc0191)
- Bucket (2026-09-30): no organizer tifxyz segments; auto-grow on surface-m7 (20260413222639, th0.2) with normal-grids (fallback: without).
- Seeds: tools/sib/fl-pherc0191/seeds.py, 8 candidates at 0.5 r_max, z = 0.5 of the volume; grows stop at 4 accepted (0 selfcross, >= 16 cm^2).
- Done markers: logs/sib/fl-pherc0191/state/*.done (committed). Heavy data: /work/fl/pherc0191 (render, infer, logs/pipeline.log).
- Exact relaunch (fresh container too; setup_env is part of the pipeline):
  setsid nohup bash tools/sib/fl-pherc0191/watchdog.sh >/dev/null 2>&1 < /dev/null &
- Orientation: auto segments have no known winding direction, so tiles are written for BOTH depth orders (manifest field direction).
