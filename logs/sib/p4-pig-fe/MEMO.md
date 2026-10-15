Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-fe memo: the FE family (red/yellow ochre, green earth) in the Paris 4 CT

Serves RULES.md DECL-P4-10 item 1 (family FE), under DECL-P4-5 (+A1) and DECL-P4-6 (+A1, A2). It was written before any
P4-J/FE number on the title strip existed. The only CT numbers used here are the p4-highz control/E1 depth profiles and
histograms that are already published (logs/sib/p4-highz/physics.json at db96abe). No image, tile or CT pixel was
opened or viewed.

Confidence tags: **[V]** checked against the cited source in this session; **[L]** from the literature as I know it,
not re-checked today, so it should be verified before any claim leans on it; **[C]** my own calculation (the code and
inputs are in this directory).

## 1. Materials and thermal stability (300-400 C, reducing pyroclastic setting)

- **Red ochre / hematite, alpha-Fe2O3.** This is the end product of heating Fe oxyhydroxides, and it is stable far
  above the Herculaneum temperatures. The 79 CE currents at Herculaneum reached about 555-495 C (the first, dilute ash
  surge), then 465-390 C and 350-315 C (charcoal reflectance; "A new hazard scenario at Vesuvius", Sci. Rep. 13 (2023), doi 10.1038/s41598-023-32623-3; author names not re-checked)
  **[V]**. The papyri themselves are usually put at about 320 C **[V, secondary statement in the search results;
  primary source not re-checked]**.
  Reduction of hematite to magnetite by carbon or CO needs higher temperatures or long contact times (usually > 400-500 C
  in reduction-roasting practice) **[L]**. A partial reduction in contact with pyrolysing papyrus cannot be excluded,
  but it would not change the CT signal: Fe3O4 attenuates like Fe2O3 to within 1 % (table 3) **[C]**.
- **Yellow ochre / goethite, alpha-FeOOH.** It dehydroxylates to hematite from about 250-300 C, topotactically (the
  particle morphology is preserved) **[V: Colorants 5(3) 24; Spectrochim. Acta A 2001 FT-IR in-situ study]**. Pompeian
  yellow ochre was partly turned red by the 79 CE eruption, and the degree of transformation has been quantified by
  Raman imaging (Raman-imaging study, 2019; author names not re-checked) **[V title; details L]**. A yellow title therefore now contains hematite, and
  it counts as the same CT target as red ochre, with about 10 % less Fe mass per grain volume.
- **Green earth** (celadonite/glauconite, K(Mg,Fe2+)(Fe3+,Al)Si4O10(OH)2). Loss of OH occurs at about 400-600 C
  **[L]**. At 300-400 C the Fe stays in the silicate. Its Fe content is modest: about 15-25 wt % as Fe oxides.
- **Grain size.** Natural ochres are mixtures: hematite or goethite crystallites of about 0.05-1 um sit on and in clay
  (kaolinite, illite) and quartz carriers. Ground pigment particles are about 1-10 um, and aggregates reach tens of um
  **[L]**. A paint layer is therefore particulate and porous, with a pigment volume fraction of perhaps 0.1-0.4.
  **Consequence:** at a 2.258 um voxel (E1 level 0) or 2.4 um (E2), a single crystallite is sub-voxel. The layer
  shows up as a **moderately raised band of partial-volume voxels**, not as a few extreme voxels. That is why this
  family's detector counts a clipped intensity band, and does not look for maxima.
- **Layer thickness.** Ink layers on papyrus are thin. Carbon ink on Herculaneum papyri is a few um to about 10-20 um
  thick, and the letters show as relief of a few um in phase-contrast CT **[L]**. Red ochre inks on Tebtunis papyri
  (next section) are particulate layers of comparable scale **[L]**. Plausible range: **2-20 um**, most likely
  **5-10 um**. The injection test uses 2, 5, 10 and 20 um.

