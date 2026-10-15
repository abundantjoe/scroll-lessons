Provenance: Project HERCULES | owner the owner | [id removed]

STATUS: DONE (handed-1 and handed-2, 2026-09-25; handed-2 in sections 10-14; decisions in ASK.md and proposals/DECL-HANDED-GEOM.md)

# Task `handed`: handedness from geometry (SG item 12)

Sibling compute session (builder role). Nothing here is a declaration. The proposed declaration text is in `proposals/DECL-HANDED-GEOM.md`.
No image, rendered slice or ink map was opened, viewed or produced. Every result below is a number computed from meshes, metadata, CT-mask statistics, binary label statistics or synthetic volumes.

## 1. Result in one paragraph

The mirror state is set by one sign: the chirality `sign(det[dP/du, dP/dv, r_out])` in the index frame, multiplied by the frame parity from the metadata. It does not depend on the acquisition z direction. The predicted rule for all 26 volumes (23 eligible, plus PHerc0139, PHerc0841 and PHerc0009B) is `convention_sign = +1` in `orient_for_reading`, because every volume is flagged `left_handed_coordinates = false`. The flag `z_direction_is_top_to_bottom` then decides up/down only:
- True: image top = low z.
- False: image top = high z.
- Null (5 eligible volumes): a 180-degree ambiguity remains, but no mirror ambiguity.

The same rule covers PHerc0139 (ascending acquisition z) and PHerc0009B (descending acquisition z, fragment, `text_side = -y`).

Every organizer mesh of 0139 (38 at 9.362 um, 8 at 2.399 um), 0009B (18), 0841 (3) and 0800 (6) is predicted to read unmirrored as stored (u right, v down). Each of these meshes votes +1 under every applicable independent r_out source. On 0139 that means the official umbilicus, the CT-mask centroid and the mesh's own normal-line centre. So state A of the HANDED tests (convention +1) is the geometry-predicted legible state for 0139. The readers' decided votes (A 12 : B 14) were at chance.

PHerc1447 is the exception: 9 of its 15 meshes are FLAGged (details in section 5.4).

The letter-level real-data check is not possible from the official labels. They are binary ink masks with no letter identities (section 6).

## 2. Rule implemented (tools/sib/handed/handed.py)

- **F1 (recto inward).** The recto (written face) is always rolled facing the umbilicus. Source: organizer docs, villa `scrollprize.org/docs/37_2026_open_problems.md`. A reader must view the sheet from the umbilicus side.
- **F2 (display parity).** With u right and v down, `dP/du x dP/dv` points into the screen. So the viewer is on the umbilicus side iff `det[dP/du, dP/dv, r_out] > 0` in a right-handed frame. The official renderer comment agrees: villa `volume-cartographer/apps/src/vc_render_tifxyz.cpp` at HEAD 6e3816c, near the `--flip-normals` option, says the standard readable orientation has N = dP/dU x dP/dV pointing outside, with U winding outside to inside and V along +z.
- **F3 (frame parity).** `parity = -1` if the root catalogue says `left_handed_coordinates = true`, +1 if false, 0 if the flag is missing or the zarr axes are not a permutation of z, y, x. Mesh (x, y, z) is mapped to array axes by name. Rule: `convention_sign = parity`.
- **F4 (fragments).** `n_out := -text_side`, and the same rule applies.
- **r_out sources, in priority order:**
  1. The official umbilicus of the same volume, or one mapped from another volume of the same scroll by the organizer affine.
  2. The CT-mask centroid per slice at zarr level 4, from byte-range reads of single planes. Slice area outliers are rejected (outside 0.2 to 2.5 times the median), then Gaussian-smoothed in z with sigma 256 vox.
  3. The mesh's own least-squares normal-line centre (`hercules.pipeline.centre.geometric_centre_curve`, no CT) as the cross-check.
  4. Lasagna, investigated and rejected as a sign source. Its normal channels are hemisphere-canonicalised: `nz = sqrt(1 - nx^2 - ny^2) >= 0` in villa `lasagna/lasagna/omezarr_pyramid.py`. So they carry no outward sign.
- **Mesh confidence:**
  - HIGH: parity known, the primary vote agrees at >= 0.98, and every pair of independent sources agrees per vertex on >= 0.95 of clear vertices.
  - MEDIUM: vote agreement >= 0.9 and sources >= 0.8, or a single declared source (fragment `text_side`).
  - FLAG: anything else, including sources disagreeing on the whole-mesh sign.
- **Up/down consistency check (F5, not used by the rule).** Rolls start outside and text runs left to right, so reading direction points inward. The inward rotation sense w about +z, measured where a mesh row spans more than one turn, therefore predicts text-top at low z iff `w * parity = +1`.

## 3. Commands (all logged in runs.jsonl with utc, exit code and output sha256; failures included)

```
source /opt/hv/bin/activate
PYTHONPATH=src python -m pytest -q tests/sib_handed_synthetic.py tests/sib_handed_maas.py      # 78 passed
PYTHONPATH=src python tools/sib/handed/synthetic_scores.py logs/sib/handed/synthetic_scores.json
python tools/sib/handed/fetch_meshes.py /work/handed/s3 logs/sib/handed/downloads_meshes.json <tifxyz prefixes>   # 424 objects, sha256 each
python tools/sib/handed/j_points.py /work/handed/j_points_0841.npy logs/sib/handed/j_points_0841.json
tools/sib/handed/run_centroids.sh        # centroid_fetch.py per volume, level 4, every 8th level-4 slice; 0841 with J exclusion
PYTHONPATH=src python tools/sib/handed/analyze_meshes.py logs/sib/handed/mesh_predictions.json
PYTHONPATH=src python tools/sib/handed/build_table.py logs/sib/handed/mesh_predictions.json logs/sib/handed/volume_table.json logs/sib/handed/volume_table.md
source /opt/hv3/bin/activate   # zarr v3 for the sharded label arrays
PYTHONPATH=src python tools/sib/handed/maas_labels.py logs/sib/handed/maas_labels_0139.json
PYTHONPATH=src python tools/sib/handed/maas_coverage.py logs/sib/handed/maas_labels_0139_coverage.json
python tools/sib/handed/summarize.py     # -> handed_summary.json
```

Environment: `/opt/hv` was rebuilt per docker/env/setup_env.sh step 4, plus imagecodecs for LZW tifxyz. `/opt/hv3` is a second venv with zarr >= 3 for the OME-Zarr 0.5 label arrays. Regression check: the existing tests test_geometry_handedness, test_geometry_level, test_pipeline_centre and test_pipeline_window give 71 passed.

