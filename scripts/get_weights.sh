#!/usr/bin/env bash
# get_weights.sh DIR: download the three public 9 um ink models used here, verify sha256, rebuild dense_native's
# villa checkpoint (bit-identical to the one used for every result; scripts/rebuild_dense_native.py). Needs curl and
# PYI = a python with torch + safetensors.
set -euo pipefail
D=${1:?usage: get_weights.sh DIR}; PYI=${PYI:-python3}; mkdir -p "$D"; HERE=$(cd "$(dirname "$0")" && pwd)
get() { local url=$1 f=$2 sha=$3
  if [ -f "$D/$f" ] && [ "$(sha256sum "$D/$f" | cut -d' ' -f1)" = "$sha" ]; then echo "OK (cached) $f"; return; fi
  curl -fL -sS --retry 5 -o "$D/$f.part" "$url"
  [ "$(sha256sum "$D/$f.part" | cut -d' ' -f1)" = "$sha" ] || { echo "SHA256 MISMATCH $f"; exit 1; }
  mv "$D/$f.part" "$D/$f"; echo "OK $f"; }
get https://huggingface.co/scrollprize/ink_9um/resolve/main/hybrid_3d2d-seed42/step-075000.pth hybrid_3d2d-seed42_step-075000.pth e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
get https://huggingface.co/scrollprize/ink_9um/resolve/main/hybrid_3d2d-seed43/step-075000.pth hybrid_3d2d-seed43_step-075000.pth 2aeaa85a35ef28d7bc7bf3e848c4a6a91385e9132710927fdba41133c4ecb28f
get https://huggingface.co/Nieuwlaar/ink9um-dense-native/resolve/main/weights/dense_native_016000.safetensors dense_native_016000.safetensors d3d95dc41dcb24ed76b84b5e12ca5dae25d7fb34edf1dfbb93e0186f91e6fc6d
get https://huggingface.co/Nieuwlaar/ink9um-dense-native/resolve/main/training/configs/train_dense_native.json train_dense_native.json 5d8459030b36cd3980a03610c684365a7407d497173eff433efdb37f75840c86
[ -f "$D/dense_native-016000.rebuilt.pth" ] || "$PYI" -I "$HERE/rebuild_dense_native.py" "$D/dense_native_016000.safetensors" "$D/train_dense_native.json" "$D/dense_native-016000.rebuilt.pth"
echo "weights ready in $D"
