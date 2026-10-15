# Provenance: Project HERCULES | owner the owner | [id removed]
"""Named constants of the HERCULES deterministic scorer.

Every value that the specification leaves to the implementation is fixed here with a
comment saying why.  Values given by the specification are marked "spec".
"""

from __future__ import annotations

# ----------------------------------------------------------------------------- versioning
# Recorded in every score output and in the input hash, so that a change of scorer logic
# can never silently reproduce an old hash.
SCORER_VERSION = "hercules-scorer-1.0.0"

# ----------------------------------------------------------------------------- orders / sides
TEXT = "text"  # spec C: the order in which text is expected to appear
NONTEXT = "nontext"  # spec C: the control order (no text expected)
ORDERS = (TEXT, NONTEXT)
LEFT = "left"
RIGHT = "right"
SIDES = (LEFT, RIGHT)

# ----------------------------------------------------------------------------- matching (spec D)
R_PRIMARY = 250.0  # spec D: primary matching radius, canvas px
R_SECONDARY = 150.0  # spec D: secondary radius, reported alongside the primary
RADII = (R_PRIMARY, R_SECONDARY)  # order in which radii are evaluated / reported
# Radius used for the permutation null, C_net, p and p_max.  Choice: primary radius only
# (the spec defines one null; R=150 is reported as raw counts).
NULL_RADIUS = R_PRIMARY
# The radius test is inclusive (distance <= R), as written in spec D.
RADIUS_INCLUSIVE = True

# ----------------------------------------------------------------------------- permutation null (spec E)
N_PERM_DEFAULT = 5000  # spec K: production number of permutations
# Fixed documented seed for the identity-permutation null.  Choice: the build date
# 2026-09-24 written as an integer.
SEED_DEFAULT = 20260924
# Permutations are drawn per window from np.random.default_rng(SeedSequence([seed, *w]))
# where w = first WINDOW_HASH_WORDS little-endian uint32 words of sha256(window_id).
# Choice: this makes permutation j of window W identical for every arm and reader
# (required by max-T) and independent of which other windows are in the decision.
WINDOW_HASH_WORDS = 4
# Number of permutations processed per vectorised block (memory bound only; results do
# not depend on it).
NULL_BLOCK = 256
# Policy for a declared (reader, window) pair with no item in the reader output.
# Choice: the reader named nothing there (C_all = E_null = C_net = 0) and still counts
# in the arm mean; the pair is listed under "missing_items".
MISSING_ITEM_POLICY = "zero"

# ----------------------------------------------------------------------------- consensus (spec F, G, I)
CONSENSUS_RADIUS = 150.0  # spec F
CONSENSUS_MIN_READERS = 2  # spec F
N_SEALERS = 3  # spec F: a seal is built from exactly 3 sealers
# Greedy clustering (spec F leaves the details open).  Choice:
#  1. drop unknown namings; order the rest canonically by (reader_id sorted as str,
#     index in that reader's list) -- this position is the naming's "rank";
#  2. candidate edges = pairs of namings of the SAME kind from DIFFERENT readers with
#     distance <= radius, sorted by (distance, rank_a, rank_b), rank_a < rank_b;
#  3. walk the edges; an edge whose two namings are both unused seeds a group;
#  4. extend the group with unused namings of the same kind from readers not yet in the
#     group that lie within radius of EVERY member (complete linkage), picking the
#     candidate with the smallest max-distance to the members, ties by rank; repeat;
#  5. group position = arithmetic mean of member positions (math.fsum, rank order).
CONSENSUS_LINKAGE = "complete"
CONSENSUS_EDGE_ORDER = ("distance", "rank_a", "rank_b")
# Seed for the between-reader identity-shuffle null (spec G).  Choice: SEED_DEFAULT + 1 so
# that it never shares a stream with the seal-permutation null.
SHUFFLE_SEED_DEFAULT = SEED_DEFAULT + 1
# Unknown namings are removed before the shuffle (they never agree), so identities are
# permuted over the positions of each reader's KNOWN namings only.
SHUFFLE_DROP_UNKNOWN = True

# ----------------------------------------------------------------------------- SG 1c (spec H)
SG1C_MIN_NULL_TILES = 40  # spec H
SG1C_PERCENTILE = 99  # spec H
SG1C_PERCENTILE_METHOD = "higher"  # spec H
SG1C_MARGIN = 10  # spec H: agreed - p99 >= margin

# ----------------------------------------------------------------------------- discovery (spec I)
DISCOVERY_K_DEFAULT = 5  # spec I (raised later from an empirical false-discovery calibration)
DISCOVERY_NONTEXT_MAX = 1  # spec I: non-text agreed count must be <= 1
DISCOVERY_N_READERS = 3  # spec I: "2 of 3" -- exactly three readers are required

# ----------------------------------------------------------------------------- confidence labels
CONF_FIRM = "firm"
CONF_TENTATIVE = "tentative"
CONFS = (CONF_FIRM, CONF_TENTATIVE)

# ----------------------------------------------------------------------------- unicode handling
# Reader characters are brought to Unicode NFC before the letter table lookup and before
# the "one character" schema check (so a base letter + combining mark counts as one char).
INPUT_UNICODE_FORM = "NFC"
# Unicode general category that must never appear in canonical JSON or sealed files.
FORBIDDEN_CATEGORY = "Cf"
