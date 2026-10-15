# Provenance: Project HERCULES | [id removed]
"""Window-census candidate rule (RULES.md DECL-P4-25-A11-A1 item 2). Numbers only.

candidates(pos_windows, max_side=3, max_n=3):
  pos_windows: {(r, c): count} of POSITIVE 2x2-tile windows (top-left tile r, c) of ONE strip.
  8-connected clusters of positive windows; each cluster's tile footprint = union of its windows' 2x2 tiles.
  A cluster is a candidate iff its footprint spans <= max_side tile rows AND <= max_side tile columns
  (a title-sized block, <= 6 x 6 cm); larger footprints are 'column-like' (reported, not candidates).
  Candidates are ranked by max window count, then size; at most max_n are returned.
"""


def clusters(keys):
    keys = set(keys)
    out = []
    while keys:
        stack = [keys.pop()]
        comp = set(stack)
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    n = (r + dr, c + dc)
                    if n in keys:
                        keys.remove(n); comp.add(n); stack.append(n)
        out.append(comp)
    return out


def footprint(comp):
    return {(r + a, c + b) for r, c in comp for a in (0, 1) for b in (0, 1)}


def candidates(pos_windows, max_side=3, max_n=3):
    cands, columns = [], []
    for comp in clusters(pos_windows):
        fp = footprint(comp)
        rs = [r for r, _ in fp]; cs = [c for _, c in fp]
        h, w = max(rs) - min(rs) + 1, max(cs) - min(cs) + 1
        rec = {'windows': sorted(comp), 'tiles': sorted(fp), 'rows': h, 'cols': w,
               'max_count': max(pos_windows[k] for k in comp)}
        (cands if h <= max_side and w <= max_side else columns).append(rec)
    cands.sort(key=lambda d: (-d['max_count'], -len(d['windows']), d['windows']))
    return cands[:max_n], cands[max_n:], columns


def _test():
    # planted 3x3-tile block (2x2 windows) survives; a 5-row column (4 windows in a column -> 5 tile rows) is dropped
    pos = {(1, 1): 9, (1, 2): 8, (2, 1): 7, (2, 2): 6,          # footprint rows 1-3, cols 1-3 -> 3x3 -> candidate
           (0, 8): 5, (1, 8): 6, (2, 8): 7, (3, 8): 8}          # footprint rows 0-4 (5 rows) -> column
    c, over, col = candidates(pos)
    assert len(c) == 1 and c[0]['rows'] == 3 and c[0]['cols'] == 3, c
    assert len(col) == 1 and col[0]['rows'] == 5, col
    many = {(r, 10 * r): 5 + r for r in range(5)}                 # 5 isolated single windows -> 5 candidates, cap 3
    c, over, col = candidates(many)
    assert len(c) == 3 and len(over) == 2 and [x['max_count'] for x in c] == [9, 8, 7]
    return 'ok'


if __name__ == '__main__':
    print(_test())
