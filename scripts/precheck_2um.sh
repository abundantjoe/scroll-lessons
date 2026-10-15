#!/bin/bash
# Pre-checks for 2.4 um rescan traces: QC 5.8 (geometry + CT mask) and R-CREST-CT (crest in the CT along the trace
# normals) for every traced patch under patches_2um/<scroll>; loops until the trace queue is done and nothing is pending.
# Usage: precheck_2um.sh <scroll> <rescan-volume-id> <pitch e.g. 2.403um-0.2m-77keV>
sc=$1; vol=$2; pitch=$3; D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
VURL="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/$sc/volumes/$vol-$pitch-masked.zarr"
source $R/.venv/bin/activate
while true; do
  pending=0
  for p in $D/patches_2um/$sc/auto_grown_*; do
    [ -f $p/meta.json ] || continue
    if [ ! -f $p/qc.json ]; then
      echo "[precheck_2um $(date -u +%FT%TZ)] QC $(basename $p)"
      python $R/scripts/patch_qc.py $p --um 9.612 --coord-scale 4 --ct-url $VURL --overlay $p/qc_overlay.png --cache $D/ct_l4_cache/${sc}_$vol 2>&1 | tail -2
    fi
    # R-CREST on a render at the trace's own pitch (28 slices x 9.612 um on pyramid level 2, the 9 um-route render): the
    # established render bar decides; R-CREST-CT stays recorded as a diagnostic (blind in tightly packed wraps)
    if [ -f $p/qc.json ] && [ "$(python -c "import json;print(json.load(open('$p/qc.json')).get('verdict'))")" = PASS ] && [ ! -f $p/render_l2_crest.json ]; then
      echo "[precheck_2um $(date -u +%FT%TZ)] L2 render + R-CREST $(basename $p)"
      RENDER_SLICES=28 RENDER_GROUP=2 RENDER_AUTOCROP=0 RENDER_ARGS="--scale-segmentation 4" VC_THREADS=2 RENDER_CACHE_GB=3 \
        bash $R/scripts/vc_tools.sh render $sc $vol $pitch 9.612 $p $p/render_l2.zarr >/dev/null 2>&1 && \
        python $R/scripts/render_crest.py $p/render_l2.zarr $p/render_l2_crest.json 2>&1 | tail -1 | cut -c1-400
      # R-COVER per grid cell (no auto-crop: 20 px = one tifxyz cell) and the 1 cm^2 window that maximises papyrus coverage
      [ -f $p/render_l2_crest.json ] && python $R/scripts/render_cover.py $p/render_l2.zarr $p/render_l2_cover.json --thr 60 --bar 0.80 --cell-px 20 | cut -c1-200
      [ -f $p/render_l2_cover.json ] && python $R/scripts/window_2um.py $p | python -c "import json,sys; d=json.load(sys.stdin); print('window: cells (%d,%d) coverage %s valid %d/%d' % (d['cell_i0'], d['cell_j0'], d['window_coverage_l2'], d['valid_cells'], d['total_cells']))"
      [ -f $p/render_l2_cover.json ] && rm -rf $p/render_l2.zarr   # 5.13: renders are not kept; profile and coverage grid are in the JSONs
    fi
    if [ ! -f $p/ct_points_check.json ]; then
      echo "[precheck_2um $(date -u +%FT%TZ)] R-CREST-CT $(basename $p)"
      python $R/scripts/ct_at_points.py $p --volume-url $VURL --level 3 --coord-div 2 --half 16 --cache $D/patches_2um/ct_points_cache/${sc}_level3 2>&1 | tail -2
      rm -rf $D/patches_2um/ct_points_cache   # diagnostic only since R-CREST-CT was superseded: do not keep its chunks on this small disk
    fi
    # a trace that passes QC, R-CREST (L2 render) and R-COVER (best window) goes straight to the 2.4 um render + read
    if [ -f $p/render_l2_crest.json ] && [ -f $p/window_2um.json ] && [ ! -f $p/.run_2um_launched ] && ! pgrep -f 'scripts/run_2um_patch.sh' >/dev/null; then
      if python -c "import json,sys; c=json.load(open('$p/render_l2_crest.json')); w=json.load(open('$p/window_2um.json')); sys.exit(0 if c.get('passed') and (w.get('window_coverage_l2') or 0) >= 0.80 else 1)"; then
        echo "[precheck_2um $(date -u +%FT%TZ)] PASS crest+cover -> launching run_2um_patch for $(basename $p)"; date -u +%FT%TZ > $p/.run_2um_launched
        (nohup bash $R/scripts/run_2um_patch.sh $sc $vol $pitch 2.403 $p >> $D/logs/run_2um_patch_$(basename $p).log 2>&1 &)
      fi
    fi
    ok=0; [ -f $p/qc.json ] && [ -f $p/ct_points_check.json ] && { [ "$(python -c "import json;print(json.load(open('$p/qc.json')).get('verdict'))")" != PASS ] || { [ -f $p/render_l2_crest.json ] && [ -f $p/render_l2_cover.json ] && [ -f $p/window_2um.json ]; }; } && ok=1
    [ $ok -eq 1 ] || pending=1
    # ledger line (5.11) for a trace that stops here (QC not PASS, or VOID by R-CREST on the L2 render); a passing trace gets its line from read_chart later
    [ $ok -eq 1 ] && python - "$p" "$sc" "$R/LEDGER.md" <<'PY'
