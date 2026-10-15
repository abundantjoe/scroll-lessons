# Provenance: Project HERCULES | owner the owner | [id removed]
"""HERCULES submission gate SG (RULES.md DECL-SG) and Route Z discovery (DECL-EMPNULL).

Modules: constants (fixed bars, each citing its item), gate (discovery, R, SG items,
runner ``sg_check``), copytest (SG 7, masked FFT NCC), synth (synthetic known-answer
inputs for tests), cli (``python -m hercules.sg.cli``), copytest_null (synthetic null of
the SG 7 statistic).  Nothing here opens, displays or describes an image.
"""

from .gate import sg_check

__all__ = ["sg_check"]
