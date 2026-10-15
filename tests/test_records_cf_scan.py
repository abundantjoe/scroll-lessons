"""Tests for hercules.records.cf_scan (invisible Unicode and image metadata).

Provenance: Project HERCULES | owner the owner | [id removed]
"""

from __future__ import annotations

import io
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import pytest
from PIL import Image, TiffImagePlugin
from PIL.PngImagePlugin import PngInfo

from hercules.records import cf_scan

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
CF_CHARS = ["\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00ad", "\U000e0041"]


def run_cli(*args: str):
    env = dict(os.environ, PYTHONPATH=str(SRC))
    return subprocess.run([sys.executable, "-m", "hercules.records.cf_scan", *args],
                          capture_output=True, env=env)


def image_bytes(fmt: str, **kw) -> bytes:
    buf = io.BytesIO()
    Image.new("L", (8, 8), 100).save(buf, fmt, **kw)
    return buf.getvalue()


@pytest.mark.parametrize("ch", CF_CHARS)
def test_cf_in_content(tmp_path, ch):
    assert unicodedata.category(ch) == "Cf"
    p = tmp_path / "notes.md"
    p.write_text(f"clean line\nabc{ch}def\n", encoding="utf-8")
    findings = cf_scan.scan_file(str(p))
    assert len(findings) == 1
    f = findings[0]
    assert (f.kind, f.line, f.col, f.codepoint) == ("cf-content", 2, 4, ord(ch))
    assert f"U+{ord(ch):04X}" in f.format()


@pytest.mark.parametrize("ch", ["\u200b", "\u2060", "\ufeff"])
def test_cf_in_filename(tmp_path, ch):
    p = tmp_path / f"re{ch}port.txt"
    p.write_text("all clean\n")
    findings = cf_scan.scan_file(str(p))
    assert [f.kind for f in findings] == ["cf-path"]
    assert findings[0].codepoint == ord(ch)
    assert ch not in findings[0].format()  # rendered escaped, never raw
    assert f"<U+{ord(ch):04X}>" in findings[0].format()


def test_clean_text_passes(tmp_path):
    p = tmp_path / "clean.md"
    p.write_text("ASCII\nGreek \u03bb\u03cc\u03b3\u03bf\u03c2, accents \u00e9\u00fc, "
                 "nbsp\u00a0ok, emoji \U0001f4dc, CJK \u6f22\n", encoding="utf-8")
    assert cf_scan.scan_file(str(p)) == []


def test_bom_at_start_flagged(tmp_path):
    p = tmp_path / "bom.py"
    p.write_bytes(b"\xef\xbb\xbfprint(1)\n")
    [f] = cf_scan.scan_file(str(p))
    assert (f.line, f.col, f.codepoint) == (1, 1, 0xFEFF)


def test_invalid_utf8_does_not_hide_cf(tmp_path):
    p = tmp_path / "mixed.txt"
    p.write_bytes(b"bad byte \xff here\nzero" + "\u200b".encode() + b"width\n")
    [f] = cf_scan.scan_file(str(p))
    assert (f.line, f.codepoint) == (2, 0x200B)


def test_utf8_text_with_nul_is_still_scanned(tmp_path):
    p = tmp_path / "nul.txt"
    p.write_bytes(b"a\x00b" + "\u2060".encode())
    assert [f.codepoint for f in cf_scan.scan_file(str(p))] == [0x2060]


def test_binary_non_image_scans_name_only(tmp_path):
    payload = b"\x00\xff\xfe" + "\u200b".encode() + bytes(range(256))
    clean = tmp_path / "blob.bin"
    clean.write_bytes(payload)
    assert cf_scan.scan_file(str(clean)) == []
    named = tmp_path / "blob\u200b.bin"
    named.write_bytes(payload)
    assert [f.kind for f in cf_scan.scan_file(str(named))] == ["cf-path"]


def test_png_with_text_chunk_flagged(tmp_path):
    info = PngInfo()
    info.add_text("Comment", "made by someone")
    p = tmp_path / "fig.png"
    p.write_bytes(image_bytes("PNG", pnginfo=info))
    [f] = cf_scan.scan_file(str(p))
    assert f.kind == "image-meta" and "tEXt" in f.message and "Comment" in f.message


def test_png_without_metadata_passes(tmp_path):
    p = tmp_path / "fig.png"
    p.write_bytes(image_bytes("PNG"))
    assert cf_scan.scan_file(str(p)) == []


def test_png_other_metadata_chunks_flagged():
    info = PngInfo()
    info.add_itxt("Author", "x")
    info.add_text("Big", "y" * 200, zip=True)
    exif = Image.Exif()
    exif[0x010F] = "Camera"
    msgs = [f.message for f in cf_scan.scan_content("a.png", image_bytes("PNG", pnginfo=info))]
    assert any("iTXt" in m for m in msgs) and any("zTXt" in m for m in msgs)
    msgs = [f.message for f in cf_scan.scan_content("b.png", image_bytes("PNG", exif=exif))]
    assert any("eXIf" in m for m in msgs)


def test_png_detected_by_magic_not_extension(tmp_path):
    info = PngInfo()
    info.add_text("k", "v")
    p = tmp_path / "innocent.txt"
    p.write_bytes(image_bytes("PNG", pnginfo=info))
    assert [f.kind for f in cf_scan.scan_file(str(p))] == ["image-meta"]


def test_truncated_png_reported():
    [f] = cf_scan.scan_content("t.png", image_bytes("PNG")[:40])
    assert f.kind == "image-error"


def test_jpeg_exif():
    exif = Image.Exif()
    exif[0x010F] = "Camera"
    [f] = cf_scan.scan_content("a.jpg", image_bytes("JPEG", exif=exif))
    assert f.kind == "image-meta" and "EXIF" in f.message
    assert cf_scan.scan_content("b.jpg", image_bytes("JPEG")) == []


def test_tiff_exif():
    assert cf_scan.scan_content("plain.tif", image_bytes("TIFF")) == []
    exif = Image.Exif()
    exif[0x010F] = "Camera"
    [f] = cf_scan.scan_content("make.tif", image_bytes("TIFF", exif=exif))
    assert "Make" in f.message
    ifd = TiffImagePlugin.ImageFileDirectory_v2()
    ifd[0x8825] = {1: "N"}
    [f] = cf_scan.scan_content("gps.tif", image_bytes("TIFF", tiffinfo=ifd))
    assert "GPS IFD" in f.message


def test_cli_exit_codes_and_output(tmp_path):
    clean = tmp_path / "clean.txt"
    clean.write_text("hello\n")
    assert run_cli(str(clean)).returncode == 0

    d = tmp_path / "tree" / "sub"
    d.mkdir(parents=True)
    (d / "a.md").write_text("x\n\ny\u200bz\n", encoding="utf-8")
    (d / "b\u2060.txt").write_text("fine\n")
    (tmp_path / "tree" / ".git").mkdir()
    (tmp_path / "tree" / ".git" / "skip\u200b").write_text("ignored\n")
    proc = run_cli(str(tmp_path / "tree"))
    assert proc.returncode == 1
    out = proc.stdout.decode("utf-8")
    assert re.search(r"a\.md:3:2: U\+200B ZERO WIDTH SPACE", out)
    assert "b<U+2060>.txt" in out and "WORD JOINER" in out
    assert "skip" not in out
    assert not any(unicodedata.category(c) == "Cf" for c in out)

    assert run_cli(str(tmp_path / "missing")).returncode == 2
