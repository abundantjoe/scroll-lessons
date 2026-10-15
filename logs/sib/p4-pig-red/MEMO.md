Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-red MEMO: the RED family (cinnabar HgS, red lead Pb3O4 -> PbO) for P4-J (RULES.md DECL-P4-10 item 1)

Written 2026-09-26 before any P4-J number, parameter or title-strip value exists. No image, tile or CT pixel was opened or viewed. The only CT-derived numbers used here are the strip-level percentiles already pushed by p4-highz (logs/sib/p4-highz/physics.json at db96abe). Attenuation values come from `tools/sib/p4-pig-red/xcom.py` and are stored in `xcom.json` in this directory.

Confidence tags: **[V]** means verified in this session against the cited source (abstract or full text). **[H]** means handbook or textbook knowledge I did not re-verify here. **[E]** means my own estimate, with its assumptions stated.

## 1. Thermal and chemical stability at 300-400 C under reducing conditions

Carbonisation temperature. The papyri were carbonised at about 300-320 C [V: Scientific Reports 2025, "Pulsed thermographic analysis of Herculaneum papyri", citing the literature]. At Villa dei Papiri, the pyroclastic density currents (PDCs) were about 350 C at first impact. Later deposits were at 465-390 C and 350-315 C [V: Giordano et al. 2018, Earth Planet. Sci. Lett., "Thermal interactions of the AD79 Vesuvius PDCs and their deposits at Villa dei Papiri"]. The rolls were carbonised, not burned, so the atmosphere was oxygen-poor.

Cinnabar, HgS:
- Cinnabar changes to metacinnabar (black, cubic HgS) at about 345 C. This is a change of crystal structure only: the composition stays the same and the density barely changes (8.10 -> 7.71 g/cm3) [V: Perez-Diez et al. 2021, Anal. Chem. 93:15870, "When Red Turns Black"; densities H].
- On Pompeian wall paintings, the 79 AD thermal impact caused some Hg sublimation, but metacinnabar was not detected by XRD [V: same source]. Earlier blackening was traced to Hg-Cl compounds and gypsum, forming a ~5 um black crust over intact cinnabar [V: Cotte et al. 2006, Anal. Chem. 78:7484].
- Significant decomposition or sublimation of HgS needs higher temperatures or oxidising roasting (Hg vapour + SO2) [H].
- Consequence: a cinnabar title would keep essentially all of its Hg at 300-400 C. It may have turned black to the eye, which is consistent with "no visible red" and does not affect CT. A partial loss of Hg by sublimation from exposed surfaces cannot be excluded [V: Perez-Diez 2021]. Inside a tightly rolled inner winding, sublimation is the least likely.

Red lead, Pb3O4:
- Red lead decomposes to PbO + O2 above about 500 C in air [V: thermogravimetric literature, J. Therm. Anal.; H], which is above the Herculaneum range.
- Under reducing conditions with carbon, PbO can be reduced towards metallic Pb at higher temperatures [H].
- Whatever the phase (Pb3O4, PbO or Pb), the lead stays in place. The CT sees mass, not phase: the table in section 3 shows these three differ by only about 10 % in mu/rho at 78 keV, and by more in mu through their densities.
- Consequence: all lead stays where it was written.

Organic reds (lakes, madder, kermes) carbonise like the substrate and are invisible to this detector. This blind spot is disclosed, as in DECL-P4-6.

## 2. Pigment grain size and layer thickness

Grain size:
- In Roman-period Egyptian red inks on papyrus, the colourant was hematite. It occurs as fine particles below the 1-2 um beam size plus larger particles of "some tens of microns" [V: Christiansen et al. 2020, PNAS 117:27825, Tebtunis temple library, c. 100-200 CE].
- Ground cinnabar and red lead pigments are typically about 1-20 um [H].
- Consequence: the pigment is granular. A thin stroke is a patchy layer of grains at 1-20 um scale, not a continuous film.

