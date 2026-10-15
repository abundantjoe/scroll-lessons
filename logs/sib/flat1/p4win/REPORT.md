Provenance: Project HERCULES | owner the owner | [id removed]

# P4 window A flattening (w010-027, canvas columns c8-c17, all rows)

STATUS: DONE. Geometry only: mesh coordinates and volume metadata. No prediction, render or CT pixel was read, and no image was produced. Script: `tools/sib/flat1/p4win.py` (rules in its docstring). Numbers: `metrics.json`.

## Region
- **Mesh:** organizer `20260701183124-on-20260411134726-2.4um.tifxyz`. The voxel size is 2.4 um, from the volume metadata.json. Mesh sha256 values are in metrics.json.
- **Window:** a fine quad belongs to the window if floor(20 (j + 0.5) / 8343) is in [8, 17]. This covers vertex columns 3337 to 7509 and all 3488 rows (canvas columns 66,744 to 150,174 px; c0 is the outer end). 14,013,213 valid quads, of which the largest component has 14,013,204; the area is about 318 cm^2.
- **Solve:** flattened on a coarse grid (every 6th vertex: 582 x 696, 388,304 coarse quads of 0.29 mm). The UVs were then interpolated bilinearly to full resolution, and **every full-resolution quad was measured**. 54,954 fine triangles (0.2 %) near holes have no UV and count as failing.

## Results at full resolution (14.0 M quads)

| flattening | quads within +-5 % | within 1 % | triangle area within +-5 % | angle error median / p95 / p99 (deg) | flipped triangles | notes |
|---|---|---|---|---|---|---|
| official (organizer grid) | 85.14 (raw 84.53) | 13.62 | 80.53 | 0.69 / 3.74 / 7.94 | 0 | reference |
| **vc_flatten (ABF++)** | **78.07** | 20.22 | 57.49 | 0.12 / 1.24 / 3.80 | 5 | conformal; area drifts; ABF rescale 0.992; ABF time 926 s |
| **SLIM** | **86.49** | 17.64 | 82.82 | 0.70 / 3.32 / 6.16 | 0 | best; SLIM time 1755 s |
| ARAP | 85.98 | 17.14 | 82.51 | 0.72 / 3.35 / 6.07 | 24 | 1 flip already at the coarse level (collapse flag set) |

The flattened tifxyz products are scored against their own nominal 20-vox step. vc_flatten: 77.85 % of 13.76 M quads within +-5 %. SLIM: 87.28 % of 13.77 M quads. Both read back identically through our loader, which follows the official C++ loader's rules.

**No method reaches the 93.1 % bar on a region of about 318 cm^2.** This matches FLAT-1: distortion grows with patch size and with crushing, as in the hard set and the whole-mesh tests. It is intrinsic curvature, not a solver failure (SLIM: 0 flips). On 4 cm^2 crops of the same segment, SLIM reached 97.72 % and vc_flatten 94.15 % (FLAT-2). **For the prize package, the region around the title should be flattened locally (tile +- 1 cm, `p4_package.py`) rather than as the whole window.**

## Delivered files (for each of vc_flatten, the FLAT-1 adopted method, and SLIM, the best)
The repository pre-commit hook refuses files > 20 MB. The full-resolution files (20-vox flattened tifxyz, full UV, source maps; each 27-45 MB) are kept in /work/flat1/p4win_full; their sha256 values are in metrics.json `deliverables`. Pushing them to the data branch needs the owner's permission (DECL-OFFLOAD-1 item 4). **ASK: permit the offload.** The compact git delivery below is exact:
- `<method>/flattened_s40.tifxyz/{x,y,z}.tif, meta.json` is the flattened tifxyz. xyz (2.4 um voxels of 20260411134726) lies on a regular grid in the flat (u, v) plane with step 40 vox (scale 0.025). It is exactly the 20-vox product subsampled [::2, ::2]; at step 20 the xyz is linear inside fine triangles. The files are float32, zlib, tiled, and -1 means empty. Orientation: rotated (proper rotation only) onto the canvas orientation; no reflection was needed (vc_flatten -178.74 deg, SLIM -0.007 deg).
- `<method>/coarse_uv.npy` holds the aligned flat (u, v) of the region vertices (6a, 6b), shape 582 x 696 x 2. The full-resolution UV of any region vertex is exactly the bilinear interpolation of this array inside the kept coarse quads (`p4win.upsample`; the alignment is linear).

### Mapping (also in metrics.json "mapping")
1. canvas px (y, x) of the w010-027 prediction canvas -> region grid (row, col) = (y / 20, x / 20 - 3337);
2. -> (u, v) = bilinear interpolation of coarse_uv at (row / 6, col / 6);
3. -> flattened_s40 node (i, j) = ((v - V0) / 40, (u - U0) / 40), with (U0, V0) = meta.json `hercules_uv_origin_vox`: vc_flatten (260, 640), SLIM (60, 720).

## Failures / notes
- The container was reclaimed at about 21:26Z during the SLIM solve. The run resumed from the saved vc_flatten result (resume logic added), and no numbers were recomputed differently.
- The first commit attempt was refused by the pre-commit hook (files > 20 MB). This was recorded and not worked around; the exact compact delivery above is used instead.

Integrity: no issues.
