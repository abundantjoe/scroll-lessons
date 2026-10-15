# Project HERCULES

Provenance: Project HERCULES

Private working repository for a Vesuvius Challenge First Letters attempt: recover
true sheet geometry and true ink signal from the official CT volumes, and claim
letters only where fresh blind readers see them under pre-declared, chance-corrected
bars.

## Record files

| File | Role |
|---|---|
| `RULES.md` | Append-only, hash-chained log of declarations, results, corrections and logged prompt conflicts. Written only by `python -m hercules.records.rules_append`. |
| `STATE.md` | Current truth: open decisions with dates and defaults, running jobs, best evidence, kill clock, compute used, next actions. |
| `METHOD.md` | Validated methods only (reader prompt, display spec, chains) with their hashes. |
| `CHANGELOG.md` | Actions taken, in time order. |
| `LEDGER.md` | Result table of every decision. |
| `logs/` | `gpu_ledger.tsv` (every compute job), `views.tsv` (every image view by the orchestrator). |
| `seals/` | Encrypted seals only (`*.age`). Plaintext seals and keys are never committed. |
| `data/catalogue/` | Hashed catalogue of official data products, checkpoints and the prize page. |
| `packages/dryrun/` | Factory dry runs only, stamped DRY RUN. |

## Layout

- `src/hercules/records`: RULES.md chain, code hashing, invisible-character scanner.
- `src/hercules/scorer`: deterministic scorer, nulls, seals (never an agent).
- `src/hercules/geometry`: tifxyz I/O, level_mesh with handedness, v2 truncation, label mapping, 3-D contamination tools.
- `src/hercules/display`, `src/hercules/harness`: display builder and blind-reader harness (not yet built).
- `tests/`: unit tests; nothing is trusted untested.
- `tools/hooks/`: pre-commit hook (append-only RULES.md, no invisible characters, no plaintext seals or keys).

## Environment

`source /opt/hv/bin/activate && PYTHONPATH=src pytest -q`. The cloud container is
ephemeral: everything worth keeping is committed and pushed. Commits are SSH-signed
with a per-session key; public keys accumulate in `.signing/allowed_signers`.
