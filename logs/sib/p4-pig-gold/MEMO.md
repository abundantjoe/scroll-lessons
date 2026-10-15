Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-gold research memo: GOLD family (RULES.md DECL-P4-10 item 1)

Builder role only. No image, tile or CT pixel has been opened, viewed or described. The numbers below come from
tabulated physics (tools/sib/p4-pig-gold/memo_numbers.py -> memo_numbers.json) and from the **published scan
metadata** (metadata.json of each PHercParis4 volume on the open-data bucket; sha256 prefixes in section 5). No
title-strip number exists at the time of writing.

Evidence grades used below: **[T]** tabulated or computed physics; **[M]** published scan metadata; **[D]** measured
on our data by another sibling (p4-highz physics.json, numbers only); **[L]** literature, cited; **[E]** my estimate,
labelled as such.

## 1. Gold as a pigment: forms, thickness, survival

- **Forms.**
  - Gold leaf: gold beaten to sub-micron leaf and laid on a mordant or size.
  - Shell gold (chrysography "ink"): gold leaf ground with honey or salt, washed, and bound in gum.
  - Imitation gold "inks": several recipes in the Leiden and Stockholm papyri (P. Leid. X, P. Holm.; Egypt, c. 3rd-4th c. AD) "write in gold" with **no gold at all**. They use orpiment (As2S3), bile, saffron or tin alloys [L: Caley 1926; Halleux 1981]. Orpiment-based letters would be As-bearing (Z 33) and far weaker in CT than Au. That is out of scope here and disclosed.
- **Leaf thickness.**
  - Pliny (NH 33.61-62) says one uncia of gold was beaten into >= 750 leaves, each 4 digits square. With 1 uncia = 27.3 g, 1 digit = 1.85 cm and rho(Au) = 19.32 g/cm3, that gives a mean leaf thickness of **0.34 um** [L+T; computed in memo_numbers.json].
  - Egyptian and Roman leaf is commonly reported at about 0.2 to a few um, thicker than modern leaf (about 0.1 um) [L: Ogden 2000; Nicholson and Shaw eds.].
- **Shell gold.**
  - Particles are flakes of about 1-10 um. A dried stroke is a few um thick, with the gold filling part of the gum matrix.
  - What CT sees is the **areal density**, the Au-equivalent thickness t_eq. For shell gold I estimate t_eq at about 0.3-3 um [E].
  - All thicknesses below are Au-equivalent thicknesses, so they cover leaf and shell gold alike.
- **Survival.**
  - Gold is chemically inert, and it melts at 1064 C.
  - At the 300-400 C of the AD 79 surge (DECL-P4-6), under reducing conditions, gold neither oxidises nor migrates.
  - The organic binder (gum, egg, honey) carbonises. Leaf or flakes then sit on or in the carbonised surface layer. They may crack, delaminate or fold with the sheet, but the Au mass stays where it was.
  - Gold is therefore the pigment most certain to survive, **if it was ever there**.

## 2. Attenuation at the Paris 4 scan energies [T]

Values are from xraylib 4.3.0 total cross sections (Schoonjans et al. 2011; equivalent to NIST XCOM / Hubbell and Seltzer within a few %). Densities: Au 19.32 g/cm3; carbonised papyrus modelled as cellulose C6H10O5 with rho_pap bracketed at 0.3-1.5 g/cm3.

| E (keV) | mu/rho Au (cm2/g) | mu Au (1/cm) | mu/rho cellulose | mu_Au / mu_pap (rho 0.5) | (rho 1.5) | delta/beta Au |
|---|---|---|---|---|---|---|
| 74 | 2.655 | 51.3 | 0.178 | 576 | 192 | 83 |
| 78 | 2.327 | 45.0 | 0.175 | 514 | 171 | 89 |
| 110 | 4.051 | 78.3 | 0.158 | 993 | 331 | 37 |
| 137 | 2.331 | 45.0 | 0.148 | 611 | 204 | 52 |

