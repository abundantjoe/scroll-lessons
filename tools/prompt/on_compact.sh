#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# SessionStart hook (matcher "compact"): standing order STANDING-ORDER-COMPACT (RULES.md).
# Prints a JSON hook result whose additionalContext tells the agent what to do after a context condensation.
cd "$(dirname "$0")/../.." || exit 0
latest=$(ls configs/prompt/hercules_master_v*.md 2>/dev/null | sort -V | tail -1)
[ -n "$latest" ] || latest="(none committed yet: use the newest scratchpad prompt_v*.txt)"
ver=$(basename "$latest" | sed -n 's/^hercules_master_v\([0-9]*\)\.md$/\1/p')
next=$(( ${ver:-6} + 1 ))
now=$(date -u +%Y-%m-%dT%H:%MZ)
python3 - "$latest" "$next" "$now" <<'EOF'
import json, sys
latest, nxt, now = sys.argv[1], sys.argv[2], sys.argv[3]
msg = (
    "STANDING ORDER (RULES.md STANDING-ORDER-COMPACT, -A1, -A2): the context was just condensed. Do these now, in order:\n"
    "1. Read RESUME_NOW.md (the live handover), then the master prompt " + latest + ", then `grep -n '^## ' RULES.md | tail -15` "
    "and the newest entries (the OWNER-STANDING-ORDER-* entries always apply). RULES.md always wins over any prompt.\n"
    "2. Read logs/owner/INBOX.md and close every open item (OWNER-STANDING-ORDER-3/-4: nothing waits on the owner; overcome blockers without being asked).\n"
    "3. Check live jobs and siblings (list_sessions saved to a file, then <scratchpad>/sibstat.py). Resume stopped siblings from their RESUME.md.\n"
    "4. Re-arm the sibling-push Monitor and a send_later check-in (60 min).\n"
    "5. Continue the in-flight steps (verify, install and score harness batches with tools/p4/rh_verify.py and score_p4.py; declarations before data).\n"
    "The multi-agent prompt-regeneration workflow is RETIRED (STANDING-ORDER-COMPACT-A2): do not launch it. Refresh the master prompt yourself, in a single pass, at most once per 24 h, "
    "keeping every integrity rule (I1-I17, sections 3.3, 3.4, 3.6, 10, the messaging format) verbatim.\n"
    "Never include personal information about the owner anywhere."
)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}}))
EOF
