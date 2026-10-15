Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-cu research memo: Cu blue/green pigments (DECL-P4-10 item 1, family CU)

Written 2026-09-26, before any detector parameter or title-strip (w010-027) number exists. Numbers only: no image, tile or CT pixel was opened or viewed. The only CT numbers used here are a grey-level histogram of the known-text **control** strip (`calib.json`).

Citation status: **[V]** means checked in this session against a search result or publisher page. **[M]** means from memory: the finding is standard, but the exact bibliographic details were not rechecked here.

## 1. Thermal stability at 300-400 C in a reducing pyroclastic setting

- **Deposition temperature at the Villa dei Papiri.** Two estimates bracket the heat the rolls saw:
  - thermal remanent magnetisation of lithic clasts: ~270 C where the flow mixed with water or wall debris (range 190-300 C), and ~350 C in unmixed deposit (range 300-440 C);
  - charcoal reflectance on wood charred in place (Caricchi et al. 2014), consistent with these.
  - Refs: Giordano G. et al. 2018, *Earth Planet. Sci. Lett.* 490:180-192 [V]; Caricchi C. et al. 2014, *J. Volcanol. Geotherm. Res.* 289:14-25 [V title/journal; pages M].
- **Egyptian blue (cuprorivaite, CaCuSi4O10).**
  - It is made by firing at ~850-1000 C and breaks down only above ~1000-1050 C. At 300-400 C it is chemically and structurally inert, even under reducing conditions, which only matter above ~900 C.
  - It is therefore the Cu pigment most likely to survive exactly as applied: discrete crystalline grains.
  - Ancient Egyptian blue is multiphase: cuprorivaite plus quartz/cristobalite, wollastonite, glass and tenorite (npj Herit. Sci. 2025, "Assessment of process variability and color in synthesized and ancient Egyptian blue pigments" [V]).
  - Refs: Berke H. 2007, *Chem. Soc. Rev.* 36:15-30 [M]; arXiv 2605.27455, "High-temperature instability of artificial cuprorivaite" [V exists].
- **Azurite Cu3(CO3)2(OH)2 and malachite Cu2CO3(OH)2.**
  - Both decompose in overlapping stages between ~250 and ~385 C to tenorite CuO. Malachite loses H2O and CO2 in one step near 380 C; azurite takes two steps.
  - At 300-400 C, therefore, part or all of the pigment converts to CuO. The grains keep all of their Cu and shrink in volume (they lose ~28-31 % of their mass).
  - In a reducing, CO-rich setting, CuO can go further to Cu2O or Cu metal. That would raise the X-ray density even more.
  - Refs: Frost R.L. et al. 2002, *Thermochim. Acta* 390:133-144 [V]; Henmi et al., *Thermochim. Acta* 1984 [V exists]; *Am. Mineral.* 49:1111 (1964) [V exists].
- **Verdigris (Cu acetates).**
  - It decomposes at ~200-300 C to Cu, Cu2O or CuO and loses most of its mass.
  - The product is a finely divided Cu-oxide or Cu residue whose original grain structure is lost, so it is more film-like than granular [M].
- **Blind spot.** Organic blues and greens (indigo, plant greens, copper-protein complexes) carbonise with the substrate. No CT channel sees them.

## 2. Grain size and layer thickness

- **Egyptian blue grain size.** Colour depends on grain size: coarse grains (tens of um) give deep blue, while finely ground material (a few um) is pale.
  - Reported pigment grains run from ~1 um to >100 um. Pigment balls traded in Roman times, from the Pozzuoli production site, measured 15-30 mm (npj Herit. Sci. 2026, the Pompeii "Blue Room" [V]).
  - The DECL-P4-10 working range of 1-50 um is adopted.
