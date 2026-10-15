#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Completes step 4-5 of setup_env.sh when `uv pip install -e vesuvius` refuses the python pin (>=3.14) on 3.13:
# the villa package is made importable by a .pth path entry (same effect as an editable install, no metadata),
# the frozen dependency list is installed, and the base checkpoint is fetched and sha256-verified.
set -euo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
SP=$(/opt/hv-ink/bin/python -c 'import site;print(site.getsitepackages()[0])')
echo /work/villa/vesuvius/src > "$SP/hrc_villa_vesuvius.pth"
grep -v -E "^-e |^vesuvius|^torch|^torchvision" "$REPO/docker/env/hv-ink-freeze.txt" > /work/devloop/hv-ink-freeze-nov.txt
VIRTUAL_ENV=/opt/hv-ink uv pip install -q -r /work/devloop/hv-ink-freeze-nov.txt --no-deps
/opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer as m; print('infer module', m.__file__)"
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
if [ ! -f "$CK" ] || ! echo "$CKPT_SHA  $CK" | sha256sum -c --quiet; then
  for i in 1 2 3 4; do
    curl -fsSL -o "$CK" "https://huggingface.co/scrollprize/ink_9um/resolve/7109667e2607db1b90c37c8b09cb876ea7fe7bb1/hybrid_3d2d-seed42/step-075000.pth" && break
    sleep $((2**i))
  done
fi
echo "$CKPT_SHA  $CK" | sha256sum -c
echo finish_hv_ink: OK