Penetration: ink penetrates the papyrus fibres thoroughly [V: Christiansen 2020]. The pigment may therefore be spread over a few um to tens of um in depth near the recto surface, rather than lying as an ideal surface film.

Layer thickness: I found no verified measurement of red-ink layer thickness on ancient papyrus. The only quantitative Herculaneum anchor I could verify is a mass thickness:
- Brun et al. 2016 [V: PNAS 113:3751] measured lead in the ink of two Herculaneum fragments at up to 84 +- 5 ug Pb/cm2.
- As solid PbO (9.53 g/cm3, 92.8 % Pb by mass), that equals a layer 0.095 um thick [E]. A dense-ink signal can therefore be sub-micron in equivalent thickness.

The injection-recovery (item 3) therefore spans equivalent solid thicknesses from 0.1 um to 15 um. DECL-P4-6 assumes 5-30 um for a pigment ink. For thin brushed or reed-written ink with a binder, I treat 2-5 um of *pigment-equivalent* thickness as the plausible centre. That value [E] is the one where DECL-P4-10's sensitivity >= 0.8 bar is applied.

## 3. Mass attenuation (xraylib 4.3 CS_Total_CP; the same Scofield/Hubbell/EPDL tabulations as NIST XCOM) at the Paris 4 scan energies

The published PHercParis4 volumes are listed in the bucket under `PHercParis4/volumes/`, as seen by this sibling via S3 ListObjects:

| Volume | Energy |
|---|---|
| 20260310170716 45.532 um | 74 keV |
| 20260310173927 45.532 um | 110 keV |
| 20260323153942 2.400 um | 137 keV |
| 20260411134726 2.400 um | 78 keV |
| 20260608103018 1.129 um | 78 keV |

Surface volumes of w028-037 exist at 1.129 um (78 keV), 2.4 um (78 keV) and 45.532 um (74 keV). p4-highz scans.json was not yet pushed when this memo was written; this list should be reconciled with it.

K edges: Hg 83.10 keV, Pb 88.00 keV, Au 80.72 keV (xraylib EdgeEnergy).

mu/rho in cm2/g, and mu in 1/cm at the given density:

| material (rho) | 74 keV | 78 keV | 110 keV | 137 keV | mu @78 keV |
|---|---|---|---|---|---|
| HgS cinnabar (8.10) | 2.406 | 2.111 | 3.601 | 2.084 | 17.1 |
| Pb3O4 red lead (8.92) | 2.683 | 2.353 | 3.969 | 2.300 | 21.0 |
| PbO litharge (9.53) | 2.743 | 2.405 | 4.061 | 2.351 | 22.9 |
| Pb metal (11.34) | 2.941 | 2.577 | 4.363 | 2.522 | 29.2 |
| Fe2O3 hematite (5.26), reference | 0.551 | 0.492 | 0.263 | 0.197 | 2.59 |
| char proxy C.70 O.25 H.05 by mass | 0.174 | 0.171 | 0.155 | 0.145 | 0.171 x rho |
| cellulose C6H10O5 | 0.178 | 0.175 | 0.158 | 0.148 | |
| graphite / carbon ink C | 0.165 | 0.162 | 0.147 | 0.138 | |

Carbonised papyrus density is not measured for Paris 4. I bracket it at rho_pap = 0.3-1.2 g/cm3 [E], which gives mu_pap = 0.05-0.21 /cm at 78 keV. Carbon ink differs from char by < 10 % in mu/rho, so its contrast comes from density and layer thickness only. That is why carbon ink is nearly invisible.

