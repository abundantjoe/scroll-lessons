Provenance: Project HERCULES | owner the owner | [id removed]

# p4-excl ASK-1 (2026-09-27): DECL-P4-21 ink fractions conflict with the builder integrity rule

DECL-P4-21 asks p4-excl for the fraction of pixels labelled ink in the official label rasters, mapped onto strip-a tiles w010-027 r0-r5 c9-c19.

The p4-excl brief sets a rule marked "never broken": "NEVER open, Read, view, display or describe any image, map or CT pixels. Mesh coordinates, distances and hashes only."

Computing an ink fraction means reading label raster pixel values over the title zone. "Numbers only" limits what is reported. It does not change what the builder reads.

Done now (geometry only; no raster read):
- logs/sib/p4-excl/label_fractions.json. For each of the 66 tiles:
  - which labelled segments' surfaces cover the tile;
  - the coverage fraction at 2 vox and 20 vox;
  - the minimum distance;
  - the segment grid row and column range the tile maps to.
- The per-vertex tile-to-segment UV map is kept in container scratch. With it, the ink step is a lookup of a few minutes.

Needed: one of the following, recorded in RULES.md.
- (a) An explicit amendment. It would let p4-excl read the label raster values of the labelled segments programmatically, never display or save them, and report only per-tile fractions. p4-excl then finishes within about 30 minutes.
- (b) Assign the ink lookup to another role, using the committed mapping (segment grid ranges; UV map on request).
