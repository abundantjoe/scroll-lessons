"""Download every input of the release from its public source and verify it against results/input_manifest.json (SHA-256).

  fetch_inputs.py [--segments 20231005123336,20231210121321,...]

Writes data/s1/labels/<seg>_inklabels.png (+ the grayscale *_L.png the pipeline reads), data/s1/<seg>/overview/ink_ds8.jpg and
render_ds8.jpg, and copies the committed crop/registration records into data/s1/<seg>/. A file whose hash differs from the manifest is
deleted and the script exits non-zero: the release's numbers are only claimed for byte-identical inputs.
The 2.4 um surface volumes themselves are streamed per crop by scripts/fetch_zarr_region.py (pinned by versioned URL).
"""
import hashlib, json, os, shutil, sys, urllib.request
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
M = json.load(open("results/input_manifest.json"))
segs = None
if "--segments" in sys.argv:
    segs = sys.argv[sys.argv.index("--segments") + 1].split(",")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def get(url, dest, want):
    if os.path.exists(dest) and sha(dest) == want:
        print("ok (cached)", dest); return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    with urllib.request.urlopen(url, timeout=600) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)
    got = sha(tmp)
    if got != want:
        os.remove(tmp); print(f"HASH MISMATCH {dest}: got {got}, manifest {want}"); return False
    os.replace(tmp, dest); print("ok", dest); return True


ok = True
for it in M["inputs"]:
    seg = it["segment"]
    if segs and seg not in segs: continue
    if not it.get("local"): continue                      # zarr metadata: pinned, not downloaded here
    want = it.get("sha256_remote") or it.get("sha256_local")
    ok &= get(it["url"], it["local"], want)
    if it["local"].endswith("_inklabels.png"):
        src_seg = os.path.basename(it["local"]).split("_")[0]
        L = f"data/s1/labels/{seg}_inklabels_L.png"
        if not os.path.exists(L):
            Image.open(it["local"]).convert("L").save(L)
            print("derived", L, "(grayscale conversion of the label published as", src_seg + ")")
for seg in {i["segment"] for i in M["inputs"]}:
    if segs and seg not in segs: continue
    os.makedirs(f"data/s1/{seg}", exist_ok=True)
    for src, dst in ((f"stats/s1_crops_{seg}.json", "crops.json"), (f"stats/s1_registration_{seg}.json", "label_registration.json"),
                     (f"stats/r1_unread_{seg}.json", "unread.json"), (f"stats/c1_confirm_{seg}.json", "confirm.json")):
        if os.path.exists(src):
            shutil.copy(src, f"data/s1/{seg}/{dst}")
print("ALL INPUTS VERIFIED" if ok else "SOME INPUTS FAILED VERIFICATION")
sys.exit(0 if ok else 1)