## 2. Attestation in Greek papyri, 3rd c. BC - 1st c. AD (kept separate from later evidence)

- **Egyptian (hieratic/demotic) papyri, Roman period, c. 100-200 CE (Tebtunis temple library).** Synchrotron XRF,
  micro-XRD and FTIR show that most red inks are Fe-based ochre (Fe co-located with Al, hematite by micro-XRD), often
  with Pb compounds. Christiansen et al. 2020, PNAS 117, 27825 (doi 10.1073/pnas.2004534117) **[V]**. These are
  Egyptian-language temple texts, where red rubrics are standard. They are not Greek literary rolls, but they are
  the nearest securely analysed red inks on papyrus in the target period. They also show that **ochre is the default
  red pigment of ink on papyrus**, not cinnabar.
- **Pliny, NH 35**, describes *sandyx*: red ochre calcined with lead white (1st c. CE; cited in Christiansen 2020)
  **[V via the secondary source]**. A red of that kind would be FE+Pb, and it would also light up in the RED family's
  channel.
- **Greek papyri.** Red ink is attested, but it is rare in the period:
  - in documents, for example P.Mich. inv. 1568v, a report of proceedings written in red ink (Oxyrhynchus, late 2nd
    c. AD, BASP 46, 2009) **[V title]**, which is later than our window;
  - in magical papyri and some later literary codices, for rubrics (3rd-5th c. AD and later) **[L]**.
  I know of **no analysed case** of red ochre titles, rubrics or marginal marks in a *Greek literary roll* of the
  3rd c. BC - 1st c. AD. Marginal signs in that period (coronis, diple, obelos, paragraphos) are normally in the text
  ink **[L]**.
- **Herculaneum.** Published analyses of Herculaneum ink find carbon ink, and in some fragments Pb-bearing ink
  (Brun et al. 2016, PNAS 113, 3751; Tack et al. 2016, Sci. Rep. 6, 20786: up to 84 +- 5 ug/cm2 Pb in letters)
  **[V]**. The attested Herculaneum end-titles (subscriptiones with author, work, book and stichometry) are, as far as
  I know, in the same black ink as the text **[L; p4-research owns the full compilation]**.
- **Honest prior.** An ochre title in PHerc. Paris 4 is possible but not expected. It would be unusual for a
  Herculaneum roll, although ochre was the ordinary red of ink on papyrus in Egypt at the time. This memo does not
  set a numeric prior. The detector test below does not depend on the prior.
- **Byzantine and medieval** chrysography and minium rubrication are outside this window. They are not used.

## 3. Attenuation at the scan energies (NIST XCOM / Hubbell-Seltzer tables) [C]

The element mu/rho values come from the NIST X-Ray Mass Attenuation Coefficients tables (Hubbell & Seltzer, NIST SRD
126; physics.nist.gov/PhysRefData/XrayMassCoef, fetched 2026-09-26, log-log interpolated). They are in
nist_mu_elements.json. Compound values use the mixture rule (mu_table.json). The published PHerc. Paris 4 surface
volumes used by the project are all 78 keV (1.129 um and 2.4 um; DECL-P4-6-A1). Fe has no absorption edge between 60
and 100 keV (Fe K = 7.1 keV), so **no dual-energy trick isolates Fe**; only density and morphology are available.

| material (assumed density g/cm3) | mu/rho 78 keV cm2/g | mu 78 keV cm-1 | mu / papyrus | electron-density / papyrus |
|---|---|---|---|---|
| hematite Fe2O3 (5.26) | 0.494 | 2.60 | 30.6 | 9.7 |
| goethite FeOOH (4.27) | 0.463 | 1.98 | 23.2 | 8.0 |
| Ti-magnetite proxy Fe3O4 (5.18) | 0.505 | 2.62 | 30.8 | 9.6 |
| green earth, ~21 wt % Fe oxides (2.8) | 0.269 | 0.75 | 8.9 | 5.4 |
| kaolinite clay (2.6) | 0.193 | 0.50 | 5.9 | 5.1 |
| Vesuvius 79 phonolitic glass, ~5 wt % Fe2O3t (2.45) | 0.226 | 0.55 | 6.5 | 4.7 |
| carbon ink, C + gum (1.2) | 0.166 | 0.20 | 2.3 | 2.4 |
| gum arabic binder (1.4) | 0.175 | 0.25 | 2.9 | 2.9 |
| carbonised papyrus, C0.80 O0.16 H0.03 Ca0.01 (0.5) | 0.170 | 0.085 | 1 | 1 |

