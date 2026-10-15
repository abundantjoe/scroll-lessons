Provenance: Project HERCULES | owner the owner | [id removed]

# census: questions for the orchestrator (each with the default I continue on)

Written 2026-09-25 ~19:13Z. Numbers behind each item: logs/sib/census/census.json (when pushed) and the walker validation files.

1. Duplicate (re-trace) estimate before tracing is weak. Validation on official PHerc1203 dev-set team segments (never the T0 five): 48 same-sheet vertex pairs (positives) and the same pairs with one end moved to the adjacent m7 sheet (negatives).
   - Walker v1 (radial snap about the centre curve): 3 of 36 determined positives called SAME, 2 of 35 determined negatives called SAME, AUC 0.47. Rejected.
   - Walker v2 (follows the local m7 sheet normal; point-to-m7-surface distance along the normal at the end, as CORR-RETRACE-RULE asks): step 4 / shift 3: 13 of 35 positives SAME, 5 of 30 negatives SAME, AUC 0.60. Step 2 / shift 1: 8 of 35 vs 5 of 33.
   Default: the seeds files report (a) the hard geometric upper bound (share of seed pairs whose trace neighbourhoods can overlap, surface distance <= 2 x 20 x generations vox), and (b) the walker v2 counts with the measured sensitivity and false-SAME rate beside them. The v2 counts are labelled low-reliability. The binding duplicate test runs after tracing on the traced meshes with CORR-RETRACE-RULE form (b) (point-to-triangulated-surface, >= 1000 points within 2 vox and count[0,1) >= 2 x count[2,3)). Of any SAME pair, the later seed (higher n) is dropped.
2. Centre on volumes without an umbilicus: CT-mask centroid (level 4, running median 65 slices + Gaussian sigma 256 vox). Calibration on the three umbilicus volumes: median error 300-390 vox (0.14-0.21 r_eq), p90 0.28-0.45 r_eq. A CT-free m7 normal-line centre was worse on 0125 and 0211 (median 396-444 vox). Default: centroid; the wrap fraction 0.35-0.70 is therefore uncertain by about +-0.2 on oval volumes, which I record per volume rather than correct.
3. Ranking formula (declared in REPORT.md before the final numbers were read): mean of five 0-1 components (axis ratio, solidity p10, centre source, lasagna + known z direction, share of 60 seeds passing every check). Then 1203 and 0846A (public rescans) are moved after all others, following the stricter handling in the D0 settled record. Default: this formula.
