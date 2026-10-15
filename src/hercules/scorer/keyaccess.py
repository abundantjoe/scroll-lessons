# Provenance: Project HERCULES | owner the owner | [id removed]
"""Scorer-only seal key access with an append-only read log.

The seal identity lives outside the repository (default /srv/scorer/seal.agekey,
mode 0400). Every decryption goes through `decrypt_logged`, which appends a line to
logs/key_reads.tsv (utc from `date -u`, caller purpose, seal path, seal sha256)
BEFORE decrypting. Agents never call this; only deterministic scorer runs do.
"""
import hashlib
import os
import subprocess

from .seal import keygen, seal_decrypt

KEY_PATH = os.environ.get("HERCULES_SEAL_KEY", "/srv/scorer/seal.agekey")
PUB_PATH = KEY_PATH + ".pub"


def _repo_root():
    return subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                          text=True, check=True).stdout.strip()


def _utc():
    return subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True,
                          text=True, check=True).stdout.strip()


def ensure_key():
    """Create the scorer identity once; return the public recipient string."""
    if not os.path.exists(KEY_PATH):
        os.makedirs(os.path.dirname(KEY_PATH), mode=0o700, exist_ok=True)
        pub = keygen(KEY_PATH)
        with open(PUB_PATH, "w", encoding="ascii") as fh:
            fh.write(pub + "\n")
    with open(PUB_PATH, encoding="ascii") as fh:
        return fh.read().strip()


def decrypt_logged(seal_path, purpose, log_path=None):
    log_path = log_path or os.path.join(_repo_root(), "logs", "key_reads.tsv")
    with open(seal_path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    new = not os.path.exists(log_path)
    with open(log_path, "a", encoding="utf-8") as fh:
        if new:
            fh.write("utc\tpurpose\tseal_path\tseal_sha256\n")
        fh.write(f"{_utc()}\t{purpose}\t{seal_path}\t{digest}\n")
    return seal_decrypt(seal_path, KEY_PATH)


def decrypt_answer_logged(answer_path, purpose, log_path=None):
    """Decrypt an agent's sealed answer (plain JSON, not canonical) with the same
    append-before-decrypt logging as decrypt_logged."""
    import json as _json
    log_path = log_path or os.path.join(_repo_root(), "logs", "key_reads.tsv")
    with open(answer_path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    new = not os.path.exists(log_path)
    with open(log_path, "a", encoding="utf-8") as fh:
        if new:
            fh.write("utc\tpurpose\tseal_path\tseal_sha256\n")
        fh.write(f"{_utc()}\t{purpose}\t{answer_path}\t{digest}\n")
    out = subprocess.run(["age", "-d", "-i", KEY_PATH, answer_path], capture_output=True, check=True)
    return _json.loads(out.stdout.decode("utf-8"))
