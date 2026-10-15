#!/bin/bash
# restart-safe driver for the strip a run (per-segment checkpoints in scratch)
cd /home/user/dominion
P4EXCL_CKPT=/tmp/claude-0/p4excl/ckpt python3 tools/sib/p4-excl/process.py a /tmp/claude-0/p4excl/tp_a.npz e25635c968e9727d2ba10eea4b2d21bdc724fa7b d4639aaa7e9bf18578cfbfb254cb3a66691a2bdb /tmp/claude-0/p4excl/struct /tmp/claude-0/p4excl/excl_a_full.json /tmp/claude-0/p4excl/strip_a /tmp/claude-0/p4excl/grid_a.json >> /tmp/claude-0/p4excl/run_a.log 2>&1
echo "exit $?" >> /tmp/claude-0/p4excl/run_a.log
