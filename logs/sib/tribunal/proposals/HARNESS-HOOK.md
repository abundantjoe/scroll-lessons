Provenance: Project HERCULES | owner the owner | [id removed]

# HARNESS-HOOK: prepared as a patch on branch `claude/gifted-bell-gavnl5-sib-tribunal`

Per the orchestrator's decision of 2026-09-25 19:04Z (item 4), this patch is NOT for merge before
D3-VERDICT. Harness code is hash-pinned (METRIC-HASH-17), and D3's 24 sealed reads use the current
harness. The orchestrator merges and re-hashes after D3-VERDICT.

## What the patch contains

1. **Package.** `src/hercules/tribunal/` holds preread, faults, synth, runner, controls, manifest,
   validity, empnull and wiring. It was moved from `tools/sib/tribunal/tribunal/` with git history kept.
2. **The single call** in `src/hercules/harness/jobs.py`, `make()`, first statement:

   ```python
   from hercules.tribunal.wiring import assert_images_certified
   TRIBUNAL_CERTS = "/work/tribunal_certs"
   ...
   def make(role, task_text, images):
       assert_images_certified(images, TRIBUNAL_CERTS)  # TRIBUNAL: no read without a passed pre-read gate
   ```

   `make()` raises `TribunalFault` before writing anything if any image's CURRENT bytes lack a
   certificate. Certificates come from a PASSED pre-read gate (`certify_window`, which refuses a failed
   gate) or from the control builders (`certify_controls`).
3. **Tests.** `tests/test_tribunal_*.py` (7 files, 110 tests) are collected by plain `pytest -q`.
   `test_tribunal_wiring.py::test_harness_make_refuses_uncertified_images` exercises the hook itself.
   Full suite on the branch: 701 passed, 0 skipped, with the official renderer present
   (`logs/sib/tribunal/out/pytest_all_v4.log`).

## Consequences for existing callers (to handle at merge)

- `tools/d1/d1_jobs.py`, `d3_jobs.py` and `jseal_jobs.py` call `make()`. After the merge, they need
  certificates for their images. Past runs are not affected.
- Display builders must call `preread_gate`, then `certify_window` for each window's PNGs. Control
  builders must call `certify_controls`.
- Batch scoring: `validity.score_batch` per batch and `validity.i16_status` over the run, before any
  decision uses a batch.
