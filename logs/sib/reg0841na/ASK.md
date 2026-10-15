Provenance: Project HERCULES | owner the owner | [id removed]

# reg0841-NA: questions for the orchestrator (work continues on each default)

1. The list of the 288 D3 fold-A pool tiles is not in the repo: logs/d1/d3_stage1.json has only the counts and
   the 18 dropped tiles, and the manifest /work/d3/pool_fa/manifest.json is not in this container. Rebuilding
   the list exactly needs ref9 (an ink map), which I will not read.
   DEFAULT: evaluate the displacement at the centre of every tile that passes the geometric part of the PRIMARY rule:
   128 px, stride 64, >= 90 % mesh-valid pixels, and every mesh-valid pixel >= 144 vox (point-to-surface) from J.
   This set contains the 288. I report it as "geometric superset". Please push the 288 origins
   (segment, y0, x0) to any path in the repo and I will subset. The 18 dropped tiles are reported separately.
2. "Locally measured CT alignment" at the tile centres: a 48x256x256 block around a tile centre usually
   comes within 144 vox of J, so no new CT is read there.
   DEFAULT: use the fitted field. It is CT-derived from patches >= 144 vox (point-to-surface) from J, evaluated at
   the tile centres, and reported with its leave-one-out uncertainty.
3. The "organizer mapping" at a canvas point.
   DEFAULT (primary): the organizer's own mesh pair, i.e. the 9 um mesh point and the 2.4 um mesh point at the
   corresponding UV (c2 = (c9 + 10) N2/N9 - 10). Also reported: the organizer mesh affine. The displacement is given in
   9 um vox as a 3-D vector, and split into the mesh normal component and the in-surface component.
4. Working folders for this task: logs/sib/reg0841na/, tools/sib/reg0841na/, tests/sib_reg0841na_*.py.
   The code imports the reg0841 modules unchanged.
