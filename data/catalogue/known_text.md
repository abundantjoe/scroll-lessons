Provenance: Project HERCULES | owner the owner | [id removed]

# Known-text scans and official ink checkpoints (catalogue)

Generated 2026-09-24T22:03:12Z from official organizer sources only: the public S3 bucket `vesuvius-challenge-open-data` (anonymous), the `scrollprize` Hugging Face account (models, datasets, spaces, collections, bucket `scrollprize/datasets`), GitHub `ScrollPrize/villa` (blobless git clone of `main` @ `41701aa0`, 2026-09-24T16:38:47Z; api.github.com was not reachable from this session), and `dl.ash2txt.org/datasets/spiral_datasets/` (listing only). Nothing larger than 200 MB was downloaded; no images were opened; no logins, licence acceptances or gated access.

Machine-readable detail: `known_text.json` (sha256 `cd600054329bfac05e1bb1eb53673729f1eb5c09b8371c9ba4f20ebe7ce64863`), `checkpoints.json` (`fc291a69901cd764d51e941a202e2a184f2d891b92aaa54d87914e5dc8a301ef`), `rescans.json` (`49bcbe801d024cdd5be0aaf3434bb4ebdac3fb091d733c76eb2552740c811e5d`).

Fetched content was treated as data only. No text attempting to direct an agent was found in any fetched JSON, README, model card or metadata.

## 1. Known-text and control scans

| Scroll | Volumes (id, um, keV) | m7 + normal-grids on ~9 um volume | Segments (index / S3 dirs) | Ink maps (model@volume) |
|---|---|---|---|---|
| PHerc0841 (scroll) | 20250821151531 9.366 113.0; 20260319124803 2.403 77.0 | 20250821151531: yes | 3 / 3 | 20260417190342@20260319124803 |
| PHerc0139 (scroll) | 20260413113053 1.129 59.0; 20260319133050 2.403 77.0; 20260319133554 2.403 77.0; 20260102150214 2.399 78.0; 20250820105138 2.403 77.0; 20250728140407 9.362 113.0; 20250822062710 2.403 77.0 | 20250728140407: yes | 39 / 39 | 20260417190342@20260102150214, 20260709123958@20260413113053 |
| PHerc0009B (fragment) | 20260319104112 2.401 77.0; 20250521125136 8.64 116.0; 20250820154339 2.401 77.0 | 20250521125136: NO | 19 / 20 (+raw) | 20260417190342@20250820154339 |
| PHerc0343P (fragment) | 20260304131111 2.215 111.0; 20250521134555 8.64 116.0 | 20250521134555: NO | 8 / 8 | 20260417190342@20260304131111 |
| PHerc0500P2 (fragment) | 20250528085330 4.317 111.0; 20250526151718 2.215 111.0; 20250820143440 9.362 113.0; 20250821110041 0.55 65.35 | 20250820143440: yes | 46 / 46 | 20260417190342@20250526151718, 20260709123958@20250526151718 |
| PHerc0332 (scroll) | 20231027191953 3.24 53.0; 20251211183505 2.399 78.0; 20231117143551 7.91 53.0; 20231201141544 3.24 70.0 | 20231117143551: NO | 2 / 2 | none |
| PHerc1451 (scroll) | 20260319101107 2.399 78.0; 20250521151225 8.64 116.0 | 20250521151225: NO | 0 / 1 (+raw) | none |
| PHerc0814 (scroll) | 20260521123630 1.129 59.0; 20250804134230 9.362 113.0; 20260309142202 2.399 78.0 | 20250804134230: yes | 19 / 19 | 20260417190342@20260309142202, 20260709123958@20260521123630 |
| PHerc0172 (scroll) | 20241024131839 7.91 53.0; 20241024131838 7.91 53.0 | 20241024131839: NO, 20241024131838: NO | 53 / 53 | 20250713185324@20241024131838, 20250713185324@20241024131839, 20251222202946@20241024131838, 20251222202946@20241024131839 |

### Verification against expected values

**PHerc0841**

