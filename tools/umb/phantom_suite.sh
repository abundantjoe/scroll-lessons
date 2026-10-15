#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-UMB-2 bar B6 (+A1 item 3): flattened-roll phantoms at 8.64 um geometry (pitch 450 um, sheet 150 um, aspect 0.1-0.25, seams
# every 1-4 mm, debris, stripes, noise; concentric arcs with outer radius >= 20 mm and innermost radius 1-5 mm) run through
# core_native v2 (npy mode); pass = z_c within 1 pitch AND both slit ends within 2 pitches on >= 95 % of sections.
# usage: phantom_suite.sh <out_dir> [n_sec=16]   output: <out_dir>/case_<k>/{phantom.json,core_native.json}, <out_dir>/summary.json
set -uo pipefail; O=$1; N=${2:-16}; REPO=/home/user/dominion; cd $REPO; mkdir -p $O; PY=/opt/hv/bin/python
# cases: width_mm, n_wind, r_in_um, seam_mm, seam_shift, noise, seed  (outer radius = r_in + (n_wind-1) * 0.45 mm; A1 item 3: outer >= 20 mm, innermost 1-5 mm)
CASES="50 42 2000 2.5 1.5 0.12 0
56 44 1500 1.5 1.0 0.12 1
60 44 4000 4.0 2.0 0.15 2
52 46 1000 1.0 1.0 0.10 3
58 40 5000 3.0 1.5 0.18 4
54 48 3000 2.0 0.5 0.12 5"
k=0; echo "$CASES" | while read wid nw rin seam shift noise seed; do
  C=$O/case_$k; mkdir -p $C; [ -f $C/core_native.json ] && { k=$((k+1)); continue; }
  $PY tools/unr/phantom_flatroll.py /dev/shm/phantom_$k.npy $C/phantom.json --n_sec $N --n_wind $nw --width_mm $wid --r_in_um $rin --seam_mm $seam --seam_shift $shift --noise $noise --seed $seed --png $C/preview.png > $C/gen.log 2>&1 || { echo "gen failed case $k: $(tail -1 $C/gen.log)"; k=$((k+1)); continue; }
  YS=$($PY -c "print(' '.join(str(i) for i in range(0,$N,max(1,$N//8))))")
  $PY tools/umb/core_native.py $C --npy /dev/shm/phantom_$k.npy --truth $C/phantom.json --cache "" --y $YS > $C/core_native.log 2>&1
  rm -f /dev/shm/phantom_$k.npy; k=$((k+1))
done
$PY - <<PY
import json,glob,numpy as np
P=0.45; rows=[]
for f in sorted(glob.glob('$O/case_*/core_native.json')):
    d=json.load(open(f)); T=json.load(open(f.replace('core_native.json','phantom.json')))
    for r in d['records']:
        ok_zc = r.get('err_zc_mm') is not None and r['err_zc_mm'] <= P; ok_sl = r.get('err_slit_mm') is not None and max(r['err_slit_mm']) <= 2*P
        rows.append({'case': f.split('/')[-2], 'y': r['y'], 'err_zc_mm': r.get('err_zc_mm'), 'err_slit_mm': r.get('err_slit_mm'), 'pass': bool(ok_zc and ok_sl), 'L_status': r['left'].get('status'), 'R_status': r['right'].get('status')})
n=len(rows); p=sum(q['pass'] for q in rows); summ={'declaration':'DECL-UMB-2 B6 + A1 item 3','pitch_mm':P,'n_sections':n,'n_pass':p,'pass_frac':round(p/max(n,1),3),'B6_pass':bool(n>0 and p/n>=0.95),'rows':rows}
json.dump(summ,open('$O/summary.json','w'),indent=1); print(json.dumps({k:summ[k] for k in summ if k!='rows'}))
PY
