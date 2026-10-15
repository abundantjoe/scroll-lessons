"""Release figures (needs matplotlib). Every figure is built from committed result files, or from the control-strip work
dir of a run (scripts/control_strips/run.sh) for the ink-map panel. Confidentiality: no PHerc0268 imagery anywhere;
PHerc0268 enters only as aggregate numbers. Ink is shown on a FIXED absolute scale (p 0.40 -> 0.70).

  python make_figures.py [--bi BI_ROOT_OF_A_CONTROL_RUN] [--which 1,2,3,4,5]
"""
import argparse
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from stripqc import patchgrid, score  # noqa: E402

FIG, RES = os.path.join(REPO, 'figures'), os.path.join(REPO, 'results')
UM = 8.64           # um per render pixel (1 px = 1 voxel along the surface at tifxyz scale 0.05)
ORANGE = np.array([1.0, 0.45, 0.0])
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'savefig.dpi': 200})


def overlay(ct, p, valid):
    """Grey CT (stretched 1-99.5 % over valid px, dimmed to 70 %) with ink painted orange, alpha = clip((p-0.40)/0.30)."""
    g = np.zeros(ct.shape, np.float32)
    if valid.any():
        lo, hi = np.percentile(ct[valid], [1, 99.5])
        g = np.clip((ct - lo) / max(hi - lo, 1e-6), 0, 1) * 0.7
    al = np.clip((p - 0.40) / 0.30, 0, 1)[..., None]
    rgb = g[..., None] * (1 - al) + ORANGE * al
    rgb[~valid] = 0
    return rgb


def scalebar(ax, x0, y0, mm=5, label=True):
    L = mm * 1000 / UM
    ax.add_patch(Rectangle((x0, y0), L, 12, color='white'))
    if label:
        ax.text(x0 + L / 2, y0 - 8, f'{mm} mm', color='white', ha='center', va='bottom', fontsize=8)


def fig1():
    """Mechanism: villa patch grid on a 260 px strip with blank margins; predicted blank share vs observed band profile."""
    ne = json.load(open(os.path.join(RES, 'margin_artifact', 'natural_experiment_PHerc0268.json')))
    prof = np.array([np.nan if v is None else v for v in ne['row_profile_mean_alpha']['260']['mean_alpha_by_row']], float)
    H = 260
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.0), gridspec_kw=dict(width_ratios=[1, 1.15]))
    ax = axs[0]
    ax.add_patch(Rectangle((0, 0), 1, 30, color='0.15'))
    ax.add_patch(Rectangle((0, 30), 1, 200, color='0.75'))
    ax.add_patch(Rectangle((0, 230), 1, 30, color='0.15'))
    ax.text(0.5, 15, 'blank margin (all-zero CT)', ha='center', va='center', color='white', fontsize=8)
    ax.text(0.5, 245, 'blank margin', ha='center', va='center', color='white', fontsize=8)
    ax.text(0.5, 130, 'valid render rows\n(papyrus CT)', ha='center', va='center', fontsize=8)
    cols = ['tab:red', 'tab:blue', 'tab:red', 'tab:red']
    for i, p in enumerate(patchgrid.positions(H)):
        x = 1.08 + 0.13 * i
        ax.add_patch(Rectangle((x, p), 0.08, 128, fill=False, lw=1.6, ec=cols[i]))
        ax.text(x + 0.04, p + 64, f'patch\n{p}-{p + 127}', ha='center', va='center', fontsize=6.5, rotation=90)
    ax.set_xlim(0, 1.65)
    ax.set_ylim(H, 0)
    ax.set_xticks([])
    ax.set_ylabel('render row (px)')
    ax.set_title('a  villa flat inference on a 13-node-row strip (260 px)', loc='left', fontsize=9)
    ax.text(0.0, 272, 'red: patch contains blank rows, so per-patch robust normalisation (no mask)\n'
            'and InstanceNorm see shifted statistics; blue: blank-free patch', fontsize=7, va='top')
    ax = axs[1]
    v = np.ones(H, bool)
    v[:30] = False
    v[230:] = False
    share = patchgrid.blank_share(v)
    ax.plot(np.arange(H), share, color='tab:red', lw=1.6, label='predicted: Hann-weighted share of\nblank-containing patches')
    ax.set_xlabel('render row (px)')
    ax.set_ylabel('predicted share', color='tab:red')
    ax.set_ylim(0, 1.05)
    ax2 = ax.twinx()
    ax2.plot(np.arange(H), prof, color='k', lw=1.2, label=f"observed: mean ink proxy, PHerc0268 strips (n = {ne['row_profile_mean_alpha']['260']['n_strips']})")
    ax2.set_ylabel('mean ink proxy (aggregate)')
    ax2.spines['right'].set_visible(True)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=6.5, loc='upper center', bbox_to_anchor=(0.5, -0.2), frameon=False, ncol=1)
    ax.set_title('b  bands sit where edge patches dominate', loc='left', fontsize=9)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.3)
    fig.savefig(os.path.join(FIG, 'fig1_mechanism.png'))
    plt.close(fig)


