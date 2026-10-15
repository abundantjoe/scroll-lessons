# Provenance: Project HERCULES | owner the owner | [id removed]
"""Wiring: no image reaches a reader unless it is certified.

* ``certify_window``: binds the sha256 of every display image built from one render
  record to that record's PASSED pre-read gate report (preread.preread_gate);
* ``certify_controls``: binds control images (canaries, baits, mirror canaries) to
  their builder keys (controls.write_controls);
* ``assert_images_certified``: called by the harness before any reader job is made
  (the one-line hook in hercules.harness.jobs.make); raises TribunalFault for any image
  without a certificate, with a failed gate, or whose bytes changed since certification.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from . import TRIBUNAL_VERSION
from .preread import TribunalFault


def _sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _report_sha(report: Mapping) -> str:
    return hashlib.sha256(json.dumps(report, sort_keys=True, default=float).encode()).hexdigest()


def certify_window(report: Mapping, image_paths: Sequence[str | Path], cert_dir: str | Path) -> Path:
    """Write a window certificate; refuses (TribunalFault) if the gate did not pass."""
    if not report.get("passed"):
        raise TribunalFault(f"cannot certify images of {report.get('window_id')}: gate failed {report.get('failed')}")
    cert = {"tribunal_version": TRIBUNAL_VERSION, "kind": "window", "window_id": report.get("window_id"),
            "gate_report_sha256": _report_sha(report), "gate_passed": True,
            "images": sorted(_sha(p) for p in image_paths)}
    return _write(cert, cert_dir)


def certify_controls(control_keys: Iterable[Mapping], image_dir: str | Path, cert_dir: str | Path) -> Path:
    imgs = []
    for k in control_keys:
        p = Path(image_dir) / k["image"]["name"]
        if _sha(p) != k["image"]["sha256"]:
            raise TribunalFault(f"control image {p.name} changed since it was built")
        imgs.append(k["image"]["sha256"])
    cert = {"tribunal_version": TRIBUNAL_VERSION, "kind": "controls", "images": sorted(imgs)}
    return _write(cert, cert_dir)


def _write(cert: dict, cert_dir: str | Path) -> Path:
    d = Path(cert_dir)
    d.mkdir(parents=True, exist_ok=True)
    body = json.dumps(cert, sort_keys=True, indent=1)
    p = d / f"{hashlib.sha256(body.encode()).hexdigest()[:32]}.json"
    p.write_text(body + "\n", encoding="utf-8")
    return p


def certified_hashes(cert_dir: str | Path) -> set[str]:
    out: set[str] = set()
    d = Path(cert_dir)
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.json")):
        c = json.loads(p.read_text(encoding="utf-8"))
        if c.get("kind") == "controls" or (c.get("kind") == "window" and c.get("gate_passed") is True):
            out.update(c.get("images", []))
    return out


def assert_images_certified(images: Sequence[str | Path], cert_dir: str | Path) -> None:
    """Raise TribunalFault unless every image's CURRENT bytes are certified."""
    ok = certified_hashes(cert_dir)
    missing = [str(p) for p in images if _sha(p) not in ok]
    if missing:
        raise TribunalFault(f"{len(missing)} image(s) lack a TRIBUNAL certificate: {missing[:3]}")
