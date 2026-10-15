# Provenance: Project HERCULES | owner the owner | [id removed]
# C3 inference runs (sequential, CPU, 3 threads). Each run is logged to logs/gpu_ledger.tsv by ledger_run.sh.
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
R=/work/c3/render/w040_crop_x1152_y2048_2048.zarr
SV=/work/c3/data/s3/PHerc0139/segments/20250831000000-w040_2025083102/surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr
export OMP_NUM_THREADS=3
run() { name=$1; shift; mkdir -p /work/c3/infer/$name
  bash /work/c3/scripts/ledger_run.sh /work/c3/infer/$name /work/c3/logs/infer_$name.log \
    /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer "$@"; }
run render_c2_tta   $R  $CKPT /work/c3/infer/render_c2_tta/w040_render.tif  --direction both --tta-mirror --batch-size 4 --num-workers 1 --no-compile
run render_c2_notta $R  $CKPT /work/c3/infer/render_c2_notta/w040_render.tif --direction both --batch-size 4 --num-workers 1 --no-compile
run teamsv_notta    $SV $CKPT /work/c3/infer/teamsv_notta/w040_teamsv.tif    --direction both --batch-size 4 --num-workers 1 --no-compile
echo ALLDONE
