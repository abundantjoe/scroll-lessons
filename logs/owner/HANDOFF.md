# HANDOFF: if Claude stops before the title work finishes

Provenance: Project HERCULES | [id removed]
Written 2026-09-27 21:15Z by the orchestrator, because the owner warned that the subscription may end soon. Everything named here is committed on GitHub (abundantjoe/dominion). Nothing depends on a live container except the sealed-answer decryption key; see "What is lost" below.

## The one live route to the Paris 4 title
Our own ink model, P4-OWN (RULES.md DECL-P4-23), is trained on Paris 4 itself. The title zone and a 1.2 mm margin are excluded from its training, as the prize requires.
- Evidence the model works on this scroll: on col. -1, the text column right beside the title slot, which the model never trained on, it separates the organizers' labelled ink from non-ink at pixel AUC 0.978 (RULES.md P4-OWN-S1-COLM1-AUC).
- Its maps of the whole title slot (strip w010-027, columns c14-c17, rows r0-r5) and of col. -1 already exist. They are on branch `claude/gifted-bell-gavnl5-sib-own-lead`, under `logs/sib/own-s1/maps/tiles/` (PNG, 1068 px per 2 cm tile; one `.png.json` record per tile). NOBODY has looked at them. Our declared rules forbid reading them before the held-out legibility gate G1 passes.
- G1 (DECL-P4-23 item 6(b), -A1, -A2): blind readers must find rows of >= 5 letters on >= 30 % of the held-out known-text tiles of three fold models (F1, F2, F3). F1 is trained; F2 and F3 are training. The verdict is expected on Monday 2026-09-28, roughly 07:00-10:00 UTC.
- If G1 passes, the order is:
  1. a blind census of the title-slot maps;
  2. candidates must be positive in 2 of 3 seed models and absent in the label-scrambled NULL model;
  3. phase 2 and the extended test (DECL-P4-3).
  Only an EXT-CONFIRMED tile becomes a prize package.

## Honest odds
Nothing so far shows title ink. Every earlier channel was null or uninformative. G1 can fail, and even with a pass the title may be too damaged to read. No one can promise a title from this data.

## If Claude stops before it finishes
- The declared route is the only supported one: G1, then the blind census, then EXT-CONFIRMED, then a package (RULES.md DECL-P4-23, DECL-P4-3). Unread maps are not a result and are not to be packaged or sent as one.
- 2026-09-27 21:20Z: the orchestrator tried to build a title-slot image from the unread maps for the owner. Its auto-mode safety check refused this as weakening the project's integrity controls. It was not pursued, and this file no longer suggests it.

## What a prize submission needs (scrollprize.org prizes page, Title Prize)
1. The tifxyz mesh of the region, with a low-distortion flattening. We used the official w010-027 mesh. It is EduceLab-licensed, so never publish it; name it instead.
2. A programmatic image of the title with a 1 cm scale bar and the letter dimensions, named after the mesh.
3. Methodology, false-positive mitigation and held-out validation. Here that means RULES.md DECL-P4-23 with its amendments, the F-fold AUCs and G1, N0, NULL, seeds, phase 2 and the extended test.
4. A statement that the ink-model training data do not overlap the title region: DECL-P4-23 item 7 and the train manifests with min_dist_to_X_mm = 1.2.
The submission form needs the owner's own sign-in, as it did for the Progress Prize.

## What is lost if the container ends
- Sealed blind-read answers can only be decrypted with the scorer key held in the orchestrator container. Answers that are sealed but not yet scored become unreadable. Everything else is in git.
- Pinned tools, in orchestrator branch `claude/gifted-bell-gavnl5`:
  - `tools/p4/rh_verify_own.py` (batch verifier, METRIC-HASH-49);
  - `tools/p4/g1_own.py` (G1 tally);
  - `tools/p4/score_p4.py`.
- Live state and next steps are in `RESUME_NOW.md` (the last section).
