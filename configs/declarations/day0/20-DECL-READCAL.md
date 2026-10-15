READ-CAL and SG-FEAS (section 6.2). Bank material only; gates D1 reads.
- Hypothesis: some display D, prompt P and reader model make known text blind-legible; measured as sealed recall.
- Data: >= 6 dense 2 x 2 cm known-text windows from clean 0139 (w024, w047, w053, title; incl. the old CLEAN-4 windows) and 0814 if legible; outside every sealed set, fold K and T/C4 shells; KD-tree certified. Each shown as REF sigma = 0 and REF blurred to sigma_eq(base). Sealed by 3-sealer consensus (same identity within 150 px from >= 2 of 3; firm = 3/3, or 2/3 both firm) before any render of the windows exists.
- Grid (3 fresh readers per cell): displays {D2 whole window at 1/2 scale; D1Q four 1 x 1 cm quadrants at full scale, 50 % overlap; D1S 2 x 0.6 cm row strips at full scale} x reader models {strongest vision model available to subagents; one other version if available} x prompts {P of section 5.10; P plus a font-rendered lunate-capital key sheet}.
- Metric: summed C_net at sigma_eq(base) (scorer code hash in METRIC-HASH entries).
- Selection: highest summed C_net -> D*, P*, reader mix; frozen and hashed in METHOD.md. sigma_crit = largest blur at which REF keeps >= 50 % of its sigma = 0 C_net.
- SG-FEAS: SG item 1 run mechanically on REF at D*. REF passes on >= 2 windows -> SG stands. Otherwise READ-CAL continues (more displays, tiling, model versions), STATE.md top blocker = "SG infeasible at current display", no SG attempt until REF passes SG 1 on a bank window. SG bars never lowered.
- PROJ = sealed recall at D* x consensus-letter density of the densest bank 4 cm^2; ranks regions and sizes budgets only.
- Default (missing / void twice / ambiguous at date): D2 display, prompt P, strongest model; SG-FEAS recorded NOT PASSED.