- [VERIFIED] 9.366 um volume: expected `20250821151531`; observed 20250821151531-9.366um-1.2m-113keV-masked.zarr (scan 20250719115350, session 20250717)
- [VERIFIED] 2.403 um volume: expected `20260319124803`; observed 20260319124803-2.403um-0.2m-77keV-masked.zarr (scan 20250721195912, session 20250717)
- [DISCREPANCY (nuance)] transform.json: expected `none`; observed no transform.json in either volume zarr root (VERIFIED); HOWEVER the root metadata.json index carries a 3x4 affine 2.403->9.366 um fitted on 7 landmarks (and its inverse) and every segment has a 2.403 um tifxyz made with it
- [VERIFIED] organizer segments: expected `3 named`; observed 3, same IDs; third segment 20260221022814 files dated 2026-09-22
- [VERIFIED] ink map model: expected `20260417190342`; observed 20260417190342 new_canon_autoresearch_recipe (resnet3d-152-3d-decoder), on the 2.403 um render only; none on 9.366 um
- [NEW] ink labels: expected `(not stated)`; observed label_set 20260918 (inklabels/supervision/validation zarr) on 2.403 um for all 3 segments
- [VERIFIED] m7 + normal-grids on 9 um: expected `-`; observed yes: surface-m7-L0-th0.2 zarr + normal-grids (also L2 on 2.403 um)

**PHerc0139**

- [VERIFIED] 9.362 um volume: expected `20250728140407`; observed 20250728140407-9.362um-1.2m-113keV-masked.zarr
- [DISCREPANCY (39 vs 38)] segments: expected `38`; observed 39 in index and on S3; 38 rendered with ink maps; 1 (20260130000001-w030_202601301912) is mesh-only (obj+tifxyz, no renders, no ink)
- [VERIFIED] ink maps at 2.399 um: expected `yes`; observed 38 segments, model 20260417190342 on 20260102150214 (2.399 um); 37 also have 1.129 um maps (model 20260709123958 on 20260413113053)
- [INFO] segment frame: expected `-`; observed all 39 originate on 20260102150214 (2.399 um); 38 have 9.362 um surface volumes
- [NEW] ink labels: expected `-`; observed label_set 20260918: 8 segments on 2.399 um, 5 on 9.362 um (w035 w039 w040 w041 w044)
- [INFO] extra volumes: expected `-`; observed 2.403 um 20250820105138, 20250822062710, 20260319133050, 20260319133554; 2.399 um 20260102150214; 1.129 um 20260413113053

**PHerc0009B**

- [VERIFIED] 8.640 um volume: expected `20250521125136`; observed 20250521125136-8.640um-1.2m-116keV-masked.zarr (MAY session 20250506)
- [VERIFIED + extra volume] 2.401 um volume: expected `20250820154339`; observed 20250820154339-2.401um-0.3m-77keV-masked.zarr (July session), PLUS a second export of the same scan 20260319104112 (window -0.03..0.19, z-crop 4472-29111)
- [INFO] sample type: expected `-`; observed index sample type = fragment
- [INFO] m7 on 8.64 um: expected `-`; observed NO; m7 L2 + normal-grids only on 2.401 um 20260319104112

**PHerc0343P**

- [VERIFIED] 8.640 um volume: expected `20250521134555`; observed 20250521134555-8.640um-1.2m-116keV-masked.zarr (MAY session)
- [VERIFIED] 2.215 um volume: expected `20260304131111`; observed 20260304131111-2.215um-0.4m-111keV-masked.zarr (scan 20250512023932, session 20250506, IRIS_15, 0.03 s)
- [INFO] m7 on 8.64 um: expected `-`; observed NO; m7 L2 + normal-grids only on 2.215 um

**PHerc0841 segments (all files)**: see `known_text.json` -> scrolls.PHerc0841.segments.per_segment_files. Per segment: mesh/intermediate/tifxyz_original (x/y/z.tif ~124-153 KB each + meta.json), _original.obj (7.0-7.6 MB), _flattened.obj (12.8-13.9 MB), _normalized.obj (9.9-10.8 MB), tifxyz_normalized; mesh/<id>-on-20250821151531-9.366um.tifxyz (x/y/z 184-219 KB) and mesh/<id>-on-20260319124803-2.403um.tifxyz (x/y/z 2.8-3.3 MB); surface-volumes/9.366um-1.2m-113keV-volume-20250821151531.zarr (0.56-0.61 GB, 1237-1327 objects) and surface-volumes/2.403um-0.22m-77keV-volume-20260319124803.zarr (31.1-32.6 GB, 17438-18251 objects); ink-detection/PHerc0841-<id>-2.403um-...-20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif (23.3-25.7 MB) + ds8 jpg; ink-labels/2.403um-volume-20260319124803/20260918/{inklabels,supervision,validation}.zarr (88-262 KB each).