- **Paint layer thickness.** The Pompeii "Blue Room" fresco layer averages 185 um [V], but that is wall paint, not ink.
  - For a pen stroke on papyrus, carbon-ink layers are ~5-20 um [M]. A pigment "ink" of coarse grains cannot be thinner than one grain diameter.
  - Plausible ranges for a Cu-pigment stroke:
    - layer: 5-30 um;
    - grain volume fraction in the layer: 0.1-0.5, the rest gum binder;
    - stroke width: 0.3-0.6 mm (DECL-P4-10).
- **Tenorite from azurite or malachite.** Same grain count as the original pigment, but each grain shrinks. Azurite and malachite are ground to ~5-50 um for use [M].

## 3. Mass attenuation at the Paris 4 scan energies and expected voxel contrast

The published PHerc. Paris 4 volumes (bucket listing, 2026-09-26) are:

| Scan | Energy |
|---|---|
| 45.5 um | 74 keV and 110 keV |
| 2.4 um | 137 keV and 78 keV |
| 1.129 um | 78 keV |

E1 (1.129 um scan, stored at 2.258 um) and E2 (2.4 um) are both 78 keV.

Method:
- Mass attenuation coefficients come from NIST SRD 126 elemental tables (Hubbell & Seltzer), log-log interpolated and combined by the mixture rule. The table pages are archived in `nist/`, the calculation is in `tools/sib/p4-pig-cu/physics.py`, and the results are in `physics.json`.
- Densities are handbook values. The char composition (C 78 %, O 15 %, rest H/N/ash) and density (nominal 0.5, range 0.3-0.8 g/cm3) are **assumptions**.

| material | mu/rho 78 keV (cm2/g) | rho (g/cm3) | mu 78 keV (1/cm) | x papyrus (78 keV, nominal) | mu/rho 137 keV |
|---|---|---|---|---|---|
| carbonised papyrus | 0.1725 | 0.5 (0.3-0.8) | 0.086 | 1.0 | 0.1435 |
| carbon ink (dry) | 0.1657 | 1.2 (0.8-1.6) | 0.199 | 2.3 | 0.141 |
| **Egyptian blue** | **0.3196** | 3.07 | **0.981** | **11.4** | 0.169 |
| verdigris | 0.379 | 1.88 | 0.71 | 8.3 | 0.183 |
| azurite | 0.526 | 3.77 | 1.98 | 23 | 0.208 |
| malachite | 0.541 | 3.9 | 2.11 | 24.5 | 0.211 |
| **tenorite CuO** | 0.685 | 6.4 | **4.38** | **51** | 0.237 |
| cuprite Cu2O | 0.742 | 6.1 | 4.53 | 52 | 0.247 |
| quartz (sand) | 0.198 | 2.65 | 0.52 | 6.1 | 0.146 |
| calcite | 0.255 | 2.71 | 0.69 | 8.0 | 0.158 |
| Vesuvian glass / leucite | 0.221 | 2.45 | 0.54 | 6.3 | 0.150 |
| augite (pyroxene) | 0.256 | 3.35 | 0.86 | 10.0 | 0.157 |
| magnetite | 0.505 | 5.18 | 2.62 | 30 | 0.203 |

Consequences:
1. **No elemental specificity.** The Cu K-edge is at 8.98 keV, far below every scan. From 74 to 137 keV, Cu attenuation falls smoothly by the same Compton/photoelectric law as Fe and Ca. No scan pair isolates Cu; unlike Hg, Pb and Au, the CU family has no K-edge test in this dataset.
   - A two-energy (78 vs 137 keV) ratio does rise with effective Z: Egyptian blue 1.89, calcite 1.62, quartz 1.36, char 1.20, CuO 2.89, magnetite 2.49.
   - However, the 137 keV data are 2.4 um only and registration is uninventoried (p4-highz DECL-P4-6-A1 task), so this is noted, not used.
