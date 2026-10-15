# Provenance: Project HERCULES | owner the owner | [id removed]
"""HERCULES deterministic scorer and seal tooling.

Public API (see the individual modules for the specification sections they implement):

* A  ``validate_reader_output``                      (schema.py)
* B  ``normalize_letter``, ``LETTER_TABLE``           (letters.py)
* C  ``DisplayMap``, ``item_namings``                 (display.py)
* D  ``match_letters``                                (matching.py)
* E  ``window_permutations``, ``null_match_counts``, ``permutation_p``,
     ``arm_summed_mean_cnet``, ``max_t_p``            (null.py)
* F  ``agreed_letters``, ``make_seal``                (consensus.py)
* G  ``identity_shuffle_null``                        (consensus.py)
* H  ``sg1c_pass``, ``sg1c_evaluate``                 (consensus.py)
* I  ``discovery``                                    (consensus.py)
* J  ``seal_encrypt``, ``seal_decrypt``, ``keygen``   (seal.py), ``canonical_json`` (canon.py)
* K  ``score_decision``                               (score.py)
"""

from .canon import canonical_bytes, canonical_json, hash_json, sha256_hex
from .consensus import agreed_letters, discovery, identity_shuffle_null, make_seal, sg1c_evaluate, sg1c_pass
from .display import DisplayMap, item_namings
from .letters import CANONICAL_KINDS, LETTER_TABLE, normalize_letter
from .matching import match_letters
from .null import arm_summed_mean_cnet, max_t_p, null_match_counts, permutation_p, window_permutations
from .schema import validate_reader_output
from .score import score_decision
from .seal import keygen, seal_decrypt, seal_encrypt

__all__ = [
    "CANONICAL_KINDS",
    "DisplayMap",
    "LETTER_TABLE",
    "agreed_letters",
    "arm_summed_mean_cnet",
    "canonical_bytes",
    "canonical_json",
    "discovery",
    "hash_json",
    "identity_shuffle_null",
    "item_namings",
    "keygen",
    "make_seal",
    "match_letters",
    "max_t_p",
    "normalize_letter",
    "null_match_counts",
    "permutation_p",
    "score_decision",
    "seal_decrypt",
    "seal_encrypt",
    "sg1c_evaluate",
    "sg1c_pass",
    "sha256_hex",
    "validate_reader_output",
    "window_permutations",
]
