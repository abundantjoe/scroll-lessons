#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UNR-1 item 3 (stage X1, the sheet-identity field), VERSION 0, at the scan's native resolution (8.64 um per voxel,
OME level 0, as amended by DECL-UNR-1-A1) on one 16-section y-slab of xz sections (frame of DECL-UMB-2: sections are xz
planes indexed by y, layers stacked along z, nested hairpins at the x edges). Geometry only: nothing here is a claim
about ink or letters. Where the declaration is silent, the simplest honest option was taken; every choice is named here.

Per section (one float32 section resident at a time; at most 2 threads):
  stripe removal = column z-median inside the mask (st_axis.stripe_removal); 2-D structure tensor, derivative sigma 2
  vox, integration sigma 8 vox (st_axis.st_eigen): the local layering normal theta (mod pi, from the x axis towards z)
  and its coherence; the orientation dispersion 1 - |<exp(2 i theta)>| in a Gaussian neighbourhood (--disp_sigma 24 vox)
  is the smooth/buckled separator for the self-test. Once per slab a 3-D structure tensor (derivative sigma (1,2,2),
  integration (2,8,8) in (y,z,x), stride 4) gives |n_y| per (z,x) at the middle section, applied to all 16 sections.
  Rays (v0 deviation, stated): straight VERTICAL rays, one per x column every --ray_step (8) voxels, over every contiguous
  in-mask run of the column (>= 2 w_s long). A first version integrated streamlines of the normal field; in this window
  the top band holds near-vertical buckled sheets, a streamline turns horizontal there and never descends, so the rays
  were unusable. With vertical rays every width and spacing measured along z is projected on the local in-plane normal
  (x |n_z|, the cosine of the ray-normal angle; fields width, spacing) and additionally by cos(y-tilt) = sqrt(1 - n_y^2)
  (fields width_c, spacing_c); the raw along-ray values are kept (width_z, spacing_z). The declared domain is recorded
  per node as flags: dom_angle (ray-normal angle <= --ray_angle_max_deg 30), dom_coh (coherence >= --coh_min 0.5),
  dom_ny (|n_y| <= --ny_max 0.5) and their conjunction `domain`. v0 deviation, stated: out-of-domain nodes are still
  created, linked and tracked (on this window the three flags hold on 27 %, 59 % and 74 % of nodes, all three on 11 %;
  a strict filter would discard the hairpin arms and the buckled band wholesale) and every statistic is reported for
  all nodes and for in-domain nodes separately, so nothing is dropped silently and the owner can filter on the flags.
  Profile and peaks: the stripe-removed section is smoothed by a Gaussian of --prof_sigma (1 vox, the specified
  operator) across the ray and max(prof_sigma, --tang_sigma) along x (tang_sigma 0 by default; 3-4 vox is the
  declaration's along-tangent smoothing, valid inside the ray-angle domain where the tangent is within 30 deg of x; it
  is exposed because at sigma 1 the fibre and ply texture inside a 14-vox sheet is resolved and peaks are picked
  intermittently from column to column, see the self-test). Lamina peaks: scipy find_peaks with prominence >= 3 MAD
  (MAD of the ray's own profile, unbounded base: the declared criterion); the peak's half-prominence interval and
  width are then measured from a prominence whose base is searched within a window of --wlen_ws (4) x w_s around the
  peak, so that a lamina's interval is bounded by its own neighbouring gaps (with the unbounded base the brightest
  lamina of a packet takes its base at a distant seam, its half-prominence interval spans the packet and swallows
  its neighbours; the recorded prominence in MAD is the unbounded one). A peak whose half-prominence interval is nested inside a
  more prominent peak's interval (overlap > 50 % of its own width) is the same lamina seen twice through noise and is
  dropped; two intervals that merely touch are both kept (the declaration's HALF candidates). Node position z = the
  midpoint of the half-prominence interval (the re-anchoring to the ridge: a flat-topped lamina has its maximum
  sample anywhere on the plateau and its flanks are stable; the maximum-sample index is kept as s). Each node carries:
  section, ray column, x, z, s, width_z, spacing_z (mean distance along the ray to the neighbouring peaks; the ray's
  median where only one neighbour exists), prominence in MAD, theta, coherence, |n_y|, dispersion, gap flags, class.
  Width classes relative to w_s (--w_s 14 vox, the UNR-X0 native median 122 um; one w_s for the window, no per-tile
  w_s in v0), on the normal-projected width: SHEET <= 1.4 w_s with a resolved gap on both sides; PAIR 1.4-2.5 w_s;
  FUSED > 2.5 w_s; DEBRIS < 0.5 w_s and isolated; plus two v0 labels the declaration does not name, used so that no
  node is mislabelled: CONTACT (<= 1.4 w_s but no resolved gap on at least one side: a lamina touching its neighbour,
  no sheet claim) and THIN (< 0.5 w_s inside a kept ridge: a continuous narrow run such as a single ply, no sheet
  claim; the HALF class and X3's cleavage test are not implemented). A resolved gap = the half-prominence interval is
  separated from its neighbour's (or from the ray end) by >= 1 vox (the one-voxel-dip test of the X0 survey).
  Isolated = not a member of a kept in-section ridge polyline; classes are finalised after in-section linking.
In-section ridge linking: nodes on adjacent ray columns are linked when the displacement projected on the first node's
  normal is <= 0.5 x its local (normal-projected) spacing, the normal angle changes by <= 25 deg and the total distance
  is <= 3 ray steps (v0 guard); greedy one-to-one by normal distance; chains of >= --min_nodes (5) nodes are kept as
  ridge polylines; shorter chains carry no id and no sheet claim (counted as short_chains_dropped).
Across sections (gated assignment, run independently in +y and -y): every node of an identified ridge predicts its
  partner at pos + its own previous displacement (0 for the first link; a node that inherited its id along its ridge
  without a link of its own uses the mean displacement of that id's linked nodes on the ridge); candidates are nodes
  of kept ridges in the next section within --col_win (2) ray columns and within gate = 0.5 x the node's local spacing
  along its normal; greedy nearest-first one-to-one assignment PER COLUMN (the same column is preferred strictly; a
  column shift is used only when the same column offers no candidate, otherwise a smooth ridge's neighbouring columns
  compete on sub-voxel noise and the two passes disagree for no physical reason). The partner is itself a re-anchored
  ridge peak, so no further snap is applied. A chosen link is refused (the BREAK rules) when the displacement along
  the normal is > --max_disp (2) vox per section or the ridge-local median width (5 nodes) changes by > --max_dw (50 %);
  a refused partner stays free for other nodes. Ids propagate node to node and then along each next-section ridge to
  its unlinked nodes (nearest linked node along the ridge); an id keeps only its largest contiguous run on a ridge
  (pruned links are released and the nodes refilled). Events per section: SPLIT (an id continues on >= 2 ridge runs:
  the largest keeps the id, every other run gets a new id with the parent recorded; never fused), CONTACT (one ridge
  carries runs of >= 2 ids: both kept as two ids), BREAK (an id whose every assigned link was refused by the BREAK
  rules: TERMINATED), LOST / RESUME / CUT (an id with no link at all is searched for up to --max_lost (2) further
  sections from its last observed nodes with the same prediction; no node is written for the unobserved sections;
  found -> RESUME, else after >= 3 lost sections -> CUT, TERMINATED). Bridging over an unobserved gap (declaration
  rules (i)-(iv), <= 2 mm) is NOT implemented in v0. No interpolation anywhere: every node is a measured peak. Status
  per node: OBSERVED, or TERMINATED on the last observed nodes of a cut or broken id. The +y and -y passes are
  independent; a +y link agrees when the -y pass links the same two nodes (`agree_fwd`; `agree_ridge_fwd` is the
  looser same-ridge test); disagreements are flagged, never averaged. Output ids are the +y ids; the -y ids are kept
  beside them (id_bwd).
Not in v0 (deferred, named so that nothing is assumed done): rays along the local normal, anisotropic tensor, 1-D
  along-ray high-pass, m7 refinement, HALF class, in-sheet slip anchors, shear-line detector, fold-defect map and
  defect-guided prediction, hairpin trace operator (hairpin apexes are near-vertical, outside the ray-angle domain of
  vertical rays, and are TERMINATED by default), bridging, seam events, tifxyz height maps, per-tile w_s.
Self-test (--selftest): sanity checks written to summary.json['sanity'] (spacing median near 44 vox; ridges per section
  against (mask height / pitch) x (width / mean ridge length); +y/-y agreement for smooth (dispersion < 0.1) and
  buckled nodes inside the domain). --phantom replaces the slab by a code-path phantom (make_phantom: 17 horizontal
  sheets, pitch 44, thickness 14, undulation, y-drift, noise, one terminating sheet); a phantom pass is evidence about
  code paths only, never about PHerc0268.
Outputs in <out>: nodes.npz (sparse node table with ids, links, status, agreement flags), events.json (per section and
  pass: splits, contacts, breaks, cuts, lost, resumes, births, links, refusals), ids.json (per-id statistics: length in
  sections, sections observed, mean displacement, width class histogram, birth and end causes), summary.json, and
  overlay_sec<k>.png / overlay_sec<k>_crop2x.png (the middle section with the kept ridges coloured by +y id, TERMINATED
  nodes circled red; the owner's cross-section audit view).
usage: sheet_track.py <out_dir> [--npy /dev/shm/umb/L0_leftedge_y5820.npy] [--y0 5820] [--w_s 14] [--selftest] [--phantom]
"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '2'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '2'); os.environ.setdefault('MKL_NUM_THREADS', '2')
import argparse, json, sys, time, numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks, peak_prominences, peak_widths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'umb')); from st_axis import stripe_removal, st_accumulate, st_eigen

VOX = 8.64
CLASSES = ['SHEET', 'PAIR', 'FUSED', 'DEBRIS', 'CONTACT', 'THIN']; SHEET, PAIR, FUSED, DEBRIS, CONTACT, THIN = range(6)
OBSERVED, TERMINATED = 0, 1
DEFAULTS = dict(sd=2.0, si=8.0, disp_sigma=24.0, ray_step=8, w_s=14.0, min_nodes=5, max_angle_deg=25.0, col_win=2, max_disp=2.0, max_dw=0.5, max_lost=2, coh_min=0.5, ny_max=0.5, ray_angle_max_deg=30.0, prof_sigma=1.0, tang_sigma=0.0, wlen_ws=4.0)


# ----------------------------------------------------------------------------------------------------------- per section
def section_fields(sec_u8, p):
    """mask, 1-vox-smoothed stripe-removed image, normal angle theta (rad, mod pi), coherence, orientation dispersion."""
    mask = sec_u8 > 0; img = stripe_removal(sec_u8.astype(np.float32) / 255.0, mask)
    th, coh, _ = st_eigen(st_accumulate([img], p['sd']), p['si']); sm = ndi.gaussian_filter(img, (p['prof_sigma'], max(p['prof_sigma'], p['tang_sigma'])))   # (z, x): across the ray, along x (the tangent inside the declared ray-angle domain)
    m = mask.astype(np.float32); w = ndi.gaussian_filter(m, p['disp_sigma']) + 1e-6
    c = ndi.gaussian_filter(np.cos(2 * th) * m, p['disp_sigma']) / w; s = ndi.gaussian_filter(np.sin(2 * th) * m, p['disp_sigma']) / w
    return mask, sm, th, coh, np.clip(1.0 - np.hypot(c, s), 0, 1).astype(np.float32)


def slab_ytilt(stack):
    """|n_y| per (z, x) from the 3-D structure tensor of the whole slab (value at the middle section), stride 4, nearest-upsampled."""
    n, Z, X = stack.shape; v = np.empty(stack.shape, np.float32)
    for i in range(n): v[i] = stripe_removal(stack[i].astype(np.float32) / 255.0, stack[i] > 0)
    g = [ndi.gaussian_filter(v, (1, 2, 2), order=o) for o in [(1, 0, 0), (0, 1, 0), (0, 0, 1)]]; del v
    st = 4; Zs, Xs = -(-Z // st), -(-X // st); J = np.zeros((Zs, Xs, 3, 3), np.float32)
    for a in range(3):
        for b in range(a, 3): J[..., a, b] = J[..., b, a] = ndi.gaussian_filter(g[a] * g[b], (2, 8, 8))[n // 2, ::st, ::st]
    del g; w, e = np.linalg.eigh(J); ny = np.abs(e[..., 0, 2]).astype(np.float32); coh3 = ((w[..., 2] - w[..., 1]) / (w[..., 2] + 1e-12)).astype(np.float32)
    up = lambda a: np.repeat(np.repeat(a, st, 0), st, 1)[:Z, :X]
    return up(ny), up(coh3)


def cast_rays(mask, p):
    """Straight vertical rays, one per x column every ray_step voxels: list of (z0, z1, x, column index) for every contiguous
    in-mask run of the column at least 2 w_s long (the run is the ray; a column can carry several rays across a mask hole)."""
    Z, X = mask.shape; out = []
    for x in range(0, X, p['ray_step']):
        col = mask[:, x]
        if not col.any(): continue
        edges = np.diff(np.concatenate([[0], col.astype(np.int8), [0]])); starts = np.nonzero(edges == 1)[0]; stops = np.nonzero(edges == -1)[0]
        for z0, z1 in zip(starts, stops):
            if z1 - z0 >= 2 * p['w_s']: out.append((int(z0), int(z1), x, x // p['ray_step']))
    return out


def ray_nodes(ray, sm, th, coh, ny, disp, p):
    """Lamina peaks along one vertical ray: list of node tuples (z, x, s, width_z, spacing_z, prom_mad, theta, coh, ny, disp, gapL, gapR).
    width_z and spacing_z are measured along the ray (z); the caller projects them on the local normal with |n_z| = |sin theta|.
    The node position z is the midpoint of the peak's half-prominence interval (the re-anchoring to the ridge: a flat-topped lamina
    has its maximum sample anywhere on the plateau, its flanks are stable); s is the maximum-sample index. A peak whose
    half-prominence interval is nested inside a more prominent peak's interval (overlap > 50 % of its own width) is the same lamina
    seen twice through noise and is dropped; two adjacent intervals that merely touch are both kept (HALF candidates)."""
    z0, z1, x, _ = ray; prof = sm[z0:z1, x]
    mad = float(np.median(np.abs(prof - np.median(prof)))) + 1e-6; pk, pr = find_peaks(prof, prominence=3 * mad); n = len(pk)                       # detection: the declared unbounded prominence
    if n == 0: return []
    P = pr['prominences']; loc = peak_prominences(prof, pk, wlen=max(3, int(round(p['wlen_ws'] * p['w_s'])))); W, _, Lp, Rp = peak_widths(prof, pk, rel_height=0.5, prominence_data=loc)   # interval and width: local base
    keep = []
    for k in np.argsort(-P, kind='stable'):
        ov = [min(Rp[k], Rp[j]) - max(Lp[k], Lp[j]) for j in keep]
        if all(o <= 0.5 * (Rp[k] - Lp[k]) for o in ov): keep.append(int(k))
    keep = sorted(keep); pk, Lp, Rp, W, P = pk[keep], Lp[keep], Rp[keep], W[keep], P[keep]; n = len(pk); zc = z0 + 0.5 * (Lp + Rp); out = []
    med_sp = float(np.median(np.diff(zc))) if n > 1 else np.nan
    for k in range(n):
        gl = (Lp[k] >= 1.0) if k == 0 else (Lp[k] - Rp[k - 1] >= 1.0); gr = (len(prof) - 1 - Rp[k] >= 1.0) if k == n - 1 else (Lp[k + 1] - Rp[k] >= 1.0)
        ds = ([zc[k] - zc[k - 1]] if k > 0 else []) + ([zc[k + 1] - zc[k]] if k < n - 1 else []); sp = float(np.mean(ds)) if ds else med_sp; zi = min(max(int(round(zc[k])), 0), sm.shape[0] - 1)
        out.append((float(zc[k]), float(x), float(pk[k]), float(W[k]), sp, float(P[k] / mad), float(th[zi, x]), float(coh[zi, x]), float(ny[zi, x]), float(disp[zi, x]), bool(gl), bool(gr)))
    return out


def angle_diff(a, b):
    """Smallest difference between two normal angles (mod pi), in radians."""
    return np.abs(((a - b + np.pi / 2) % np.pi) - np.pi / 2)


def link_in_section(N, idx, p, poly_base):
    """Ridge polylines inside one section: greedy one-to-one links between nodes on adjacent ray columns. Writes poly and pos
    into N for chains of >= min_nodes; returns the number of polylines made and the number of chains discarded as short."""
    rays = N['ray'][idx]; groups = {r: idx[rays == r] for r in np.unique(rays)}; nxt = {}; prv = {}; amax = np.deg2rad(p['max_angle_deg']); dmax = 3.0 * p['ray_step']
    for r in sorted(groups):
        if r + 1 not in groups: continue
        A, B = groups[r], groups[r + 1]; ta = N['th'][A]; dz = N['z'][B][None, :] - N['z'][A][:, None]; dx = N['x'][B][None, :] - N['x'][A][:, None]
        along = np.abs(dz * np.sin(ta)[:, None] + dx * np.cos(ta)[:, None]); ok = (along <= 0.5 * N['spacing'][A][:, None]) & (angle_diff(ta[:, None], N['th'][B][None, :]) <= amax) & (np.hypot(dz, dx) <= dmax)
        ai, bi = np.nonzero(ok); ua = set(); ub = set()
        for q in np.argsort(along[ai, bi], kind='stable'):
            i, j = int(ai[q]), int(bi[q])
            if i in ua or j in ub: continue
            ua.add(i); ub.add(j); nxt[int(A[i])] = int(B[j]); prv[int(B[j])] = int(A[i])
    n_poly = 0; n_short = 0
    for a in idx:
        a = int(a)
        if a in prv: continue
        chain = [a]
        while chain[-1] in nxt: chain.append(nxt[chain[-1]])
        if len(chain) < p['min_nodes']: n_short += int(len(chain) > 1); continue
        N['poly'][chain] = poly_base + n_poly; N['pos'][chain] = np.arange(len(chain)); n_poly += 1
    return n_poly, n_short


def classify(N, p):
    r = N['width'] / p['w_s']; inpoly = N['poly'] >= 0; cls = np.full(len(r), SHEET, np.int8)
    cls[r > 1.4] = PAIR; cls[r > 2.5] = FUSED; narrow = r < 0.5; cls[narrow & inpoly] = THIN; cls[narrow & ~inpoly] = DEBRIS
    mid = (r >= 0.5) & (r <= 1.4); cls[mid & ~(N['gapL'] & N['gapR'])] = CONTACT; return cls


def ridge_median_width(N):
    """Per node: the median width over its ridge neighbours within +-2 positions (its own width outside a ridge)."""
    w = N['width'].copy(); inpoly = np.nonzero(N['poly'] >= 0)[0]
    for pid in np.unique(N['poly'][inpoly]):
        m = inpoly[N['poly'][inpoly] == pid]; m = m[np.argsort(N['pos'][m])]; ww = N['width'][m]
        for k in range(len(m)): w[m[k]] = np.median(ww[max(0, k - 2):k + 3])
    return w


# ------------------------------------------------------------------------------------------------- across sections
def track(N, order, p):
    """Gated assignment along the given section order (+y or -y). Returns ids, link (successor node index or -1), status,
    pdisp (per-node previous displacement (dz, dx) per section), events (list), born {id: (sec, cause, parent)}, ended {id: (sec, cause)}."""
    n = len(N['sec']); ids = np.full(n, -1, np.int32); link = np.full(n, -1, np.int32); pred = np.full(n, -1, np.int32); status = np.zeros(n, np.int8)
    pdisp = np.zeros((n, 2), np.float32); sec_nodes = {s: np.nonzero(N['sec'] == s)[0] for s in order}; cnt = [0]; events = []; born = {}; ended = {}

    def new_id(sec, cause, parent=-1): i = cnt[0]; cnt[0] += 1; born[i] = (int(sec), cause, int(parent)); return i

    def polys_of(sec):
        idx = sec_nodes[sec]; idx = idx[N['poly'][idx] >= 0]; out = {}
        for pid in np.unique(N['poly'][idx]): m = idx[N['poly'][idx] == pid]; out[int(pid)] = m[np.argsort(N['pos'][m])]
        return out

    def runs(vals):
        """contiguous runs of equal value: list of (value, start, stop)."""
        out = []; s = 0
        for k in range(1, len(vals) + 1):
            if k == len(vals) or vals[k] != vals[s]: out.append((int(vals[s]), s, k)); s = k
        return out

    def fill(m):
        """give unlinked nodes of ridge m the id of the nearest linked node along the ridge; their pdisp = that id's mean linked pdisp on m."""
        lk = np.nonzero(ids[m] >= 0)[0]
        if len(lk) == 0: return False
        un = np.nonzero(ids[m] < 0)[0]
        if len(un):
            j = np.clip(np.searchsorted(lk, un), 0, len(lk) - 1); j2 = np.clip(j - 1, 0, len(lk) - 1); near = np.where(np.abs(lk[j] - un) <= np.abs(lk[j2] - un), lk[j], lk[j2]); ids[m[un]] = ids[m[near]]
            for i in np.unique(ids[m[near]]): sel = m[lk][ids[m[lk]] == i]; mean_d = pdisp[sel].mean(0); pdisp[m[un][ids[m[near]] == i]] = mean_d
        return True

    s0 = order[0]
    for pid, m in polys_of(s0).items(): ids[m] = new_id(s0, 'first')
    ghosts = {}
    for k in range(len(order) - 1):
        y, y1 = order[k], order[k + 1]; P1 = polys_of(y1); ev = {'section': int(y1), 'splits': [], 'contacts': [], 'breaks': [], 'cuts': [], 'lost': [], 'resumes': [], 'births': 0, 'links': 0, 'refused_disp': 0, 'refused_width': 0}
        A = sec_nodes[y]; A = A[ids[A] >= 0]; mult = np.ones(len(A), np.float32)
        if ghosts:
            GA = np.concatenate([g['nodes'] for g in ghosts.values()]); GM = np.concatenate([np.full(len(g['nodes']), g['lost'] + 1, np.float32) for g in ghosts.values()]); A = np.concatenate([A, GA]); mult = np.concatenate([mult, GM])
        B = np.concatenate(list(P1.values())) if P1 else np.zeros(0, np.int64); active = set(int(i) for i in ids[A]); refused = {}
        if len(A) and len(B):
            ta = N['th'][A]; nz, nx = np.sin(ta), np.cos(ta); gate = 0.5 * N['spacing'][A]; predz = N['z'][A] + pdisp[A, 0] * mult; predx = N['x'][A] + pdisp[A, 1] * mult
            dz = N['z'][B][None, :] - predz[:, None]; dx = N['x'][B][None, :] - predx[:, None]; res = np.abs(dz * nz[:, None] + dx * nx[:, None]); dray = np.abs(N['ray'][B][None, :] - N['ray'][A][:, None])
            ai, bi = np.nonzero((res <= gate[:, None]) & (dray <= p['col_win'])); cost = res[ai, bi] + 1000.0 * dray[ai, bi]; del dz, dx, res, dray                # per column: a column shift is used only when the same column has no candidate
            ua = np.zeros(len(A), bool); ub = np.zeros(len(B), bool)
            for q in np.argsort(cost, kind='stable'):
                i, j = int(ai[q]), int(bi[q])
                if ua[i] or ub[j]: continue
                a, b = int(A[i]), int(B[j]); ddz = (N['z'][b] - N['z'][a]) / mult[i]; ddx = (N['x'][b] - N['x'][a]) / mult[i]; dn = abs(ddz * nz[i] + ddx * nx[i]); wa, wb = N['wmed'][a], N['wmed'][b]
                ua[i] = True
                if dn > p['max_disp']: refused[int(ids[a])] = refused.get(int(ids[a]), 0) + 1; ev['refused_disp'] += 1; continue
                if abs(wb - wa) / max(wa, 1e-6) > p['max_dw']: refused[int(ids[a])] = refused.get(int(ids[a]), 0) + 1; ev['refused_width'] += 1; continue
                ub[j] = True; ids[b] = ids[a]; link[a] = b; pred[b] = a; pdisp[b] = (ddz, ddx); ev['links'] += 1
        # ridge propagation, one run per id per ridge, births
        for pid, m in P1.items():
            if not fill(m): ids[m] = new_id(y1, 'birth'); ev['births'] += 1; continue
            rr = runs(ids[m]); seen = {}
            for v, s, e in rr: seen.setdefault(v, []).append((e - s, s, e))
            changed = False
            for v, lst in seen.items():
                if len(lst) < 2: continue
                lst.sort(reverse=True)
                for _, s, e in lst[1:]:
                    for b in m[s:e]:
                        if pred[b] >= 0: link[pred[b]] = -1; pred[b] = -1
                    ids[m[s:e]] = -1; pdisp[m[s:e]] = 0; changed = True
            if changed: fill(m)
        # events per id that was active in y (or a ghost)
        runs_by_id = {}
        for pid, m in P1.items():
            for v, s, e in runs(ids[m]): runs_by_id.setdefault(v, []).append((pid, s, e, m[s:e]))
        for A_id in sorted(active):
            rs = runs_by_id.get(A_id, [])
            if not rs:
                last_nodes = ghosts[A_id]['nodes'] if A_id in ghosts else sec_nodes[y][ids[sec_nodes[y]] == A_id]
                if refused.get(A_id, 0) > 0:
                    ev['breaks'].append({'id': A_id, 'refused': refused[A_id]}); ended[A_id] = (int(y), 'BREAK'); status[last_nodes] = TERMINATED; ghosts.pop(A_id, None); continue
                g = ghosts.setdefault(A_id, {'nodes': last_nodes, 'lost': 0}); g['lost'] += 1
                if g['lost'] > p['max_lost']: ev['cuts'].append({'id': A_id, 'lost': g['lost']}); ended[A_id] = (int(y), 'CUT'); status[last_nodes] = TERMINATED; del ghosts[A_id]
                else: ev['lost'].append({'id': A_id, 'lost': g['lost']})
                continue
            if A_id in ghosts: ev['resumes'].append({'id': A_id, 'lost': ghosts[A_id]['lost']}); del ghosts[A_id]
            if len(rs) > 1:
                rs.sort(key=lambda t: -(t[2] - t[1]))
                for pid, s, e, nodes in rs[1:]: c = new_id(y1, 'split', A_id); ids[nodes] = c; ev['splits'].append({'parent': A_id, 'child': c, 'nodes': int(len(nodes))})
        for pid, m in P1.items():
            u = [v for v, s, e in runs(ids[m])]
            if len(u) > 1: ev['contacts'].append({'ids': u, 'ridge': int(pid)})
        events.append(ev)
    for i in range(cnt[0]):
        if i not in ended: ended[i] = (int(order[-1]), 'OPEN' if i not in ghosts else 'LOST_AT_END')
    return ids, link, status, pdisp, events, born, ended


def id_stats(N, ids, pdisp, link, born, ended):
    out = {}; sec = N['sec']
    for i in range(len(born)):
        m = np.nonzero(ids == i)[0]
        if len(m) == 0: continue
        ss = np.unique(sec[m]); lk = m[link[m] >= 0] if len(m) else m; disp = np.hypot(pdisp[m, 0], pdisp[m, 1]); linked = m[np.isin(m, np.nonzero(link >= 0)[0]) | (sec[m] != ss.min())]
        hist = {CLASSES[c]: int((N['cls'][m] == c).sum()) for c in range(len(CLASSES))}
        out[i] = {'first_section': int(ss.min()), 'last_section': int(ss.max()), 'length_sections': int(ss.max() - ss.min() + 1), 'sections_observed': int(len(ss)), 'n_nodes': int(len(m)),
                  'mean_disp_vox_per_section': round(float(disp[sec[m] != ss.min()].mean()), 3) if (sec[m] != ss.min()).any() else None, 'mean_width_vox': round(float(N['width'][m].mean()), 2),
                  'class_hist': hist, 'modal_class': CLASSES[int(np.argmax([hist[c] for c in CLASSES]))], 'born': {'section': born[i][0], 'cause': born[i][1], 'parent': born[i][2]}, 'end': {'section': ended[i][0], 'cause': ended[i][1]},
                  'domain_frac': round(float(N['domain'][m].mean()), 3)}
    return out


# ------------------------------------------------------------------------------------------------------------ outputs
def overlay(N, ids, status, sec_k, sm, out_png, scale=1, crop=None):
    from PIL import Image, ImageDraw
    lo, hi = np.percentile(sm, [1, 99]); g = np.clip((sm - lo) / (hi - lo + 1e-6) * 255, 0, 255).astype(np.uint8)
    if crop is not None: z0, z1, x0, x1 = crop; g = g[z0:z1, x0:x1]
    else: z0, x0 = 0, 0
    im = Image.fromarray(g).convert('RGB')
    if scale != 1: im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    dr = ImageDraw.Draw(im); idx = np.nonzero((N['sec'] == sec_k) & (N['poly'] >= 0))[0]
    def colour(i):
        h = (i * 0.618033988749895) % 1.0; r, gg, b = [int(255 * v) for v in __import__('colorsys').hsv_to_rgb(h, 0.9, 1.0)]; return (r, gg, b)
    for pid in np.unique(N['poly'][idx]):
        m = idx[N['poly'][idx] == pid]; m = m[np.argsort(N['pos'][m])]
        for a, b in zip(m[:-1], m[1:]):
            pa = ((N['x'][a] - x0) * scale, (N['z'][a] - z0) * scale); pb = ((N['x'][b] - x0) * scale, (N['z'][b] - z0) * scale)
            dr.line([pa, pb], fill=colour(int(ids[a])) if ids[a] >= 0 else (128, 128, 128), width=max(1, scale))
        for a in m:
            if status[a] == TERMINATED: q = ((N['x'][a] - x0) * scale, (N['z'][a] - z0) * scale); dr.ellipse([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2], outline=(255, 0, 0))
    im.save(out_png)


def run(stack, p, out, y0=0, selftest=False):
    t0 = time.time(); n, Z, X = stack.shape; os.makedirs(out, exist_ok=True); ny_f, coh3 = slab_ytilt(stack); t_tilt = time.time() - t0
    cols = ['z', 'x', 's', 'width_z', 'spacing_z', 'prom', 'th', 'coh', 'ny', 'disp']; rows = {c: [] for c in cols + ['gapL', 'gapR', 'sec', 'ray']}; per_sec = []; sm_keep = {}
    for i in range(n):
        mask, sm, th, coh, disp = section_fields(stack[i], p); rays = cast_rays(mask, p); nn = 0
        for ray in rays:
            for nd in ray_nodes(ray, sm, th, coh, ny_f, disp, p):
                for c, v in zip(cols, nd[:10]): rows[c].append(v)
                rows['gapL'].append(nd[10]); rows['gapR'].append(nd[11]); rows['sec'].append(i); rows['ray'].append(ray[3]); nn += 1
        per_sec.append({'section': i, 'y': y0 + i, 'rays': len(rays), 'nodes': nn, 'mask_frac': round(float(mask.mean()), 4), 'coh_median': round(float(np.median(coh[mask])), 3), 'mean_ray_len': round(float(np.mean([q[1] - q[0] for q in rays])), 1) if rays else 0})
        if i == n // 2: sm_keep = {'sm': sm}
        del mask, sm, th, coh, disp
    N = {c: np.array(rows[c], np.float32) for c in cols}; N['gapL'] = np.array(rows['gapL'], bool); N['gapR'] = np.array(rows['gapR'], bool); N['sec'] = np.array(rows['sec'], np.int16); N['ray'] = np.array(rows['ray'], np.int16)
    nn = len(N['sec']); N['poly'] = np.full(nn, -1, np.int32); N['pos'] = np.full(nn, -1, np.int32)
    med_sp = float(np.nanmedian(N['spacing_z'])) if np.isfinite(N['spacing_z']).any() else 3 * p['w_s']; N['spacing_z'] = np.where(np.isfinite(N['spacing_z']), N['spacing_z'], med_sp).astype(np.float32)
    N['nz'] = np.abs(np.sin(N['th'])).astype(np.float32); N['width'] = N['width_z'] * N['nz']; N['spacing'] = N['spacing_z'] * N['nz']                       # along the in-plane normal: x cos(ray-normal angle)
    ctilt = np.sqrt(np.clip(1 - N['ny'] ** 2, 0, 1)); N['width_c'] = N['width'] * ctilt; N['spacing_c'] = N['spacing'] * ctilt                                      # x cos(y-tilt)
    N['dom_angle'] = N['nz'] >= np.cos(np.deg2rad(p['ray_angle_max_deg'])); N['dom_coh'] = N['coh'] >= p['coh_min']; N['dom_ny'] = N['ny'] <= p['ny_max']; N['domain'] = N['dom_angle'] & N['dom_coh'] & N['dom_ny']
    t_nodes = time.time() - t0; base = 0
    for i in range(n):
        idx = np.nonzero(N['sec'] == i)[0]; npoly, nshort = link_in_section(N, idx, p, base); base += npoly; per_sec[i].update({'polylines': npoly, 'short_chains_dropped': nshort, 'nodes_in_polylines': int((N['poly'][idx] >= 0).sum())})
    N['cls'] = classify(N, p); N['wmed'] = ridge_median_width(N); t_link = time.time() - t0
    fwd = track(N, list(range(n)), p); bwd = track(N, list(range(n - 1, -1, -1)), p); t_track = time.time() - t0
    ids_f, link_f, status_f, pdisp_f, ev_f, born_f, ended_f = fwd; ids_b, link_b, status_b, pdisp_b, ev_b, born_b, ended_b = bwd
    agree = np.full(nn, -1, np.int8); has = link_f >= 0; agree[has] = (link_b[link_f[has]] == np.nonzero(has)[0]).astype(np.int8)
    agree_b = np.full(nn, -1, np.int8); hb = link_b >= 0; agree_b[hb] = (link_f[link_b[hb]] == np.nonzero(hb)[0]).astype(np.int8)
    agree_ridge = np.full(nn, -1, np.int8); back = np.where(has, link_b[np.where(has, link_f, 0)], -1); hr = has & (back >= 0)                       # looser: the -y pass returns to the same ridge polyline
    agree_ridge[has] = 0; agree_ridge[hr] = ((N['poly'][back[hr]] == N['poly'][hr]) & (N['sec'][back[hr]] == N['sec'][hr])).astype(np.int8)
    stats = id_stats(N, ids_f, pdisp_f, link_f, born_f, ended_f); stats_b = id_stats(N, ids_b, pdisp_b, link_b, born_b, ended_b)
    # ---- summary
    inpoly = N['poly'] >= 0; hasid = ids_f >= 0; dom = N['domain']
    def frac(m, w=None): return round(float(m[w].mean()), 4) if (w is None or w.any()) and len(m) else None
    def agree_frac(sel): s = has & sel; return {'n_links': int(s.sum()), 'agree': frac(agree == 1, s), 'agree_same_ridge': frac(agree_ridge == 1, s)} if s.any() else {'n_links': 0, 'agree': None, 'agree_same_ridge': None}
    bins = [(0, 0.05), (0.05, 0.1), (0.1, 0.2), (0.2, 1.01)]
    lengths = [v['length_sections'] for v in stats.values()]; multi = [L for L in lengths if L >= 2]
    sp_hist, sp_edges = np.histogram(N['spacing'], bins=np.arange(0, 124, 4)); spc_hist, _ = np.histogram(N['spacing_c'], bins=np.arange(0, 124, 4))
    mean_len_vox = float(np.mean([(N['poly'] == q).sum() for q in np.unique(N['poly'][inpoly])])) * p['ray_step'] if inpoly.any() else float('nan')
    mask_h = float(np.mean([s['mask_frac'] for s in per_sec])) * Z; expected_poly = (mask_h / float(np.median(N['spacing']))) * (X / mean_len_vox) if mean_len_vox > 0 else None
    summary = {'vox_um': VOX, 'y0': y0, 'n_sections': n, 'shape_zx': [Z, X], 'params': p, 'seconds': {'ytilt': round(t_tilt, 1), 'nodes': round(t_nodes, 1), 'in_section_linking': round(t_link - t_nodes, 1), 'tracking_both_passes': round(t_track - t_link, 1)},
               'nodes_total': int(nn), 'nodes_in_polylines': int(inpoly.sum()), 'nodes_with_id': int(hasid.sum()), 'nodes_in_domain_frac': frac(dom), 'nodes_coh_ge_min_frac': frac(N['dom_coh']), 'nodes_ny_le_max_frac': frac(N['dom_ny']), 'nodes_ray_angle_le_max_frac': frac(N['dom_angle']), 'nodes_in_polylines_in_domain_frac': frac(dom, inpoly),
               'n_sheet_ids_fwd': len(stats), 'n_ids_bwd': len(stats_b), 'n_ids_fwd_ge2_sections': int(sum(1 for L in lengths if L >= 2)), 'n_ids_fwd_spanning_slab': int(sum(1 for L in lengths if L == n)),
               'ids_fwd_by_modal_class': {c: int(sum(1 for v in stats.values() if v['modal_class'] == c)) for c in CLASSES}, 'ids_fwd_by_end_cause': {c: int(sum(1 for v in stats.values() if v['end']['cause'] == c)) for c in ['OPEN', 'CUT', 'BREAK', 'LOST_AT_END']},
               'ids_fwd_by_birth_cause': {c: int(sum(1 for v in stats.values() if v['born']['cause'] == c)) for c in ['first', 'birth', 'split']},
               'frac_nodes_observed_of_id_nodes': frac(status_f == OBSERVED, hasid), 'frac_nodes_terminated_of_id_nodes': frac(status_f == TERMINATED, hasid),
               'mean_segment_length_sections_fwd': round(float(np.mean(lengths)), 2) if lengths else None, 'median_segment_length_sections_fwd': float(np.median(lengths)) if lengths else None, 'mean_segment_length_sections_fwd_ge2': round(float(np.mean(multi)), 2) if multi else None,
               'mean_segment_length_sections_bwd': round(float(np.mean([v['length_sections'] for v in stats_b.values()])), 2) if stats_b else None,
               'agreement': {'fwd_links': agree_frac(np.ones(nn, bool)), 'fwd_links_in_domain': agree_frac(dom), 'fwd_links_out_of_domain': agree_frac(~dom), 'bwd_links': {'n_links': int(hb.sum()), 'agree': frac(agree_b == 1, hb)},
                             'by_dispersion_bin': {f'{a}-{b if b <= 1 else 1}': agree_frac((N['disp'] >= a) & (N['disp'] < b)) for a, b in bins}, 'smooth_disp_lt_0.1': agree_frac(N['disp'] < 0.1), 'buckled_disp_ge_0.1': agree_frac(N['disp'] >= 0.1),
                             'smooth_disp_lt_0.1_in_domain': agree_frac((N['disp'] < 0.1) & dom), 'buckled_disp_ge_0.1_in_domain': agree_frac((N['disp'] >= 0.1) & dom), 'dispersion_pcts_10_50_90': np.percentile(N['disp'], [10, 50, 90]).round(3).tolist()},
               'class_frac_all_nodes': {c: frac(N['cls'] == i) for i, c in enumerate(CLASSES)}, 'class_frac_id_nodes': {c: frac(N['cls'] == i, hasid) for i, c in enumerate(CLASSES)}, 'class_frac_in_domain_nodes': {c: frac(N['cls'] == i, dom) for i, c in enumerate(CLASSES)},
               'spacing_vox': {'median': round(float(np.median(N['spacing'])), 1), 'p10_p90': np.percentile(N['spacing'], [10, 90]).round(1).tolist(), 'median_in_domain': round(float(np.median(N['spacing'][dom])), 1) if dom.any() else None, 'median_tilt_corrected': round(float(np.median(N['spacing_c'])), 1), 'hist_bin4': sp_hist.tolist(), 'hist_bin4_tilt_corrected': spc_hist.tolist(), 'hist_edges': sp_edges.tolist()},
               'width_vox': {'median': round(float(np.median(N['width'])), 1), 'p10_p90': np.percentile(N['width'], [10, 90]).round(1).tolist(), 'median_tilt_corrected': round(float(np.median(N['width_c'])), 1), 'median_sheet_class': round(float(np.median(N['width'][N['cls'] == SHEET])), 1) if (N['cls'] == SHEET).any() else None},
               'ny_abs_pcts_10_50_90': np.percentile(N['ny'], [10, 50, 90]).round(3).tolist(), 'coh_pcts_10_50_90': np.percentile(N['coh'], [10, 50, 90]).round(3).tolist(),
               'polylines': {'per_section_mean': round(float(np.mean([s['polylines'] for s in per_sec])), 1), 'mean_length_nodes': round(mean_len_vox / p['ray_step'], 1), 'mean_length_vox': round(mean_len_vox, 1), 'expected_per_section_order': round(expected_poly, 1) if expected_poly else None, 'short_chains_dropped_per_section': round(float(np.mean([s['short_chains_dropped'] for s in per_sec])), 1)},
               'events_fwd_totals': {k: int(sum(len(e[k]) if isinstance(e[k], list) else e[k] for e in ev_f)) for k in ['splits', 'contacts', 'breaks', 'cuts', 'lost', 'resumes', 'births', 'links', 'refused_disp', 'refused_width']},
               'events_bwd_totals': {k: int(sum(len(e[k]) if isinstance(e[k], list) else e[k] for e in ev_b)) for k in ['splits', 'contacts', 'breaks', 'cuts', 'lost', 'resumes', 'births', 'links', 'refused_disp', 'refused_width']}, 'per_section': per_sec}
    if selftest:
        ag = summary['agreement']; sm_ag, bk_ag = ag['smooth_disp_lt_0.1_in_domain']['agree'], ag['buckled_disp_ge_0.1_in_domain']['agree']
        summary['sanity'] = {'spacing_median_near_44': {'median': summary['spacing_vox']['median'], 'pass_within_10': bool(abs(summary['spacing_vox']['median'] - 44) <= 10)},
                             'polylines_per_section_vs_expected': {'observed': summary['polylines']['per_section_mean'], 'expected_order': summary['polylines']['expected_per_section_order'], 'ratio': round(summary['polylines']['per_section_mean'] / expected_poly, 2) if expected_poly else None},
                             'agreement_smooth_gt_0.9_in_domain': {'smooth': sm_ag, 'buckled': bk_ag, 'pass': bool(sm_ag is not None and sm_ag > 0.9), 'buckled_lower': bool(sm_ag is not None and bk_ag is not None and bk_ag < sm_ag)},
                             'agreement_all_links': ag['fwd_links']['agree']}
    np.savez_compressed(os.path.join(out, 'nodes.npz'), **{k: N[k] for k in N}, id_fwd=ids_f, id_bwd=ids_b, link_fwd=link_f, link_bwd=link_b, status_fwd=status_f, status_bwd=status_b, agree_fwd=agree, agree_bwd=agree_b, agree_ridge_fwd=agree_ridge, pdisp_fwd=pdisp_f, pdisp_bwd=pdisp_b, classes=np.array(CLASSES), y0=y0)
    json.dump({'fwd': ev_f, 'bwd': ev_b}, open(os.path.join(out, 'events.json'), 'w'), indent=1); json.dump({'fwd': stats, 'bwd': stats_b}, open(os.path.join(out, 'ids.json'), 'w'), indent=1)
    json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
    k = n // 2; overlay(N, ids_f, status_f, k, sm_keep['sm'], os.path.join(out, f'overlay_sec{k}.png')); overlay(N, ids_f, status_f, k, sm_keep['sm'], os.path.join(out, f'overlay_sec{k}_crop2x.png'), scale=2, crop=(Z // 4, 3 * Z // 4, 0, X // 2))
    return summary


def make_phantom(n=16, Z=768, X=1024, pitch=44.0, thick=14.0, seed=0):
    """Code-path phantom (evidence about code paths only, never about 0268): horizontal sheets of the given pitch and thickness,
    undulating in x (amplitude 6 vox, period 400) and drifting 0.3 vox per section along y, intensity 160 on sheets / 60 in gaps,
    Gaussian noise sigma 15, a 40-vox out-of-mask strip at the left; one sheet terminates at x = 600 in every section (a ridge end)."""
    rng = np.random.default_rng(seed); z = np.arange(Z)[:, None].astype(np.float32); x = np.arange(X)[None, :].astype(np.float32); out = np.zeros((n, Z, X), np.uint8)
    for i in range(n):
        off = 6 * np.sin(2 * np.pi * x / 400) + 0.3 * i + 20; phase = (z - off) % pitch; img = np.where(phase < thick, 160.0, 60.0)
        k_end = int(((Z - 20) // pitch) // 2); band = ((z - off) // pitch == k_end) & (x > 600); img = np.where(band, 60.0, img)
        img = np.clip(img + rng.normal(0, 15, img.shape), 1, 255); img[:, :40] = 0; out[i] = img.astype(np.uint8)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--npy', default='/dev/shm/umb/L0_leftedge_y5820.npy'); ap.add_argument('--y0', type=int, default=5820); ap.add_argument('--selftest', action='store_true'); ap.add_argument('--phantom', action='store_true')
    for k, v in DEFAULTS.items(): ap.add_argument('--' + k, type=type(v), default=v)
    a = ap.parse_args(); p = {k: getattr(a, k) for k in DEFAULTS}
    if a.phantom: stack = make_phantom(); a.y0 = 0
    else: stack = np.asarray(np.load(a.npy, mmap_mode='r'))
    s = run(stack, p, a.out, a.y0, a.selftest); keys = ['nodes_total', 'nodes_with_id', 'nodes_in_domain_frac', 'n_sheet_ids_fwd', 'frac_nodes_observed_of_id_nodes', 'mean_segment_length_sections_fwd', 'agreement', 'class_frac_id_nodes', 'spacing_vox', 'polylines', 'events_fwd_totals', 'sanity', 'seconds']
    print(json.dumps({k: s[k] for k in keys if k in s}, default=str))


if __name__ == '__main__': main()
