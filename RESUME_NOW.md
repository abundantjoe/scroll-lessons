# RESUME_NOW.md (read this first after a context clear)

Provenance: Project HERCULES | [id removed]

Written 2026-10-09 21:32Z, fleet table updated 21:46Z (51 siblings) by the orchestrator (session_01JNjAnFPejnNF7eVAiNeRJp). Order of truth: RULES.md (hash-chained; newest entries first), then this file. The September handover is in git history (RESUME_NOW.md before this commit).

## LIVE 2026-10-11 04:00Z: PHerc0268 spiral fit (CPU fleet), repo pherc0268 branch claude/gifted-bell-gavnl5
- Orders in pherc0268 docs/BANDS.md (Order 6 fit; 6-A5 PoC snapshot/resume; 6-A5-E1 `git add -f` mesh tifs; 6-A6
  track_dt ON via `TRACK_DT=1 fit_window.sh resume`, owner-approved 03:50Z, dispatched to all 69 unit sessions).
  Coverage docs/FLEET.md, queue docs/QUEUE.md, post-fit stages docs/PIPELINE.md, PoC docs/POC.md.
- Finding: 2000-step fits never ran track_dt (villa starts it at step 10000); all five pre-track_dt snapshots score
  phase lock 0.99-1.00 (random) vs 2.46 for the winning PHerc0343 segment (tools/post/phase_lock.py; poc/qa/).
- PoC chain: tools/post/poc_chain.sh; local work only in /dev/shm/poc (root disk allowance nearly full; git objects
  for snapshot fetches go to the alternate store /dev/shm/poc/gitobj). Unit sessions: scratchpad nudge_w2.json.
