# Progress Prize submission sheet (September 2026 round)
Provenance: Project HERCULES | owner the owner | [id removed]

**Form:** September 2026 Progress Prizes, https://docs.google.com/forms/d/e/1FAIpQLScNBMj25FMnphngRG1Ciryv_2_Mkdq2YPJOD9WqPfZExII2iQ/viewform
- Submit one form per tool (three in all). Do not use the Grand Prize, First Letters or Title forms.
- Deadline: 2026-09-30, 11:59 pm Pacific (2026-10-01 06:59 UTC). Submit as early as possible: the organizers favour early releases.

**Status (orchestrator fills this in):**
- READY = the public repo is pushed, the scrub is clean, the tests pass, the README has been reviewed and the numbers re-checked against it.
- **This form only accepts responses from a signed-in Google account.** The orchestrator's POST returned 401 Unauthorized at 01:33Z (DECL-PP-1-A3). The owner, signed in, submits every entry marked READY by pasting from this sheet (about 1 minute each).

| Tool | Public repo | Status |
|---|---|---|
| flatcheck | https://github.com/abundantjoe/flatcheck | SUBMITTED by the owner (~01:40Z). Verified READY (public 948a19d; clean-clone install; 21/21 tests; citation, licences, credits and AI line verified; no leaks; numbers checked against the README; 01:33Z) |
| tifxyz-dist | https://github.com/abundantjoe/tifxyz-dist | READY (public dfaa71a; clean-clone install; 25/25 tests; citation, licences, credits (including the July tool) and AI line verified; no leaks; text aligned to the README; 02:36Z) |
| handcheck | https://github.com/abundantjoe/handcheck | READY (public eb986cc; clean-clone install; 94 passed 1 skipped; citation, licences, credits and AI line verified; no leaks; text aligned to the README; 02:13Z) |

**Fields, the same for all three:**
- Email: yours.
- Your full name: yours.
- Team description: `Individual. Built with the help of AI coding agents (Claude Code); all code, tests and numbers are in the linked repository.`
- Discord display name: yours, if you have one (optional; it helps the "gets used" criterion).
- URL: the repo link in the table above.
- What is your contribution?: the text for that tool below, pasted as-is.
- Terms and Conditions: "Yes, I agree".

---
## 1. flatcheck: contribution text
flatcheck checks tifxyz surface flattenings for distortion, fold-overs and collapse, and re-flattens with SLIM or ARAP, before anyone renders or reads them.

(1) Scroll data: public organizer meshes of PHerc0139 (volume 20250728140407, 9.362 µm, 38 meshes; 2.399 µm meshes for a cross-check) and small meshes of PHerc0800 and PHerc1447 (8.64 µm), from the open-data bucket (Vesuvius Challenge - CT Scans of Herculaneum Papyri, Angelotti et al.). It uses mesh geometry only.

(2) Every milestone prize asks for "a low-distortion isometric 2D parametrization", but there has been no standard per-quad test for it. flatcheck reports, per mesh or per window:
- the % of quads whose edges keep their 3-D length within ±5 %;
- fold-overs;
- area and angle distortion;
- a collapse flag.
It also measures intrinsic curvature, which no flattening can remove, and repairs with flip-free SLIM. Entrants see, before rendering, where letters will be stretched or folded.

(3) Failure cases of existing methods on real scroll data:
- On the 10 hardest 4 cm² windows of the PHerc0139 meshes, the official ABF++ (vc_flatten) meets the 93.1 % reference bar in 0/10, SLIM in 3/10 and ARAP in 4/10. SLIM and ARAP beat ABF++ in all 10 windows, by 2.9-55.3 points.
- ABF++ can collapse: 22.2-33.9 % of quads within ±5 %, UVs rescaled ×2.58-3.36, up to 12 fold-overs. SLIM never collapsed.
- SLIM ≥ ABF++ in 33 of 33 comparisons.
- Reproducible in this repo:
  - the distributed grid flattening of three whole meshes scores 90.1-92.9 %;
  - SLIM and ARAP improve all 9 of the most-curved windows, by 5.1-18.1 points;
  - ARAP folds over in 4 of those 9 windows, SLIM in none.

