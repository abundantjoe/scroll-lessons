# Provenance: Project HERCULES | owner the owner | [id removed]
# Usage: bash ledger_run.sh <output_path_or_-> <logfile> <command...>
# Runs the command, appends a row to logs/sib/fl2-pherc0813/ledger.tsv (copy of tools/c3/ledger_run.sh):
# host gpu(cpu) command start_utc end_utc exit output_sha256
# output_sha256: file -> sha256 of file; directory -> sha256 of its sorted "sha256  relpath" manifest; '-' -> '-'.
out="$1"; shift; log="$1"; shift
LEDGER=/home/user/dominion/logs/sib/fl2-pherc0813/ledger.tsv
start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" > "$log" 2>&1
rc=$?
end=$(date -u +%Y-%m-%dT%H:%M:%SZ)
if [ "$out" = "-" ]; then h="-"
elif [ -f "$out" ]; then h=$(sha256sum "$out" | cut -d' ' -f1)
elif [ -d "$out" ]; then h=$(cd "$out" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)
else h="missing"; fi
cmd=$(printf '%q ' "$@" | tr '\t\n' '  ')
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$(hostname)" cpu "$cmd" "$start" "$end" "$rc" "$h" >> "$LEDGER"
echo "rc=$rc start=$start end=$end out_sha256=$h"
exit $rc
