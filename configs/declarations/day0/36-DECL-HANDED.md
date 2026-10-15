Handedness convention test on PHerc0139 (section 5.2 real-data test), declared before any of its data exists.
- Material: 4 windows (1 x 1 cm, 1068 px at full 9.362 um scale) on base-trained, non-clean 0139 segments that are in no READ-CAL, canary or sealed set (chosen by code: the 4 windows with the highest fraction of valid reference coverage on w041 and w039; never chosen by viewing).
- Arms: the official 2.399 um reference map mapped to the 9 um canvas, levelled, and shown in state A = orient_for_reading with convention_sign = +1, and state B = state A mirrored in u. No CT, no model map.
- Readers: 3 fresh blind readers (harness per DECL-HARNESS), each seeing all 4 windows as LEFT/RIGHT pairs (A/B side randomised per window by the display builder; key held by the scorer). Brief: "One image of each pair is mirror-reversed. Say which side shows normally oriented writing, then list the letters you can identify in that side."
- Metric: votes = 12 (3 readers x 4 windows); a vote is for A or B.
- Bar: >= 10 of 12 votes for one state -> convention_sign fixed for ascending-z JULY scans (+1 if A, -1 if B); otherwise AMBIGUOUS -> every 9 um read renders both mirror states as separate declared arms until a re-test on 4 new windows passes.
- The descending-z convention (0009B) is tested the same way before any MAY or descending-z read.
- Default: AMBIGUOUS.
