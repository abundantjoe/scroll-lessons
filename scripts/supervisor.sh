#!/bin/bash
# Idempotent resume-everything script for this box (the container restarts without notice and kills every process).
# Run at the start of every session/turn: it (1) starts dockerd if needed, (2) resumes the gate inference queue,
# (3) resumes the coverage loop for the scrolls listed in COVERAGE (tracer per seed, sequential), (4) resumes the
# QC->render->read loop over traced patches. Each step skips finished work via markers. Safe to run repeatedly.
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}; mkdir -p $D/logs
# scroll:volume:um:pitch. PHerc1203 / PHerc1447 / PHerc0800 are the only eligible volumes that publish team segments
# (fetched with scripts/fetch_team_segments.py into patches/<scroll>/team_*); their tracer_paused marker keeps the
# tracer off them entirely - there is nothing to trace when the surfaces already exist.
COVERAGE=${COVERAGE:-"PHerc1203:20250820131727:9.362:9.362um-1.2m-113keV PHerc1447:20250521151220:8.64:8.640um-1.2m-116keV PHerc0800:20250521135224:8.64:8.640um-1.2m-116keV PHerc0826:20250821151701:9.362:9.362um-1.2m-113keV PHerc0358:20250821151737:9.362:9.362um-1.2m-113keV PHerc0175A:20250521115057:8.64:8.640um-1.2m-116keV PHerc0343:20250521140437:8.64:8.640um-1.2m-116keV PHerc0813:20250821151723:9.362:9.362um-1.2m-113keV PHerc0191:20250821151635:9.362:9.362um-1.2m-113keV"}
# RULES G-GP part 4: <scroll>:<volume>:<um>:<seed file>. Seeds come from one patch's own surface points.
DENSE=${DENSE:-"PHerc0826:20250821151701:9.362:$D/gates/ggp/part5_seeds.json"}
# One warm tracer beats two cold ones on this disk. With two concurrent 9 um traces the normal-grid caches of two
# scrolls compete for a 30 GB disk that also holds two renders, the guard sits permanently at its tight 500 MB cap,
# and every trace refetches its grids: 40-generation traces measured 269 and 333 s with a warm cache against 886 and
# 1567 s while thrashing (median 535 s). One slot keeps a single scroll's cache under the cap and warm.
TRACERS=${TRACERS:-1}
export TRACE_SLOTS=${TRACE_SLOTS:-2}   # G-GP part 4 is all on one scroll, so a second slot costs no extra normal grids   # tracer_loop.sh and rsmall_loop.sh both read this
log(){ echo "[supervisor $(date -u +%FT%TZ)] $*"; }
# A worker restart moves the egress proxy to a new port; every long-running loop that fetches from S3 keeps the old
# HTTPS_PROXY in its environment and then fails every fetch (HTTP 0 / connection refused). stale_proxy <pid> is true
# when that process was started under a different HTTPS_PROXY than the current one: such loops are killed and restarted.
stale_proxy(){ local e; [ -r /proc/$1/environ ] || return 1; e=$(tr '\0' '\n' < /proc/$1/environ 2>/dev/null | grep -m1 '^HTTPS_PROXY=' | cut -d= -f2-); [ -n "$HTTPS_PROXY" ] && [ -n "$e" ] && [ "$e" != "$HTTPS_PROXY" ]; }
kill_tree(){ for c in $(pgrep -P $1); do kill_tree $c; done; kill -9 $1 2>/dev/null; }
# kill a loop by its pid file and make sure the guard below sees it gone (a stale pid file, or a child still being
# reaped, used to make the restart guard skip and leave the loop down)
kill_loop(){ local pf=$1; [ -f "$pf" ] || return 0; local p; p=$(cat "$pf"); kill_tree $p; for i in 1 2 3 4 5; do kill -0 $p 2>/dev/null || break; sleep 1; done; rm -f "$pf"; }
# 1. dockerd
if ! docker info >/dev/null 2>&1; then
  mkdir -p /var/run; (nohup dockerd --iptables=false --ip6tables=false --bridge=none --storage-driver=overlay2 --data-root=/var/lib/docker >> $D/logs/dockerd.log 2>&1 &)
  for i in $(seq 1 20); do docker info >/dev/null 2>&1 && break; sleep 1; done; log "dockerd started"
