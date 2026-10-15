set -e
IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
VILLA_SHA=41701aa0eaa1aa765523db3f9f972b5830abf549
docker image inspect $IMG >/dev/null 2>&1 || docker pull $IMG
if [ ! -d /work/villa/.git ]; then
  git clone --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa /work/villa
  git -C /work/villa sparse-checkout set .github volume-cartographer vesuvius ink-detection
fi
git -C /work/villa fetch --depth 1 origin $VILLA_SHA || true
git -C /work/villa checkout -q $VILLA_SHA
git -C /work/villa rev-parse HEAD
cp /home/user/dominion/docker/env/vc_wrapper.sh /work/bin/vc; chmod +x /work/bin/vc
[ -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] || bash /work/scripts/vc_build_p139.sh
echo ENV_OK
