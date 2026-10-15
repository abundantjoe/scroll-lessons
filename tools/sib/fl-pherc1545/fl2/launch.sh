#!/bin/bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-2 launcher (env only, no pipeline logic): wait for docker/env/setup_env.sh, apply the brief's item-3 env fixes
# (imagecodecs into /opt/hv; vesuvius editable on Python 3.13 with --ignore-requires-python if not importable), then
# start the watchdog, which runs pipeline.sh (it re-runs setup_env.sh itself; that script is idempotent).
cd /home/user/dominion
while pgrep -f "^bash docker/env/setup_env.sh" >/dev/null; do sleep 20; done
bash docker/env/setup_env.sh >> /work/fl2/setup_env.log 2>&1
[ -x /opt/hv/bin/python ] && uv pip install -q --python /opt/hv/bin/python imagecodecs >> /work/fl2/setup_env.log 2>&1
if ! /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" 2>/dev/null; then
  /opt/hv-ink/bin/python -m ensurepip >/dev/null 2>&1
  /opt/hv-ink/bin/python -m pip install -q --ignore-requires-python --no-deps -e /work/villa/vesuvius >> /work/fl2/setup_env.log 2>&1
  grep -v "^-e\|vesuvius\|^torch==\|^torchvision==" docker/env/hv-ink-freeze.txt > /work/fl2/freeze_noself.txt
  uv pip install -q --python /opt/hv-ink/bin/python --no-deps -r /work/fl2/freeze_noself.txt >> /work/fl2/setup_env.log 2>&1
fi
exec bash tools/sib/fl-pherc1545/fl2/watchdog.sh
