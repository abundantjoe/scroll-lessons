Provenance: Project HERCULES | owner the owner | [id removed]
# p4-purple STATUS (2026-09-27 07:10Z): DONE
- Items 1, 3 and 4 are complete; see REPORT.md.
- DUAL_FREEZE.md is copied here verbatim (sha256 93d04a4d0bbba551fe0d648b64904e3491ed15981047c36568472cdee48f9427) for the orchestrator's METRIC-HASH.
- No title-zone number exists. Blockers: none.
- 07:17Z: METRIC-HASH-40 recorded (RULES.md line 3497). The single title-zone application of DUAL_FREEZE was delegated to de (trig_019XBCfpT8QtTHgajzzu6bsK, 07:20Z) -> de/title_zone.json. Check-in at 08:18Z.
- 11:00Z: de stopped at the usage limit (~08:23Z) during apply.py (1781 blocks; APPLY.md d54aa3a and apply.py 482e966 were pushed before any number). Woken 11:02Z with checkpoint pushes; check-in 12:15Z. title_zone.json not yet pushed.
- 12:16Z: de is running again. Its block cache survived: 623 of 1781 blocks done. title_zone.json is not yet pushed. Check-in at 13:47Z.
## Dual-energy title-zone application (METRIC-HASH-40, once; de c371b1c, title_zone.json; verified: all 15 frozen tool sha256 match, only apply.py was added)
1. r3 c10-c17: 11,674 patches used. 1 hotspot (z < -T, r3_c11, isolated); 0 with z > +T; largest cluster 1. Rate 0.0001 vs control FPR 0.0215: NULL.
2. That rate is about 200x BELOW the control FPR (z p99 2.0-2.3 against 3.2-3.5 in r3 c0-c9). The z scale does not transfer exactly from the control, so the null is conservative and does not show the method's own sensitivity there.
3. Outside the title zone: r4 c0-c7 have z > +T on 33-96 % of patches (p ~1e-103). This is a reported artefact (D1): the lower end and cylinder edge of the 137 keV volume lie outside the control domain. r3 c0-c9 rates are 0.012-0.023, consistent with the FPR (p >= 0.31).
4. Sensitivity (DUAL_FREEZE): only CuO, orpiment and gold at 10-20 um. Tyrian purple, purpurissum, lakes, carbon ink, ochre, cinnabar and lead white are undetectable at <= 20 um.
5. Meaning: no Cu/As/Au layer >= 10 um on the covered 14-27 % of r3 c10-c17. A purple title there is "untestable by dual energy", not "absent".
- 2026-09-30T04:02:43Z fl-pherc0125 (DECL-FL-1): pipeline launched detached (tools/sib/fl-pherc0125/run.sh). No organizer segments for PHerc0125, so it grows <= 4 on surface-m7 (remote; no normal grids), then renders C2-NT, runs ink_9um and pushes tiles to logs/sib/fl-pherc0125/.
- 2026-09-30T04:16:05Z fl-pherc0125 pipeline: VOID run. All 12 grow tries crashed at start: the target dir did not exist (pipeline bug; grow_tries_bug1_missing_target_dir.jsonl). Fixed and relaunched; no segment or tile existed.
- 2026-09-30T04:19:30Z fl-pherc0125: relaunched after 3 tooling fixes (vc_build proxy port, vesuvius install, grow target dir). Grow try 1 is kept: 26.3 cm2, 0 transverse self-crossings. The detached pipeline pushes each unit.
