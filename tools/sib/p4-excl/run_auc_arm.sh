#!/bin/bash
# run_auc_arm.sh <arm lower-case: s2|s3|null>  -- col. -1 AUC for one P4-OWN arm from own-lead's branch, commit + push
set -e
cd /home/user/dominion
a=$1; A=$(echo $a | tr a-z A-Z); B=origin/claude/gifted-bell-gavnl5-sib-own-lead; P=/tmp/claude-0/p4excl
git fetch -q origin claude/gifted-bell-gavnl5-sib-own-lead; C=$(git rev-parse $B)
mkdir -p $P/$a
for rc in r0_c11 r0_c12 r0_c13 r1_c11 r1_c12 r1_c13; do git show $B:logs/sib/own-$a/maps/arrays/20260701183124-w010-027_$rc.npz > $P/$a/$rc.npz; done
python3 tools/sib/p4-excl/colm1_auc.py $A $P/$a "origin/claude/gifted-bell-gavnl5-sib-own-lead $C logs/sib/own-$a/maps/arrays/" $P/strip_a $P/grid_a.json $P/struct $P/labels logs/sib/p4-excl/p4own/colm1_auc_$A.json
python3 - $A <<'PY'
import json,time,sys
A=sys.argv[1]; p=f'logs/sib/p4-excl/p4own/colm1_auc_{A}.json'; d=json.load(open(p))
open('logs/sib/p4-excl/runs.jsonl','a').write(json.dumps({'step':f'colm1_auc_{A}','utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'tool':'tools/sib/p4-excl/colm1_auc.py','out':p,'result':f"pooled AUC {d['pooled']['auc']:.4f} over {d['pooled']['n_covered']} covered x4 px",'wall_s':d['seconds']})+'\n')
PY
git add logs/sib/p4-excl tools/sib/p4-excl/run_auc_arm.sh
git commit -q -m "p4-excl: DECL-P4-23 item 6(c) col. -1 AUC for $A

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01RniFbp6Sjnue4zDUUcENiC"
git push -q origin claude/gifted-bell-gavnl5-sib-p4-excl
echo $a >> $P/auc_done.txt
python3 -c "import json;d=json.load(open('logs/sib/p4-excl/p4own/colm1_auc_$A.json'));print('$A', d['pooled'], [round(v['auc'],4) for v in d['tiles'].values() if v.get('auc')])"
