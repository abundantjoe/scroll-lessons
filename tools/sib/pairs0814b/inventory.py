# Provenance: Project HERCULES | owner the owner | [id removed]
"""Task pairs0814 goal (a): field-by-field protocol check and data inventory of the known-text scrolls.

Sources (official only): the public bucket vesuvius-challenge-open-data (anonymous HTTPS): the root index
metadata.json, every volume's own metadata.json, and delimiter listings of <scroll>/segments/. Numbers and
paths only; no image is downloaded or opened.

Protocol fields per scan (7): session (BlissFirstScan path .../bm18/<session>/), voxel size (the VOLUME's
metadata.json scan.tomo.acquisition.detector.samplePixelSize, mm -> um; the index pixel_size_um is reported
alongside), keV, detector distance, exposure (expo_time), Paganin delta/beta, unsharp coeff/sigma.
References are re-derived from the index (JULY = PHerc0139 scan of volume 20250728140407; MAY = PHerc0009B scan
of volume 20250521125136) and checked against the task brief's numbers.

Usage: python3 inventory.py OUT_DIR
"""
import hashlib
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BUCKET = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
SCROLLS = ["PHerc0814", "PHerc0500P2", "PHerc0332", "PHerc1451"]
REF = {"JULY": ("PHerc0139", "20250728140407"), "MAY": ("PHerc0009B", "20250521125136")}
BRIEF = {  # the task brief's reference values (checked, not trusted)
    "JULY": dict(session="20250717", voxel_um=9.362, keV=113.0, distance_m=1.2, exposure_s=0.012,
                 paganin=1000.0, unsharp=[4.0, 1.2]),
    "MAY": dict(session="20250506", voxel_um=8.640, keV=116.0, exposure_s=0.03),
}
FIELDS = ["session", "voxel_um", "keV", "distance_m", "exposure_s", "paganin", "unsharp"]
TOL = {"voxel_um": 5e-4, "keV": 1e-6, "distance_m": 1e-3, "exposure_s": 1e-9, "paganin": 1e-6}
CTX = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE", "/root/.ccr/ca-bundle.crt"))
FETCHED = []


def get(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
            with urllib.request.urlopen(req, context=CTX, timeout=120) as r:
                b = r.read()
            if b[:2] == b"\x1f\x8b":
                import gzip
                b = gzip.decompress(b)
            return b
        except Exception as e:  # network retry with backoff
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))


