"""Fill the number tables of README.md, docs/RESULTS.md, docs/EXPERIMENTS.md and SUBMISSION.md from committed result JSON, between
<!-- BEGIN:name --> / <!-- END:name --> markers, so no number is transcribed by hand.  python write_tables.py"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
J = lambda *p: json.load(open(os.path.join(REPO, *p)))  # noqa: E731
RR = J('results', 'control_strips_rerun', 'results.json')
OR = J('results', 'control_strips', 'original_results.json')
NE = J('results', 'margin_artifact', 'natural_experiment_PHerc0268.json')
FT = J('results', 'margin_artifact', 'fill_test_PHerc0268_aggregate.json')
BR = J('results', 'blind_read', 'read2_calibrated_controls.json')
A = RR['arms']
LAB = {'REF': 'full context (reference), its valid px in node rows 42-107', 'Z13': '13-row strips, blank margins', 'P13': '13-row + 2 real padding rows',
       'F13': '13-row, margin reflect-filled (partial fix, exploratory)', 'Z20': '20-row strips, blank margins',
       'D8': '13-row moved 8 vox outward (negative control)', 'FD8': 'same, with the fill (exploratory; conservative floor, RESULTS §1)'}


def trunc(x, nd):
    """Format x with nd decimals, truncated toward zero (a range bound is never rounded up)."""
    q = 10 ** nd
    return f'{int(x * q) / q:.{nd}f}'


def f(x, n=3, pct=False):
    if x is None:
        return 'n/a'
    return f'{100 * x:.{max(n - 2, 1)}f} %' if pct else f'{x:.{n}f}'


def ci(m):
    lo, hi = m.get('recall_ci95') or (None, None)
    return f"{f(m['recall'])} [{f(lo)}, {f(hi)}]" if lo is not None else f(m.get('recall'))


def control_table():
    rows = ['| arm | strong ink in letter boxes | strong ink outside | enrichment E | recall [95 % CI] | r vs REF | box AUC | coverage |',
            '|---|---|---|---|---|---|---|---|']
    for k in ('REF', 'Z13', 'P13', 'F13', 'Z20', 'D8', 'FD8'):
        m = A.get(k)
        if not m:
            continue
        rows.append(f"| {LAB[k]} (`{k}`) | {f(m['f_in'], 4, True)} | {f(m['f_out'], 4, True)} | {f(m['E'], 1)} | {ci(m) if k != 'REF' else '1 (by definition)'} | "
                    f"{f(m['r'])} | {f(m['auc_box'])} | {f(m['coverage'], 2)} |")
    return '\n'.join(rows)


def headline_table():
    # full context = the reference map restricted to the same pixels the 13-row strips score (Z13 ref_* fields)
    z, fl, d8, fd8 = A['Z13'], A['F13'], A['D8'], A.get('FD8') or {}
    return '\n'.join([
        '| PHerc0343 positive control (13 known letters), d = +1 | full context (same pixels) | 13-row strip, blank margins (as usual) | same strip, margin reflect-filled (exploratory) | negative control: moved 8 vox outward (plain / filled, exploratory; conservative, RESULTS §1) |',
        '|---|---|---|---|---|',
        f"| strong ink (p > 0.55) inside the letter boxes | {f(z['ref_f_in'], 4, True)} | {f(z['f_in'], 4, True)} | **{f(fl['f_in'], 4, True)}** | {f(d8['f_in'], 4, True)} / {f(fd8.get('f_in'), 4, True)} |",
        f"| recall of the full-context strong ink [95 % CI, 13 letters] | 1 | {ci(z)} | **{ci(fl)}** | {f(d8['recall'])} / {f(fd8.get('recall'))} |",
        f"| box AUC (letter boxes vs the rest, rank-based) | {f(z['ref_auc_box'])} | {f(z['auc_box'])} | **{f(fl['auc_box'])}** | {f(d8['auc_box'])} / {f(fd8.get('auc_box'))} |",
        f"| strong ink outside the letter boxes | {f(z['ref_f_out'], 4, True)} | {f(z['f_out'], 4, True)} | {f(fl['f_out'], 4, True)} | {f(d8['f_out'], 4, True)} / {f(fd8.get('f_out'), 4, True)} |",
    ])


def _repro_cmp():
    """Original-vs-rerun comparisons: the scorer's strip arms plus the reference map itself."""
    cmp = dict(RR.get('reproduction_vs_original') or {})
    o, n = OR['arms'].get(f"REF_d{RR.get('depth', 1)}"), A.get('REF')
    if o and n:
        cmp = {'REF': {k: dict(original=o[k], rerun=n[k], abs_diff=abs(o[k] - n[k])) for k in ('f_in', 'f_out')}, **cmp}
    return cmp


