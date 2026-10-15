#!/usr/bin/env python
"""run_patch_dir.py -- the 5.11 automation loop over one scroll's patches directory (MASTER_PROMPT_v4 5.8-5.11).

For every auto_grown_* child of <patches_dir>:
  QC + CT-mask check (scripts/patch_qc.py, marker .qc_done; verdict PASS / FAIL / UNREADABLE; only PASS goes on)
  -> render (scripts/vc_tools.sh render, 28 slices, both depth orders read; marker .render_complete)
  -> inference, the fixed 5.1 call (no --gpus on this box; marker .infer_complete_<tag>)
  -> read (scripts/read_chart.py: assertions, rule 5.5, contact sheet, ledger line; marker read_<tag>/.read_complete).
Keys already in LEDGER.md are skipped before any work. The read dir, maps, inference marker and ledger key all carry the
tag, so a second checkpoint/TTA variant is a fresh read of the same render. patch_qc.py is invoked every time (it is
idempotent itself and re-runs a stale geometry-only PASS to add the 5.8 CT-mask check). With --delete-renders the render zarr is removed after a
successful read (markers stay, so a rerun skips it). Throughput per chart goes to records/throughput.jsonl
(cm^2 read, charts, MB/s = render bytes / render seconds). Nothing here runs docker or the model itself except through
subprocess; the command builders are pure functions (tested without running anything).
um/px comes from the volume's metadata.json (samplePixelSize mm x 1000) cross-checked against the catalogue.
usage: run_patch_dir.py <patches_dir> --scroll <PHercXXXX> --vol <vol id> [--ckpt ...] [--tag ink9um_seed42+tta]
       [--delete-renders] [--only NAME ...] [--data-root ...] [--catalogue ...] [--ledger ...] [--records ...]
"""
import glob, argparse, datetime, json, os, shutil, subprocess, sys, time
import numpy as np
import requests
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import read_chart  # noqa: E402
import rule55  # noqa: E402

DATA_ROOT = DATA
BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
CATALOGUE = os.path.join(DATA_ROOT, "cat", "metadata.min.json")
CKPT = os.path.join(DATA_ROOT, "models", "ink_9um", "hybrid_3d2d-seed42", "step-075000.pth")
TAG, DEPTH_OFFSET, ORDER = "ink9um_seed42+tta", "0", "both"   # ledger key parts: scroll|surface|depth offset|ckpt+TTA|order
# RULES R-DEPTH (declared 2026-09-18; an ADMITTED verdict on 2026-09-19 was withdrawn -- it rested on a truncated map --
# and the re-run FAILED, so CENTRE stays the default): the three declared windows over the 28-slice render. The layer arguments and
# the ledger depth-offset field are locked together in one table so a read can never be filed under an offset it did
# not use -- the exact class of mismatch that the unit_origin defect was. CENTRE is the reader's own default (6..22).
DEPTH_WINDOWS = {
    "centre": dict(layers=(), offset="0", centre_slice=14),
    "low": dict(layers=("--layer-start", "0", "--layer-end", "17"), offset="-6", centre_slice=8),
    "high": dict(layers=("--layer-start", "11", "--layer-end", "28"), offset="+5", centre_slice=19),
}
VC_TOOLS, PATCH_QC, READ_CHART = [os.path.join(HERE, n) for n in ("vc_tools.sh", "patch_qc.py", "read_chart.py")]
RENDER, READ_DIR, M_RENDER, M_INFER, M_QC = "render.zarr", "read", ".render_complete", ".infer_complete_%s", ".qc_done"


