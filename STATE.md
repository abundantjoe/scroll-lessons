# STATE.md (current truth)

Provenance: Project HERCULES | owner the owner | [id removed]

Updated: 2026-09-25 ~18:10Z (day 1).

## Headline
No submission ready. 0 firm letters on any eligible volume. The binding constraint is now reader legibility: blind LLM readers do not agree on letters even in the official high-resolution reference ink maps of known text (PROBE1-RESULT). PROBE-3 replicated the key-sheet result on fresh papyrus (w044: 10 agreed letters, p 0.0005, 0 firm), so letter-reading decisions resume for display K_D2 (key sheet + D2) with the fable reader only. SG-FEAS is still NOT PASSED: readers never agree on firm letters, agreement is insensitive to mirroring, and agreed letters are mostly simple shapes (O, I, T). All three probe verdicts were independently re-derived by an auditor (AUDIT-PROBES: PASS). D1 = FAIL (D1-VERDICT, audited PASS 4/4): the calibrated readers recover 80 % of the J seal from the official 2.4 um reference maps of unseen 0841, but name nothing at all in our 9 um base or RAW maps of the same windows (0 of 180 panels), while they do see letters in base maps of base-trained 0139 papyrus. Our 9 um zero-shot chain does not make unseen letters legible.

## Verified results (RULES.md IDs)
- 9 um chain: official render reproduces organizer SVs (Pearson 0.99999 on 4 crops, 2 segments). Base with --tta-mirror FAILED C3 (C3-R1-VERDICT, forward 0.978 < 0.987); base without TTA PASSED on fresh w044 (C3-NT-R1-VERDICT: 0.99960 / 0.58558). C2-NT is the validated 9 um base-map chain.
- Harness: sealed-output mode (agents write age-encrypted answers; audit voids any other tool call); 1068 px image cap (HARNESS-COORD, HARNESS-SEALED-TEST).
- Reference legibility: READ-CAL picker 0-4 letters per window, 0 firm, 0 of 33 windows qualify (RCPICK-1); J picker 15 letters, 3 firm over J1-J5 (JPICK-1); PROBE-1 max 4 agreed letters per window, 0 agreed-firm, no window beats the shuffle null, native resolution names nothing (PROBE1-RESULT); PROBE-2 with a font key sheet, same windows: best cell 5 agreed (A_fable w039, shuffle p 0.031), 0 agreed-firm anywhere, mirror states A 15 : B 6 agreed (PROBE2-RESULT); PROBE-3 on 3 fresh w040/w044 windows: primary arm A_fable 10 agreed at w044 (p 0.0005), all four arms significant there in both mirror states, 0 firm in the primary arm, mirror A 19 : B 18 (PROBE3-RESULT).
- Handedness (0139): AMBIGUOUS three times (HANDED-1, -R2, -R3B); pooled decided votes A 12 : B 14: readers cannot tell mirrored reference maps from normal ones.
- Prize: rules unchanged, 23 eligible volumes, no award; 0826 publicly attempted by an outside team (D0-PRIZE-CHECK).

