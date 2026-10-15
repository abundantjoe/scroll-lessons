# p4-layout ASK (questions for the owner / orchestrator)

Provenance: Project HERCULES | owner the owner | [id removed]

## ASK-1 (2026-09-26 ~18:50Z): may we accept the EduceLab Data License to fetch the 2024 title-search segment meshes?
- DECL-P4-13 item 3 needs the organizers' 2024 title-search segments: 20240102231959, 20240110113230, 20240116164433 (1A) and 20240101215220, 20240109095720 (1B) (logs/p4/recon.md).
- They exist only on dl.ash2txt.org (PHercParis4.volpkg/paths, on the 7.91 um DLS volumes 20230205180739 / 20230206171837). They are not in the CC BY-NC open-data bucket.
- The host is reachable anonymously, but https://dl.ash2txt.org/LICENSE.txt (fetched 2026-09-26 ~18:47Z) says: "By registering for downloads from the Vesuvius Challenge Data Server ... I agree to license the data ... under the following terms". The terms include non-redistribution and publication limits, and an EduceLab citation requirement. The organizers' atlas (villa atlasOverlay.json) scopes the EduceLab licence to "the 7.91 um DLS scans".
- Accepting a licence is the owner's decision, not a sibling's. recon.md also records dl.ash2txt.org as outside its declared source list. So nothing was fetched from dl.ash2txt.org except LICENSE.txt.
- What we would do if allowed: fetch only the 5 segments' mesh files (meta.json and OBJ or tifxyz; a few hundred MB, no CT). Map the 1A ones to 20260411134726 through the bucket's transform.json (24 landmarks, affine to 20230205180739). The 1B ones have no published transform, so they would stay unmapped and be reported as such. Then compute the minimum mesh distance to every strip-a tile. The outputs are numbers only (distances), with no redistribution of data.
- Unblocked meanwhile: the distance code is validated on open-bucket segments (the labelled segment 20231016151002, whose 2026 re-mesh is in the bucket).

## ASK-2 (2026-09-26 ~21:30Z): the session's safety check refused use of the EduceLab meshes; the owner must authorise it in this session
- OWNER-LICENSE-EDUCELAB-1 (RULES.md) was relayed to this session by the orchestrator (scheduled-trigger notifications of 18:50Z and 21:20Z), and I verified it in RULES.md.
- The five meshes were fetched to local scratch: meta.json plus <id>.obj only, nothing else, 89 MB. meta.json gives the volumes: 1A (20240102231959, 20240110113230, 20240116164433) are on 20230205180739, and 1B (20240101215220, 20240109095720) are on 20230206171837. OBJ sha256 values: 6603ba8c.. (…231959), 241501eb.. (…113230), fafc3ff3.. (…164433), f2bb7bd2.. (…215220), ae633f42.. (…095720).
- When I ran the distance computation on them, this session's auto-mode safety check denied it ("Real-World Transactions", i.e. licence use). The acceptance reached this session only as a relay, not as the owner's own message here. I did not route around the denial.
- The files were deleted from scratch immediately afterwards. Nothing from them was committed, and no number derived from them exists.
- To unblock, either:
  (a) the owner states the acceptance directly in this sibling session; or
  (b) the owner adds a permission rule; or
  (c) the orchestrator or another session that holds the owner's direct message runs `tools/sib/p4-layout/orgmap.py <strip meshdir> <id>.obj 7.91 <bucket transform.json> <out.json>` for the 1A ids.
- Ready and validated:
  - OBJ loader;
  - the transform direction (inverse of the bucket's 20260411134726 transform.json);
  - the transform accuracy: on 20231016151002, the 7.91 um tifxyz mapped to 2.4 um vs the organizers' 2.4 um re-mesh gives 8.6 / 19.1 / 26.8 / 32.1 um at p10/p50/p90/p99 (edge/xfcheck.json).
- 1B has no published transform to 20260411134726, so it stays unmapped in any case.
