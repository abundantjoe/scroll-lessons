# handcheck

Does a flattened scroll surface read correctly, or is it mirrored or upside down?
handcheck answers this from geometry alone, before anyone looks at the render.

It takes a tifxyz mesh (the `x.tif`, `y.tif`, `z.tif` + `meta.json` format of the official
ScrollPrize/villa tools) and the volume's catalogue flags. It returns, for the grid as stored
(u = column to the right, v = row downward):

- `mirror_u`: flip the columns to read the text unmirrored;
- `flip_v`: flip the rows to put the text top at the image top (`null` when the volume does not say which z end is the top; then only a 180-degree rotation is ambiguous, and never a mirror);
- a confidence (HIGH / MEDIUM) or a flag explaining why no decision is safe.

A mirrored render of Greek text is easy to misread, and it silently breaks ink-model training
labels. handcheck makes the orientation an explicit, checkable property of each mesh.

## The rule

1. The written face (recto) is rolled facing the umbilicus, so text is read from the umbilicus side.
2. With u to the right and v downward, dP/du x dP/dv points into the screen. The viewer is on the
   umbilicus side iff the chirality `sign det[dP/du, dP/dv, r_out]` is +1 in a right-handed frame
   (r_out = the outward radial direction).
3. The volume's index frame has parity -1 if its catalogue says `left_handed_coordinates: true`,
   and +1 if false. The render reads unmirrored iff chirality equals parity. An unknown parity is
   flagged, never guessed.
4. Fragments use the catalogue `text_side` (outward = -text_side) instead of r_out.
5. Up/down comes from `z_direction_is_top_to_bottom`.

r_out comes from independent sources: the official umbilicus (or a CT-mask centroid track as a
proxy), and the mesh's own normal-line centre. The normal-line centre is used only when its
least-squares systems are well conditioned (median condition number <= 10).

Gates, in order:
- the parity must be known;
- the mesh must lie on the scroll in its declared volume (zero CT <= 5 %, outside <= 1 %);
- at least one valid source;
- the sources agree on the whole-mesh sign;
- patches reversed under every source (folds, sheet jumps) are masked out up to 20 %, and flagged above that.

Confidence:
- HIGH needs two sources each agreeing on >= 98 % of vertices, >= 95 % pairwise, and <= 2 % reversed.
- MEDIUM: every source >= 90 % and pairwise >= 80 %, or a single source >= 95 %.

## Use

```
pip install .            # numpy, scipy, tifffile
handcheck path/to/meshes --left-handed false --top-to-bottom true --umbilicus umbilicus.json --out result.json
```

One JSON line per mesh:
- `state`: OK / FLAG / FRAME_UNVERIFIED / PARITY_UNKNOWN
- `confidence`, `mirror_u`, `flip_v`
- `sources`: agreement per source
- `flags`

The command line does not run the frame check, because that needs CT access. Its output carries
"frame not checked". In Python, `handcheck.rule.frame_check_from_volume(points, sampler)` runs it
with any voxel sampler.

## Validation (numbers)

**Planted glyphs** (`python -m handcheck.validate`; the same cases are in `tests/test_rule.py`):
- A font glyph (R or K) is written on the recto of one winding of a synthetic spiral scroll.
- There are 32 cases: 2 glyphs x 4 volume frames x 4 grid parameterisations.
  - Frames: ascending, rotated 180 degrees, reflected in z, reflected in x. The reflections flip the parity.
  - Grid parameterisations: as traced, columns reversed, rows reversed, both.
- The mesh is levelled, the rule decides, and the render along the normals is scored against the
  glyph and its mirror image (normalised cross-correlation, margin 0.2).
  - The rule reads the glyph unmirrored in **32/32** cases (minimum margin 0.262).
  - The wrong-sign control (the opposite mirror decision on the same cases) reads mirrored in **32/32**.

**Up/down from winding (F5).** On PHerc0139, the inward rotation sense along rows spanning more
than one turn predicts the text-top end of z, consistent with the catalogue flag on 36/36 meshes.

**Official meshes** (public data; catalogue flags and official umbilicus or CT-mask centroid):

| scroll | meshes | decision |
|---|---|---|
| PHerc0139 | 38 | 38 OK HIGH, read as stored |
| PHerc0009B | 18 | 18 OK MEDIUM, read as stored |
| PHerc0800 | 6 | 6 OK MEDIUM, read as stored |
| PHerc1447 | 15 | **11 flagged** (10 FRAME_UNVERIFIED, 1 FLAG); 4 OK MEDIUM, read as stored |

**PHerc1447 flags, reported as flags, to be confirmed by the organizers.** These are not claimed errors.

- **10 meshes dated 2025-05-02, z 20,400-24,970, are FRAME_UNVERIFIED.** They lie 41-91 % on zero
  (masked-out) CT and 0-19 % outside the volume they declare (the 8.640 um volume 20250521151220).
  - The traces predate that volume's export, and the catalogue lists no transform for them.
  - No single z shift explains all 10, so their true frame is not recoverable from the mask alone.
  - A render from these meshes at their declared coordinates would show CT from the wrong place.
- **1 mesh (20250502205333) is FLAG.** Its chirality sources conflict: 24 % of vertices disagree,
  3.3 % are reversed under every source, and the normal-line centre is ill-conditioned (condition number 10.3).
  Read it in both mirror states or exclude it.
- **Double-check.** Every one of the 15 decisions was recomputed with this standalone package and matches.
  The frame check was repeated independently at a finer CT pyramid level (level 3 instead of 4, and
  with a 1-voxel dilation), and it gives the same 10 failures and 5 passes.

## Tests

`pip install .[test] && pytest -q`: 112 passed, 1 skipped (the skip is a symmetric-glyph case
where up/down cannot be scored).

## Known limits

- The rule needs the catalogue's `left_handed_coordinates`. Without it, the result is PARITY_UNKNOWN.
- Up/down needs `z_direction_is_top_to_bottom`, or rows spanning more than one turn (the winding check).
- The frame check needs CT access.
- In tightly wound cores, and on short or nearly flat meshes, the normal-line centre is often
  ill-conditioned. The result then rests on the umbilicus or centroid alone (MEDIUM).
- The umbilicus must be in the same volume frame as the mesh. Map it with the catalogue affine
  first; a positive determinant means no reflection.
- Synthetic validation uses clean cylinders-of-spirals. Real sheet jumps are handled only by the
  reversed-patch mask and the flags.

## Licence

MIT (see LICENSE).