def repro_table():
    cmp = _repro_cmp()
    rows = ['| arm | metric | original run (14 Oct) | rerun (fresh clone, fresh CT and weights) | abs. difference |', '|---|---|---|---|---|']
    for k, d in cmp.items():
        for metric, v in d.items():
            rows.append(f"| `{k}` | {metric} | {f(v['original'], 4)} | {f(v['rerun'], 4)} | {f(v['abs_diff'], 4)} |")
    return '\n'.join(rows)


def decisions_table():
    od = OR.get('decisions', {})
    rd = RR.get('decisions_preregistered', {})
    names = [('Z13_sees_ink', '13-row strips see ink (recall >= 0.5, E >= 5, r >= 0.6)'), ('Z20_sees_ink', '20-row strips see ink'),
             ('Z13_margin_artifact', 'blank margins create an edge-band artifact on the control'), ('P13_padding_fixes', '2 real padding rows fix it (recall >= 0.7, r >= 0.8, band rule not met)'),
             ('D8_no_ink_arm_works', 'negative ("no-ink") arm works (D8 in-box strong <= 0.2 x Z13)')]
    rows = ['| pre-registered decision | original run | rerun |', '|---|---|---|']
    for k, lab in names:
        rows.append(f'| {lab} | {od.get(k)} | {rd.get(k)} |')
    dz, d1 = OR['arms'].get('Z13_d-2', {}), OR['arms'].get('Z13_d1', {})
    rows.append(f"| depth, report only (no threshold): recall of `Z13` at d = -2 / at d = +1 | "
                f"{od.get('Z13_depth_recall_ratio_dm2_over_dp1')} ({dz.get('recall')} / {d1.get('recall')}) | not rerun |")
    ex = RR.get('exploratory', {})
    x13 = OR['arms'].get('X13_d1', {})
    rows += ['', '| exploratory (not pre-registered) | rerun |', '|---|---|',
             f"| margin fill: 13-row strips see ink (same rule) | {ex.get('F13_sees_ink')} |",
             f"| margin fill meets the stricter 'fix' bar (recall >= 0.7, r >= 0.8; applied post hoc) | {ex.get('F13_fixes_bar_R0.7_r0.8')} (original run: {od.get('exploratory_F13_margin_fill_fixes')}) |",
             f"| filled displaced copy (`FD8`): strong fraction, all scored px (conservative floor) | {f(ex.get('fill_no_ink_floor_f055_all'), 4, True)} |",
             f"| extrapolated 2-row padding (`X13`, original run only, not rerun) meets the 'fix' bar | "
             f"{od.get('exploratory_X13_extrap_padding_fixes')} (original run: recall {x13.get('recall')}, r {x13.get('r')}, E {x13.get('E')}) |"]
    return '\n'.join(rows)


def pherc0268_table():
    h = NE['by_render_height']
    rows = ['| PHerc0268 strips (aggregate only) | value |', '|---|---|']
    for H, d in h.items():
        rows.append(f"| natural experiment, {H} px strips: ink proxy at rows 50-90, 30-row vs 10-row blank top margin | {f(d['mean_alpha_30row_margin'])} vs {f(d['mean_alpha_10row_margin'])}; higher with 30 in {d['strips_where_30_gt_10']}/{d['n_strips_with_both_classes']} strips |")
    rows.append(f"| strong ink (p > 0.55) before -> after the margin fill, {FT['n_strips']} strips | {f(FT['strong_ink_frac_p055_before'][0], 4, True)}-{f(FT['strong_ink_frac_p055_before'][1], 4, True)} -> {f(FT['strong_ink_frac_p055_after_fill'][0], 4, True)}-{f(FT['strong_ink_frac_p055_after_fill'][1], 4, True)} ({trunc(FT['fold_drop_range'][0], 2)}-{trunc(FT['fold_drop_range'][1], 1)}× lower) |")
    rows.append(f"| edge-band / middle ink ratio before -> after the fill | {FT['band_mid_ratio_before'][0]:.2f}-{FT['band_mid_ratio_before'][1]:.2f} -> {FT['band_mid_ratio_after'][0]:.2f}-{FT['band_mid_ratio_after'][1]:.2f}; below 1.3 in {FT['strips_band_ratio_below_1p3_after_fill']}/{FT['n_strips']} |")
    return '\n'.join(rows)


