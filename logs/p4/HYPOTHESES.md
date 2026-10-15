# P4 title hypothesis register (OWNER-STANDING-ORDER-2)
Provenance: Project HERCULES | owner the owner | [id removed]

Started 2026-09-26 21:50Z. Re-ranked after every result, with a red-team review at each re-rank. Priors are UNCERTAIN judgements; their sources are cited, and p4-research DOSSIER v4 is cited as D.
No title words appear here, and none ever will.

## Location / face / depth
| id | hypothesis | prior | mechanism / CT signature | declared test | validation | status |
|---|---|---|---|---|---|---|
| L1 | End title beside the last column, window A (w010-027 c10-c14, about w019-w022) | 0.45 (D s5; Cavallo: 91 % beside) | deposit layer at recto depth d* | M1 (read; labelled-adjacent, so not a candidate), E2, L2, L2S, L3, P4-W | known-text gate c0-c8; N0 | L2S r0-r1 0 letters; L3 pending d* |
| L2 | Second or calligraphic end title, window B (c15-c19) | 0.20 (D; PHerc. 1497, 1675) | as L1; letters larger | as L1 plus P4-W block | as L1 | pending |
| L3 | Title partly or wholly above the traced top edge (the "top rows physically missing") | 0.10 (D) | sheet continues about 2 mm above the mesh in c9-c14 (p4-layout) | tracer top-edge trace, then a render declaration | seam consistency, winding continuity | trace running |
| L4 | Title below a short last column (c11-c13 r2-r4) | inside L1 | as L1 | E1, M2a (0), L3 | as L1 | L3 pending |
| L5 | Core, w000-w009 | 0.05 (D H4) | no mesh; pitch anomaly 0.07-0.15 mm | DECL-P4-7 crossing count (p4-core, p4-inner) | synthetic planted-sheet error <= 1 winding | count.json pushed; decision pending |
[line withheld: prize-candidate detail under review]
| L7 | Title on the verso (end or outer) | 0.02 (PHerc. 339, 1491, 1670) | deposit at -d*, mirror-reversed in renders | DECL-P4-15(b) P4-V | mirrored known-text gate; verso null; offset check | after d* |
| L8 | External tag (sillybos) or wrapper at the outer end, still attached | 0.01 (Martial 3.2, Ovid Tristia 1.1: luxury copies) | separate thin sheet outside the roll body | DECL-P4-15(c) P4-TAG geometry | geometry only | builder p4-core |
| L9 | Title lost with damaged or missing papyrus (as the organizers suspect for PHerc. 1667) | 0.10 | no sheet there | none; the register records "unrecoverable" if L1-L8 all fail | - | - |
| L10 | Mesh error: the official mesh jumps sheets (sheet switch) across the title zone, so the title surface is not traced | 0.05 (new; the crushed inner roll) | neighbour-distance ratio and normal flips in c9-c19 | tracer / flat1 metrics on the official w010-027 mesh (to declare) | metrics on the known-text columns as reference | to dispatch |

## Ink / colourant / form
| id | hypothesis | prior | CT physics | test | status |
|---|---|---|---|---|---|
| I1 | Same carbon ink as the body (bright 10-20 um deposits in the Paganin volume) | 0.90 or more (D 2.4; PHerc. 172 same scribe) | deposit at d* | L3 at d*; P4-W; reader-free detector | pending d* |
| I2 | Dense mineral ink (cinnabar, minium, ochre, Egyptian blue, gold, Cu greens) | 0.02-0.04 (D) | brighter than carbon | P4-F (null within +-15 um); re-run at d* (DECL-P4-6-A3) | pending d* |
| I3 | Purple: Tyrian purple (Br, 38 % by mass) or purpurissum (dye on chalk, Ca) | 0.005-0.01 (no Herculaneum attestation; codex-era practice) | Br or Ca raises attenuation, if it survived carbonisation | DECL-P4-16 items 1-3 (attenuation table, injection limits, 78/137 keV dual energy on r3) | p4-purple, p4-highz |
| I4 | Organic dye with no mineral carrier (orchil, kermes, madder, indigo) | 0.005 | composition contrast about nil; deposit relief may remain | DECL-P4-16 item 4 (morphology), L3 deposit channel | morphology gate AUC >= 0.70 on control |
| I5 | Faint, diluted or thin carbon ink | 0.05 | weak deposit | L3, reader-free detector at 5 x 5 mm cells | pending |
| F1 | Sparse, large-letter or ornamented title block missed by the 5-letter tile rule | new blind spot | block of 2-6 lines, 3-6 cm wide | DECL-P4-17 (P4-W windows; "block" brief; reader-free detector) | declared |