fi
# 2. gates queue
if ! grep -q 'all done' $D/logs/gates_queue.log 2>/dev/null && [ ! -f $D/gates/gateA/.tta_not_run ] && ! pgrep -f 'gates/queue.sh' >/dev/null; then
  (nohup nice -n 10 $D/gates/queue.sh >> $D/logs/gates_queue.log 2>&1 &); log "gates queue resumed"
fi
# 3. coverage: tracer loop (one process runs the seeds of a scroll sequentially; skips seeds with a .done marker)
for spec in $COVERAGE; do IFS=: read sc vol um pitch <<< "$spec"
  pidf=$D/patches/$sc/tracer_loop.pid
  if [ -f $pidf ] && kill -0 $(cat $pidf) 2>/dev/null && stale_proxy $(cat $pidf); then
    log "tracer loop of $sc holds a stale HTTPS_PROXY: restarting it (running tracer containers are stopped; their seeds are retraced)"
    kill_loop $pidf
    for c in $(docker ps -q); do docker inspect --format '{{.Path}} {{join .Args " "}}' $c | grep -q "vc_grow_seg_from_seed.*/$sc/" && docker kill $c >/dev/null; done
  fi
  # a marker patches/<sc>/tracer_paused (written by hand or by 4b below) keeps the tracer loop of that scroll down, e.g. while the
  # 2 um calibration needs the CPU; the read loop keeps running
  if [ -f $D/patches/$sc/tracer_paused ]; then
    # a pause must also stop a loop that is already running, or the marker only prevents a restart (the read_paused
    # branch below has always worked this way); the trace in flight finishes, the loop does not start another
    [ -f $pidf ] && kill -0 $(cat $pidf) 2>/dev/null && { kill_loop $pidf; log "tracer loop of $sc paused (tracer_paused marker)"; }
  elif ! { [ -f $pidf ] && kill -0 $(cat $pidf) 2>/dev/null; }; then
    (nohup bash $R/scripts/tracer_loop.sh $sc $vol $um $TRACERS >> $D/logs/tracer_loop_$sc.log 2>&1 &); log "tracer loop resumed for $sc"
  fi
  # 4. read loop (pid file; restarted when its HTTPS_PROXY is stale, see above)
  rpidf=$D/patches/$sc/read_loop.pid
  if [ -f $rpidf ] && kill -0 $(cat $rpidf) 2>/dev/null && stale_proxy $(cat $rpidf); then
    log "read loop of $sc holds a stale HTTPS_PROXY: restarting it"; kill_loop $rpidf
  fi
  # a marker patches/<sc>/read_paused holds that scroll's read loop down, e.g. to give the inference lock to a
  # declared experiment queue instead of to more coverage on an already well-covered volume
  if [ -f $D/patches/$sc/read_paused ]; then
    [ -f $rpidf ] && kill -0 $(cat $rpidf) 2>/dev/null && { kill_loop $rpidf; log "read loop of $sc paused (read_paused marker)"; }
  elif ! { [ -f $rpidf ] && kill -0 $(cat $rpidf) 2>/dev/null; }; then
    (nohup nice -n 10 bash -c "echo \$\$ > $rpidf; source $R/.venv/bin/activate && while true; do python $R/scripts/run_patch_dir.py $D/patches/$sc --scroll $sc --vol $vol --ckpt $D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth --tag ink9um_seed42+plain --no-tta --ledger $R/LEDGER.md --records $R/records/throughput.jsonl --delete-renders; sleep 300; done" >> $D/logs/read_loop_$sc.log 2>&1 &); log "read loop resumed for $sc"
  fi
