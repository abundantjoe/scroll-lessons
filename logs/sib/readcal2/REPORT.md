Provenance: Project HERCULES | owner the owner | [id removed]

# readcal2 REPORT (READCAL-2 builder)

STATUS: DONE

Builder only: no reader, picker or sealer ran; no image, rendered slice or map was opened, displayed or described;
no seal, key, scorer path or encrypted file was touched; nothing from PHerc0841 or an eligible scroll was fetched.
Official data only (s3://vesuvius-challenge-open-data, anonymous; HF scrollprize/ink_9um step-075000 sha256
e635558a...9cab; villa 41701aa); every download hashed in downloads.jsonl (257 objects). Every run is in runs.jsonl
(three container restarts killed jobs; each kill is logged and the job resumed from its caches).
Host: 4 vCPU Xeon 2.1 GHz with AMX (amx_bf16, amx_int8, amx_tile), 15 GB RAM, no GPU.

## Deliverables

| Item | Where | Validation (measured) |
|---|---|---|
| Declaration drafts | proposals/DECL-READCAL2.md, proposals/READCAL2-BANK-1.md | arms, metric, bars, guard rails, replication, default NO_GAIN; frozen D* untouched |
| Arms K_D2, EX, EXPL, MS, ROW, SIG2 | rc2lib.py, build_sheets.py, build_ref_windows.py, briefs/*_DRAFT.txt | 30 unit tests (tests/sib_readcal2_*_test.py) pass |
| Key sheet | rc2lib.keysheet | byte-exact regeneration of METRIC-HASH-12 (5da96bde...) |
| Exemplar / placebo sheets (0.15, 0.30, 0.45 mm) | sheets_manifest.json (build_sheets.py; PNGs rebuilt on demand) | two builds byte-identical; blob area within 1 % of each glyph; max blob-glyph IoU 0.54 (glyph-glyph up to 0.89); EX/EXPL mean 114.3/114.3; identical noise field per sigma |
| Noise model | noise_psd.json, noise_psd_2d.npz | C2-NT base maps of the 2 SEAL-J-D1 w053 blanks: mean 76.8, variance 501 u8^2; masked vs tile estimator median ratio 1.01 (0.91-1.08) |
| REF ladder / MS / ROW builders | rc2lib.ref_ladder_images, ms_images, row_letter_residuals | sigma-0 ladder equals hercules.display.builder path; blur second moment within 2 % of sigma; MS frames equal scorer DisplayMap convention |
| Bank candidates | candidates.json | 4016 text, 46 blank, 95-window picker tiling, 1125 held (RCPICK-1) |
| REF renders of the tiling | refwin_manifest.json (arrays /work/rc2/refwin/arrays, displays /work/rc2/refwin/img) | 78 PHerc0139 windows, 78 picker images (state A, K_D2); valid 0.899-1.000; no flips; 5 ambiguous-sign windows excluded from the picker; 17 PHerc0814 not built |
| Scoring glue | score_rc2.py | synthetic end-to-end on score_decision; D1 ladder reproduces sigma_crit 0.30 (discrete) / 0.35 mm (interpolated) |

## Findings that matter for the orchestrator

1. Same-papyrus check reproduces the record: w047 vs base w045 / w046 = 1.34e5 / 1.38e5 vox^2 (RCBANK-1: 1.39e5 /
   1.44e5). New: w053 has ~1250 vox^2 within 2 vox of base w039 (pixel-excluded with halo; no w053 window is SAME).
2. RCPICK-1 cannot be reconstructed from the record (rcpick1_reconstruction.json: 310 / 161 / 490 candidates vs
   recorded 251 / 165 / 1731), so all E0 papyrus is held fail-closed (ASK 1). The bank therefore comes from tier N
   (non-base neighbours of the clean controls, excluded from D2) and PHerc0814 unless the 33 windows are published.
3. The centre curve for state A reproduces PROBE-3's recorded ranges exactly (centre0139.json).
4. The reference mapping (declared +10 offset) leaves the last ~7 canvas px of each axis without source; those
   pixels count as uncovered.
5. Blank base maps are not white noise: 82 % of their power lies below 0.01 cycles/px (> 1 mm), and one blank has
   3.8 % of pixels >= 150 (ink-like false positives). The exemplar noise reproduces the spectrum, not the blobs.
6. The multi-scale arm's quadrants are 1068 px at full scale, so MS shows the same pixels at 106.8 px/mm; the
   letter heights in its brief (214-427 px) follow from that.

## Known limitations (disclosed)

- Noise maps came from the organizer SV (official infer centre-crops slices 6..22: centre 14 vs surface 13.5), not
  from the -n 31 render path of D1; a half-voxel shift.
- Exemplar glyphs are a modern font (DejaVu Serif Bold), sharper than the reference; EX teaches degradation, not
  ancient letter forms.
- PHerc0814 windows reach only coverage 0.75-0.90 (ribbons); their state-A build needs a 0814 centre curve (not built).
- ASK 1-6 still unanswered at report time; the report follows their defaults.
- HANDED-1 windows (1 x 1 cm) were treated as 2 x 2 cm squares in the used-window test (conservative).

## File hashes (sha256)

| File | sha256 |
|---|---|
| `logs/sib/readcal2/ASK.md` | `170af1a64efc19cfcfa432d477e144a24cabec427746d47fa3b7c5df0ec3b591` |
| `logs/sib/readcal2/STATUS.md` | `1420d361b2379347ac5371610737b0127861d90ab8b06efbb501ccbb35bb78a8` |
| `logs/sib/readcal2/candidates.json` | `8af0f04ec9bb0eb8392af214c12eb5fa7fe61be65855a593f9f65405d96edf4e` |
| `logs/sib/readcal2/centre0139.json` | `de8538e2f14773adc8897e1d08c471c512dce216266ccf90561cca91c627c7f8` |
| `logs/sib/readcal2/downloads.jsonl` | `921f853a3a26eba564c467b44007ab259c4a4ece3661e5316e61c66ebc586e0c` |
| `logs/sib/readcal2/noise_psd.json` | `3b2bb6d5ac58fdef0ad7646e9c792bf7ce93172dc5e7e667012e0ad5fc6667c1` |
| `logs/sib/readcal2/noise_psd_2d.npz` | `aeaef6deea44221bcb847c6044402c0dc6ab4a76a95daf85881a5fefad92b290` |
| `logs/sib/readcal2/proposals/DECL-READCAL2.md` | `6a58cc1e981acb64c7882dfe572c80450a7e8180d6860a80eaf863640e7c3b8c` |
| `logs/sib/readcal2/proposals/READCAL2-BANK-1.md` | `075de0637071b45665d661cfa57d47f74f4a2e5b1f3b7a87421293b9ad451992` |
| `logs/sib/readcal2/rcpick1_reconstruction.json` | `1ceacc90d1e2159078eebf549ab8f7b7ee6318065c63abd2bf3bc046d8c81164` |
| `logs/sib/readcal2/refwin_manifest.json` | `3bf01a5a43e3fd43b947fa08ad3468e3b09a4637653c00feb9a36b34a2b4722c` |
| `logs/sib/readcal2/sheets_manifest.json` | `7352545d99545fb49dbf0bc995da58264b579ce1961032ac856fac8e0521a174` |
| `tests/sib_readcal2_builders_test.py` | `6b0adbd43cd09cc677667fe313117c9f5a44a520b2bfb71b30911943a9e90363` |
| `tests/sib_readcal2_geom_test.py` | `9abaade78feb549ce8277c7a3395ecc14e9c04576f03c76ae85d19175ff64f3d` |
| `tests/sib_readcal2_score_test.py` | `79d3492d4114f773eb60d38148af51d047bd984bad96453f4a944fa4f3fcf8ab` |
| `tools/sib/readcal2/REPORT_body.md` | `7703a8e770c3639f42ae5e0294e73ec8ef8990da40d2e2cc3c1544aefb9cbd19` |
| `tools/sib/readcal2/briefs/ex_task_DRAFT.txt` | `2a65302d3bcaf233a7c8adbc3cba047ae3c8c94dd4d45e1b8655205bbef882bd` |
| `tools/sib/readcal2/briefs/ms_task_DRAFT.txt` | `f52aab5f59c3e02019b2cd68b1a45010cc90fe2ab4cf3c2330a0b348991943ef` |
| `tools/sib/readcal2/briefs/row_task_DRAFT.txt` | `196d857d2b010344df5ffc1643ef7137eaf5727429f92ffa1891e0541a4ec588` |
| `tools/sib/readcal2/build_ref_windows.py` | `6f85dc18df56a70083bbcdbb22518662cc443c7ab2192f2920f83a33b1e887e3` |
| `tools/sib/readcal2/build_sheets.py` | `2aed4755aa4b32acbe3aa1a30a14f71aa46639103733d90d48f54917bc80df0f` |
| `tools/sib/readcal2/cand.py` | `486d04241e7adf6a6c184fe49c1786250eb0b7ed401ad40c131d194e472e2aa7` |
| `tools/sib/readcal2/centre0139.py` | `3384fb080aec37d0f0f16eff9e92ec50dca0403dfd80d8bfe292ca9a7b5975c9` |
| `tools/sib/readcal2/fetch_all.py` | `a48a6e7c6861760ffe9246a68a5802ae8c0bd0319b929f5bca5bfc2cba6bf6ed` |
| `tools/sib/readcal2/geom.py` | `e2c0861e74bff411dd166faa75367e85d6d13b51a1c6d053927b49792dee9fd1` |
| `tools/sib/readcal2/noise_crop.py` | `29d684bfdcd0518d27d8514d23dcb89e27cf0314f7f5aaed601e8c6428e1e6bb` |
| `tools/sib/readcal2/noise_infer.sh` | `ffc677b49364b134071e7dd0c4c1283e47289af3ec1e652e624f729ea7112846` |
| `tools/sib/readcal2/noise_psd.py` | `c0d14b6f2ecc7d0ce4869f27252cceb0e969517b9da79168c2e3d282226c0743` |
| `tools/sib/readcal2/rc2lib.py` | `9c3a2ab9db4b5bf125f82ff56931baf0fd7258fbd72ee8b750b7306825b1578c` |
| `tools/sib/readcal2/runlog.sh` | `e7c033e89cc1f711395e9f953cd1f4e0910aba180c5d751419728230e6cfbb3b` |
| `tools/sib/readcal2/s3fetch.py` | `55bbf669291c39a4750dd8dfe5a6ef3705e34478b7369668999b41ff07ce1df7` |
| `tools/sib/readcal2/score_rc2.py` | `c615d3bcd26bc8bb02156c231ea71edfc5f941e1d152e235289293026d68bf08` |
| `tools/sib/readcal2/setup_ink_env.sh` | `0502c0d417f1ca21303d2ff489215bf5e593789ff0fb849ec4f6d55f7a44279f` |
| `tools/sib/readcal2/write_report.py` | `b7e8ca1f457c1c0c14f8e69f2872ee7817019308809a096b92a3537a274833eb` |
