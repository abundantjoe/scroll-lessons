Provenance: Project HERCULES | owner the owner | [id removed]

# pairs0814b report: PHerc0814 D2 training pairs, handed-over half

STATUS: DONE (2026-09-26T00:45Z)

Numbers and hashes only. No image, slice or map was opened, viewed or described.

## Segments (exactly the two in logs/sib/pairs0814/HANDOVER.md)

| Segment | 9 um valid cm^2 | candidates (>= 90 % valid both canvases) | blocks | PASS | fail NCC only | fail align only | fail both | RENDER_FAILED |
|---|---|---|---|---|---|---|---|---|
| 20250928235953-auto_grown_20250928235953722 | 81.39 | 304 | 71 | 140 | 17 | 28 | 119 | 0 |
| 20250926051122-auto_grown_20250926051122829 | 74.88 | 241 | 65 | 95 | 19 | 20 | 107 | 0 |
| total | 156.27 | 545 | 136 | 235 (43.1 %) | 36 | 48 | 226 | 0 |

The gates are those of stage_b.py, unchanged:
* NCC: render slice 15 vs organizer 2.399 um SV slice 54 >= 0.8, at zero shift, over both-valid pixels.
* Alignment: >= 7 of the 3 x 3 windows of 128 px align. A window aligns when integer NCC over +-3 px plus
  parabolic refinement gives a shift with norm <= 1 px, and the window has >= 50 % both-valid pixels.
* PASS requires both gates. For every row, `passed` was re-derived from ncc0 and n_aligned, and all 545 agree.

For comparison, pairs0814's 412 registry rows on its branch have 149 PASS (36 %).

Labels over PASS patches (ref9 >= 150 ink, <= 100 blank, else or invalid ignored):

| Segment | ink px | blank px | ignored px |
|---|---|---|---|
| 20250928235953 | 2,991,172 | 16,263,538 | 1,389,130 |
| 20250926051122 | 2,569,477 | 10,414,605 | 1,024,238 |

## Validation

* **Stage A reproducibility.** Every field of both stage A JSONs, except the utc timestamp, is identical to
  pairs0814's own stage A outputs for these segments. This covers the fitted affine, the residuals and the normal
  distances. The ref9, cov9 and val9 array sha256 also match. So the canvas geometry and labels are bit-identical to
  pairs0814's. Affine fit residual p95 is 0.002 px9 for both segments, and the normal distance p95 is 0.0 vox9.
* **Inputs.**
  * Root metadata.json, decoded: sha256 8119d1c2..., the same as pairs0814's protocol_check.
  * 9.362 um volume metadata.json: sha256 7db0a497..., the same. stage_b.py asserts voxel 9.362 um from it.
  * The PHerc0814 landmark affine (20260309142202 -> 20250804134230) is identical to the one pairs0814 used.
* **Registry.** There are 545 rows (304 + 241), which equals the candidate counts, and there are 0 duplicate
  patch_ids. The key set is identical to the union of keys in pairs0814's GATED rows.
* **npz files.**
  * All 68 block files: the sha256 equals the `staged_sha256` in the registry.
  * Each file's patch_id set equals the registry rows that name it, for 235 patches in total.
  * Arrays: images uint8 (21, 384, 384) = render slices 5..25; ref9 and labels uint8 (384, 384); valid bool;
    xyz float32 (17, 17, 3).
  * The largest file is 33.6 MB. No `.tmp` files were left behind, and no file was 90 MB or larger.
* **Code.** The copy that was run (tools/sib/pairs0814/, local, not committed) was verified after the run against
  tools/sib/pairs0814b/SHA256SUMS. See the next section for the code sha256.

## Code sha256 (identical to what pairs0814 ran; copied unchanged into tools/sib/pairs0814b/)

