"""Tests for scripts/sweep_renders.py. Run: python -m pytest scripts/tests/test_sweep_renders.py -q"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import sweep_renders as sw  # noqa: E402


def age(p, seconds):
    import time
    t = time.time() - seconds
    for dp, _, fs in os.walk(p):
        os.utime(dp, (t, t))
        for f in fs:
            os.utime(os.path.join(dp, f), (t, t))


def make(root, name, reads):
    """reads: {read_dir_name: finished?}"""
    p = os.path.join(root, "PHerc0826", name)
    os.makedirs(os.path.join(p, "render.zarr", "0"), exist_ok=True)
    open(os.path.join(p, "render.zarr", "0", "0"), "wb").write(b"\0" * 1024)
    open(os.path.join(p, ".render_complete"), "w").write("x")
    open(os.path.join(p, "render.zarr.complete"), "w").write("x")
    for r, done in reads.items():
        os.makedirs(os.path.join(p, r), exist_ok=True)
        if done:
            open(os.path.join(p, r, ".read_complete"), "w").write("x")
    return p


def test_sweeps_only_what_no_read_needs(tmp_path):
    root = str(tmp_path)
    finished = make(root, "auto_grown_done", {"read_a": True, "read_b": True})
    inflight = make(root, "auto_grown_inflight", {"read_a": True, "read_b": False})
    unread = make(root, "auto_grown_unread", {})
    for p in (finished, inflight, unread):
        age(p, 3600)                                   # old enough that the liveness guard does not hold them
    assert sw.main(["--patches", root]) == 0
    assert not os.path.exists(os.path.join(finished, "render.zarr"))          # every read finished: removable
    assert not os.path.exists(os.path.join(finished, ".render_complete"))     # both markers go with it
    assert not os.path.exists(os.path.join(finished, "render.zarr.complete"))
    assert os.path.isdir(os.path.join(inflight, "render.zarr"))               # a read is still queued against it
    assert os.path.isdir(os.path.join(unread, "render.zarr"))                 # never read: may be about to be


def test_a_render_being_written_is_never_swept(tmp_path):
    """The case that broke PHerc1203: a patch being RE-read has a finished earlier read and a render in progress.
    An unconditional 'all reads done' test called that render removable and deleted it mid-write, three times."""
    root = str(tmp_path)
    p = make(root, "auto_grown_rerender", {"read_a": True})
    age(p, 3600)
    os.remove(os.path.join(p, ".render_complete"))
    os.remove(os.path.join(p, "render.zarr.complete"))     # no marker: the render is being written right now
    sw.main(["--patches", root])
    assert os.path.isdir(os.path.join(p, "render.zarr")), "a render with no completion marker must never be swept"


def test_a_freshly_written_render_is_never_swept(tmp_path):
    root = str(tmp_path)
    p = make(root, "auto_grown_fresh", {"read_a": True})   # markers present but mtime is now
    sw.main(["--patches", root])
    assert os.path.isdir(os.path.join(p, "render.zarr")), "a render touched in the last 10 minutes must be kept"