Registration files: per-volume `transform.json` exists for PHerc0139 (20250820105138, 20250822062710, 20260102150214, 20260413113053), PHerc0009B (20250521125136 -> 2.401 um), PHerc0343P (20250521134555 -> 2.215 um), PHerc0500P2 (4 volumes), PHerc0332 (20251211183505 -> DLS 7.91 um), PHerc0814 (1.129 um only). None for PHerc0841, PHerc1451, PHerc0172, PHerc1203, PHerc0846A. All landmark affines are also embedded in the root index (`samples.<id>.sample.properties.volume_transforms`, plus per-volume `properties.transforms`), including 0841 (7 landmarks) and 0814 2.399 -> 9.362 um (13 landmarks) which have no transform.json file.

### Protocol verdicts (JULY = session 20250717, 9.362 um, 113 keV, 1.2 m, 0.012 s, Paganin 1000, unsharp 4.0/1.2; MAY = session 20250506, 8.640 um, 116 keV, IRIS_15, 0.03 s)

- **PHerc0500P2**: JULY protocol MATCH (8/8) for 9.362 um scan 20250720125517 -> volume 20250820143440 (secondary fields Pco/Fixed_X1/GAGG_100um_reflective/half-acq/attenuators also identical to July eligible scans; tomo_N 6000 because it is a small fragment). No MAY-protocol scan: its May-session scans are 4.317 um/111 keV and 2.215 um/111 keV. Sample type: fragment.
- **PHerc0332**: matches NEITHER protocol. Only DLS 2023 scans (3.24 um 53/70 keV, 7.91 um 53 keV; hosted at data.aws.ash2txt.org, EduceLab Data License) and an ESRF Dec-2025 2.399 um/78 keV/0.22 m/0.013 s scan (volume 20251211183505; Paganin 1000, unsharp 4.0/1.2). No ~9 um BM18 volume.
- **PHerc1451**: MAY protocol MATCH (5/5) for 8.640 um scan 20250509145349 -> volume 20250521151225 (also Paganin 1000, unsharp 4.0/1.2, 1200.02 mm, Fixed_X1, GAGG_100_reflective, half-acq false, same attenuators). Plus Dec-2025 2.399 um volume 20260319101107. No registration between them. 0 indexed segments (17 unindexed raw tifxyz in segments/raw/).
- **PHerc0814**: JULY protocol MATCH (8/8) for 9.362 um scan 20250719170512 -> volume 20250804134230 (secondary fields identical to July eligible scans). Plus Dec-2025 2.399 um (20260309142202) and 1.129 um (20260521123630) volumes; 19 segments with ink maps on 2.399 and 1.129 um.

Field-by-field tables per scan are in `known_text.json` -> scrolls.<id>.protocol_comparison.

## 2. Rescans of eligible scrolls

Eligible list: villa `scrollprize.org/src/data/prizeEligibility.json` key `first-letters-2027` (23 volumes; sha256 `8935c2953fac2d3a635048218849b2f07f99a1d7a1476417a29e8e7a866b6f29`).

- [CONFIRMED] PHerc1203 20260319130212-2.403um-0.2m-77keV: volume 20260319130212-2.403um-0.2m-77keV-masked.zarr, scan 20250721080303 (session 20250717)
- [CONFIRMED] PHerc0846A 20260319102732: volume 20260319102732-2.403um-0.2m-77keV-masked.zarr, scan 20250721134414 (session 20250717)
- [NONE FOUND] other high-resolution rescans of eligible scrolls: the other 21 eligible scrolls have exactly one volume each (the eligible 8.640/9.362 um volume) in both the root index and S3 volumes/ listings
- PHerc0846A 20260319102732-2.403um-0.2m-77keV-masked.zarr: scan 20250721134414-2.403um-0.2m-77keV, 36.4 mm tall band (eligible 9.362 um volume 131.2 mm), m7 L2 + normal-grids present, registration to eligible volume: none (no transform.json, no index transform); segments: 0
- PHerc1203 20260319130212-2.403um-0.2m-77keV-masked.zarr: scan 20250721080303-2.403um-0.2m-77keV, 36.4 mm tall band (eligible 9.362 um volume 177.7 mm), m7 L2 + normal-grids present, registration to eligible volume: none (no transform.json, no index transform); segments: 0 indexed; 22 unindexed raw tifxyz in PHerc1203/segments/raw/ (frame UNVERIFIED)

