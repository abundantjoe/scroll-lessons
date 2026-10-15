#!/bin/sh
# Sequential wrapper: never two Scroll-1 raw fetches at once (disk). Stage logs are appended, markers preserved.
cd /home/user/megara
scripts/run_s1.sh >> /tmp/s1.log 2>&1 || { echo "STAGE1_FAILED"; exit 1; }
echo STAGE1_OK
scripts/run_s1_v2.sh >> /tmp/s1v2.log 2>&1 || { echo "STAGE2_FAILED"; exit 1; }
echo STAGE2_OK
scripts/run_s1_v3.sh >> /tmp/s1v3.log 2>&1 || { echo "STAGE3_FAILED"; exit 1; }
echo STAGE3_OK