def volume_info(scroll, vol, catalogue=CATALOGUE, fetch=None, cache_dir=None):
    """CT volume path, pitch string (e.g. 8.640um-1.2m-116keV) and um from the catalogue and the volume's own
    metadata.json (fetched over https unless cached under cache_dir); the two must agree within 0.5 %."""
    v = json.load(open(catalogue))["samples"][scroll]["volumes"][vol]
    path = next(d["origins"][0]["path"] for d in v["data"] if d["type"] == "ome-zarr").rstrip("/")
    name = path.split("/")[-1]                                   # <vol>-<pitch>um-1.2m-<keV>keV-masked.zarr
    pitch = name[len(vol) + 1:-len("-masked.zarr")]
    cat_um = float(v["properties"]["pixel_size_um"])
    cached = os.path.join(cache_dir, "%s-metadata.json" % vol) if cache_dir else None
    if cached and os.path.exists(cached):
        meta = json.load(open(cached))
    else:
        meta = (fetch or (lambda u: requests.get(u, timeout=120).json()))("%s/%s/metadata.json" % (BUCKET, path))
        if cached:
            os.makedirs(cache_dir, exist_ok=True); json.dump(meta, open(cached, "w"))
    meta_um = float(meta["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]) * 1000
    if abs(meta_um - cat_um) > 0.005 * cat_um:
        raise SystemExit("voxel size mismatch: metadata.json %.4f vs catalogue %.4f um" % (meta_um, cat_um))
    return dict(scroll=scroll, vol=vol, zarr_path=path, ct_url="%s/%s" % (BUCKET, path), pitch=pitch, um=meta_um, catalogue_um=cat_um)


def ledger_key(scroll, patch, tag=TAG, window="centre"):
    return "|".join([scroll, os.path.basename(patch.rstrip("/")), DEPTH_WINDOWS[window]["offset"], tag, ORDER])


def dir_tag(tag, window="centre"):
    """Marker/directory label. CENTRE keeps the historical name so no existing read is orphaned; an off-centre window
    gets its own suffix so its maps, its inference marker and its read directory cannot collide with the centre's."""
    if window == "centre":
        return tag
    return tag + "+d" + DEPTH_WINDOWS[window]["offset"].replace("+", "p").replace("-", "m")


def qc_cmd(patch, um, ct_url, cache, overlay=None):
    c = [sys.executable, PATCH_QC, patch, "--um", repr(um), "--ct-url", ct_url, "--cache", cache]
    return c + (["--overlay", overlay] if overlay else [])


def render_cmd(info, patch, render=None):
    return [VC_TOOLS, "render", info["scroll"], info["vol"], info["pitch"], repr(info["um"]), patch, render or os.path.join(patch, RENDER)]


REREAD = False
IGNORE_CREST = False
MIN_FREE_RENDER_GB = float(os.environ.get("HERCULES_MIN_FREE_RENDER_GB", 5.0))
TTA = True   # --tta-mirror in the 5.1 call; screening reads run plain since 2026-09-18 (RULES: reading recipe), TTA on candidates


# Dataloader worker count. It affects throughput only -- the maps are identical for any value -- but each worker is
# a process, and on 2026-09-19 an inference died mid-run leaving "18 leaked semaphore objects to clean up at
# shutdown", the signature of workers being killed under pressure, with partial output on disk. Two concurrent
# inferences at 3 workers each is 6 loader processes on 4 cores on top of the tracers. Default lowered to 2.
INFER_WORKERS = os.environ.get("HERCULES_INFER_WORKERS", "2")


def infer_cmd(render, ckpt, out_tif, tta=None, window="centre"):
    """The fixed 5.1 call minus --gpus (no GPU on this box); --tta-mirror only when tta (default: module flag TTA).
    `window` appends the R-DEPTH layer arguments; it costs nothing at render time, only a different slice window."""
    tta = TTA if tta is None else tta
    return ([sys.executable, "-m", "vesuvius.ink_detection.inference.infer", render, ckpt, out_tif,
             "--direction", "both"] + (["--tta-mirror"] if tta else []) + list(DEPTH_WINDOWS[window]["layers"])
            + ["--batch-size", "4", "--no-compile", "--num-workers", INFER_WORKERS])


def read_cmd(render, fwd, rev, um, out, key, ledger, note=""):
    return ([sys.executable, READ_CHART, render, fwd, rev, "--um", repr(um), "--out", out, "--key", key, "--ledger", ledger]
            + (["--note", note] if note else []))


def read_dir(patch, tag):
    """Tag-specific read dir: read_<tag> with '+' -> '_' (one dir per checkpoint+TTA variant)."""
    return os.path.join(patch, READ_DIR + "_" + tag.replace("+", "_"))


def map_paths(patch, tag):
    out = os.path.join(read_dir(patch, tag), tag.replace("+", "_") + ".tif")
    return out, out[:-4] + "_reverse.tif"


def dir_bytes(path):
    return sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(path) for f in fs) if os.path.isdir(path) else 0


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd, log):
    with open(log, "a") as fh:
        fh.write("# %s %s\n" % (now(), " ".join(cmd))); fh.flush()
        return subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=ROOT).returncode


