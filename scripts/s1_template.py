"""Depth templates. 'from_d1': w_face(δ) = mean_text − mean_blank from a D1 json (w028), δ in [-4, 6], unit L2. 'measure': same measured on a Scroll-1 TRAIN crop (needs I_stack_<face>.npy written by s1_score.py --dump)."""
import sys, os, json, numpy as np
mode = sys.argv[1]; DELTAS = list(range(-4, 7))
if mode == "from_d1":
    d1, out = sys.argv[2], sys.argv[3]; r = json.load(open(d1)); dl = r["deltas"]; T = {}
    for face in ("top", "bot"):
        w = np.array([r[face]["mean_text"][dl.index(d)] - r[face]["mean_blank"][dl.index(d)] for d in DELTAS], np.float64)
        T[face] = (w / np.linalg.norm(w)).tolist()
    json.dump({"source": d1, "deltas": DELTAS, "w": T}, open(out, "w"), indent=1); print(json.dumps(T))
else:  # measure <derived_dir> <out>
    d, out = sys.argv[2], sys.argv[3]; T = {}
    text = np.load(os.path.join(d, "cls_text.npy")); blank = np.load(os.path.join(d, "cls_blank.npy"))
    for face in ("top", "bot"):
        P = np.load(os.path.join(d, f"I_stack_{face}.npy"), mmap_mode="r")  # (len(DELTAS), H, W) float16
        w = np.array([float(np.asarray(P[i])[text].mean()) - float(np.asarray(P[i])[blank].mean()) for i in range(len(DELTAS))])
        T[face] = (w / np.linalg.norm(w)).tolist(); print(face, "raw diff", np.round(w, 2).tolist())
    json.dump({"source": d, "deltas": DELTAS, "w": T}, open(out, "w"), indent=1)
