Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-gold REPORT: GOLD family (RULES.md DECL-P4-10; DECL-P4-12 items 3 and 5)

Builder role only. No image, tile or CT pixel was opened, viewed or described; everything below is numbers.

## Verdict
- **E2 (2.4 um, all 160 strip-a tiles, including the title zone c10-c17): no gold.**
  - Under the frozen rules there are 0 DECL-P4-10 hotspots. The rules count as hotspots only tiles that are not labelled-adjacent, and every tile over the area bar is labelled-adjacent.
  - Under DECL-P4-12 item 3, where flags are reported but do not exclude, 8 tiles pass the area and in-sheet rules: r0_c8, r0_c9, r0_c10, r0_c11, r4_c16, r5_c14, r5_c16, r5_c18. Five of them lie in c10-c17: r0_c10, r0_c11, r4_c16, r5_c14 and r5_c16.
  - All 8 are physically inconsistent with a gold layer of >= 0.1 um (next section). I recommend no targeted read on GOLD grounds. That decision belongs to the orchestrator.
- **Detection limit at 2.4 um.**
  - With the frozen rule, 12/12 locations are recovered at t >= 0.05 um Au-equivalent for rho_pap 1.5 (the conservative case). For rho_pap 0.5 they are recovered at t = 0.02-0.3 um.
  - Nothing is recovered at 0.01 um.
  - The frozen rule misses half the cases at 1 um for rho_pap 0.5 (6/12): a saturated plateau defeats the ridge statistic. Those layers still produce a disc-mean Z of >= 109, far above anything on the strip (post hoc, below).
  - Ancient leaf (Pliny: about 0.34 um) and shell gold are therefore well above the E2 limit.
- **E1 (1.129 um L1): INSENSITIVE, which is not the same as absent.**
  - The best sensitivity is 3/12 at any thickness. It fails because the L1 build takes a per-1.129 um-slice clip followed by a 2x mean, and together with the unsharp mask's dark lobes that blunts the ridge statistic.
  - E1 scores are reported, but they rule nothing out.
- **K-edge.** No usable Au-specific scan pair exists.
  - The only discriminating pair, 45.5 um 74 + 110 keV, has no published transform for the 110 keV volume.
  - 78 + 137 keV at 2.4 um has an Au specificity of only 1.19x, and the 137 keV ROI covers 3.0 % of the strip.

## Numbers
| | C1 (ctrl, 1.129) | E1 | C2 (ctrl, 2.4) | E2 |
|---|---|---|---|---|
| tiles scored | 64 | 60 | 168 | 160 |
| tau (Z, grey) | 95.5 | same | 63.75 | same |
| A_p99 bar (mm2) | 0.463 | same | 0.502 | same |
| tiles over bar | (1 % by construction) | 3 (r4_c14-c16, f_in 0.71-0.78) | | 16 |
| max tile Z anywhere | 117.3 | 130.5 | 87.4 | 93.6 |
| hotspots, DECL-P4-10 rule | | 0 | | 0 |
| candidates, DECL-P4-12 item 3 | | 0 | | 8 |

- E2 over-bar tiles:
  - hot area 0.52-1.27 mm2 (a planted letter adds a median of 1.9-5.5 mm2 of new hot area at t >= 0.05 um, minimum 0.97);
  - largest connected component 0.05-0.31 mm2;
  - tile Z_max 75.9-87.8.
- **Physical-consistency check (post hoc, not part of the frozen rule).** The same detector on planted gold gives a minimum Z_max in the glyph region of:
  - E2, rho 1.5: 83.5 at 0.05 um, **154.5 at 0.1 um**, 214.4 at 0.3 um, 202.1 at 1 um;
  - E2, rho 0.5: 98.3 at 0.02 um, 109.0 at 1 um.
  - The highest Z anywhere on the E2 strip is 93.6, and in c10-c17 it is 83.4. **No letter-scale gold layer of >= 0.1 um (rho 1.5), or of 0.02-1 um (rho 0.5), exists in the scored E2 area.** That area is about 62,400 mm2 of usable surface at 4.8 um, 25,100 mm2 of it in c10-c17.
  - E1 injected Z_max values (77-117) overlap the natural E1 range (max 130.5), so E1 rules nothing out.
- The E2 excess over the control (75 % vs 45 % of tiles with any hot area; median tile Z_p50 30.2 vs 27.6) is a strip-wide shift. It is not localised, and it is concentrated in known-text r0 and in labelled-adjacent tiles. Carbon ink visible as 10-20 um bright deposits (Angelotti et al. 2026, via DECL-P4-12) is a thin bright layer too. The ridge responds to it weakly, which is why both controls are known-text strips.
- False positives: a virtual glyph on uninjected patches passes the criterion 0/12 times on the unrotated patch and 0/12 on rot-90, in every material. The tile score is rotation-invariant, so the tile-level rot-90 null equals the unrotated control by construction.

## What was done
1. MEMO.md (commit 74881a4): Au attenuation (xraylib); partial-volume contrast; the Paganin (delta/beta 500/1000) and unsharp (x4) chain taken from the published metadata; artefacts; attestation (no Greek roll of the 3rd c. BC-1st c. AD with gold writing known to me; the prior is a few % at most). kedge_inventory.json.
2. Detector core fixed before any number (dd238a3).
   - v1 was replaced by v2, the thin-layer ridge, after a single control pilot injection showed v1 insensitive. That design iteration is disclosed in detector_core.json.
   - params.json was frozen from the controls only at 28ffd2e (sha256 84ab70b9...), before any title-strip number.
3. Injection (injection/): 12 counted locations per material, in 4 materials (C1, E1, C2, E2), each with 6 thicknesses x 2 papyrus densities.
   - The glyphs are Greek capitals 2-4 mm tall with strokes of 0.3-0.6 mm.
   - The model uses Paganin-mismatch and unsharp transfer, sub-slice clipping and partial-volume occupancy.
4. Scoring: scores.json and hotspots.json.
   - Z maps recomputed from the stored block sums match the stored Z (all tiles).
   - Flags: E1 uses excl_d_a (sha256 c1b6f222...); E2 uses excl_a_union_e2 (bcfd8564...).

## Limits, disclosed
- The transfer model is an approximation: a separable 3-D approximation, a single 78 keV energy for a polychromatic beam, and an unknown papyrus density (bracketed at 0.3-1.5 g/cm3; 1.5 is conservative).
- The results cover only +-20 um around the traced mesh, only mesh-valid pixels, and only in-scan pixels. Untraced surfaces are not covered.
- Imitation "gold" inks without Au (orpiment, bile, saffron) and organic binders alone are invisible to this channel.
- Sub-siblings e1 and e2 hit the account session limit before doing any work. The parent ran all scoring itself (SUBSIBS.md).
