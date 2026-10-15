#!/bin/bash
# Disk guard: this box has ~30 GB writable and two tracers plus two renders refill the caches within minutes.
# Runs as its own FILE rather than as a string inside supervisor.sh: an inline `bash -c '...'` body is not parsed by
# `bash -n` on the supervisor, so a stray quote in it is invisible until the job dies at runtime. That is exactly how
# this guard was killed on 2026-09-18 by a `grep -v ' 0 render'`, and the class of bug is removed by this file
# existing. Every edit here is covered by `bash -n scripts/disk_guard.sh` in the test suite.
#
# usage: disk_guard.sh [interval_seconds]   (env: HERCULES_DATA, HERCULES_ROOT)
D=${HERCULES_DATA:-/home/user/hercules_data}
R=${HERCULES_ROOT:-/home/user/hercules}
INTERVAL=${1:-60}
RC=$D/vc_home/.VC3D/remote_cache
KEEP_CT="PHerc0826|PHerc0358|PHerc1447|PHerc1203|PHerc0800"
# MB: the most a scroll's grids may hold while its tracer is running. Two tiers, for the same reason the prune
# target has two: pruning a live tracer's grids forces it to refetch them and was measured at a ~4x slowdown
# (269/333 s before, median 1052 s over the 14 traces after). When there is real headroom above the render floor
# the cap is generous; when there is not, it tightens. Changed 2026-09-19 04:55 UTC with the guard STOPPED, because
# editing a running script is what corrupted rdepth.sh tonight.
ACTIVE_CAP_ROOMY=${ACTIVE_CAP_ROOMY:-3000}
ACTIVE_CAP_TIGHT=${ACTIVE_CAP_TIGHT:-1500}
ACTIVE_CAP=${ACTIVE_CAP:-$ACTIVE_CAP_TIGHT}

log() { echo "[disk_guard $(date -u +%FT%TZ)] $*"; }

# True if a level-4 CT cache directory name is on KEEP_CT. The earlier form, `case $name in $KEEP_CT)`, never matched:
# a `|` that arrives through a variable expansion is a literal character in a case pattern, not alternation, so below
# the floor every cache was deleted, the five kept ones included (found while writing the release, 2026-10-15; cost:
# refetch time only, no map or verdict touched).
keep_ct() { [[ "|$KEEP_CT|" == *"|$1|"* ]]; }

# Scrolls with a VC3D tracer or renderer running right now, read from the container process argv
# (--target-dir /data/patches/<scroll>[_small] or --segmentation /data/patches/<scroll>/...).
active_scrolls() {
  ps -eo args | grep -E "[/]opt/vc/bin/vc_(grow_seg_from_seed|render_tifxyz)" \
    | grep -oE "/data/patches/[A-Za-z0-9]+" | sed -e 's#.*/##' -e 's/_small$//' | sort -u
}

# $1 = cap in MB; $2 = "force" to prune even a scroll that is being traced right now.
# Pruning the grids under a LIVE tracer does not relieve pressure: the tracer refetches them within the minute, so the
# directory is back over the cap and the trace pays the network for it. Measured on 2026-09-18: 40-generation interior
# traces ran 269 s and 333 s before the guard began pruning PHerc0358's grids under a running trace, and a median of
# 1052 s (max 2358 s) over the 14 after -- a ~4x slowdown on the one experiment producing readable interior surfaces.
# Below the 3 GB hard floor the guard still prunes everything, because running out of disk is worse than a slow trace.
prune_grids() {
  local act; act=$(active_scrolls)
  for g in $D/normal_grids/*/; do
    [ -d "$g" ] || continue
    local name; name=$(basename "$g")
    gm=$(du -sm "$g" 2>/dev/null | cut -f1); gm=${gm:-0}
    # An active scroll is exempt from the cap, but only up to ACTIVE_CAP. Exempting it without limit is how two
    # concurrent traces took this box from 8.1 GB to 3.8 GB free on 2026-09-18 while the guard stood by: the
    # anti-thrash rule must not be able to outrank the disk itself.
    if [ "${2:-}" != force ] && [ "$gm" -le "$ACTIVE_CAP" ] && printf '%s\n' "$act" | grep -qx "$name"; then
      continue
    fi
    if [ "$gm" -gt "$1" ]; then
      log "normal grids $g ${gm} MB > ${1}: pruning"
      find "$g" -type f ! -name metadata.json ! -name normal-grids-remote.json -delete
    fi
  done
}

while true; do
  f=$(df --output=avail -k / | tail -1)
  mb=$(du -sm "$RC" 2>/dev/null | cut -f1); mb=${mb:-0}
  busy=$(ps -eo args | grep -cE "[/]opt/vc/bin/vc_(render|grow)")

  # the VC3D remote chunk cache: cleared above 1 GB when nothing is rendering or tracing, above 1.5 GB regardless
  if { [ "$mb" -gt 1000 ] && [ "$busy" -eq 0 ]; } || [ "$mb" -gt 1500 ]; then
    log "remote cache ${mb} MB (busy $busy): clearing"; rm -rf "$RC"/* 2>/dev/null
  fi

  if [ "$f" -lt 7000000 ]; then
    # renders are the largest thing written here and an interrupted read leaves its render behind; sweep those first,
    # since a cache prune costs refetch time while an orphan render costs nothing to remove
    "$R"/.venv/bin/python "$R"/scripts/sweep_renders.py 2>/dev/null | grep -v "0 render(s), 0 MB"
    # two tiers: a tracer that refetches its grids every run is network-bound (40-generation traces went from ~250 s
    # to 15 min after an over-eager prune), so the tight cap applies only when the floor is actually at risk
    # the live-tracer exemption follows the same free-space tiers as the prune target
    if [ "$f" -lt 5500000 ]; then ACTIVE_CAP=$ACTIVE_CAP_TIGHT; prune_grids 500
    else ACTIVE_CAP=$ACTIVE_CAP_ROOMY; prune_grids 900; fi
  fi

  if [ "$f" -lt 3000000 ]; then
    log "free ${f}k: clearing every cache that can be refetched"
    rm -rf "$RC"/* 2>/dev/null
    for c in $D/ct_l4_cache/*; do
      keep_ct "$(basename "$c")" || rm -rf "$c"
    done
    prune_grids 0 force
    rm -rf $D/patches_2um/ct_points_cache /tmp/pytest-of-root $D/pred_l1_cache $D/ct_l1_cache 2>/dev/null
    rm -rf $D/lasagna_cache/*/nx $D/lasagna_cache/*/ny 2>/dev/null
  fi
  sleep "$INTERVAL"
done
