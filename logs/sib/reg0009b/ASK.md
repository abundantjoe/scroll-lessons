Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (reg0009b), 2026-09-26 ~05:45Z: a decision for the orchestrator

**Question.** DECL-DEVLOOP-A1 item 7 puts 0009B DEV windows "outside every KTLB-M candidate window + 144 vox". Measured by devzone.py (devzone.json; numbers only; no map produced), that leaves 0009B with essentially no inked DEV material:

| exclusion set | reading of 144 vox | allowed area cm^2 | 2 x 2 cm windows fully allowed | of which ink150 >= 0.05 | 1 x 1 cm blanks (cov >= 0.90, ink < 0.01) |
|---|---|---|---|---|---|
| 23 dedup candidates | 8.64 um vox (1.24 mm), + sampling margin | 99.4 | 0 | 0 | 5 |
| 23 dedup candidates | 2.401 um vox, + margin | 188.7 | 15 | 0 | 67 |
| all 76 dense windows | 8.64 um vox | 34.1 | 0 | 0 | 0 |
| all 76 dense windows | 2.401 um vox | 136.6 | 2 | 0 | 46 |

The 144-vox clearance is 3-D, so it also removes the neighbouring wraps.

**Needed decisions:**
1. Which unit does "144 vox" use? The strict 8.64 um reading is assumed by default.
2. What counts as "every KTLB-M candidate window": the 23-window pool, all 76 dense windows, or only the windows the picker finally seals?

**Why it matters.** 0009B can serve as a DEV scroll only if KTLB-M seals a subset and releases the rest of the pool. A 0009B DEV scroll would need both text windows and >= 4 blanks, so a sealed set smaller than the pool is the only route. That trade-off (KTLB-M S >= 30 letters vs a third DEV scroll) is the orchestrator's call.

**Default if unanswered.** 0009B contributes no DEV windows. Nothing is blocked on my side: all KTLB-M material is delivered.

**RESOLVED 2026-09-26 05:59Z** (orchestrator ruling): native 2.401 um vox, point-to-surface. Proposal: proposals/DECL-DEVLOOP-0009B-EXT-proposal.md.
