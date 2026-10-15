# Provenance: Project HERCULES | owner the owner | [id removed]
# Decode official LZW model-map TIFFs (needs imagecodecs, present only in /opt/hv-ink) to <tif>.npy for auc_eval.py.
import sys, hashlib, numpy as np, tifffile
for p in sys.argv[1:]:
    a = tifffile.imread(p)
    np.save(p + '.npy', a)
    print(p, a.shape, a.dtype, int(a.min()), int(a.max()), hashlib.sha256(open(p, 'rb').read()).hexdigest())
