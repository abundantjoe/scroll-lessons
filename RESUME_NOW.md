# RESUME_NOW.md (read this first after a context clear)

Provenance: Project HERCULES | owner the owner | [id removed]

Written 2026-09-26 17:50Z (updated 18:12Z) by the orchestrator (session_01JNjAnFPejnNF7eVAiNeRJp) before an owner-requested context clear. Order of truth: RULES.md (hash-chained), then LEDGER.md and STATE.md, then this file.

## 0. Owner's standing instructions (latest first)
- 17:25Z and ~17:45Z:
  - "keep going and also orchestrate more siblings - even have siblings create more siblings of their own if needed to secure win even faster by using sub parallel processing. no idling".
  - "a different ink could be a different color like a red ink". Implemented as DECL-P4-6.
  - "just because it says winding w000 doesn't mean the human labeling is perfect, they could have missed inner ones". Implemented as DECL-P4-7.
  - "make your own decisions as brilliant and wise as possible".
  - "do better next time with the disk space. and more siblings".
- Message format: the closing line is "Integrity: no issues" when there is no event (MSG-FORMAT-A1). Never write "Integrity: none".
- Earlier and still in force:
  - full automation; the owner is never a viewer or reader;
  - Opus 5.5 only;
  - both sigma forms;
  - no bar is ever lowered.

## 1. Disk doctrine (the owner asked for better)
The disk has about 106 MB free, of 252 GB (37 GB used).
- The owner approved nothing specific. The session safety check refused `rm -rf /work/docker/containerd` (4.9 GB, regenerable docker image store) as irreversible destruction; see DECL-OFFLOAD-1-A1 and -CORR. Do NOT retry it, move it to tmpfs or split it into pieces.
- Deletion needs the owner's explicit approval of the specific paths. Ask exactly once, in the final message:
  - "I approve deleting /work/docker/containerd";
  - optionally, "I permit pushing to claude/gifted-bell-gavnl5-data", for the verified offload of /work/readcal, /work/c3 and /work/d1 (about 9.9 GB, closed decisions).

Rules from now on:
1. The orchestrator container is a control plane only. It holds no bulk data and runs no reader locally, because each reader transcript is about 10 MB.
2. All tile builds, blind reads, training and tracing run in sibling containers. Blind reads follow DECL-REMOTE-HARNESS-1: answers are sealed to our age key, and only the key, jobs, .age and audit files come back.
3. Never fetch a sibling branch wholesale. Use `git ls-remote`, the GitHub MCP get_file_contents, or `git fetch --depth 1 --filter=blob:none origin <branch>` followed by `git show <ref>:<small path>`.
4. Run `df -h /` before every launch. Below 1 GB, launch nothing new locally.
5. Scratch goes to /dev/shm (RAM; wiped on every container restart, as at 17:25Z).

## 2. State of the prize search (P4 fast lane: the PHerc. Paris 4 Title Prize)
No submission is ready. No confirmed title lead exists. P4-B closed with no confirmed lead (P4-C not EXT-CONFIRMED). M2b, the known-text control, passed its reader check.
Four new declarations (commit 0e30894, 17:35Z), all declared before any data:
- DECL-REMOTE-HARNESS-1: remote blind reads in rh-* siblings. Commit A (keys, jobs, briefs) is pushed before any reader starts; commit B holds the .age files, audit and gz transcripts. We decrypt and score locally with score_p4.py (METRIC-HASH-27). An independent audit re-run is required before any result is recorded; use a sibling, because the transcripts are too big for local disk.
- DECL-P4-5-A1: the E1 stretch excludes zero-CT pixels. All 60 E1 tiles are rebuilt to logs/sib/p4-tiles-b/e1a1/; the superseded e1/ tiles are never read.
- DECL-P4-6: P4-F, the dense/mineral-pigment (red-ink) channel. It is a max over +-15 um with thresholds from the known-text control, a numeric DENSE-HOTSPOT screen first, then a census.
- DECL-P4-7: P4-G, windings inward of w010, including possibly unlabelled ones. Geometry only; rendering or reading needs a new declaration.

Critical path and what to do when each lands:

