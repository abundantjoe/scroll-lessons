# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-14-A2 item 2 equivalence check, numbers only: full-resolution u8 predictions of ONE tile (r0 c5) from the
fp32 and the bf16 run. PASS iff <= 1 % of mesh-valid pixels differ by more than 2/255. Also reported: all pixels,
the 1068 px display, max |diff|, histogram of |diff|. Usage: p4o_bf16_check.py <fp32.npy> <bf16.npy> <out.json>"""
import hashlib, json, sys
import numpy as np
import cv2
a, b = np.load(sys.argv[1]), np.load(sys.argv[2])
assert a.shape == b.shape and a.dtype == b.dtype == np.uint8
d = np.abs(a.astype(np.int16) - b.astype(np.int16))
valid = (a > 0) | (b > 0)
da = cv2.resize(a, (1068, 1068), interpolation=cv2.INTER_AREA).astype(np.int16)
db = cv2.resize(b, (1068, 1068), interpolation=cv2.INTER_AREA).astype(np.int16)
dd = np.abs(da - db)
frac_valid = float((d[valid] > 2).mean()) if valid.any() else None
res = dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
           rule="DECL-P4-14-A2 item 2: <= 1 % of pixels differing from fp32 by more than 2/255",
           fp32_sha256=hashlib.sha256(a.tobytes()).hexdigest(), bf16_sha256=hashlib.sha256(b.tobytes()).hexdigest(),
           shape=list(a.shape), n_valid_px=int(valid.sum()),
           frac_gt2_valid=frac_valid, frac_gt2_all=float((d > 2).mean()), frac_gt2_display=float((dd > 2).mean()),
           max_abs_diff=int(d.max()), mean_abs_diff_valid=float(d[valid].mean()) if valid.any() else None,
           hist_abs_diff_valid={str(k): int(v) for k, v in enumerate(np.bincount(np.minimum(d[valid], 10).ravel(), minlength=11))},
           valid_mask_identical=bool(np.array_equal(a == 0, b == 0)))
res["pass"] = bool(frac_valid is not None and frac_valid <= 0.01)
json.dump(res, open(sys.argv[3], "w"), indent=1)
print(json.dumps(res))