## 3. Checkpoints

| Item | Repo / path | Bytes | sha256 (LFS oid) | Licence | Gated |
|---|---|---|---|---|---|
| a_ink_9um_hybrid_3d2d_seed42_step075000 | scrollprize/ink_9um / hybrid_3d2d-seed42/step-075000.pth | 138,360,039 | `e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab` | No LICENSE file in repo; model card YAML "license: mit" (repo tag license:mit) | not gated, public |
| b_ink_canonical_2um_r152_3ddec_v2_l5_epoch13 | scrollprize/ink_canonical_2um / r152_3ddec_v2_l5_epoch13.ckpt | 1,549,556,213 | `36dd0de84b7b7aa6590184192c7415466cd8a1ba7c1e59f42c6373846373c3e0` | No LICENSE file in repo; model card YAML "license: mit" and card text "MIT - released by the Vesuvius Challenge. Underlying tomographic data are distributed under CC BY-NC 4.0." | not gated, public |
| c_timesformer_scroll5_27112024 | scrollprize/timesformer_scroll5_27112024 / timesformer_scroll5_27112024_20241108111522_epoch=19.ckpt | 455,711,244 | `3c6b0b4d1b766a69cef2ba86b51574d91c71dded7fa4d9ec7435a1a95c61320f` | No LICENSE file in repo; model card YAML "license: mit" | not gated, public |
| NEWER: hecate | scrollprize/hecate / hecate_2.4um.pth | 522,656,918 | `fa2de3827ebd247ff2d33df1b6f899ea79d5269036cf16765997c62f0e9988c7` | MIT (LICENSE file) | not gated |
| NEWER: hecate | scrollprize/hecate / hecate_9.6um.pth | 522,576,086 | `809f4f10f7cb7afa19b4bee0f7d2ab31edd7e11b664f9f210cc9c17f22fcfe5d` | MIT (LICENSE file) | not gated |
| displacement | scrollprize/extrap_displacement_latest / extrap_displacement_latest.pth | 1,228,585,385 | `662f8065031480c8ee611a7fb7cb466a7e839b4b9d0b5d239d94fb82a1aedfbe` | NONE (no README, no LICENSE, no licence tag) | not gated |
| displacement | scrollprize/copy_displacement_latest / copy_displacement_latest.pth | 1,698,235,447 | `22cf4392f2f61e6a5548c7b68148e97fed4ee772abf4f842cc6b8d1ef3ca1370` | NONE (README has no licence; no LICENSE, no licence tag) | not gated |
| displacement | scrollprize/ps256_copy_baseline / ps256_copy_baseline.pth | 1,698,235,447 | `22cf4392f2f61e6a5548c7b68148e97fed4ee772abf4f842cc6b8d1ef3ca1370` | NONE | not gated |

**Newer than base step-075000 (decision trigger): YES.** `scrollprize/hecate` (commit 9cb86e50, 2026-09-15) releases experimental Hecate ink models for 9.6 um and 2.4 um inputs (distilled from ink_canonical_2um; 9.6 um model expects renders resampled to 9.6 um in all axes). Also new: official 9.362 um human ink labels (label_set 20260918) on S3 for 5 PHerc0139 segments. The S3 model registry does not list ink_9um or hecate.

**Displacement / neural tracing**: villa `vesuvius/src/vesuvius/neural_tracing/nets/models.py` maps sentinels `extrap_displacement_latest` and `copy_displacement_latest` to HF repos of the same names (snapshot_download); VC3D C++ uses the same sentinels. Both repos are public, not gated, with no licence anywhere on HF (UNVERIFIED licence; villa code itself is MIT). `ps256_copy_baseline.pth` has the identical sha256 to `copy_displacement_latest.pth`.

