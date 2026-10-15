#!/bin/bash
# Run protocol 9 for the surface a read_stats.json belongs to, deriving every argument from the record itself.
# At the moment a candidate appears, the one thing that must not go wrong is composing the command: the patch lives
# in patches/<scroll>_cons_partN or _small or _dense, the volume id must come from the supervisor's COVERAGE string
# and never from memory, and um comes from the read's own stats. This does that and then runs protocol9.sh.
# It ALWAYS does the dry run first and refuses to continue if any input is missing.
#   protocol9_for.sh <path/to/read_stats.json> [--go]
set -uo pipefail
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
[ $# -ge 1 ] || { echo "usage: protocol9_for.sh <read_stats.json> [--go]" >&2; exit 2; }
stats=$1; go=${2:-}
[ -f "$stats" ] || { echo "no such read_stats.json: $stats" >&2; exit 2; }
patch=$(cd "$(dirname "$(dirname "$stats")")" && pwd)
dir=$(basename "$(dirname "$patch")")          # e.g. PHerc0826_cons_part5
sc=${dir%%_*}
um=$($R/.venv/bin/python -c "import json;print(json.load(open('$stats'))['um_per_px'])")
vol=$($R/.venv/bin/python -c "
import re
cov=re.search(r'COVERAGE=\\\$\\{COVERAGE:-\"([^\"]*)\"\\}', open('$R/scripts/supervisor.sh').read()).group(1)
m={p.split(':')[0]: p.split(':')[1] for p in cov.split()}
print(m.get('$sc',''))")
[ -n "$vol" ] || { echo "no COVERAGE volume id for $sc (from directory $dir)" >&2; exit 2; }
echo "protocol 9 for $sc vol $vol um $um"
echo "  patch: $patch"
echo "  read:  $stats"
$R/.venv/bin/python -c "
import json;d=json.load(open('$stats'));r=d.get('rule55') or {};t=(r.get('units') or r).get('0.5cm2') or {}
print('  verdict %s | onsheet %.2f cm2 | FLAGGED %s of %s | largest cluster %s'
      % (d.get('verdict'), d.get('onsheet_cm2') or 0, t.get('n_flagged'), t.get('n_valid'), t.get('largest_cluster')))"
echo "--- dry run"
P9_DRY=1 bash $R/scripts/protocol9.sh "$sc" "$vol" "$um" "$patch" || { echo "DRY RUN FAILED -- not running protocol 9" >&2; exit 1; }
[ "$go" = "--go" ] || { echo; echo "dry run clean. Re-run with --go to execute protocol 9."; exit 0; }
echo "--- executing protocol 9"
exec bash $R/scripts/protocol9.sh "$sc" "$vol" "$um" "$patch"
