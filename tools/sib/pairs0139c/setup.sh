#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# pairs0139c environment, mirroring pairs0139: docker/env/setup_env.sh steps 1-3 (dockerd under /work, deps image,
# villa 41701aa sparse, official CLI build via tools/sib/pairs0139/vc_build.sh = proxy-from-env copy of
# docker/env/vc_build.sh, /work/bin/vc wrapper) and the pairs python env /work/p139/py (the /opt/hv package list).
# Ink inference (/opt/hv-ink, checkpoint) is not needed for pair building and is not installed.
set -euo pipefail
REPO=/home/user/dominion
P="${HTTPS_PROXY}"
VILLA_SHA=41701aa0eaa1aa765523db3f9f972b5830abf549
DEPS_IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
mkdir -p /work/logs /work/bin /work/scripts /work/p139
if ! docker info >/dev/null 2>&1; then
  HTTPS_PROXY=$P HTTP_PROXY=$P nohup dockerd --data-root /work/docker > /work/logs/dockerd.log 2>&1 &
  for _ in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 2; done
fi
docker info >/dev/null
docker image inspect "$DEPS_IMG" >/dev/null 2>&1 || docker pull "$DEPS_IMG"
docker image inspect "$DEPS_IMG" --format '{{.Id}}'
if [ ! -d /work/villa/.git ]; then
  git clone --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa /work/villa
  git -C /work/villa sparse-checkout set .github volume-cartographer vesuvius ink-detection
fi
git -C /work/villa fetch --depth 1 origin "$VILLA_SHA" || true
git -C /work/villa checkout -q "$VILLA_SHA"
echo "villa HEAD $(git -C /work/villa rev-parse HEAD)"
cp "$REPO/docker/env/vc_wrapper.sh" /work/bin/vc; chmod +x /work/bin/vc
git -C "$REPO" show origin/claude/gifted-bell-gavnl5-sib-pairs0139:tools/sib/pairs0139/vc_build.sh > /work/scripts/vc_build_p139.sh
[ -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] || bash /work/scripts/vc_build_p139.sh
[ -x /work/p139/py/bin/python ] || { uv venv /work/p139/py --python 3.11 -q && \
  VIRTUAL_ENV=/work/p139/py uv pip install -q numpy scipy opencv-python-headless tifffile "zarr<3" numcodecs pytest jsonschema pillow pyyaml requests boto3 s3fs fsspec; }
/work/p139/py/bin/python -c "import numpy, scipy, zarr, tifffile, boto3; print('py ok', numpy.__version__, scipy.__version__, zarr.__version__)"
/work/p139/py/bin/python -m pip freeze 2>/dev/null || VIRTUAL_ENV=/work/p139/py uv pip freeze
echo "setup: OK"