- Linear attenuation of HgS at 78 keV is **80-340x** that of carbonised papyrus. For PbO it is **110-450x**.
- K-edge signatures, for a later declaration only (DECL-P4-6-A1 item 2; nothing computed here):
  - The ratio mu(110)/mu(74) is 1.50 for HgS, 1.48 for PbO and 0.89 for char. A 45.5 um pair brackets both the Hg and Pb edges. It is strongly diagnostic, but coarse: at 45.5 um a 0.5 mm stroke is about 11 px wide.
  - The ratio mu(137)/mu(78) is 0.99 for HgS, 0.98 for PbO and 0.85 for char. The 2.4 um pair also brackets both edges, but at 137 keV the tail of the photoelectric edge has decayed, so the discrimination is only about 15 %. That is weak, but it is at the resolution that resolves strokes.

## 4. Expected voxel contrast at 1.129 um (surface volume at 2.258 um) and at 2.4 um

Gray model [E]: g = g0 + k*mu, with the uint8 volume clipped at 255.
- From p4-highz physics.json, the control's sheet-slab median is 80, its p99.9 is 233 and its p99.99 is 255. 0.030 % of sheet voxels are already saturated. The gap-slab median is 65. True air (g0) is not yet measured; it is bracketed at 0-65.
- Then k = (80 - g0)/mu_pap lies between 73 gray per 1/cm (pessimistic: g0 = 65, rho_pap = 1.2) and about 1600 (optimistic: g0 = 0, rho_pap = 0.3).

Fill fraction needed to saturate. Take a 2.258 um voxel with volume fraction f of HgS (mu 17.1). It reaches 255 from 80 when k*f*17 >= 175:
- pessimistic: f >= 0.14, i.e. 0.32 um of solid HgS per voxel;
- optimistic: f >= 0.0064, i.e. 0.015 um.
- For PbO (22.9/cm) the thresholds are about 25 % lower.

Point spread. The instrument point-spread function (phase contrast at 0.22-0.23 m propagation; reconstruction) spreads a thin layer over several voxels in depth. With a Gaussian depth PSF of sigma = 2 voxels, a laterally extended layer of thickness t has a peak fill of about t/(2.5 sigma). Solid HgS then saturates above t of about 1.6 um (pessimistic) or 0.07 um (optimistic). Below saturation, it still exceeds the control's p99.9 (233) above t of about 1.4 um (pessimistic).

Brun-level lead ink (84 ug Pb/cm2, 0.095 um PbO-equivalent) would add about +70 to +1500 gray over a single-voxel layer before the PSF. This is **a testable consequence for the control**: if the w028-037 black ink carried Brun-level Pb, the in-sheet extreme voxels would co-localise with the official ink map.

p4-highz found that the density of voxels > 233 is the same in the sheet slab and in the gap slabs (control 0.00097 vs 0.00099). The existing saturated voxels are therefore not surface-bound as a population. That is a first hint that the control's ink is not strongly lead-bearing at detectable levels. It is not proof, because a sparse signal could hide in a population average. The detector's control false-positive rate (item 3) is the direct test.

At 2.4 um, the same arithmetic applies with a 2.4 um voxel and that scan's own gray mapping (to be measured on the w028-037 2.4 um control surface volume, which exists).

Conclusion [E]: at the plausible centre (2-5 um pigment-equivalent thickness), a cinnabar or red-lead stroke 0.3-0.6 mm wide would be a **laterally extended, depth-thin sheet of saturated or near-saturated voxels**. Per letter that is about 10^5-10^6 px of 2.258 um at the recto surface. Isolated saturated voxels occur at 3e-4 anyway, uniformly in depth. The discriminant is therefore **lateral connectedness at the 0.1-1 mm scale plus depth-thinness near the mesh**, not brightness alone. That is the design basis of params.json (item 2).

Caveats [E]:
- Beam hardening and streaks from dense grains, and phase-retrieval edge effects, can make the true response non-linear.
- The organizers' uint8 windowing is unknown.
- That is why injection-recovery reports the pessimistic calibration as the primary result.

## 5. Attestation of red ink in Greek papyri, 3rd c. BC to 1st c. AD (kept separate from later evidence)

