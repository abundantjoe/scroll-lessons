#!/bin/bash
# RULES G-GP part 6: fires only after the G-OWN trace has finished, because G-OWN can make part 6 pointless.
set -uo pipefail
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
sc=PHerc0826; vol=20250821151701; um=9.362; X=3590; Y=2095; Z=4179
log(){ echo "[ggp6 $(date -u +%FT%TZ)] $*"; }
while kill -0 "$(cat $D/patches/PHerc0139_gown/gown.pid 2>/dev/null)" 2>/dev/null; do sleep 60; done
log "G-OWN trace finished; building part 6 (th 8) then part 6b (th 10)"
for spec in "6 8" "6b 10"; do
  set -- $spec; part=$1; th=$2
  [ -d "$D/patches/${sc}_cons_part${part}" ] && { log "part $part already built"; continue; }
  log "part $part at consensus_default_th $th"
  PART=$part bash $R/scripts/ggp4_consensus.sh "$sc" "$vol" "$um" "$X" "$Y" "$Z" "$th" 2>&1 | tail -6
done
log "measuring grid fill for every threshold on record"
$R/.venv/bin/python - <<'PY'
import glob, json, os, numpy as np, tifffile
rows=[]
for part in ("4","5","5b","6","6b"):
    for d in sorted(glob.glob(os.environ.get("HERCULES_DATA", "/home/user/hercules_data") + "/patches/PHerc0826_cons_part%s/auto_*" % part)):
        try:
            x=tifffile.imread(d+"/x.tif"); y=tifffile.imread(d+"/y.tif"); z=tifffile.imread(d+"/z.tif")
        except Exception: continue
        ok=np.isfinite(x)&np.isfinite(y)&np.isfinite(z)&(x>0)&(y>0)&(z>0)
        m=json.load(open(d+"/meta.json"))
        rows.append(dict(part=part, surface=os.path.basename(d), grid=list(ok.shape),
                         valid_nodes=int(ok.sum()), grid_fill=float(ok.mean()), area_cm2=m.get("area_cm2")))
        print("part %-3s %-52s grid %3dx%-3d fill %.3f area %s" %
              (part, os.path.basename(d)[:52], ok.shape[0], ok.shape[1], ok.mean(), round(m.get("area_cm2") or 0, 2)))
json.dump(rows, open(os.environ.get("HERCULES_DATA", "/home/user/hercules_data") + "/gates/ggp/part6_fill.json","w"), indent=1, sort_keys=True)
PY
log "part 6 build complete; reads are the supervisor's job from here"