def blind_table():
    rows = ['| reader | AUC, 8 positives vs 5 negatives | positives flagged letter-like | negatives flagged |', '|---|---|---|---|']
    for r in BR['readers']:
        rows.append(f"| {r['reader']} | {r['auc_all_pos_vs_neg']:.3f} | {r['positives_flagged']}/8 | {r['negatives_flagged']}/5 |")
    return '\n'.join(rows)


def summary_text():
    z, fl = A['Z13'], A['F13']
    h = NE['by_render_height']['260']
    aucs = [r['auc_all_pos_vs_neg'] for r in BR['readers']]
    cb = J('results', 'blind_read', 'colour_baseline.json')
    t = (f"Ink models in villa normalise each 128 px patch over all of its voxels, and thin strips rendered by "
         f"vc_render_tifxyz carry all-zero rows at their edges, so every edge patch is normalised with zeros. On a public "
         f"positive control (PHerc0343, Erwin Nieuwlaar's First Letters segment, 13 letters), 13-row strips cut as mass "
         f"runs cut them lowered the share of strong-ink pixels in the letter boxes from {f(z['ref_f_in'], 4, True)} to "
         f"{f(z['f_in'], 4, True)} (recall {ci(z)}); a pre-registered test failed them. Reflect-filling the margin for "
         f"the ink models (exploratory) raised it to {f(fl['f_in'], 4, True)}, but recovered only {ci(fl)} of the "
         f"full-context strong pixels and doubled those outside the letters ({f(fl['f_out'], 4, True)} vs "
         f"{f(z['ref_f_out'], 4, True)}). On the unread PHerc0268 the blank margins instead painted false bands (ink "
         f"proxy {f(h['mean_alpha_30row_margin'])} vs {f(h['mean_alpha_10row_margin'])} by margin class at the same "
         f"rows); the fill lowered strong ink {trunc(FT['fold_drop_range'][0], 2)}-{trunc(FT['fold_drop_range'][1], 1)}× "
         f"and removed the bands in {FT['strips_band_ratio_below_1p3_after_fill']} of {FT['n_strips']} strips. Why the "
         f"sign differs is open. We release the fill, a diagnostic kit, a positive-control-first protocol, a "
         f"hidden-control blind-read protocol (reader AUC {min(aucs):.3f}-{max(aucs):.3f}, colour alone reaches "
         f"{cb['colour_auc_all_pos_vs_neg']:.3f}), 33 lessons and a rerun with fresh data. No letters are claimed.")
    n = len(t.split())
    assert n <= 200, f'summary has {n} words'
    return t


def model_fit():
    """Fig. 1b: pooled 260 px row profile of the PHerc0268 ink proxy vs the predicted blank share (30-row top margin)."""
    import numpy as np
    from stripqc import patchgrid
    prof = np.array([np.nan if v is None else v for v in NE['row_profile_mean_alpha']['260']['mean_alpha_by_row']], float)
    v = np.zeros(260, bool)
    v[30:230] = True
    share = np.asarray(patchgrid.blank_share(v), float)
    m = np.isfinite(prof) & v
    r = np.corrcoef(share[m], prof[m])[0, 1]
    p1, p2 = 30 + int(np.nanargmax(prof[30:130])), 130 + int(np.nanargmax(prof[130:230]))
    tr = 60 + int(np.nanargmin(prof[60:200]))
    return (f"- **Model fit (qualitative; MEASURED from the committed profile):** over the valid rows 30-229 of the "
            f"{NE['row_profile_mean_alpha']['260']['n_strips']} pooled 260 px strips, Pearson r = {r:.2f} between the "
            f"ink proxy and the predicted blank share. The bands peak at rows {p1} and {p2}, where the predicted share "
            f"falls from 1 toward 0, and the trough at row {tr} is where only blank-free patches contribute. The model "
            f"does not predict the low proxy right at the valid edges (rows 30-35: {np.nanmean(prof[30:36]):.3f}), where "
            f"the share is 1 (fig. 1b).")


def _decimals(x):
    t = repr(float(x))
    return len(t.split('.')[1]) if '.' in t and 'e' not in t else 6


