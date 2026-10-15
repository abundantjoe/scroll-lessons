# rh-e1 ASK
Provenance: Project HERCULES | owner the owner | [id removed]

## ASK-1 (2026-09-26 ~17:50Z): M2a has no scan-coverage field; M2a batch held
- Builder ref origin/claude/gifted-bell-gavnl5-sib-p4-tiles-a @ e505001, logs/sib/p4-tiles-a/m2a/manifest.json:
  100 tiles with valid_fraction >= 0.5, but neither per-tile `stats.frac_mesh_points_outside_1129_volume`
  nor `frac_outside` exists (also absent from m2a/tile_census.jsonl).
- DECL-P4-4-A1 item 1 takes that fraction "from the builder manifest", and METRIC-HASH-27 norm_manifest.py --coverage
  treats a missing value as not eligible, so the declared command gives 0 eligible M2a tiles.
- Not done by rh-e1 (it would change the eligibility input, which the task forbids): using the E1 manifest's `frac_outside` for the
  same (r, c), since DECL-P4-5 item 1 says the grids are identical; computing the fraction from m2a/tile_points.npz.
- Needed: either p4-tiles-a adds the per-tile fraction to its m2a manifest, or the orchestrator declares which source to use.
  Until then no d_a / nd_a key, job or read exists. E1 proceeds independently.

### ASK-1 update (~17:58Z): builder added the field; the key name still misses the frozen tool
- p4-tiles-a 52bcf46 (17:45Z) added per-tile `frac_mesh_points_outside_1129_volume` at the TOP level of each tile
  (builder summary: 100 with >= 50 % valid, 60 read-eligible under A1, 40 excluded; 0 disagreements with the tiles-b E1 grid).
- METRIC-HASH-27 norm_manifest.py reads `stats.frac_mesh_points_outside_1129_volume`, falling back to top-level
  `frac_outside`, and never reads that name at top level. Dry run of the exact declared command into a scratch dir:
  {"eligible": 0, "skipped": {"mesh_valid": 0, "coverage": 100}}. Nothing was imported and no key was written.
- Either fix unblocks M2a with no rule change: (a) p4-tiles-a adds `frac_outside` (same value) or nests the field
  under `stats` in m2a/manifest.json; or (b) the orchestrator declares and hashes a norm_manifest.py that also reads the
  top-level name. rh-e1 edits neither the manifest nor the hashed tool. The d_a / nd_a / census_da batch stays held.

## ASK-2 (2026-09-26 ~18:05Z): rh_verify.py A5 rejects the declared partial last session of E1
- E1 has 60 census tiles, so METRIC-HASH-27 p4_jobs.py jobs builds 7 sessions of 8+1 and one of 4+1 (job 1e3a1314).
  METRIC-HASH-28 rh_verify.py A5 compares norm_brief(brief) == norm_brief(reference), and norm_brief keeps one
  '<IMG>' line per image, so a 5-image brief can never equal a 9-image reference. E2 (160 = 20 x 8) never hit this.
- rh-e1 dry run of the non-decrypting checks (A0-A5, B1, B2; B3 not run, no key here) against its own branch:
  A0 A1 A2 A3 A4 B1 B2 true; A5 false only because of 1e3a1314 (the other 7 briefs equal the reference exactly after
  normalisation; 1e3a1314 equals the same template with 5 image lines, audit VALID, prompt == brief).
- rh-e1 changes nothing and re-runs nothing. For the orchestrator: amend rh_verify so that A5 compares the brief with runs of
  <IMG> lines collapsed (image count checked instead against the job record and the n_census + n_null of the job),
  and re-hash it. E1 install waits on that.

### ASK-1 resolved (METRIC-HASH-29, f8f43c4). ASK-2 still open (~18:02Z)
- M2a ran with norm_manifest d2faee66: 60 eligible, 40 coverage-skipped. The M2a batch also has one 4+1 session (256397cc),
  so the METRIC-HASH-29 rh_verify.py (norm_brief unchanged) will fail A5 on it exactly as on E1 1e3a1314.
- rh-e1 non-decrypting dry run on both batches: A0 A1 A2 A3 A4 B1 B2 true; A5: 7 of 8 briefs equal the reference exactly,
  and the 8th equals it once runs of <IMG> lines are collapsed; every census and N0 tile is covered exactly once.