**ink_9um human labels** (hf://buckets/scrollprize/datasets/ink_9um (web: https://huggingface.co/buckets/scrollprize/datasets/tree/ink_9um)): 380,992 files, 33,362,621 bytes. aligned-scrollprizeorg-21slices: 24 segments, 51 zarr arrays, 27,590,175 bytes (pherc0139-w016, pherc0139-w017, pherc0139-w028, pherc0139-w029, pherc0139-w035, pherc0139-w039, pherc0139-w040, pherc0139-w041, pherc0139-w043, pherc0814-46527, pherc1667-w013, pherc1667-w018, pherc1667-w023, pherc1667-w028, pherc1667-w029, pherc1667-w031, phercparis4-w00, phercparis4-w01, phercparis4-w02, phercparis4-w03, phercparis4-w05, phercparis4-w06, phercparis4-w07, phercparis4-w09). native9-scrollprizeorg-21slices: 5 segments (w035, w039, w040, w041, w044), 10 zarr arrays, 5,761,707 bytes. Licence: no licence stated in the ink_9um README or bucket metadata (UNVERIFIED); HF model card of scrollprize/ink_9um is MIT.

## 4. Spiral tracks (dl.ash2txt.org/datasets/spiral_datasets/)

26 folders listed. Eligible volumes with tracks on the exact eligible volume id: **18 of 23** (PHerc0125, PHerc0175A, PHerc0175B, PHerc0191, PHerc0211, PHerc0257, PHerc0268, PHerc0306B, PHerc0343, PHerc0358, PHerc0483A, PHerc0483B, PHerc0490A, PHerc0490B, PHerc0800, PHerc0813, PHerc0826, PHerc0846A). Missing: PHerc0846B, PHerc1203, PHerc1218, PHerc1447, PHerc1545. Archive claim "20 of 23" is REFUTED; the 5-missing list is CONFIRMED. Non-eligible folders with tracks include PHerc0841 (both volumes), PHerc0139 (9.362 um), PHerc0814 (both), PHerc0500P2 (2), PHerc0009B, PHerc0343P, PHerc0332, PHercParis4 (not crawled).

## 5. Sources and sha256 of fetched JSON / metadata

| Source | sha256 |
|---|---|
| root_index (https://vesuvius-challenge-open-data.s3.amazonaws.com/metadata.json) | `8119d1c2d48b54f880c81bfd7ff9a51eb5edd166c9c06eac754abf15dba7e0ac` |
| root_index_min (https://vesuvius-challenge-open-data.s3.amazonaws.com/metadata.min.json) | `0eb7df954e66fe07efe7a3552236190baa31a513b02d79799fac0a3f7c2df63f` |
| bucket_licence (https://vesuvius-challenge-open-data.s3.amazonaws.com/LICENSE.txt) | `3711f963c05d0be80d53e5923308a6dee31b203da23435c9cfb7c7b6e4dd5e19` |
| prize_eligibility (https://raw.githubusercontent.com/ScrollPrize/villa/41701aa0eaa1aa765523db3f9f972b5830abf549/scrollprize.org/src/data/prizeEligibility.json) | `8935c2953fac2d3a635048218849b2f07f99a1d7a1476417a29e8e7a866b6f29` |
| hf_models_listing (https://huggingface.co/api/models?author=scrollprize&limit=500&full=true) | `de06d1d9eda27c0548e203800411a710ee6f5675f410efb09a690b200bafb1c5` |
| hf_datasets_listing (https://huggingface.co/api/datasets?author=scrollprize) | `410009e638c6cc1f309c35a5134b753f85d1f7d00f5dabde6d80d33aea52fb61` |
| hf_spaces_listing (https://huggingface.co/api/spaces?author=scrollprize) | `-` |
| hf_bucket_ink_9um_readme (hf://buckets/scrollprize/datasets/ink_9um/README.md) | `c9a88ff970594fcef3788eb588bb75dbbd0e6436f4812f89074e26c0d9fef7a5` |
| ash2txt_spiral_index (https://dl.ash2txt.org/datasets/spiral_datasets/) | `daf5e930367e9f992532b95705a18dcca3f974380c67a6787af4169a062981cf` |
| HF ink_9um README.md | `ef0f3cf3186e9d05c8816718c4024aeb356e27a8c02d7da1bacdee113c5ef273` |
| HF ink_canonical_2um README.md | `a9eaef931e8ada20f484700ba355ccc0f926126133623745ca883b8452badc0a` |
| HF ink_canonical_2um config.json | `19b38c27cf1a5e2bcbd8329ecf83ab5517c5b231426581cd0ea5a8e0da8ce6c4` |
| HF timesformer_scroll5_27112024 README.md | `6af52e1cf9ffe0d1c2e9fcef51a2b4637600243dd42d4813edf43311ea67537d` |
| HF hecate README.md | `17d7f029ffcff421dbf767c89e0e36a91f141fdfb5a647cc254e4c88cffabe9e` |
| HF hecate LICENSE | `85b6c05ee6c6c25c2808ad4396a6e8f1f739cf12369885cc29644b7eaade349b` |
| HF copy_displacement_latest README.md | `2ed51f4ca49869795923f9c16df0358d0fd9f6141388197fd8ac996329af7987` |
| HF collections listing | `4d57c48d1f67d154b59047c2c73018229d18d55dc211d4a98efdf280ba51eab8` |
| HF tree ink_9um | `4527ac966d40f1c58383547fa448b0d4e026e03a01a35757a2b0dfba8c4532f1` |
| HF tree ink_canonical_2um | `eb78df47ba2c1f1c7dc10854b8bbe7bc49aabe0fdb4dff0a737bafca0674849f` |
| HF tree timesformer_scroll5_27112024 | `4bb646647a3748a2f04c66b604413e566dead12bd25db4a7565819d450a1640b` |
| HF tree hecate | `cf8e60ea9e02e1caa4bf346933daa1687888e40330e3fcccfa28a6d1646d8ff0` |
| HF tree extrap_displacement_latest | `f092e3511bf6b676358d6c54fe0b606e07fb3cee8874a18951a5cc3f389522a4` |
| HF tree copy_displacement_latest | `c827fc22efdd8395c5d46baacdccac3f092bc942ed40a585bb5002d03f01356e` |
| villa neural_tracing/nets/models.py | `3600ec788bfa46b0d82a184761c41474f47dce4302f5bfa26e8ced02e6bd321a` |
| villa LICENSE | `87070eec603117b5365e2172999e81b08890aef91c1673383cf9779ee9c89976` |
| S3 PHerc0009B/LICENSE.txt (identical to bucket LICENSE.txt) | `3711f963c05d0be80d53e5923308a6dee31b203da23435c9cfb7c7b6e4dd5e19` |

Per-volume files in S3 volume zarr roots (metadata.json / transform.json / meta.json):

| S3 key | bytes | sha256 |
|---|---|---|
| PHerc0009B/volumes/20250521125136-8.640um-1.2m-116keV-masked.zarr/metadata.json | 7607 | `e8b7bb92af4f9e149dfc75bee7f605a217dcca12c039c90f7e31428c42d9a59b` |
| PHerc0009B/volumes/20250521125136-8.640um-1.2m-116keV-masked.zarr/transform.json | 1525 | `4f7dcc53e148e15ad6c259973c52c78beb47129c31a896ce7cae2a05fee594c4` |
| PHerc0009B/volumes/20250820154339-2.401um-0.3m-77keV-masked.zarr/metadata.json | 8543 | `31803d0e40550c239204533741c589ac7c4f86f814334e119ae2ea68be18d3e4` |
| PHerc0009B/volumes/20260319104112-2.401um-0.3m-77keV-masked.zarr/metadata.json | 8561 | `7adb915988ca27aaa821485f883d671019f76326fc558ab4f845bba34f4a182a` |
| PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/metadata.json | 8125 | `95917633ca11a1ddff2e6b7d66360c508f8158bbe05be277c8d51477befb5bae` |
| PHerc0139/volumes/20250820105138-2.403um-0.2m-77keV-masked.zarr/metadata.json | 8575 | `764827148721a930b707051d3bc1994693bc45a1b44b827b49ce6e8e28bb2fb4` |
| PHerc0139/volumes/20250820105138-2.403um-0.2m-77keV-masked.zarr/transform.json | 1854 | `3d5002e24e9503e4d384a97b9325c331d0768208cc86cacd6e141c05a9a05100` |
| PHerc0139/volumes/20250822062710-2.403um-0.2m-77keV-masked.zarr/metadata.json | 8576 | `5c08c9ca26db431644cbce466222ba00aeb6f17135cba809208ac30e3fb21ead` |
| PHerc0139/volumes/20250822062710-2.403um-0.2m-77keV-masked.zarr/transform.json | 1692 | `8060c77086d214bf781e041c9967eff0f0ba5d271d2043b90e4c759892b4ec36` |
| PHerc0139/volumes/20260102150214-2.399um-0.2m-78keV-masked.zarr/metadata.json | 8336 | `c788219f290b15ba7648eba2814964a887a895f5526fd5c027a5c8fae13b56bc` |
| PHerc0139/volumes/20260102150214-2.399um-0.2m-78keV-masked.zarr/transform.json | 2811 | `572e69e08b37d7a92b29f78559e9de3d62c436a0fe52aee8e0cb56db9df5b161` |
| PHerc0139/volumes/20260319133050-2.403um-0.2m-77keV-masked.zarr/metadata.json | 8592 | `f700578b28e5e67f4f87bc8e47c8928959fea6cf6598e28b66db97451d41b22b` |
| PHerc0139/volumes/20260319133554-2.403um-0.2m-77keV-masked.zarr/metadata.json | 8594 | `1181648213b2bb2c242a3ebbbdb025ece9fa7840d0b961c8676a6e25d79872eb` |
| PHerc0139/volumes/20260413113053-1.129um-0.2m-59keV-masked.zarr/metadata.json | 150295 | `e4cdee140e9d2759ec68fe0c611c6639c3d75f90580d5c2e75aff331ac28e2e0` |
| PHerc0139/volumes/20260413113053-1.129um-0.2m-59keV-masked.zarr/transform.json | 2477 | `f8a6fb72fcd7b41fb0642212c1750bd331c701af1607556e69f9cf632599cbd8` |
| PHerc0172/volumes/20241024131838-7.910um-53keV-masked.zarr/meta.json | 244 | `6201efd328d54ea67dadd8207b18cc985513c56c3f6f289ffc2e7549a49c2046` |
| PHerc0172/volumes/20241024131839-7.910um-53keV-masked.zarr/metadata.json | 668 | `9ce6a759a2463e474a241ed081f2cc1432320160ea7a6be0e6bd55714e625f2c` |
| PHerc0332/volumes/20251211183505-2.399um-0.2m-78keV-masked.zarr/metadata.json | 7514 | `56a9e8295721f9052c2f34b1f134112c99547404ab1b14486aacb409fb3424dc` |
| PHerc0332/volumes/20251211183505-2.399um-0.2m-78keV-masked.zarr/transform.json | 1500 | `98bd0e1e444139bd9c6c17b6bf582895b46ad0d467d49f2117e83f46885abc56` |
| PHerc0343P/volumes/20250521134555-8.640um-1.2m-116keV-masked.zarr/metadata.json | 7605 | `1091c911c7654b44facca9700453131b21c604391204f0081ec34f6aa7f9227d` |
| PHerc0343P/volumes/20250521134555-8.640um-1.2m-116keV-masked.zarr/transform.json | 1403 | `e111e9779bd621a927ac9595b68182d01493084bcfe709c731db5ccc70b84ee3` |
| PHerc0343P/volumes/20260304131111-2.215um-0.4m-111keV-masked.zarr/metadata.json | 7978 | `2d2f0dfa479c3bc1c987d4a85dba1da5cdfc4ce650a8f2bda389eab2bd00eb9a` |
| PHerc0500P2/volumes/20250526151718-2.215um-0.4m-111keV-masked.zarr/metadata.json | 7733 | `b2b4e120705d9facb2dde2a4857f0be37fb4dd94f278d7c985f28670005ce6d1` |
| PHerc0500P2/volumes/20250526151718-2.215um-0.4m-111keV-masked.zarr/transform.json | 1207 | `f6fc92a96286d00743a15cb37f4d6e53cee2d392723962c6d3fc6d30950a05f0` |
| PHerc0500P2/volumes/20250528085330-4.317um-1.2m-111keV-masked.zarr/metadata.json | 7648 | `7ed39c4dcc79aa5774a16ae0700f1260e67e833e2073c158f47d56d878034fa8` |
| PHerc0500P2/volumes/20250528085330-4.317um-1.2m-111keV-masked.zarr/transform.json | 1530 | `8ac69b883b45a20fccd4149848773a65afe3a0a2d2bcbeba1916875bed2058b8` |
| PHerc0500P2/volumes/20250820143440-9.362um-1.2m-113keV-masked.zarr/metadata.json | 8630 | `5c630cedf01c6f246bfeb544f377f227e5bb75fdd9200a45ab7f123e579ddb77` |
| PHerc0500P2/volumes/20250820143440-9.362um-1.2m-113keV-masked.zarr/transform.json | 1188 | `6faa3f5d20e808a54557f08730519aa0fe4d78245caf3ae7dd53a8f711b44505` |
| PHerc0500P2/volumes/20250821110041-0.500um-masked.zarr/transform.json | 1678 | `1178f7e00e7544c9df8903bccbf5062e1214dfd433636dff83f8ff84e91fca60` |
| PHerc0500P2/volumes/20250821110041-0.550um-0.1m-65keV-masked.zarr/transform.json | 1678 | `1178f7e00e7544c9df8903bccbf5062e1214dfd433636dff83f8ff84e91fca60` |
| PHerc0814/volumes/20250804134230-9.362um-1.2m-113keV-masked.zarr/metadata.json | 8446 | `7db0a497ed78165a17b681debacd40e6fadd99326aed8423b9e337007cad4b92` |
| PHerc0814/volumes/20260309142202-2.399um-0.2m-78keV-masked.zarr/metadata.json | 8350 | `e60e9aa8d084366983026fdf5e6a77e1e1f82f981dffef07c604bfed2099c979` |
| PHerc0814/volumes/20260521123630-1.129um-0.2m-59keV-masked.zarr/metadata.json | 59583 | `857270ad5dc8e912078fd510744d74ea8f5d6e5e2a81a9794629630952de4082` |
| PHerc0814/volumes/20260521123630-1.129um-0.2m-59keV-masked.zarr/transform.json | 2328 | `f5c16b8930082a6974c2c0e2d4b3df08d074f03a9fc1f9ff03aec3948e804493` |
| PHerc0841/volumes/20250821151531-9.366um-1.2m-113keV-masked.zarr/metadata.json | 8549 | `5189f91307b49a929cb6f4882553889ecd027454c235728eae567222a951ac2e` |
| PHerc0841/volumes/20260319124803-2.403um-0.2m-77keV-masked.zarr/metadata.json | 8584 | `b3bcec46fc460864a393a14b3a781115a83e5f7a631cb28ea947e0b0ac1f1d45` |
| PHerc0846A/volumes/20250728152254-9.362um-1.2m-113keV-masked.zarr/metadata.json | 8140 | `0d0d7f3f30f76fd88623ee6357541600d901c54b455880d1cc752ac368d97d00` |
| PHerc0846A/volumes/20260319102732-2.403um-0.2m-77keV-masked.zarr/metadata.json | 8570 | `a6805a556a76715c5e533fbc44184e947d717dab4044006bce94e268fb208de0` |
| PHerc1203/volumes/20250820131727-9.362um-1.2m-113keV-masked.zarr/metadata.json | 8531 | `092c709fb37b7248c2bbbbf8d0e1986cb2f690a4918860c2e4f19489fd807fd0` |
| PHerc1203/volumes/20260319130212-2.403um-0.2m-77keV-masked.zarr/metadata.json | 8557 | `1e8f0c743af88744da78c23175f96b152d392e67f825977bd1e88d9fee9e90d2` |
| PHerc1451/volumes/20250521151225-8.640um-1.2m-116keV-masked.zarr/metadata.json | 7608 | `ee5f24a566a792c2ce26f9ddad4d78086663042975dea74dea29ff54ad35c1e6` |
| PHerc1451/volumes/20260319101107-2.399um-0.2m-78keV-masked.zarr/metadata.json | 7514 | `ef349e2debbf9659976bd68e43ea7fefbb5f32aec53460ed8fb4f4e1b3a3c2e7` |

## UNVERIFIED items

- Licence of the extrap/copy displacement weights and of the ink_9um label bucket (none stated at source).
- Coordinate frame of the unindexed `segments/raw/` tifxyz folders (PHerc1203: 22, PHerc1451: 17, PHerc1447: 37; PHerc0009B raw/ holds 5 PNGs).
- PHercParis4 spiral folder contents (not crawled; not eligible).
- Anything on api.github.com (blocked by the session proxy); villa facts come from a git clone of main.

