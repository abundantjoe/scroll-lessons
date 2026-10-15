# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4 anti-hallucination validation: scorer, nulls, windows, P4-L tile checks (synthetic only; the
test text is invented and is not any edition of PHerc. Paris 4)."""

import copy

import numpy as np
import pytest

from hercules.tribunal import p4val as V

COL = ["ΤΟΝΔΕΚΑΙΜΕΝ", "ΠΡΟΣΗΔΟΝΗΝ", "ΑΙΣΘΗΣΕΙΣ", "ΚΑΙΤΑΜΟΥΣ", "ΛΟΓΟΙΣΤΕ"]   # invented
OTHER = ["ΒΡΩΜΑΤΑΞΥΛΑ", "ΦΩΝΗΚΕΡΑΣ", "ΨΥΧΗΓΑΜΟΣ", "ΖΩΗΟΦΙΣΧΥ", "ΝΥΞΑΣΤΡΟΝ"]  # invented


def _reader(lines, seed=0, drop=0.0, noise=0.0, mirror=False, line_h=150.0):
    rng = np.random.default_rng(seed)
    out = []
    for i, ln in enumerate(lines):
        for j, ch in enumerate(ln):
            if rng.random() < drop:
                continue
            if rng.random() < noise:
                ch = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΤΥΦΧΨΩ"[rng.integers(23)]
            x = 100 + 70 * (len(ln) - 1 - j if mirror else j) + rng.normal(0, 5)
            y = 120 + line_h * i + rng.normal(0, 8)
            out.append({"ch": ch, "x": x, "y": y, "box": [x - 25, y - 60, x + 25, y + 60], "conf": "tentative"})
    return out


def test_normalize_published_line():
    got = V.normalize_published_line("ἡδον[ὴν] καὶ ς ọ.")
    kinds = [k for k, _ in got]
    vis = [v for _, v in got]
    assert kinds[:4] == ["Η", "Δ", "Ο", "Ν"] and vis[:4] == [True] * 4 and vis[4:6] == [False, False]
    assert got[-1][0] == "Ο" and got[-1][1] is True           # underdot: visible trace
    assert got[-2][0] == "Ϲ"                               # final sigma -> lunate
    assert V.normalize_published_line("[ΑΒ]") == [("Α", False), ("Β", False)]


def test_perfect_reader_scores_all_and_beats_nulls():
    r = {"r1": _reader(COL), "r2": _reader(COL, seed=1, drop=0.2)}
    res = V.score_known_text(r, {"colA": COL, "colB": OTHER}, n_perm=60)
    n_vis = sum(len(s) for s in COL)
    assert res["readers"]["r1"]["M"] == n_vis and res["readers"]["r1"]["column"] == "colA"
    assert res["readers"]["r1"]["p_text_shuffle"] <= 2 / 61 and res["readers"]["r1"]["p_reader_shuffle"] <= 2 / 61
    assert res["pooled"]["p_text_shuffle"] <= 2 / 61


def test_random_reader_is_not_significant():
    rng = np.random.default_rng(3)
    fake = ["".join("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΤΥΦΧΨΩ"[i] for i in rng.integers(0, 23, len(s))) for s in COL]
    res = V.score_known_text({"r": _reader(fake, seed=4)}, {"colA": COL, "colB": OTHER}, n_perm=60)
    assert res["readers"]["r"]["p_text_shuffle"] > 0.05


def test_position_agreement_mirrored_order_scores_lower():
    ok = V.score_known_text({"r": _reader(COL)}, {"colA": COL}, n_perm=0)["readers"]["r"]["M"]
    mir = V.score_known_text({"r": _reader(COL, mirror=True)}, {"colA": COL}, n_perm=0)["readers"]["r"]["M"]
    assert mir < ok / 2


def test_line_order_is_enforced():
    rev = V.score_known_text({"r": _reader(COL[::-1])}, {"colA": COL}, n_perm=0)["readers"]["r"]
    fwd = V.score_known_text({"r": _reader(COL)}, {"colA": COL}, n_perm=0)["readers"]["r"]
    assert rev["M"] < fwd["M"] / 2  # residual matches are chance local alignments; the nulls absorb them


def test_restored_letters_never_count():
    col = ["[ΤΟΝΔΕ]ΚΑΙ"]
    res = V.score_known_text({"r": _reader(["ΤΟΝΔΕΚΑΙ"])}, {"c": col}, n_perm=0)
    assert res["readers"]["r"]["M"] == 3


def test_known_text_windows_from_census_profile():
    N = None
    census = [[5, 5, 3, 3, 4, 6, N, 13, 4, 8, N, 1, 2, 8] + [N] * 6,
              [11, 6, 2, 6, 4, 4, N, 8, 6, 9, 1, 7, 8, 2] + [N] * 6,
              [12, 4, 2, 4, 4, 6, 1, 9, 10, 6] + [N] * 10,
              [5, 9, 1, 4, 4, 7, N, 7, 7, 9] + [N] * 10,
              [9, 10, N, 6, 3, 6, 1, 6, 4, 5] + [N] * 10,
              [5, 8, 1, 10, 10, 9, 2, 8, 10, 4] + [N] * 10]   # the census counts quoted in DOSSIER 4.2
    w = V.known_text_windows(census)
    assert w["last_text_col"] == 9 and w["slots"][0]["tile_cols"] == [7, 8, 9]
    assert 11 in w["short_block_cols_r0r1"] and 2 in w["intercolumn_candidates"]


def _l2_manifest():
    T = 8343
    tiles = [{"file": f"tiles/x_r{r}_c{c}.png", "r": r, "c": c, "valid_fraction": 0.8,
              "canvas_rows": [r * T, (r + 1) * T], "canvas_cols": [c * T, (c + 1) * T]} for r in (0, 1) for c in range(3)]
    return {"thresholds": {"T_mid": 93, "T_hi": 203}, "slab": {"slices": [48, 60], "centre": 54, "n": 13},
            "display": "clip(255*(max - T_mid)/(T_hi - T_mid), 0, 255), rint, uint8; 0 outside mesh-valid; "
                       "cv2.INTER_AREA 8343 -> 1068", "checks": {"png_only_IHDR_IDAT_IEND": True}, "tiles": tiles}


@pytest.mark.parametrize("fault", ["origin", "tmid", "slab", "dup", "vf", "swap"])
def test_l2_manifest_faults(fault):
    m = _l2_manifest()
    assert V.check_l2_manifest(m)["passed"]
    b = copy.deepcopy(m)
    if fault == "origin":
        b["tiles"][2]["canvas_cols"] = [x + 8 for x in b["tiles"][2]["canvas_cols"]]
    elif fault == "tmid":
        b["thresholds"]["T_mid"] = 94
    elif fault == "slab":
        b["slab"] = {"slices": [49, 61], "centre": 55, "n": 13}
    elif fault == "dup":
        b["tiles"].append(copy.deepcopy(b["tiles"][0]))
    elif fault == "vf":
        b["tiles"][1]["valid_fraction"] = 0.4
    else:
        b["tiles"][1]["r"], b["tiles"][1]["c"] = 1, 0
    assert not V.check_l2_manifest(b)["passed"]


def test_l2_pixel_faults():
    rng = np.random.default_rng(5)
    T, side = 600, 96
    H, W, n = 2 * T, 3 * T, 20
    from scipy.ndimage import gaussian_filter
    stack = np.clip(gaussian_filter(rng.normal(100, 30, (n, H // 4, W // 4)), (0.5, 2, 2)), 0, 255)
    stack = np.kron(stack, np.ones((1, 4, 4))).astype(np.uint8)
    valid = np.ones((H, W), bool)
    valid[:, :50] = False
    slab = (7, 13)
    good = V.expected_l2_tile(stack, valid, 1, 1, T, slab, 93, 203, side)
    assert V.verify_l2_tile(good, stack, valid, 1, 1, T, slab, 93, 203, side)["passed"]
    faults = {
        "offset8": V.expected_l2_tile(np.roll(stack, -8, 2), np.roll(valid, -8, 1), 1, 1, T, slab, 93, 203, side),
        "rot90": np.ascontiguousarray(np.rot90(good, -1)),
        "mirror": np.ascontiguousarray(good[:, ::-1]),
        "wrong_threshold": V.expected_l2_tile(stack, valid, 1, 1, T, slab, 80, 203, side),
        "slab_off_by_one": V.expected_l2_tile(stack, valid, 1, 1, T, (8, 14), 93, 203, side),
    }
    for name, t in faults.items():
        assert not V.verify_l2_tile(t, stack, valid, 1, 1, T, slab, 93, 203, side)["passed"], name


def test_known_text_gate():
    cen = [{"c": c, "rows": "Y", "letters": 6} for c in range(3)] + [{"c": c, "rows": "N", "letters": 0} for c in range(3, 9)]
    g = V.known_text_gate(cen)
    assert g["n_pool"] == 9 and g["passed"] and abs(g["fraction"] - 1 / 3) < 1e-12
    g2 = V.known_text_gate(cen[1:])
    assert not g2["passed"] and g2["status"] == "uninformative"


# ----------------------------------------------------------------------------- P4-O

SHA = "a" * 64


def _prov():
    return {"checkpoints": {
        "ok": {"source_url": "https://x", "weights_sha256": SHA, "quoted_training_statement": ["segments of other scrolls"],
               "paris4_scroll1_in_documentation": False, "eligible": True},
        "p4": {"source_url": "https://y", "weights_sha256": "b" * 64, "documentation": ["card"],
               "paris4_in_training": "YES (documented)", "eligible": False}}}


def test_p4o_provenance_consistency():
    r = V.check_p4o_provenance(_prov())
    assert r["passed"] and r["eligible_sha256"] == [SHA]
    for mut in ("p4yes", "nosha", "nodoc", "noexplicit"):
        p = copy.deepcopy(_prov())
        e = p["checkpoints"]["ok"]
        if mut == "p4yes":
            e["paris4_scroll1_in_documentation"] = "YES"
        elif mut == "nosha":
            e["weights_sha256"] = "unknown"
        elif mut == "nodoc":
            del e["quoted_training_statement"]
        else:
            del e["paris4_scroll1_in_documentation"]
        assert not V.check_p4o_provenance(p)["passed"], mut
    lst = {"checkpoints": [dict(_prov()["checkpoints"]["p4"], checkpoint="p4c")]}
    assert V.check_p4o_provenance(lst)["passed"] and V.check_p4o_provenance(lst)["eligible_sha256"] == []


def _p4o_manifest():
    T = 8343
    return {"checkpoint_sha256": SHA, "segment": "20260701183124-w010-027", "native_voxel_um": 9.6,
            "display": "raw 0-255 prediction, 0 outside mesh-valid, cv2.INTER_AREA 8343 -> 1068",
            "tiles": [{"file": f"t/x_r{r}_c{c}.png", "r": r, "c": c, "valid_fraction": 0.9,
                       "canvas_rows": [r * T, (r + 1) * T], "canvas_cols": [c * T, (c + 1) * T]} for r in (0, 1) for c in (0, 1)]}


@pytest.mark.parametrize("fault", ["ckpt", "display", "origin", "noresample", "segment"])
def test_p4o_manifest_faults(fault):
    m = _p4o_manifest()
    assert V.check_p4o_manifest(m, [SHA])["passed"]
    b = copy.deepcopy(m)
    if fault == "ckpt":
        b["checkpoint_sha256"] = "b" * 64
    elif fault == "display":
        b["display"] = "clip(255*(max - T_mid)/(T_hi - T_mid)), INTER_AREA"
    elif fault == "origin":
        b["tiles"][0]["canvas_rows"] = [8, 8351]
    elif fault == "noresample":
        del b["native_voxel_um"]
    else:
        b["segment"] = "20260701183125-w028-037"
    assert not V.check_p4o_manifest(b, [SHA])["passed"]