import json, sys, os, datetime
p, sc, ledger = sys.argv[1:4]; name = os.path.basename(p)
key = f"{sc}|{name}|0|ink_canonical_2um|both"; esc = key.replace("|", "\\|")
txt = open(ledger).read()
if esc in txt: sys.exit(0)
q = json.load(open(f"{p}/qc.json")); c = json.load(open(f"{p}/ct_points_check.json")); m = json.load(open(f"{p}/meta.json"))
rc = json.load(open(f"{p}/render_l2_crest.json")) if os.path.exists(f"{p}/render_l2_crest.json") else None
wj = json.load(open(f"{p}/window_2um.json")) if os.path.exists(f"{p}/window_2um.json") else {}
wcov = wj.get("window_coverage_l2")
if q.get("verdict") == "PASS" and rc is not None and rc.get("passed") and wcov is not None and wcov >= 0.80: sys.exit(0)
seed = " ".join(str(int(v)) for v in m.get("seed", []))
ct = f"R-CREST-CT ratio {c.get('crest_ratio')} at {c.get('crest_offset'):+d} vx (diagnostic)"
if q.get("verdict") != "PASS":
    verdict = q.get("verdict"); note = f"seed {seed}; QC 5.8 {verdict} (area {q.get('area_cm2', 0):.2f} cm², mean|nz| {q.get('mean_abs_nz', 0):.3f}); {ct}; not rendered at 2.4 um, no inference"
elif rc is not None and not rc.get("passed"):
    verdict = "VOID"; note = (f"seed {seed}; QC PASS {q.get('area_cm2', 0):.2f} cm²; R-CREST on the 28-slice 9.612 um render: ratio {rc.get('ratio')}, crest slice {rc.get('crest_slice')} (central {rc.get('central_bounds')}), on-sheet {rc.get('onsheet_frac_mid', 0):.2f}; {ct}; not rendered at 2.4 um, no inference")
else:
    verdict = "VOID-COVER"; note = (f"seed {seed}; QC PASS {q.get('area_cm2', 0):.2f} cm²; R-CREST on the 9.612 um render PASS (ratio {rc.get('ratio')}, crest slice {rc.get('crest_slice')}) but R-COVER: best 1 cm² window sees papyrus on {wcov} of its pixels (bar >= 0.80; whole trace {json.load(open(f'{p}/render_l2_cover.json')).get('coverage')}); not rendered at 2.4 um, no inference")
line = f"| {datetime.date.today().isoformat()} | {esc} | - | - | - | - | - | - | {verdict} | {note} |\n"
anchor = "\n## Throughput"
i = txt.find(anchor)
txt = (txt[:i].rstrip("\n") + "\n" + line + txt[i:]) if i > 0 else txt.rstrip("\n") + "\n" + line
open(ledger, "w").write(txt); print("[precheck_2um] ledger line:", verdict, name)
PY
  done
  if grep -q 'all done' $D/logs/trace_queue_2um.log 2>/dev/null && [ $pending -eq 0 ] && ! pgrep -f "trace_queue.sh|trace_seeds_2um.sh" >/dev/null; then echo "[precheck_2um] done"; break; fi
  sleep 120
done