## Owner inputs weighed (OWNER-STANDING-ORDER-2 item 1)
- "Different colour / rubrication": codex-era and Egyptian temple practice. Roman luxury copies used red tags and purple wrappers (Ovid, Martial). This is kept as I2, I3 and L8, at low prior, and each is tested.
- "Purple as a hint (the 2023 first word)": that word belongs to the 2,000-year-old text (an Epicurean treatise with frequent references to food and luxury). It carries no information about the title's ink. Purple is still tested on its physics (I3).
- "Fancy title": decoration is attested in Herculaneum titles (dashes, curves, coronis, calligraphic large letters). This is covered by F1 / DECL-P4-17.
- "Missed inner windings": L5.

## Re-rank 2026-09-27 02:15Z (after CERC54-LAYOUT-RESULT: the last column is short, 7 lines, upper margin lost)
- The c11-c13 r0-r1 block is most likely col. -1, the short last column. This supports p4-titulus Q1 (i), which was at 0.65 and rises to about 0.85 until DECL-P4-19 reports.
- End-title location, given (i):
  - beside col. -1 in c14-c17: about 0.60 in total. Of that, top rows (lost, with L3): 0.20; preserved rows r1-r4: 0.40;
  - below col. -1 in c11-c13 r2-r5: about 0.08;
  - further on, in c18-c19 or the core (a second or calligraphic title, or the blank end): about 0.10;
  - lost or damaged elsewhere (L9): about 0.15;
  - other locations (L6-L8): about 0.07.
- Search priority for L4 (DECL-P4-18) and P4-W (DECL-P4-17): c14-c17 all rows first, then c11-c13 r2-r5, then c18-c19.
- The red team (p4-titulus) is asked to re-derive these numbers from logs/p4/cerc54_layout.json.