| File | sha256 |
|---|---|
| stage_a.py | 418dd8719a40aa8b591127e04985b41c758911207c5ff03d1e0c65a377aa2063 |
| stage_b.py | 69358bd672fc7c2f78c2caa536426e8d6689709384b9bc8a0638d8e74d15e3e8 |
| stage_c.py | cc8aaa4ff0dc5d5bab268e9cf56f7a361ba360e02df1469205b606320c606e25 |
| runlog.sh | 94cd5403faea7313f275b32a08d0154a93c52c7983470094d66985b94e2676d6 |
| setup_env_sib.sh | 9345cd1dc4eaa939d04483341a7124cd01b4f519d932b2c46345e87859b0b8a1 |
| vc_build_sib.sh | c8a352b46162a15904751bf77a3755ea2c901326155e100e69680ddd8b683b58 |

The other copied files and their hashes are listed in tools/sib/pairs0814b/SHA256SUMS. The whole set hashes to
6310219e..., the same as the pairs0814 branch at 002bba5.

Note: after the copy, pairs0814 changed stage_b.py (commit 376701c; its sha256 is now 2274ea26...). The change adds
only `HANDED_OVER = {...}` and skips those two segments when the argument is `all`. This run used the explicit
segment id, which reaches the same code path, and none of the processing logic differs.

## Time

* Stage A: 20250928235953 took 9.0 min (19:42:31-19:51:31Z). 20250926051122 took 9.2 min (19:51:31-20:00:44Z).
* Stage B: 20250928235953 took 34.6 min (23:24:44-23:59:19Z). 20250926051122 took 31.1 min (23:59:19Z-00:30:23Z).
  Each segment finished in a single pass, with no resume needed.
* Time per block, as the sum of render wait, 2.4 um fetch and gate:

| Segment | blocks | median | mean | max | render wait (median) | 2.4 um fetch (median) | gate (median) |
|---|---|---|---|---|---|---|---|
| 20250928235953 | 71 | 29.2 s | 28.9 s | 52.5 s | 9.9 s | 9.0 s | 10.7 s |
| 20250926051122 | 65 | 29.6 s | 28.5 s | 45.4 s | 8.9 s | 9.6 s | 10.7 s |

  The official render of a 1552 px block with -n 31 takes 12-48 s. It runs one block ahead, in parallel with the
  current block's fetch and gate.
* The environment build took about 11 min: dockerd, the deps image, villa 41701aa and the vc_* tools (GCC Release,
  build rc=0 at 19:43Z). The vesuvius (hv-ink) install step fails because it requires Python 3.14. HANDOVER expected
  this, and neither stage uses it.

## lscpu

Intel(R) Xeon(R) Processor @ 2.10GHz, 4 CPUs (4 cores, 1 thread/core, 1 socket), AVX-512 + AMX-BF16, L2 8 MiB,
L3 260 MiB, KVM guest, 15 GB RAM, no GPU.

## Outputs on this branch

* logs/sib/pairs0814b/registry/<seg>.jsonl: registry rows, same schema as pairs0814, byte copies. Also
  <seg>.SEGMENT_DONE.json.
* logs/sib/pairs0814b/stage_a/<seg>.json: stage A outputs, byte copies.
* logs/sib/pairs0814b/runs.jsonl: byte copy of the code's run log. It has 140 rows: 2 stage A, 2 stage B and 136
  vc_render_tifxyz, all with exit_code 0.
* data/sib/pairs0814b/blockpairs/<seg>/<by>_<bx>.npz: stage B block files, unchanged. There are 37 + 31 = 68
  files, 622 MB in total, and each directory has a SHA256SUMS.
  They were pushed in batches of <= 500 MB. One batch was 452.7 MB, and the rest went in progress commits.
* tools/sib/pairs0814b/sync_push.sh: the only new script. It copies the outputs byte for byte and pushes them. It
  does not process data.

Not done here, per HANDOVER: stage C (base-papyrus and duplicate annotation under CORR-RETRACE-RULE, and packing into
20-patch shards). That is run over the union of both branches by whoever merges.

Deviation from ASK.md Q1: the run log is stored as runs.jsonl, not runs_code.jsonl. It is the code's own log,
unmodified, and it covers every run in this session.