- Next: lock on each post-track_dt snapshot (scratchpad snap_watch.sh); when lock rises, run the PoC chain end to end.
- 07:00Z CORRECTION: the 2.46 control is Erwin's post-snap+flatten mesh (his mesh/README.md), not raw fit output, so raw
  lock ~1.0 does not show the fits are unusable. Root-cause workflow wf_e7039fc3-c6c running (snap evaluation with
  non-circular metrics, m7/CT registration audit, villa/Erwin config diff, 3 adversarial verifiers); reports in
  scratchpad/wf/*/REPORT.md, final in scratchpad/wf/FINAL.md. Container restarted 06:51Z (/dev/shm wiped; pherc0268
  alternates repaired by recreating /dev/shm/poc/gitobj and dropping dangling spiral refs). Owner: no more questions, no
  trial runs on the fleet; validate first, change the fleet once.
- 10:40Z (owner: low on usage, run with what we have): workflow stopped after synthesis + code verifier. Findings and
  PoC v0 in pherc0268 docs/POC.md (77d12e8a): failure is orientation (inner windings 42 deg off), not phase; clean outer
  region b16 s1100 w160-169 theta 165-225 is Erwin-like. PoC v0 = snapped w161, single-sheet fibres on theta 189-225
  (~0.5 cm2), layer profile peaks at 33; seed42 ink null (patch 2.2 mm tall). Renderer: start dockerd with
  --data-root /work/docker after a restart. No fleet order sent; fits run to 2000 on their own. Next: stack the arc over
  >= 5 windows (seams in that arc) and run the 4-model ink ensemble.

## 0. Owner's standing instructions in force today (2026-10-09)
- OWNER-STANDING-ORDER-6: keep the sibling fleet at the maximum at all times; every sibling runs a declared, measurable job and pushes to the lane branch; no bar lowered for speed.
- "The um needs to always match the um of the scan, and it's rolled not folded" (UMB-PHERC0268-RESULT-A1, DECL-UMB-2, DECL-UNR-1-A1): every sheet-level claim at 8.64 um (OME level 0); PHerc0268 is a flattened, crushed ROLL; coarser levels only locate windows and budget bytes.
- Umbilicus before unrolling (executed: UMB-GEOMETRY-RESULT, DECL-UMB-1 + A1, UMB-PHANTOM-RESULT, UMB-PHERC0268-RESULT, then the correction above); unrolling under DECL-UNR-1 (+A1); the ink model (DECL-FL-7) is applied only to validated rendered pieces.
- The "question everything" audit mandate: flag hidden failure modes and hardened alternatives before code (the audit syntheses are logs/umb/audit_spec.md and logs/umb/DECL-UNR-1.review.md).
- Earlier standing orders still hold: no fabricated readings, declarations before data, the orchestrator claims no letters, no personal information about the owner anywhere, the HRC-JB provenance line only in dominion commits.

## 1. Geometry of PHerc0268 (measured)
Former roll axis along the volume's y; windings stacked along z over ~90 mm; nested hairpin columns at both x edges, split into lobes by seams; at 8.64 um: sheet width 122 um median, pitch 380 um median (UNR-X0-SURVEY-RESULT). Level-3 analyses (st_axis/topo_axis/topo_defects) are packet-scale surveys only.

## 2. Live work and where it lands (lane branch claude/gifted-bell-gavnl5-fl4t; read with `git fetch --depth 1 --filter=blob:none origin +refs/heads/claude/gifted-bell-gavnl5-fl4t:refs/watch/fl4t` and `git show refs/watch/fl4t:<path>`)
| Job | Where | Output |
|---|---|---|
| DECL-UMB-2 native core, 192 y positions | umbcore-0..23 (tools/umb/lane_core.sh <L mod 6> 6 <0|102|51|153>) | logs/umb/native/lane<L>[_o<off>]/core_native.json (+ cached fields on the lane in /dev/shm/umb_fields) |
| DECL-UMB-2 bar B6 phantom suite | phantom-w1 (waits for tools/unr/phantom_flatroll.py, which a local worker is writing) | logs/umb/phantom_native/summary.json |
| DECL-FL-7 round 1 (fp32, 2 epochs from logs/fl7/global_r0.pt) | lanes 0,3,4,5,6 and ink-7..13 (partitions 0-6, tag b); ink-central = centralized control (lane_central.sh 1, all 18 shards, 4 epochs) | logs/fl7/lanes/lane<L>[b]_r1.pt + hist; then tools/master/avg_ckpts.py -> global_r1 |
| ink_9um held-out baseline | lane 1 (lane_baseline.sh 18) | logs/fl7/baseline/PHerc0343P_20250511003658/ |
| DINO-3D SSL | lane 2 (PHerc0009B shards), ssl-0800 (PHerc0800 unlabelled) | logs/fl7/ssl/ssl_r0.pt, ssl_0800.pt |
| Public baselines on the held-out shard (DECL-FL-7 3(ii)) | base-hecate, base-dense, base-8um | logs/fl7/baseline/<model>/ scored with tools/master/baseline_eval.py |
| DECL-UNR-1 operators (items 3-6, W12) | dev-hairpin, dev-shear, dev-x2, dev-x3gate, dev-mesh, dev-w12 | tools/unr/{hairpin_trace,shear_lines,fused_count,x3_gate0,mesh_checks,frame_test}.py, logs/dev/* |
| Literature sweep (native-resolution sheet tracking of crushed rolls) | research-2026 | logs/research/unrolling_2026.md + JSON of verified claims |
| local fp32 sanity run (17 shards) | this container, /dev/shm/sanity/run.log | epoch lines |
Session ids: logs/sib/registry.json (fleet_2026-10-09). Orders go by create_trigger with persistent_session_id and run_once_at a few minutes ahead; a new session by create_session with source_url the repo and source_revision the lane branch.

## 2b. SIB-KEEPALIVE-1 (23:00Z): idle sibling containers are reclaimed and detached jobs die. Every compute order now: resumable script + DONE marker, the sibling polls in <10-min Bash calls until DONE, backup trigger +100 min, orders via a dispatcher sibling from a committed brief (logs/sib/dispatch_2026-10-09_2300.md; dispatcher session_015m3dKh7GGq1nBAFcgSZ3SJ). Pass 2 (DECL-UMB-2-A1, U-turn operator tools/umb/uturns.py, windows to mid-x, ~25 min per y) runs on umbcore-0..23 -> logs/umb/native2/lane<L>_o<OFF>/ ; round 1 re-runs on lane0,3,4,5,6 + ink-7..13. Bars: tools/umb/umb2_bars.py over logs/umb/native2/lane*/core_native.json. B6 generator: tools/unr/phantom_flatroll.py (v3: concentric nested windings sized by width, lobes with shifts and gaps, 11 s per section); suite: tools/umb/phantom_suite.sh (phantom-w1 restarted 23:19Z with keepalive; local one-case check in /dev/shm/b6/case0). Dispatcher follow-up at 23:40Z creates section-C triggers (ink-central, lane1, lane2, ssl-0800). UNR-X1-V0-RESULT recorded: X1 v1 needs the sheet-scale ridge operator (DECL-UNR-1 amendment pending).