The density of carbonised papyrus (0.5) is an assumption. All ratios scale inversely with it.

**Paint layers (volume fractions; the rest is pore):**
- *standard ochre ink*: 0.30 hematite + 0.20 clay + 0.20 gum. mu = 0.93 cm-1 (**10.9 x papyrus**); electron density
  **4.5 x papyrus**.
- *lean ochre ink*: 0.10 hematite + 0.30 clay + 0.20 gum. mu 5.4 x; electron density 3.1 x.
- *green-earth ink*: 0.40 green earth + 0.20 gum. mu 4.1 x; electron density 2.7 x.

**Which ratio applies to the voxel values?** The volumes are propagation-phase-contrast scans (0.22-0.23 m distance
in the volume names) and are probably phase-retrieved. A single-material Paganin reconstruction gives values that
follow the electron density (delta) more than mu (beta) **[L]**. The contrast of a Fe-rich layer then sits between
the electron-density ratio (conservative) and the mu ratio (optimistic). **The injection test uses the conservative
electron-density ratio as its primary regime and the mu ratio as its secondary regime.**

## 4. Expected voxel contrast [C, calibrated on published p4-highz numbers]

- The per-slice mean over the control's sheet is about 82 (uint8) at the sheet core (slices 49-51). It is about 67 in
  the gap on the + side (slice 76), and the median sheet voxel is 80 (p4-highz physics.json). The papyrus - air
  difference is therefore only about 15-30 grey levels. A voxel filled with standard ochre paint would sit at about
  air + 4.5 x (papyrus - air), roughly 65 + 4.5 x 25 = 180, in the conservative regime. In the mu regime it would
  saturate at 255.
- Partial volume. A 5 um layer covers about 2.2 voxels at 2.258 um (E1) and about 2.1 voxels at 2.4 um (E2), before
  the point-spread / Paganin blur. After a blur of sigma about 1 voxel, the peak of a 5 um standard layer is expected
  at about papyrus + 0.6-0.8 x (180 - papyrus), about 140-160. A 2 um layer reaches about 100-120.
- The natural tail is high: the control sheet slab has p99 = 169 and p99.9 = 233 (p4-highz). **A single voxel of a
  realistic ochre layer is therefore not an outlier.** Detection has to come from *many* moderately raised voxels
  that are (i) confined to the recto surface layer and (ii) laterally organised into strokes 0.3-0.6 mm wide and
  mm long. This is the "weak to moderate" regime named in the task. The E2 (2.4 um) contrast is about the same per
  voxel, with a little more partial-volume dilution.
- Carbon ink (2.3 x papyrus at 1.2 g/cm3) in a 5-10 um layer stays mostly below the band, so the known-text control
  should not light up. That is the specificity test.

## 5. Natural Fe-bearing mimics (confounders)

- **Vesuvius 79 tephra.** The phonolitic/tephriphonolitic glass has about 4.5-5.2 wt % Fe2O3t (grey pumice; Fe2O3t
  4.55-5.22 wt %) **[V: EJM 6(3) chemical variations of the AD 79 pumice]**. Its minerals include clinopyroxene,
  garnet and leucite, and the opaque phase is **Ti-magnetite** (Usp 12-21 mol %) **[V: Springer 2024 white pumice
  PDC chapter]**.
  - Glass or ash shards: 4.7-6.5 x papyrus. Their per-voxel brightness is similar to a lean ochre layer.
  - Ti-magnetite grains: 9.6-31 x papyrus. Per voxel they cannot be told from hematite.
  - Ash was forced into the rolls by the surge. It occurs **throughout the depth** of the roll (in the gaps and
    embedded in sheets) and as **isolated grains**. It does not form letter-shaped films on one surface.