Contemporary or near-contemporary evidence:
- Red ink on papyrus in Egypt has a pharaonic tradition of headings and rubra [V: general; Christiansen 2020 introduction].
- In the Roman-period Tebtunis temple library (c. 100-200 CE, Egyptian-language texts, just after the target window), the red inks were iron-based: ochre or hematite. Lead was present as a drier. **Neither cinnabar nor red lead was detected** [V: Christiansen 2020 PNAS]. This is the closest analysed papyrus corpus in time. Its red is the FE family (p4-pig-fe), not RED.
- Minium and cinnabar are both attested as pigments in Greco-Roman Egypt, including cinnabar in a Ptolemaic funerary (Book of the Dead) papyrus described as its earliest use there. They are painting and funerary contexts, not Greek literary titles [V: search summary of the pigment literature; exact citation to be pinned by p4-research].
- Roman sources describe red ink made from cinnabar, red lead or red ochre as used sparingly for important words [V: secondary, encyclopaedic; primary sources such as Pliny NH 33 and 35 are to be pinned by p4-research].
- Herculaneum: the black ink of at least some PHerc fragments contains lead at up to 84 ug/cm2 [V: Brun et al. 2016].
- To my knowledge, Herculaneum end-titles read so far are in the same black ink as the text [H, echoed in the DECL-P4-6-A1 orchestrator note]. I know of no published red-ink title in a Herculaneum roll. That is an absence of evidence at my level of knowledge, not evidence of absence; p4-research owns this question.

Later evidence (not used for the prior):
- Rubricated titles and initials in red (cinnabar, minium) are standard in late-antique and Byzantine Greek codices and in medieval manuscripts. Gold and blue conventions belong there too (DECL-P4-6-A2 note).

Prior for RED on the Paris 4 title:
- Low to moderate for any red, and lower still for Hg/Pb red specifically: the nearest analysed papyrus reds are Fe-based.
- The detector does not depend on the prior. An iron red would give about 7x weaker contrast per unit thickness than HgS (mu 2.6 vs 17-23/cm), and that case is p4-pig-fe's.

## 6. Validation plan implied (frozen in params.json before any title-strip number)

- **Detector:** in-sheet (+-20 um) extreme voxels >= the control's in-sheet p99.99, then 2-D block density, then connected components at letter-stroke scale, then planarity (depth spread) and distance to the mesh.
- **Injection-recovery:** HgS and PbO strokes of Greek capitals (2-4 mm tall, 0.3-0.6 mm stroke), at t = 0.1, 0.5, 2, 5 and 15 um, with a granular fill. Pessimistic (primary) and optimistic calibrations, with a Gaussian PSF, planted into real CT at >= 10 control and >= 10 title-strip locations.
- **False positives:** every control tile, and the rot-90 nulls.
- **Consistency check:** in-sheet fraction vs gap slabs for any hotspot.

## Sources

- Christiansen T. et al. 2020, PNAS 117:27825. https://www.pnas.org/doi/10.1073/pnas.2004534117
- Brun E. et al. 2016, PNAS 113:3751. https://www.pnas.org/doi/10.1073/pnas.1519958113
- Cotte M. et al. 2006, Anal. Chem. 78:7484. https://pubs.acs.org/doi/10.1021/ac0612224
- Perez-Diez S. et al. 2021, Anal. Chem. 93:15870. https://pubs.acs.org/doi/10.1021/acs.analchem.1c02420
- Giordano G. et al. 2018, Earth Planet. Sci. Lett. https://www.sciencedirect.com/science/article/abs/pii/S0012821X18301456
- Pulsed thermographic analysis of Herculaneum papyri, Sci. Rep. 2025. https://www.nature.com/articles/s41598-025-19911-w
- Red lead thermal decomposition, J. Therm. Anal. https://link.springer.com/article/10.1007/BF01912896
- Schoonjans T. et al. 2011, Spectrochim. Acta B 66:776 (xraylib).
