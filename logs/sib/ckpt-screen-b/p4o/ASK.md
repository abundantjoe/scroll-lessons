Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (ckpt-screen-b, P4-O), 2026-09-26 21:25Z. Work continues meanwhile.

1. Cost. At the documented geometry (2.4 um, 62 slices, card stride 128) one 2 x 2 cm tile takes about 3.3-4.2 CPU-h. That is ~400 CPU-h for c0-c17 x r0-r5 per checkpoint, or ~4-5 days wall with 4 workers.
   The option is stride 256, i.e. no overlap averaging. It cuts the cost 4x (~1 h per tile), but the card only mentions 128 (2x) and 64 (8x), so it departs from the card.
   Running now: stride 128, r0-r1 first (title zone c10-c17 plus the c0-c9 control). Tell me if you want stride 256 or GPU capacity instead.
2. Order. The input is the organizer surface volume itself, so the documented training convention applies directly: iterations 1-5 use slices ascending (reverse_layers False, as for l_2); iteration 0 is reversed. Only that order is mapped for P4-O. Say if you want both orders (2x cost).
