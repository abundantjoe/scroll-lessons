Provenance: Project HERCULES | owner the owner | [id removed]

# RESUME (task handed)

- handed-1, handed-2 and ktlb4p-prep: DONE (REPORT sections 1-15; logs/sib/ktlb4p-prep/REPORT.md).
- P4 orientation (dispatch 2026-09-26 18:49Z): logs/sib/handed/p4orient.json and REPORT section 16. Section 16 is the section the dispatch requested as "section 13"; 13 was already taken. Tool: tools/sib/handed/p4orient.py.
- Frame checks: logs/sib/handed/p4/ct_occupancy_p4_2p4.json and ct_occupancy_p4_1p129.json.
- Mesh hashes: logs/sib/handed/p4_mesh_manifest.json.
- Rerun: `PYTHONPATH=src /opt/hv/bin/python tools/sib/handed/p4orient.py OUT.json logs/sib/handed/p4/ct_occupancy_p4_2p4.json logs/sib/handed/p4/ct_occupancy_p4_1p129.json`. This needs the meshes under /work/handed/s3/PHercParis4 (fetch_meshes.py) and the metadata under /work/handed/meta/p4.
- handcheck (DECL-PP-1): DONE at tools/sib/handed/handcheck/ (REPORT section 17; ASK "handcheck packaging").
  - Scrub PASS: logs/sib/handed/pp/scrub.json.
  - Tests: 112 passed, 1 skipped.
  - Validation: 32/32 unmirrored, and the wrong-sign control mirrored 32/32.
  - PHerc1447: 11 of 15 flagged, double-checked.
  - Rerun the tests: `cd tools/sib/handed/handcheck && PYTHONPATH=. python -m pytest -q tests`.
  - Rerun the scrub: `python tools/sib/handed/pp_scrub.py tools/sib/handed/handcheck OUT.json`.