- The Au K-edge is at **80.725 keV** (xraylib EdgeEnergy; Deslattes et al. 2003). At the edge, mu/rho(Au) jumps from 2.14 to 8.88 cm2/g, a factor of 4.15.
- Hg (83.10 keV) and Pb (88.00 keV) lie just above the Au edge.
- Carbon and cellulose have no edge anywhere in 20-200 keV. Their mu/rho falls smoothly, by 0.89x from 74 to 110 keV.
- Au is 170-860x more attenuating per unit volume than carbonised papyrus at 78 keV, over the whole density bracket. In phase (delta) it is only 9-47x.

## 3. What the published reconstructions do to a thin gold layer [M]+[T]

The published metadata.json of each volume gives these facts, which the memo relies on.

- **Beam.** BM18 (ESRF), a filtered polychromatic beam; the "energy" field is the nominal (mean) energy.
  - 1.129 um (20260608103018): filters sapphire 1 mm + Ag 0.1 mm + Mo.
  - 2.4 um 78 keV (20260411134726) and 2.4 um 137 keV: sapphire 5+15 mm and **Au 0.1 mm**.
  - The Au filter removes photons just above 80.7 keV from the 2.4 um beams, so the Au K-edge jump is under-represented in those spectra.
  - The effective mu of gold in a polychromatic beam with mean 78 keV is still >= the 78 keV value, because part of the spectrum lies above the edge where Au absorbs 4x more. The 78 keV mono value used below is therefore **conservative**.
- **Phase retrieval.** Paganin, applied in projections, then GHBP reconstruction.
  - delta/beta = 500 (1.129 um), 1000 (2.4 um 78 keV), 2000 (137 keV), 10 (45.5 um).
  - Then an unsharp mask of coefficient 4 with a Gaussian sigma of 2.5 px (1.129 um) or 1.2 px (2.4 um 78 keV).
- **Grey scale.** uint8 = linear window of the f32 reconstruction.
  - 1.129 um: f32 window [-0.030, 0.145], so f32 = 0 (air) is grey 43.7 and grey 255 is f32 = 0.145.
  - 2.4 um 78 keV: [-0.04, 0.22], so air is grey 39.2.
  - p4-highz measured the sheet-slab median at grey 80 (control) and 77 (E1) [D]. Papyrus therefore sits about 36 grey above air, and saturation (255) is reached at about **5.8x the papyrus value** in f32.
  - The voxel fraction already at 255 is 0.030 % in the control sheet slab and 0.021 % in E1 [D].

Consequences for a gold layer of Au-equivalent thickness t:

1. **Linearity and conservation.**
   - The projected Au path is at most mu*t = 45 /cm x 2e-4 cm = 0.009 for t = 2 um at normal incidence, so projections stay in the linear regime.
   - The Paganin filter 1/(1 + pi*lambda*z*(delta/beta)*k^2) has DC gain 1. The *depth integral* of the grey excess over the layer is therefore conserved: integral = dG_pap * (t / voxel) * mu_Au/mu_pap, where dG_pap is about 36 grey.
2. **Blur.**
   - The layer is spread over the Paganin length L = sqrt(lambda*z*(delta/beta)/(4 pi)): 12 um at 1.129 um and 17 um at 2.4 um.
   - Gold's own phase term (delta/beta = 89 < 500) makes the net transfer for gold (1 + a*89 k^2)/(1 + a*500 k^2), which does not tend to 0. Gold keeps a sharp component of about 18 % (1.129 um) or 9 % (2.4 um).
   - The unsharp mask then boosts edges x5 at high k. This produces over- and undershoot (dark halos) of a few voxels around dense layers.
3. **Partial-volume contrast.** dG is the unblurred single-voxel increment; "int" is the depth integral in grey x slices; "mean19" is the mean increment over a 19-slice (+-20 um) slab.

