Provenance: Project HERCULES | owner the owner | [id removed]

# Clarification to prereg_heldout.md

Committed before any level-0 block is read. `prereg_heldout.md` is not edited.

Model-selection item 3 contains a garbled sentence. Its intended and binding meaning is the reg0841na "Q" field, exactly as in the sibling code (tools/sib/reg0841na/field.py, `quad_feats`):
- f(p) = A (p + u(p)) + c, where A and c are the final 2-pass affine;
- u(p) = W^T [x, y, z, 1, x^2, xy, y^2], with coordinates divided by 1000 and W of size 7 x 3 (21 parameters);
- u is fitted by least squares to the fit-patch residuals d9 under that affine.

The only candidates are the affine and this Q field. No RBF or other field is considered. The selection criterion is leave-one-out RMS over the 24 fit patches, as stated.

Level handling. Blocks of the 2.215 um volume are read at level 1. For the fit the affine is expressed in level-1 coordinates, A1 = A0 / 2 and c1 = (c0 - 0.5) / 2, and converted back with A0 = 2 A1 and c0 = 2 c1 + 0.5. Reported residuals are in 9 um vox.
