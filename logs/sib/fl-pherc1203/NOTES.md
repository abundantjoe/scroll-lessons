Provenance: Project HERCULES | owner the owner | [id removed]
# fl-pherc1203 notes (numbers only; no image viewed)
- Material: organizer raw tifxyz (s3 PHerc1203/segments/raw/, 22 dirs; 17 pass checks, 5 T0 tracer test ids excluded). Implied voxel from meta area_cm2/area_vx2 = 9.362 um and bbox inside the 9.362 um level-0 shape, so the segments are in 20250820131727 coordinates (closes the catalogue's UNVERIFIED note for these 3).
- Picked (3 largest): auto_grown_20251005230830031 16.10 cm^2, ...231446965 12.53 cm^2, ...221856743 11.79 cm^2.
- GEOMETRY CAVEAT: vc_tifxyz_selfcross finds all 3 NOT clean: transverse contacts 15927/19911, 8951/7999, 12717/11033 (two triangulations). Organizer segments are not filtered on this (brief), but any candidate tile must be checked against the crossing sites (selfcross.json) before a reading counts: a tile over a crossing may mix sheets.
- Env fixes (pushed): vc_build.sh takes the proxy from $HTTPS_PROXY; setup_env.sh installs vesuvius with pip --ignore-requires-python (uv refuses the 3.14 pin) and is idempotent per step.
- Infer takes the centre 17 of the 31 render slices (select_layer_indices center crop); forward = ink.tif, reverse = ink_reverse.tif.
- Context: RESUME_NOW 03:50Z records that the orchestrator's creation of further FL workers was classifier-denied and left to the owner; this worker was dispatched afterwards at the owner's request.
