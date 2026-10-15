# Published VC3D image check, 2026-10-15 (fresh container)

Question: is `ghcr.io/scrollprize/villa/volume-cartographer:edge` still the stale build recorded in RULES.md G-B
(pre-run note, 2026-09-16: "built 2026-05-13, villa 1e3f4c0 ... has no `--flip-normals` (added 2026-06-17)")?

## Registry metadata (anonymous GHCR API, 2026-10-15)
- Tags `edge` and `main` resolve to the same OCI index; linux/amd64 manifest `sha256:b2509de2c107...`.
- Image config: `created` 2026-05-13T18:41:20Z; labels `org.opencontainers.image.revision` =
  `1e3f4c021f4e53bea3867772ed05f51a7e586a9c`, `org.opencontainers.image.created` = 2026-05-13T18:26:28.356Z.
- `docker pull ...:edge` -> local digest `sha256:bad516f66001abca759454cc43e4fd11e5b19aa55d36bdc2043817291c8083c4`, 12 GB.

## The binary
- `vc_render_tifxyz --help` inside the image: saved verbatim in `vc_render_tifxyz_help_edge_2026-05-13.txt` (this
  directory). It lists `--flip arg (=-1)  Flip: 0=V, 1=H, 2=Both` (an image flip) and **no `--flip-normals`**.
- Running it with `--flip-normals` prints `Error: unrecognised option '--flip-normals'` and exits 1.

## What the public documentation says (scrollprize.org, fetched 2026-10-15)
- https://scrollprize.org/segmentation: "We host an up-to-date image on the github container registry which can be
  pulled with a simple command : docker pull ghcr.io/scrollprize/villa/volume-cartographer:edge".
- https://scrollprize.org/tutorial5 (ink detection): the render command ends in `--flip-normals`, and the page says
  "--flip-normals reproduces the depth orientation of the published renders and the training labels".

## Reading
- VERIFIED: the image the segmentation page calls up to date cannot run the render command in the ink tutorial.
- MEASURED (2026-09-16, RULES.md G-B pre-run note): a 256 x 256 smoke render of the w040 mesh with this binary matched
  the team stack only with the slice order reversed, at Pearson 0.42-0.82 per slice.
- INFERENCE: a user who drops the unrecognised flag to make the command run gets the depth order the model was not
  trained on. On known text, that order scores at chance (Gate A reverse AUC 0.49633 vs forward 0.99659, RULES.md G-A).
  This was not run end to end with the stale binary.
- Workaround used by this project: build the tools from villa source (`scripts/build_vc3d.sh`, villa 5ab585f). The
  rebuilt renderer matches the team stack at Pearson >= 0.999999 on all 28 slices (RULES.md G-B Bar 1).

## Corrections (appended 2026-10-15, after an adversarial check of docs/UPSTREAM_ISSUES.md)
The two readings above are kept as written. Their corrected forms are:
- "VERIFIED: ... cannot run the render command in the ink tutorial" says more than was run. What was run is the
  binary with `--flip-normals`, which the tutorial's render command ends in. That printed the error and exited 1. The
  tutorial's full command was not run against this image. Corrected reading: VERIFIED, the image the segmentation page
  calls up to date rejects `--flip-normals`, the flag the ink tutorial's render command ends in.
- "Pearson >= 0.999999" turns a six-decimal minimum into a bound. RULES.md G-B Bar 1 records "Pearson min 0.999999
  over the 28 slices", and a true minimum below 0.9999990 that rounds to 0.999999 would break the bound. Corrected
  reading: minimum Pearson 0.999999 (six decimals) on the 2048 x 2048 crop, not bit-identical (identical-pixel
  fraction min 0.9956).
