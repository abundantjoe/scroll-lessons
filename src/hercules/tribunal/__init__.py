# Provenance: Project HERCULES | owner the owner | [id removed]
"""TRIBUNAL: anti-self-deception controls run in every reading batch (DECL-EMPNULL).

Modules
-------
preread  : planted-fault checks the pipeline calls before any read (fail closed).
faults   : fault injectors used by the runner and the tests.
synth    : synthetic CT volume / tifxyz / zarr world (TEST HELPER ONLY).
runner   : injects every fault into many synthetic worlds and reports the catch rate.
controls : batch-control image builders (positive canaries, baits, mirror canaries).
validity : batch-validity scorer and the I16 run-halt rule.
empnull  : empirical null tile builder (plan section 8.2).

Nothing here reads, views or describes an image; all outputs are numbers, hashes or
image bytes written for the orchestrator's harness.
"""

PROVENANCE = "Provenance: Project HERCULES | owner the owner | [id removed]"
TRIBUNAL_VERSION = "tribunal-0.1.0"