- **Soil/clay and Fe-staining** from burial, groundwater and the post-excavation history (Paris 4 was unrolling-
  attempted and handled). These are diffuse, can be surface-bound, and can form films. **This is the most dangerous
  mimic**, because a surface film of clay-rich soil is physically very close to a lean ochre ink. Morphology is the
  only discriminant: strokes of constant width, letter-scale structure, and alignment with the line direction.
- **Pb-bearing black ink** (Brun 2016) is denser than carbon ink. It is not FE, but the FE detector would respond to it.
  The control strip (known carbon-ink text) measures this directly.
- **Mesh misregistration and sheet contacts.** Where the mesh sits off the true surface, or two windings touch, the
  surface band samples papyrus instead of air. That raises the band. The detector subtracts the sheet interior and a
  local background to suppress this.

## 6. Consequences for the detector (frozen in params.json)

1. Intensity **band** [B_lo, B_hi], per voxel, with a clipped excess max(0, min(v, B_hi) - B_lo).
   - B_lo is a high percentile of the control's own surface-plus-interior voxels.
   - B_hi is the expected full-voxel value of standard ochre paint in the conservative regime. It caps extreme grains
     (magnetite, Pb/Hg), so single grains cannot dominate.
2. **Recto surface layer** (0 to +20 um on the gap side of the mesh surface) **minus sheet interior** (-20 to -7 um),
   per pixel. The side is fixed from the published depth profile: the sheet core is at slices < 58 and the gap at
   > 58.
3. **Stroke-scale matched filter.** The excess is block-averaged to 22.6 um, then correlated with oriented bar-minus-
   flank kernels (0.45 mm wide, 1.8 mm long, 4 orientations), normalised by the control's robust spread.
4. **Validation.**
   - Injection of Greek-capital strokes at 2/5/10/20 um in both regimes, at >= 10 control and >= 10 title-strip
     locations.
   - False-positive rate on the control and on rot-90 nulls.
   - In-sheet fraction against a deep band (-40 to -22 um) for every hotspot, so depth-uniform ash does not count.
5. What the detector **cannot** do: tell ochre from a clay-rich soil film or from Pb-bearing ink by physics at
   78 keV. A hotspot is only a place to look, under a separate declaration.

## Sources (URLs)
- Christiansen et al. 2020, PNAS: https://www.pnas.org/doi/10.1073/pnas.2004534117 (PMC7668004)
- Sci. Rep. 2023 (Vesuvius ash cloud surges, Herculaneum charcoal reflectance): https://www.nature.com/articles/s41598-023-32623-3
- Goethite to hematite: https://doi.org/10.3390/colorants5030024 ; Pompeian yellow ochre Raman imaging:
  https://www.researchgate.net/publication/337088411
- Brun et al. 2016, PNAS: https://www.pnas.org/doi/10.1073/pnas.1519958113 ; Tack et al. 2016, Sci. Rep.:
  https://www.nature.com/articles/srep20763
- AD 79 pumice chemistry, EJM 6(3):
  https://www.schweizerbart.de/papers/ejm/detail/6/83686/Chemical_variations_of_the_AD_79_pumice_deposits_of_Vesuvius ;
  white pumice PDC clasts: https://link.springer.com/chapter/10.1007/978-3-031-48758-3_62
- P.Mich. inv. 1568v (red ink, Oxyrhynchus, late 2nd c. AD), BASP 46 (2009) 23-29:
  https://www.academia.edu/20124058
- NIST X-ray mass attenuation coefficients: https://physics.nist.gov/PhysRefData/XrayMassCoef/
