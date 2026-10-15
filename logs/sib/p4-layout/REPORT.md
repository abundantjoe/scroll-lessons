# p4-layout REPORT: DECL-P4-13 part P4-M (items 1-3), numbers only

Provenance: Project HERCULES | owner the owner | [id removed]
Sibling p4-layout; branch claude/gifted-bell-gavnl5-sib-p4-layout. No image, tile or CT pixel was opened, viewed or described. PNG/TIFF/zarr data were decoded only to arrays and reduced to sums, indices and distances. The DOSSIER's EXPECTED-TEXT section was not read. No sub-siblings were created (SUBSIBS: none), because the work was CPU- and network-light.

## Item 2: edge check (edge.json). Answer: YES, sheet continues above the official top edge, but only about 2 mm
1. **The official top edge is a z cut, not a sheet end.**
   - Edge z is 172.2-172.8 mm (p5-p95) in every column c0-c20. That equals the spiral-fit z limit of 172.8 mm (fitted_m7_ds2_z3000_18000).
   - The r0 tiles are 79-90 % mesh-valid. The 10-22 % invalid part is the top 2.9-3.9 mm of canvas above the cut.
2. **Scroll material above the edge is limited.** On the top-edge footprint, the organizers' mask is:

   | z (mm) | mask present |
   |---|---|
   | up to 172.6 | 100 % |
   | 174.4 | 87 % |
   | 176.3 | 48 % |
   | 177.7 | 5 % |
   | from 178.1 | 0 % |

   So at most about +3 to +5 mm of material exists above the edge. The declared 0-2 cm window is physically bounded by the scroll top.
3. **The organizers' own mesh continues above.** The labelled segment 20231016151002 (2.4 um re-mesh, open bucket) coincides with strip a in r0-r3 c9-c15 at 0.001-0.009 mm, which reproduces p4-excl. In c9-c14 it extends 5.1-5.3 mm (median) above strip a's edge, to z 177.2-177.4 mm.
4. **CT test anchored on that mesh** (edge/edge_anchor.json). Method: centred-peak index against a half-pitch (125 um) null, at level 2 (9.6 um), with a bootstrap over 759 segment columns.
   - Pooled c9-c15, sheet is supported in every 0.5 mm band from 0 to +2.0 mm. From +2.0 mm upward the on-mesh index turns negative (no sheet), while mask zeros rise to 84 % by +4.0 to +4.5 mm.
   - Per column:

     | Column | Sheet supported to | Note |
     |---|---|---|
     | c9 | +2.0 mm | undetermined from +2 to +3 mm |
     | c12 | +2.0 mm | |
     | c13 | +1.5 mm | |
     | c14 | +0.5 mm | undetermined from +0.5 to +1.5 mm |
     | c10, c11 | undetermined | their below-edge reference index is <= 0, so the test has no power there |
     | c15 | not tested | too few anchor vertices |

5. **For P4-N:** a 1-2 cm extension is not supported. About +2 mm (to z ~174.5 mm) in c9-c14 is supported, and the organizer mesh 20231016151002 can seed and validate the trace.
6. **A first test failed its own validation and is not used.** This was a patch-correlation tracker (edge/edge_cont.json). Its positive-control r (p50 0.41) fell below the shuffled null (p50 0.72), and its tracker drift was p50 148 um and p90 481 um.

## Item 3: organizer-segment mapping (orgmap.json). PARTIAL; blocked on ASK-2
- The five 2024 title-search meshes (meta.json + OBJ) were fetched under OWNER-LICENSE-EDUCELAB-1.
  - meta.json places 20240102231959, 20240110113230 and 20240116164433 on 1A (20230205180739), and 20240101215220 and 20240109095720 on 1B (20230206171837).
  - This session's safety check then refused to compute with them, because the acceptance arrived only as an orchestrator relay. I did not route around that. The files were deleted, and no number derived from them exists.
- 1B cannot be mapped at all: there is no published transform to 20260411134726.
- **The transform is validated.** Mapping 20231016151002's 7.91 um mesh through the inverse bucket transform.json onto its 2.4 um re-mesh leaves residuals of 8.6 / 19.1 / 26.8 / 32.1 um (p10 / p50 / p90 / p99). The wrong-direction control gives 131.8 mm. So 1A segments can be assigned to a winding, since the half pitch is about 125 um.
- **Open question:** whether the 2024 title search covered window A (c10-c14) is still unknown.
- **Citation:** any future numbers derived from those meshes use the EduceLab-Scrolls dataset (Parsons, Parker, Chapman, Hayashida and Seales 2023, arXiv 2304.02084), under the EduceLab Data License.

## Item 1: column profile with pitch validation (profile.json)
1. **Pitch validation, declared.**

   | Channel and span | Periodogram peak | SNR | Autocorrelation | Result |
   |---|---|---|---|---|
   | M1, strip a c0-c9 | 76 mm (native resolution +-16 mm) | 64 | 79 mm, r 0.59 | PASS |
   | M1, w028-037 c0-c20 | 78 mm (+-8 mm) | 102 | 76 mm, r 0.82 | PASS |
   | E2 (+-53 um mean) | none in 50-120 mm; dominant period 12-16 mm | | | FAIL |
   | P4-L thin-slab max (L2) | none in 50-120 mm; dominant period 12-16 mm | | | FAIL |

   So the raw-CT channels show no column layout at this scale. The interior-peak condition was added after seeing the E2 result. It tightens the bar and changed no M1 verdict.
2. **Intercolumns from M1.**
   - Strip a: 51, 126 and 214 mm (c2.55, c6.3, c10.7).
   - Strip b: 84, 163, 237, 315 and 388 mm (spacings 73-79 mm).
   - Precision is **not** +-1 mm across rows. The per-row positions spread +-3 to +-8 mm on strip a and +-1.5 to +-5 mm on strip b. Only the pooled profile is quantised to 1 mm.
3. **The c11-c13 block (M1, r0-r1).**
   - Its extent is 217-276 mm (c10.85-c13.8, **60 mm wide**) above the c15-c19 background + 3 sd. It starts 3 mm after the c10.7 intercolumn.
   - Vertically it runs from 5 to 38 mm below the canvas top. That is from within about 1-2 mm of the mesh top cut to about 34 mm down the sheet, so the block is truncated by the cut.
   - E2 and L2 show nothing above background there.

## Honest uncertainty
- **The edge result rests on one organizer mesh as the anchor, at 9.6 um.** A sheet that bends away from that mesh above +2 mm would read as "no sheet"; the mask end bounds any such continuation. The index is weak (pooled below-edge reference 3.4 grey levels), and in c10-c11 the test has no power.
- **The block is a model (M1) signal.** Its 60 mm width matches a full text column (pitch minus intercolumn). That fits a short final text column (H1) at least as well as a centred title (H2). This profile cannot tell text from title, and the census letter counts it echoes are unconfirmed.
- **The pitch uses short spans.** 200-420 mm gives a native period resolution of +-8 to +-16 mm, so the pitch is 76-78 mm with that uncertainty. It agrees with the DOSSIER's 8 +- 2 cm.
- **Item 3 is incomplete.** It is the one open item, pending ASK-2.

Integrity: no issues. The safety-check refusal of the EduceLab computation (ASK-2) was respected: nothing was worked around, and the data were deleted.
