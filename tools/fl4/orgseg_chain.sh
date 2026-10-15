#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-6: slot P of 6 runs sv0800 items P, P+6,... (6 items) then tx1203 items P, P+6, P+12, P+18 (20 items).
# usage: setsid nohup bash tools/fl4/orgseg_chain.sh <P> > /work/ochain.out 2>&1 < /dev/null &
P=$1; REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
while pgrep -f "tools/fl4/ring2_run.sh" >/dev/null; do sleep 60; done
for j in $(seq $P 6 5); do bash tools/fl4/orgseg_run.sh sv0800 $j; done
for j in $(seq $P 6 19); do bash tools/fl4/orgseg_run.sh tx1203 $j; done
touch logs/fl4t/OCHAIN_DONE_p$P; flock /work/own/git.lock -c "git add logs/fl4t/OCHAIN_DONE_p$P; git commit -q -m 'orgseg chain p$P done

Provenance: Project HERCULES | [id removed]
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>'; git push -q origin HEAD:$(git rev-parse --abbrev-ref HEAD) || (git pull -q --rebase origin $(git rev-parse --abbrev-ref HEAD) && git push -q origin HEAD:$(git rev-parse --abbrev-ref HEAD))"