## 2c. 2026-10-10 00:50Z: the master pipeline (owner order: one shot per scroll, everything trained today in one chain)
tools/master/hercules_pipeline.sh <config> <out> [stages 0123456]: S0 frame survey (level 4, bookkeeping) -> S1 umbilicus (core_native v2 + umb2_bars) -> S2 sheet trace over a y band at level 0 (e2e_sheet.py trace: CT 16-section means as the ridge prior, orientation-field streamline tracer with ridge re-anchoring, grid seeds by extent; DECL-E2E-1, -A1, -A2) -> S3 mesh checks -> S4 render 17 layers -> S5 master ink model global_r0 fwd/rev -> S6 gold + checks.json. Config configs/pipeline/PHerc0268.json (band y 5820 +- 2.5 mm). Running in logs/unr/e2e/PHerc0268_y5820/ (sections cached in /work/e2e/PHerc0268_5820/). Findings so far: the m7 surface prediction is speckle in xz sections (unusable as prior); the Hessian ridge locks on crack rims; the field tracer gives at most 18.8 mm of continuous sheet on the seed section (G1 fails, recorded). Fleet: the dispatcher sibling (session_015m3dKh7GGq1nBAFcgSZ3SJ) is blocked on a permission prompt and created no triggers; the orchestrator created the 12 round-1 re-run triggers itself (00:02-00:13Z); umbcore pass 2 is NOT dispatched; next fleet use = the master pipeline per band once this band's run validates.


## 2d. 2026-10-10 02:56Z: E2E-1-RESULT recorded (RULES.md line 5856). The master pipeline ran end to end on band y5820: one 19 mm tapering strip, 0 self-intersections, G5 0.61, master model global_r1/r2 at held-out AUC 0.58 (ink bars fail), 11 gold pixels at p > 0.5, umbilicus not determined on 3 positions (B1 0/3, B2 0.0, B6 partial). Deliverables sent to the owner (gold_preview, ink_heat_preview, centre). Next: DECL-E2E-2 (surface operator) from the design-review workflow wf_964e144c-7cb (synthesis pending) and its 30-minute pilot on the cached band /work/e2e/PHerc0268_5820; DECL-FL-7-A1 fine-tune on base-dense (trigger 02:06Z); round-2 control done (global_r2 0.578). Fleet: 12 ink lanes idle after round 2; umbcore lanes idle (pass 2 never dispatched); phantom-w1 B6 partial.

## 2e. 2026-10-10 04:30Z: DECL-E2E-2 ORD-3 (the next surface operator) and its pilots
Design-review workflow synthesis -> DECL-E2E-2 (RULES line 5871) + amendments A1 (gap-adaptive gate), A2 (12-section tensor, correlated phantom tilts, hop test rules), A3 (DORMANT revival grammar, I5 twin-distance continuity, I4 on the tilt-corrected mean, phantoms seeds 0/2/14, PASS-A = V1 on all phantoms + identifiability), A4 (two-scale ridge sigma 2.5/4, margin rule removed, seed-row prior off, interpolated carrying of dormant cells, I2 relaxed, I4 memory + two-row termination, hop detection = flagged or unexported). Code: tools/unr/ord3.py (operator, raw and means modes), tools/unr/phantom_ord3.py (phantom generator), tools/unr/pilot_ord3a.py (pilot A driver), configs/pipeline/ord3_params.json. Phantoms live in /dev/shm/ord3_phantom{,_s2,_s14} (regenerate with `phantom_ord3.py <dir> --seed <0|2|14>`, 60 s each). Results: ORD3-PILOTA-RESULT (FAIL-A; real-band nulls: d_comp 11/14/17, identifiability at dy 4 0.84, the cached 32-section step cannot carry identity, hop test on means void), ORD3-PILOTA2-RESULT (FAIL-A on all three phantoms; causes measured -> A4). pilotA3 (A4 grammar) running at 04:28Z -> logs/unr/ord3/PHerc0268_y5820/pilotA3/. If PASS-A: pilot B = the raw level-0 block of item 2a (660 chunks, 1.4 GB, S3) with bars V1-V12 -> ORD3-PILOTB-RESULT; only then the fleet gets the block/stitch job. Also recorded tonight: UMB2-B6-RESULT (umbilicus phantom fails, umbilicus not determined), FL7-A1-RESULT (dense fine-tune no gain; best ink model = public dense_native base 0.76 AUC, bars not met). Check-in trigger: E2E-2 check-in 3 at 05:01Z.

