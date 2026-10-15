# Provenance: Project HERCULES | owner the owner | [id removed]
"""AMX equivalence gate: does a bf16 (AMX) base-model map reproduce the validated fp32 C2-NT map?

Numbers only. The inputs are uint8 model maps (official infer output: clip(sigmoid, 0, 1) * 255, truncated), read as
arrays and never displayed.

Inputs (each .npy, or .tif/.tiff read with tifffile; all the same 2-D shape):
  --fp32-fwd / --bf16-fwd   forward-order maps (C2-NT, no TTA) from the fp32 and the bf16 chain
  --fp32-rev / --bf16-rev   reverse-order maps (optional; needed for the reverse-AUC bar)
  --labels                  organizer label image (raw values; binarised as in tools/c3/auc_eval.py:
                            ink = label > (min + max) / 2 of the label value range, blank = label == 0, rest ignored)
                            or already binary with --labels-binary (1 ink, 0 blank, other values ignored)
  --valid                   valid mask (nonzero = valid; e.g. render-valid AND organizer supervision mask, as C3-NT-R1)

Metrics (hercules.metrics.pixel, the code hashed in DECL-C3):
  pearson           Pearson r(fp32, bf16) over valid pixels, per order
  auc_forward       Mann-Whitney AUC of the bf16 forward map against the labels over valid pixels (fp32 also reported)
  auc_reverse       same for the reverse-order map
  frac_within_2     fraction of valid pixels with |bf16 - fp32| <= 2 grey levels, per order
  max_abs_diff      max |bf16 - fp32| over valid pixels, per order
  (also: mean_abs_diff, histogram of |diff| 0..5+, delta AUC bf16 - fp32)

Bars (proposal logs/sib/amx/proposals/decl_amx_1.txt; defaults below, overridable):
  pearson >= 0.999 (both orders present: each), auc_forward(bf16) >= 0.987, auc_reverse(bf16) < 0.60,
  frac_within_2 >= 0.999 (each order). PASS only if every bar is evaluable and met; a missing reverse pair makes the
  reverse bar NOT_EVALUATED and the verdict INCOMPLETE."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(_REPO, "src"))
from hercules.metrics.pixel import auc, pearson  # noqa: E402

BARS = dict(pearson_min=0.999, auc_forward_min=0.987, auc_reverse_max=0.60, frac_within_2_min=0.999)
TOL_GREY = 2


def load_map(path):
    if path.endswith(".npy"):
        a = np.load(path)
    elif path.endswith((".tif", ".tiff")):
        import tifffile
        a = tifffile.imread(path)
    else:
        raise ValueError(f"unsupported map format: {path}")
    a = np.asarray(a)
    if a.ndim == 3 and a.shape[0] == 1:
        a = a[0]
    if a.ndim != 2:
        raise ValueError(f"{path}: expected a 2-D map, got shape {a.shape}")
    return a


def binarize_labels(raw):
    """tools/c3/auc_eval.py rule: ink (1) = raw > (min + max) / 2; blank (0) = raw == 0; others -1 (ignored)."""
    raw = np.asarray(raw)
    lo, hi = float(raw.min()), float(raw.max())
    out = np.full(raw.shape, -1, np.int8)
    out[raw == 0] = 0
    if hi > lo:
        out[raw.astype(np.float64) > (lo + hi) / 2.0] = 1
    return out


def _check_u8(name, a):
    a = np.asarray(a)
    if a.dtype != np.uint8:
        raise TypeError(f"{name}: maps must be uint8 (official infer output), got {a.dtype}")
    return a


def pair_metrics(m32, m16, valid):
    """Equivalence of one order: bf16 map m16 against fp32 map m32 over valid pixels."""
    m32, m16 = _check_u8("fp32", m32), _check_u8("bf16", m16)
    if m32.shape != m16.shape or m32.shape != valid.shape:
        raise ValueError(f"shape mismatch: fp32 {m32.shape}, bf16 {m16.shape}, valid {valid.shape}")
    n = int(valid.sum())
    if n == 0:
        raise ValueError("no valid pixels")
    d = np.abs(m16.astype(np.int16) - m32.astype(np.int16))[valid]
    hist = np.bincount(np.minimum(d, 5), minlength=6)
    return dict(n_valid=n, pearson=pearson(m32, m16, valid), max_abs_diff=int(d.max()),
                mean_abs_diff=float(d.mean()), frac_within_2=float((d <= TOL_GREY).sum() / n),
                frac_identical=float((d == 0).sum() / n),
                abs_diff_hist_0_1_2_3_4_5plus=[int(v) for v in hist])


def gate(fp32_fwd, bf16_fwd, labels_bin, valid, fp32_rev=None, bf16_rev=None, bars=None):
    """labels_bin: 1 ink, 0 blank, other values ignored. valid: bool mask. Returns a JSON-able dict with a verdict."""
    bars = dict(BARS, **(bars or {}))
    valid = np.asarray(valid).astype(bool)
    labels_bin = np.asarray(labels_bin)
    if labels_bin.shape != valid.shape:
        raise ValueError(f"labels shape {labels_bin.shape} != valid shape {valid.shape}")
    res = dict(bars=bars, tol_grey=TOL_GREY, n_ink=int(((labels_bin == 1) & valid).sum()),
               n_blank=int(((labels_bin == 0) & valid).sum()), orders={})
    orders = [("forward", fp32_fwd, bf16_fwd)]
    if fp32_rev is not None and bf16_rev is not None:
        orders.append(("reverse", fp32_rev, bf16_rev))
    elif (fp32_rev is None) != (bf16_rev is None):
        raise ValueError("reverse maps must be given as a pair (fp32 and bf16) or not at all")
    for name, m32, m16 in orders:
        r = pair_metrics(m32, m16, valid)
        r["auc_fp32"] = auc(m32, labels_bin, valid)
        r["auc_bf16"] = auc(m16, labels_bin, valid)
        r["delta_auc_bf16_minus_fp32"] = r["auc_bf16"] - r["auc_fp32"]
        res["orders"][name] = r
    checks = {}
    for name, r in res["orders"].items():
        checks[f"pearson_{name}"] = bool(r["pearson"] >= bars["pearson_min"])
        checks[f"frac_within_2_{name}"] = bool(r["frac_within_2"] >= bars["frac_within_2_min"])
    fwd = res["orders"]["forward"]
    checks["auc_forward"] = bool(np.isfinite(fwd["auc_bf16"]) and fwd["auc_bf16"] >= bars["auc_forward_min"])
    if "reverse" in res["orders"]:
        rv = res["orders"]["reverse"]
        checks["auc_reverse"] = bool(np.isfinite(rv["auc_bf16"]) and rv["auc_bf16"] < bars["auc_reverse_max"])
    else:
        checks["auc_reverse"] = None
    res["checks"] = checks
    res["pearson"] = min(r["pearson"] for r in res["orders"].values())
    res["frac_within_2"] = min(r["frac_within_2"] for r in res["orders"].values())
    res["max_abs_diff"] = max(r["max_abs_diff"] for r in res["orders"].values())
    res["auc_forward"] = fwd["auc_bf16"]
    res["auc_reverse"] = res["orders"]["reverse"]["auc_bf16"] if "reverse" in res["orders"] else None
    if any(v is False for v in checks.values()):
        res["verdict"] = "FAIL"
    elif any(v is None for v in checks.values()):
        res["verdict"] = "INCOMPLETE"
    else:
        res["verdict"] = "PASS"
    return res


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fp32-fwd", required=True)
    ap.add_argument("--bf16-fwd", required=True)
    ap.add_argument("--fp32-rev")
    ap.add_argument("--bf16-rev")
    ap.add_argument("--labels", required=True)
    ap.add_argument("--labels-binary", action="store_true")
    ap.add_argument("--valid", required=True)
    ap.add_argument("--out", required=True, help="output JSON")
    a = ap.parse_args(argv)
    paths = {k: getattr(a, k) for k in ("fp32_fwd", "bf16_fwd", "fp32_rev", "bf16_rev", "labels", "valid") if getattr(a, k)}
    lab = load_map(a.labels)
    lab = np.where((lab == 0) | (lab == 1), lab, -1).astype(np.int8) if a.labels_binary else binarize_labels(lab)
    res = gate(load_map(a.fp32_fwd), load_map(a.bf16_fwd), lab, load_map(a.valid) != 0,
               load_map(a.fp32_rev) if a.fp32_rev else None, load_map(a.bf16_rev) if a.bf16_rev else None)
    res["inputs"] = {k: dict(path=v, sha256=_sha(v)) for k, v in paths.items()}
    res["code_sha256"] = _sha(os.path.abspath(__file__))
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: res[k] for k in ("verdict", "pearson", "auc_forward", "auc_reverse", "frac_within_2", "max_abs_diff")}))
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
