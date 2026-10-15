# tifxyz-dist: contribution text
<!-- Numbers from sib-p4-excl REPORT/tests; the demo must use NON-Paris-4 segments. Re-check against the pp-tifxyz-dist README. -->
tifxyz-dist computes exact distances between points or meshes and tifxyz surfaces. Its main use is certifying that a prediction region does not overlap training data.

(1) Data: organizer tifxyz meshes from the public open-data bucket. The demo uses public segments of <scroll named in the package README>.

(2) All milestone prizes require "no overlap between training and prediction regions". tifxyz-dist returns the exact minimum 3-D distance from any point set or mesh to a triangulated tifxyz, splitting every valid quad into two triangles. An entrant can state, and the team can re-check, the clearance between a candidate region and every training segment.

(3) It avoids sampled or vertex-to-vertex approximations. A KD-tree over the vertices plus a proven covering bound (every point of a triangle lies within L/√3 of one of its vertices) gives exact point-to-triangle minima without densifying the mesh. A certified lower bound is reported for thresholds. It also reports mesh-to-mesh spacing and near-contacts.

(4) Evidence: 21/21 tests. The batched method, a per-point loop and brute force agree exactly on curved sheets with holes, folds, a hole rim and a worst-case lattice. On a real organizer mesh, points on the surface return at most 1.6e-11 voxel. Code MIT.