def _ts(path, event):
    """Timestamp of the first log line '<ISO time> <event>' whose event text starts with `event`."""
    import datetime
    for line in open(os.path.join(REPO, path)):
        parts = line.split(maxsplit=1)
        if len(parts) == 2 and parts[1].strip().startswith(event):
            return datetime.datetime.fromisoformat(parts[0].replace('Z', '+00:00'))
    return None


def repro_note():
    cmp = _repro_cmp()
    vals = [(k, m, v) for k, d in cmp.items() for m, v in d.items() if v['original'] is not None and v['rerun'] is not None]
    same = sum(round(v['rerun'], _decimals(v['original'])) == v['original'] for _, _, v in vals)
    mx = max(v['abs_diff'] for _, _, v in vals)
    od, rd = OR.get('decisions', {}), RR.get('decisions_preregistered', {})
    dsame = all(od.get(k) == v for k, v in rd.items())
    R = 'results/control_strips_rerun/'
    t0, t1 = _ts(R + 'job.log', 'start'), _ts(R + 'job.log', 'reproduce.sh exit')
    a0, a1, a2, a3 = (_ts(R + 'run.log', x) for x in ('start', 'plain arms done', 'fill arms done', 'done'))
    mins = lambda a, b: f'{(b - a).total_seconds() / 60:.1f} min'  # noqa: E731
    mirror = [json.loads(l) for l in open(os.path.join(REPO, R + 'batch.log')) if l.startswith('{"mirror"')]
    fetched = sum(m['fetched_bytes'] for m in mirror)
    bs = J('results', 'control_strips_rerun', 'box_shift_check.json')
    nmaps = sum(1 for _ in open(os.path.join(REPO, R + 'ens_sha256.txt')))
    return '\n'.join([
        f"- **Match (MEASURED):** {same} of {len(vals)} compared values equal the original when rounded to the decimals the "
        f"original stored (3-4); the largest absolute difference is {mx:.6f}. All {len(rd)} thresholded pre-registered "
        f"decisions are {'identical' if dsame else 'NOT identical'}. Decision 6 (the depth ratio, report only) and the "
        f"exploratory `X13` arm were run in the original only.",
        "- **Limits of the match:** the original run kept its numbers rounded and not its maps, so the maps cannot be compared "
        f"bit for bit. The sha256 of all {nmaps} reproduced ensemble maps is in "
        "[`ens_sha256.txt`](../results/control_strips_rerun/ens_sha256.txt) for future comparisons.",
        f"- **Inputs:** {fetched / 1e9:.2f} GB of CT fetched fresh from S3; the weights downloaded fresh and passed their sha256. "
        "The segment repository was a local copy of commit `e8370f1`, not a fresh clone; its checksums passed.",
        f"- **Runtime (MEASURED, 4 cores, 3 ink runs at a time):** {mins(t0, t1)} for `reproduce.sh` in total: "
        f"{mins(t0, a0)} checksums and weights, {mins(a0, a1)} for the 19 plain strips (including the CT download), "
        f"{mins(a1, a2)} for the 10 filled strips, {mins(a2, a3)} scoring.",
        f"- **Box registration (MEASURED):** moving every letter box by ±{bs['shift_px']} px (one node) in x and y, "
        f"{len(bs['by_shift'])} positions in all, changes "
        f"{'no pre-registered or exploratory decision' if not bs['decisions_changed'] else 'these decisions: ' + ', '.join(bs['decisions_changed'])} "
        "([`box_shift_check.json`](../results/control_strips_rerun/box_shift_check.json)).",
    ])


def n_experiments():
    """Experiment branches of the private working repository (dominion): all its branches except main, the research log,
    the data archive and the checkpoint store."""
    s = open(os.path.join(REPO, 'BRANCH_INDEX.md')).read()
    sec = s[s.index('## dominion'):].split('\n## ')[0]
    rows = [r for r in sec.splitlines() if r.startswith('| `')]
    names = [r.split('|')[1].strip(' `') for r in rows]
    return len([n for n in names if n != 'main' and n != 'claude/gifted-bell-gavnl5' and not n.endswith(('-data', '-ckpt'))])


