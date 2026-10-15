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
    "STANDING ORDER (RULES.md STANDING-ORDER-COMPACT): the context was just condensed. Do these now, in order:\n"
    f"1. Read the current master prompt {latest} in full, then the last 5 RULES.md entries. RULES.md always wins over any prompt.\n"
    "2. Check the live jobs (pgrep -af 'd3_train|d3_infer|infer_arms|ink_queue|run_arms'). Restart anything stopped using the prompt's recovery commands.\n"
    "3. Launch the prompt-regeneration workflow in the background: the Workflow tool with scriptPath tools/prompt/regen_prompt_workflow.js and "
    f"args {{\"source\": \"{latest}\", \"out\": \"configs/prompt/hercules_master_v{nxt}.md\", \"version\": \"v{nxt}\", \"stamp\": \"{now}\", "
    f"\"work\": \"<scratchpad>/prompt_wf_v{nxt}\"}} (use absolute paths).\n"
    "4. Meanwhile, continue the in-flight safety-critical steps (sealed reads, audits, restarts) under the current prompt.\n"
    "5. Adopt the regenerated prompt only after all of its verification checks pass and it is committed and pushed. "
    "It may never weaken, drop or reword away any integrity rule (I1-I17, sections 3.3, 3.4, 3.6, 10, the messaging format).\n"
    "Never include personal information about the owner anywhere."
)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}}))
EOF