done
# 4a0. RULES R-SMALL: the interior trace queues themselves (interior seeds at a reduced growth budget). Each stops on
# its own when the queue is exhausted or RSMALL_MAX traces exist; a marker patches/<scroll>_small/rsmall_paused holds it down.
for spec in $COVERAGE; do IFS=: read sc vol um pitch <<< "$spec"
  [ -f $R/seeds/${sc}_interior.json ] || continue
  sd=$D/patches/${sc}_small
  [ -f $sd/rsmall_paused ] && continue
  grep -q "interior queue done" $D/logs/rsmall_$sc.log 2>/dev/null && continue
  pf=$sd/rsmall_loop.pid
  if [ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null && stale_proxy $(cat $pf); then log "rsmall loop of $sc holds a stale HTTPS_PROXY: restarting it"; kill_loop $pf; fi
  if ! { [ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null; }; then
    (nohup bash $R/scripts/rsmall_loop.sh $sc $vol $um >> $D/logs/rsmall_$sc.log 2>&1 &); log "R-SMALL interior queue resumed for $sc"
  fi
done
# 4a0b. RULES G-GP part 4: the concentrated-seeding campaign. Seeds sampled from ONE patch's own surface points, so
# every trace starts on the same physical sheet; the queue stops on its own when the seed file is exhausted, and a
# marker patches/<scroll>_dense/dense_paused holds it down. Its reads run in 4a1b.
for spec in $DENSE; do IFS=: read sc vol um seeds <<< "$spec"
  # Do not resume a queue whose every declared seed already has its .done marker: the loop would start, find
  # nothing to do and exit, leaving a log line that reads as if the campaign were still running. G-GP part 5
  # finished at 07:41 UTC and the block kept announcing "dense queue resumed" afterwards.
  alldone=$($R/.venv/bin/python -c "
import json, os, sys
try: seeds = json.load(open('$seeds'))['seeds']
except Exception: sys.exit(0)
d = '$D/patches/${sc}_dense/logs'
print('yes' if seeds and all(os.path.exists('%s/seed_%s_%s_%s.done' % (d, s['x'], s['y'], s['z'])) for s in seeds) else 'no')" 2>/dev/null)
  [ "$alldone" = yes ] && continue
  [ -f $seeds ] || continue
  dd=$D/patches/${sc}_dense
  [ -f $dd/dense_paused ] && continue
  for part in $(seq 0 $(( ${DENSE_PARTS:-2} - 1 ))); do
    [ -f $dd/dense_part${part}_paused ] && continue
    pf=$dd/dense_loop_$part.pid
    if [ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null && stale_proxy $(cat $pf); then log "dense loop $part of $sc holds a stale HTTPS_PROXY: restarting it"; kill_loop $pf; fi
    if ! { [ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null; }; then
      (DENSE_PART=$part DENSE_PARTS=${DENSE_PARTS:-2} nohup bash $R/scripts/dense_loop.sh $sc $vol $um $seeds >> $D/logs/dense_$sc.log 2>&1 &); log "G-GP dense queue part $part resumed for $sc ($(basename $seeds))"
    fi
  done
done
# 4a1b. Reads for the dense campaign's patches: same scroll, volume, checkpoint and plain screening tag as every other
# read; only the patch directory differs. They share the _small inference lock, being the same size class.
for spec in $DENSE; do IFS=: read sc vol um seeds <<< "$spec"
  dd=$D/patches/${sc}_dense
  [ -d $dd ] || continue
  [ -f $dd/read_paused ] && continue
  dpidf=$dd/read_loop.pid
  if [ -f $dpidf ] && kill -0 $(cat $dpidf) 2>/dev/null && stale_proxy $(cat $dpidf); then
    log "read loop of ${sc}_dense holds a stale HTTPS_PROXY: restarting it"; kill_loop $dpidf
  fi
  if ! { [ -f $dpidf ] && kill -0 $(cat $dpidf) 2>/dev/null; }; then
    (nohup nice -n 10 bash -c "echo \$\$ > $dpidf; export HERCULES_INFER_LOCK=$D/logs/infer_small.lock; source $R/.venv/bin/activate && while true; do python $R/scripts/run_patch_dir.py $dd --scroll $sc --vol $vol --ckpt $D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth --tag ink9um_seed42+plain --no-tta --ledger $R/LEDGER.md --records $R/records/throughput.jsonl --delete-renders; sleep 300; done" >> $D/logs/read_loop_${sc}_dense.log 2>&1 &); log "read loop started for ${sc}_dense"
  fi
done
# 4a1. RULES R-SMALL and R-SMALL-2: the interior traces grown at a reduced budget live in patches/<scroll>_small and
# patches/<scroll>_rs2 and need their own read loop (same scroll, same volume, same checkpoint, same plain screening
# tag; only the patch directory differs).
# DEFECT FIXED 2026-09-19: this block covered _small only. R-SMALL-2 writes into _rs2, so its 15 traces sat QC'd by
# nobody and read by nobody, and its declared bar -- a READABLE FRACTION -- could never have been evaluated however
# long the tracer ran. The suffix is now a loop variable rather than a literal, so a future campaign that adds a
# suffix to RSMALL_SUFFIXES gets its reader with it instead of silently getting none.
for suf in ${RSMALL_SUFFIXES:-_small _rs2}; do
for spec in $COVERAGE; do IFS=: read sc vol um pitch <<< "$spec"
  sd=$D/patches/${sc}${suf}
  [ -d $sd ] || continue
  [ -f $sd/read_paused ] && continue
  spidf=$sd/read_loop.pid
  if [ -f $spidf ] && kill -0 $(cat $spidf) 2>/dev/null && stale_proxy $(cat $spidf); then
    log "read loop of ${sc}${suf} holds a stale HTTPS_PROXY: restarting it"; kill_loop $spidf
  fi
  if ! { [ -f $spidf ] && kill -0 $(cat $spidf) 2>/dev/null; }; then
    # The R-SMALL reads get their OWN inference lock. The global lock exists because two big concurrent inferences
    # oversubscribe 4 cores; a 2.2 cm2 interior read is ~3 minutes against the 25-70 minutes an R-CREST-POWER read
    # holds the lock, so serialising them behind it starves the experiment that could unlock scroll interiors while
    # costing the other one almost nothing. They still serialise among themselves.
    (nohup nice -n 10 bash -c "echo \$\$ > $spidf; export HERCULES_INFER_LOCK=$D/logs/infer_small.lock; source $R/.venv/bin/activate && while true; do python $R/scripts/run_patch_dir.py $sd --scroll $sc --vol $vol --ckpt $D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth --tag ink9um_seed42+plain --no-tta --ledger $R/LEDGER.md --records $R/records/throughput.jsonl --delete-renders; sleep 300; done" >> $D/logs/read_loop_${sc}${suf}.log 2>&1 &); log "read loop resumed for ${sc}${suf}"
  fi
done
done
# 4a3. RULES R-CREST-POWER, the PHerc1203 members on their own inference lock (the informative half; see RULES)
n1203=$(while read sc pt; do [ -z "$sc" ] && continue; [ -f $D/patches/$sc/$pt/read_ink9um_seed42_plain_nocrest/.read_complete ] || echo x; done < $R/records/rcrest_power_1203.txt | wc -l)
[ -f $D/logs/rcrest_power_1203_paused ] && n1203=0     # the pause must be tested BEFORE the queue is resumed
# DEFECT FIXED 2026-09-19 10:38 UTC: rcrest_power.sh runs the FULL declared 12-member phase-1 list, which INCLUDES
# these three PHerc1203 members. With both queues alive, two run_patch_dir processes wrote the same read directory
# at once -- observed, two `--only team_20251005230830031` readers in flight. That is the R-DEPTH shape: two writers,
# one output. A pause marker is not enough because a marker can be cleared (which is how this happened); the real
# invariant is ONE QUEUE, so the subset queue stands down whenever the full queue is alive, marker or no marker.
if [ -f $D/logs/rcrest_power.pid ] && kill -0 "$(cat $D/logs/rcrest_power.pid 2>/dev/null)" 2>/dev/null; then
  n1203=0; log "rcrest_power.sh (full phase-1 queue) is running; the PHerc1203 subset queue stands down"
fi
if [ "$n1203" -gt 0 ]; then
  pf=$D/logs/rcrest_power_1203.pid
  if [ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null && stale_proxy $(cat $pf); then log "rcrest_power_1203 holds a stale HTTPS_PROXY: restarting it"; kill_loop $pf; fi
  if ! { [ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null; }; then
    (nohup nice -n 10 bash $R/scripts/rcrest_power_1203.sh >> $D/logs/rcrest_power_1203.log 2>&1 &); log "R-CREST-POWER PHerc1203 queue resumed"
  fi
fi
# 4a2. RULES R-CREST-POWER phase 1: the VOID-surface re-read queue, resumed until its own log says it is complete
rcp_left=$(while read sc pt; do [ -z "$sc" ] && continue; [ -f $D/patches/$sc/$pt/read_ink9um_seed42_plain_nocrest/.read_complete ] || echo x; done < $R/records/rcrest_power_phase1.txt | wc -l)
[ -f $D/logs/rcrest_power_paused ] && rcp_left=0        # the pause must be tested BEFORE the queue is resumed
if [ "$rcp_left" -gt 0 ]; then
  pf=$D/logs/rcrest_power.pid
  if [ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null && stale_proxy $(cat $pf); then log "rcrest_power holds a stale HTTPS_PROXY: restarting it"; kill_loop $pf; fi
  if ! { [ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null; }; then
    (nohup nice -n 10 bash $R/scripts/rcrest_power.sh >> $D/logs/rcrest_power.log 2>&1 &); log "R-CREST-POWER phase 1 resumed"
  fi
fi
# 4b. Gate C TTA is paused (SIGSTOP, marker logs/gateC_tta_paused) while the w028 2 um calibration runs: resume it when both
# calibration orders are complete (or the calibration process is gone).
if [ -f $D/logs/gateC_tta_paused ]; then gp=$(cut -d' ' -f1 $D/logs/gateC_tta_paused)
  if ! kill -0 $gp 2>/dev/null; then rm -f $D/logs/gateC_tta_paused
  elif [ -f $D/w028_2um/calib_out/.complete_reverse ] || ! pgrep -f 'run_2um.py.*calib' >/dev/null; then kill -CONT $gp && rm -f $D/logs/gateC_tta_paused && log "gateC TTA resumed (pid $gp)"; fi
fi
if [ -f $D/w028_2um/calib_out/.complete_reverse ] || ! pgrep -f 'run_2um.py.*calib' >/dev/null; then
  for m in $D/patches/*/tracer_paused; do [ -f "$m" ] && grep -q calibration "$m" && rm -f "$m" && log "tracer pause lifted: $m"; done
fi
# VC3D processes run inside containers (children of containerd, not of the nice'd docker client): keep them below the readers
for p in $(pgrep -f '^/opt/vc/bin/vc_grow_seg_from_seed'); do renice -n 15 -p $(ls /proc/$p/task 2>/dev/null) >/dev/null 2>&1; done
for p in $(pgrep -f '^/opt/vc/bin/vc_render_tifxyz'); do renice -n 10 -p $(ls /proc/$p/task 2>/dev/null) >/dev/null 2>&1; done
# the 2 um calibration/reads (run_2um.py) get the CPU first: all their threads at nice 0
for p in $(pgrep -f 'scripts/run_2um.py'); do renice -n 0 -p $(ls /proc/$p/task 2>/dev/null) >/dev/null 2>&1; done
# control-gate inference (gates/) runs on spare cycles only: the coverage reads are what find letters
for p in $(pgrep -f 'inference.infer .*/controls/'); do renice -n 19 -p $(ls /proc/$p/task 2>/dev/null) >/dev/null 2>&1; done
# 4c. logs/yield_pids: background CPU jobs (the 2 um calibration) that every 9 um inference stops while it runs and
# continues afterwards (run_patch_dir.stage). Dead pids are dropped; a stray stopped pid with no inference running is continued.
if [ -f $D/logs/yield_pids ]; then live=""; for p in $(cat $D/logs/yield_pids); do kill -0 $p 2>/dev/null && live="$live $p"; done
  echo $live > $D/logs/yield_pids; [ -z "$live" ] && rm -f $D/logs/yield_pids
  if ! pgrep -f 'inference.infer' | grep -v "^$(cut -d' ' -f1 $D/logs/gateC_tta_paused 2>/dev/null)$" | grep -q . ; then for p in $live; do kill -CONT $p 2>/dev/null; done; fi
fi
# 4d. published surface volumes: the team's own renders of their curated segments on PHerc1447 and PHerc0800.
# fetch_surface_volumes.py keeps at most 2 unread stacks on disk per scroll and stops below 4 GB free; the read loop
# deletes each stack once its read is in the ledger. Nothing to fetch on the other eligible volumes.
for sc in PHerc1447 PHerc0800; do
  pf=$D/logs/fetch_sv_$sc.pid
  if [ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null && stale_proxy $(cat $pf); then
    log "surface-volume fetch loop of $sc holds a stale HTTPS_PROXY: restarting it"; kill_loop $pf
  fi
  # a fetcher started before a worker restart keeps the old proxy port and fails every request: drop any stray one
  for q in $(pgrep -f "fetch_surface_volumes.py $sc"); do
    [ -f $pf ] && [ "$q" = "$(cat $pf)" ] && continue
    stale_proxy $q && { kill -9 $q 2>/dev/null; log "killed stray $sc fetcher $q (stale proxy)"; }
  done
  if ! { [ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null; }; then
    (nohup bash -c "echo \$\$ > $pf; exec $R/.venv/bin/python $R/scripts/fetch_surface_volumes.py $sc --max-ahead 2 --min-free-gb 4 --loop 120" >> $D/logs/fetch_sv_$sc.log 2>&1 &); log "surface-volume fetch loop started for $sc"
  fi
done
# 4b2. RULES G-GP part 5: fire the consensus build the moment the dense queue finishes, so the hours between the
# last trace and the build are not lost to waiting for a check-in. The script is a no-op unless every declared
# part-5 seed has its .done marker and no dense loop is alive, and it refuses to run twice.
if [ ! -d $D/patches/PHerc0826_cons_part5 ] && ! pgrep -f "ggp5_when_ready.sh" >/dev/null; then
  (nohup bash $R/scripts/ggp5_when_ready.sh >> $D/logs/ggp5.log 2>&1 &)
fi
# 4b1. Integrity audits, run every check-in rather than whenever someone happens to look. A truncated reverse map
# INFLATES the rule 5.5 margin (unwritten pixels read as zero), so it pushes toward false positives; and a read that
# happened but was never ledgered is the one gap that cannot be reconstructed once its maps are pruned.
if ! pgrep -f "map_integrity.py" >/dev/null; then
  (nohup nice -n 18 $R/.venv/bin/python $R/scripts/map_integrity.py --json $D/gates/integrity/maps.json \
     >> $D/logs/integrity.log 2>&1 || true &)
fi
# Report the LATEST audit only, and loudly only when it found something. Tailing the whole log printed the same
# clean summary three times per check-in, and a log that repeats itself hides the one line that matters.
last=$(grep -n "^checked .* pairs;" $D/logs/integrity.log 2>/dev/null | tail -1 | cut -d: -f1)
if [ -n "$last" ]; then
  summary=$(sed -n "${last}p" $D/logs/integrity.log)
  case "$summary" in
    *", 0 SUSPECT") log "map integrity: $summary" ;;
    *) log "MAP INTEGRITY: $summary"
       sed -n "$((last+1)),\$p" $D/logs/integrity.log | grep -E "SUSPECT|          " | head -6 | \
         while read -r l; do log "  $l"; done ;;
  esac
fi
$R/.venv/bin/python $R/scripts/ledger_audit.py > $D/logs/ledger_audit.log 2>&1 || \
  log "LEDGER AUDIT FAILED: $(grep -c UNRECORDED $D/logs/ledger_audit.log) read(s) on disk with no ledger line"
# 4b4. Remove a KILLED read's leftover maps before a later run can pair a fresh reverse with a stale forward.
# Conservative by construction: no .read_complete, at least one .tif, and untouched for 6 h (the longest observed
# single-direction write is 1.9 h, from map_integrity's STALE measurements). Added 2026-09-19 after this bit twice
# in one morning: a resumed R-CREST-POWER found a leftover from the previous day, and a sweep then found two more.
$R/.venv/bin/python $R/scripts/sweep_partial_reads.py --go 2>&1 | grep -v "^no partial reads" | while read -r l; do log "$l"; done
# 4b3. RULES R-SMALL-2: start the newly-admitted-band interior queue as soon as G-GP part 5 stops tracing, so the
# trace slots are never idle. The script is a no-op while part 5 still has seeds, honours its own pause marker and
# refuses to start a second loop for a scroll that already has one.
if ! pgrep -f "rsmall2_when_ready.sh" >/dev/null; then
  (nohup bash $R/scripts/rsmall2_when_ready.sh >> $D/logs/rsmall2.log 2>&1 &)
fi
# 4c. RULES R-DEPTH and R-BEST: two declared experiments that are not part of any scroll loop. Both are idempotent
# (R-DEPTH skips a window whose .infer_complete marker exists; R-BEST skips a surface that already has its
# read_stats.json), so resuming them after a worker or container restart costs nothing and losing them costs hours.
# rdepth_part2 is what the ADMITTED verdict owes: the declared re-read set at the two off-centre windows. It is
# idempotent (it skips any surface/window whose read_*/.read_complete exists) and pausable by a marker, and like
# R-DEPTH it renders, so it keeps the stale-proxy check.
for job in rdepth rdepth_part2 rbest rbest2; do
  case $job in
    rdepth) done_file=$D/gates/rdepth/rdepth.json; done_test='verdict_not_pending' ;;
    rdepth_part2) done_file=$D/logs/rdepth_part2.log; done_test='grep2' ;;
    rbest)  done_file=$D/logs/rbest.log;           done_test='grep' ;;
    rbest2) done_file=$D/logs/rbest2.log;          done_test='grep' ;;
  esac
  # part 2 only starts once R-DEPTH itself has a verdict, and only if that verdict admitted an off-centre window
  if [ "$job" = rdepth_part2 ]; then
    adm=$($R/.venv/bin/python -c "
import json
try:
    d=json.load(open('$D/gates/rdepth/rdepth.json')); print('yes' if d.get('verdict')=='ADMITTED' else 'no')
except Exception: print('no')" 2>/dev/null)
    [ "$adm" = yes ] || continue
    [ -f $D/gates/rdepth/part2_paused ] && continue
  fi
  if [ "$done_test" = verdict_not_pending ]; then
    v=$($R/.venv/bin/python -c "
import json,sys
try: print(json.load(open('$done_file')).get('verdict',''))
except Exception: print('')" 2>/dev/null)
    [ -n "$v" ] && [ "$v" != PENDING ] && continue
  elif [ "$done_test" = grep2 ]; then
    grep -q "queue done" "$done_file" 2>/dev/null && continue
  else
    grep -q "every population member has its +tta read" "$done_file" 2>/dev/null && continue
  fi
  pf=$D/logs/$job.pid
  # The stale-proxy restart exists for jobs that FETCH. R-DEPTH reads a local render, a local checkpoint and local
  # labels and makes no network call at all, so restarting it for a stale proxy only destroys work: it cost 77 minutes
  # of a 2048x2048 inference on 2026-09-18. R-BEST does render, so it keeps the check.
  if [ "$job" != rdepth ] && [ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null && stale_proxy $(cat $pf); then
    log "$job holds a stale HTTPS_PROXY: restarting it"; kill_loop $pf
  fi
  if ! { [ -f $pf ] && kill -0 $(cat $pf) 2>/dev/null; }; then
    (nohup bash -c "echo \$\$ > $pf; exec bash $R/scripts/$job.sh" >> $D/logs/$job.log 2>&1 &); log "$job resumed"
  fi
done
# 5. disk guard (every 60 s): the policy lives in scripts/disk_guard.sh, as its own FILE so that `bash -n` parses it.
# It was an inline `bash -c` string until 2026-09-18, when a stray quote inside it killed the guard silently - the
# supervisor parsed fine because the body was just a string to it. Nothing here should go back to being inline.
if ! { [ -f $D/logs/disk_guard.pid ] && kill -0 $(cat $D/logs/disk_guard.pid) 2>/dev/null; }; then
  [ -f $D/logs/disk_guard.pid ] && kill $(cat $D/logs/disk_guard.pid) 2>/dev/null
  (HERCULES_DATA=$D HERCULES_ROOT=$R nohup bash $R/scripts/disk_guard.sh 60 >> $D/logs/disk_guard.log 2>&1 &
   sleep 1; pgrep -f "disk_guard.sh 60" | head -1 > $D/logs/disk_guard.pid)
  log "disk guard started (60 s, scripts/disk_guard.sh)"
fi
# 6. review folder refresh (5.12) every 10 min
if ! { [ -f $D/logs/review_loop.pid ] && kill -0 $(cat $D/logs/review_loop.pid) 2>/dev/null; }; then
  (nohup nice -n 15 bash -c 'echo $$ > '$D'/logs/review_loop.pid; source '$R'/.venv/bin/activate; python '$R'/scripts/review_folder.py --reads-root '$D'/patches --out '$R'/review_sheets --loop 10' >> $D/logs/review_loop.log 2>&1 &); log "review loop started"
fi
log "state: $(pgrep -fc '^/opt/vc/bin/vc_grow_seg_from_seed') tracer(s), $(pgrep -fc 'inference.infer') inference, disk $(df -h / | awk 'NR==2{print $4}') free"
