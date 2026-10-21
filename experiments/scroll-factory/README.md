# Scroll Factory: public records of the October 2026 controls

Scroll Factory is the follow-on to Dominion (same owner, Joseph Balmaceda; run by Claude research agents, Anthropic). Its
working repository is private because the owner's rule is that no target-scroll material is published before any
submission. This page publishes the **controls**: the
experiments on known text and on synthetic truth, which carry no information about any unread target. Target screens are
left out until they have been reviewed. No letter is claimed on any scroll.

E1, E1-AM, E2a and E3a were declared before their data were computed. Each declaration was committed and pushed first,
and the commit is given.
- E1-REPRO had no separate declaration.
- E3-REF is a record of measurements made before the amendment that used them.
- E5 was declared after both of its calibration outcomes were already known, so it is a consistency check, not a
  blind prediction.

Numbers come from the result files at the commits named. The lessons are L657-L668 in [MASTER_LESSONS.md](../../MASTER_LESSONS.md).

**Chain (all CPU, 4 vCPU, 15 GB):**
- Rendering: `render66.py`, AndreasHad04/villa-apple-silicon @8320e35. A 66-layer unflipped frame for PHerc0343;
  `--num-slices 31 --flip-normals` matched one public atlas render of the same mesh (99.43 % identical
  voxels, 100 % within 1 grey level).
- Inference: villa `koine_machines` inference, branch merge-ink-pipelines @3ea17f5, with Reader V3
  (domenicor046/reader-v3 @aee1d64, sha256 `ea405417450abd8ace1b8ff79ebce3adb646c5e48ab95da46844d77efe984d8a`).
- Scorers: box AUC and strong-ink ratio on letter boxes; pixel AUC against labels.

| ID | question | declared | verdict | key numbers | lesson |
|---|---|---|---|---|---|
| E1 | Does the CPU chain recover the published PHerc0343 First Letters ink, while displaced depths do not? | `fe140aa` | **PASSED** | Render parity 0.99978 within 1 grey level (layers 33/35: 0.136). Better order (chosen on arm A, as declared) reverse: box AUC 0.6929, strong-ink ratio 9.58. Forward order 0.5686. Displaced +12 / −10 voxels: 0.4842 / 0.5441. 762 s for both directions, 3.57 GB. | L657, L663 |
| E1-AM | Does robust normalisation over CT voxels only (zeros masked) beat the published recipe? | amendment 1, `0a98c20` | **PASSED** (adopted) | Box AUC 0.7368 against 0.6929. Strong-ink ratio 24.53 against 9.58. Off-box strong fraction at 0-64 px from invalid 0.002 against 0.033. | L662 |
| E1-REPRO | Does a cold cloud session reproduce E1 from the pinned scripts alone? | not declared (task T-007) | **PASSED** | Setup 132 s, reproduction 324 s, unmodified. Box AUC 0.6929000366 and ink-map sha256 `7c49d066…09e9c` identical. | L665 |
| E2a | Does Reader V3 detect held-out text at 9.366 um / 113 keV, and which order is the reading face in the official frame? | `d29e860` | **PASSED** | PHerc0841 w00 (outside the training data). Pixel AUC forward 0.8881 published / 0.9199 masked. Background at 80 % recall 0.154 / 0.113. Reverse pixel AUC 0.5156 / 0.7168. | L661, L663 |
| E3a | Does `snap_meshes.py` onto m7 repair a known displacement and restore known letters? | `d169aa0` | **PASSED** | Original 0.6929. Displaced +4 to +8 voxels: 0.5687. Snapped: 0.6763. Median node distance 1.99 voxels (p90 8.48). | L658 |
| E3-REF | O1 (fraction of nodes whose nearest m7 sheet centre is within ±2 voxels) of the known-good mesh | measured before amendment 1 (`fc75ed6`) | **RECORD** | Known-good 0.582; displaced 0.108. Amendment 1 replaced the declared O1 metric (m7 > 0 within ±1 voxel along the normal, never computed) with this one, and moved the bar, before any target was measured. | L659 |
| E5 | Does the normal sign against the scroll axis, with the render frame, predict the reading face? | `02a85f9` (after both outcomes were known) | **PASSED** (consistency check) | PHerc0343 f_out 0.997 (median n·r 0.840), predicted reverse = observed. PHerc0841 w00 f_out 0.985 (0.857), predicted forward = observed. | L660 |

**Method notes needed to reproduce:**
- **E2a labels.** The team's 2.403 um ink labels for PHerc0841 w00, resampled to the 9.366 um canvas by area
  interpolation: scale 0.25638 × 0.25647, against a voxel ratio of 0.25657. 2.81 % of valid pixels are ink. Used for
  scoring the control only.
- **E3a displacement.** δ = base + amplitude · sin · cos along the mesh normal, 3 periods per side. Snap used
  `snap_meshes.py` defaults.
- **E5 axis.** The published umbilicus where one exists. Otherwise the centroid of CT-occupied voxels (level-4 pyramid,
  volume > 0) on 7 axial slices across the mesh's z range, interpolated in z.
  - Sign: f_out ≥ 0.8 outward, ≤ 0.2 inward, otherwise ambiguous (read both ways and flagged).
