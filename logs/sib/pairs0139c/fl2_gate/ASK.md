Provenance: Project HERCULES | [id removed]

# pairs0139c FL2 gate (DECL-FL-2 item 4): two blockers for the orchestrator / owner

## 1. Community material vs this session's integrity rules: RESOLVED by DECL-FL-2-E1 (02:13Z): DENSE withdrawn, no Nieuwlaar code or crop; official only
This session's standing integrity rules (its original tasking) say: official organizer data and checkpoints only
(s3 vesuvius-challenge-open-data, HF scrollprize, GitHub ScrollPrize/villa); community models, checkpoints, code and
claims are never used. The gate order asks for:
- the title-bar crop from huggingface.co/Nieuwlaar/ink9um-dense-native (crop_bounds.py, common0139.py): community code
  and claims;
- the DENSE arm (Nieuwlaar dense_native_016000): a community checkpoint.
DECL-FL-2 item 3 admits DENSE, but that conflicts with the rule above, and only the owner can resolve it. Until the
owner's own message resolves it, this session:
- does not read the Nieuwlaar repository (no coordinates or code taken from it);
- does not run the DENSE arm (step 4), even after DENSE_OK.json appears.

## 2. The official title material holds no 2 x 2 cm cell under the unchanged tiler
- Organizer title segment: 20260422000000-title_2026042222_zmid_flatboi. Its 9.362 um tifxyz grid is 1.67 cm tall
  (RULES.md READCAL bank attempt 1: "canvas 5360 x 1780 px = 1.67 cm tall: no 2 x 2 cm window fits").
- 3-D search, numbers only, 2026-10-01 ~02:15Z: none of the other 38 organizer PHerc0139 segments intersects the title
  segment's 9.362 um bounding box (+-50 vox). w030 (20260130000001-w030_202601301912) has no 9.362 um mesh and was not
  tested. So no larger official segment carries the title papyrus.
- The template's cmd_tiles (fl-pherc0257@54b29c96, "never change the tiling") keeps only whole 2 cm (2136 px) cells
  inside the canvas, so it will keep 0 cells. The numbers will be in STATUS.md once the run finishes.

## Running now (official data and checkpoint only)
tools/sib/pairs0139c/fl2_gate.sh (detached):
1. environment;
2. title tifxyz, sha256 recorded;
3. C2-NT render as in the template, voxel size from metadata.json;
4. official ink_9um step-075000, both directions, no TTA;
5. template cmd_tiles, unchanged, with the result recorded.
The predictions are kept in /work/fl2gate/infer, with sha256 pushed, so any tiling the orchestrator declares can be applied
without re-rendering.

## Decisions needed
(a) Is a gate tiling allowed for a < 2 cm tall strip? For example: 2 cm wide cells spanning the full 1.67 cm height,
    padded to 2 x 2 cm, valid >= 50 %. If so, declare it, and also whether eligible tiles must use the same tiling.
(b) Resolved by DECL-FL-2-E1.

Open: only (a). Under the unchanged template tiler, the gate has 0 tiles (see STATUS.md once the tiles step has run).

## 3. Disk blocker for the large held-out segments (02:25-03:22Z, numbers only)
- All 8 render attempts (w054, w055, w051, w057, twice each) failed with 'No space left on device'.
- Cause, measured (/work/fl2gate/disk.log): vc_render_tifxyz's persistent remote chunk cache (villa 41701aa
  RemoteCacheSettings.cpp: ~/.VC3D/remote_cache inside the container, SourceMirror encoding, no size cap) grows
  /work/docker from ~6 GB to ~30 GB, about 24 GB within ~7 min. That exhausts the session disk allowance at about 55 % of w054.
- Estimate from 128^3 source chunks within +-16 vox of each mesh, scaled to w054's measured rate:
  - w054-w059 and w051-w057: 37-40 GB of cache each;
  - w047, w048, w049: about 27 GB;
  - w023, w024, w025: 21-23 GB;
  - w050 (15.64 cm2): about 12 GB;
  - free: about 16 GB.
- Done now: w050 rendered alone (the only held-out segment estimated to fit). It is the gate material until a decision.
- Options (orchestrator/owner):
  - (i) more disk for this session;
  - (ii) an operational cache setting ([perf] remote_cache_delta3d=true in the VC3D settings ini; whether it is lossless is not verified);
  - (iii) render large segments in --crop pieces, which is a render-option change and needs a declaration.

- Result: w050 rendered and tiled (4 gate tiles in tiles_official/20260302000001-w050_2026030220/). Its measured cache peak was about 19 GB
  (/work/docker 5.0 -> 23.7 GB; free fell to 7.6 GB), above the 12 GB estimate. So w023, w024 and w025 (about 2x the chunks) will not fit either.
  No further held-out segment can be rendered in this session without option (i), (ii) or (iii).
