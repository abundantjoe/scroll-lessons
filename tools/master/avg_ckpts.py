# Provenance: Project HERCULES | [id removed]
"""Federated averaging of Master checkpoints trained one epoch each on disjoint shard subsets (plain parameter mean,
weighted by the number of training crops). usage: avg_ckpts.py <out.pt> <ckpt1.pt> <ckpt2.pt> ..."""
import sys, torch
out, paths = sys.argv[1], sys.argv[2:]; cks = [torch.load(p, map_location='cpu') for p in paths]; ws = [float(c.get('n_train', 1)) for c in cks]; W = sum(ws)
avg = {k: sum(c['model'][k].float() * w for c, w in zip(cks, ws)) / W for k in cks[0]['model']}
for k in avg: avg[k] = avg[k].to(cks[0]['model'][k].dtype)
torch.save({'model': avg, 'base': cks[0]['base'], 'ssl': cks[0].get('ssl'), 'round_members': paths, 'n_train': int(W)}, out); print('averaged', len(cks), 'checkpoints ->', out)
