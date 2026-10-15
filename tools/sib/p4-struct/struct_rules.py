"""P4-I (DECL-P4-8) items 3-4: gate and STRUCT-positive rules, as declared."""
import numpy as np

import struct_core as sc

GATE_FRAC = 0.30
THETA_TOL = 10.0


def nonblank(ctrl):
    """Control tiles that are not blank: M_ink >= the control median (item 3)."""
    ok = {k: v for k, v in ctrl.items() if not v['insufficient']}
    if not ok:
        return {}, None
    med = float(np.median([v['M_ink'] for v in ok.values()]))
    return {k: v for k, v in ok.items() if v['M_ink'] >= med}, med


def gate(ctrl, T):
    nb, med_mink = nonblank(ctrl)
    theta_c = sc.circ_median([v['theta_star'] for v in nb.values()])
    n_pass = sum(1 for v in nb.values()
                 if v['S_row'] > T and sc.ang_diff(v['theta_star'], theta_c) <= THETA_TOL)
    n_above_T = sum(1 for v in nb.values() if v['S_row'] > T)
    frac = n_pass / len(nb) if nb else None
    return dict(n_control=len(ctrl), n_nonblank=len(nb), control_M_ink_median=med_mink,
                theta_c_median_nonblank=theta_c, n_above_T=n_above_T, n_pass=n_pass,
                frac_pass=frac, bar=GATE_FRAC,
                **{'pass': bool(frac is not None and frac >= GATE_FRAC)})


def struct_positive(title, T, theta_c, gate_pass):
    """Item 4. A missing labelled-adjacency flag (None) never passes (fail-closed)."""
    if not gate_pass or theta_c is None:
        return []
    out = []
    for k in sorted(title):
        v = title[k]
        if v['insufficient'] or v.get('labelled_adjacent') is not False:
            continue
        if v['S_row'] > T and sc.ang_diff(v['theta_star'], theta_c) <= THETA_TOL:
            out.append(k)
    return out
