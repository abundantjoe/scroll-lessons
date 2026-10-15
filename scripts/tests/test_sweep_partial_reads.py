import os, sys, time, tempfile, numpy as np, tifffile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import sweep_partial_reads as S


def mk(root, scroll, patch, read, tifs=1, complete=False, age_h=0.0):
    d = os.path.join(root, scroll, patch, read)
    os.makedirs(d, exist_ok=True)
    for i in range(tifs):
        tifffile.imwrite(os.path.join(d, "m%d.tif" % i), np.zeros((4, 4), np.uint8))
    if complete:
        open(os.path.join(d, ".read_complete"), "w").close()
    t = time.time() - age_h * 3600
    for p in [d] + [os.path.join(d, f) for f in os.listdir(d)]:
        os.utime(p, (t, t))
    return d


def test_a_finished_read_is_never_touched_however_old():
    r = tempfile.mkdtemp(); mk(r, "S", "P", "read_x", complete=True, age_h=999)
    assert S.partial_reads(r) == []


def test_a_live_read_is_never_touched_however_slow():
    r = tempfile.mkdtemp(); mk(r, "S", "P", "read_x", age_h=1.9)   # longest observed single-direction write
    assert S.partial_reads(r) == []


def test_a_killed_reads_leftover_is_found():
    r = tempfile.mkdtemp(); d = mk(r, "S", "P", "read_x", age_h=19.2)  # the real PHerc1447 case
    rows = S.partial_reads(r)
    assert len(rows) == 1 and rows[0]["dir"].rstrip("/") == d.rstrip("/")


def test_an_empty_read_directory_is_left_alone():
    r = tempfile.mkdtemp(); mk(r, "S", "P", "read_x", tifs=0, age_h=99)
    assert S.partial_reads(r) == []


def test_the_age_bar_is_well_clear_of_the_longest_observed_write():
    assert S.MIN_AGE_H == 6.0
    r = tempfile.mkdtemp(); mk(r, "S", "P", "read_x", age_h=5.9)
    assert S.partial_reads(r) == []
    r2 = tempfile.mkdtemp(); mk(r2, "S", "P", "read_x", age_h=6.1)
    assert len(S.partial_reads(r2)) == 1


def test_dry_run_is_the_default_and_deletes_nothing():
    r = tempfile.mkdtemp(); d = mk(r, "S", "P", "read_x", age_h=19)
    S.main(["--root", r])
    assert os.path.isdir(d)
    S.main(["--root", r, "--go"])
    assert not os.path.isdir(d)
