#!/bin/sh
# One sequential chain for everything that touches the disk: registrations -> v3 -> v5 -> segment-2 transfer -> extra-segment prep + v6.
cd /home/user/megara
for s in 20230929220926 20231012184424; do
  test -f data/s1/$s/label_registration.json || .venv/bin/python scripts/s1_register_label.py data/s1/labels/${s}_inklabels_L.png data/s1/$s/overview/ink_ds8.jpg data/s1/$s/label_registration.json data/s1/$s/overview/label_overlay.png 0.965 0.99 > /tmp/s1reg_$s.log 2>&1
done
echo REG_OK
scripts/run_s1_v3.sh >> /tmp/s1v3.log 2>&1 && echo STAGE3_OK >> /tmp/s1rj.log || { echo STAGE3_FAILED | tee -a /tmp/s1rj.log; }
scripts/run_s1_v5.sh >> /tmp/s1v5.log 2>&1 || echo V5_FAILED
scripts/run_s1_seg2_chain.sh >> /tmp/s1seg2.log 2>&1 || echo SEG2_FAILED
scripts/run_s1_v6.sh >> /tmp/s1v6.log 2>&1 || echo V6_FAILED
echo MASTER_DONE
