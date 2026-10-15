Provenance: Project HERCULES | owner the owner | [id removed]

# pairs0814 -> pairs0814b handover (2026-09-25T19:42Z)

Segments handed over (whole, not started here; this session skips them from now on):

| Segment | 9 um valid cm^2 | candidate 384 px patches in 1536 px blocks |
|---|---|---|
| 20250928235953-auto_grown_20250928235953722 | 81.4 | 71 blocks |
| 20250926051122-auto_grown_20250926051122829 | 74.9 | 65 blocks |

Total 136 of the 263 blocks remaining at handover. 20250926051122 was the next segment in this session's queue and
had not started. This session keeps 20250925222237 (in progress), 20250926165636, 20250926203608,
20250928235954, 20250929040153, 20250930083742, 20251001060526 and 20260226000000 (46527), about 141 blocks.
20251001060526 stays here (the orchestrator's example listed it) so that the two halves balance.

Exact procedure (same code, same schema), from a checkout of this branch with /opt/hv and /work/bin/vc built
(tools/sib/pairs0814/setup_env_sib.sh; the vesuvius step fails on Python 3.14 and is not needed):
1. mkdir -p /work/sib/meta; fetch https://vesuvius-challenge-open-data.s3.amazonaws.com/metadata.json (gunzip if
   gzip; decoded sha256 8119d1c2d48b54f880c81bfd7ff9a51eb5edd166c9c06eac754abf15dba7e0ac) to
   /work/sib/meta/root_metadata.json, and PHerc0814/volumes/20250804134230-9.362um-1.2m-113keV-masked.zarr/metadata.json
   (sha256 7db0a497ed78165a17b681debacd40e6fadd99326aed8423b9e337007cad4b92) to /work/sib/meta/v0814_9.json.
2. PYTHONPATH=src /opt/hv/bin/python tools/sib/pairs0814/stage_a.py <SEG_ID>   (writes logs/sib/pairs0814/stage_a/)
3. PYTHONPATH=src /opt/hv/bin/python tools/sib/pairs0814/stage_b.py <SEG_ID>   (repeat until
   /work/sib/blocks/<SEG_ID>/SEGMENT_DONE.json exists; blocks resume)
4. Push logs/sib/pairs0814/registry/<SEG_ID>.jsonl, stage_a/<SEG_ID>.json and the staged block files
   (/work/sib/blockpairs/<SEG_ID>/*.npz, or shards packed by stage_c.py) to the pairs0814b branch.
Stage C (base-papyrus and duplicate annotation, packing) is run over the union of both branches by whoever merges.