| voxel | t = 0.1 um (rho_pap 0.5 / 1.5) | t = 0.5 um | t = 2 um |
|---|---|---|---|
| 1.129 um native | dG 1651 / 550 | 8256 / 2752 | saturated |
| 2.258 um (E1 L1 surface volume) | dG 826 / 275; int 826 / 275; mean19 43 / 14 | dG 4128 / 1376; mean19 217 / 72 | dG 16513 / 5504; mean19 869 / 290 |
| 2.4 um (E2) | dG 873 / 291; mean19 46 / 15 | dG 4364 / 1455; mean19 230 / 77 | dG 17455 / 5818; mean19 919 / 306 |

   - The headroom to saturation is 255 - 80 = 175 grey. Even 0.1 um of gold exceeds it at the unblurred voxel level for any papyrus density.
   - After the Paganin blur (L about 5 slices at 2.258 um) the peak drops, by roughly the blur factor, to about 50-170 grey above papyrus for t = 0.1 um. t >= 0.5 um saturates over several slices.
   - **Prediction:** leaf of 0.3 um (Pliny's figure) or more, and shell gold, would appear as a mm-scale, depth-thin sheet of saturated or near-saturated voxels on the papyrus surface. Clipping at 255 destroys the conserved integral, so a detector must use both the peak (saturation fraction) and the integral.
4. **Detection limit, anticipated.**
   - A 0.02-0.05 um layer (thinner than any ancient leaf) gives a mean19 increment of about 3-20 grey, comparable to papyrus texture at stroke scale.
   - I therefore expect the detection limit near 0.02-0.1 um [E]. Injection-recovery (step 3) measures it; this sentence is a prediction, not a result.

## 4. Artefacts to expect near dense gold grains or leaves [T]+[L]

- **Streaks and beam hardening.** When the beam is tangent to a leaf, the chord through the gold reaches the stroke width, 0.3-0.6 mm. Then mu*L is 1.3-2.7, the polychromatic log is nonlinear, and it produces dark and bright streaks along the tangent [L: De Man et al. 1999; Barrett and Keat 2004]. In a flattened surface volume these streaks lie at about the leaf's depth, along the local sheet tangent. Two streak signatures should be absent for real papyrus text: in-sheet "tails" that extend a stroke beyond its end, and a depth-symmetric dark band.
- **Unsharp-mask halos.** A negative ring of a few voxels around bright objects, both in-plane and in depth. A gold layer may therefore darken the voxels just above and below it. This affects any column-median baseline, and the detector is designed to use a column median over +-20 um, which is robust to a thin band.
- **Paganin mismatch.** delta/beta(Au) = 89 is below the recon value of 500-1000. Gold is under-regularised and keeps residual edge fringes (item 3.2).
- **Saturation.** uint8 clipping at 255 removes the integral. Detection must count saturated voxels explicitly.
- **Ring artefacts and mosaic seams.** The 1.129 um volume is a 19-tile mosaic. Rings are centred on each tile's rotation axis and can create arcs of elevated grey. They are not surface-bound and are not mm-letter-shaped, and the gap-slab null (same detector 60-120 um off-sheet) tests for them.
- **Natural dense inclusions (false positives).** Volcanic-ash and mineral grains (Fe-Ti oxides, pumice fragments), and Pb in some Herculaneum inks (Brun et al. 2016). These are grains of 1-50 um, not planar mm-scale layers. The 0.03 % saturated voxels already present in the control are such grains or noise; they set the false-positive floor.

## 5. Scans bracketing the Au K-edge (80.7 keV) [M]

Inventory of PHercParis4/volumes (bucket listing 2026-09-26). The metadata.json sha256 prefixes are in kedge_inventory.json (step 2).

| volume | px | energy | Paganin delta/beta | registration (transform.json) |
|---|---|---|---|---|
| 20260310170716 | 45.532 um | 74 keV | 10 | to PHerc4Paris-20230205180739 |
| 20260310173927 | 45.532 um | 110 keV | 10 | **none published** |
| 20260323153942 (ROI1) | 2.4 um | 137 keV | 2000 | to PHercParis4-20230205180739 |
| 20260411134726 | 2.4 um | 78 keV | 1000 | to PHercParis4-20230205180739 |
| 20260608103018 | 1.129 um | 78 keV | 500 | to 2.4um_PHerc-Paris4 (= 20260411134726) |

- **Pair A: 74 + 110 keV at 45.5 um.** It brackets the Au (and Hg, Pb) K-edges.
  - At 45.5 um, a 0.34 um leaf fills 0.75 % of a voxel. That is about 1.9x papyrus mu at 110 keV and about 1.3x at 74 keV (rho_pap 0.5, mono values).
  - The Au 110/74 ratio is 1.53, against 0.89 for papyrus. A leaf-bearing voxel would therefore show a ratio about 1.4x papyrus's, but only if the stroke covers a whole 45 um voxel in-plane, which 0.3-0.6 mm strokes do.
  - Blockers: the 110 keV volume has **no published transform**, and only the 74 keV scan has surface volumes (segments 20260623141924 and 20260701183124 w010-027 both list a 45.532um-11.0m-74keV surface volume).
  - A K-edge map would need our own registration of 110 to 74 keV. The two scans were acquired 35 min apart with the same geometry, so a rigid refinement is plausible. It also needs its own declaration (DECL-P4-6-A1 item 2).
- **Pair B: 78 + 137 keV at 2.4 um.** It formally brackets the edge.
  - For Au the mono ratio mu(137)/mu(78) is 1.00 (above-edge 137 keV has fallen back to the below-edge 78 keV value), against 0.84 for papyrus. The contrast is weak (1.19x), and the Au filter in both beams depletes the above-edge photons.
  - ROI1 covers only 15.9 mm in z. Its coverage of the w010-027 strip is computed numerically in step 2.
- **Conclusion.**
  - Pair A is the only K-edge-discriminating pair. It needs registration and a separate declaration, and it has 45 um resolution.
  - Pair B is not K-edge-specific.
  - The primary GOLD test is therefore density plus geometry: a thin, planar, saturated layer at mm letter scale on the sheet.

## 6. Attestation of gold writing [L]; periods kept separate

**Greek papyri and rolls, 3rd c. BC - 1st c. AD (the relevant period)**
- I know of no extant Greek literary roll of this period with a title or text written in gold, and no published report of Au in Herculaneum inks.
- Herculaneum titles that have been read are written in the same black ink as the text, sometimes in larger letters, with decorative strokes or stichometric notes. Del Mastro (2014) catalogues all Herculaneum titles and bibliological annotations; none is reported as gilded, to my knowledge. Chemical and XRF studies of Herculaneum ink report carbon, and in some fragments Pb, not Au (Brun et al. 2016; Tack et al. 2016).
- Literary report: the Letter of Aristeas (Ps.-Aristeas section 176, 2nd c. BC) describes Hebrew Torah rolls brought to Ptolemy II "written in gold in Jewish letters". This is a literary claim about a Hebrew roll, not an extant Greek object. Later rabbinic tradition (Soferim 1.8-9; b. Shabbat 103b) forbids writing the divine name in gold, which implies the practice existed.
- Pliny's NH 33 discusses gold leaf and gilding at length. It gives no instance of gold titles on Greek rolls in the 1st c. AD.

**Later: Roman imperial to Byzantine; not evidence for PHerc. Paris 4**
- The Historia Augusta (Maximini duo 30.4, written in the late 4th c.) reports a Homer written in gold letters on purple parchment given to the young Maximinus (3rd c.).
- Jerome, Preface to Job (c. 390s), criticises books written "in gold and silver letters on purple parchment".
- Gold recipes in P. Leid. X and P. Holm. (3rd-4th c. AD), many of them imitations.
- Purple codices with gold or silver script, 6th c.: Codex Argenteus (Uppsala), Rossano Gospels, Vienna Genesis, Codex Petropolitanus Purpureus.
- Gold titles and initials in middle Byzantine codices.

**Prior for PHerc. Paris 4 (a Herculaneum Greek roll, before AD 79)**
- A gold title is **improbable** [E]. I would put it at a few % at most; the research sibling p4-research should refine that.
- Gold is nonetheless the cheapest pigment to test, and the one most decisively testable: inert, and hundreds of times denser than papyrus. The test does not depend on the prior.

## 7. Detector design implied by 1-4 (frozen in params.json, step 2)

- **Primary statistic.** A thin, planar, in-sheet, near-saturating layer at stroke scale.
  - Level 0, +-20 um slab (DECL-P4-10 item 2).
  - Per column, the peak excess of the 3-slice running mean over the column median, plus a saturation flag.
  - Both are smoothed in-plane at stroke scale (0.3-0.6 mm strokes).
  - Thresholds come from the control strips only. The same statistic is computed on gap slabs 60-120 um off-sheet for the in-sheet fraction.
- **Validation.**
  - Injection-recovery with a Paganin-plus-unsharp transfer model for gold (item 3), at t = 0.02, 0.05, 0.1, 0.3 and 1.0 um and rho_pap bracket values.
  - False positives on the control and on the gap-slab and rot-90 nulls. The primary statistic is rotation-invariant, so the rot-90 null reproduces the unrotated values by construction; this is reported, not hidden.

## References
- Barrett J.F., Keat N. (2004) Artifacts in CT: recognition and avoidance. RadioGraphics 24:1679-1691.
- Brun E. et al. (2016) Revealing metallic ink in Herculaneum papyri. PNAS 113:3751-3754.
- Caley E.R. (1926) The Leyden Papyrus X. J. Chem. Educ. 3:1149-1166; (1927) The Stockholm Papyrus, J. Chem. Educ. 4:979-1002.
- De Man B. et al. (1999) Metal streak artifacts in X-ray computed tomography: a simulation study. IEEE Trans. Nucl. Sci. 46:691-696.
- Del Mastro G. (2014) Titoli e annotazioni bibliologiche nei papiri greci di Ercolano. Cronache Ercolanesi Suppl. 5, Napoli.
- Deslattes R.D. et al. (2003) X-ray transition energies. Rev. Mod. Phys. 75:35-99.
- Halleux R. (1981) Les alchimistes grecs I: Papyrus de Leyde, Papyrus de Stockholm, Recettes. Paris: Les Belles Lettres.
- Hubbell J.H., Seltzer S.M. NIST Standard Reference Database 126: X-ray mass attenuation coefficients.
- Nicholson P.T., Shaw I. (eds., 2000) Ancient Egyptian Materials and Technology, Cambridge (Ogden J., "Metals").
- Paganin D. et al. (2002) Simultaneous phase and amplitude extraction from a single defocused image of a homogeneous object. J. Microsc. 206:33-40.
- Pliny the Elder, Naturalis Historia 33.61-62 (gold beating), 33 passim (gilding).
- Ps.-Aristeas, Letter to Philocrates 176.
- Schoonjans T. et al. (2011) The xraylib library for X-ray-matter interactions. Recent developments. Spectrochim. Acta B 66:776-784.
- Tack P. et al. (2016) Tracking ink composition on Herculaneum papyrus scrolls: quantification and speciation of lead by X-ray based techniques and Monte Carlo simulations. Sci. Rep. 6:20763.
- Jerome, Prologus in libro Iob; Historia Augusta, Maximini duo 30.4.

Citation humility: the physics numbers are reproducible from memo_numbers.py. The historical citations are from my knowledge and have not been re-checked against the texts in this session. Page and section numbers may need correction by p4-research.
