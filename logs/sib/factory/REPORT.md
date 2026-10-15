Provenance: Project HERCULES | owner the owner | [id removed]

# factory: submission-package factory and verifier (dry run)

STATUS: DONE for the factory task as briefed (items a-f, dry run, tests). The Paris 4 package mode and the
licence check (orchestrator messages 00:36Z-06:01Z) are follow-ups and are listed under "Next".

Branch claude/gifted-bell-gavnl5-sib-factory. Machine-readable summary: logs/sib/factory/report.json.
No image was opened, viewed or described by this session; only hashes and numbers were read.

## What was built (tools/sib/factory/)
| File | Role |
|---|---|
| pngio.py | canonical PNG writer/strict parser (IHDR, one IDAT of STORED deflate blocks, IEND; filter 0; no compressor, so bytes depend only on pixels); tifxyz TIFF writer with exactly the 10 structural tags of the official meshes |
| build_image.py | image = 64 px header (DRY RUN stamp top-left in dry runs, else zero) + CT panel (linear 1-99 % window over render > 0; cv2.INTER_AREA only if scale < 1) + 96 px footer (solid 1 cm bar, round(10000/voxel_um x scale) px, and a "1 cm" label) |
| render_build.py | official vc_render_tifxyz (villa 41701aa, binary sha256 473369f9...9f2c, via /work/bin/vc in the official deps image), -n 1, scale 1, streaming the S3 zarr; metadata.json fetch; voxel from scan.tomo.acquisition.detector.samplePixelSize; refuses PHerc0841 |
| factory.py | package maker: `<mesh>.png`, mesh/<mesh>/ (x,y,z.tif, meta.json), render/<mesh>_raw.npy, inputs/volume_metadata.json, tools/, reproduce.sh, package.json, README.txt (provenance on line 1), SHA256SUMS |
| verify.py | 16 mechanical checks (below); trusts nothing in the package (its own copies of layout constants and tools, the repo eligibility catalogue) |
| reproduce_check.py + reproduce.sh | reproduce.sh VOLUME_URL MESH -> fresh metadata fetch and render in a new temp dir under /work/repro, rebuild, sha256 comparison of raw render, CT panel and PNG; exit 0 only if identical |
| pick_window.py | coded window rule on w035 (below) |
| fault_drill.py | plants faults into copies of a finished package |
| setup_renderer.sh, s3get.py, runlog.sh, run_dryrun.sh | renderer build, hashed downloads (downloads.jsonl), run logging (runs.jsonl), dry-run driver |

## Verifier checks (verify.py)
package_json_strict (exact key sets; any extra key = extra metadata), file_layout (exactly the allowed files,
no symlinks, no __pycache__), sha256_manifest, names_ascii_basename (image basename == mesh name == meta uuid,
plain ASCII), no_cf_characters (names, contents and decoded JSON strings, so \u escapes are caught),
png_no_metadata (chunk whitelist IHDR/IDAT/IEND, CRCs, no trailing bytes, canonical re-encoding),
mesh_no_metadata (TIFF tag whitelist, meta.json keys), voxel_from_metadata (sha256 of the packaged
metadata.json, URL voxel token, scanRadix names the scroll), volume_eligible (real mode: (scroll, id, URL) in
data/catalogue/eligible_products.json; dry run: reported NOT ELIGIBLE and allowed only as DRY RUN),
dry_run_marking (dry: DRY_RUN_ dir, "DRY RUN" name, pixel-exact stamp, under packages/dryrun/; real: no
DRY[ _-]*RUN in any name or text, header strip all zero), tools_pinned, linear_display (panel recomputed
pixel-exact from the raw render), scale_bar_measured (connected-component measurement of the one solid bar
outside the panel; |L - 10000/voxel x scale| <= 0.5 px; footer pixel-exact), letter_table (columns; mm = px /
px_per_mm to 3 dp; bbox inside panel; real mode >= 10 rows with joint bbox <= 400 mm^2), provenance_visible,
fields_wellformed.

## Dry run
- Window rule (logs/sib/factory/window_pick.json, run pick_window_v7; ASK.md defaults 1-2, accepted by the
  orchestrator 05:25Z): 108 x 108-vertex sub-grid of w035 on volume 20250728140407 (107 cells = 2140 px >= 2
  cm), all vertices valid; >= 150 vox (144 + 6 vox discretisation margin) from the SEAL-J-D1 w053 blanks, the
  D1 w044 canary and the whole title mesh; >= 40 vox from the whole w024/w047/w053/w044 meshes; minimum overlap
  with the unsealed PROBE window w035_y1792_x768. 1108 candidates, 63 pass.
- Chosen: grid rows 20-128, cols 12-120 (canvas y0 400, x0 240). Clearance 257.6 vox (2.412 mm) to the nearest
  sealed window (blank_w053_y256_x7168); canary 286.8; title mesh 3874.3; whole meshes w024 151.1, w047 131.4,
  w053 213.3, w044 83.2 vox. PROBE overlap 26.3 % of the window area (unavoidable: every w035 window overlaps it).