def form_text():
    """The 'What is your contribution?' answer of the Progress Prize form, numbers from the committed JSON."""
    em = J('results', 'experiments', 'experiment_map.json')
    z, fl = A['Z13'], A['F13']
    h = NE['by_render_height']['260']
    aucs = [r['auc_all_pos_vs_neg'] for r in BR['readers']]
    cb = J('results', 'blind_read', 'colour_baseline.json')
    cmp = _repro_cmp()
    vals = [v for d in cmp.values() for v in d.values() if v['original'] is not None and v['rerun'] is not None]
    same = sum(round(v['rerun'], _decimals(v['original'])) == v['original'] for v in vals)
    rd = RR.get('decisions_preregistered', {})
    dsame = all(OR.get('decisions', {}).get(k) == v for k, v in rd.items())
    nmaps = sum(1 for _ in open(os.path.join(REPO, 'results/control_strips_rerun/ens_sha256.txt')))
    ntests = sum(open(os.path.join(REPO, 'tests', f)).read().count('\ndef test_') for f in os.listdir(os.path.join(REPO, 'tests')) if f.startswith('test_'))
    return '\n\n'.join([
        f"Dominion is the record of {em['n_experiments']} experiments, run on {n_experiments()} experiment branches, a research "
        f"log and related repositories, on finding "
        f"ink inside carbonized Herculaneum scrolls. This release maps them with their outcomes ({em['n_published']} in full, "
        f"{em['n_withheld']} only counted for confidentiality) and packages the finding that survived validation: blank render "
        f"margins silently corrupt villa ink inference on thin strips. We measure the damage on a public positive control, "
        f"give a partial fix, and ship a kit (stripqc) to check your own runs.",
        "(1) Scroll data: PHerc0343 (volume 20250521140437, 8.64 µm, 116 keV) as the positive control, with Erwin "
        "Nieuwlaar's public First Letters segment and letter boxes (MIT); PHerc0268 (volume 20251110183117, 8.64 µm, "
        "116 keV), aggregate numbers only. Models: the organizers' ink_9um (seeds 42 and 43) and Erwin Nieuwlaar's "
        "dense_native. Renderer and inference: ScrollPrize/villa 41701aa. Dataset: Vesuvius Challenge - CT Scans of "
        "Herculaneum Papyri (Angelotti et al.), CC BY-NC 4.0.",
        "(2) vc_render_tifxyz renders of thin surface strips (fit-derived strips, ring patches, tile crops) carry all-zero "
        "rows at their edges, because border mesh nodes have no normal. villa's ink inference skips patches that are "
        "entirely empty but normalises partly blank ones with their zeros, and that code is unchanged on villa main as of "
        "14 Oct 2026. The defect is silent: villa raises no warning, and nothing in its output marks the affected edge rows.",
        f"(3) Results on real data: on the positive control (13 known letters, d = +1), 13-row strips cut as mass runs cut "
        f"them lowered the share of strong-ink pixels in the letter boxes from {f(z['ref_f_in'], 4, True)} to "
        f"{f(z['f_in'], 4, True)} (recall {ci(z)}, letter-bootstrap 95 % CI); a pre-registered test failed them. "
        f"Reflect-filling the margin for the ink models (stripqc.fill, exploratory) raised it to {f(fl['f_in'], 4, True)} "
        f"(box AUC {f(fl['auc_box'])}, full context {f(z['ref_auc_box'])}) but recovered only {ci(fl)} of the "
        f"full-context strong pixels and about doubled the strong pixels outside the letters, so it is a partial fix. On "
        f"PHerc0268 the same margins painted false ink bands in about 2/3 of the strips of a 56-strip mass run; inside the "
        f"strips the ink proxy at the same rows was {f(h['mean_alpha_30row_margin'])} vs {f(h['mean_alpha_10row_margin'])} "
        f"by blank-margin class, and the fill lowered strong ink {trunc(FT['fold_drop_range'][0], 2)}-"
        f"{trunc(FT['fold_drop_range'][1], 1)}× and removed the bands in {FT['strips_band_ratio_below_1p3_after_fill']} of "
        f"{FT['n_strips']} strips. Why the sign differs between the two scrolls is not explained. A blind-read protocol "
        f"with hidden positives and negatives reached reader AUC {min(aucs):.3f}-{max(aucs):.3f}, but colour alone "
        f"reaches {cb['colour_auc_all_pos_vs_neg']:.3f}, so it shows calibration to colour, not letter recognition. No "
        f"letters are claimed.",
        f"(4) Evidence: a pip-installable package with {ntests} synthetic tests; scripts/reproduce.sh reruns the control's "
        f"d = +1 arms (all but the exploratory X13) from public data in one command (1.6 GB of downloads, 71 min on 4 CPU cores); compared with the "
        f"committed original run (RESULTS §2), {same} of {len(vals)} of its values match at the stored precision and all {len(rd)} thresholded "
        f"pre-registered decisions are {'identical' if dsame else 'NOT identical'}; the sha256 of all {nmaps} maps; a "
        f"letter-box shift check; every number in the README's result tables generated from committed JSON. Also: the "
        f"experiment map (verdict and key numbers of every published experiment), 33 lessons, and the retracted claims of the "
        f"work behind them. Code MIT; results CC BY-NC 4.0. Run by AI research agents (Claude) directed by one owner; the "
        f"d = +1 positive-control numbers (all arms but X13) are reproduced by the scripts in this repository, the X13, d = -2 and strip-middle values come from the committed original run, and the other numbers (PHerc0268 "
        f"aggregates, blind-read scores, experiment map) are committed as JSON from the private working record.",
    ])


