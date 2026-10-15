Provenance: Project HERCULES | owner the owner | [id removed]

Package: DRY RUN PHerc0139 PHerc0139_w035_r020-128_c012-120
Dry run: yes (DRY RUN: not a submission)
Volume: s3://vesuvius-challenge-open-data/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/ (volume id 20250728140407, voxel 9.362 um from its metadata.json)
Mesh: mesh/PHerc0139_w035_r020-128_c012-120 (tifxyz)
Image: PHerc0139_w035_r020-128_c012-120.png (106.8148 px/mm; 1 cm bar = 1068 px)

Display: linear 1-99 % window of the renderer's surface slice; cv2.INTER_AREA only if scale < 1; no
other operation. The image was generated programmatically and verified mechanically.

Reproduce (needs the official vc_render_tifxyz, villa 41701aa, via /work/bin/vc):
  bash reproduce.sh 's3://vesuvius-challenge-open-data/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/' mesh/PHerc0139_w035_r020-128_c012-120
It re-renders in a fresh temporary directory and compares sha256 of the raw render, the CT panel and the
whole PNG with package.json.

SHA256SUMS lists every other file of this package.
