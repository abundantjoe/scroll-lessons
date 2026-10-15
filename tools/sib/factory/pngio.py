# Provenance: Project HERCULES | owner the owner | [id removed]
"""Canonical, implementation-independent PNG and TIFF byte encoders plus strict parsers.

PNG (canonical form, the only form the factory writes and the verifier accepts):
  signature, IHDR (8-bit greyscale, colour type 0, no interlace), exactly one IDAT, IEND; nothing else.
  IDAT = zlib stream (CMF 0x78, FLG 0x01) of STORED deflate blocks of at most 65535 bytes, every scanline
  with filter byte 0; adler32 trailer. Because no compressor is involved, the bytes depend only on the
  pixels: the same pixels give the same file on any machine and any zlib build.
TIFF (tifxyz coordinate band, official C++ layout): little-endian, one strip, uncompressed float32, exactly
  the ten structural tags the official meshes carry (no Software, DateTime, resolution or description tags).
Pure Python + numpy; no PIL, no zlib compressor."""
import struct
import zlib

import numpy as np

PNG_SIG = b"\x89PNG\r\n\x1a\n"
ALLOWED_PNG_CHUNKS = (b"IHDR", b"IDAT", b"IEND")
MAX_STORED = 65535
TIFF_TAGS_ALLOWED = {256: "ImageWidth", 257: "ImageLength", 258: "BitsPerSample", 259: "Compression",
                     262: "PhotometricInterpretation", 273: "StripOffsets", 277: "SamplesPerPixel",
                     278: "RowsPerStrip", 279: "StripByteCounts", 339: "SampleFormat"}


def _chunk(ctype: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + ctype + data + struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)


def _stored_zlib(raw: bytes) -> bytes:
    out = bytearray(b"\x78\x01")
    n = len(raw)
    pos = 0
    while True:
        blk = raw[pos:pos + MAX_STORED]
        pos += len(blk)
        final = 1 if pos >= n else 0
        out += bytes([final]) + struct.pack("<HH", len(blk), len(blk) ^ 0xFFFF) + blk
        if final:
            break
    out += struct.pack(">I", zlib.adler32(raw) & 0xFFFFFFFF)
    return bytes(out)


def encode_png_gray8(img: np.ndarray) -> bytes:
    img = np.ascontiguousarray(img)
    if img.dtype != np.uint8 or img.ndim != 2 or min(img.shape) < 1:
        raise ValueError("canonical PNG needs a non-empty 2-D uint8 array")
    h, w = img.shape
    raw = np.zeros((h, w + 1), np.uint8)
    raw[:, 1:] = img  # filter byte 0 on every row
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0)
    return PNG_SIG + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", _stored_zlib(raw.tobytes())) + _chunk(b"IEND", b"")


class PngError(ValueError):
    pass


def parse_png_chunks(data: bytes):
    """Return [(type, offset, length, crc_ok)] and trailing-byte count; raises PngError on structure errors."""
    if not data.startswith(PNG_SIG):
        raise PngError("not a PNG (bad signature)")
    pos, chunks = len(PNG_SIG), []
    while True:
        if pos + 12 > len(data):
            raise PngError("truncated before IEND")
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        if pos + 12 + length > len(data):
            raise PngError(f"chunk {ctype!r} overruns the file")
        body = data[pos + 8:pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        chunks.append((ctype, pos, length, crc == (zlib.crc32(ctype + body) & 0xFFFFFFFF)))
        pos += 12 + length
        if ctype == b"IEND":
            break
    return chunks, len(data) - pos


def decode_canonical_png(data: bytes) -> np.ndarray:
    """Strictly decode a canonical PNG; any deviation from the canonical form raises PngError."""
    chunks, trailing = parse_png_chunks(data)
    types = [c[0] for c in chunks]
    bad = [t for t in types if t not in ALLOWED_PNG_CHUNKS]
    if bad:
        raise PngError(f"non-whitelisted chunk(s): {sorted(set(t.decode('latin-1') for t in bad))}")
    if types != [b"IHDR", b"IDAT", b"IEND"]:
        raise PngError(f"chunk sequence {[t.decode('latin-1') for t in types]} != IHDR, IDAT, IEND")
    if trailing:
        raise PngError(f"{trailing} byte(s) after IEND")
    if not all(c[3] for c in chunks):
        raise PngError("CRC mismatch")
    _, off, ln, _ = chunks[0]
    w, h, bd, ct, cm, fm, il = struct.unpack(">IIBBBBB", data[off + 8:off + 8 + ln])
    if (bd, ct, cm, fm, il) != (8, 0, 0, 0, 0):
        raise PngError(f"IHDR not 8-bit greyscale non-interlaced: {(bd, ct, cm, fm, il)}")
    _, off, ln, _ = chunks[1]
    raw = zlib.decompress(data[off + 8:off + 8 + ln])
    if len(raw) != h * (w + 1):
        raise PngError("IDAT size mismatch")
    a = np.frombuffer(raw, np.uint8).reshape(h, w + 1)
    if a[:, 0].any():
        raise PngError("non-zero scanline filter (not canonical)")
    img = a[:, 1:].copy()
    if encode_png_gray8(img) != data:
        raise PngError("bytes differ from the canonical re-encoding")
    return img


def encode_tiff_f32(band: np.ndarray) -> bytes:
    band = np.ascontiguousarray(band, dtype="<f4")
    h, w = band.shape
    pix = band.tobytes()
    tags = [(256, 3, 1, w), (257, 3, 1, h), (258, 3, 1, 32), (259, 3, 1, 1), (262, 3, 1, 1),
            (273, 4, 1, 8), (277, 3, 1, 1), (278, 3, 1, h), (279, 4, 1, len(pix)), (339, 3, 1, 3)]
    ifd_off = 8 + len(pix)
    ifd_off += ifd_off % 2  # word alignment
    out = bytearray(b"II*\x00" + struct.pack("<I", ifd_off)) + pix
    out += b"\x00" * (ifd_off - len(out))
    out += struct.pack("<H", len(tags))
    for tag, typ, cnt, val in tags:
        out += struct.pack("<HHI", tag, typ, cnt) + (struct.pack("<HH", val, 0) if typ == 3 else struct.pack("<I", val))
    out += struct.pack("<I", 0)
    return bytes(out)


def tiff_tags(data: bytes) -> dict:
    """{tag: (type, count, value_or_offset)} of every IFD; raises ValueError on a malformed/big-endian file."""
    if data[:4] != b"II*\x00":
        raise ValueError("not a little-endian classic TIFF")
    (off,) = struct.unpack("<I", data[4:8])
    tags, n_ifd = {}, 0
    while off:
        n_ifd += 1
        if n_ifd > 1:
            raise ValueError("more than one IFD")
        (n,) = struct.unpack("<H", data[off:off + 2])
        for i in range(n):
            tag, typ, cnt, val = struct.unpack("<HHII", data[off + 2 + 12 * i:off + 14 + 12 * i])
            tags[tag] = (typ, cnt, val & 0xFFFF if typ == 3 else val)
        (off,) = struct.unpack("<I", data[off + 2 + 12 * n:off + 6 + 12 * n])
    return tags