2. **Egyptian blue is as bright as common volcanic minerals.** Its linear attenuation (0.98 /cm) sits between augite (0.86) and calcite (0.69), just above quartz and volcanic glass (0.52-0.54). **Grain intensity alone cannot separate Egyptian blue from sand or ash.** CuO, azurite and malachite relics (2-4.5 /cm) overlap magnetite and hematite.
3. **Expected voxel values.** A control-only calibration probe (`calib.json`: 400 random control chunks, all 116 slices) shows an air/void mode at 41 and a papyrus mode at 109. With a linear grey-to-mu model (v = 41 + (mu/mu_pap) x 68):
   - A voxel fully filled with Egyptian blue maps to ~816, or ~524 if the papyrus density is 0.8. Either way it saturates at 255.
   - The occupancy needed to exceed the frozen p4-highz threshold T_hi = 233 on a papyrus background (109) is **0.18 (0.30 if rho_pap = 0.8)**. That corresponds to an Egyptian blue grain of ~1.6-1.9 um diameter centred in a 2.258 um voxel, before blur.
   - At E2 (2.4 um), the same grain gives about 0.8x the occupancy.
   - Carbon ink, by contrast, is ~2x papyrus at most. Where it is a thin film on papyrus, the gain is well under one grey unit per um. This matches the project's finding that carbon ink is nearly invisible in raw CT.
   - Caveats: phase-contrast edge enhancement and reconstruction filtering are not modelled. The gain is uncertain by ~2.7x because the papyrus density is unknown.
   - **Prediction:** Cu-pigment grains of >= ~2-3 um appear as saturated or near-saturated voxel clusters. Grains of ~1 um are sub-threshold unless clumped.
4. **Existing bright voxels are not rare.** On the control, the p4-highz physics shows:
   - 0.1 % of sheet voxels exceed 233 and 0.03 % sit at 255;
   - these occur at the **same density in the sheet slab as in the gap slabs 60-120 um away** (in-sheet fraction 0.19 vs 0.194 if uniform in depth).
   - So the natural bright-grain population (inclusions, noise) is depth-uniform. A pigment layer would add a depth-localised, laterally stroke-shaped excess.

## 4. Natural bright inclusions that mimic grains, and how to separate them

Sources of bright grains in or on carbonised Herculaneum papyrus:
- **Volcanic ash from the AD 79 pyroclastic flows:** leucite, sanidine, pyroxene and glass shards, 1-100 um. It penetrates between windings, so it is concentrated between layers and on the outer windings.
- **Mineral grains in papyrus manufacture:** Nile silt, and particles trapped when the strips were beaten and pressed.
- **Lead in some Herculaneum black inks:** Brun E. et al. 2016, *PNAS* 113:3751 [M]; Tack P. et al. 2016, *Sci. Rep.* 6:20763 [M]. It would be denser than Egyptian blue and ink-localised.
- **Reconstruction noise and ring or streak residues.**

Separating features, all numerical and fixed in `params.json` before any title-strip number:
1. **Stroke-scale lateral clustering.** Natural inclusions are spatially random at the 0.1-1 mm scale, or clustered along fibres, cracks and layer contacts.
   - A written stroke concentrates grains inside a 0.3-0.6 mm band 2-4 mm long, forming letter-scale clusters of 0.5-5 mm.
   - Test: grain density in 0.1 mm cells, smoothed at stroke scale, against a **local** background of the 3 mm median. The excess must be letter-scale in extent.
2. **On-sheet fraction.** Pigment lies within about +-20 um of the recto surface. Inclusions and noise are depth-uniform (item 3.4).
   - Test: the excess grain count in the cluster footprint, sheet slab (+-20 um) vs gap slabs (60-120 um).
   - DECL-P4-10 requires an in-sheet fraction >= 0.8. The depth-uniform baseline is 19/(19+54) = 0.26.
