"""CLI over a folder of tifxyz meshes (synthetic spiral sheet, with an umbilicus file)."""
import json

import numpy as np

from handcheck import cli
from handcheck import synth as S
from handcheck.tifxyz import TifxyzMesh, write_tifxyz


def _write(tmp_path, pts, name):
    m = TifxyzMesh(points=pts.astype(np.float32), scale=(1.0, 1.0), uuid=name)
    return write_tifxyz(tmp_path / "meshes" / f"{name}.tifxyz", m)


def _setup(tmp_path, reverse_cols=False):
    sp = S.Spiral(centre=(70.0, 70.0), r_outer=62.0, pitch=9.0, turns=4.5, phi_start=np.radians(-20.0), w=1)
    pts = S.spiral_sheet_grid(sp, 1, (40, 40), 1.5, 0.0, s0=-30.0, z0=25.0, phi_ref=np.radians(35.0))
    if reverse_cols:
        pts = np.ascontiguousarray(pts[:, ::-1])
    _write(tmp_path, pts, "a")
    umb = tmp_path / "umb.json"
    umb.write_text(json.dumps({"control_points": [{"x": 70.0, "y": 70.0, "z": z} for z in (0.0, 50.0, 110.0)]}))
    return umb


def _run(tmp_path, capsys, *extra):
    rc = cli.main([str(tmp_path / "meshes"), *extra, "--out", str(tmp_path / "o.json")])
    rows = json.loads((tmp_path / "o.json").read_text())
    return rc, rows


def test_cli_native_grid_reads_as_stored(tmp_path, capsys):
    umb = _setup(tmp_path)
    rc, rows = _run(tmp_path, capsys, "--left-handed", "false", "--top-to-bottom", "true", "--umbilicus", str(umb))
    assert rc == 0 and len(rows) == 1
    r = rows[0]
    assert r["state"] == "OK" and r["mirror_u"] is False and r["flip_v"] is False
    assert "frame not checked" in r["flags"]


def test_cli_reversed_columns_need_mirror(tmp_path, capsys):
    umb = _setup(tmp_path, reverse_cols=True)
    rc, rows = _run(tmp_path, capsys, "--left-handed", "false", "--top-to-bottom", "true", "--umbilicus", str(umb))
    assert rows[0]["state"] == "OK" and rows[0]["mirror_u"] is True


def test_cli_left_handed_frame_flips_the_decision(tmp_path, capsys):
    umb = _setup(tmp_path)
    rc, rows = _run(tmp_path, capsys, "--left-handed", "true", "--top-to-bottom", "true", "--umbilicus", str(umb))
    assert rows[0]["convention_sign"] == -1 and rows[0]["mirror_u"] is True


def test_cli_unknown_parity_is_flagged(tmp_path, capsys):
    umb = _setup(tmp_path)
    rc, rows = _run(tmp_path, capsys, "--left-handed", "unknown", "--umbilicus", str(umb))
    assert rows[0]["state"] == "PARITY_UNKNOWN" and rows[0]["mirror_u"] is None


def test_cli_unknown_updown_keeps_mirror_decision(tmp_path, capsys):
    umb = _setup(tmp_path)
    rc, rows = _run(tmp_path, capsys, "--left-handed", "false", "--umbilicus", str(umb))
    assert rows[0]["flip_v"] is None and rows[0]["rot180_equivalent"] is True


def test_cli_empty_folder(tmp_path):
    (tmp_path / "meshes").mkdir()
    assert cli.main([str(tmp_path / "meshes"), "--left-handed", "false"]) == 2
