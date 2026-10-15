#!/bin/bash
# restart-safe driver for a P4-D strip: run_d.sh <a|b> <commit> <blob> <repo_path>
cd /home/user/dominion
P4EXCL_CKPT=/tmp/claude-0/p4excl/ckpt python3 tools/sib/p4-excl/process_d.py $1 /tmp/claude-0/p4excl/tpd_$1.npz $2 $3 $4 /tmp/claude-0/p4excl/grid_d_$1.json /tmp/claude-0/p4excl/struct /tmp/claude-0/p4excl/stripd_$1 logs/sib/p4-excl/excl_d_$1.json >> /tmp/claude-0/p4excl/run_d_$1.log 2>&1
echo "exit $?" >> /tmp/claude-0/p4excl/run_d_$1.log
