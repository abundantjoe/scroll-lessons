"""Input manifest: public URL and SHA-256 of every input file, verified against the remote copy.

  manifest_inputs.py <out.json> [--verify-remote]

Inputs pinned: the Grand-Prize hand labels (GitHub), the team ink-detection overviews and surface renders (S3, ds8 JPEGs), and the
2.4 um surface-volume zarr metadata (.zarray, .zattrs). Zarr chunks are fetched per crop and deleted after use, so they are pinned by
the versioned volume URL plus metadata hash, not chunk by chunk. Files derived locally (``*_L.png``, ``mid_l3.png``, ``onsheet_ds8.png``)
are listed with their derivation.
"""
import hashlib, json, os, sys, tempfile, urllib.request

S3 = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/segments"
GH = "https://raw.githubusercontent.com/younader/Vesuvius-Grandprize-Winner/main/all_labels"
VOL = "2.4um-0.22m-78keV-volume-20260411134726"
INK = "20260417190342-new_canon_autoresearch_recipe-tile256-stride128"
SEGS = ["20231005123336", "20231210121321", "20230929220926", "20231012184424"]
LABEL_SRC = {"20231012184424": "20231012184423"}     # recorded in RULES.md at declaration: this segment uses the 184423 label


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def remote_sha(url):
    with tempfile.NamedTemporaryFile() as t:
        with urllib.request.urlopen(url, timeout=300) as r:
            while True:
                b = r.read(1 << 20)
                if not b: break
                t.write(b)
        t.flush(); return sha(t.name), os.path.getsize(t.name)


def main():
    out, verify = sys.argv[1], "--verify-remote" in sys.argv
    items = []
    for seg in SEGS:
        src = LABEL_SRC.get(seg, seg)
        local = f"data/s1/labels/{src}_inklabels.png"
        items.append({"role": "hand label (Grand Prize, 7.91 um UV)", "segment": seg, "url": f"{GH}/{src}_inklabels.png",
                      "local": local if os.path.exists(local) else None, "note": "" if src == seg else f"published as {src}"})
        for role, url, local in (
            ("team ink-detection overview (ds8, JPEG)", f"{S3}/{seg}/ink-detection/downsampled/PHercParis4-{seg}-{VOL}-{INK}-ds8.jpg",
             f"data/s1/{seg}/overview/ink_ds8.jpg"),
            ("surface render overview (ds8, JPEG)", f"{S3}/{seg}/surface-renders/downsampled/PHercParis4-{seg}-{VOL}-alpha-overlay-combined-ds8.jpg",
             f"data/s1/{seg}/overview/render_ds8.jpg"),
            ("surface volume metadata .zarray (level 0)", f"{S3}/{seg}/surface-volumes/{VOL}.zarr/0/.zarray", None),
            ("surface volume metadata .zattrs", f"{S3}/{seg}/surface-volumes/{VOL}.zarr/.zattrs", None)):
            items.append({"role": role, "segment": seg, "url": url, "local": local if local and os.path.exists(local) else None})
    for it in items:
        if it.get("local"):
            it["sha256_local"] = sha(it["local"]); it["bytes_local"] = os.path.getsize(it["local"])
        if verify or not it.get("local"):
            try:
                it["sha256_remote"], it["bytes_remote"] = remote_sha(it["url"])
            except Exception as e:
                it["remote_error"] = repr(e)
        if it.get("sha256_local") and it.get("sha256_remote"):
            it["verified_identical"] = it["sha256_local"] == it["sha256_remote"]
        print(it["segment"], it["role"][:40], it.get("verified_identical", "-"), (it.get("sha256_local") or it.get("sha256_remote", ""))[:16], flush=True)
    derived = [
        {"file": "data/s1/labels/<seg>_inklabels_L.png", "derivation": "PIL Image.open(published RGB label).convert('L'); verified pixel-identical"},
        {"file": "data/s1/20231005123336/overview/mid_l3.png", "derivation": "CT mid slice of the surface volume at pyramid level 3 (on-sheet proxy)"},
        {"file": "data/s1/<seg>/overview/onsheet_ds8.png", "derivation": "on-sheet mask of the surface volume at ds8 (segments where it exists)"},
    ]
    json.dump({"inputs": items, "derived_locally": derived, "volume_version": VOL, "ink_model_version": INK}, open(out, "w"), indent=1)
    print("written", out)


if __name__ == "__main__":
    main()
