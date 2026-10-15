# Provenance: Project HERCULES | owner the owner | [id removed]
"""Spec J: sealing (age encryption) of canonical JSON objects.

* ``keygen(path)``: ``age-keygen -o path``, chmod 0400, returns the public key.
* ``seal_encrypt(obj, recipient_pubkey, out_path)``: canonical JSON (sorted keys, UTF-8,
  no Cf characters) encrypted with ``age -r``; returns sha256 of the ciphertext file.
* ``seal_decrypt(path, identity_file)``: ``age -d -i``; returns the decoded object.

Neither function ever overwrites an existing file.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from .canon import canonical_bytes, canonical_json, contains_forbidden, sha256_hex

AGE_BIN = "age"  # resolved on PATH (installed at /usr/bin/age)
AGE_KEYGEN_BIN = "age-keygen"
# Native age X25519 recipients only: "age1" + 58 bech32 characters.
AGE_RECIPIENT_RE = re.compile(r"^age1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{58}$")
IDENTITY_FILE_MODE = 0o400  # spec J: identity files are read-only for the owner
# Choice: refuse to overwrite an existing seal or key (a seal must never be silently replaced).
SEAL_OVERWRITE = False
# Choice: binary (not ASCII-armoured) ciphertext.
AGE_ARMOR = False
# Choice: decrypted plaintext must re-serialise byte-identically (detects foreign files).
SEAL_REQUIRE_CANONICAL = True


def _run(args: list[str], stdin: bytes | None = None) -> subprocess.CompletedProcess:
    proc = subprocess.run(args, input=stdin, capture_output=True, check=False)
    if proc.returncode != 0:
        msg = proc.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"{args[0]} failed (exit {proc.returncode}): {msg}")
    return proc


def _check_recipient(pubkey: str) -> None:
    if not isinstance(pubkey, str) or not AGE_RECIPIENT_RE.match(pubkey):
        raise ValueError("recipient must be an age X25519 public key (age1...)")


def keygen(path: str | os.PathLike) -> str:
    """Generate an age identity at ``path`` (must not exist), chmod 0400, return its public key."""
    path = Path(path)
    if path.exists() and not SEAL_OVERWRITE:
        raise FileExistsError(str(path))
    _run([AGE_KEYGEN_BIN, "-o", str(path)])
    os.chmod(path, IDENTITY_FILE_MODE)
    pub = _run([AGE_KEYGEN_BIN, "-y", str(path)]).stdout.decode("ascii").strip()
    _check_recipient(pub)
    return pub


def seal_encrypt(obj: Any, recipient_pubkey: str, out_path: str | os.PathLike) -> str:
    """Encrypt canonical JSON of ``obj`` to ``recipient_pubkey``; return sha256 hex of the file."""
    _check_recipient(recipient_pubkey)
    plaintext = canonical_bytes(obj)  # raises ValueError on Cf characters / NaN
    out_path = Path(out_path)
    if out_path.exists() and not SEAL_OVERWRITE:
        raise FileExistsError(str(out_path))
    args = [AGE_BIN, "-r", recipient_pubkey] + (["-a"] if AGE_ARMOR else [])
    ciphertext = _run(args, stdin=plaintext).stdout
    with open(out_path, "xb") as fh:  # exclusive create: never overwrite
        fh.write(ciphertext)
    return sha256_hex(out_path.read_bytes())


def seal_decrypt(path: str | os.PathLike, identity_file: str | os.PathLike) -> Any:
    """Decrypt a seal with ``age -d -i identity_file`` and return the JSON object."""
    data = _run([AGE_BIN, "-d", "-i", str(identity_file), str(path)]).stdout
    text = data.decode("utf-8")
    if contains_forbidden(text):
        raise ValueError("sealed plaintext contains a format (Cf) character")
    obj = json.loads(text)
    if SEAL_REQUIRE_CANONICAL and canonical_json(obj) != text:
        raise ValueError("sealed plaintext is not canonical JSON")
    return obj