3. **Grain size and shape.** Components with an equivalent diameter > 50 um, or thicker than 50 um in z, are not Cu-pigment grains. Examples are pumice lapilli, sand grains and large crystals. They are excluded, which leaves the 1-50 um population.
   - Within 1-50 um, shape does not separate pigment from ash at 2.258 um sampling: a 10 um grain spans ~4 voxels. So shape is used only as the size gate.
4. **Carbon-ink control.** On the known-text strip w028-037, carbon letters should not produce grain clusters. If they do (for example Pb-bearing black ink), the control's score distribution absorbs it into the hotspot threshold. This is disclosed in the report.
5. **Nulls.**
   - Rot-90, as declared. The cluster score is isotropic, so rot-90 leaves it unchanged by construction; this is reported as a check, not as independent evidence.
   - A cell-permutation null: grain counts shuffled among valid cells of the same tile. This destroys the spatial clustering and keeps the count distribution.

## 5. Attestation of blue or green ink in Greek papyri, 3rd c. BC to 1st c. AD

Kept separate from later evidence.

- **Greek literary rolls of the period.** I know of **no** published analytical or palaeographic attestation of a blue or green writing ink, in titles or in text, in any Greek literary roll of the 3rd c. BC to 1st c. AD, including the Herculaneum rolls.
  - End-titles of Herculaneum rolls read so far (for example the Philodemus titles) are, as far as I know, in the same black ink as the text [M; the p4-research sibling is compiling this].
  - This is an absence of evidence from a limited, black-ink-dominated corpus. It is not evidence of absence.
- **Coloured inks and pigments in Graeco-Roman Egypt.** Red is the attested accent colour.
  - Rubrics in red on papyri of the Tebtunis temple library (Roman period, ~100-200 AD) are Fe (ochre/hematite) based, with Pb acting probably as a drier: Christiansen T. et al. 2020, *PNAS* 117:27825-27835 [V]. Those are Egyptian (hieratic and demotic) temple texts, not Greek literary rolls.
  - **Egyptian blue on papyrus is attested as a painting pigment, not an ink.** A Ptolemaic Book of the Dead papyrus uses it in blue vignettes, and mixed with goethite in green ones: "Characterisation of the pigments in a Ptolemaic Egyptian Book of the Dead papyrus" [V title; authors/journal M].
- **Egyptian blue at Herculaneum.** It was the standard blue of Campanian wall painting (Pompeii "Blue Room", npj Herit. Sci. 2026 [V]), and it was produced at Pozzuoli on the Bay of Naples [V]. It was therefore materially available in the Villa's environment.
- **Later evidence, not used as a prior.** Coloured (red, gold, blue, green) titles and initials are characteristic of Byzantine and medieval codices, several centuries after AD 79 (DECL-P4-6-A2 orchestrator note).

**Prior for this family:** a Cu-pigment title in PHerc. Paris 4 is **unattested and unlikely**. I put it lower than red (Fe/Pb/Hg). The search is justified only because it is cheap, and because Egyptian blue, if present, is thermally inert and dense enough to be seen. A null result must be reported as "not detected at the measured sensitivity", never as "absent".

## 6. Design consequences (carried into params.json)

- **Intensity band:** voxels > T_hi from the p4-highz frozen control threshold (233 on the 1.129 um L1 scan) up to 255. Egyptian blue saturates, so the family band's upper end is the dtype maximum. Cu relics (CuO) and Fe/Hg/Pb pigments cannot be separated from Egyptian blue by grey value in these data; the CU detector responds to all dense granular pigments.
- **Statistic:** the density of bright voxels belonging to grain-sized components (2 voxels to 50 um equivalent diameter, z-extent <= 50 um), in 0.1 mm cells within +-20 um of the mesh surface.
- **Clustering:** stroke-scale smoothing, local 3 mm median background, clusters of letter extent, and an excess-count score.
- **Validation:** planted Egyptian-blue grain letters (DECL-P4-10 item 3). Grain density and layer thickness are varied over the section 2 ranges, and grey values follow the section 3 calibration with PSF blur.
