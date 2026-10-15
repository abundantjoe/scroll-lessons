# Provenance: Project HERCULES | owner the owner | [id removed]
"""bf16 (AMX autocast) run of the UNCHANGED p4o_tiles.py builder (DECL-P4-14-A2 item 2).
The only change: FastModel runs the official model under torch.autocast('cpu', bfloat16) and returns fp32 logits.
The builder's start-up layout check (fp32 vs channels_last fp32) is the FIRST call and is left in fp32, so it tests
what it was written to test; every later call (the tiles) is bf16. Same CLI as p4o_tiles.py.
Permitted for title-zone tiles only after p4o_bf16_check.py PASSES on r0 c5 (<= 1 % of pixels differ > 2/255)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p4o_resumable as R  # noqa: E402  (within-tile resume; patches infer_1667.card_tiling)
import p4o_tiles as P  # noqa: E402

R.TAG["tag"] = "bf16"

_Base = P.FastModel


class BF16Model(_Base):
    calls = 0

    def __call__(self, t):
        BF16Model.calls += 1
        if BF16Model.calls == 1:
            return super().__call__(t)
        with self.torch.autocast(device_type="cpu", dtype=self.torch.bfloat16):
            out = super().__call__(t)
        out.logits = out.logits.float()
        return out


P.FastModel = BF16Model
if __name__ == "__main__":
    print('{"precision": "bf16 autocast (tiles); layout check fp32", "within_tile_resume": true}', flush=True)
    P.main()