## 4. Synthetic validation (tests/sib_handed_synthetic.py, 69 tests; synthetic_scores.json)

**Scene.** An Archimedean spiral scroll with 4.5 turns and pitch 9 vox. A font-rendered capital (R and K, cv2 Hershey simplex) is planted as a density bump 1.2 vox inside the recto face of one winding. It reads correctly from the umbilicus side with its top at low z.

**Frames tested:**
- ascending;
- rot180x: scroll upside down, a proper rotation, z descending;
- reflect_z: slice order reversed, so the metadata declares left-handed;
- reflect_x: in-plane reflection, left-handed.

Each frame was also tested with four input parameterisations: as built, u-mirrored, v-flipped, and both. Every case goes through `level_mesh`, then `orient_for_reading` with the rule sign and the CT-mask-centroid r_out, then a render along normals. The render is correlated (`TM_CCOEFF_NORMED`) with the template and its mirror images.

**Glyph scores:**
- Rule cases: 32/32 unmirrored. Minimum NCC with the true glyph is 0.954. Minimum margin over the left-right mirror is 0.262 (bar 0.2). R is also upright in every case; K is nearly up-down symmetric, so it tests only the mirror.
- Wrong-sign controls: 32/32 come out left-right mirrored.
- Descending z in a proper frame (rot180x) needs the SAME sign as ascending. Using -1 "because z descends" mirrors the glyph (test_descending_z_is_not_a_mirror_in_a_proper_frame).
- Fragment rule (`n_out = -text_side`): unmirrored for both input handednesses.
- Mesh-intrinsic centre instead of the CT centroid: unmirrored.

**Normal-sign and round-trip tests:**
- Normal sign at 12 azimuths (0 to 330 deg) on the spiral with centroid r_out: sign +1, never ambiguous, correct flip for inward normals.
- Crushed cross-section (axis ratio 0.3): ambiguous only at the ends of the major axis, correct sign elsewhere.
- Radial sheet: chirality 0 and prediction FLAG.
- Cylinder round trip (`level_mesh` then `map_back`): maximum error below the double-interpolation chord bound of 0.167 vox. `orient_for_reading` is correct for all 4 combinations of z order and sign. Flips are involutions. Chirality is reversed by a u- or v-mirror and kept by a 180-degree grid rotation.

**Winding sense:** recovered exactly for w = +1 and w = -1, with dr per turn = -9 w vox. It is undetermined (w = 0) for a mesh spanning less than one turn. In all 4 frames, `w * parity = +1` iff text-top is at low z.

## 5. Real geometry (meshes, metadata, centroids; no image, no ink map)

### 5.1 Metadata parity is internally consistent (affine_determinants.json)

- **Affines:** 114 organizer inter-volume affines (landmark fits between scans of the same object, 11 samples).
  - All 100 affines between volumes with the same `left_handed_coordinates` flag have det > 0.
  - All 14 between volumes with different flags have det < 0 (PHercParis4 2023 volume and PHerc0500P2 0.55 um volume, both flagged true).
  - The flag therefore matches the measured reflections 114/114.
- **Acquisition z direction is not a reflection.** Six affine entries (three volume pairs) connect scans of the same scroll with opposite acquisition z directions, and all have det > 0:
  - 0841: 9.366 um descending to 2.403 um ascending, det +59.24.
  - 0814: 9.362 um descending to 2.399 um ascending, det +58.89.
  - 0814: 9.362 um descending to 1.129 um ascending, det +566.8.
- **Up/down is a separate property.** The acquisition z direction and `z_direction_is_top_to_bottom` are independent. For example, 0841 is acquisition-descending but top-to-bottom True, and 0358 is also descending and True.

### 5.2 PHerc0139 (known text, ascending acquisition z, top-to-bottom True, parity +1)

- **Chirality votes:** 38 organizer meshes on the 9.362 um volume. Chirality is +1 under all three sources in 38/38.
  - Minimum per-mesh vote agreement: umbilicus 0.994, normal-line centre 0.990, centroid 0.862. The centroid minimum is on the title segment, which is MEDIUM.
  - Per-vertex sign agreement between sources: umbilicus vs normal-line centre minimum 0.9999; umbilicus vs centroid minimum 0.931; median 1.000 for every pair.
  - The umbilicus is the official 2.399 um annotation, mapped with the organizer affine 20260102150214 -> 20250728140407.
- **Confidence:** HIGH 37, MEDIUM 1 (the title segment).
- **Predicted state:** native grid legible in 38/38; `mirror_u_needed` False and `flip_v_needed` False in 38/38.
- **2.399 um frame:** the same 8 labelled segments give +1 under the native umbilicus and the normal-line centre (8/8 HIGH). The frame change is a det > 0 affine.
- **Winding check (F5):** 36 of the 38 meshes span more than one turn. All 36 give w = +1, and `w * parity = +1` predicts text-top at low z, which equals the organizer flag: 36/36 consistent (7/7 in the 2.399 um frame). Per-mesh pair agreement ranges from 0.70 to 1.00.
- **Centroid reliability:** calibrated against the umbilicus. Median centroid-umbilicus offset is 474 vox (0.247 of the mask radius). The centroid r_out deviates by more than 60 deg on 2.5 % of the papyrus cross-section and by more than 90 deg on 1.0 %.
- **Consequence for the HANDED tests.** The windows used `orient_for_reading` with sign +1 and the mesh normal-line centre, which agrees with the umbilicus at >= 0.9999 on 0139. State A is therefore the geometry-predicted legible state for every HANDED-1, R2 and R3B window.

### 5.3 PHerc0009B (fragment; 8.64 um MAY volume, descending acquisition z, top-to-bottom True, `text_side = -y`)

- **Votes:** 18 organizer meshes on the 8.64 um frame. With `n_out = +y` all 18 vote +1, with minimum agreement 0.997, so the native grid is predicted legible 18/18.
- **Confidence: MEDIUM**, because it rests on a single declared source. `text_side` is taken to mean the direction the inked face points to; that meaning is an assumption and is recorded as such.
- **Other sources:** the centroid and normal-line centre have no meaning on a flat fragment. Their votes are listed as informational only (median agreement 0.80, minimum 0.0008).
- **Frame:** the 8.64 to 2.401 um affine has det +46.7, so the 2.401 um frame carries the same state.
- **Conclusion:** the same convention (+1) holds for ascending 0139 and descending 0009B.

### 5.4 Organizer meshes on PHerc0841 and the eligible volumes