(4) Evidence: 21 passing tests on synthetic surfaces with known geometry (cylinder, sphere, Gauss-Bonnet), scripts/reproduce.sh (about 2 min; it regenerates the results table exactly), per-window tables with segment IDs and mesh sha256s, and a CLI plus Python API. Code MIT; results CC BY-NC 4.0.
---
## 2. tifxyz-dist: contribution text
tifxyz-dist computes exact, certified distances between tifxyz surfaces and point sets or other meshes. Its main use is the train/prediction overlap check that every milestone prize requires.

(1) Scroll data: public PHerc0172 (Scroll 5) segments traced on volume 20241024131838 (7.91 µm), 53 segments, mesh coordinates only (Vesuvius Challenge - CT Scans of Herculaneum Papyri, Angelotti et al.).

(2) If an ink model is scored on a surface that lies on, or within a few voxels of, a training surface, the result is not independent evidence of ink. Nearest-vertex checks are unreliable:
- on a 20-voxel grid, a point 1 voxel above the sheet can read 13.1 voxels away;
- two sheets 1.0 voxel apart edge-to-edge can have every vertex at least 5.1 voxels away.
tifxyz-dist gives:
- exact point-to-surface distances;
- a proven [lower, upper] interval for surface-to-surface clearance, with a witness point;
- a PASS/FAIL certificate at a chosen margin.
An entrant can state the clearance of a candidate region from every training segment, and the team can re-check it with one command.

(3) What it enables, shown on real data:
- Certified clearance for 243 of the 396 manual × auto-grown PHerc0172 segment pairs. At a 20-voxel (158 µm) margin: 225 PASS, 18 FAIL, 0 inconclusive, without refinement.
- Manual segment w078 touches or crosses all 9 auto-grown segments (0.02-1.1 µm). They must never be split across training and prediction.
- A mesh-hygiene finding: stray vertices in w066 create apparent contacts.
- Compared with the July 2026 intersection tool (Josep Carrera), it adds proven distances, not only contact, plus point-set distances and a margin certificate.

(4) Evidence:
- 25 unit tests pass.
- The triangle kernel matches an independent implementation to 2.1e-14.
- Pruning matches brute force exactly on 4,000 queries.
- 100,000 points sampled on a real 385k-quad segment return at most 2.7e-12 voxel.
- The demo scripts regenerate the results table.
- Code MIT; results CC BY-NC 4.0.
---
## 3. handcheck: contribution text
handcheck predicts, before any rendering, whether a tifxyz mesh render will read mirrored (and which way is up), from mesh geometry and catalogue metadata. It also says why it cannot decide when that is the case.

(1) Scroll data: public organizer meshes and catalogue metadata for PHerc0139 (38 meshes, 9.362 µm), PHerc0800 (6), PHerc1447 (15) and PHerc0009B (18 fragment meshes, 8.64 µm), with level-4 masked CT used for a frame check (Vesuvius Challenge - CT Scans of Herculaneum Papyri, Angelotti et al.).

(2) A mirrored render sends mirror-image letters into ink detection and reading. On a new scroll with no known text, looking at the render does not settle it.
- handcheck multiplies the mesh chirality, sign(det[dP/du, dP/dv, r_out]), by the frame parity from the catalogue.
- It cross-checks independent centre sources (official umbilicus, CT-mask centroid, the mesh's normal-line centre).
- A frame check confirms that the mesh actually lies on the scroll in the volume it declares.
- It returns the flips needed, a confidence level, and every reason for a flag.

(3) Actionable results on real data:
- 10 of the 15 PHerc1447 organizer meshes (the 2025-05-02 traces) are not on the scroll in the volume frame they declare: 41-91 % of their sampled vertices lie on masked-out CT, against at most 3.6 % for every PHerc0139 control. A handedness check without this frame test would have passed them. These are flags for the organizers to confirm, not established errors.
- Every decided organizer mesh reads unmirrored as stored: PHerc0139 38/38 (HIGH), PHerc0800 6/6, and the decided PHerc1447 and PHerc0009B meshes.
- An independent winding-sense check agrees with the catalogue's up/down flag on 36/36 PHerc0139 meshes.

(4) Evidence:
- 94 tests pass.
- Planted-glyph validation: 32/32 read unmirrored (min NCC 0.954, margin over the mirror image 0.262), and the wrong-sign control comes out mirrored 32/32.
- scripts/reproduce_official.py regenerates the per-mesh table from public data.
- A CLI and Python API are included. Code MIT; results CC BY-NC 4.0.
