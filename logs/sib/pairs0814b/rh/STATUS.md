Provenance: Project HERCULES | owner the owner | [id removed]

# pairs0814b P4-O harness STATUS (DECL-P4-14-A1 item 2; DECL-REMOTE-HARNESS-1; sigma2t per DECL-P4-12-A1)

Batches: o1 = ckpt-screen-b (latest PHerc.1667 iteration), o2 = ckpt-screen-a (iteration-0), o3 = ckpt-screen-c.

## 2026-09-26 21:45Z setup
- Merged orchestrator commit ce25174 (dispatch base). Hashes verified:
  - norm_manifest d2faee66 (METRIC-HASH-29)
  - p4_jobs 7966d6b1, p4_phase2 df93f9bf, p4_ext b58d555d (METRIC-HASH-35)
  - score_p4 581bc41e (METRIC-HASH-27)
  - audit.py e36cb995 (METRIC-HASH-5)
  - k_d2_task_sigma2t f07fbdff, ref_brief_sigma2t 627ebb0f, keysheet_sigma2.png 164262e6
- Runtime paths as declared: /work/p4/img, /work/jobs, /work/sealed_io, /srv/scorer.
  - /srv/scorer holds only the orchestrator's PUBLIC age recipient (seal.agekey.pub) and the batch keys that
    p4_jobs writes. No private key exists in this container, and nothing is ever decrypted here.
- Tools in tools/sib/pairs0814b/rh/:
  - prep_batch.sh: norm_manifest (no --coverage) -> import o<k> -> null no<k> ceil(n/8) o<k> ->
    jobs census_o<k> o<k> no<k> sigma2t -> COMMIT A, pushed and verified on the remote before any reader.
  - audit_e2.py: a verbatim copy of rh-e2's tool (sha256 3b37b61e).
  - poll.sh: checks the builders every 5 min.
- Builders at 21:40Z: no p4o manifest on ckpt-screen-a, -b or -c yet.

State: WAITING for builder manifests. Blockers: none.
- 01:35Z o1: builder manifest interim (3 tiles, title zone only, commit a1190c5) not flagged partial; held per ASK Q1 default; poller requires n >= 18 or a non-interim commit.

## 2026-09-27 02:45Z DECL-P4-14-A3 stage reading
- Merged orchestrator e1c687d. Hashes match METRIC-HASH-38: p4_jobs e9f99ce4, p4_phase2 999cb553, p4_ext 843a2664,
  score_p4 9a5b4761, rh_verify c6a948e6. norm_manifest d2faee66, audit e36cb995, jobs.py 02d9bd78, sigma2t
  f07fbdff, ref brief 627ebb0f and keysheet 164262e6 are unchanged.
- prep_batch.sh <k> <stage> <branch> <manifest> builds batch o<k>s<stage>:
  - It drops tiles read in earlier stages; those must be byte-identical to the earlier read, or the script fails.
  - It requires >= 3 new gate tiles (c5-c8) and >= 4 new title-zone tiles (c9-c19), and fails closed otherwise.
  - N0 = n<batch>, ceil(n/8) rot-90 copies drawn from the batch itself; jobs census_<batch>, sigma2t.
  - COMMIT A goes to logs/sib/pairs0814b/rh/O<k>/A/<batch>; COMMIT B to O<k>/B/<batch>.
- Dry run on ckpt-screen-b a1190c5 (3 tiles: 0 gate, 3 title) refused as intended. No key or job was written.
- poll.sh checks o2 (ckpt-screen-b iteration-5) and o3 (ckpt-screen-c iteration-4) every 5 min against the stage rule.
State: WAITING for a stage-eligible manifest (expected ~05:00-07:00Z). Blockers: none.

## 2026-09-27 06:45-06:55Z stage o2s1 (iteration 5, ckpt-screen-b @ 42a4500)
- Stage rule met: 10 new tiles; gate r0c7 r0c8 r1c7 (3); title zone r0c10 r0c11 r0c14 r1c10 r1c15 r1c16 r2c16 (7).
- norm_manifest: 10 eligible, 0 skipped. import o2s1 10 (key 1c38d238...). null no2s1 2 rot-90 copies from o2s1
  (seed 20344282, key bd914339...). jobs census_o2s1 sigma2t: 2 sessions (8+1, 2+1). Briefs match the ref_brief_sigma2t
  template.
- Harness defect, fixed and disclosed: prep_batch.sh's packaging step reused the batch-name variable, and failed after
  the declared tools had written the keys and jobs. Nothing had been committed and no reader had started. After the
  fix, a resume path re-ran only the packaging; before that, the tile sha256 in the key and in manifest_norm were
  checked against builder commit 42a4500.
- COMMIT A da4b973: pushed and verified on the remote before any reader.
- Reads: 2 fresh general-purpose opus readers, prompt = brief bytes, run concurrently.
- Audit (audit_e2.py -> hercules.harness.audit, sealed-output, orchestrator recipient):
  - 2/2 VALID; prompt == brief 2/2; hand-back DONE 2/2.
  - Images read: 10/10 and 4/4, 0 unread; 0 violations; image bytes unchanged since commit A 2/2.
  - .age sha256 == answer_sha256 2/2.
  - Re-runs: 0.
- COMMIT B at logs/sib/pairs0814b/rh/O2/B/o2s1: age/, audit.json, harness_jobs.tsv, transcripts/*.jsonl.gz, SHA256SUMS.
- No answer was read, decrypted or quoted here.