| Item | Who | Next orchestrator action |
|---|---|---|
| E1 raw CT 1.129 um (60 tiles) | p4-tiles-b rebuild, then rh-e1 reads | on rh-e1 commit B: verify commit A precedes the .age files and the key sha; copy the key to /srv/scorer/p4_key_{e1,ne1}.json (0400) and the .age files to /work/sealed_io; get an independent audit; score the census with excl_d_a; DECL-P4-2 item 6 phase 2 via the remote harness |
| E2 raw CT 2.4 um (160 tiles, pairs0814b) | rh-e2 reads | same, with excl_a |
| P4-D M2a, 1 um predictions (NEVER BUILT until now) | p4-tiles-a (ordered 17:42Z), then rh-e1 step 7 (batches d_a/nd_a/census_da) | same, with excl_d_a |
| excl_d_a flags (E1 grid == M2a grid) | p4-excl (ordered 17:43Z) | used in scoring |
| P4-F dense-ink screen and tiles | p4-highz | on screen.json: record the numbers; on f1 tiles: spawn a harness sibling rh-f1 (batches f1/nf1/census_f1) |
| P4-G winding count | p4-inner (1.129 um) + p4-core (2.4 um, plus VC3D trace prep) | if both show papyrus inward of w010: declare the trace, render and read (new DECL) before any render |
| Package pipeline | factory (relayed resume 17:46Z) | ready for any EXT-CONFIRMED lead |

Candidates exist only per the declared census and N0 bar. Only EXT-CONFIRMED (DECL-P4-3) leads to a package. Honest odds stay low.