VERDICTS = ['PASSED', 'FAILED', 'NULL', 'INCONCLUSIVE', 'VOID', 'STOPPED', 'TOOL', 'UNKNOWN']
VERDICT_MEANING = {
    'PASSED': 'met its stated bars (declared before its data for pre-registered tests; for checks and infrastructure, its acceptance check)',
    'FAILED': 'missed its stated bars (declared before its data for pre-registered tests; for checks and infrastructure, its acceptance check)',
    'NULL': 'ran as declared and found nothing',
    'INCONCLUSIVE': 'ran, but the result cannot decide the question (for example, a detector too insensitive)',
    'VOID': 'invalidated under its own declared clause (for example, a metric mismatch or a freshness breach)',
    'STOPPED': 'stood down or stopped before its verdict step',
    'TOOL': 'built a tool or ran infrastructure; there is no hypothesis to pass or fail',
    'UNKNOWN': 'the outcome is not in the record',
}
MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()


def _em():
    return J('results', 'experiments', 'experiment_map.json')


def _anchor(title):
    """GitHub's heading anchor."""
    return re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')


def _cell(x):
    return str(x).replace('|', '\\|').replace('\n', ' ').strip()


def _period(p):
    if not p:
        return '-'
    a, b = (f'{int(d[8:10])} {MONTHS[int(d[5:7]) - 1]}' for d in p.split('..'))
    return f'{a} to {b}'


def _src(k):
    ref = re.sub(r'\s*@\s*', ' @ ', re.sub(r'^origin/', '', k['source_ref'].strip()))
    return f"`{_cell(k['source_path'])}` ({_cell(ref)})"


def _tally(es, withheld=0):
    import collections
    c = collections.Counter(e['verdict'] for e in es)
    parts = [f'{c[v]} {v.lower()}' for v in VERDICTS if c[v]]
    return ' · '.join(parts + ([f'{withheld} withheld'] if withheld else []))


def _withheld_note(em):
    fam = {f['key']: f for f in em['families']}
    assert fam['paris4']['withheld'] == em['n_withheld'] and not fam['paris4']['experiments']
    return (f"{em['n_withheld']} experiments are withheld and only counted: every experiment on PHerc. Paris 4, whatever it "
            "showed. The scroll is treated here as not officially read, so its per-experiment results are not published; withholding "
            "says nothing about their outcome.")


def experiments_table():
    """README: one row per experiment family, outcome counts from results/experiments/experiment_map.json."""
    em = _em()
    rows = ['| family | period | experiments | outcomes |', '|---|---|---:|---|']
    for f in em['families']:
        rows.append(f"| [{_cell(f['title'])}](docs/EXPERIMENTS.md#{_anchor(f['title'])}) | {_period(f['period'])} | "
                    f"{len(f['experiments']) + f['withheld']} | {_tally(f['experiments'], f['withheld'])} |")
    every = [e for f in em['families'] for e in f['experiments']]
    rows.append(f"| **all families** | | **{em['n_experiments']}** | {_tally(every, em['n_withheld'])} |")
    return '\n'.join(rows + [
        '',
        f"An experiment here is one question with its own verdict, listed once. The {em['n_experiments']} come from the research "
        f"log, the {n_experiments()} experiment branches and related repositories; "
        f"{sum(1 for e in every if e['verdict'] == 'PASSED')} of the {em['n_published']} published here passed. Passed and failed "
        "mean the experiment met or missed its stated bars (declared before its data for the pre-registered tests; some checks, "
        "such as the training-overlap screen and the data-offload self-test, had an acceptance check but no pre-registration); "
        "null means it ran as declared and found nothing; stopped means it was stood down before its verdict step; tool means it built "
        "a tool rather than testing a hypothesis. " + _withheld_note(em)])