## Open decisions (date / default / status)
| Decision | Date | Default | Status |
|---|---|---|---|
| READ-CAL + SG-FEAS | 2026-09-30 | D2, P, strongest model; SG-FEAS not passed | FROZEN (READCAL-FREEZE): D* = K_D2, P* k_d2_task.txt, reader fable; SG-FEAS NOT PASSED |
| D1 KTLB-3R | 2026-10-03 | FAIL | DONE: FAIL (D1-VERDICT; REF not VOID, sigma_crit 0.30 mm; all model arms 0 namings); J decisions used 1 of 3 |
| DECL-HECATE screen | before first D1 model read | screened out | DONE: screened out at AUC 0.678 (HECATE-SCREEN); base 0.634 on the same 0.066 cm^2 |
| FACTORY v1, GATE-E2E-0139, 0841 registration, T0 | 2026-10-07 | not passed | not started |
| T1, T2 | 2026-10-09 | not passed | not started |
| CHAIN VALID, a* | 2026-10-10 | not passed / undefined | not started |
| D3, D4 | 2026-10-17 | not passed | D3 RUNNING: CTRL, FA, NULLA trained (model_final 6b690dda / 123ab62a / 0225b7d8); CTRL and FA maps done; NULLA inference running (1 thread); REVA training at step ~950/2000 at 18:02Z (ETA ~19:02Z), then REVA inference (~1 h at 3 threads). Then d3_build --full, stage-2 record (tools/d3/d3_stage2_record.py), 24 sealed reads of the frozen reader, score, audit workflow, D3-VERDICT (target ~22:00-23:00Z 2026-09-25). D4 INFEASIBLE on current material (no 2 x 2 cm 0841 window outside the T shell; needs own traces); Route F therefore blocked |
| D-M1, T-RESCAN | 2026-10-24 | cut-off / unresolved | not started |
| D2 TRAIN-1 | GPU + 6 days; NOT RUN if no GPU by 2026-11-15 | not-passed for K1 | blocked: no GPU |

## Kill-criteria clock
K1 JULY (DECL-KILL): D1 not PASS = TRUE (D1-VERDICT); D2 NOT RUN = expected at 2026-11-15 unless a GPU appears; D3 not passed = open (training; verdict expected ~2026-09-26). K1 triggers when all three hold; it closes JULY letter reading with current models and Route F, while RAW presence reading and DEV-LOOP continue.
K1 JULY triggers if D1 is not PASS, D2 FAIL/ALARM/NOT RUN and D3 not passed (on current evidence all three are likely). K2 2026-10-15; MAY cut-off 2026-10-31; early watch 2026-11-15; K3 2026-12-31; GP review 2027-01-15; K4 2027-02-28 / 2027-05-15; deadline 2027-06-25 23:59 Pacific.

## Top blockers
1. Reader chain: our 9 um base/RAW maps of unseen 0841 are not legible at all (D1-VERDICT: 0 namings), although the same readers read the official 2.4 um reference maps (80 % seal recall). A better 9 um reader needs training (D2/DEV-LOOP) and therefore a GPU; CPU allows only the small D3 fine-tunes.
1b. SG firm bar: readers rarely mark letters firm (PROBE series 0 agreed-firm; J seal 9 firm of 20).
2. No GPU: D2 and DEV-LOOP cannot run.
3. Disk ~4.4 GB free (D3 needs < 1.5 GB): no full normal-grid sync; census limited.
4. Ephemeral container: seal key (/srv/scorer), /work caches and sealed answers are lost when the container is reclaimed; everything decision-relevant is committed as records and hashes.

## Cumulative usage (to 2026-09-25 11:00Z)
GPU-h 0. CPU: ~14 core-h (builds, C3 and D1 renders and inference, Hecate screen, bank building, KD-tree work, D3 counts, D3 pools, smoke tests; D3 training running at 3 threads). Reader/blind agents: 3 harness tests, 6 pickers (1 stopped), 3 J sealers, 18 handedness readers, 36 PROBE-1, 12 PROBE-2, 12 PROBE-3, 12 D1-REF and 18 D1 model-arm readers (+6 CHANCE agents that died before any tool call). Builder/auditor agents: ~45 (incl. two audit workflows).

## Owner sitting list (nothing waits on it)
- Optional: a persistent secret for the scorer seal key (cloud environment secret), so seals survive container restarts.
- Optional: a GPU would unblock D2 and DEV-LOOP.

## Next 3 actions
1. D3 stage 2 back-to-back after REVA inference (v7 section 3.1): build, stage-2 record committed before jobs, 24 readers, score, audit, D3-VERDICT.
2. P4 (DECL-P4-1): reconnaissance agent running (logs/p4/recon.json); then DECL-P4-2 before any title-region map; P4-A after the D3 maps.
3. HRV-1 (DECL-HRV-1): builder relaunched (RAW overviews, then nice-10 ink queue); batches go to the owner as they appear. Watch agent checking for new official checkpoints and eligible-volume segments (logs/watch/).
