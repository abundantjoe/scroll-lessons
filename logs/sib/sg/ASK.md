Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (task sg): questions for the orchestrator, each with the default I am working on

Status (2026-09-26 18:5xZ): Q11 RESOLVED for the Title Prize (logs/sib/sg/p4kit/Q11.md). Earlier: Q1-Q4 ANSWERED (orchestrator, 2026-09-25T19:16:15Z: all four defaults accepted; write scope not widened; the orchestrator performs the merge). Q5-Q6 OPEN.

1. **Write scope for the merge layout.** The rulings ask for the code as `src/hercules/sg/` with tests `tests/test_sg_*.py`. My brief's INTEGRITY list says I write only under `logs/sib/sg/`, `tools/sib/sg/` and `tests/sib_sg_*.py`, and it says integrity rules are never broken. A later message cannot silently widen them.
   **Default:** I build the exact merge layout inside my area, at `tools/sib/sg/pkg/src/hercules/sg/` and `tools/sib/sg/pkg/tests/test_sg_*.py`. `tools/sib/sg/pkg/run_merged_tests.sh` copies it over a scratch copy of `src/` and `tests/` and runs a plain `pytest`, so the merged layout is tested byte for byte. The merge itself is one `cp -r` (commands in `pkg/MERGE.md`), done by you or by me on your explicit confirmation that the write scope is widened for this purpose.

2. **Which reads count for B13 (fresh readers) and B14 (model mix).** The ruling lists discovery, confirmation, +-1 slice, second lineage, re-trace and rotation.
   **Default (stricter):** I also include the SG 9 arm reads (NULL, REV and CTRL, each a separate read) and the SG 13 band sealers.
   Excluded by construction: the opposite-order namings (SG 3) and the batch blank/canary namings (SG 2). In the paired display these come from the same readers as the read they accompany, so they are not separate reads.

3. **B1 in the discovery calibration.** The rule applied to the >= 200 null tiles is the full discovery rule, now including max per-reader F_B <= 1. A stricter rule lets fewer null tiles pass, so the calibrated k can only be the same or lower than under the agreed-count-only rule. It is never below 5.
   **Default:** calibrate with exactly the rule that is applied to candidates (consistent FDR). The alternative, calibrating with the looser rule, would give a conservatively higher k.

4. **B7 n_eff floor when a crop meets label patches of different sizes.** The disc diameter d (and so n_eff) depends on the patch size.
   **Default:** the floor n_eff >= 30 must hold for every patch-size group the crop is compared with. Any group below the floor makes the crop not evaluable, and SG 7 FAILs.

## Added after the rulings were applied (commit 7c83418)

5. **B8 may reject genuine text (measured).** On 68 letter blobs from the official PHerc0139 human labels, only 75-78 % fall in 2-4 mm, whichever box side is used, against B8's >= 80 % bar. Details are in `proposals/PROPOSAL-SG-LINESPACING-1.md`, section 3.
   **Default:** B8 stays as ruled and coded. I have recorded the risk. Proposed validation: run SG 11 mechanically on REF reads of sealed known-text bank windows and record the pass rate.

6. **B9 alternative cannot be computed from the official labels.** The labels hold only 4-25 isolated letters per segment (68 distinct in total), which is not enough for row pitch or pitch CV.
   **Default:** the ">= 3 qualifying rows" rule stands. The measuring tool is validated and ready (`tools/sib/sg/label_spacing.py`, 6 known-answer tests). Should I apply it to the organizers' official 2.4 um ink predictions on clean 0139 windows? That is model output, not human labels, so it needs your approval. I will not do it without an answer.

## Added after the answers of 19:41Z (B8 revised; Q6 approved)

Q5 and Q6 are ANSWERED. B8 is revised to the median-only bar, with the fraction reported and no bar on it. Q6 is approved for calibration only.

7. **"Clean" 0139 segments versus "exclude any window in a sealed set".** The clean 0139 controls (w024, w047, w053, title region) are exactly the segments that host the sealed READ-CAL bank windows and the D1 blanks (w053). The window coordinates were kept under `/work`, which did not survive the container, so I cannot exclude only the sealed windows. Excluding those whole segments leaves no clean segment.
   **Default (running now; calibration only):** use the 18 PHerc0139 segments that appear in no RULES.md, STATE.md, LEDGER.md, METHOD.md, CHANGELOG.md, configs or logs record at all. They have no sealed, read, canary, clean-control, neighbour or C3 role; w042 is also excluded because a C3 audit mentions it.
   These segments are base-trained papyrus. That does not matter for line geometry used for calibration only, but they are **not** the "clean" set.
   The alternative is for you to supply the sealed-window coordinates on w024/w047/w053/title, so that the clean segments can be measured with those windows removed.
8. **Binarising the predictions.** The organizer predictions are probability maps (uint8).
   **Default:** ink = prediction >= 128 (p >= 0.5), at pyramid or downsampled level ~9.6 um. The rest of the method is identical to the human-label run: ink >= 2 % per tile, periodicity >= 0.3. Sensitivity is reported at thresholds 96 and 160.

## Submit-kit task (received 2026-09-25T19:45:53Z)

9. **Automatic filing conflicts with K7 and with my integrity rules.** The task says "a submission will be filed automatically when a candidate passes SG 0-14". But RULES.md DECL-KILL K7 and DECL-SG both say "no form unless SG 0-14 all pass **and the owner is present**". My brief also forbids logging in, accepting terms and handling credentials, and a Google Form submission may need a sign-in and always needs the owner's identity fields.
   **Default (what I build):** a generator that writes files only: the answer sheet, methodology, FL-14 mitigation, FL-15 table and disclosure block. It contains **no code that opens, fills or submits the form** or contacts any external service. Its output is headed "DRAFT - NOT SUBMITTED - K7: owner must be present to file". Identity, payment, tax and credential fields stay empty and are marked OWNER-ONLY. The generator refuses to produce anything but a draft unless the SG record says overall PASS. Even then the result is a draft for the owner.
   If full automation of the *filing* step is wanted, that needs a RULES.md declaration that amends K7. It should be done by the owner, not by a builder session.

10. **Package manifest for tests.** **Default:** use the factory sibling's DRY RUN package manifest from `origin/claude/gifted-bell-gavnl5-sib-factory` (read-only, `git show`) if it exists. Otherwise use a synthetic manifest stamped DRY RUN.

## sg-pkg2 (received 2026-09-26T00:42:29Z; Q9 and Q10 defaults accepted)

11. **The licence lineage of the current base reader is BLOCKS** (`logs/sib/sg/licence/lineage_base_ink9um.json`; public metadata only).
    - The ink_9um checkpoint is MIT: PERMITS-RELEASE.
    - The open-data bucket's LICENSE.txt (sha256 3711f963...) is **CC BY-NC 4.0**. The prize now requires open-sourcing "code, data, model weights and results", and the form's terms say "under a permissive license". Data, and arguably weights, derived from CC BY-NC CT cannot be relicensed permissively: BLOCKS.
    - The ink_9um training labels state no licence: UNVERIFIED.
    - This is almost certainly a question for the organizers, since it is their own data under their own rule, not a real obstacle. But it is the owner's to settle before any filing.
    - **Default:** the checker reports it as a pre-submission package item (never an SG bar), and the submit-kit checklist shows the lineage verdict. Proposed owner action: ask the organizers whether releasing derived data under the same CC BY-NC terms satisfies the open-source requirement.
