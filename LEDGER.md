# LEDGER.md

Provenance: Project HERCULES | owner the owner | [id removed]

One row per decision verdict, citing the RULES.md declaration and result entry IDs.
Numbers are copied from scorer output JSON (sha256 given); never typed from memory.

| Decision | Declaration ID | Result ID | Verdict | Key numbers | Scorer output sha256 | Auditor |
|---|---|---|---|---|---|---|
| C3 run 1 (9 um K0) | DECL-C3 | C3-RUN1 | VOID (metric-definition defect) | Pearson 0.999999; in-mask AUC TTA 0.9902/0.5658 | see logs/c3/c3_results.json | runner report |
| C3-R1 (9 um K0, C2 with TTA) | DECL-C3-R1 | C3-R1-VERDICT | FAIL | Pearson 0.9999989; TTA fwd 0.97795 (< 0.987), rev 0.56648 | 1473c540b7199797bb559c9930febdfc56f6f27526a755b31c2f5fed7091aca7 | audit_r1.json PASS (f406328e0ede25184673c6ccd8792122a4b47f061a9447e142ed222fe67d0adf) |
| C3-NT (C2 no TTA, w040 crop 3) | DECL-C3-NT | C3-NT-VERDICT | VOID (undisclosed prior map covered crop) | fwd 0.99926, rev 0.56528 (not used) | see logs/c3/c3_nt_results.json | audit_nt.json VOID |
| C3-NT-R1 (C2 no TTA, w044) | DECL-C3-NT-R1 | C3-NT-R1-VERDICT | PASS | Pearson 0.9999989; fwd 0.99960; rev 0.58558 | 9a430680bb46ca9886f779413321d6c19b3a06bbf3470fbab0456ca6da1b8b6e | audit_nt_r1.json PASS (c4139c1c6f9af20eb5ba946745739648e1fec8a216d7505ba50ca5f51cdbc2de) |
| Handedness 0139 (x3) | DECL-HANDED / -R2 / -R3B | HANDED-1 / HANDED-R2 / HANDED-R3B | AMBIGUOUS x3 | votes A:B 0:0, 7:1, 5:13 | logs/handed/ | code-scored |
| READ-CAL PROBE-1 | DECL-READCAL-PROBE1 (+A1, A2) | PROBE1-RESULT | SG-FEAS NOT PASSED; REF not blind-legible | max 4 agreed per window, 0 agreed-firm, all shuffle p >= 0.107 | aaa9bc22895563ccc1721ab6a708ab031faad3226b8a473991c94ff13972ff8f | audit of 36 transcripts VALID |
| READ-CAL PROBE-2 (key sheet, paired on PROBE-1 windows) | DECL-READCAL-PROBE2 (+A1) | PROBE2-RESULT | declared condition MET in 1 cell (K_D2_A_fable w039); SG-FEAS NOT PASSED; nothing lifted until fresh-material replication | w039 A_fable 5 agreed, p 0.031; 0 agreed-firm; mirror A 15 : B 6 | 0e4b3fecfe908fb6ae9490132c3ce318012207ccf8c2eb5b226e358a36ab55d8 | audit of 12 transcripts VALID |
| READ-CAL PROBE-3 (replication, fresh w040/w044) | DECL-READCAL-PROBE3 | PROBE3-RESULT | REPLICATED (primary K_D2_A_fable); suspension lifts for K_D2 + fable only; SG-FEAS NOT PASSED | w044 A_fable 10 agreed, p 0.0005, 0 firm; mirror A 19 : B 18; agreed identities mostly O/I/T (exploratory) | 222976e3531fd835a7311e156203662dcaf6d096a6ff75ae949bba7bcefc7da3 | audit of 12 transcripts VALID |
| D1 REF ladder (K_D2 + fable, 0841 J) | DECL-D1 (+A1..A6) | D1-REF-RESULT | NOT VOID; sigma_crit 0.30 mm | REF0 C_all 16.0 of S' 20, C_net 11.37, p 1/5001 | 7c3884a2b43dc9b50fb41ce03fc1c3503239551eca0623dcb550bbaace5d7cd8 | re-derived exactly (audit_d1_rederive) |
| D1 KTLB-3R model arms (BASE, RAW, CHANCE x A/B) | DECL-D1 (+A1..A6) | D1-VERDICT | FAIL | 0 namings on all J windows and blanks (18 readers); C_net 0; p_max 1 | 22b2a0faf24b85c4e5288cdbb8d08e05645b4356413c577b4859b0c4bd0a7b7a | multi-lens audit PASS 4/4 (63c8044ea947e7e1006fc4e992e17b5d3334cabe917631b6ff13e053ed635127) |
| Hecate 9.6 screen on 0841 | DECL-HECATE | HECATE-SCREEN | screened out | AUC 0.678 (base 0.634) on 0.066 cm^2 | logs/d1/hecate_screen_summary.json | builder report |
| D3 FOLD-0841 (4 fine-tune arms, 24 sealed reads of J) | DECL-D3D4 (+A1..A3), METRIC-HASH-18 | D3-VERDICT | NOT PASSED (audit PASS) | C_all/C_net 0 in all 8 arm-states; FA 0 namings on 72 J/blank panels; p_max(FA) 1; canary 3-13 per reader | logs/d1/d3_summary.json fb8d31c0...; logs/d1/audit_d3.json 3ad936ed... | auditor (3rd attempt) |
