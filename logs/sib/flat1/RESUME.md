Provenance: Project HERCULES | owner the owner | [id removed]

# flat1 RESUME (2026-09-27)

- FLAT-1: DONE (logs/sib/flat1/REPORT.md).
- FLAT-2: DONE (REPORT.md, FLAT-2 section).
- P4 window A: DONE (logs/sib/flat1/p4win/REPORT.md). The full-resolution files are in /work/flat1/p4win_full and are not in git (20 MB hook). **ASK: owner permission to offload them to the data branch.**
- DECL-PP-1 flatcheck: READY in pp/flatcheck/.
  - Tests: 22 pass and 1 skips without the ABF++ path; 23 pass with FLATCHECK_ABF_CMD set.
  - Demo on public PHerc0139 data reproduces the study (demo/demo_result.json).
  - scrub.json: pass.
  - Remaining for submission, owned by the orchestrator / p4-research: fill the form from README.md; publish the repository (public, MIT) when required; the licence holder name ("flatcheck contributors" as a placeholder).
- To re-run flatcheck: `cd pp/flatcheck && pip install -e '.[test,demo]' && pytest -q tests && python demo/run_demo.py [--abf] && python scrub.py`.