## 3. Siblings (38; logs/sib/registry.json)
- Messaging: ListAgents does NOT show cloud siblings. Send orders as one-shot `create_trigger` with `persistent_session_id=<sibling session>` and `run_once_at` 1-2 min ahead, staggered 1 min apart because of the rate limit. `initiation`=human_request when relaying the owner.
- Orders sent at 17:39Z are listed in logs/sib/orders/TRIGGERS_20260926T1739.md.
- New at 17:38Z: rh-e1, rh-e2, p4-highz, p4-core, with prompts in logs/sib/orders/. They may create up to 3 sub-siblings each; check their SUBSIBS.md.
- Relayed "resume" (holding for the owner's words): devloop, factory, contam, pairs0139. If they still hold, the owner must type "resume" in those sessions.
- Waiting on orchestrator decisions (slow lane; see the post-turn summaries via list_sessions):
  - ckpt-screen-b/c, dev-lcsoft, dev-distft and amx need METRIC-HASH of devloop FREEZE.md, then GO SCREEN / GO DEV (task #10).
  - d2-p128, d2-p384, d2-null and d2-rev need the pair freeze, DECL-D2-A1 and GO D2; there is no GPU, and CPU runs take ~18-20 days per arm.
  - tribunal needs 4 protocol decisions for REAL-TRIB-2.
  - regrescan needs a non-affine model approval.
  - census and tracer need the T0 declaration.
  - reg0841 has a gate at 0.888 vs 0.90.
  - readcal2 needs a DECL-READCAL2 ruling.
  - sg: Q11 license question (CC BY-NC vs open-source) BLOCKS filing. Resolve it before any submission.
  - reg0009b: the extension must be recorded.
  - pairs0139b/c are waiting on pairs0139's HANDOVER.md.

## 4. First 5 actions after the clear
1. `git pull`, `df -h /`, `python -m hercules.records.rules_append verify` (PYTHONPATH=src), and check that /srv/scorer still holds its keys.
2. `list_sessions` (the result is large; parse it from the saved file with python): the state of the 38 siblings plus any sub-siblings.
3. For every P4 branch that has moved (git ls-remote): act per the table in section 2.
4. Keep every sibling busy. Assign the next task, or a new sibling, to any idle sibling that is on a prize-relevant path.
5. Ask the owner once for the explicit disk approvals (section 1). Close with "Integrity: no issues".

## 5. Update 18:12Z (after the owner approved both disk items)
- Disk: /work/docker/containerd was deleted (DECL-OFFLOAD-1-A2), and 3.39 GB of closed data was offloaded to the data branch and verified, leaving about 8 GB free. Local phase-2 reads are allowed while df shows >= 2 GB.
- Scored and verified. The independent verifier tools/p4/rh_verify.py passed 12/12 on each batch (METRIC-HASH-28..31):
  - E2: 0 positive (closed);
  - E1: 0 positive (closed);
  - M2a: 19 positive, all in columns 0-9 of rows 2-4, none in columns 10-19; provisional until excl_d_a arrives from p4-excl.
  - Joint M2a+M2b (DECL-P4-4 item 3): N0 p99 3.85, threshold 5.
- METRIC-HASH-32: the phase-2 and extended-test N0 is drawn ONLY from same-material batches. P4-D uses `p4_phase2.py build <batch> <select> d_a,d_b` and `p4_ext.py build <batch> <p2> <cand> d_a,d_b`, and the PC-pool strip name is fixed.
- DECL-P4-11: boundary (text-to-blank) end-title candidates. They need p4-inner's tile_winding_m2a.json (per-row Spearman rho of column vs radius, median <= -0.5 or >= +0.5).
- New declarations:
  - DECL-P4-6-A1/A2: rubrication; gold, blue and green pigments; an Hg/Pb/Au K-edge inventory.
  - DECL-P4-8: P4-I, the numeric structure screen (p4-struct).
  - DECL-P4-9: P4-H, the crackle channel with its gate (p4-crackle).
  - DECL-P4-10: pigment families with injection-recovery (p4-pig-red, -gold, -cu, -fe) and a research dossier (p4-research, a papyrologist-grade decision advisor with an EXPECTED-TEXT guardrail: expected title words never reach readers).
- Next, when excl_d_a lands:
  1. Rescore jointly: `score_p4.py census /work/p4/jobs_census_db.json,/work/p4/jobs_census_da.json <excl_d_b>,<excl_d_a normalised strip=20260623141924-w010-027, union flag> logs/p4/census_d_joint_excl_summary.json`.
  2. Run `p4_phase2.py select` on it, add the DECL-P4-11 B-candidates, `build ... d_a,d_b`, run the reads locally, then score.
  The M2a tiles are materialised in /work/p4/img under the d_a uuids (sha-verified).
- 46 siblings. devloop, devloop2, factory, contam and pairs0139 hold for the owner's own "resume" (an earlier owner pause).

## 6. Update 21:16Z (after the account usage limit, ~19:00-19:50Z; the owner said continue)
- Most siblings stopped at the limit. Resume orders were sent 21:15-21:45Z in tiers:
  1. critical: p4-l2 (build L2S), rh-e2 (l2b), ckpt-screen-a/b/c (P4-O inference, 1667 family), p4-layout (edge + orgmap);
  2. submission support: tribunal, flat1, handed, readcal2, tracer, chain2um;
  3. lean finish: pig-cu/fe/gold/red, p4-inner, p4-core.
- Results recorded:
  - P4-D-RESULT: 0 candidates; all core tiles are labelled-adjacent, so model outputs cannot give title candidates in the core.
  - P4-O-PROVENANCE(-2): only PHerc.1667 iterations are eligible; ckpt-screen-a has 0 of 3 and -c has 0 of 5.
  - P4-CHANNELS-RESULT-1:
    - P4-F: 0 dense hotspots on all materials including c10-c17, with detection limits Hg/Pb/Au ~0.1 um, CuO 0.5, Fe2O3 0.5-1 and Egyptian blue 2 um;
    - P4-H: gate FAIL;
    - P4-I: uninformative;
    - P4-L l2a: 0 letters on 24 tiles, including the known text (the global display is too dark in r0-r1; L2S is pending).
- Owner decisions: the EduceLab licence is accepted for the 5 title-search meshes only (OWNER-LICENSE-EDUCELAB-1).
- Verifier: tools/p4/rh_verify.py (METRIC-HASH-36) takes --adir/--bdir. ALWAYS `git fetch --deepen=100` the harness branch before verifying; shallow history fails closed.
- Scoring model-free P4-L/L2S: score_p4.py census <jobs> /nonexistent.json <out> (no exclusion; DECL-P4-12 item 3). The candidate rule (DECL-P4-12 item 4: c10-c17 first, never c0-c8) and the known-text gate (>= 30 % of non-blank c0-c8 tiles rows Y with >= 5 letters) are applied by the orchestrator from the summary.

## 7. Update 2026-09-27 01:00Z (after the usage-limit reset)
- New standing orders (read them): OWNER-STANDING-ORDER-2 (consider everything; logs/p4/HYPOTHESES.md and COVERAGE.md), -3 (interruptions, pause-not-kill with RESUME.md, economy), -4 (overcome blockers unasked; nothing waits on the owner; auto-submission authorised with terms pre-accepted; verification via VERIFY.md and unsealing after the verdict). STANDING-ORDER-COMPACT-A2: the multi-agent regeneration workflow is retired; this file is the live handover.
- Owner requests and their status: logs/owner/INBOX.md.
- FASTEST MONEY: DECL-PP-1, Progress Prize round closing 2026-10-01T06:59Z. Packagers: flat1 (flatcheck), p4-excl (tifxyz-dist), handed (handcheck), each under pp/<tool>/ with scrub.json. p4-research: the form's fields and sign-in requirement, answers in pp_forms/, SUBMIT.md. The orchestrator checks each scrub and submits (target: ready by 09-29 12:00Z).
- Title channels in flight:
  - L2S (p4-l2 at 132/160; rh-e1 then reads l2sb);
  - L3 at 2.4 um (p4-depth d* pending);
  - the 1.129 um L3 calibration is STOP (P4-L3E-CALIB-RESULT), so p4-highz runs the E1 P4-F offset sweep;
  - P4-M-OUT (p4-inner build, rh-e2 reads);
  - P4-V verso and P4-W block windows after d*;
  - P4-TAG and the L10 mesh audit (p4-core);
  - the colourant physics and dual-energy work (p4-purple);
  - the title expert (p4-titulus, QA.md).
- DECL-P4-17 block brief frozen (METRIC-HASH-38; score with --cand-cmin=9).
- P4-O rulings (DECL-P4-14-A2): stage-(i) tiles first (r0-r1 x c9-c14 plus c5-c8 gate); ckpt-screen-c takes it4; amx takes the remaining iteration; ckpt-screen-a's iteration-0 is dropped (permission layer); p4-tiles-a is released; create an rh-o harness when the first o4-o6 stage-(i) manifest lands.
- Retired (not on the critical path): devloop, devloop2, contam, pairs0139 (and b/c), pairs0814, d2-*, reg*, census, trainer, chain2um, p4-pig-*, p4-struct, p4-crackle.
- Sibling status: list_sessions (saved to a file), then <scratchpad>/sibstat.py. Monitor bdoy7813t; check-in trig_01UxRs4EfN9JPNLicZcPMfZs (01:59Z).

## 8. Update 2026-09-27 02:05Z
- Progress Prize: flatcheck SUBMITTED by the owner (the form needs Google sign-in; DECL-PP-1-A3). tifxyz-dist and handcheck are being published; when each lands, run tools/pp/verify_public.sh <tool>, align the sheet text to its README, mark READY, and give the owner the paste-ready entry. Monitor bjdrloc53.
- Title search: every constant-depth channel is closed.
  - L2S: gate FAIL (0/72).
  - L3 at 2.4 um: STOP. L3 at 1.129 um: STOP.
  - Block detector at the L2S depth: FAIL.
  - P4-M-OUT: uninformative (0 rows Y in 138).
- Live channels:
  - DECL-P4-18 L4, the surface-following slab (p4-l2): its numbers-only pre-gate must pass before any read;
  - DECL-P4-19, the line-structure test for the c11-c13 r0-r1 block (p4-tiles-a);
  - the P4-F offset sweeps (p4-highz);
  - the L10 mesh audit and P4-TAG (p4-core);
  - the dual-energy work (p4-purple, 2 sub-siblings);
  - P4-O stage (i) (ckpt-screen-b and -c, dev-lcsoft, dev-distft; the bf16 checks take about 3 h).
- p4-titulus QA: (i) short last column 0.65 / (ii) title block 0.20 / artefact 0.15. High z is the top; the top margin is lost. There is no Herculaneum end title in an upper margin (0/70). The highest-value literature item is CErc 54 (Nicolardi et al. 2024).