def get_json(url):
    b = get(url)
    FETCHED.append({"url": url, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    return json.loads(b)


def s3_list(prefix, delimiter="/"):
    """(common prefixes, [(key, size)]) under prefix, all pages."""
    dirs, files, token = [], [], None
    ns = "{http://s3.amazonaws.com/doc/2006-03-01/}"
    while True:
        q = f"list-type=2&prefix={urllib.parse.quote(prefix)}"
        if delimiter:
            q += f"&delimiter={urllib.parse.quote(delimiter)}"
        if token:
            q += f"&continuation-token={urllib.parse.quote(token)}"
        root = ET.fromstring(get(f"{BUCKET}/?{q}"))
        dirs += [e.find(f"{ns}Prefix").text for e in root.findall(f"{ns}CommonPrefixes")]
        files += [(e.find(f"{ns}Key").text, int(e.find(f"{ns}Size").text)) for e in root.findall(f"{ns}Contents")]
        if root.find(f"{ns}IsTruncated").text != "true":
            return dirs, files
        token = root.find(f"{ns}NextContinuationToken").text


def scan_fields(scan):
    m = scan["creation"]["metadata"]
    tomo = (m.get("metadata") or {}).get("tomo") or {}
    acq = tomo.get("acquisition") or {}
    proc = tomo.get("processing") or {}
    phase = (proc.get("preprocessing") or {}).get("phase") or {}
    first = (proc.get("general") or {}).get("BlissFirstScan")
    sess = None
    if first:
        mm = re.search(r"/bm18/(\d{8})/", first)
        sess = mm.group(1) if mm else None
    dist = acq.get("sampleDetectorDistance", m.get("detector_distance_mm"))
    return {
        "session": sess,
        "index_pixel_size_um": m.get("pixel_size_um"),
        "keV": acq.get("energy", m.get("energy_keV")),
        "distance_m": None if dist is None else round(float(dist) / 1000.0, 5),
        "exposure_s": acq.get("expo_time"),
        "paganin": phase.get("delta_beta") if (phase.get("method") or "").lower() == "paganin" else None,
        "phase_method": phase.get("method"),
        "unsharp": [phase.get("unsharp_coeff"), phase.get("unsharp_sigma")] if phase else None,
        "unsharp_method": phase.get("unsharp_method"),
        "extra": {"sensor": (acq.get("detector") or {}).get("sensor"),
                  "optics": (acq.get("detector") or {}).get("opticsName"),
                  "scintillator": (acq.get("detector") or {}).get("scintillator"),
                  "half_acquisition": acq.get("half_acquisition"), "scanType": acq.get("scanType"),
                  "tomo_N": acq.get("tomo_N"), "recon": (proc.get("reconstruction") or {}).get("method"),
                  "bliss_first_scan": first},
    }


def eq(field, a, b):
    if a is None or b is None:
        return None
    if field == "session":
        return str(a) == str(b)
    if field == "unsharp":
        return all(x is not None and abs(float(x) - float(y)) <= 1e-9 for x, y in zip(a, b))
    return abs(float(a) - float(b)) <= TOL[field]


def compare(obs, ref):
    rows = {}
    for f in FIELDS:
        if f not in ref:
            rows[f] = {"observed": obs.get(f), "reference": None, "match": "not in protocol"}
            continue
        m = eq(f, obs.get(f), ref[f])
        rows[f] = {"observed": obs.get(f), "reference": ref[f],
                   "match": "MISSING" if m is None else ("MATCH" if m else "DIFFER")}
    decided = [r["match"] for r in rows.values() if r["match"] in ("MATCH", "DIFFER", "MISSING")]
    n_match = sum(1 for m in decided if m == "MATCH")
    return {"fields": rows, "n_compared": len(decided), "n_match": n_match,
            "verdict": "MATCH" if n_match == len(decided) else "NO MATCH"}


def classify(key):
    k = key.lower()
    if "/ink-labels/" in k:
        return "ink_labels"
    if "/ink-detection/" in k:
        return "ink_map_downsampled" if "/downsampled/" in k else "ink_map"
    if "/surface-volumes/" in k:
        return "surface_volume"
    if "/mesh/" in k or k.endswith(".obj") or "tifxyz" in k:
        return "mesh"
    return "other"


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    root = get_json(f"{BUCKET}/metadata.json")
    S = root["samples"]
    vol_meta = {}

    def vmeta(scroll, vol):
        if (scroll, vol["id"]) not in vol_meta:
            url = f"{BUCKET}/{scroll}/volumes/{vol['long_id']}/metadata.json"
            try:
                md = get_json(url)
                mm = md["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]
                vol_meta[(scroll, vol["id"])] = {"url": url, "voxel_um": round(float(mm) * 1000.0, 6),
                                                 "sha256": FETCHED[-1]["sha256"]}
            except Exception as e:
                vol_meta[(scroll, vol["id"])] = {"url": url, "voxel_um": None, "error": repr(e)[:200]}
        return vol_meta[(scroll, vol["id"])]

    def volume_rows(scroll):
        rows = []
        for vid, v in sorted(S[scroll]["volumes"].items()):
            sc = S[scroll]["scans"].get(v.get("scan_id"))
            f = scan_fields(sc) if sc else {}
            vm = vmeta(scroll, v)
            f["voxel_um"] = vm.get("voxel_um")
            rows.append({"volume_id": vid, "long_id": v["long_id"], "scan_id": v.get("scan_id"),
                         "volume_metadata": vm, "fields": f})
        return rows

    # references, re-derived
    refs = {}
    for name, (scroll, vid) in REF.items():
        row = next(r for r in volume_rows(scroll) if r["volume_id"] == vid)
        f = row["fields"]
        derived = {k: f.get(k) for k in FIELDS}
        brief_check = {k: {"brief": BRIEF[name][k], "index": derived[k],
                           "agree": eq(k, derived[k], BRIEF[name][k])} for k in BRIEF[name]}
        protocol = dict(BRIEF[name])  # MAY: distance/Paganin/unsharp not in the brief -> 'not in protocol'
        refs[name] = {"scroll": scroll, "volume": row, "derived": derived, "brief_check": brief_check,
                      "protocol_used": protocol}

    protocol = {}
    for scroll in SCROLLS:
        vols = volume_rows(scroll)
        for r in vols:
            r["vs_JULY"] = compare(r["fields"], refs["JULY"]["protocol_used"])
            r["vs_MAY"] = compare(r["fields"], refs["MAY"]["protocol_used"])
        july = [r["volume_id"] for r in vols if r["vs_JULY"]["verdict"] == "MATCH"]
        may = [r["volume_id"] for r in vols if r["vs_MAY"]["verdict"] == "MATCH"]
        protocol[scroll] = {"sample_type": ((S[scroll]["sample"].get("properties") or {}).get("type")),
                            "volumes": vols, "JULY_match_volumes": july, "MAY_match_volumes": may,
                            "verdict": ("JULY" if july else "") + ("+" if july and may else "") +
                                       ("MAY" if may else "") or "NEITHER"}

    # inventories
    inv = {}
    for scroll in SCROLLS:
        idx = S[scroll].get("segments") or {}
        seg_dirs, top_files = s3_list(f"{scroll}/segments/")
        segs = {}
        for d in seg_dirs:
            name = d.rstrip("/").split("/")[-1]
            sid = name.split("-", 1)[0]
            rec = {"s3_dir": d, "indexed": sid in idx, "subdirs": {}, "counts": {}}
            if sid in idx:
                e = idx[sid]
                rec["index"] = {"long_id": e["long_id"], "original_volume_id": e.get("original_volume_id"),
                                "width": (e.get("properties") or {}).get("width"),
                                "height": (e.get("properties") or {}).get("height"),
                                "scale": e["creation"]["metadata"].get("scale"),
                                "data_types": sorted({x["type"] for x in e.get("data", [])}),
                                "data_paths": sorted({(x["type"], o["path"]) for x in e.get("data", [])
                                                      for o in x.get("origins", [])})}
            sub, files = s3_list(d)
            rec["top_files"] = [k for k, _ in files]
            for sd in sub:
                sname = sd[len(d):].rstrip("/")
                if sname in ("surface-volumes", "mesh", "ink-detection", "ink-labels"):
                    s2, f2 = s3_list(sd)
                    rec["subdirs"][sname] = {"dirs": [x[len(sd):] for x in s2],
                                             "files": [(x[len(sd):], n) for x, n in f2]}
                    if sname == "ink-detection":
                        s3d, f3 = s3_list(sd + "downsampled/")
                        rec["subdirs"][sname]["downsampled"] = [(x[len(sd):], n) for x, n in f3]
                    if sname == "mesh":
                        for mdir in s2:
                            if mdir.endswith("intermediate/"):
                                s4, f4 = s3_list(mdir)
                                rec["subdirs"][sname]["intermediate"] = {"dirs": [x[len(sd):] for x in s4],
                                                                         "files": [(x[len(sd):], n) for x, n in f4]}
                    if sname == "ink-labels":
                        deep = []
                        for vdir in s2:
                            s5, _ = s3_list(vdir)
                            deep += [x[len(sd):] for x in s5]
                        rec["subdirs"][sname]["label_sets"] = deep
                else:
                    rec["subdirs"][sname] = {"dirs": "not listed"}
            sv = rec["subdirs"].get("surface-volumes", {}).get("dirs", [])
            mesh = rec["subdirs"].get("mesh", {})
            ink = rec["subdirs"].get("ink-detection", {}).get("files", [])
            rec["surface_volumes"] = sv
            rec["meshes_tifxyz"] = [x for x in mesh.get("dirs", []) if x.rstrip("/").endswith(".tifxyz")]
            rec["meshes_obj"] = [x for x, _ in mesh.get("files", []) if x.endswith(".obj")] + \
                [x for x, _ in (mesh.get("intermediate") or {}).get("files", []) if x.endswith(".obj")]
            rec["ink_maps"] = [(x, n) for x, n in ink if x.endswith(".tif")]
            rec["ink_labels"] = rec["subdirs"].get("ink-labels", {}).get("label_sets", [])
            hr = re.compile(r"(2\.\d+um|1\.\d+um|0\.\d+um)")
            rec["counts"] = {"surface_volumes": len(sv),
                             "surface_volumes_highres": sum(1 for x in sv if hr.search(x)),
                             "mesh_tifxyz": len(rec["meshes_tifxyz"]), "mesh_obj": len(rec["meshes_obj"]),
                             "ink_maps": len(rec["ink_maps"]), "ink_label_sets": len(rec["ink_labels"])}
            segs[name] = rec
        unindexed_in_index = sorted(set(idx) - {n.split("-", 1)[0] for n in segs})
        tot = {k: sum(r["counts"].get(k, 0) for r in segs.values())
               for k in ("surface_volumes", "surface_volumes_highres", "mesh_tifxyz", "mesh_obj", "ink_maps",
                         "ink_label_sets")}
        inv[scroll] = {"n_s3_segment_dirs": len(segs), "n_indexed": len(idx),
                       "indexed_but_missing_on_s3": unindexed_in_index,
                       "top_level_files": [k for k, _ in top_files], "totals": tot,
                       "volumes": [{"volume_id": v["volume_id"], "long_id": v["long_id"],
                                    "voxel_um_metadata": v["volume_metadata"].get("voxel_um"),
                                    "highres": (v["volume_metadata"].get("voxel_um") or 99) < 5.0}
                                   for v in protocol[scroll]["volumes"]],
                       "segments": segs}

    out = {"provenance": "Project HERCULES | owner the owner | [id removed]",
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "viewing": "no image was downloaded or opened; metadata and listings only",
           "references": refs, "protocol": protocol, "fetched": FETCHED}
    with open(f"{out_dir}/protocol_check.json", "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=False, default=list)
    with open(f"{out_dir}/segment_inventory.json", "w") as fh:
        json.dump({"provenance": out["provenance"], "generated_utc": out["generated_utc"],
                   "root_index_sha256": FETCHED[0]["sha256"], "inventory": inv}, fh, indent=1, default=list)
    for scroll in SCROLLS:
        p = protocol[scroll]
        print(scroll, p["verdict"], "JULY:", p["JULY_match_volumes"], "MAY:", p["MAY_match_volumes"],
              "segments:", inv[scroll]["n_s3_segment_dirs"], inv[scroll]["totals"])


if __name__ == "__main__":
    import urllib.parse  # noqa: F401
    main(sys.argv[1])
