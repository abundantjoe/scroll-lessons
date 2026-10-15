Provenance: Project HERCULES | owner the owner | [id removed]

# d2-p128 STATUS

Updated 2026-09-26 ~06:05Z. Phase 1 DONE (READY.md). Prep complete. WAITING for GO D2. No real data fetched or trained.

- Gate: no D2 amendment in RULES.md (checked at claude/gifted-bell-gavnl5 219e271); no pair freeze; no GO.
- Env pinned (setup_p128_env.sh; hv-ink-freeze versions matched). Base ckpt sha256 verified.
- Tests at 8475920f: 26/26 passed. Tests at 08d7e42 (later trainer, preparation only): 30/30 passed (1370 s).
- Synthetic smoke P128 s1 fp32 4 threads batch 32: 18.35 s/step median, peak RSS 6.85 GB, bitwise resume.
  Smoke config sha256 2e23202b...c5cc (synthetic source; the real config hash is recorded after the freeze).
- Hold-out check (holdout_check.json): the DECL-D2 filter reproduces the dry-run allowlist (329); 121 of them are on DEV
  segments -> ASK.md item 1.
- Open questions: ASK.md (DEV hold-outs, trainer commit, ckpt ref, fp32).
- 06:01Z orchestrator check-in: the ASK.md defaults (DEV hold-out stop-and-ask, trainer commit named by GO, local-only
  checkpoints, fp32) apply to preparation only. Recipe, pool and gate answers come with DECL-D2-A1 in RULES.md.
  Nothing is running; this session idles until GO D2.