- **PHerc0841** (3 meshes, 9.366 um; descending acquisition z, top-to-bottom True, parity +1):
  - Every vertex within 159 vox (144 + one grid step) of any J-window mesh point was excluded from voting. That leaves 11.1 %, 11.1 % and 9.0 % of the vertices.
  - The level-4 centroid track was computed after zeroing every pixel whose level-0 centre lies within 175 vox of a J point (159,853 level-4 pixels excluded before any statistic).
  - No ink model, render or map of 0841 was produced.
  - Result: +1 under both sources (agreement 0.984 to 0.987 centroid, 0.981 normal-line centre; per-vertex source agreement 1.000). 3/3 HIGH, native grid legible.
  - The winding check is not possible: the kept rows span only 0.25 turn.
- **PHerc0800** (eligible; 6 meshes): 6/6 HIGH, +1 under both sources, per-vertex agreement 1.000.
- **PHerc1447** (eligible; 15 organized meshes): 4 HIGH, 2 MEDIUM, 9 FLAG.
  - On 4 meshes (20250502184201, -184658, -184845, -185519) the CT-mask centroid votes -1 with weak agreement (0.63 to 0.77). The normal-line centre votes +1 at 0.99 to 1.00, and per-vertex agreement between the two is only 0.20 to 0.29. The state of these 4 is UNDETERMINED.
  - Note: `mesh_predictions.json` lists `native_legible = False` for them because the centroid is the primary source. Read FLAG as "undetermined", not as "mirrored".
  - On 5 meshes both sources agree on +1 but with mixed within-mesh chirality (vote agreement 0.55 to 0.87). This is a mesh-quality signal: parts of those meshes run with reversed orientation (folds or sheet jumps), and those parts would render locally mirrored under any global flip.
  - 1447 is oval (centroid axis ratio 0.60). No 1447 mesh spans a full turn, so the winding check is not possible.
- **Other eligible volumes:** 21 of the 23 have no organized segments.
  - PHerc1203 has 22 raw segments whose frame the catalogue marks UNVERIFIED. They were not analysed.
  - PHerc1447 also has 37 raw segments, not analysed.

### 5.5 Centroid reliability calibration (4 volumes with an official umbilicus)

| Volume | axis ratio | centroid-umbilicus offset (vox) | offset / radius | area with r_out error > 60 deg | > 90 deg |
|---|---|---|---|---|---|
| PHerc0125 | 0.51 | 245 | 0.111 | 0.007 | 0.003 |
| PHerc0211 | 0.58 | 308 | 0.157 | 0.034 | 0.015 |
| PHerc0826 | 0.50 | 353 | 0.181 | 0.021 | 0.008 |
| PHerc0139 | 0.81 | 474 | 0.247 | 0.025 | 0.010 |

"Area" means a uniform annulus from 0.15 R to R about the umbilicus. Even on the oval 0125 and 0826, the centroid gives the right outward half-space almost everywhere. The LOW class in the table (axis ratio < 0.5, or named crushed by the brief) is a conservative rule, not a measured failure. The measured failure mode (1447) was caught by the per-mesh cross-check.

## 6. Real-data check with official human ink labels

Labels exist for PHerc0139 (label_set 20260918: 8 segments at 2.399 um, 5 at 9.362 um) and PHerc0841. The 0841 labels were not read, because they are the J benchmark labels.

**No letter identities.** The label arrays are `inklabels.zarr`, `supervision.zarr` and, for 0841, `validation.zarr`. Each is a single-channel uint8 OME-Zarr 0.5 (axes y, x) with no class table, and the attributes contain only transfer provenance. **The labels carry no letter identities, so the requested asymmetric-letter correlation test is not possible from labels alone.**