## Re-rank 2026-09-27 02:50Z (after P4-W1-RESULT, P4-L4-PREGATE-RESULT, P4-CORE-AUDIT-RESULT, CERC54 full extract)
- In the organizers' carbon-ink model (M1), at title scale: blank at all 8 prime windows (the gate passed 6/6). Carbon ink in the preserved upper and middle rows of c12-c18 is unlikely.
- Remaining mass (UNCERTAIN), from p4-titulus Q4 after this null:
  - different or faint ink in the prime windows (the organizers' own hint): 0.25;
  - lost at the top (0.10) or surface damaged (0.12): 0.22;
  - low rows r4-r7 in c14-c19, where M1 is weak and the mesh is defective (DECL-P4-22): 0.15;
  - further inward (c19, core) within about 17 cm of col. -1: 0.10;
  - below col. -1 (c11-c13 r2-r5; M1 census blank, W1 (3,12) blank): 0.06;
  - never written: 0.07;
  - other: 0.15.
- Tests that can still move these:
  - the P4-F E2/E1 offset sweeps (dense mineral ink at any depth);
  - P4-O (the eligible independent model; the fleet runs tonight);
  - DECL-P4-22 (the re-traced low patch);
  - DECL-P4-21 (organizer label fractions).

## Re-rank 2026-09-27 06:05Z (owner item 22: think different; mesh holes; initial title; own model)
- New mechanism L11, "the mesh stops before the papyrus". r0 tiles are 83-90 % mesh-valid, with 13-16 % missing surface-volume chunks (P4-O it5 manifest 615af40). Row r8 was never in any census. The "lost upper margin" (CERC54) was a statement about 2019 segmentation, not a CT measurement of the papyrus edge.
  - If the sheet continues above the mesh top in c14-c19, a title there was never rendered by anyone.
  - Weight about 0.08, taken from "lost at the top" 0.10 and "other" 0.15. Test: DECL-P4-24 item (e).
- Interior holes and stretched renders (L10 variants): untested until DECL-P4-24 items (a)-(d); prior about 0.03.
- L6 (initial title at the outer start): pending p4-titulus Q5. It stays about 0.03 until the literature check; P4-M-OUT was uninformative, so the outer start has no informative test yet.
- "Different or faint ink" (0.25) gains a new test: P4-OWN (DECL-P4-23), a model trained on Paris 4's own ink appearance at 2.4 um with the title zone excluded. Its sensitivity is checked locally on col. -1.
- Red team (orchestrator): (1) Could P4-OWN learn the organizers' label style rather than ink? The NULL arm and held-out folds bound this. (2) Could an extension above the mesh top be the wrong sheet? The DECL-P4-22 gate applies to it too.

## Re-rank 2026-09-27 06:16Z (p4-titulus Q5, logs/sib/p4-titulus/QA.md ccb7c5b; red team built in)
- The owner's point is confirmed. PHerc. 1497/1583 has an initial title on its outer layer AND two final titles. 6 recto initial titles are attested (12-25 cm outward of col. 1), and Capasso ascribes their rarity to loss of the outer turns.
- L6 (initial title, readable in the imaged data): 0.01 -> about 0.045. It is independent of the end title (a second chance). Verso-outer: about 0.01.
- End-title partition now (p4-titulus q5_partition.json), c14-c17 beside col. -1:
  - top, wholly above the edge 0.11; top, partly in r0 0.12; centred r2-r3 0.11; low r4-r5 0.09.
  - Elsewhere: further c18+ 0.12, of which top lost 0.03; below col. -1 0.10; surface damaged or flaked 0.17; the block is the title 0.03; never written 0.07; core 0.05.
- Tests added:
  - DECL-P4-25: locator of the outer-end first column and blank length (p4-inner, rh-e2).
  - DECL-P4-26: facing-surface offset channel (p4-core facing mesh; model gate first). It aims at the "flaked" cell, 0.17.
- Top-edge formula (for DECL-P4-24 (e)): P(title ink above the edge) ≈ 0.24 × min(1, L / 12.5 mm). 5 mm of continuation is the practical threshold.
- P(at least one title recoverable) ≈ 0.30 (p4-titulus; UNCERTAIN, optimistic).

## Update 2026-09-27 06:53Z (results, no re-weight of locations)
- P4-F-SWEEP-RESULT: 0 dense hotspots at every offset on E2 and E1. The mineral-ink subset of "different ink" falls to about 0.01; organic or faint ink remains.
- P4-O-STAGE-O2S1-RESULT: the eligible PHerc.1667 iteration-5 model fails the known-text gate (0/3; prediction mean about 0.55 on known text). It is uninformative on Paris 4. The eligible-model route now rests on P4-OWN (DECL-P4-23).
[line withheld: prize-candidate detail under review]
- Coverage: M1, E1, E2, L2S, L3, L4, P4-F, P4-O (it5) and W1 have all been run on the title zone. Every informative channel is null there, and the uninformative ones are marked as such. Live: P4-OWN, DECL-P4-24 (edges), DECL-P4-25 (outer end), DECL-P4-26 (facing, queued).

## Update 2026-09-27 07:24Z (outer end, L6)
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
- Physics: purple or lake dyes are untestable by the available CT at <= 20 um (METRIC-HASH-40).

[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
- End title: the organizers' labels mark ink in col. -1 and nothing in c14-c19 (P4-21-RESULT). The top edge in c9-c14 continues about 2 mm at most; c15-c19 are unmeasurable (P4-24-E2-RESULT). The cells are unchanged from Q5 (e).
- Tests still live: P4-OWN (training), P4-OFF facing surfaces (p4-core building meshes), r2_c19 re-trace (tracer), dual-energy one-shot (p4-purple), DECL-P4-25-A3 (after G1).
