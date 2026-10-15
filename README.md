<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="D2 trainer checkpoint-shard test ref: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# D2 trainer checkpoint-shard test ref

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-trainer-ckpt` · ink-model training and checkpoint screening · 2026-09-25..2026-09-25 · status **ARCHIVE** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md).

## Question

Does the trainer's reclaim-safe checkpoint scheme survive a real push to GitHub: shards under 90 MB as one parentless, force-pushed commit that can be fetched back byte-identical?

## Method

The trainer lane saved a full resume state into shards, force-pushed it as a single orphan commit to this dedicated ref, then replaced it with the final weights of a synthetic 2-step test run and fetched them back to compare sha256.

## What ran on this branch

One push on 2026-09-25 (23:44Z) from the trainer lane. Before this README, the branch held only MANIFEST.json and two shard files: the final weights of a synthetic 2-step test run, 138,362,143 bytes, with no project files and no real-data weights.

## Outcome

The fetch returned the weights byte-identical, and the ref held exactly one commit, as designed, until the README commits of 2026-10-15. After the orchestrator's Q6 ruling (no weights on git), the trainer was changed to refuse network remotes. Its attempt to delete this ref was refused by the session's safety check, so the ref remains as a leftover test artifact. The trainer report says the owner or orchestrator should delete it.

| key number | meaning | file on this branch |
|---|---|---|
| 138,362,143 bytes | total size of the stored synthetic test weights (2 shards: 90,000,000 + 48,362,143) | `MANIFEST.json` |
| step 2 | training step of the stored synthetic test model | `MANIFEST.json` |
| 4e3572c7...9490 | sha256 of the stored model_final, which matched on fetch | `MANIFEST.json` |

## Where the records are

- `MANIFEST.json`
- `shard_000.bin`
- `shard_001.bin`

## Lesson

A test artifact pushed to a remote ref needs a cleanup route that does not depend on a destructive git command the session may be refused.

## Related

- sib-trainer
- DECL-OFFLOAD-1
- DECL-D2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. This branch has its own history, unrelated to the research log, and had no README before this one.

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