def fig2():
    ne = json.load(open(os.path.join(RES, 'margin_artifact', 'natural_experiment_PHerc0268.json')))
    fig, axs = plt.subplots(1, 2, figsize=(7, 3.2), sharey=True)
    for ax, H in zip(axs, ('260', '400')):
        d = ne['by_render_height'][H]
        pairs = np.array(d['per_strip_pairs_anonymised'])
        for a, b in pairs:
            ax.plot([0, 1], [a, b], color='0.6', lw=0.8)
        ax.scatter(np.zeros(len(pairs)), pairs[:, 0], s=12, color='tab:red', zorder=3)
        ax.scatter(np.ones(len(pairs)), pairs[:, 1], s=12, color='tab:blue', zorder=3)
        ax.plot([0, 1], [d['mean_alpha_30row_margin'], d['mean_alpha_10row_margin']], color='k', lw=2.2)
        ax.set_xticks([0, 1], ['30 blank rows\nabove', '10 blank rows\nabove'])
        ax.set_xlim(-0.4, 1.4)
        ax.set_title(f"{H} px strips: {d['strips_where_30_gt_10']}/{d['n_strips_with_both_classes']} higher with 30", fontsize=9)
    axs[0].set_ylabel('mean ink proxy, render rows 50-90\n(same rows, same strip)')
    fig.suptitle('Natural experiment inside PHerc0268 strips (aggregate numbers only)', fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, 'fig2_natural_experiment.png'))
    plt.close(fig)


def fig3(bi, rows=(55, 68)):
    """Positive control, before/after fill: REF | 13-row strip | 13-row strip with margin fill | displaced negative control."""
    t0, t1 = rows
    ref = score.load_arm(os.path.join(bi, 'ctrlS_REF_r40-110'), 1)
    import tifffile
    panels = [('full context (reference)', 'ctrlS_REF_r40-110'), ('13-row strip, blank margins (as mass runs)', f'ctrlS_Z13_r{t0}-{t1}'),
              ('13-row strip, margin reflect-filled (partial fix)', f'ctrlS_F13_r{t0}-{t1}'), ('same strip moved 8 vox outward (negative control, no fill)', f'ctrlS_D8_r{t0}-{t1}')]
    y0, y1 = 20 * (t0 - 2), 20 * (t1 + 2)
    fig, axs = plt.subplots(len(panels), 1, figsize=(10, 6.4))
    for ax, (title, name) in zip(axs, panels):
        w = os.path.join(bi, name)
        arm = score.load_arm(w, 1)
        ct = tifffile.imread(os.path.join(w, 'ctlayers_31-35.tif')).astype(np.float32).mean(0)
        H, W = ref['E'].shape
        canvas_p = np.zeros((y1 - y0, W), np.float32)
        canvas_c = np.zeros((y1 - y0, W), np.float32)
        canvas_v = np.zeros((y1 - y0, W), bool)
        for i in range(y1 - y0):
            ai = y0 + i - arm['r0']
            if 0 <= ai < arm['E'].shape[0]:
                j0 = arm['c0'] - ref['c0']
                canvas_p[i, j0:j0 + arm['E'].shape[1]] = arm['E'][ai]
                canvas_c[i, j0:j0 + arm['E'].shape[1]] = ct[ai]
                canvas_v[i, j0:j0 + arm['E'].shape[1]] = arm['valid'][ai]
        ax.imshow(overlay(canvas_c, canvas_p, canvas_v), interpolation='nearest')
        ax.axhline(20 * t0 - y0, color='w', lw=0.6, ls=':')
        ax.axhline(20 * t1 - y0, color='w', lw=0.6, ls=':')
        ax.set_title(title, loc='left', fontsize=8.5)
        ax.set_xticks([])
        ax.set_yticks([])
        scalebar(ax, 40, y1 - y0 - 30)
    fig.text(0.5, 0.005, f'PHerc0343 (Erwin Nieuwlaar\'s public First Letters segment), node rows {t0}-{t1} (dotted lines = scored rows); '
             'ink = 3-model ensemble, orange alpha = (p - 0.40)/0.30, fixed scale; 5 mm bar', ha='center', fontsize=7)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(os.path.join(FIG, 'fig3_control_before_after_fill.png'))
    plt.close(fig)


