Provenance: Project HERCULES | owner the owner | [id removed]

# P4-OWN label-shard interface requested from p4-excl (DECL-P4-23 item 2, DECL-P4-21-A1)

own-lead's build_patches.py reads (numbers only, never displayed):
1. Certification: p4-excl t_cert.py output as is: T_cert.json + T_mask_<strip>.npz (keys "<strip>_r<R>_c<C>", bool
   ceil(T/4) x ceil(T/4), pixel (y,x) covers tile px [4y,4y+4) x [4x,4x+4)). Already supported.
2. Labels, REQUESTED on the SAME x4 per-tile grid as the T mask, T tiles only (never X):
   - file labels/<strip>_r<R>_c<C>.npz with arrays
       ink uint8 (ceil(T/4), ceil(T/4)): number of the 4x4 sub-samples with inklabel == 255 (0..16), or 0/1 if one sample;
       sup uint8 same shape: number of sub-samples with supervision == 255 (0..16), or 0/1;
       n_sub = 16 or 1 (scalar);
   - sampling: per strip px (or per x4 pixel centre if 1 sample), the strip mesh UV interpolated BILINEARLY inside the
     strip quad (not nearest vertex), -> exact closest point on the labelled segment (<= 20 vox) -> label px round(uv*20).
     One sample per 20 x 20 px vertex cell is too coarse for a stride-4 (9.6 um) loss on 10-20 um ink deposits.
   - nearest covering segment decides (as label_frac.py any_segment).
   - labels.json: {strip, T_px, grid:'x4 of tile', files:[{file, strip, r, c, sha256, n_sup_px, n_ink_px}]}.
3. If only the per-vertex (20 px) sampling can be delivered tonight, deliver it on a x20 grid with the same keys
   (n_sub = 1, grid 'x20'); own-lead will record the coarser label resolution in RECIPE.md before any training.