def experiments_full():
    """docs/EXPERIMENTS.md: every published experiment with its verdict, numbers, sources and lesson."""
    em = _em()
    L = [f"Survey date {em['survey_date']}. {em['n_experiments']} experiments in {len(em['families'])} families: "
         f"{em['n_published']} published here, {em['n_withheld']} withheld and only counted. Generated from "
         "[`results/experiments/experiment_map.json`](../results/experiments/experiment_map.json) by "
         "`scripts/write_tables.py`.", '', em['note'], '', '**Verdicts**', '']
    L += [f'- **{v}**: {VERDICT_MEANING[v]}.' for v in VERDICTS]
    L += ['', '**Families**', '', '| family | period | experiments | outcomes |', '|---|---|---:|---|']
    L += [f"| [{_cell(f['title'])}](#{_anchor(f['title'])}) | {_period(f['period'])} | {len(f['experiments']) + f['withheld']} | "
          f"{_tally(f['experiments'], f['withheld'])} |" for f in em['families']]
    L += ['', _withheld_note(em)]
    for f in em['families']:
        L += ['', f"## {f['title']}", '',
              (f"{_period(f['period'])} 2026 · " if f['period'] else '') + f"{len(f['experiments']) + f['withheld']} experiments · "
              f"{_tally(f['experiments'], f['withheld'])}", '', f['summary']]
        if f['withheld'] and f['experiments']:
            L += ['', f"{f['withheld']} further experiment{'s' if f['withheld'] > 1 else ''} of this family "
                      f"{'are' if f['withheld'] > 1 else 'is'} withheld and only counted (see above)."]
        for e in f['experiments']:
            L += ['', f"### {e['name']}", '', f"**Verdict: {e['verdict']}**", '', f"**Question.** {e['question'].strip()}"]
            if e.get('method', '').strip():
                L += ['', f"**Method.** {e['method'].strip()}"]
            L += ['', f"**Result.** {e['public_summary'].strip()}"]
            if e['key_numbers']:
                L += ['', '| number | meaning | source |', '|---|---|---|']
                L += [f"| {_cell(k['value'])} | {_cell(k['meaning'])} | {_src(k)} |" for k in e['key_numbers']]
            if e.get('lesson', '').strip():
                L += ['', f"**Lesson.** {e['lesson'].strip()}"]
    return '\n'.join(L)


def intro_text():
    """README intro: where the experiments ran, counts from the experiment map and BRANCH_INDEX.md."""
    em = _em()
    s = open(os.path.join(REPO, 'BRANCH_INDEX.md')).read()
    summ = s[s.index('## Summary'):].split('\n## ')[0]
    nrepo = len([r for r in summ.splitlines() if r.startswith('| ') and not r.startswith(('| repository', '| **total'))])
    return (f"In all, {em['n_experiments']} experiments ran on the {n_experiments()} experiment branches of the project's private "
            f"working repository, its research log and related repositories (among them the separate PHerc0268 repository); "
            f"every branch of the {nrepo} project repositories is indexed in [BRANCH_INDEX.md](BRANCH_INDEX.md).")


TABLES = dict(form=form_text, model_fit=model_fit, repro_note=repro_note, summary=summary_text, headline=headline_table, control=control_table, repro=repro_table, decisions=decisions_table,
              pherc0268=pherc0268_table, blind=blind_table, experiments=experiments_table, experiments_full=experiments_full,
              intro=intro_text)
for fn in ('README.md', 'docs/RESULTS.md', 'SUBMISSION.md', 'docs/EXPERIMENTS.md'):
    p = os.path.join(REPO, fn)
    if not os.path.exists(p):
        continue
    s = open(p).read()
    for name, fun in TABLES.items():
        s = re.sub(rf'(<!-- BEGIN:{name} -->\n).*?(\n<!-- END:{name} -->)', lambda m: m.group(1) + fun() + m.group(2), s, flags=re.S)
    open(p, 'w').write(s)
    print('filled', fn)
