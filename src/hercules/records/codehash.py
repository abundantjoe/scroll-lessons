"""sha256 of code files plus one combined hash, for metric-code declarations.

Provenance: Project HERCULES | owner the owner | [id removed]

CLI:  python -m hercules.records.codehash [--root DIR] <files...>

Prints one ``<sha256>  <path>`` line per file (sorted by path), then
``combined_sha256 <hex>``. The combined hash is the sha256 of the UTF-8
concatenation of ``"<path>\\t<sha256>\\n"`` lines sorted by path (Unicode
codepoint order). Paths are POSIX paths relative to ``--root`` (default: the
git top level of the cwd, else the cwd), so the combined hash does not depend
on where the command is run from; files outside the root keep their absolute
path. Only regular files are accepted: list a directory's files explicitly
(e.g. ``git ls-files src/hercules/scorer``) so the hashed set is unambiguous.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from typing import Iterable

CHUNK = 1 << 20


def file_sha256(path: str | os.PathLike) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def combined_sha256(pairs: Iterable[tuple[str, str]]) -> str:
    """sha256 over sorted "path\\tsha256\\n" lines."""
    text = "".join(f"{path}\t{digest}\n" for path, digest in sorted(pairs))
    return hashlib.sha256(text.encode("utf-8", "surrogateescape")).hexdigest()


def default_root() -> str:
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                             text=True, check=True).stdout.strip()
        if top:
            return top
    except (OSError, subprocess.CalledProcessError):
        pass
    return os.getcwd()


def display_path(path: str, root: str) -> str:
    absolute = os.path.abspath(path)
    root = os.path.abspath(root)
    if os.path.commonpath([absolute, root]) == root:
        return os.path.relpath(absolute, root).replace(os.sep, "/")
    return absolute


def hash_paths(paths: Iterable[str], root: str | None = None) -> tuple[list[tuple[str, str]], str]:
    """Return ([(display_path, sha256), ...] sorted by path, combined_sha256)."""
    root = root or default_root()
    table: dict[str, str] = {}
    for path in paths:
        if not os.path.isfile(path):
            raise ValueError(f"not a regular file: {path}")
        shown = display_path(path, root)
        if "\t" in shown or "\n" in shown:
            raise ValueError(f"path contains a tab or newline: {shown!r}")
        table[shown] = file_sha256(path)
    if not table:
        raise ValueError("no files given")
    pairs = sorted(table.items())
    return pairs, combined_sha256(pairs)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m hercules.records.codehash",
                                 description="Per-file and combined sha256 of code files.")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--root", default=None,
                    help="base for displayed paths (default: git top level, else cwd)")
    args = ap.parse_args(argv)
    try:
        pairs, combined = hash_paths(args.paths, args.root)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for path, digest in pairs:
        print(f"{digest}  {path}")
    print(f"combined_sha256 {combined}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