# One 9 um inference at a time across the scroll read loops (4 cores). HERCULES_INFER_LOCK overrides the path so a
# test run never waits behind a production inference holding the real lock.
INFER_LOCK = os.environ.get("HERCULES_INFER_LOCK") or os.path.join(DATA_ROOT, "logs", "infer.lock")
# A GLOBAL cap on concurrent 9 um inferences, on top of whichever named lock the caller chose.
# Seven different scripts pass seven different HERCULES_INFER_LOCK paths, so the named locks never serialised them
# against each other and up to eight inferences could share four cores. On 2026-09-19 two reverse passes stopped
# early under that load; one of them manufactured an ADMITTED verdict before it was caught. Unwritten reverse pixels
# read as zero, which INFLATES the rule 5.5 margin, so this failure pushes toward false positives. The cap is an
# engineering limit on this box, not a scientific threshold: it changes no bar, no level and no verdict.
INFER_SLOTS = max(1, int(os.environ.get("HERCULES_INFER_SLOTS", "2")))
SLOT_DIR = os.path.join(DATA_ROOT, "logs", "infer_slots")


def acquire_slot(poll=5.0):
    """Block until one of INFER_SLOTS global inference slots is free; returns the open file holding it."""
    import fcntl
    os.makedirs(SLOT_DIR, exist_ok=True)
    while True:
        for i in range(INFER_SLOTS):
            fh = open(os.path.join(SLOT_DIR, "slot%d" % i), "w")
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return fh
            except OSError:
                fh.close()
        time.sleep(poll)


def drop_render_markers(patch, render):
    """Both completion markers of a deleted render: ours and the one vc_tools.sh / fetch_surface_volumes.py write."""
    for m in (os.path.join(patch, M_RENDER), render + ".complete"):
        if os.path.exists(m):
            os.remove(m)


def stage(patch, marker, cmd, log, lock=None):
    """Run cmd unless the marker exists; on success write the marker. Returns (skipped, seconds, ok).
    With lock=<path> the command runs under an exclusive flock (the inference stage: two concurrent CPU inferences
    oversubscribe the 4 cores and take longer together than one after the other)."""
    m = os.path.join(patch, marker)
    if os.path.exists(m):
        return True, 0.0, True
    t = time.time()
    if lock:
        import fcntl, signal
        os.makedirs(os.path.dirname(lock), exist_ok=True)
        slot = acquire_slot()
        with open(lock, "w") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX); t = time.time()
            # background CPU jobs listed in logs/yield_pids (one pid per line, e.g. the 2 um calibration) are stopped
            # while an inference runs and continued afterwards: they fill the gaps between reads instead of competing
            yp = os.path.join(os.path.dirname(lock), "yield_pids"); pids = []
            if os.path.exists(yp):
                pids = [int(x) for x in open(yp).read().split() if x.isdigit()]
                for pid in pids:
                    try: os.kill(pid, signal.SIGSTOP)
                    except ProcessLookupError: pass
            try:
                rc = run(cmd, log)
            finally:
                for pid in pids:
                    try: os.kill(pid, signal.SIGCONT)
                    except ProcessLookupError: pass
                slot.close()
    else:
        rc = run(cmd, log)
    if rc == 0:
        open(m, "w").write(now() + "\n")
    return False, time.time() - t, rc == 0


