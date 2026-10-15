#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# D3 stage 2 ledger wrapper (tools/c3/ledger_run.sh convention, D3 ledger and run_arms.sh columns).
# Usage: d3_ledger_run.sh <threads> <output_path_or_-> <logfile> <command...>
# Runs the command with OMP/MKL/OPENBLAS/NUMEXPR threads = <threads>, stdout+stderr -> <logfile>, then appends
# host, cpu, command, start_utc, end_utc, exit, output_sha256 to /work/d3/work/ledger.tsv.
# output_sha256: file -> sha256 of the file; directory -> sha256 of its sorted "sha256  ./relpath" manifest; '-' -> '-'.
T="$1"; shift; out="$1"; shift; log="$1"; shift
LEDGER=/work/d3/work/ledger.tsv
export OMP_NUM_THREADS=$T MKL_NUM_THREADS=$T OPENBLAS_NUM_THREADS=$T NUMEXPR_NUM_THREADS=$T PYTHONDONTWRITEBYTECODE=1
start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" > "$log" 2>&1
rc=$?
end=$(date -u +%Y-%m-%dT%H:%M:%SZ)
if [ "$out" = "-" ]; then h="-"
elif [ -f "$out" ]; then h=$(sha256sum "$out" | cut -d' ' -f1)
elif [ -d "$out" ]; then h=$(cd "$out" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)
else h="missing"; fi
cmd="OMP_NUM_THREADS=$T MKL_NUM_THREADS=$T OPENBLAS_NUM_THREADS=$T NUMEXPR_NUM_THREADS=$T $(printf '%q ' "$@" | tr '\t\n' '  ')"
CPU="cpus=$T/$(getconf _NPROCESSORS_ONLN) $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$(hostname)" "$CPU" "$cmd" "$start" "$end" "$rc" "$h" >> "$LEDGER"
echo "rc=$rc start=$start end=$end out_sha256=$h"
exit $rc
