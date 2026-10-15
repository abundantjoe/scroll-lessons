Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-red STATUS

2026-09-26 ~18:45Z. State: **BLOCKED on CT access** (ASK.md ASK-1). Steps 1-2 are done; steps 3-4 have not started.

Done:
- **Step 1, MEMO.md.** The memo cites its sources, and xcom.json holds the xraylib table.
  - Attenuation at 78 keV: HgS 2.11 cm2/g (17.1/cm), PbO 2.41 cm2/g (22.9/cm), char about 0.17 cm2/g (0.05-0.21/cm). Contrast per volume is 80-450x.
  - Paris 4 scans bracket both the Hg and Pb K-edges: 74/110 keV at 45.5 um, and 78/137 keV at 2.4 um. A K-edge test needs its own declaration.
  - The closest analysed papyrus reds (Tebtunis, 100-200 CE) are Fe-based, with no cinnabar or minium.
  - Brun 2016 Herculaneum Pb ink is about 0.1 um PbO-equivalent.
- **Step 2, params.json.** Detector rules are frozen before any title-strip number. They are control-derived thresholds, block density, stroke-scale components, planarity and mesh distance.

Not done:
- Step 3 (injection-recovery) and step 4 (scoring). No title-strip number exists.
- No verdict on sensitivity. MEMO section 4 predicts it would be sensitive at >= about 2 um (pessimistic calibration), but that is unvalidated.

Blocker: the session safety check refused the first CT fetch and said it would keep refusing in this session. It is not routed around.

Next step: a fresh session, or default permissions, runs steps 3-4 with params.json unchanged.

Sub-siblings: none. None were created, because they would only be a way around the refusal.

## 2026-09-26 ~18:30Z: orchestrator addendum (DECL-P4-12)
- Recorded in ADDENDUM-1.md:
  - E2 is scored first, with c10-c17 reported separately.
  - Flags are reported but do not exclude tiles.
- detlim_model_2p4.json holds the analytic 2.4 um detection-limit PREDICTION only:
  - pessimistic: HgS about 1.5-1.7 um and PbO about 1.1-1.3 um;
  - optimistic: < 0.1 um.
- The measured injection-recovery is still blocked (ASK-1). State unchanged: BLOCKED on CT access.
