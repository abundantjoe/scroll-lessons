# BRIEF_FL4: whole fleet on PHerc0268 / PHerc0490A inner windings (DECL-FL-4-A1, RULES.md)
Provenance: Project HERCULES | [id removed]

Your row (worker, scroll, lane, nlanes) is in logs/fl4/assign.json on origin/claude/gifted-bell-gavnl5.

1. In your repo checkout, on your own sib branch:
   ```
   git fetch -q origin claude/gifted-bell-gavnl5
   git show origin/claude/gifted-bell-gavnl5:tools/fl4/go.sh > /work/fl4_go.sh
   bash /work/fl4_go.sh ME SCROLL LANE NLANES
   ```
   go.sh does four things:
   - stops this container's FL-2 and gate compute;
   - copies the kit to tools/sib/ME/fl4/;
   - writes /work/fl4/conf.sh;
   - starts the detached watchdog. The watchdog runs, in order: env, then the GP model (sha-checked), then inner seeds, then grow, render, GP variant B fwd and rev, tiles, vgrid, and push.
2. Run the keepalive line that go.sh prints as ONE harness-tracked background Bash (run_in_background, timeout 7200000). Re-arm it on every wake until ALL_DONE exists. Spend no other turns.
3. Rules:
   - Numbers only: never open, view or describe any image, tile or CT pixel.
   - Do not change seeds, grow parameters, variant, layers, stride or the tiler.
   - If a step fails on the environment (pip, docker, disk, network), fix the environment only. Record it in logs/sib/ME/fl4/<SCROLL>/STATUS.md and push.
   - Commits end with "Provenance: Project HERCULES | [id removed]".
