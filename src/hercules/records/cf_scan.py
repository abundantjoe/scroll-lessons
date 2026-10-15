"""Scanner for invisible Unicode (category Cf) characters and image metadata.

Provenance: Project HERCULES | owner the owner | [id removed]

Findings:
  * cf-path     : a Unicode Cf character in a file or directory NAME/path.
  * cf-content  : a Unicode Cf character in a text file (decoded as UTF-8;
                  undecodable bytes are replaced, so one bad byte cannot hide
                  the rest of the file).
  * image-meta  : a PNG tEXt/iTXt/zTXt/eXIf chunk, or EXIF in a JPEG/TIFF.
  * image-error : an image (detected by magic bytes) whose metadata could not
                  be parsed; reported so that it is never silently accepted.

A file is "binary" when it contains a NUL byte AND is not valid UTF-8. Binary
files that are not PNG/JPEG/TIFF images get only their name scanned. Images
are detected by magic bytes, not by extension.

CLI:  python -m hercules.records.cf_scan [--max-bytes N] <paths...>
Directories are walked recursively (``.git`` is skipped). Each finding is
printed as ``path[:line:col]: message``. Exit status: 0 clean, 1 findings,
2 usage or read errors.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import struct
import sys
import unicodedata
from dataclasses import dataclass
from typing import BinaryIO, Iterator

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_METADATA_CHUNKS = (b"tEXt", b"iTXt", b"zTXt", b"eXIf")
TIFF_MAGICS = (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")
# TIFF: EXIF sub-IFD pointers plus the EXIF-defined descriptive IFD0 tags
# (structural tags such as ImageWidth are present in every TIFF and ignored).
TIFF_EXIF_TAGS = {
    0x8769: "Exif IFD", 0x8825: "GPS IFD", 0x010E: "ImageDescription", 0x010F: "Make",
    0x0110: "Model", 0x0131: "Software", 0x0132: "DateTime", 0x013B: "Artist",
    0x013C: "HostComputer", 0x8298: "Copyright",
}
DEFAULT_MAX_BYTES = 64 * 1024 * 1024

_NON_ASCII = re.compile(r"[^\x00-\x7f]")
_ESCAPE_CATEGORIES = ("Cf", "Cc", "Cs", "Co")


@dataclass(frozen=True)
class Finding:
    path: str
    kind: str
    message: str
    line: int | None = None
    col: int | None = None
    codepoint: int | None = None

    def format(self) -> str:
        loc = display(self.path)
        if self.line is not None:
            loc += f":{self.line}:{self.col}"
        return f"{loc}: {self.message}"


def display(text: str) -> str:
    """Render text safely: invisible/control/surrogate chars become <U+XXXX>."""
    out = []
    for ch in text:
        if unicodedata.category(ch) in _ESCAPE_CATEGORIES:
            out.append(f"<U+{ord(ch):04X}>")
        else:
            out.append(ch)
    return "".join(out)


def describe(ch: str) -> str:
    return f"U+{ord(ch):04X} {unicodedata.name(ch, 'UNNAMED')} (Cf)"


def iter_cf(text: str) -> Iterator[tuple[int, int, str]]:
    """Yield (line, col, char) for every Cf character; line and col are 1-based."""
    if text.isascii():  # no ASCII character is in category Cf
        return
    for lineno, line in enumerate(text.split("\n"), 1):
        if line.isascii():
            continue
        for m in _NON_ASCII.finditer(line):
            ch = m.group()
            if unicodedata.category(ch) == "Cf":
                yield lineno, m.start() + 1, ch


def scan_name(path: str, name_part: str | None = None) -> list[Finding]:
    """Scan a path string (or only ``name_part`` of it) for Cf characters."""
    target = path if name_part is None else name_part
    findings = []
    for idx, ch in enumerate(target):
        if unicodedata.category(ch) == "Cf":
            findings.append(
                Finding(path, "cf-path", f"{describe(ch)} in path name (char {idx + 1})",
                        codepoint=ord(ch))
            )
    return findings


def scan_text(path: str, text: str, what: str = "content") -> list[Finding]:
    return [
        Finding(path, "cf-content", f"{describe(ch)} in {what}", line=ln, col=col,
                codepoint=ord(ch))
        for ln, col, ch in iter_cf(text)
    ]


def image_kind(head: bytes) -> str | None:
    if head.startswith(PNG_SIGNATURE):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head[:4] in TIFF_MAGICS:
        return "tiff"
    return None


def scan_png(path: str, fp: BinaryIO) -> list[Finding]:
    """List PNG metadata chunks (tEXt, iTXt, zTXt, eXIf)."""
    findings = []
    fp.seek(len(PNG_SIGNATURE))
    offset = len(PNG_SIGNATURE)
    while True:
        header = fp.read(8)
        if len(header) < 8:
            findings.append(Finding(path, "image-error", "malformed PNG: truncated before IEND"))
            break
        length, ctype = struct.unpack(">I4s", header)
        if ctype in PNG_METADATA_CHUNKS:
            peek = fp.read(min(length, 80))
            detail = ""
            if ctype != b"eXIf":
                keyword = peek.split(b"\x00", 1)[0].decode("latin-1")
                detail = f" keyword={display(keyword)!r}"
            findings.append(
                Finding(path, "image-meta",
                        f"PNG {ctype.decode('ascii')} chunk{detail} at byte {offset} ({length} bytes)")
            )
        fp.seek(offset + 12 + length)
        offset += 12 + length
        if ctype == b"IEND":
            break
    return findings


def scan_exif(path: str, fp: BinaryIO, kind: str) -> list[Finding]:
    """Report EXIF presence in a JPEG or TIFF (via Pillow; pixels are not decoded)."""
    import warnings

    from PIL import Image

    findings = []
    saved_limit = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fp.seek(0)
            with Image.open(fp, formats=["JPEG" if kind == "jpeg" else "TIFF"]) as im:
                if kind == "jpeg":
                    exif = im.getexif()
                    if im.info.get("exif") or len(exif):
                        findings.append(
                            Finding(path, "image-meta", f"JPEG EXIF present ({len(exif)} tags)")
                        )
                else:
                    tags = getattr(im, "tag_v2", {}) or {}
                    hits = [name for tag, name in TIFF_EXIF_TAGS.items() if tag in tags]
                    if hits:
                        findings.append(
                            Finding(path, "image-meta", f"TIFF EXIF present ({', '.join(hits)})")
                        )
    except Exception as exc:  # noqa: BLE001 - any parse failure is a finding
        findings.append(
            Finding(path, "image-error", f"could not parse {kind.upper()} metadata: {exc}")
        )
    finally:
        Image.MAX_IMAGE_PIXELS = saved_limit
    return findings


def scan_image(path: str, fp: BinaryIO, kind: str) -> list[Finding]:
    if kind == "png":
        return scan_png(path, fp)
    return scan_exif(path, fp, kind)


def is_binary(data: bytes) -> bool:
    if b"\x00" not in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def scan_content(path: str, data: bytes) -> list[Finding]:
    """Scan file content only (not the name)."""
    kind = image_kind(data[:8])
    if kind:
        return scan_image(path, io.BytesIO(data), kind)
    if is_binary(data):
        return []
    return scan_text(path, data.decode("utf-8", errors="replace"))


def scan_bytes(path: str, data: bytes) -> list[Finding]:
    """Scan a path string plus its content (e.g. a staged git blob)."""
    return scan_name(path) + scan_content(path, data)


def scan_file(path: str, max_bytes: int = DEFAULT_MAX_BYTES,
              name_part: str | None = None) -> list[Finding]:
    findings = scan_name(path, name_part)
    if os.path.islink(path):
        return findings + scan_text(path, os.readlink(path), what="symlink target")
    size = os.path.getsize(path)
    with open(path, "rb") as fp:
        kind = image_kind(fp.read(8))
        if kind:
            return findings + scan_image(path, fp, kind)
        if size > max_bytes:
            print(f"cf_scan: warning: {display(path)}: {size} bytes > --max-bytes; "
                  "content not scanned", file=sys.stderr)
            return findings
        fp.seek(0)
        data = fp.read()
    return findings + scan_content(path, data)


def iter_targets(root: str) -> Iterator[tuple[str, str | None, bool]]:
    """Yield (path, name_part, is_dir) for root and, if a directory, everything below it."""
    if not os.path.isdir(root) or os.path.islink(root):
        yield root, None, False
        return
    yield root, None, True
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        for d in dirnames:
            yield os.path.join(dirpath, d), d, True
        for f in sorted(filenames):
            yield os.path.join(dirpath, f), f, False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m hercules.records.cf_scan",
        description="Reject invisible Unicode (Cf) in text/paths and metadata in images.",
    )
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES,
                    help="do not read content of non-image files larger than this")
    args = ap.parse_args(argv)

    findings: list[Finding] = []
    errors = 0
    files = 0
    for top in args.paths:
        if not os.path.lexists(top):
            print(f"cf_scan: error: {display(top)}: no such file or directory", file=sys.stderr)
            errors += 1
            continue
        for path, name_part, is_dir in iter_targets(top):
            try:
                if is_dir:
                    findings.extend(scan_name(path, name_part))
                else:
                    files += 1
                    findings.extend(scan_file(path, args.max_bytes, name_part))
            except OSError as exc:
                print(f"cf_scan: error: {display(path)}: {exc}", file=sys.stderr)
                errors += 1
    for f in findings:
        print(f.format())
    print(f"cf_scan: {len(findings)} finding(s), {files} file(s) scanned, {errors} error(s)",
          file=sys.stderr)
    if errors:
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
