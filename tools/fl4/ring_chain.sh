#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-5-A1: run rings 2, 3, 4 for one seed index in sequence (each ring2_run.sh call is idempotent; waits for any running
# runner first). usage: setsid nohup bash tools/fl4/ring_chain.sh <IDX> > /work/chain.out 2>&1 < /dev/null &
I=$1; REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
while pgrep -f "tools/fl4/ring2_run.sh" >/dev/null; do sleep 60; done
for spec in "ring2 logs/fl4/seeds_b070_PHerc0268.json" "ring3 logs/fl4/seeds_b055_PHerc0268.json" "ring4 logs/fl4/seeds_b085_PHerc0268.json"; do
  set -- $spec; RING=$1 SEEDS=$2 bash tools/fl4/ring2_run.sh $I 60
done
touch logs/fl4t/CHAIN_DONE_i$I; flock /work/own/git.lock -c "git add logs/fl4t/CHAIN_DONE_i$I; git commit -q -m 'chain i$I done

Provenance: Project HERCULES | [id removed]
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>' ; git push -q origin HEAD:$(git rev-parse --abbrev-ref HEAD) || (git pull -q --rebase origin $(git rev-parse --abbrev-ref HEAD) && git push -q origin HEAD:$(git rev-parse --abbrev-ref HEAD))"