## ASK-3 (2026-09-26 ~21:40Z): how to import the L2S remainder (l2sb) without re-reading l2sa tiles
- l2sa (early batch, DECL-P4-12-A2 harness order) was built from the p4-l2 partial manifest AS COMMITTED at 6166973:
  41 tiles = all 40 eligible r0-r1 tiles + r2_c0 (the builder had already pushed r2_c0; its commit message says 40).
  norm_manifest.py imports every eligible tile in a manifest, and rh-e1 does not filter manifests, so r2_c0 is in l2sa.
  Commit A 69cfae2 lists the exact (r, c) set in L2S/A/builder_ref.json "tiles_rc".
- The full l2s manifest will list all 131 eligible tiles. Importing it as l2sb would re-read those 41 tiles.
  Options, none of which rh-e1 takes by itself:
  (a) p4-l2 pushes a remainder manifest (e.g. l2s/manifest_rest.json) listing only the tiles not in l2sa;
  (b) the orchestrator declares a norm_manifest option to exclude a (r, c) list;
  (c) the orchestrator declares that l2sb re-reads all 131 tiles (l2sa then counts as an extra read).
- Layout: l2sb will go under logs/sib/rh-e1/L2Sb/{A,B}. rh_verify A1 dates the first commit that adds <rh_dir>/A,
  so a second batch cannot share L2S/A.

### ASK-3 answered (orchestrator ruling 21:39Z; rh_verify --prior per METRIC-HASH-37, verified on 4385db3)
- l2sb = the FULL l2s manifest normalised into scratch, minus exactly the 41 l2sa (r, c) (L2S/A/builder_ref.json tiles_rc),
  then import / null nl2sb (from l2sb only) / jobs census_l2sb sigma2t, under L2Sb/{A,B}. Commit A records the removed list,
  the filtered manifest_norm sha256 and the full-manifest sha; builder_ref points to the FULL manifest.
- Precondition: the full manifest must list 160 eligible tiles (same set as L2). If fewer, wait for p4-l2's corrected manifest.

## ASK-4 (2026-09-27 ~02:25Z): DECL-P4-17-A1 null vs the frozen p4_jobs session rule (w1 batch held until answered)
- The rule: census = 14 windows (8 title-zone + 6 known-text controls) + (4,18) blank-end "descriptive null" (15 pushed);
  N0 = rot-90 copies of 6 of the 14 (seed 20260927); 8+1 sessions.
- p4_jobs.py (METRIC-HASH-38) jobs puts exactly ONE N0 per 8-tile session (zip of groups and nulls). 15 census windows
  give 2 sessions, so only 2 of 6 N0 would ever be read; 4 would sit unread and rh_verify A5 ("every N0 once") fails.
- p4_jobs null nw1 6 w1 draws from ALL rot-0 tiles of batch w1, i.e. from 15 windows incl. (4,18), not "6 of the 14".
- rh-e1 changes neither the tool nor the rule. Options for the orchestrator to declare:
  (a) null nw1 2 w1 (one N0 per session, the tool's rule) and record that the null is 2, not 6;
  (b) a p4_jobs option for k N0 per session (e.g. 8+3 / 7+3), hashed; or 3 sessions of 5+2 etc.;
  (c) import (4,18) as its own batch so the null pool is exactly the 14 (e.g. w1 = 14, w1x = (4,18) read in the same sessions only if the tool supports it).
- Until an answer arrives, rh-e1 builds nothing for w1 (no key, no job). The w1 tiles are polled.

## ASK-5 notes (2026-09-27 ~20:55Z; not blocking, P4-OWN G1 proceeds as ordered)
1. Block brief scale: the frozen block task text (METRIC-HASH-38) tells readers each item is "a 4 x 4 cm patch ... at
   26.7 px/mm". The OWN held-out tiles are 2 x 2 cm at 53.4 px/mm (same display as P4-O). census_own_*k readers will
   therefore get a wrong scale statement. rh-e1 builds it as ordered unless the orchestrator rules otherwise.
2. rh_verify A4 keys census tiles by (r, c) only. The OWN held-out manifest spans two segments and the F1 list has the same
   (r, c) in both (e.g. (2,1), (2,0)), so A4 against the full builder manifest needs a per-segment comparison for
   own_<fold>a (w028-037) / own_<fold>b (w010-027). rh-e1 records per-segment eligible (r, c) in split.json (commit A).
3. norm_manifest needs a top-level 'segment' and reads manifest + tiles from one git ref, so prep_own.sh splits the
   manifest per segment into a LOCAL commit (parent = own-lead ref; tiles are the builder's blobs, unchanged); its sha,
   the split manifests' sha256 and the original manifest sha256 go into commit A. Dry run on a synthetic noise manifest
   (scratch names zdry_x1*, removed afterwards): eligibility, keys, N0 ceil(n/8), two job sets, briefs == refs; arm
   mismatch rejected.
