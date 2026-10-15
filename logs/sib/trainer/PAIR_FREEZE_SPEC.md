Provenance: Project HERCULES | owner the owner | [id removed]

# D2 pair-freeze record: exact format (schema `hercules-d2-pair-freeze/1`)

The tool is `tools/sib/trainer/pair_freeze.py`, tested in `tests/sib_trainer_units_test.py::test_pair_freeze_record`.
It reads registries and hashes only. It never opens an image and never trains. Its outputs are the frozen data
identity that every D2 arm config pins.

A DRY RUN on the current pairs0814 branch state (c5fe80c) is in `freeze_dryrun/`. It is not a freeze. Result:
- 957 candidates, 957 gated, 329 passed, over 11 segments;
- registry label px: ink 7,227,625, blank 37,903,762, ignore 3,381,637;
- loaded arrays agree with the registry, with 0 label-rule mismatches.

### DRY RUN on the final pairs0814 union (05:34Z), in `freeze_dryrun_u0814/` (not a freeze)

- **Tree.** `logs/sib/pairs0814` from pairs0814 2305656, plus `data/sib/pairs0814b` from pairs0814b d1b6af5 (the
  commit named in its shards.json). One `stagec` source with `data_root`.
- **Result.**
  - 564 patches (384 px);
  - all 180 block files match their shards.json sha256;
  - `--verify` loads all 564 patches with 0 label-rule mismatch px;
  - ink 12,788,274 px and supervised 77,370,179 px, equal to pairs0814 summary.json (ink + blank);
  - record_sha256 ad853490...
- **Hold-out candidates.** `tools/sib/trainer/holdouts_from_registry.py` over the stage-C pair_registry.json, in
  `freeze_dryrun_u0814/holdout_candidates/`. The tool applies whichever rule is declared; it never chooses one.

  | Rule | Patches held out (of 564) |
  |---|---|
  | `base_same` (SAME papyrus as the 46527 re-trace, fail-closed rule, or on 46527 itself) | 7 |
  | `base_within:64` | 205 |
  | `base_within:128` | 282 |
  | `dedupe_groups` (keep 1 per duplicate group) | 222 |

## 1. Procedure (orchestrator)

1. When a pairs branch reports done, note its branch and commit. Materialise the data dir from that exact commit:
   `git archive <commit> logs/sib/<task> | tar -x -C /work/freeze/<task>`. Shards that are not in git are copied
   and hashed the same way.
2. Write the request JSON (section 2). It holds the D2 date, the hold-out lists and one entry per source.
3. Run `/opt/hv-ink/bin/python tools/sib/trainer/pair_freeze.py --request req.json --out logs/<freeze dir> --verify`.
4. Record `record_sha256` and `data_registry_digest` in the declaration. Each arm-trainer then runs
   `make-config ... --source <name>=<kind>:<path> --allow-ids <name>=<out>/allow_<name>.json --hash-sources`.
   The allowlist sha256 goes into the config, so its sha256 binds the freeze.

## 2. Request JSON

```json
{
  "decl": "DECL-D2-A1",
  "d2_date": "YYYY-MM-DD",
  "sources": [
    {"name": "pairs0139",  "kind": "tilegrid3",  "branch": "claude/gifted-bell-gavnl5-sib-pairs0139",  "commit": "<sha>", "path": "<dir with registry/ and shards/>"},
    {"name": "pairs0139b", "kind": "tilegrid3",  "branch": "claude/gifted-bell-gavnl5-sib-pairs0139b", "commit": "<sha>", "path": "..."},
    {"name": "pairs0139c", "kind": "tilegrid3",  "branch": "claude/gifted-bell-gavnl5-sib-pairs0139c", "commit": "<sha>", "path": "..."},
    {"name": "pairs0814",  "kind": "blockpairs", "branch": "claude/gifted-bell-gavnl5-sib-pairs0814",  "commit": "<sha>", "path": "<dir with registry/ and blockpairs/>"},
    {"name": "pairs0814b", "kind": "blockpairs", "branch": "claude/gifted-bell-gavnl5-sib-pairs0814b", "commit": "<sha>", "path": "..."}
  ],
  "holdouts": [
    {"reason": "clean controls and neighbours (DECL-D2 0139)", "file": "<JSON list of tile/patch ids>"},
    {"reason": "READ-CAL / PROBE / canary windows",            "file": "..."},
    {"reason": "base-training papyrus (46527) or duplicate group, if declared", "file": "..."}
  ]
}
```

- `kind` values:
  - `tilegrid3`: 128 px tiles mosaicked into complete, grid-aligned 3 x 3 blocks (ASK 3 ruling). `tilegrid` gives
    plain 128 px tiles.
  - `blockpairs`: the pairs0814 stage-B layout.
  - `stagec`: the stage-C `shards.json` layout, if stage C runs.
- Preferred for 0814: once stage C has run over the union, list ONE source
  `{"name": "pairs0814u", "kind": "stagec", "path": "<tree>/logs/sib/pairs0814", "data_root": "<tree>"}`.
  - `<tree>` holds `logs/sib/pairs0814` from the pairs0814 commit and `data/sib/pairs0814b` from the pairs0814b
    commit named in shards.json (both taken with `git archive`).
  - Stage C also annotates base-papyrus (46527) and duplicate groups. Hold-outs are built from those annotations.
  - Do not also list the two blockpairs sources: overlapping patch ids are not de-duplicated across sources.
- Hold-out files are JSON lists of ids: `tile_id` for tile grids, `patch_id` for 384 px patches. One held-out tile
  removes its whole 3 x 3 block (fail-closed).

## 3. Record `pair_freeze.json`

| Field | Meaning |
|---|---|
| `schema`, `decl`, `d2_date`, `created_utc`, `request_sha256`, `provenance` | identity |
| `label_rule` | ink >= 150, blank <= 100, rest ignored; rotated-in pixels ignored, never blank (ASK 4 ruling) |
| `holdouts[]` | {reason, file, sha256, n}; `holdout_ids_total` |
| `sources[].name/kind/branch/commit/path` | where the data came from |
| `sources[].registry_files_sha256` | sha256 of every registry/*.jsonl (or shards.json) |
| `sources[].data_files_sha256`, `data_files_digest` | sha256 of every shard/block file that holds a used patch (checked against the registry; any mismatch aborts) |
| `sources[].counts` (tile grids) | candidates, kept, held_out, after_holdouts, **in_block**, **out_of_block**, blocks, mosaic, patches_px, segments |
| `sources[].counts` (384 px) | candidates, gated, passed, held_out, after_holdouts, patches_px, segments, label_px_registry {ink, blank, ignore} |
| `sources[].allow_ids` | {file, sha256, n}: the ids that enter training (`allow_<name>.json`) |
| `sources[].verified_load` (--verify) | loaded patches, size, ink px, supervised px, loader registry digest, label-rule mismatch 0 |
| `totals.allow_ids`, `data_registry_digest` | digest over (name, data digest, allowlist sha256) of all sources |
| `record_sha256` | sha256 of the canonical record without `created_utc` (the value the declaration cites) |

## 4. Checks the tool enforces

- Every used data file's sha256 equals the registry value.
- With `--verify`, every patch loads and its stored labels equal the DECL-D2 rule recomputed from the teacher map.
- Hold-outs are applied before the block completeness test.
- The allowlists are written and hashed by the tool, never by hand.