def crest_precheck(render, um):
    """RULES R-CREST before any inference: per-slice on-sheet mean of the render and read_chart.crest_check.
    Returns (crest dict, profile, onsheet_cm2). A flat profile means the surface is not centred on a sheet: the patch is
    VOID and the 5.1 call (the expensive step) is skipped."""
    arr = read_chart.open_render(render)
    onsheet = np.asarray(arr[arr.shape[0] // 2]) > 0
    profile, _ = read_chart.slice_profile(arr, onsheet)
    return read_chart.crest_check(profile), profile, rule55.px_to_cm2(int(onsheet.sum()), um)


def write_void(read_out, key, um, render, profile, cc, onsheet_cm2, ledger, note=""):
    """Stats, ledger line and marker for a VOID render (no maps exist: rule 5.5 never ran)."""
    os.makedirs(read_out, exist_ok=True)
    stats = dict(key=key, date=datetime.date.today().isoformat(), um_per_px=um, maps_only=False,
                 inputs=dict(render=render, forward=None, reverse=None), n_slices=len(profile),
                 onsheet_cm2=round(onsheet_cm2, 4), slice_mean_profile=profile, crest_slice=cc["crest_slice"],
                 crest_check=cc, verdict="VOID", verdict_reason=cc["reason"] + "; inference skipped (R-CREST pre-check)")
    if note:
        stats["provenance_note"] = note.strip()
    try:                                                                  # keep a picture of what was rendered (1:3, raw)
        import cv2
        arr = read_chart.open_render(render); mid = np.asarray(arr[arr.shape[0] // 2])[::3, ::3]
        cv2.imwrite(os.path.join(read_out, "void_render_mid_slice_1to3.png"), mid)
    except Exception as exc:  # pragma: no cover - best effort
        stats["mid_slice_png_error"] = str(exc)
    json.dump(stats, open(os.path.join(read_out, read_chart.STATS), "w"), indent=1)
    line = "| %s | %s | - | - | - | - | - | - | VOID | R-CREST pre-check: crest ratio %.2f, crest slice %d; no inference%s |" % (
        stats["date"], read_chart.escape_key(key), cc["ratio"], cc["crest_slice"], note or "")
    read_chart.append_ledger(ledger, line)
    open(os.path.join(read_out, read_chart.MARKER), "w").write("VOID\n")
    return stats


def process_patch(patch, info, ckpt, tag, ledger, records, delete_renders=False, cache=None, window="centre"):
    """QC -> mask check -> render -> inference -> read for one patch dir. Returns a status string."""
    dtag = dir_tag(tag, window)
    key, log = ledger_key(info["scroll"], patch, tag, window), os.path.join(patch, "run_patch_dir.log")
    read_out = read_dir(patch, dtag)
    if os.path.exists(os.path.join(read_out, read_chart.MARKER)) or read_chart.ledger_has_key(ledger, key):
        return "skip: already read / ledgered (%s)" % key
    others = [d for d in glob.glob(os.path.join(patch, READ_DIR + "_*", read_chart.MARKER)) if os.path.dirname(d) != read_out]
    if others and not REREAD:   # a patch read under another checkpoint/TTA tag is not read again by the screening loop
        return "skip: already read under %s" % os.path.basename(os.path.dirname(others[0]))
    cache = cache or os.path.join(DATA_ROOT, "ct_l4_cache", info["scroll"])
    overlay = os.path.join(patch, "qc_overlay_l4.png")
    # QC is always invoked: patch_qc.py is idempotent (cached_covers) and a .qc_done left by a geometry-only run
    # (no --ct-url) must be re-run with the CT-mask check before anything is rendered. It writes .qc_done = verdict.
    t = time.time(); rc = run(qc_cmd(patch, info["um"], info["ct_url"], cache, overlay), log); t_qc = time.time() - t
    if rc != 0 or not os.path.exists(os.path.join(patch, M_QC)):
        return "ERROR: qc failed rc=%s (see %s)" % (rc, log)
    verdict = open(os.path.join(patch, M_QC)).read().strip()
    qc_note = ""
    if verdict == "UNREADABLE" and os.path.exists(os.path.join(patch, "render_source.json")):
        # UNREADABLE means only the 5.8 CT-mask proxy: 100 points sampled on the level-4 mask (138 um voxels at 8.64 um)
        # came back more than half zero. Where the team published their own render of this surface, that render IS the
        # ground truth of what lies inside the volume, and rule 5.5 then requires >= 90 % on-sheet pixels per 0.5 cm2
        # unit before any unit counts. The proxy is superseded, so the read proceeds and the fraction is recorded.
        # RULES: "QC CT-mask proxy on published renders". No verdict rule is relaxed by this.
        try:
            zf = json.load(open(os.path.join(patch, "qc.json")))["ct"]["zero_frac"]
        except Exception:
            zf = None
        qc_note = " (qc CT-mask proxy %s overridden: the team's published render defines the volume, rule 5.5 gates coverage)" % (
            "zero_frac %.2f" % zf if zf is not None else "UNREADABLE")
        verdict = "PASS"
    if verdict == "PASS" and not qc_note:
        # RULES "QC CT-mask bar: an in-mask AREA arm": patch_qc records which arm admitted the patch. A read admitted by
        # the in-mask area arm carries that on its ledger line, so the corpus can be re-partitioned by arm later.
        try:
            ct = json.load(open(os.path.join(patch, "qc.json"))).get("ct") or {}
        except Exception:
            ct = {}
        if ct.get("arm") == "in_mask_area":
            qc_note = " (qc in-mask area arm: zero_frac %.2f over the 0.50 bar, in-mask area %.2f cm2 >= 1.5)" % (
                ct.get("zero_frac", float("nan")), ct.get("in_mask_cm2", float("nan")))
    # RULES R-SMALL: a patch grown at a budget other than the standard 60 generations says so on its ledger line, so
    # the corpus can be split by growth budget without relying on which directory it happens to sit in.
    try:
        mg = json.load(open(os.path.join(patch, "meta.json"))).get("max_gen")
    except Exception:
        mg = None
    if mg is not None and int(mg) != 60:
        qc_note += " (RULES R-SMALL: grown at %d generations, not the standard 60)" % int(mg)
    if verdict != "PASS":
        return "stop: qc %s" % verdict                                   # FAIL = geometry, UNREADABLE = outside the masked CT
    render = os.path.join(patch, RENDER)
    # A render is the largest thing this pipeline writes (up to ~900 MB for a 24 cm2 surface) and several loops can
    # reach this point at once. Starting one on a nearly full disk is how the whole box wedges, so the floor is checked
    # here rather than left to the disk guard to clean up afterwards; the loop simply comes back on its next pass.
    if not os.path.isdir(render):
        # the floor is about the filesystem the render will be WRITTEN to, so measure that one, not DATA_ROOT
        st = os.statvfs(patch); free_gb = st.f_bavail * st.f_frsize / 1e9
        if free_gb < MIN_FREE_RENDER_GB:
            return "stop: %.1f GB free is below the %.1f GB render floor; not starting a render" % (free_gb, MIN_FREE_RENDER_GB)
    # --delete-renders removes the stack but not the completion markers, so a second read of the same patch (a re-read,
    # or the R-CREST-POWER pass) would skip the render stage and then find nothing to read. There are TWO markers: ours
    # (.render_complete) and vc_tools.sh's own (render.zarr.complete, also written by fetch_surface_volumes.py for a
    # published render). A marker without its render is stale and both have to go, or vc_tools reports "complete" and
    # renders nothing.
    if not os.path.isdir(render):
        if os.path.exists(os.path.join(patch, "render_source.json")):
            return ("stop: published render deleted; re-fetch it (fetch_surface_volumes.py) rather than rendering it "
                    "ourselves, so the ledger line keeps the team's provenance")
        for m in (os.path.join(patch, M_RENDER), render + ".complete"):
            if os.path.exists(m):
                os.remove(m)
    _, t_render, ok = stage(patch, M_RENDER, render_cmd(info, patch, render), log)
    if not ok:
        return "ERROR: render failed (see %s)" % log
    render_mb = dir_bytes(render) / 1e6
    fwd, rev = map_paths(patch, dtag)
    os.makedirs(read_out, exist_ok=True)
    cc, profile, on_cm2 = crest_precheck(render, info["um"])
    if not cc["passed"] and IGNORE_CREST:
        # RULES R-CREST-POWER: the crest veto is disabled for this read, under its own tag and ledger key, to measure
        # whether R-CREST discards readable canvas on volumes whose wraps show no papyrus-to-gap density contrast.
        # Nothing else is relaxed: same checkpoint, same plain call, both orders, same rule 5.5 thresholds.
        qc_note += " (R-CREST-POWER: crest veto off for this read; render crest ratio %.2f, crest slice %s)" % (
            cc["ratio"], cc["crest_slice"])
    elif not cc["passed"]:                                                # RULES R-CREST: VOID before the 5.1 call
        write_void(read_out, key, info["um"], render, profile, cc, on_cm2, ledger, qc_note)
        if delete_renders and os.path.isdir(render):
            shutil.rmtree(render); drop_render_markers(patch, render)
        rec = dict(time=now(), scroll=info["scroll"], patch=os.path.basename(patch), key=key, verdict="VOID",
                   cm2_read=0.0, charts=0, render_mb=round(render_mb, 2), s_qc=round(t_qc, 1), s_render=round(t_render, 1),
                   s_infer=0.0, s_read=0.0, crest_ratio=cc["ratio"], render_deleted=bool(delete_renders))
        os.makedirs(os.path.dirname(records), exist_ok=True)
        with open(records, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        return "VOID: %s (no inference)" % cc["reason"]
    _, t_infer, ok = stage(patch, M_INFER % dtag, infer_cmd(render, ckpt, fwd, window=window), log, lock=INFER_LOCK)
    if not ok:
        return "ERROR: inference failed (see %s)" % log
    t = time.time(); rc = run(read_cmd(render, fwd, rev, info["um"], read_out, key, ledger, qc_note), log); t_read = time.time() - t
    stats_path = os.path.join(read_out, read_chart.STATS)
    stats = json.load(open(stats_path)) if os.path.exists(stats_path) else {}
    # read_chart exits non-zero for UNREADABLE assertions but has still written stats, marker and ledger line:
    # completion is judged by those, not by the exit code.
    if not stats or "verdict" not in stats or not os.path.exists(os.path.join(read_out, read_chart.MARKER)):
        return "ERROR: read failed rc=%s (see %s)" % (rc, log)
    if delete_renders and os.path.isdir(render):
        shutil.rmtree(render); drop_render_markers(patch, render)
    rec = dict(time=now(), scroll=info["scroll"], patch=os.path.basename(patch), key=key,
               verdict=stats.get("verdict"), cm2_read=stats.get("onsheet_cm2"), charts=1, render_mb=round(render_mb, 2),
               s_qc=round(t_qc, 1), s_render=round(t_render, 1), s_infer=round(t_infer, 1), s_read=round(t_read, 1),
               mb_per_s=round(render_mb / t_render, 3) if t_render > 0 else None, render_deleted=bool(delete_renders))
    os.makedirs(os.path.dirname(records), exist_ok=True)
    with open(records, "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    return "done: %s %s cm^2" % (stats.get("verdict"), stats.get("onsheet_cm2"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("patches_dir"); ap.add_argument("--scroll", required=True); ap.add_argument("--vol", required=True)
    ap.add_argument("--ckpt", default=CKPT); ap.add_argument("--tag", default=TAG, help="checkpoint+TTA label used in markers and ledger keys")
    ap.add_argument("--delete-renders", action="store_true"); ap.add_argument("--only", nargs="*", help="patch names to process")
    ap.add_argument("--no-tta", action="store_true", help="plain inference (no --tta-mirror); pair with a '+plain' tag")
    ap.add_argument("--reread", action="store_true", help="read a patch again under this tag even if another tag's read exists")
    ap.add_argument("--depth-window", choices=tuple(DEPTH_WINDOWS), default="centre",
                    help="RULES R-DEPTH window over the 28-slice render: centre (6..22, offset 0, the historical "
                         "default), low (0..16, offset -6) or high (11..27, offset +5, ADMITTED 2026-09-19). The "
                         "layer arguments and the ledger depth-offset field come from one table and cannot disagree.")
    ap.add_argument("--ignore-crest", action="store_true",
                    help="RULES R-CREST-POWER: do not veto a read on a failing render crest; the ratio is still recorded "
                         "and the ledger note says the veto was off. Pair with a distinct '+nocrest' tag.")
    ap.add_argument("--data-root", default=DATA_ROOT); ap.add_argument("--catalogue", default=CATALOGUE)
    ap.add_argument("--ledger", default=os.path.join(ROOT, "LEDGER.md")); ap.add_argument("--records", default=os.path.join(ROOT, "records", "throughput.jsonl"))
    a = ap.parse_args(argv)
    global TTA, REREAD, IGNORE_CREST
    TTA, REREAD, IGNORE_CREST = (not a.no_tta), a.reread, a.ignore_crest
    info = volume_info(a.scroll, a.vol, a.catalogue, cache_dir=os.path.join(a.data_root, "vc_cache", a.scroll))
    print("%s %s: %s um/px (catalogue %s), pitch %s" % (a.scroll, a.vol, info["um"], info["catalogue_um"], info["pitch"]))
    # auto_grown_* = a surface we traced; team_* = a surface published by the team and fetched with
    # scripts/fetch_team_segments.py (source.json records its bucket key). Both are read the same way.
    # auto_trace_* is what vc_grow_seg_from_segments (stage 2) names its consensus result; auto_grown_* is the
    # smaller companion it writes beside it. Enumerating only auto_grown_/team_ SILENTLY SKIPPED every consensus
    # surface, including the 4.077 cm2 one that met G-GP part 4's milestone 2 -- the run printed its header and
    # exited with nothing to do.
    dirs = sorted(d.path for d in os.scandir(a.patches_dir)
                  if d.is_dir() and (d.name.startswith("auto_grown_") or d.name.startswith("auto_trace_")
                                     or d.name.startswith("team_")))
    # a patch whose render is already on disk (our earlier render, or a surface volume the team published and
    # fetch_surface_volumes.py dropped in) is read first: it costs only inference, while the rest cost a render too
    dirs.sort(key=lambda d: (0 if os.path.exists(os.path.join(d, RENDER + ".complete")) else 1, d))
    if a.only:
        # A --only that names nothing must FAIL, not quietly read zero patches. That is how the milestone-2
        # consensus surface looked "read" for half an hour while the process had already exited.
        want = set(a.only)
        dirs = [d for d in dirs if os.path.basename(d) in want]
        missing = sorted(want - {os.path.basename(d) for d in dirs})
        if missing:
            sys.exit("--only names %d patch(es) not present in %s: %s" % (len(missing), a.patches_dir, ", ".join(missing)))
    for d in dirs:
        print("%s: %s" % (os.path.basename(d), process_patch(d, info, a.ckpt, a.tag, a.ledger, a.records, a.delete_renders,
                                                        os.path.join(a.data_root, "ct_l4_cache", a.scroll),
                                                        window=a.depth_window)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
