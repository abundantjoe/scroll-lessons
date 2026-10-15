# Provenance: Project HERCULES | owner the owner | [id removed]
"""Build logs/sib/regrescan/REPORT.md and summary.json from the stage records."""
import hashlib
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
LOGS = REPO / "logs" / "sib" / "regrescan"
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
SCROLLS = ["PHerc1203", "PHerc0846A"]


def j(p):
    return json.loads(Path(p).read_text())


def f(x, n=3):
    return "n/a" if x is None else f"{x:.{n}f}"


def main():
    summ = {"provenance": PROV, "task": "regrescan", "scrolls": {}}
    L = [PROV, "", "# regrescan: 9.362 um <-> 2.403 um CT-to-CT affine registration (PHerc1203, PHerc0846A)", ""]
    L += ["STATUS: DONE", ""]
    rows = []
    for s in SCROLLS:
        fa = j(LOGS / s / "final_affine.json")
        co = j(LOGS / s / "coarse.json")
        mid = j(LOGS / s / "mid.json")
        ck = fa["check"]
        mc = fa["model_comparison_heldout"]
        summ["scrolls"][s] = {
            "pass": fa["bars"]["pass"], "heldout_median_r": ck["heldout_median_r"],
            "heldout_rms_vox": ck["heldout_rms_vox"], "control_median_r": ck["control_median_r"],
            "control_median_drop": ck["control_median_drop"], "control_frac_lower": ck["control_frac_lower"],
            "fit_rms_vox": fa["fit"]["rms_vox"], "fit_n_used": fa["fit"]["n_used"],
            "F": fa["F_from_metadata"], "z0": fa["transform"]["z0"], "M": fa["transform"]["M"],
            "b": fa["transform"]["b"], "Pm": fa["transform"]["Pm"], "orientation": fa["transform"]["orientation"],
            "H_9um_to_rescan_raw_xyz1": fa["H_9um_to_rescan_raw_xyz1"],
            "band": fa["band"], "remount": fa["remount"], "M_decomposition": fa["M_decomposition"],
            "translation_only_heldout_rms_vox": mc["translation_only_rms_vox"],
            "final_affine_sha256": hashlib.sha256((LOGS / s / "final_affine.json").read_bytes()).hexdigest()}
        rows.append((s, fa, co, mid))
    L += ["## Verdict (bars: held-out median r >= 0.85 AND RMS <= 1.5 vox on 16 NEW patches; control must drop clearly)", "",
          "| Scroll | held-out median r | held-out RMS (9 um vox) | control median r | median drop | ctrl < aligned | fit RMS (24) | RESULT |",
          "|---|---|---|---|---|---|---|---|"]
    for s, fa, co, mid in rows:
        ck = fa["check"]
        L.append(f"| {s} | {f(ck['heldout_median_r'])} | {f(ck['heldout_rms_vox'])} | {f(ck['control_median_r'])} | "
                 f"{f(ck['control_median_drop'])} | {round(ck['control_frac_lower'] * ck['n_ok'])}/{ck['n_ok']} | "
                 f"{f(fa['fit']['rms_vox'])} | **{'PASS' if fa['bars']['pass'] else 'FAIL'}** |")
    c1p = LOGS / "PHerc0846A" / "fine_check_fititer1.json"
    if c1p.exists():
        c1 = j(c1p)
        b = c1["bars"]
        L.append(f"| PHerc0846A (fit iteration 1, sha256 bcb9c43f..., as specified by the orchestrator) | {f(c1['heldout_median_r'])} | "
                 f"{f(c1['heldout_rms_vox'])} | {f(c1['median_r_ctrl'])} | {f(c1['median_drop'])} | "
                 f"{round(c1['frac_ctrl_lower'] * c1['n_ok'])}/{c1['n_ok']} | {f(j(LOGS / 'PHerc0846A' / 'fine_fit_iter1.json')['fit_rms'])} | "
                 f"**{'PASS' if b['pass'] else 'FAIL'}** |")
        summ["scrolls"]["PHerc0846A"]["check_with_fit_iteration1"] = {
            "heldout_median_r": c1["heldout_median_r"], "heldout_rms_vox": c1["heldout_rms_vox"],
            "control_median_r": c1["median_r_ctrl"], "control_median_drop": c1["median_drop"],
            "control_frac_lower": c1["frac_ctrl_lower"], "pass": b["pass"],
            "fit_sha256": hashlib.sha256((LOGS / "PHerc0846A" / "fine_fit_iter1.json").read_bytes()).hexdigest()}
    L += ["", "Two 0846A rows: the pipeline ran fit -> refit (re-measure at the level-0 affine) -> check as one command, as for 1203, so the first check "
          "used fit iteration 2 (sha256 5dbe5d1f...), which was not committed before that check. The orchestrator then specified the committed iteration-1 fit "
          "(sha256 bcb9c43f...); that check was run once, on the same 16 pre-fixed patches with unchanged bars and control criterion. Both results are reported; "
          "neither was selected by outcome."]
    L += ["", "Archive reference (not used by the fit): 1203 band z 7936-11824, held-out r 0.964; 0846A band z 1856-5744, held-out r 0.946. "
          "Our held-out r is lower than the archive's; our r is plain Pearson over the whole 48x256x256 block including air/gaps "
          "(no mask, no filtering) at the fitted affine, so it is not directly comparable to an archive r of unknown definition.", ""]
    L += ["## Model and affines", "",
          "rescan voxel (x, y, z) = F * (p + t(p) - z0 e_z), t(p) = M (p - Pm) + b; p = 9 um level-0 voxel centre (x, y, z); "
          "F = samplePixelSize_9 / samplePixelSize_r from each metadata.json = 0.009362 / 0.002403 = "
          f"{rows[0][1]['F_from_metadata']:.10f}. No axis flip or permutation was found, so the raw rescan frame = canonical. "
          "Full 4x4 homogeneous matrices (both directions) are in `<scroll>/final_affine.json`.", ""]
    for s, fa, co, mid in rows:
        t = fa["transform"]
        md = fa["M_decomposition"]
        H = np.array(fa["H_9um_to_rescan_raw_xyz1"])
        L += [f"### {s}", "",
              f"- 9 um: `{fa['volume_9um']}` (metadata sha256 {fa['metadata_sha256']['v9']})",
              f"- rescan: `{fa['volume_rescan']}` (metadata sha256 {fa['metadata_sha256']['vr']})",
              f"- z0 = {t['z0']:.0f}; b = ({', '.join(f'{v:.3f}' for v in t['b'])}); Pm = ({', '.join(f'{v:.1f}' for v in t['Pm'])})",
              "- M = [" + "; ".join(" ".join(f"{v:+.6f}" for v in r) for r in t["M"]) + "]",
              f"- M decomposition: rotation vector (deg, x y z) = ({', '.join(f'{v:+.4f}' for v in md['rotation_vector_deg_xyz'])}); "
              f"z-axis tilt {md['z_axis_tilt_deg']:.4f} deg; trace(M) = {md['trace_M']:+.6f} (volumetric scale deviation)",
              "- H (9 um xyz1 -> rescan raw xyz1) = [" + "; ".join(" ".join(f"{v:.6f}" for v in r) for r in H[:3]) + "]",
              f"- Band (9 um z covered by the rescan array): centre column {f(fa['band']['rescan_centre_column_z9'][0], 1)}-{f(fa['band']['rescan_centre_column_z9'][1], 1)}; "
              f"any column {f(fa['band']['z9_range_any_column'][0], 1)}-{f(fa['band']['z9_range_any_column'][1], 1)}; "
              f"all columns {f(fa['band']['z9_common_all_columns'][0], 1)}-{f(fa['band']['z9_common_all_columns'][1], 1)}; "
              f"rescan disc centre (x, y) = ({', '.join(f'{v:.1f}' for v in fa['band']['rescan_centre_xy9'])}), radius {fa['band']['rescan_disc_radius_9um_vox']:.1f} vox",
              f"- Held-out model comparison: translation-only RMS {f(fa['model_comparison_heldout']['translation_only_rms_vox'])} vox "
              f"(max {f(fa['model_comparison_heldout']['translation_only_max_vox'])}) vs affine {f(fa['model_comparison_heldout']['affine_rms_vox'])} vox",
              ""]
    fa0 = j(LOGS / "PHerc0846A" / "final_affine.json")
    rv = fa0["M_decomposition"]["rotation_vector_deg_xyz"]
    fi1 = j(LOGS / "PHerc0846A" / "fine_fit_iter1.json")
    M1 = np.array(fi1["transform"]["M"])
    W1 = 0.5 * (M1 - M1.T)
    rv1 = np.degrees([W1[2, 1], W1[0, 2], W1[1, 0]])
    L += ["## 0846A tilt against the archive", "",
          "| Source | rotation about x (deg) | rotation about y (deg) | rotation about z (deg) |", "|---|---|---|---|",
          f"| Archive (remount tilt) | 0.26 | 0.12 | n/a |",
          f"| M, fit iteration 2 (antisymmetric part) | {rv[0]:+.3f} | {rv[1]:+.3f} | {rv[2]:+.3f} |",
          f"| M, fit iteration 1 (antisymmetric part) | {rv1[0]:+.3f} | {rv1[1]:+.3f} | {rv1[2]:+.3f} |",
          "", f"Magnitudes agree with the archive to <= 0.01 deg (iteration 2: |x| {abs(rv[0]):.3f}, |y| {abs(rv[1]):.3f}); the archive gives no signs or axis convention, so only magnitudes are compared. "
          f"z-axis tilt implied by M: {fa0['M_decomposition']['z_axis_tilt_deg']:.3f} deg.", ""]
    L += ["## Diagnostic only (does not change any verdict): r at each check patch's own optimum", "",
          "Run after the check. Per check patch, the transform is offset by that patch's own measured residual, so r is the best any registration could reach on that block.", "",
          "| Scroll | median r at the affine | median r at own optimum | patches >= 0.85 at own optimum |", "|---|---|---|---|"]
    for s_ in SCROLLS:
        cz = j(LOGS / s_ / "ceiling.json")
        L.append(f"| {s_} | {cz['median_r_affine']:.4f} | {cz['median_r_own_optimum']:.4f} | "
                 f"{sum(r['r_at_own_optimum'] >= 0.85 for r in cz['rows'])}/16 |")
    L += ["", "Reading: for 0846A the per-patch optimum reaches median 0.878, so the r shortfall under the affine (0.844) is at least partly the "
          "mapping model (local non-affine misfit at sub-voxel residuals: residual RMS 0.72 vox), not only the scans' different contrast. "
          "A non-affine model would need its own pre-registration and NEW check patches (see ASK.md); nothing of that kind was run.", ""]
    L += ["## Method and step results", "",
          "1. **Flips and remounts first.** 9 um level 4 (149.8 um) and rescan level 5 (76.9 um, area-downsampled by F/2 onto the level-4 grid) streamed whole. "
          "Exhaustive search at ~600 um (bin 4): z flip x x mirror x in-plane rotation 0-358 deg in 2 deg steps (720 candidates; y flip = mirror + 180 deg), "
          "full 3-D translation, whole-volume NCC by FFT. Then rotation refined at ~300 um (0.5 deg, then 0.1 deg steps).",
          "2. **Coarse z-band by whole-slice 3-D NCC** of the full rescan against every z placement of the 9 um volume (~300 um).",
          "3. **Coarse tilt**: 3-D phase correlation of 18 sub-blocks (2 z x 3 x 3) at 150 um -> affine; both rotation sign conventions tried, better kept.",
          "4. **Mid level**: 9 um level 1 vs rescan level 2 (F/2), 24 patches of 64x256x256 9 um voxels, 2 iterations -> affine.",
          "5. **Level 0** (only at the patches): 48x256x256 9 um blocks vs the rescan area-integrated (exact box) onto the 9 um grid; "
          "3-D phase correlation (sub-voxel, window-bias-corrected, c6.phase_correlate_3d) at 24 fit patches -> affine (3-sigma MAD rejection; none rejected); "
          "re-measured once at the new affine (refit).",
          "6. **Check on 16 NEW patches** (patch list committed before any level-0 read; min distance to a fit patch in the table below): r = Pearson "
          "between the 9 um block and the resampled rescan at the fitted affine; residual = phase-correlation shift at the fitted affine; RMS = sqrt(mean |residual|^2) (3-D).",
          "7. **Control**: the same block with the transform shifted by half the local sheet pitch along the local sheet normal. "
          "Normal = dominant structure-tensor eigenvector; pitch = first local maximum of the block autocorrelation along it. "
          "Criterion fixed before the check (in patches.json): median(r - r_ctrl) >= 0.20 and r_ctrl < r in >= 15/16.", ""]
    L += ["| Scroll | remount best (600 um) | best NCC | best distinct alternative | refined rotation (deg) | z-band peak (9 um z of rescan top) | peak NCC | 2nd peak >4 bins | mid median r | mid RMS (L1 vox) | min check-fit dist (vox) |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s, fa, co, mid in rows:
        b = co["remount_600um"]["best"]
        ru = co["remount_600um"]["runner_up_distinct"]
        zb = co["zband_300um"]
        h = mid["history"][-1]
        pt = j(LOGS / s / "patches.json")
        L.append(f"| {s} | zflip={b['zflip']} mirror={b['mirror']} rot={b['theta']:.0f} | {b['ncc']:.4f} | "
                 f"zflip={ru['zflip']} mirror={ru['mirror']} rot={ru['theta']:.0f}: {ru['ncc']:.4f} | {co['remount']['theta_deg']:.3f} | "
                 f"{zb['best_z9_level0_of_rescan_top']:.0f} | {zb['best_ncc']:.4f} | {zb['second_best_ncc_gt4bins']:.4f} | "
                 f"{h['median_r']:.3f} | {h['rms_L1']:.3f} | {pt['min_check_to_fit_distance_vox']:.0f} |")
    L += ["", "The remount rotation from step 1 is not physical tilt: the fully fitted M at level 0 absorbs it (see M decomposition). "
          "The 300 um z-band profile is monotone on both sides of its single peak for both scrolls (no competing z placement).", ""]
    L += ["## Per-patch held-out results (16 NEW check patches)", ""]
    for s, fa, co, mid in rows:
        L += [f"### {s}", "", "| # | centre (x, y, z) | r | r_ctrl | residual (x, y, z) vox | pitch vox | PC peak |", "|---|---|---|---|---|---|---|"]
        for i, p in enumerate(fa["check"]["patches"]):
            L.append(f"| {i} | ({', '.join(f'{v:.0f}' for v in p['centre_xyz'])}) | {f(p['r'])} | {f(p['r_ctrl'])} | "
                     f"({', '.join(f'{v:+.2f}' for v in p['residual_xyz'])}) | {f(p['pitch_vox'], 1)} | {f(p['peak'])} |")
        L.append("")
    L += ["Fit-patch tables (24 each, with residuals against the final affine) are in `<scroll>/final_affine.json` under `fit.patches`.", ""]
    L += ["## Round-trip tests", "",
          "`tests/sib_regrescan_test_roundtrip.py` (run: `source /opt/hv/bin/activate && PYTHONPATH=src pytest -q tests/sib_regrescan_test_roundtrip.py`): "
          "level-pyramid transform conversions exact (< 1e-8); 9 -> 2.4 -> 9 um round trip on the fitted affines of both scrolls: exact < 1e-6 vox and, "
          "with the rescan coordinate rounded to the nearest stored voxel, < 0.5 vox (5000 random band points each); synthetic flips; NCC-map vs brute force; "
          "template search with out-of-volume placement; pitch estimator on synthetic sheets. Result recorded in `tests_result.txt`.", ""]
    L += ["## Exact commands", "",
          "```",
          "# environment (fresh container): uv venv /opt/hv --python 3.11; uv pip install numpy scipy 'zarr<3' numcodecs pytest s3fs fsspec ...",
          "# every stage via the logger (appends to logs/sib/regrescan/runs.jsonl):",
          "export PYTHONPATH=src OMP_NUM_THREADS=4",
          "for S in PHerc1203 PHerc0846A; do for STAGE in meta coarse patches mid fit refit check final; do",
          "  tools/sib/regrescan/run.sh /opt/hv/bin/python tools/sib/regrescan/regrescan.py $STAGE $S; done; done",
          "/opt/hv/bin/python tools/sib/regrescan/make_report.py",
          "```", "",
          "Data read: anonymous S3 only (`s3://vesuvius-challenge-open-data/`), 9 um levels 0, 1, 4 and rescan levels 0, 2, 5; level 0 only in the patch boxes "
          "(~9 GB of rescan level 0 per scroll per pass). sha256 of every metadata.json, .zattrs and level .zarray is in `<scroll>/meta.json`. "
          "Voxel sizes from metadata.json (`scan.tomo.acquisition.detector.samplePixelSize`).", ""]
    runs = [json.loads(x) for x in (LOGS / "runs.jsonl").read_text().splitlines() if x.strip()]
    bad = [r for r in runs if r.get("exit_code") != 0]
    L += ["## Failed or killed runs (from runs.jsonl)", "", f"{len(runs)} runs logged; {len(bad)} did not exit 0:", "",
          "| utc start | utc end | exit | command |", "|---|---|---|---|"]
    for r in bad:
        L.append(f"| {r['utc_start']} | {r['utc_end']} | {r['exit_code']} | `{r['command'].split('regrescan.py ')[-1]}` |")
    L += [""]
    L += ["## Failures and deviations (all logged in runs.jsonl)", "",
          "- Coarse run 1 (1203) killed by me to add FFT caching (exit 143); run 2 killed by the container OOM (exit 137) in a 150 um NCC-map rotation pass (>14 GB); "
          "replaced by a second 300 um pass at 0.1 deg steps (M is fitted fully downstream, so the coarse rotation only initialises).",
          "- Coarse run 3 (0846A, exit 143) killed by me because it had started with the pre-fix code (it would have hit the same OOM).",
          "- First level-0 fit run of 1203 killed after 4 patches (its runs.jsonl line is reconstructed from the surviving output log; exit code not recorded): the spectral-peak sheet-pitch estimator gave ~47 vox (low-frequency leakage). "
          "Replaced by the structure-tensor/autocorrelation estimator (median ~9 vox); stale rows deleted; no control number from the old estimator is used.",
          "- The stage-position z0 prior in meta.json (1203: ~7965) is a hint only and was not used; it ignores zarr_export crops.",
          "- The pyramid convention (level-k voxel centred at 2^k i + (2^k-1)/2) is assumed for the coarse and mid levels only; level 0 is exact and absorbs any bias.",
          "- Flip handling on non-power-of-two shapes is approximate at coarse levels (not exercised: no flip was found).", ""]
    L += ["## Integrity", "",
          "CT only. No ink model was run on any volume. No image, slice or map was written or viewed; only numbers and hashes. "
          "No manual annotation; no training. No PHerc0841 data touched. No seals, keys or encrypted files touched.", ""]
    L += ["## What the orchestrator needs to declare next", "",
          "1. Accept or reject each scroll's registration against the C6 bars (table above) and record the affines by the sha256 of `<scroll>/final_affine.json` "
          f"(1203 {summ['scrolls']['PHerc1203']['final_affine_sha256'][:16]}..., 0846A {summ['scrolls']['PHerc0846A']['final_affine_sha256'][:16]}...).",
          "2. Declare the T-RESCAN band extents per scroll (proposal in `proposals/DECL-REGRESCAN.md`), including the 128-vox exclusion rule for windows found with 2.4 um help.",
          "3. Before any 2.4 um ink result exists (I11): commit each band's 9 um search order. Nothing here produced any ink output.", ""]
    (LOGS / "REPORT.md").write_text("\n".join(L) + "\n")
    (LOGS / "summary.json").write_text(json.dumps(summ, indent=1) + "\n")


if __name__ == "__main__":
    main()
