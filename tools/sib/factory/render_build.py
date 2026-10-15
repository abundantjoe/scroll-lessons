# Provenance: Project HERCULES | owner the owner | [id removed]
"""Render (official vc_render_tifxyz) + build the package image. Shared by the factory and reproduce.sh.

render(volume_url, mesh_dir, workdir, voxel_um) -> (raw uint8 H x W, command, utc start, utc end)
  Streams remote zarr chunks from the official bucket; never downloads a volume. One surface slice
  (-n 1, no normal offset), scale 1, group 0, level-0 zarr output without compression or pyramid.
fetch_metadata(volume_url, dst) -> sha256   (anonymous S3; the volume's own metadata.json)
voxel_um_from_metadata(path) -> float       (scan.tomo.acquisition.detector.samplePixelSize mm x 1000)"""
import datetime
import hashlib
import json
import os
import re
import subprocess

import numpy as np

VC = os.environ.get("HRC_VC_WRAPPER", "/work/bin/vc")
BUCKET = "vesuvius-challenge-open-data"
FORBIDDEN_SCROLLS = ("PHerc0841",)  # task rule: no render of PHerc0841 by this factory
URL_RE = re.compile(r"^s3://vesuvius-challenge-open-data/(PHerc[0-9A-Za-z]+)/volumes/([0-9]{14})-[^/]+\.zarr/$")


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_volume_url(url: str):
    m = URL_RE.match(url)
    if not m:
        raise ValueError(f"not an official volume URL: {url!r}")
    return m.group(1), m.group(2)


def fetch_metadata(volume_url: str, dst: str) -> str:
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    parse_volume_url(volume_url)
    key = volume_url[len(f"s3://{BUCKET}/"):] + "metadata.json"
    boto3.client("s3", config=Config(signature_version=UNSIGNED)).download_file(BUCKET, key, dst)
    return hashlib.sha256(open(dst, "rb").read()).hexdigest()


def voxel_um_from_metadata(path: str) -> float:
    md = json.load(open(path))
    mm = float(md["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"])
    return round(mm * 1000.0, 6)


def render_command(volume_url: str, mesh_dir: str, out_zarr: str, voxel_um: float):
    return [VC, "vc_render_tifxyz", "-v", volume_url, "--remote-url", volume_url, "--segmentation", mesh_dir,
            "--scale", "1", "--group-idx", "0", "--num-slices", "1", "--voxel-size", f"{voxel_um:g}",
            "--voxel-unit", "micrometer", "--cache-gb", "2", "--zarr-compressor", "none", "--pyramid", "0",
            "--zarr-output", out_zarr]


def render(volume_url: str, mesh_dir: str, workdir: str, voxel_um: float, log_path: str | None = None):
    scroll, _ = parse_volume_url(volume_url)
    if scroll in FORBIDDEN_SCROLLS:
        raise PermissionError(f"{scroll} may not be rendered by the factory")
    os.makedirs(workdir, exist_ok=True)
    out = os.path.join(os.path.abspath(workdir), "render.zarr")
    if os.path.exists(out):
        raise FileExistsError(out)
    cmd = render_command(volume_url, os.path.abspath(mesh_dir), out, voxel_um)
    t0 = utc()
    with open(log_path or os.path.join(workdir, "render.log"), "w") as fh:
        subprocess.run(cmd, check=True, stdout=fh, stderr=subprocess.STDOUT, cwd=workdir)
    t1 = utc()
    import zarr
    z = zarr.open(os.path.join(out, "0"), mode="r")
    a = np.asarray(z[:])
    if a.ndim == 3:
        if a.shape[0] != 1:
            raise ValueError(f"expected one slice, got {a.shape}")
        a = a[0]
    if a.dtype != np.uint8:
        raise ValueError(f"render dtype {a.dtype} is not uint8")
    return np.ascontiguousarray(a), cmd, t0, t1
