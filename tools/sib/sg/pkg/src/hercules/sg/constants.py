# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fixed bars of the submission gate SG (RULES.md DECL-SG, DECL-EMPNULL).

Every value marked "DECL-SG n" or "DECL-EMPNULL" is copied from the declaration and is
NEVER changed in code (DECL-SG: "declared now, never lowered").  Values marked
"choice" are implementation details the declarations leave open; each says why it was
chosen.  Where a declaration is ambiguous the STRICTER reading is implemented and the
ambiguity is listed in logs/sib/sg/REPORT.md for the orchestrator to settle.
Values marked "ruling Bn" implement the orchestrator's rulings on PROPOSAL-SG-CODE-1
(logs/sib/sg/rulings_applied.md); where a ruling chose between readings, the chosen one is
the one coded here.
"""

from __future__ import annotations

SG_VERSION = "hercules-sg-1.2.0"  # 1.1: rulings B1, B6, B7, B8, B9, B13, B14; 1.2: B8 revised

# ----------------------------------------------------------------------------- shared
CONSENSUS_RADIUS_PX = 150.0  # DECL-SG 1a, 5 and DECL-EMPNULL: "within 150 px" (canvas px)
MIN_READERS_AGREE = 2  # DECL-SG 1a: ">= 2 of 3"
N_READERS = 3  # DECL-SG 1a: "3 fresh blind readers"

# ----------------------------------------------------------------------------- discovery (DECL-EMPNULL)
DISCOVERY_K0 = 5  # DECL-EMPNULL: k = 5 initially
DISCOVERY_NONTEXT_AGREED_MAX = 1  # DECL-EMPNULL: non-text-order agreed count <= 1
DISCOVERY_FB_MAX = 1  # ruling B1: AND max per-reader F_B (known non-text namings) <= 1
DISCOVERY_MIN_NULL_TILES = 200  # DECL-EMPNULL: ">= 200 empirical-null tiles"
DISCOVERY_FDR_MAX = 0.01  # DECL-EMPNULL: "raise k by 1 until <= 1 %"

# ----------------------------------------------------------------------------- R (DECL-SG preamble)
R_AREA_CM2 = 4.00  # DECL-SG: R = a 4.00 cm^2 rectangle
R_AREA_TOL = 0.01  # DECL-SG: +-1 %
R_ASPECT_MAX = 2.0  # DECL-SG: aspect <= 2:1
# choice: candidate widths are scanned in steps of 1/4 mm between the aspect limits (at
# 9.366 um that is ~27 px, about a tenth of a letter height); finer steps change the
# placement by less than the consensus radius and cost time quadratically.
R_WIDTH_STEP_MM = 0.25

# ----------------------------------------------------------------------------- SG 1
SG1A_MIN_AGREED = 12  # DECL-SG 1a
SG1B_MIN_FIRM = 8  # DECL-SG 1b: ">= 8 of them firm for >= 2 readers"
SG1B_MIN_FIRM_READERS = 2  # DECL-SG 1b
SG1C_MIN_NULL_TILES = 40  # DECL-SG 1c
SG1C_PERCENTILE = 99  # DECL-SG 1c
SG1C_MARGIN = 10  # DECL-SG 1c
SG1D_ALPHA_NUMERATOR = 0.01  # DECL-SG 1d: p < 0.01 / m
# choice: the shuffle uses max(5000, 20 / alpha) permutations so that the smallest
# attainable p (1 / (1 + N)) is always at least 20 times below the bar.
SG1D_MIN_PERM = 5000
SG1D_PERM_PER_ALPHA = 20

# ----------------------------------------------------------------------------- SG 2-4
SG2_CANARY_FRACTION = 0.70  # DECL-SG 2: ">= 70 % of its REF ceiling"
SG2_BLANK_MAX_NAMINGS = 1  # DECL-SG 2: "a blank gets <= 1 naming"
SG3_OPPOSITE_MAX_NAMINGS = 2  # DECL-SG 3: "<= 2 namings in R"
SG4_RECONFIRM_FRACTION = 0.80  # DECL-SG 4: ">= 80 % re-confirmed"
SG4_SLICE_OFFSETS = (-1, 1)  # DECL-SG 4: "+-1 slice" (both offsets must hold: stricter reading)

# ----------------------------------------------------------------------------- SG 5-6
SG5_FRACTION = 0.50  # DECL-SG 5
SG6_OVERLAP_MIN = 0.60  # DECL-SG 6: re-trace ">= 60 % overlap"
SG6_FRACTION = 0.50  # DECL-SG 6: "reproduces >= 50 %"

# ----------------------------------------------------------------------------- SG 7 copy test
SG7_NCC_MAX = 0.80  # DECL-SG 7: NCC >= 0.8 is a copy
SG7_ROT_STEP_DEG = 15  # DECL-SG 7: "any 15 deg rotation step"
SG7_ROTATIONS_DEG = tuple(range(0, 360, SG7_ROT_STEP_DEG))  # 24 steps
SG7_ABS_NCC = True  # ruling B6: |NCC| >= 0.8 is a copy (an inverted copy is still a copy)
SG7_NEFF_MIN = 30.0  # ruling B7: a crop is evaluable only if n_eff >= 30 (else SG 7 FAILs)
SG7_NULL_MIN_TILES = 40  # ruling B7: copy-test null on >= 40 empirical-null tiles
SG7_NULL_MAX_FALSE_FLAGS = 0  # ruling B7: ... with 0 false flags, else SG 7 uninformative
# choice: windows whose masked variance is below this fraction of the template's own
# variance scale are treated as flat (NCC undefined -> 0); prevents FFT round-off in a
# constant label region from producing spurious large NCC values.
SG7_FLAT_REL_EPS = 1e-6

# ----------------------------------------------------------------------------- SG 9
SG9_ARM_MAX_LETTERS = 1  # DECL-SG 9: NULL, REV and CTRL each <= 1 letter in R
SG9_ARMS = ("NULL", "REV", "CTRL")

# ----------------------------------------------------------------------------- SG 11 layout
SG11_MIN_ROWS = 2  # DECL-SG 11
SG11_BASELINE_MAX_DEG = 10.0  # DECL-SG 11
SG11_PITCH_CV_MAX = 0.20  # DECL-SG 11
SG11_HEIGHT_MM = (2.0, 4.0)  # DECL-SG 11
SG11_HEIGHT_FRACTION_MIN = None  # ruling B8 REVISED (19:41Z): median bar only; the fraction in 2-4 mm is
# reported with no bar until declared from REF reads of sealed known-text bank windows
SG11_MIN_ROWS_FOR_CV = 3  # ruling B9: pitch CV needs >= 2 pitches, so SG 11 needs >= 3 rows
# choices for the coded row finder (letters come from the agreed boxes only):
SG11_ROW_MIN_LETTERS = 3  # a baseline is fitted to >= 3 letters (2 points always fit a line)
SG11_LINK_DX_H = 2.5  # neighbours: centre gap <= 2.5 letter heights horizontally
SG11_LINK_DY_H = 0.5  # and <= 0.5 letter heights vertically (rows ~1.5 h apart never link)

# ----------------------------------------------------------------------------- SG 13
SG13_RADIUS_PX = 250.0  # DECL-SG 13: "same kind within 250 px"
SG13_FRACTION = 0.50  # DECL-SG 13

# ----------------------------------------------------------------------------- SG 14
SG14_ROT_DEG = 15.0  # DECL-SG 14: "a 15 deg render rotation"
SG14_FRACTION = 0.50  # DECL-SG 14: keeps >= 50 %

# choice: inclusive bars on quantities derived by floating-point arithmetic (heights in
# mm from px / (px/mm), angles, CV) are compared with a relative tolerance of 1e-9, so a
# value that equals a bar exactly in real arithmetic is not failed by round-off.  1e-9 of
# 4 mm is 4 femtometres: this never lowers a bar in any physical sense.
BAR_REL_EPS = 1e-9

# Items of DECL-SG, 0..14 (K7: no form unless all pass).
SG_ITEMS = tuple(str(i) for i in range(15))
# Items (or parts) this code evaluates mechanically; all others must be attested by a
# record (RULES.md id) supplied by the orchestrator.
COMPUTED_ITEMS = ("1", "2", "3", "4", "5", "6", "7", "9", "11", "13")
# ruling B13 / B14: reads whose readers must be pairwise disjoint and each cover every
# available reader model (arms and band sealers included: ASK.md Q2 default).
FRESH_READS = ("discovery", "confirmation", "slice_-1", "slice_+1", "second_lineage", "retrace", "rotation",
               "arm_NULL", "arm_REV", "arm_CTRL", "band_sealers")
PARTIAL_ITEMS = {"14": "rotation part computed; RAW-F/B profile and unit-test parts attested"}
