#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""Cheap, undeclared, numbers-only test (orchestrator 06:53Z suggestion): does a per-tile input re-normalisation to
PHerc.1667-iteration-5's training input statistics change the gate-tile prediction mean/std on r0 c7?

Training statistics are taken from the weights themselves (no training data exists here): bn1 follows the bias-free
linear conv1, so for an affine input change x' = a*x + b (x = clip(u8,0,200)/255):
    mean_c(conv1 x') = a*mean_c(conv1 x) + b*sum(w_c),   var_c(conv1 x') = a^2 * var_c(conv1 x).
a is fitted so the tile's conv1 variances match bn1.running_var (median ratio), then b by least squares so the means
match bn1.running_mean. Region: a 768 x 768 core at the centre of r0 c7 (+128 halo), card tiling, both variants.
Outputs only scalars to logs/sib/ckpt-screen-b/p4o/renorm_test.json. No image is written or viewed."""
import json, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import infer_1667 as I  # noqa: E402
import p4o_tiles as P  # noqa: E402

R, C, CORE = 0, 7, 768
cy, cx = R * P.T + P.T // 2, C * P.T + P.T // 2
y0, x0 = cy - CORE // 2 - P.HALO, cx - CORE // 2 - P.HALO
y1, x1 = y0 + CORE + 2 * P.HALO, x0 + CORE + 2 * P.HALO
H = W = CORE + 2 * P.HALO


def main():
    import torch
    torch.set_num_threads(int(os.environ.get('THREADS', '4')))
    t0 = time.time()
    valid = P.load_valid()
    m = P.canvas_mask(valid, P.H0, P.W0, y0, y1, x0, x1)
    img, rd = P.read_stack(y0, y1, x0, x1, H, W, P.ORDER[5])
    model, ck = I.load_model(5)
    fm = P.FastModel(model)
    sd = model.state_dict()
    Wc = sd['backbone.conv1.weight'].double()
    rm, rv = sd['backbone.bn1.running_mean'].double(), sd['backbone.bn1.running_var'].double()
    ws = Wc.reshape(64, -1).sum(1)
    # conv1 statistics of this region's normalised input (valid windows only)
    xs = []
    for yy in range(0, H - 255, 256):
        for xx in range(0, W - 255, 256):
            if m[yy:yy + 256, xx:xx + 256].all():
                xs.append(torch.from_numpy(img[yy:yy + 256, xx:xx + 256]).permute(2, 0, 1)[None, None].float())
    # per-window accumulation (one window's conv1 output is ~260 MB; a batched pass OOM-killed the first run)
    s1 = torch.zeros(64, dtype=torch.float64)
    s2 = torch.zeros(64, dtype=torch.float64)
    nn_ = 0
    xsum = xsq = xn = 0.0
    with torch.no_grad():
        for xw in xs:
            xw = I.train_norm(xw)
            xsum += float(xw.double().sum()); xsq += float((xw.double() ** 2).sum()); xn += xw.numel()
            y = model.backbone.conv1(xw.contiguous())[0]
            s1 += y.double().sum((1, 2, 3)); s2 += (y.double() ** 2).sum((1, 2, 3)); nn_ += y[0].numel()
            del y
    mc = s1 / nn_
    vc = s2 / nn_ - mc ** 2
    xmean = xsum / xn
    xstd = (xsq / xn - xmean ** 2) ** 0.5
    a = float(torch.sqrt(torch.median(rv / vc)))
    b = float(((rm - a * mc) * ws).sum() / (ws * ws).sum())
    res = dict(provenance=I.PROV, test='per-tile affine input re-normalisation to bn1 training statistics (undeclared, '
                                       'numbers only, orchestrator suggestion 06:53Z)',
               tile=[R, C], region_canvas=dict(rows=[y0, y1], cols=[x0, x1], core=CORE), mesh_valid_frac=float(m.mean()),
               input_norm_stats=dict(mean=xmean, std=xstd, n_windows=len(xs)),
               bn1_fit=dict(a=a, b=b, corr_mean_before=float(np.corrcoef(mc.numpy(), rm.numpy())[0, 1]),
                            median_var_ratio=float(torch.median(rv / vc)),
                            implied_training_input=dict(mean=a * xmean + b, std=a * xstd)),
               chunks=rd, checkpoint_sha256=ck['files']['model.safetensors']['sha256'])
    core = (slice(P.HALO, P.HALO + CORE), slice(P.HALO, P.HALO + CORE))
    fmk = np.zeros((I.pad256(H), I.pad256(W)), np.uint8)
    fmk[:H, :W] = m
    imgp = np.zeros((I.pad256(H), I.pad256(W), img.shape[2]), np.uint8)
    imgp[:H, :W] = img
    tf = lambda yy, xx: imgp[yy:yy + 256, xx:xx + 256]
    for name, norm in (('baseline', I.train_norm), ('renorm', lambda t: I.train_norm(t).mul_(a).add_(b))):
        pred, cnt = I.card_tiling(fm, fmk.shape[0], fmk.shape[1], fmk, tf, norm)
        u8 = I.to_u8(pred[:H, :W][core])
        v = u8[m[core]]
        res[name] = dict(mean=float(v.mean()), std=float(v.std()), p5=float(np.percentile(v, 5)),
                         p95=float(np.percentile(v, 95)), frac_gt_127=float((v > 127).mean()),
                         coverage=float((cnt[:H, :W][core] > 0)[m[core]].mean()), sha256=I.arr_sha(u8))
        print(name, json.dumps(res[name]), flush=True)
    res['seconds'] = round(time.time() - t0, 1)
    p = os.path.join(I.REPO, 'logs/sib/ckpt-screen-b/p4o/renorm_test.json')
    json.dump(res, open(p, 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('input_norm_stats', 'bn1_fit', 'baseline', 'renorm')}))


if __name__ == '__main__':
    main()