## 2f. 2026-10-10 05:00Z: ORD-3 pilots done. pilotA (FAIL-A), pilotA2, pilotA3 (phantom limits), DECL-E2E-2-A5 (CLEAN export; pilot B as a measurement), ORD3-PILOTB-RESULT (FAIL-B on the raw block: CLEAN anchored 0.63 at +-4 sections -> 0.30 at 0.24 mm -> 0.06 at 0.73 mm; acceptance margin over random 0.13; I4 power 0.17-0.5; hop detection 0.30 with 0.05 control; RSS 7.2 GB). The raw block is in /dev/shm/ord3/block.npy (1.38 GB, (Y,Z,X), y 5632-6015, z 5632-7040, x 2688-5248; fetch.json beside it); the seed-0 phantom in /dev/shm/ord3_phantom. Next (to declare, not launched): DECL-E2E-3 = (a) band-observability survey across y of PHerc0268 (seed-row statistics at level 0 only: acceptance margins T/C1/C3, d_comp, I4 power at dy 4, twin-distance continuity) to find where sheets are trackable at all, a fleet job of one y per lane; (b) a 3-D sheet-likeness operator over the 12-section stack (the HFG-3D ridge of the review) replacing the 2-D ridge acceptance, tested first on the block in /dev/shm. Fleet idle until declared.

## 2g. 2026-10-10 09:40Z: fleet down (usage credits), work continues locally
All sibling sessions failed at about 05:15Z: "out of usage credits" (seven-day overage on the sibling model; resets 2026-10-14 03:00Z; INBOX item 36). This session's model was switched by the owner. The container restarted during the gap (/dev/shm wiped; level-4 volume, the raw block /dev/shm/ord3/block.npy and the seed-0 phantom /dev/shm/ord3_phantom were re-made at 09:38-09:41Z). DECL-E2E-3 survey: 17 y positions from lanes 0-7 (pulled into logs/unr/obs/), the remaining 55 running locally (scratchpad obs_local.sh, workers local0-2, logs/unr/obs/local<K>.log, DONE markers local<K>.DONE). Interim: every window passes the declared one-step rule (margins over C1 0.38-0.46, over C3 0.49-0.58), the same as y 5820 where tracking failed: the one-step margin does not discriminate regions. DECL-E2E-3 item 2 (3-D operator, tools/unr/ord3.py gated_fields3d, configs/pipeline/ord3_params_s3.json): phantom run logs/unr/ord3/PHerc0268_y5820/pilotS3_phantom/ in progress; real-block run next (pilot_ord3b.py with params_s3 -> pilotS3_block/).

## 2h. 2026-10-10 11:05Z: state after the second line of operators
Recorded today after 09:35Z: OBS-SURVEY-RESULT (216 windows over the whole body; homogeneous; the one-step rule passes everywhere and does not discriminate; texture power below 0.8 everywhere), ORD3-S3-RESULT (3-D sheet-likeness operator: no gain over the 2-D ridge on phantom or raw block; the local-operator line on PHerc0268 at 8.64 um is closed), DECL-E2E-4 + VC3D-AUDIT-RESULT (78 VC3D-grown PHerc0268 surfaces found on lane branches, list logs/unr/vc3d_audit/surfaces.txt; the W3 peak statistic has no power here: surface 0.145-0.155 vs control 0.145-0.157; stopped by its sensitivity rule after 2 surfaces). PHerc0268 exists only at 8.64 um. Fleet blocked until 2026-10-14 03:00Z (INBOX 36). Open options, none launched: (a) ridge-based 'sits on a sheet' audit of the 78 grown surfaces (tests placement, not identity); (b) a global identity formulation (assign ridge fragments of a block to ordered sheets with non-crossing constraints across u and y); (c) concentrate the ink side on surfaces already validated elsewhere. Raw block and phantom in /dev/shm (lost on restart; re-made by ord3_fetch_block.py and phantom_ord3.py).

## 3. Next steps
1. When umbcore lanes push: merge their core_native.json records, run the DECL-UMB-2 bars (B1-B5) only after phantom-w1 reports B6; record UMB2-PHERC0268-RESULT.
2. Round 1: average all lane*_r1.pt (weighted by n_train) -> logs/fl7/global_r1.pt (sync_fl4t), dispatch round 2; bars of DECL-FL-7 item 3 before any application.
3. DECL-UNR-1 X1 at native resolution: the sheet-identity tracker is NOT written yet; design per logs/umb/DECL-UNR-1.md item 3 and A1; pilot rows chosen by the declared rule.
4. Keep the fleet full (standing order 6); re-arm the self check-in every hour (send_later).

## 4. Shell hazards learned today
pkill/pgrep patterns match the orchestrator's own shell (exit 144): exclude $$ and $PPID, never combine a kill-by-pattern with a relaunch naming the same script; `logs/umb/PHerc0268/fields.npz` and live run logs are kept out of git via .git/info/exclude.
