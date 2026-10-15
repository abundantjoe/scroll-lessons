# Provenance: Project HERCULES | owner the owner | [id removed]
# P4-O input manifest for tiles r0-r5 x c0-c17 of the strip-a grid (w010-027, 2.4 um SV, level 0).
# Per tile: canvas bounds, mesh-valid fraction (grid NN, every 8th px), chunk-index ranges, number of chunk objects
# present on S3, a digest of the S3 listing (sha256 over sorted "key etag size" lines of the tile's chunk objects),
# and the content sha256 of the default model slab (z [23, 85), SV order, uint8, C-order (H, W, 62)) over the
# 512 x 512 px ROI at the 128-aligned tile centre (checkable by any consumer with p4o_stack.read_stack).
import json, sys, os, re, hashlib, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__)); import p4o_stack as P
L = 'https://vesuvius-challenge-open-data.s3.amazonaws.com/'
PRE = 'PHercParis4/segments/20260701183124-w010-027/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr/0/0/'
def list_row(cy):
    tok, out = None, {}
    while True:
        q = {'list-type': '2', 'prefix': f'{PRE}{cy}/'}
        if tok: q['continuation-token'] = tok
        t = urllib.request.urlopen(L + '?' + urllib.parse.urlencode(q), timeout=60).read().decode()
        for c in re.findall(r'<Contents>(.*?)</Contents>', t, re.S):
            k = re.search(r'<Key>(.*?)</Key>', c).group(1); e = re.search(r'<ETag>(.*?)</ETag>', c).group(1).replace('&quot;', '')
            s = int(re.search(r'<Size>(\d+)</Size>', c).group(1)); out[int(k.rsplit('/', 1)[1])] = (e, s)
        m = re.search(r'<NextContinuationToken>(.*?)</NextContinuationToken>', t)
        if not m: return cy, out
        tok = m.group(1)
R, C, T = 6, 18, P.T
cy_max = ((R * T) - 1) // 128
with ThreadPoolExecutor(16) as ex:
    rows = dict(ex.map(list_row, range(cy_max + 1)))
vf = json.load(open('/work/p4o/tile_valid_frac.json'))
tiles = {}
for r in range(R):
    for c in range(C):
        y0, y1, x0, x1 = P.tile_bounds(r, c)
        cys, cxs = range(y0 // 128, (y1 - 1) // 128 + 1), range(x0 // 128, (x1 - 1) // 128 + 1)
        lines = sorted(f'0/0/{cy}/{cx} {rows[cy][cx][0]} {rows[cy][cx][1]}' for cy in cys for cx in cxs if cx in rows[cy])
        cy_, cx_ = ((y0 + y1) // 2) // 128 * 128 - 256, ((x0 + x1) // 2) // 128 * 128 - 256
        roi = P.read_stack(cy_, cy_ + 512, cx_, cx_ + 512)
        tiles[f'r{r}_c{c}'] = dict(canvas_yx=[y0, y1, x0, x1], mesh_valid_fraction=vf[f'r{r}_c{c}'],
            chunk_rows=[cys.start, cys.stop - 1], chunk_cols=[cxs.start, cxs.stop - 1],
            chunks_expected=len(cys) * len(cxs), chunks_present=len(lines),
            listing_digest_sha256=hashlib.sha256('\n'.join(lines).encode()).hexdigest(),
            bytes_present=sum(int(l.split()[2]) for l in lines),
            center_roi_canvas_yx=[cy_, cy_ + 512, cx_, cx_ + 512], center_roi_slab_sha256=P.stack_sha256(roi),
            center_roi_nonzero_fraction=float((roi > 0).mean()))
        print(f'r{r}_c{c}', tiles[f'r{r}_c{c}']['chunks_present'], tiles[f'r{r}_c{c}']['center_roi_slab_sha256'][:12], flush=True)
json.dump(dict(tiles=tiles), open(sys.argv[1], 'w'), indent=1)
