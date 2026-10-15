"""Tests for scripts/vc_tools.sh (MASTER_PROMPT_v4 5.7, 5.9, 5.13). Run: python -m pytest scripts/tests/test_vc_tools.py -q
Offline: VC_DRY_RUN=1 makes the script print the exact docker argv (one element per line) and run nothing."""
import json, os, subprocess
import pytest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vc_tools.sh")
IMG = "ghcr.io/scrollprize/villa/volume-cartographer:builder-ubuntu-26.04"
SURF = "20250521133212-surface-20260413222639-surface-m7-L0-th0.2"


def prefix(data_root, threads="2"):
    return ["docker", "run", "--rm", "--network", "host", "-e", "HTTPS_PROXY", "-e", "https_proxy", "-e", "NO_PROXY", "-e", "no_proxy",
            "-e", "SSL_CERT_FILE=/ca.crt", "-e", "CURL_CA_BUNDLE=/ca.crt", "-e", "AWS_CA_BUNDLE=/ca.crt",
            "-e", "AWS_EC2_METADATA_DISABLED=true", "-e", "HOME=/data/vc_home", "-e", "OMP_NUM_THREADS=%s" % threads,
            "-e", "LD_LIBRARY_PATH=/opt/vc/lib", "-v", "/root/.ccr/ca-bundle.crt:/ca.crt:ro", "-v", "%s:/data" % data_root,
            "-v", "%s/vc_install:/opt/vc:ro" % data_root, IMG]


def vc(args, data_root=None, **env):
    e = dict(os.environ, VC_DRY_RUN="1", **env)
    e.pop("HERCULES_DATA", None)            # each test states its data root; the caller's environment never leaks in
    if data_root:
        e["HERCULES_DATA"] = str(data_root)
    r = subprocess.run(["bash", SCRIPT] + args, capture_output=True, text=True, env=e)
    return r.returncode, r.stdout.splitlines(), r.stderr


def test_help_and_bad_args():
    rc, out, _ = vc(["help"]); assert rc == 0 and out[0].startswith("vc_tools.sh --") and any("trace" in l for l in out)
    assert subprocess.run(["bash", SCRIPT, "-h"], capture_output=True).returncode == 0
    rc, _, err = vc(["render", "a", "b"]); assert rc == 1 and "render <scroll>" in err
    rc, _, err = vc(["bogus"]); assert rc == 1 and "unknown subcommand" in err


def test_trace_argv_and_params(tmp_path):
    patches = tmp_path / "patches" / "PHerc0306B"; patches.mkdir(parents=True)
    rc, argv, err = vc(["trace", "PHerc0306B", "20250521133212", "8.64", "1234", "5678", "9012", str(patches)], tmp_path)
    assert rc == 0, err
    assert argv == prefix(tmp_path) + ["/opt/vc/bin/vc_grow_seg_from_seed", "--volume",
        "s3://vesuvius-challenge-open-data/PHerc0306B/representations/predictions/surfaces/%s.zarr/" % SURF,
        "--target-dir", "/data/patches/PHerc0306B", "--params", "/data/patches/PHerc0306B/params.json", "--seed", "1234", "5678", "9012"]
    p = json.load(open(patches / "params.json"))                 # 5.7, verbatim
    assert p == {"mode": "seed", "min_area_cm": 0.2, "generations": 60, "thread_limit": 2, "cache_root": "/data/vc_cache/PHerc0306B",
                 "direction_fields": [], "voxelsize": 8.64, "normal_grid_path": "/data/normal_grids/PHerc0306B"}
    assert isinstance(p["voxelsize"], float) and isinstance(p["generations"], int)
    g = tmp_path / "normal_grids" / "PHerc0306B"
    assert json.load(open(g / "normal-grids-remote.json")) == {"url":
        "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0306B/representations/predictions/surfaces/%s.normal-grids" % SURF}
    assert not (g / "metadata.json").exists()                     # dry run never touches the network
    assert (patches / "logs").is_dir() and (tmp_path / "vc_cache" / "PHerc0306B").is_dir()
    # idempotence: a finished seed is skipped
    (patches / "logs" / "seed_1234_5678_9012.done").write_text("x")
    rc, out, _ = vc(["trace", "PHerc0306B", "20250521133212", "8.64", "1234", "5678", "9012", str(patches)], tmp_path)
    assert rc == 0 and out == ["trace: seed 1234 5678 9012 already done (%s)" % (patches / "logs" / "seed_1234_5678_9012.done")]


def test_render_argv(tmp_path):
    patch = tmp_path / "patches" / "PHerc0306B" / "auto_grown_20260916"; patch.mkdir(parents=True)
    out = patch / "render.zarr"
    rc, argv, err = vc(["render", "PHerc0306B", "20250521133212", "8.640um-1.2m-116keV", "8.64", str(patch), str(out)], tmp_path, VC_THREADS="3")
    assert rc == 0, err
    assert argv == prefix(tmp_path, "3") + ["/opt/vc/bin/vc_render_tifxyz", "--volume", "/data/vc_cache/PHerc0306B", "--remote-url",
        "s3://vesuvius-challenge-open-data/PHerc0306B/volumes/20250521133212-8.640um-1.2m-116keV-masked.zarr/",
        "--segmentation", "/data/patches/PHerc0306B/auto_grown_20260916", "--zarr-output", "/data/patches/PHerc0306B/auto_grown_20260916/render.zarr",
        "--scale", "1", "--group-idx", "0", "--num-slices", "28", "--slice-step", "1", "--cache-gb", "4", "--voxel-size", "8.64",
        "--voxel-unit", "micrometer", "--auto-crop", "--pyramid", "0"]
    assert "--flip-normals" not in argv                           # own patches: orientation unknown, both orders are read
    (tmp_path / "patches" / "PHerc0306B" / "auto_grown_20260916" / "render.zarr.complete").write_text("done")
    rc, out_lines, _ = vc(["render", "PHerc0306B", "20250521133212", "8.640um-1.2m-116keV", "8.64", str(patch), str(out)], tmp_path)
    assert rc == 0 and out_lines == ["render: complete (%s.complete)" % out]


def test_flatten_argv_default_data_root():
    patch, out = "/home/user/hercules_data/controls/w040/mesh", "/home/user/hercules_data/controls/w040/mesh_flat"
    rc, argv, err = vc(["flatten", patch, out])
    assert rc == 0, err
    assert argv == prefix("/home/user/hercules_data") + ["/opt/vc/bin/vc_flatten", "-i", "/data/controls/w040/mesh", "-o", "/data/controls/w040/mesh_flat"]
    assert not os.path.exists(out)


def test_paths_outside_data_root_are_refused(tmp_path):
    rc, _, err = vc(["flatten", "/etc", str(tmp_path / "x")], tmp_path)
    assert rc == 1 and "path not under" in err


@pytest.mark.parametrize("stack,zero", [(None, True), (0, True), (7, False)])
def test_render_is_zero(tmp_path, stack, zero):
    import zarr, numpy as np
    z = tmp_path / "r.zarr"
    if stack is not None:
        g = zarr.open_group(str(z), mode="w", zarr_format=2)
        a = g.create_array("0", shape=(28, 16, 16), chunks=(28, 16, 16), dtype="uint8",
                           chunk_key_encoding={"name": "v2", "separator": "/"}, compressors=None)
        a[:] = stack
    rc = subprocess.run(["bash", "-c", "set -- help; source %s >/dev/null; render_is_zero %s" % (SCRIPT, z)], capture_output=True).returncode
    assert (rc == 0) is zero