**Layout test attempted instead.** A reader-free substitute was tried: column slant (Maas's law) of the binary label layout. The slant of a column is kept by a 180-degree rotation and reversed by a mirror, so it tests handedness independently of up/down.
- The estimator is validated on synthetic layouts (tests/sib_handed_maas.py, 9 tests). It recovers -1.5 and -3 deg within 0.8 deg, reverses under a mirror, is unchanged under a 180-degree rotation, is robust to a 5-degree line tilt, and returns no measurement on patches without column edges.
- On the 8 labelled 0139 segments (level 3, 19.2 um/px, resampled into the levelled mesh frame), the supervised regions are patches up to 33 mm across. The widest contiguous ink run is 20.8 mm, narrower than one column. **0 columns were measurable, so the layout test is underpowered on these labels; no result.**
- Label canvas and mesh canvas agree exactly on all 8 segments (for example 22640 x 20400 both ways for w035).

## 7. Per-volume table

The full table (every column, including acquisition z values, the voxel size read from metadata.json, centroid statistics and mesh counts) is in `volume_table.json` and `volume_table.md`.

- **Rule in every row:** "convention_sign = +1 (orient_for_reading: det[dP/du, dP/dv, r_out] = +1)". The only thing that varies is up/down: image top = low z (flag True), high z (flag False), or unknown (flag null).
- **Axes:** z, y, x in every volume; `left_handed_coordinates` false everywhere, so parity +1.
- **Voxel sizes:** read from each volume's metadata.json. 9.362 um for JULY, 8.64 um for MAY, 9.366 um for 0841.

Column key:
- **z acq.:** acquisition z direction (z_start to z_end).
- **top-to-bottom:** root catalogue `z_direction_is_top_to_bottom`.
- **Up rule:** image top = low z (flag True), high z (False), or UNKNOWN (null; up/down only).

| Scroll | Elig. | z acq. | top-to-bottom | Up rule | Centroid reliability | r_out source | Rule confidence | Organizer meshes |
|---|---|---|---|---|---|---|---|---|
| PHerc0125 | yes | asc | null | UNKNOWN | umbilicus-validated, area err > 60 deg 0.007 | official umbilicus | HIGH | none |
| PHerc0191 | yes | asc | False | high z | round (0.82) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0211 | yes | asc | True | low z | umbilicus-validated, 0.034 | official umbilicus | HIGH | none |
| PHerc0257 | yes | asc | False | high z | medium (0.59) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0358 | yes | desc | True | low z | medium (0.59) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0813 | yes | asc | False | high z | round (0.82) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0826 | yes | asc | True | low z | umbilicus-validated, 0.021 | official umbilicus | HIGH | none |
| PHerc0846A | yes | asc | null | UNKNOWN | LOW (0.50, crushed per brief) | centroid + mesh cross-check | LOW | none |
| PHerc0846B | yes | desc | False | high z | LOW (0.42) | centroid + mesh cross-check | LOW | none |
| PHerc1203 | yes | asc | null | UNKNOWN | medium (0.73) | centroid + mesh cross-check | MEDIUM | 22 raw, frame unverified, not analysed |
| PHerc1545 | yes | asc | True | low z | LOW (0.48) | centroid + mesh cross-check | LOW | none |
| PHerc0175A | yes | desc | True | low z | round (0.75) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0175B | yes | desc | True | low z | round (0.86) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0268 | yes | desc | False | high z | round (0.78) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0306B | yes | desc | True | low z | round (0.79) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0343 | yes | desc | False | high z | round (0.75) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0483A | yes | desc | True | low z | medium (0.51) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0483B | yes | desc | False | high z | medium (0.71) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0490A | yes | desc | null | UNKNOWN | round (0.77) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0490B | yes | desc | null | UNKNOWN | round (0.86) | centroid + mesh cross-check | MEDIUM | none |
| PHerc0800 | yes | desc | False | high z | medium (0.61) | centroid + mesh cross-check | MEDIUM | 6: HIGH 6, all legible as stored |
| PHerc1218 | yes | desc | False | high z | LOW (0.48) | centroid + mesh cross-check | LOW | none |
| PHerc1447 | yes | desc | True | low z | medium (0.60) | centroid + mesh cross-check | MEDIUM | 15: HIGH 4, MEDIUM 2, FLAG 9 (4 undetermined, 5 mixed chirality) |
| PHerc0139 | no | asc | True | low z | umbilicus-validated, 0.025 | official umbilicus (affine-mapped) | HIGH | 38: HIGH 37, MEDIUM 1; winding 36/36 consistent |
| PHerc0841 | no | desc | True | low z | round (0.80), J-excluded | centroid + mesh cross-check | MEDIUM (meshes HIGH) | 3: HIGH 3 (J-excluded vertices only) |
| PHerc0009B | no (fragment) | desc | True | low z | n/a (fragment) | -text_side (-y) | MEDIUM | 18: MEDIUM 18, all legible as stored |

Rule confidence in the table is for the volume's rule, independent of any particular mesh. A mesh on a LOW or MEDIUM volume still needs the per-mesh cross-check, and a mesh whose sources disagree must be FLAGged.

## 8. Limits and failures (stated plainly)

- **What the rule rests on.** The rule rests on F1 (organizer documentation), F2 (geometry; the organizer renderer states the same convention) and the metadata parity flag. The flag is internally consistent (114/114 affines). There is no absolute, letter-level real-data confirmation. The strongest independent real-data support is the 0139 winding-versus-top-flag consistency (36/36), which jointly supports parity +1, the top flag and the "text runs inward" prior.
- **Global reflection.** If all organizer volumes shared one global reflection that was never flagged, the affine check could not see it. The winding check would, if the reflection were in-plane, because w would flip against the top flag.
- **Letter-label check:** not possible (no letter identities).
- **Layout (Maas) check:** underpowered (0 measurable columns). The Maas prior is itself a papyrological tendency, not a law.
- **Fragment convention (0009B):** depends on the meaning of the organizer `text_side` field (one declared source).
- **Lasagna:** unusable as a sign source (hemisphere-canonicalised normals).
- **Not analysed:** raw (unorganized) segments of 1203 (frame unverified) and 1447.
- **Run failures:** 26 centroid jobs failed at import on the first batch (missing PYTHONPATH). All 26 were rerun successfully, and both runs are in runs.jsonl. Two synthetic test expectations of mine were wrong at first: a chord-error bound and a winding dr sign that should scale with w. They were corrected with derived bounds, and the code under test was not changed. The first mesh pass failed on 4 LZW tifxyz files until imagecodecs was installed.
- **Files and privacy.** No file over 95 MB. Label arrays and CT planes were never stored or printed. One label attribute and one umbilicus metadata block contain personal names or paths; they were not copied into any file here.

## 9. What the orchestrator needs to declare next

1. **A geometry handedness declaration** (draft in `proposals/DECL-HANDED-GEOM.md`): `convention_sign = parity` (+1 on all 26 volumes), up/down from `z_direction_is_top_to_bottom`, and r_out from umbilicus, else centroid cross-checked per mesh against the normal-line centre. FLAG a mesh when the sources disagree on the whole-mesh sign or the vote agreement is below 0.9. This replaces the reader-based HANDED bar, which failed three times at chance.
2. **Whether to stop rendering both mirror states as separate arms** on 0139, 0841 and the eligible volumes. The proposal is to stop for HIGH and MEDIUM meshes and keep both states only for FLAG meshes, for example 9 of the 15 on 1447.
3. **The 5 eligible volumes with null top-to-bottom** (0125, 0846A, 1203, 0490A, 0490B) keep a 180-degree up/down ambiguity, but no mirror ambiguity. The winding check (F5) can resolve up/down once a mesh on them spans more than one turn. Readers are not needed for that.
4. **An optional absolute confirmation.** If the orchestrator wants letter-level confirmation independent of all metadata, it needs letter-identity labels, which the official data lack. The winding check on eligible meshes spanning more than one turn is the geometric alternative.

---

# Task handed-2 (2026-09-25)

Orchestrator brief:
1. Resolve the 1447 FLAGs.
2. Up/down for the 5 null-flag volumes.
3. Package `orient_for_reading(mesh, volume)` for merge.
4. Finalise the DECL proposal with the SG 12 pass criterion.

Questions and defaults are in `ASK.md`; I continued on the defaults.

## 10. PHerc1447: why the meshes were FLAGged, and the resolution

### 10.1 Frame check (tools/sib/handed/ct_occupancy.py)

- **Method.** Sample every 4th valid vertex at the nearest level-4 voxel of the masked CT volume, in the mesh's declared frame. Chunks are held in memory only; nothing is written.
- **Controls.**
  - PHerc0139: 38 meshes at 0-3.6 % on zero CT, 0 % outside.
  - PHerc0800: 6 meshes at 0 % and 0 %.
- **PHerc1447 split:**
  - The 10 traces dated 2025-05-02 at z 20,400-24,970 lie 41-91 % on zero CT, and 0-19 % of their vertices are outside the volume (z extent 24,297).
  - The other 5 meshes lie 0-1.4 % on zero CT and 0 % outside.
- **Why the 10 are off-frame.** The mask area of 1447 collapses above z of about 22,400 and is almost empty above 23,100. The 10 traces predate the volume's own export (workflow creation 2025-05-21), and the catalogue lists no transform for them. They are therefore not on the scroll in the frame they declare.
- **No single offset explains it.**
  - The best common pure z-shift leaves the worst mesh at 65 % occupancy (h2/ct_occupancy_1447.json).
  - A joint 3-D translation search (h2/frame_search_1447.json) is degenerate. Mask occupancy reaches 1.0 for any offset that pushes the meshes into the scroll body, and the optimum sat at the search boundary (dz = -4096). So the true frame cannot be recovered from the mask. It would need sheet-level registration, which this task did not attempt.

### 10.2 Chirality structure (tools/sib/handed/mixed_chirality.py; h2/mixed_chirality.json)

- **Control.** On 0139, vertices reversed under every source are <= 0.6 %, sources disagree on <= 5.6 % (11.6 % on the title segment), and the normal-line centre has condition number <= 3.0.
- **1447 has two distinct failure types:**
  - Orientation-reversed patches, where every source agrees the local chirality is reversed. This means a fold or sheet jump in the trace: 180708 (16.3 %, one component), 182456 (12.9 %, one component), 205333 (3.3 %) and 183421 (5.1 %).
  - Source conflicts caused by an ill-conditioned normal-line centre (condition number 17-35, i.e. near-parallel normals): 184201, 184658, 184845 and 185519, plus 20250703025628 and 20250702235910. In those, the whole-mesh sign votes had disagreed.

### 10.3 Per-mesh outcome under the packaged rule (h2/rule_applied.json)

| Mesh | handed-1 | z range | zero CT | outside | reversed (all sources) | sources disagree | cond | handed-2 decision |
|---|---|---|---|---|---|---|---|---|
| 20250502180708 | FLAG | 22135-24650 | 0.906 | 0.049 | 0.163 | 0.006 | 6.9 | FRAME_UNVERIFIED |
| 20250502180748 | HIGH | 20830-24678 | 0.593 | 0.049 | 0.000 | 0.000 | 9.7 | FRAME_UNVERIFIED |
| 20250502182142 | HIGH | 20396-23936 | 0.412 | 0.000 | 0.000 | 0.000 | 8.9 | FRAME_UNVERIFIED |
| 20250502182456 | FLAG | 20497-24956 | 0.591 | 0.113 | 0.129 | 0.001 | 9.8 | FRAME_UNVERIFIED |
| 20250502183138 | HIGH | 21116-24096 | 0.524 | 0.000 | 0.000 | 0.013 | 7.8 | FRAME_UNVERIFIED |
| 20250502183421 | FLAG | 20912-24555 | 0.632 | 0.019 | 0.051 | 0.124 | 6.5 | FRAME_UNVERIFIED |
| 20250502184201 | FLAG | 21531-24960 | 0.626 | 0.186 | 0.000 | 0.691 | 34.1 | FRAME_UNVERIFIED |
| 20250502184658 | FLAG | 20970-24962 | 0.582 | 0.160 | 0.000 | 0.649 | 17.5 | FRAME_UNVERIFIED |
| 20250502184845 | FLAG | 20571-24971 | 0.466 | 0.143 | 0.000 | 0.766 | 21.5 | FRAME_UNVERIFIED |
| 20250502185519 | FLAG | 21608-24662 | 0.553 | 0.072 | 0.000 | 0.727 | 16.7 | FRAME_UNVERIFIED |
| 20250502205333 | FLAG | 12616-15980 | 0.000 | 0.000 | 0.033 | 0.244 | 10.3 | FLAG (both mirror states, or exclude) |
| 20250702235910 | MEDIUM | 11308-14088 | 0.000 | 0.000 | 0.000 | 0.219 | 15.5 | OK MEDIUM (centroid only; mesh centre ill-conditioned) |
| 20250703025628 | FLAG | 3017-6961 | 0.000 | 0.000 | 0.012 | 0.432 | 35.4 | OK MEDIUM (centroid only; 1.2 % reversed masked) |
| 20250703034159 | HIGH | 3693-7182 | 0.000 | 0.000 | 0.007 | 0.022 | 2.9 | OK MEDIUM (mesh-centre agreement 0.949 < 0.98) |
| 20251105093211 | MEDIUM | 5838-15277 | 0.014 | 0.000 | 0.055 | 0.000 | 7.8 | OK MEDIUM (5.5 % scattered reversals masked) |

In all 4 OK decisions the organizer grid is read as stored (`mirror_u = False`, `flip_v = False`).

**Important correction to handed-1.** Three meshes that handed-1 rated HIGH (180748, 182142, 183138) lie 41-59 % on zero CT. Their handedness vote was internally consistent, but they are not on the scroll in their declared frame. The frame gate is therefore required before any confidence is reported.

**Rule changes relative to handed-1:**
- frame gate added;
- the mesh normal-line centre is a source only if its condition number is <= 10;
- the centroid is informational when an umbilicus exists. This fixed the 0139 title segment, which is now HIGH;
- patches reversed under every source (<= 20 %) are masked out rather than voting.

Effect elsewhere: 0139 is 38/38 HIGH. On 0800 all 6 and on 0841 2 of 3 drop to MEDIUM, because their normal-line centre is ill-conditioned (condition number 13-23) and the centroid becomes the single source. The mirror state is unchanged in every case.

## 11. The package (tools/sib/handed/pkg/)

- `src/hercules/geometry/handed_rule.py`: `orient_for_reading(mesh, volume, *, frame=None, keep=None) -> HandedDecision`. The decision carries state, confidence, convention_sign, chirality, mirror_u, flip_v, rot180_equivalent, keep, reversed_frac, sources and flags, plus `.apply(arr, flip_v=None)`. Also included: `VolumeInfo.from_metadata`, `FrameCheck`, `frame_check_from_volume`, `normal_line_centre`, `winding_sense`, `up_from_winding`, `frame_parity`, `text_side_vector`.
- `src/hercules/geometry/handed_synth.py`: synthetic spiral scrolls with a planted font glyph. Test helper only.
- `tests/test_geometry_handed_rule.py`: 55 tests.
  - planted R/K glyph in 4 frames x 4 parameterisations;
  - native-grid fields;
  - up/down unknown (both 180-degree candidates unmirrored);
  - parity-unknown, frame, reversed-patch, ill-conditioned-centre, source-disagreement and umbilicus-precedence gates;
  - the keep mask;
  - fragments;
  - winding-based up/down in 4 frames.
- `run_merged_tests.sh`: overlays the package on a clean `git archive HEAD` and runs the new tests plus the existing geometry and pipeline tests. Result: 126 passed, 1 skipped. The skip is designed: K is up-down symmetric, so its 180-degree rotation equals its mirror image. The script prints the sha256 of every package file.
- The existing `level_mesh.orient_for_reading` is untouched. The new function lives in its own module.

## 12. Up/down for the 5 volumes with z_direction_is_top_to_bottom = null

The mirror state is already decided for these volumes. Only a 180-degree rotation is open, and the package reports it as `flip_v = None, rot180_equivalent = True`.

### 12.1 Geometric method (F5, validated)

- **Principle.** Rolls are read inward: the beginning is outside and the end title sits at the core. The villa renderer comment agrees ("U winding outside->inside"). So text-top is at low z iff `w * parity = +1`, where w is the inward rotation sense about +z.
- **Validation on 0139.** Measured along mesh rows that span more than one turn (`handed_rule.winding_sense`), F5 agrees with the organizer flag on 36/36 0139 meshes, and on 7/7 of the same segments in the 2.399 um frame. Row spans were 1.00-1.31 turns, with 22-35,381 phi + 2 pi pairs per mesh. The per-mesh pair agreement was 0.70-1.00, so a single short trace is weak evidence.
- **Proposed requirement per volume:**
  - at least 2 traces;
  - each passes the frame gate;
  - each has a row spanning >= 1.05 turns and >= 200 pairs, with pair agreement >= 0.8;
  - the r_out source is valid (umbilicus, or a centroid cross-checked by a normal-line centre with condition number <= 10);
  - all traces agree on w.
- **Synthetic check.** `test_winding_predicts_up` checks F5 in all 4 frames.

### 12.2 CT-only estimator (pitch angle): NEGATIVE result, not usable

`tools/sib/handed/spiral_sense.py` estimates w from the tilt of the sheets against the circumferential direction in axial slices. It uses a structure tensor and a harmonic fit of psi * r in phi, which removes first-order centre-error bias and second-order crushing bias.
- **Synthetic.** Correct sign in all resolved cases (tests/sib_handed_spiral.py, 9 tests), including a 15 px centre error and a 0.45 axis-ratio crush. The documented limit: the sign becomes unreliable when crushing compresses the sheet spacing to about 1 px.
- **Real data** (h2/spiral_sense_0139_L1.json). On PHerc0139 at level 1 (18.7 um/px) with the official umbilicus as centre, the 16 slices give a0 between -60 and +133 vox, split 8 positive / 8 negative. The expected pitch term is about +3 vox (sheet spacing / 2 pi). The median sign happened to be right, but the per-slice scatter is about 20 times the signal.
- **Earlier level-2 run.** The mean-psi version gave the wrong sign for 0841 (5 slices negative, 4 positive).
- **Conclusion.** Real sheet deformation dwarfs the pitch angle. Winding sense has to come from traced sheets spanning more than one turn, not from local CT orientation. The 26-volume validation run was stopped after this finding, so no CT-only up/down claim is made anywhere.

### 12.3 What would settle each volume

| Volume | Current material | r_out available | What settles up/down |
|---|---|---|---|
| PHerc0125 | no segments | official umbilicus (centroid validated: area error > 60 deg 0.7 %) | >= 2 own traces meeting the 12.1 requirement; or the organizers filling `z_direction_is_top_to_bottom` |
| PHerc0846A | no segments; 2.403 um rescan with no registration | centroid LOW (axis ratio 0.50, crushed) | own traces meeting 12.1 with a valid normal-line centre (condition <= 10) or an umbilicus annotation; or the organizer flag |
| PHerc1203 | 22 raw auto-grown segments. All pass the frame gate (<= 0.2 % zero CT, 0 % outside). Rule: OK 6 (HIGH 1, MEDIUM 5), FLAG 16. Longest row span 1.00 turn (auto_grown_20251005221856743, which also has 14 % reversed), so w is undetermined for every segment | centroid (axis ratio 0.73) | a trace spanning >= 1.05 turns (growing the longest raw segment further would do); or the organizer flag |
| PHerc0490A | no segments | centroid GOOD (0.77) | own traces meeting 12.1; or the organizer flag |
| PHerc0490B | no segments | centroid GOOD (0.86) | own traces meeting 12.1; or the organizer flag |

The 1203 raw segments are catalogued as frame UNVERIFIED. They pass the frame gate here: they lie on the scroll in the eligible volume's frame. In 5 of the 6 OK decisions, the raw grid needs `mirror_u = True`. That is expected: raw auto-grown grids do not follow the organizer (u, v) convention, and the rule handles either orientation.

## 13. Files for handed-2

Under `logs/sib/handed/`:
- `h2/ct_occupancy_{1447,0800,0139}.json`
- `h2/frame_search_1447.json`
- `h2/mixed_chirality.json`
- `h2/rule_applied.json` (every organizer mesh under the packaged rule)
- `h2/raw_1203.json`
- `h2/spiral_sense_0139_L1.json`
- `ASK.md`
- `proposals/DECL-HANDED-GEOM.md` (final draft)

Under `tools/sib/handed/`:
- `pkg/` (merge package)
- `ct_occupancy.py`, `frame_search.py`, `mixed_chirality.py`, `apply_rule.py`, `raw_segments.py`, `spiral_sense.py`, `run_spiral.sh`

Tests: `tests/sib_handed_spiral.py`. The sibling test total is 87 passed. The package overlay gives 126 passed and 1 designed skip.

## 14. Failures and corrections in handed-2 (stated plainly)

- **Logging defect.** `logrun.sh` recorded the exit code of the last stage of a pipe (for example `tail`). One failing pytest run was therefore logged as exit 0. Fixed with `pipefail`, and a NOTE line was added to runs.jsonl. The outputs and hashes of earlier runs are unaffected.
- **Stray file.** Importing `apply_rule.py` from `raw_segments.py` ran its top-level loop and wrote a stray JSON file named `PHerc1203` in the repository root. It was deleted before any commit, and `apply_rule.py` now has a `__main__` guard.
- **My own `pkill -f` killed my own shell** once. No data effect.
- **Package test fixes.**
  - A genuine bug: `np.linalg.solve` raised on an exactly singular normal-line system. Such bands are now recorded as ill-conditioned (condition = inf).
  - A test-design error: the K glyph's 180-degree rotation equals its mirror image, so the up/down-unknown test runs only on R.
- **Rule design fix.** The centroid had vetoed the official umbilicus on the 0139 title segment. It is now informational when an umbilicus exists, with a dedicated test.
- **Search stopped early.** The 3-D frame-offset search was degenerate (see 10.1). No frame correction is proposed for the 10 1447 traces.

## 15. Per-mesh frame status, PHerc1447 and PHerc0800 (orchestrator request, 19:28Z)

The orchestrator accepted all five ASK defaults on 2026-09-25 at 19:28Z.

- **Method.** Every 4th valid vertex is sampled at the nearest level-4 voxel of the masked eligible volume, in the mesh's declared frame (`tools/sib/handed/ct_occupancy.py`). Gate: FRAME-UNVERIFIED if more than 5 % of vertices are on zero CT or more than 1 % are outside the volume.
- **Why it matters for the RAW overviews.** A RAW overview rendered from a FRAME-UNVERIFIED mesh shows mostly masked-out (zero) CT, or CT from the wrong place, not papyrus at the declared location. Treat any such overview as uninformative.
- **SG 10 note (orchestrator).** Any masked, reversed area inside a candidate rectangle R vetoes that rectangle.

| Scroll | Segment id | z range (vox) | zero-CT fraction | outside-volume fraction | Frame status | Handedness decision |
|---|---|---|---|---|---|---|
| PHerc1447 | 20250502180708-auto_grown_20250502160708188 | 22135-24650 | 0.906 | 0.049 | FRAME-UNVERIFIED | excluded (not read) |
| PHerc1447 | 20250502180748-auto_grown_20250502160748721 | 20830-24678 | 0.593 | 0.049 | FRAME-UNVERIFIED | excluded (not read) |
| PHerc1447 | 20250502182142-auto_grown_20250502161324419 | 20396-23936 | 0.412 | 0.000 | FRAME-UNVERIFIED | excluded (not read) |
| PHerc1447 | 20250502182456-auto_grown_20250502161202782 | 20497-24956 | 0.591 | 0.113 | FRAME-UNVERIFIED | excluded (not read) |
| PHerc1447 | 20250502183138-auto_grown_20250502162038685 | 21116-24096 | 0.524 | 0.000 | FRAME-UNVERIFIED | excluded (not read) |
| PHerc1447 | 20250502183421-auto_grown_20250502161744358 | 20912-24555 | 0.632 | 0.019 | FRAME-UNVERIFIED | excluded (not read) |
| PHerc1447 | 20250502184201-auto_grown_20250502163549332 | 21531-24960 | 0.626 | 0.186 | FRAME-UNVERIFIED | excluded (not read) |
| PHerc1447 | 20250502184658-auto_grown_20250502163923577 | 20970-24962 | 0.582 | 0.160 | FRAME-UNVERIFIED | excluded (not read) |
| PHerc1447 | 20250502184845-auto_grown_20250502164121265 | 20571-24971 | 0.466 | 0.143 | FRAME-UNVERIFIED | excluded (not read) |
| PHerc1447 | 20250502185519-auto_grown_20250502164303733 | 21608-24662 | 0.553 | 0.072 | FRAME-UNVERIFIED | excluded (not read) |
| PHerc1447 | 20250502205333-auto_grown_20250502181030065 | 12616-15980 | 0.000 | 0.000 | OK | FLAG FLAG |
| PHerc1447 | 20250702235910-auto_grown_20250702235910292 | 11308-14088 | 0.000 | 0.000 | OK | OK MEDIUM, mirror_u=False, flip_v=False |
| PHerc1447 | 20250703025628-auto_grown_20250703025628283 | 3017-6961 | 0.000 | 0.000 | OK | OK MEDIUM, mirror_u=False, flip_v=False |
| PHerc1447 | 20250703034159-auto_grown_20250703034159599 | 3693-7182 | 0.000 | 0.000 | OK | OK MEDIUM, mirror_u=False, flip_v=False |
| PHerc1447 | 20251105093211-z_dbg_gen_00320 | 5838-15277 | 0.014 | 0.000 | OK | OK MEDIUM, mirror_u=False, flip_v=False |
| PHerc0800 | 20251028213516-auto_grown_20251028213516907 | 11085-13076 | 0.000 | 0.000 | OK | OK MEDIUM, mirror_u=False, flip_v=False |
| PHerc0800 | 20251028220042-auto_grown_20251028220042762 | 11153-13033 | 0.000 | 0.000 | OK | OK MEDIUM, mirror_u=False, flip_v=False |
| PHerc0800 | 20251028220955-auto_grown_20251028220955262 | 10986-12902 | 0.000 | 0.000 | OK | OK MEDIUM, mirror_u=False, flip_v=False |
| PHerc0800 | 20251028222030-auto_grown_20251028222030940 | 10867-13189 | 0.000 | 0.000 | OK | OK MEDIUM, mirror_u=False, flip_v=False |
| PHerc0800 | 20251028225813-auto_grown_20251028225813045 | 11107-13243 | 0.000 | 0.000 | OK | OK MEDIUM, mirror_u=False, flip_v=False |
| PHerc0800 | 20251029010146-auto_grown_20251029010146642 | 11618-12494 | 0.000 | 0.000 | OK | OK MEDIUM, mirror_u=False, flip_v=False |

10 of 21 meshes are FRAME-UNVERIFIED.

## 16. P4 reading orientation of the title canvases (dispatch 2026-09-26 18:49Z; requested as "section 13", which was already taken)

Output: `logs/sib/handed/p4orient.json` (sha256 355c8fe532d4ab88de0bda4aaaabcf45055745262ad9e918e40d9e9107694316). Tool: `tools/sib/handed/p4orient.py`, which applies the packaged DECL-HANDED-GEOM rule unchanged. Geometry and metadata only. No image, render, ink map or surface-volume voxel was opened.

**Verdict.** A tile rendered on its canvas (canvas row down, column right; canvas pixel c <-> grid (c + 0.5) * scale) reads **unmirrored and upright as rendered. It needs no horizontal flip and no vertical flip**, on both title grids.

| canvas | frame (voxel from metadata.json) | state | confidence | mirror_u | flip_v | tiles agreeing |
|---|---|---|---|---|---|---|
| strip-a 20260701183124-w010-027 (P4-B strip a / E2; T 8343) | 20260411134726, 2.4 um | OK | MEDIUM | no | no | 189/189 (min 0.973) |
| M2a / E1 20260623141924-w010-027 | 20260608103018, 1.129 um | OK | MEDIUM | no | no | 126/126 (min 0.990) |
| same segment, cross-check | 20260411134726, 2.4 um | OK | MEDIUM | no | no | 126/126 (min 0.990) |
| known-text control 20260701183125-w028-037 | 20260411134726, 2.4 um | OK | HIGH | no | no | 189/189 (min 0.963) |

Why each canvas gets this verdict:
- **Parity is +1 in both frames.** Both volumes have `left_handed_coordinates` false and zarr axes (z, y, x). The organizer affine 20260411134726 -> 20260608103018 has det +9.58, so it is not a mirror.
- **Chirality is +1.** It is measured as sign det[dP/du, dP/dv, r_out] with r_out taken from the official umbilicus (`20260411134726-umbilicus-20260524235033.json`, sha256 5759e460...474e). The umbilicus is native on 2.4 um and mapped by the affine onto 1.129 um. The umbilicus agrees on >= 0.9998 of vertices. The independent normal-line centre (cond 1.9-2.2) gives the same sign. Chirality equals parity, so mirror_u = no.
- **Up/down.** Volume 20260411134726 has `z_direction_is_top_to_bottom` = false (image top = high z). The 1.129 um volume has a null flag. The flag is carried to it through the affine, because +z maps to (0.0004, -0.0023, 1.0000). This carry is MEDIUM (carried, not declared).
  - On every canvas, rows run from high z to low z: 98.3-98.7 % of row steps decrease z. Strip-a row 0 is at 172.6 mm and the last row at 29.0 mm (the brief's r0 about 165 mm agrees). So flip_v = no.
- **Independent F5 check (winding sense).** Rows span 18 turns on w010-027 and 10 on w028-037. w = -1 on all four meshes (agreement 0.94-0.997). Under parity +1 this predicts text-top at high z, which is consistent with the flag on every mesh.
- **Canvas axes (numbers).** Column 0 is the outer end on both strips. Per-tile-column median radius:
  - strip-a: 5.21 mm (c0) -> 1.73 mm (c20);
  - w028-037: 7.10 mm (c1) -> 5.23 mm (c20), which continues into strip-a c0;
  - M2a: 5.63 -> 2.82 mm.
  So text on these canvases runs outer -> inner, left to right.
- **Frame checks** (`logs/sib/handed/p4/`):
  - 2.4 um: 0 % outside and 0-0.07 % zero CT on all three meshes.
  - 1.129 um: 28.9 % of the vertices lie outside the ROI mosaic, and 2.3 % of the inside vertices are on zero CT.
  - Declared deviation: on 1.129 um the whole-mesh outside gate is replaced by excluding the outside vertices (keep = inside the level-0 bounds). The same segment passes every gate in the 2.4 um frame with the identical verdict.
- **Why MEDIUM on the title grids.** The normal-line centre agrees 0.956-0.963, below the HIGH bar of 0.98. The tightly wound core (radius 1.7-6 mm) makes that estimator noisier. The umbilicus itself agrees >= 0.9998, and every tile agrees. The rule was not changed to lift the grade.

**Validation on w028-037, stated plainly.**
- The rule gives this known-text strip HIGH / unmirrored / upright as stored. The organizers publish this canvas with no flip or rotation field: the data_browser index.json keys contain no transform, and the viewer code has no scale(-1) or rotate on these images. They state "Substantial continuous Greek text recovered; ink clearly legible at 2.4 um" with "Ink detection across windings 28-37 (2.4 um)".
- Their readings therefore imply that the canvas as stored is legible. That matches the rule's prediction.
- This is indirect evidence. No organizer statement names an orientation numerically, and none of their images was viewed.
- The rule's direct validation remains 0139 (36/36 F5, 38/38 HIGH).
- Strip-a and M2a come from the same organizer pipeline, frame and axis conventions as w028-037, and they give the same chirality, parity and z-grading.

**Commands** (in runs.jsonl):
- fetch_meshes.py (16 objects, manifest p4_mesh_manifest.json)
- ct_occupancy.py on 2.4 um (level 4) and on 1.129 um (level 5). The first 1.129 um attempt was killed for memory (logged), and the rerun succeeded.
- p4orient.py: an unframed run, then the final run. A first attempt had a syntax error and was killed (OOM) on the undecimated 1.129 um mesh; both failures are logged. The 1.129 um mesh is analysed at every 3rd row and column; the canvas mapping accounts for the decimation.

Not done by this sibling: the SessionStart standing order (prompt regeneration workflow) is addressed to the orchestrator. It writes outside logs/sib/handed and tools/sib/handed, so it was not run here.

Integrity: no issues.

## 17. handcheck: Progress Prize package (DECL-PP-1; dispatch 2026-09-27 00:58Z)

- **Package:** tools/sib/handed/handcheck/ (14 files).
  - It is standalone: numpy, scipy and tifffile; opencv is needed only for tests and validation.
  - The rule, the tifxyz I/O and the levelling are vendored unchanged apart from import paths and docstrings. One metadata key was renamed, which has no effect on decisions.
  - New files: a CLI over a folder of tifxyz (`handcheck`), `handcheck.validate`, a README, the MIT LICENSE and pyproject.
- **Tests:** 112 passed, 1 skipped. The suite also passes in an isolated copy with no repo on the path.
  - 32 planted-glyph cases.
  - 32 wrong-sign controls (new).
  - 6 CLI tests (new).
  - The level_mesh and rule unit tests.
- **Validation, recomputed with the packaged code** (logs/sib/handed/pp/validation.json): the rule reads the glyph unmirrored in 32/32 cases (minimum margin 0.262), and the wrong-sign control reads mirrored in 32/32.
  - The earlier 32/32 in synthetic_scores.json came from the handed-1 code path. This is the packaged rule.
- **PHerc1447 double-check** (logs/sib/handed/pp/check_1447.json, sha256 e16f0efe6a863681d35cc26b4b6615cb90fe627dba46f84f0f8ab0d8de88cd0e):
  - 11 of 15 are flagged: 10 FRAME_UNVERIFIED and 1 FLAG (20250502205333). 4 are OK MEDIUM.
  - All 15 decisions are identical to h2/rule_applied.json.
  - An independent frame recheck (level 3 instead of 4, +-1 voxel dilation; logs/sib/handed/pp/ct_occupancy_1447_L3_dil1.json) gives zero CT 0.42-0.92 on the 10 and 0-0.014 on the 5. The gate outcomes are the same.
  - **Correction to the dispatch:** "9 of 15" was the handed-1 count. The README states 11 of 15, as flags to be confirmed by the organizers.
- **Content rules:**
  - no Paris 4 data or numbers;
  - PHerc0841 is omitted from the README table (its J windows are sealed material);
  - no project paths, RULES, hashes, keys or governance references;
  - no personal information.
- **Scrub** (tools/sib/handed/pp_scrub.py → logs/sib/handed/pp/scrub.json, sha256 e3cf70dd918480c0a16a3e140a68c53199c81ea622bd7f72ceec0b75f62e7825): **PASS.**
  - Checks: secrets and keys, local paths, Paris-4 search identifiers, project/governance coupling, personal information, Cf characters, binaries/caches, size, and the MIT licence.
  - All findings are 0.
  - A positive control with planted strings (a key, a /work path, Paris-4 ids and "hercules") was caught: 6 findings, FAIL.
- **Not done here:** publication, the form, and the pp/handcheck/ copy (ASK item 1). The orchestrator owns these.

Integrity: no issues.
