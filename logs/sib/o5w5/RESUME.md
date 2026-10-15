Provenance: Project HERCULES | owner the owner | [id removed]

# o5w5 RESUME
Detached: worker pid /work/p4o/worker.pid (log /work/p4o/worker.log), in-tile checkpoints /work/p4o/it5/ckpt/<tile>/ every 15 min; push loop /work/p4o/pushloop.sh (30-min progress commits; on completion runs /work/p4o/finalize.py and pushes).
Resume (same container): cd /home/user/dominion && OMP_NUM_THREADS=4 P4O_WORK=/work/p4o setsid nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/o5w5/p4o/PHerc.1667-iteration-5 --tiles "1,15" >> /work/p4o/worker.log 2>&1 < /dev/null & echo $! > /work/p4o/worker.pid; then setsid nohup /work/p4o/pushloop.sh &
New container: redo WORKER.md section 1-3 (git checkout 98cd075 -- tools/sib/ckpt-screen-b/ logs/sib/ckpt-screen-b/SPECS.json logs/sib/ckpt-screen-b/p4o/provenance.json; venv /opt/ckb; fetch.py cards 5; fetch.py model.safetensors 5), recreate /work/p4o/{pushloop.sh,finalize.py} from this session's description; the tile restarts from window 0.
