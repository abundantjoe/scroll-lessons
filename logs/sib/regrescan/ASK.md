Provenance: Project HERCULES | owner the owner | [id removed]

# regrescan: questions for the orchestrator (each with the default I follow if unanswered)

1. PHerc0846A failed the C6 r bar (held-out median r 0.8439 with the specified fit iteration 1; 0.8437 with iteration 2; bar 0.85). RMS (0.72 vox) and the control pass. Should a non-affine 0846A model be pre-registered?
   Default: no. FAIL is recorded and no further 0846A registration work is done. If the answer is yes, I propose a pre-registration (not run): a smooth displacement field (tri-cubic B-spline, knot spacing ~1000 vox, fitted to the same 24 fit patches plus 24 NEW fit patches). It would be checked on 16 NEW check patches that have never been read, chosen by the same seeded procedure with a new seed, with the same bars and control criterion. The diagnostic shows a per-patch optimum median r of 0.878, so any non-affine gain is at most about +0.034 on these blocks.
2. Which 0846A check is of record: the specified fit iteration 1 (sha256 bcb9c43fab0675ca...), or the pipeline's refit iteration 2?
   Default: iteration 1, as specified. Both FAIL, so the verdict does not depend on the choice.
3. May the 1203 affine (PASS; final_affine.json sha256 09d7caeb021d8ffc...) be used as a ground-truth mapping for T-RESCAN, under I11 (no region choice by 2.4 um data)?
   Default: yes, once the orchestrator records it. Nothing in this task used it for anything else.
