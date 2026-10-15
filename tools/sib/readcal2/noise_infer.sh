#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# C2-NT command (official infer, both orders, no TTA, CPU) on the two cropped w053 blank SV arrays.
set -euo pipefail
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
export OMP_NUM_THREADS=3 MKL_NUM_THREADS=3
for w in blank_w053_y256_x1536 blank_w053_y256_x7168; do
  mkdir -p /work/rc2/noise/infer/$w
  [ -f /work/rc2/noise/infer/$w/$w.tif ] && [ -f /work/rc2/noise/infer/$w/${w}_reverse.tif ] && continue
  /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer /work/rc2/noise/$w.zarr $CK \
    /work/rc2/noise/infer/$w/$w.tif --direction both --batch-size 4 --num-workers 1 --no-compile
done
sha256sum /work/rc2/noise/infer/*/*.tif
