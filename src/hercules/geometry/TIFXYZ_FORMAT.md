Provenance: Project HERCULES | owner the owner | [id removed]

# tifxyz on-disk format (from the official ScrollPrize/villa source)

The only sources used are official ScrollPrize files in `ScrollPrize/villa`,
branch `main` at commit `41701aa0eaa1aa765523db3f9f972b5830abf549`, fetched
2026-09-24 from `raw.githubusercontent.com`. No community code was used.
Line numbers refer to that commit. Abbreviations:

* `QS` = `volume-cartographer/core/src/QuadSurface.cpp` (the C++ reference writer/loader)
* `TIFF` = `volume-cartographer/core/src/Tiff.cpp`, `TIFFH` = `volume-cartographer/core/include/vc/core/util/Tiff.hpp`
* `GP` = `volume-cartographer/core/src/GrowPatch.cpp` (the tracer)
* `GEO` = `volume-cartographer/core/src/Geometry.cpp`
* `O2T` = `volume-cartographer/apps/src/vc_obj2tifxyz_legacy.cpp`
* `PYW`, `PYR`, `PYT` = `vesuvius/src/vesuvius/tifxyz/{writer,reader,types}.py` (official Python package)

## Files

A tifxyz surface is a directory holding

| file | content | source |
|---|---|---|
| `x.tif`, `y.tif`, `z.tif` | one coordinate component each | QS 1856-1865 (`writeDataToDirectory`) |
| `meta.json` | metadata (below) | QS 2077-2145 (`save`) |
| `mask.tif` (optional) | validity mask | QS 2493-2640 (loader), PYW 200-236 |
| `<name>.tif` (optional) | extra channels, e.g. `generations.tif` (uint16 tracer generation per vertex) | QS 1835-1853, 1867-1872; GP 3777 |

The loader requires x/y/z.tif and meta.json (QS 2477-2484; PYR 383).

## Coordinate TIFFs

* The surface is a `cv::Mat_<cv::Vec3f>` (float32 xyz per grid vertex); `cv::split`
  gives three CV_32FC1 planes written to x/y/z.tif (QS 1860-1865).
* `writeTiff(path, plane, cvType=-1, tileW=0, tileH=0, padValue=-1, COMPRESSION_NONE, dpi_)`:
  `cvType=-1` keeps the float32 type (TIFF 122), CV_32FC1 means 32-bit IEEE float samples
  (TIFF 55); one sample per pixel, minisblack (TIFF 139-143); tile size 0 means a
  **single strip** (`ROWSPERSTRIP = H`), uncompressed (TIFF 154, QS 1862 comment
  "untiled, uncompressed"). The resolution tag is written only if dpi > 0 (TIFF 147-151), where
  `dpi = 25400 / voxel_size_um` (TIFFH 12-15; GP 3712 `setDpi(voxelSizeToDpi(voxelsize))`).
* **Axis order.** Image shape is (rows, cols) = (H, W). Pixel (row j, col i) holds grid
  vertex `points(j, i)`; `x.tif` holds component 0 (volume x), `y.tif` component 1, `z.tif`
  component 2 (QS 1860-1865, 2482-2484). The official Python package reads these into
  (H, W) arrays and stacks them as (z, y, x) for volume indexing (PYT 725-766), i.e. the
  volume array is indexed `[z, y, x]` and z is the slice index. Grid columns = u
  (`loc[0]`), rows = v (`loc[1]`) (GEO 68).
* **Loader tolerance.** The C++ loader accepts 8/16/32/64-bit uint/int/float samples,
  tiled or stripped, but exactly one sample per pixel (QS 2337-2400).
* The official *Python* writer instead writes LZW-compressed 1024-tiled float32 plus a
  mask.tif (PYW 21-29, 139-153, 217-236). Both layouts load in both readers. We write the
  C++ layout.

## Invalid points

* Sentinel **(-1, -1, -1)**. The C++ validity test is "no component == -1 and all finite"
  (QS 275-279); many code paths test only `x == -1` (e.g. QS 1083, 1605; GEO 44-46).
* The **loader also invalidates every vertex with z <= 0**, setting it to (-1, -1, -1)
  (QS 2486-2490; the Python reader does the same when there is no mask, PYR 677-684).
* `mask.tif` (optional): channel 0 is validity; the C++ loader keeps a vertex only if the
  value is >= 255 (QS 2525-2533) and accepts a mask that is an integer multiple of the grid
  size, where any sub-pixel below threshold invalidates its vertex (QS 2513-2566). The Python
  reader treats mask > 0 as valid (PYR 541-549). These two rules differ for 1..254.
* Empty-surface bbox is the -1 marker (QS 2290-2303; PYR 41-43, 125).

## meta.json

Written by `QuadSurface::save` with `meta.dump(4)` (4-space indent) through a temp
file and rename (QS 2140-2145). Required keys (QS 2117-2137, same in `save_meta`
QS 2260-2272):

| key | value |
|---|---|
| `bbox` | `[[xmin, ymin, zmin], [xmax, ymax, zmax]]` over valid vertices, recomputed on save (QS 2117-2129, 2290-2303) |
| `type` | `"seg"` |
| `uuid` | segment id string (usually the directory name, QS 1774-1780) |
| `format` | `"tifxyz"` |
| `scale` | `[scale_x, scale_y]` = `[_scale[0], _scale[1]]` (QS 2134-2137) |

Other keys already in the surface's `meta` are preserved, e.g. the tracer's
`max_gen`, `seed`, `elapsed_time_s`, `seed_surface_id`, `grid_offset` (GP 3726-3852);
the Python writer may add `area` (PYW 188-190). The eager loader reads `scale[0]`,
`scale[1]` (QS 2477-2478); the lazy loader requires a >= 2-element array of finite
positive numbers (QS 304-338). Both read `uuid` (QS 2646).
Key order is not significant.

## What `scale` means

`scale` is **grid vertices per voxel**, so the nominal grid step is `1/scale` voxels:

* tracer: `float T = step; ... new QuadSurface(points, {1/T, 1/T})` (GP 3570, 3711, 3775);
* `vc_obj2tifxyz_legacy`: "Scale = 1/step_size (matching GrowPatch.cpp pattern)" and help
  text "step_size: UV units per grid cell (default: 20) ... Scale will be 1/step_size
  (default: 0.05)" (O2T 223-224 and usage text);
* nominal size in voxels = `cols / scale[0]`, `rows / scale[1]` (QS 940-944); nominal
  coordinates = internal grid coordinates / scale (QS 760-769);
* the Python package: area = valid quads / (scale_y * scale_x) (PYT 897-898), and the tracer's
  area uses `vx_per_quad = step * step` (GP 4960).

So scale 0.05 means 20 voxels per grid cell. `scale[0]` applies to columns (u) and
`scale[1]` to rows (v). The Python package swaps them internally to (scale_y, scale_x)
(PYR 412-417; PYW 172-174). `scale` is nominal: real edge lengths vary.

## Normals

C++ `grid_normal` = normalize(xv x yv), where xv is the column (u) difference and yv the row (v)
difference (GEO 48-54). `hercules.geometry.tifxyz.vertex_normals` uses the same order.
The official Python package uses ty x tx (row x column), the **opposite sign**
(PYT 383-395). Normal orientation relative to the scroll is not stored anywhere.

## Things this document does not establish

* Which face of the sheet (recto/verso) the normal or (u, v) handedness corresponds to:
  nothing in the format fixes it. See `level_mesh.py` (chirality / convention_sign).
* The voxel size. It is only implicit in the optional TIFF dpi tag and is scan-specific.