- Package packages/dryrun/DRY_RUN_PHerc0139_w035_r020-128_c012-120 (9.5 MB, 15 files), repo commit 88079a1:
  image 2320 x 2160 px (panel 2160 x 2160), sha256 f04bc9084bd403f5f212e80ed310ccf0ce12064dad443b45ac4f448322dd7de7;
  raw render pixels sha256 760f516e...c2f0, 96.3 % of pixels > 0; window [16, 178]; voxel 9.362 um from
  metadata.json (sha256 95917633...5bae); 106.8148 px/mm; bar 1068 px (exact 1068.148).
- Verifier: 16/16 pass (logs/sib/factory/verify_dryrun.json). volume_eligible reads "NOT ELIGIBLE ... allowed
  only because this is a DRY RUN": PHerc0139 is not an eligible volume, so this package can never pass as real.
- Reproduce: `bash reproduce.sh <volume URL> mesh/<name>` in /work/repro/hrc_repro_3CMq7v, 55 s: raw render,
  CT panel and PNG byte-identical (logs/sib/factory/reproduce_dryrun.json). The PNG sha256 was also identical in
  all three independent factory builds (23:25Z, 23:36Z, 23:46Z).
- Fault drill on copies of the real package (logs/sib/factory/fault_drill.json): clean copy passes; each fault
  rejected by its own check: hidden tEXt chunk (png_no_metadata), bar 6 px short (scale_bar_measured, measured
  1062), U+200B in README (no_cf_characters), wrong volume ID (volume_eligible), dry run relabelled real
  (dry_run_marking), gamma 0.8 on the panel (linear_display, 4,395,748 px differ).
- Unit tests: tests/sib_factory_verify_test.py, 49 pass (planted faults for every check, including tEXt/iTXt/
  zTXt/eXIf/pHYs/tIME chunks, trailing bytes, recompressed PNG, TIFF Software tag, extra JSON/meta keys, Cf in
  file text, JSON and file names, non-eligible and bogus volume IDs, DRY RUN text/stamp in real packages, mocked
  reproduce detecting a single grey-level change). Full repo suite: 638 passed.

## Commands
```
bash tools/sib/factory/setup_renderer.sh                  # official vc_render_tifxyz, villa 41701aa
tools/sib/factory/runlog.sh pick_window_v7 -- /opt/hv/bin/python tools/sib/factory/pick_window.py
bash tools/sib/factory/run_dryrun.sh                      # factory -> verify -> reproduce.sh -> fault drill
/opt/hv/bin/python tools/sib/factory/verify.py PACKAGE_DIR
PYTHONPATH=src /opt/hv/bin/python -m pytest -q tests/sib_factory_verify_test.py
```

## Failures and corrections (all in runs.jsonl)
- pick_window v1 (per-candidate KD-tree queries) was too slow and was killed (exit 144; the line was written by
  hand). v2-v4: 0 candidates at 432 or 144 vox from whole meshes (best achievable 92.6 vox, adjacent windings)
  and from the PROBE window (on w035 itself). v6 chose a window at 145.0 vox, inside the discretisation margin,
  so the bar was raised to 150 (v7).
- First dry run: reproduce.sh wrote tools/__pycache__ into the package, and the first fault drill passed
  vacuously (every copy failed file_layout first). Fixed with python -B and a drill that requires a clean
  baseline plus a real failure of the named check; the package was rebuilt from the committed code (88079a1).
- Invisible characters were briefly written into the test file as literal characters; cf_scan caught them
  before any commit, and they were replaced by \u escapes.

## Limits
- Byte identity depends on the pinned renderer binary and on numpy/OpenCV versions (recorded in
  package.json; OpenCV matters only for the text glyphs and for INTER_AREA when scale < 1).
- The letter table is fields only in the dry run (no letters are claimed); the 400 mm^2 rule is a conservative
  bounding-box reading of "10 letters within a single 4 cm^2 area".
- The package image is the unflattened tifxyz render; there are no flattening stats yet.

## Next (for the orchestrator to declare or dispatch)
1. Record FACTORY dry-run bar (a) as met by this CT-image package. Bar (b) (a fresh agent rebuilds from the
   tarball and README within 4 h) is not tested: this was a self-reproduce in a clean directory.
2. Paris 4 package mode (DECL-P4-2 item 7; orchestrator 05:25Z/06:01Z): mesh crop +- 1 cm, vc_flatten +
   FLAT-1 stats, raw 2.4 um prediction image, slab-mean CT render, disclosures; DRY RUN on a labelled w028-037
   tile. Not started.
3. Licence check in the verifier (prize page requires open-sourcing after a win). Not started.
4. Ink-map versions (DECL-FACTORY: base map, reference stand-in) reuse the same image path.
