"""Unit tests on synthetic sheets (no CT data). Run: python3 test_surfdist.py"""
import json, sys, time
import numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from surfdist import Surface, closest_point_dist

R = []


def check(name, got, want, tol=1e-6):
    ok = bool(np.all(np.abs(np.asarray(got) - np.asarray(want)) <= tol))
    R.append({'test': name, 'got': np.round(np.asarray(got, float), 6).tolist(),
              'want': np.round(np.asarray(want, float), 6).tolist(), 'pass': ok})
    print(('PASS' if ok else 'FAIL'), name, got, want)


def plane(n=40, step=20.0, z0=1000.0, off=500.0):
    j, i = np.meshgrid(np.arange(n), np.arange(n))
    return np.stack([off + j * step, off + i * step, np.full(i.shape, z0)], -1).astype(np.float32)


def main():
    t0 = time.time()
    # 1 triangle primitive, all regions
    a, b, c = np.array([[0, 0, 0.]]), np.array([[10, 0, 0.]]), np.array([[0, 10, 0.]])
    qs = np.array([[2, 2, 5.], [-3, -4, 0.], [5, -2, 0.], [10, 10, 0.], [20, 0, 0.]])
    want = [5, 5, 2, np.sqrt(50), 10]
    check('triangle regions', closest_point_dist(qs, np.repeat(a, 5, 0), np.repeat(b, 5, 0), np.repeat(c, 5, 0)), want)

    # 2 plane z=1000, 20-vox grid; points at known heights, including dense-cell centres where the
    # nearest vertex is up to 14.1 vox away laterally (the CORR-RETRACE defect case)
    S = Surface(plane())
    P = np.array([[810, 810, 1000.0 + h] for h in (0, 0.5, 1, 2, 7.3, 100, 499.9, 500.1)])
    check('plane heights (cell centre)', S.point_dist(P), [0, 0.5, 1, 2, 7.3, 100, 499.9, 500.1])
    check('plane min over set', S.min_dist(P)[0], 0.0)
    check('plane far point 3000', S.point_dist(np.array([[810, 810, 4000.0]])), [3000.0])
    P2 = np.array([[810, 810, 1003.0], [830, 850, 1250.0]])
    check('plane set min = 3', S.min_dist(P2)[0], 3.0)
    # outside plane footprint: distance to boundary edge
    check('beyond plane edge', S.point_dist(np.array([[500 - 30.0, 700, 1040.0]])), [50.0])

    # 3 folded sheet: V fold along x = 900, both wings rising at 45 deg
    n = 40; j, i = np.meshgrid(np.arange(n), np.arange(n))
    x = 500 + j * 20.0; y = 500 + i * 20.0
    z = 1000 + np.abs(x - 900)
    Sf = Surface(np.stack([x, y, z], -1).astype(np.float32))
    # inside the V above the crease at height h: nearest is a wing at h/sqrt2
    check('fold: inside V above crease', Sf.point_dist(np.array([[900, 800, 1000 + 100.0]])), [100 / np.sqrt(2)])
    # below the crease: nearest is the crease line itself
    check('fold: below crease', Sf.point_dist(np.array([[900, 800, 1000 - 37.0]])), [37.0])
    # off-wing normal distance: point p = foot + d * n, foot on right wing
    foot = np.array([1100, 810, 1200.0]); nrm = np.array([1, 0, -1]) / np.sqrt(2)
    check('fold: wing normal offset 13', Sf.point_dist((foot + 13 * nrm)[None]), [13.0])
    # sheet folded back on itself (U), point between the two layers, 6 vox from one, 14 from the other
    xs = 500 + j * 20.0
    zu = np.where(i < 20, 1000.0, 1020.0)
    yu = np.where(i < 20, 500 + i * 20.0, 500 + (39 - i) * 20.0)
    # join rows 19/20 by a vertical segment at y=880
    gu = np.stack([xs, yu, zu], -1).astype(np.float32)
    Su = Surface(gu)
    check('U fold: between layers', Su.point_dist(np.array([[810, 700, 1006.0]])), [6.0])
    check('U fold: between layers other side', Su.point_dist(np.array([[810, 700, 1014.0]])), [6.0])

    # 4 invalid cells: hole punched in the plane -> distance to hole rim
    g = plane(); g[10:20, 10:20] = -1
    Sh = Surface(g)
    # hole covers vertices 10..19 -> removed quads span x,y in (500+9*20, 500+20*20) = (680, 900)
    check('hole centre dist to rim', Sh.point_dist(np.array([[790, 790, 1000.0]])), [110.0])

    # 5 random curved sheets: exact method == brute force
    rng = np.random.default_rng(20260926)
    worst = 0.0
    for t in range(6):
        n = 25; j, i = np.meshgrid(np.arange(n), np.arange(n))
        x = 1000 + j * 20.0 + rng.normal(0, 3, (n, n)); y = 1000 + i * 20.0 + rng.normal(0, 3, (n, n))
        z = 2000 + 80 * np.sin(j / 4.0 + t) + 60 * np.cos(i / 5.0) + rng.normal(0, 2, (n, n))
        g = np.stack([x, y, z], -1).astype(np.float32)
        g[rng.random((n, n)) < 0.05] = -1
        Sr = Surface(g)
        Q = np.column_stack([rng.uniform(900, 1600, 60), rng.uniform(900, 1600, 60), rng.uniform(1700, 2400, 60)])
        a1 = Sr.point_dist(Q); a2 = Sr.brute(Q); a3 = Sr.point_dist_loop(Q)
        worst = max(worst, float(np.abs(a1 - a2).max()), float(np.abs(a3 - a2).max()))
        m = Sr.min_dist(Q)[0]
        check(f'random sheet {t}: set min == brute min', m, a2.min(), 1e-6)
    check('random sheets: per-point max |exact - brute| (batched and loop)', worst, 0.0, 1e-6)

    # 6 worst case for the L/sqrt(3) radius: equilateral-ish lattice, point straight above a
    # triangle centroid (nearest vertex at circumradius), distances small and large
    n = 30; j, i = np.meshgrid(np.arange(n), np.arange(n))
    x = 1000 + 20.0 * (j + 0.5 * (i % 2)); y = 1000 + 20.0 * np.sqrt(3) / 2 * i
    ge = np.stack([x, y, np.full(x.shape, 3000.0)], -1).astype(np.float32)
    Se = Surface(ge)
    Q = np.column_stack([rng.uniform(1100, 1400, 300), rng.uniform(1100, 1400, 300), 3000 + rng.choice([0.01, 0.3, 2, 40, 900], 300)])
    check('lattice: batched == brute', float(np.abs(Se.point_dist(Q) - Se.brute(Q)).max()), 0.0, 1e-6)
    m, _, info = Se.min_dist(Q)
    check('lattice: set min', m, float(Se.brute(Q).min()), 1e-6)
    npass = sum(r['pass'] for r in R)
    print(f'{npass}/{len(R)} pass, {time.time() - t0:.1f}s')
    json.dump({'tests': R, 'pass': npass, 'total': len(R)}, open(sys.argv[1] if len(sys.argv) > 1 else '/dev/null', 'w'), indent=1)
    return npass == len(R)


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
