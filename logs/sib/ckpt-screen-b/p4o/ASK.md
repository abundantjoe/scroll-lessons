Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (ckpt-screen-b, P4-O), 2026-09-26 21:25Z. Work continues meanwhile.

1. Cost. At the documented geometry (2.4 um, 62 slices, card stride 128) one 2 x 2 cm tile takes about 3.3-4.2 CPU-h. That is ~400 CPU-h for c0-c17 x r0-r5 per checkpoint, or ~4-5 days wall with 4 workers.
   The option is stride 256, i.e. no overlap averaging. It cuts the cost 4x (~1 h per tile), but the card only mentions 128 (2x) and 64 (8x), so it departs from the card.
   Running now: stride 128, r0-r1 first (title zone c10-c17 plus the c0-c9 control). Tell me if you want stride 256 or GPU capacity instead.
2. Order. The input is the organizer surface volume itself, so the documented training convention applies directly: iterations 1-5 use slices ascending (reverse_layers False, as for l_2); iteration 0 is reversed. Only that order is mapped for P4-O. Say if you want both orders (2x cost).

## 2026-09-27 07:55Z: re-normalisation test (undeclared, numbers only; p4o/renorm_test.json)
Region: the 768 x 768 centre of r0 c7 (the known-text gate), iteration-5, mesh-valid 1.0.
- Input (clip/255): mean 0.267, std 0.141.
- Training input implied by the weights (bn1 fit, corr 0.99998): mean 0.243, std 0.163.
- Fitted affine correction: a = 1.152, b = -0.065. It is small: the Paris 4 input is already near the training scale.

| prediction u8 | mean | std | p5 | p95 | frac > 127 |
|---|---|---|---|---|---|
| baseline | 124.9 | 54.2 | 60 | 217 | 0.43 |
| renormalised | 106.6 | 46.0 | 59 | 200 | 0.29 |

- Reading: the correction changes mean/std by ~15%, mostly by moving the upper tail down; the low tail is unchanged.
- A near-global affine input change cannot create ink/papyrus separation the model does not already see. The o2s1 gate failure (0 letters) is more likely a domain gap (Paris 4 BM18 Paganin contrast vs the PHerc1667 l_2 training scan) than a scale error.
- Proposal: do NOT spend fleet compute on a renormalised iteration-5 run. If the orchestrator wants the question closed cheaply, declare one renormalised gate tile (r0 c7, ~3.3 CPU-h) read as its own tiny batch, with the same gate bar.
- Mean/std alone cannot answer legibility, and no read happened here.