def fig4():
    r = json.load(open(os.path.join(RES, 'control_strips_rerun', 'results.json')))
    A = r['arms']
    order = [('Z13', '13-row strip\n(blank margins)'), ('P13', '13-row +2 real\npadding rows'), ('F13', '13-row, margin\nfill (exploratory)'),
             ('Z20', '20-row strip\n(blank margins)'), ('D8', '13-row moved\n8 vox (negative)'), ('FD8', 'moved 8 vox +\nfill (exploratory)')]
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    labels = []
    for i, (k, lab) in enumerate(order):
        m = A.get(k)
        if not m:
            labels.append(lab)
            continue
        lo, hi = m['recall_ci95']
        ax.errorbar(i, m['recall'], yerr=[[m['recall'] - lo], [hi - m['recall']]], fmt='o', color='k', capsize=4)
        if m.get('recall_matched_rate') is not None:
            ax.plot(i + 0.15, m['recall_matched_rate'], 'o', mfc='none', color='tab:orange')
        labels.append(f"{lab}\n{m['recall']:.3f} [{lo:.3f}, {hi:.3f}]")
    ax.axhline(0.5, color='tab:red', ls='--', lw=1)
    ax.text(len(order) - 0.55, 0.51, 'pre-registered bar 0.5', color='tab:red', fontsize=7, ha='right', va='bottom')
    ax.set_xticks(range(len(order)), labels, fontsize=7)
    ax.set_ylim(-0.02, 1.0)
    ax.set_ylabel('recall of full-context strong ink\nin letter boxes (p > 0.55)')
    ax.set_title('Positive control (PHerc0343, 13 letters): recall by strip geometry, 95 % letter-bootstrap CI\n'
                 'filled = fixed threshold (pre-registered); hollow orange = matched-rate threshold (exploratory)', fontsize=8.5, loc='left')
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, 'fig4_recall_by_strip_geometry.png'))
    plt.close(fig)


def fig5():
    from stripqc.blindread import roc_points
    d = json.load(open(os.path.join(RES, 'blind_read', 'read2_calibrated_controls.json')))
    fig, ax = plt.subplots(figsize=(4.2, 4))
    for rows, summ, c in zip(d['per_image'], d['readers'], ['tab:blue', 'tab:green', 'tab:purple']):
        pos = np.array([x['confidence'] for x in rows if x['cls'].startswith('pos')])
        neg = np.array([x['confidence'] for x in rows if x['cls'] == 'neg_displaced'])
        pts = np.array(roc_points(pos, neg))
        ax.plot(pts[:, 0], pts[:, 1], color=c, label=f"reader {summ['reader']}: AUC {summ['auc_all_pos_vs_neg']:.3f}")
    cb = json.load(open(os.path.join(RES, 'blind_read', 'colour_baseline.json')))
    cls = {x['image']: x['cls'] for x in d['per_image'][0]}
    cpos = np.array([v for k, v in cb['strong_fraction_by_image'].items() if cls[k].startswith('pos')])
    cneg = np.array([v for k, v in cb['strong_fraction_by_image'].items() if cls[k] == 'neg_displaced'])
    cp = np.array(roc_points(cpos, cneg))
    ax.plot(cp[:, 0], cp[:, 1], color='k', ls='--', lw=1.2,
            label=f"colour only (strong-pixel fraction): AUC {cb['colour_auc_all_pos_vs_neg']:.3f}")
    ax.plot([0, 1], [0, 1], color='0.7', ls=':')
    ax.set_xlabel('false-positive rate (hidden negatives)')
    ax.set_ylabel('true-positive rate (hidden positives)')
    ax.set_title('Blind read #2: 8 hidden positives,\n5 hidden negatives (same format)', fontsize=8.5, loc='left')
    ax.legend(fontsize=7, frameon=False, loc='lower right')
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, 'fig5_blindread_roc.png'))
    plt.close(fig)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--bi')
    ap.add_argument('--which', default='1,2,3,4,5')
    a = ap.parse_args()
    os.makedirs(FIG, exist_ok=True)
    w = set(a.which.split(','))
    if '1' in w: fig1()
    if '2' in w: fig2()
    if '3' in w and a.bi: fig3(a.bi)
    if '4' in w and os.path.exists(os.path.join(RES, 'control_strips_rerun', 'results.json')): fig4()
    if '5' in w: fig5()
    print('figures:', sorted(os.listdir(FIG)))
