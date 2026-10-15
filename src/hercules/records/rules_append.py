"""Append-only, hash-chained RULES.md log.

Provenance: Project HERCULES | owner the owner | [id removed]

File layout: a preamble (everything before the first entry), then entries.
Every entry starts at a line beginning with ``## `` and runs through the byte
before the next such line (the last entry runs to end of file):

    ## <ID>
    - utc: <output of `date -u +%Y-%m-%dT%H:%M:%SZ`>
    - prev_sha256: <sha256 of the previous entry's exact bytes; for the first
                    entry, sha256 of the preamble>
    - kind: <declaration|result|correction|conflict|decision|metric-hash>
    <body, verbatim>

The tool appends one newline if the body does not end with one, then one
blank separator line; both belong to the entry's bytes. IDs are unique, match
``[A-Za-z0-9][A-Za-z0-9._-]{0,127}``, and no body line may start with ``## ``.
Bodies must be UTF-8, non-blank, and free of Unicode Cf characters.

CLI (default file: RULES.md at the git top level of the cwd):
    python -m hercules.records.rules_append append --id ID --kind KIND --body-file PATH|-
    python -m hercules.records.rules_append verify
    python -m hercules.records.rules_append last
    python -m hercules.records.rules_append init
Each subcommand accepts ``--file PATH``. ``append`` creates the file with the
standard preamble when it is missing or empty, and refuses to write when the
existing file fails ``verify``. Appends hold an exclusive flock on the file.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from hercules.records.cf_scan import describe, iter_cf

PROVENANCE = "Provenance: Project HERCULES | owner the owner | [id removed]"
KINDS = ("declaration", "result", "correction", "conflict", "decision", "metric-hash")
DATE_CMD = ("date", "-u", "+%Y-%m-%dT%H:%M:%SZ")
HEADER_PREFIX = b"## "

ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
UTC_RE = re.compile(
    r"\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])T([01]\d|2[0-3]):[0-5]\d:([0-5]\d|60)Z"
)
HEADER_RE = re.compile(rb"## (.*)")
UTC_LINE_RE = re.compile(rb"- utc: (.*)")
PREV_LINE_RE = re.compile(rb"- prev_sha256: ([0-9a-f]{64})")
KIND_LINE_RE = re.compile(rb"- kind: (.*)")

PREAMBLE = f"""# RULES.md (append-only)
{PROVENANCE}

This file is an append-only, hash-chained log. Lines are never removed or
edited; a mistake is fixed by appending a `correction` entry. Entries are
written only with `python -m hercules.records.rules_append append`.
Each entry is a `## <ID>` header line, then `- utc:` (from `date -u`),
`- prev_sha256:` (sha256 of the previous entry's exact bytes, from its
header line through the byte before the next header; the first entry uses
the sha256 of this preamble, i.e. every byte before the first entry) and
`- kind:` (declaration, result, correction, conflict, decision or
metric-hash), then the body verbatim. Check the whole chain with
`python -m hercules.records.rules_append verify`.

""".encode("utf-8")


class RulesError(Exception):
    """Invalid input or a RULES.md that fails verification."""


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Entry:
    id: str
    utc: str
    prev_sha256: str
    kind: str
    body: bytes
    raw: bytes
    line: int

    @property
    def sha256(self) -> str:
        return sha256_hex(self.raw)


@dataclass
class VerifyResult:
    ok: bool
    preamble_sha256: str
    entries: list[Entry] = field(default_factory=list)
    error: str | None = None
    line: int | None = None

    @property
    def last_id(self) -> str | None:
        return self.entries[-1].id if self.entries else None

    @property
    def last_sha256(self) -> str:
        return self.entries[-1].sha256 if self.entries else self.preamble_sha256


def split_segments(data: bytes) -> tuple[bytes, list[tuple[int, bytes]]]:
    """Split file bytes into (preamble, [(line_number, raw_entry_bytes), ...])."""
    starts = [0] if data.startswith(HEADER_PREFIX) else []
    starts += [m.start() + 1 for m in re.finditer(rb"\n## ", data)]
    preamble = data[: starts[0]] if starts else data
    segments = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(data)
        segments.append((data.count(b"\n", 0, start) + 1, data[start:end]))
    return preamble, segments


def _text_problem(chunk: bytes, first_line: int) -> str | None:
    try:
        text = chunk.decode("utf-8")
    except UnicodeDecodeError as exc:
        return f"invalid UTF-8 at byte {exc.start} of this segment"
    for ln, col, ch in iter_cf(text):
        return f"invisible character {describe(ch)} at line {first_line + ln - 1}, col {col}"
    return None


def parse_entry(raw: bytes, line: int) -> Entry:
    lines = raw.split(b"\n")
    if not raw.endswith(b"\n") or len(lines) < 5:
        raise RulesError("entry must have header, utc, prev_sha256 and kind lines and end "
                         "with a newline")
    m = HEADER_RE.fullmatch(lines[0])
    entry_id = m.group(1).decode("utf-8", "replace") if m else ""
    if not ID_RE.fullmatch(entry_id):
        raise RulesError(f"bad header line {lines[0]!r}")
    m = UTC_LINE_RE.fullmatch(lines[1])
    if not m or not UTC_RE.fullmatch(m.group(1).decode("ascii", "replace")):
        raise RulesError(f"bad utc line {lines[1]!r}")
    utc = m.group(1).decode("ascii")
    m = PREV_LINE_RE.fullmatch(lines[2])
    if not m:
        raise RulesError(f"bad prev_sha256 line {lines[2]!r}")
    prev = m.group(1).decode("ascii")
    m = KIND_LINE_RE.fullmatch(lines[3])
    kind = m.group(1).decode("utf-8", "replace") if m else ""
    if kind not in KINDS:
        raise RulesError(f"bad kind line {lines[3]!r}")
    body = b"\n".join(lines[4:])
    return Entry(entry_id, utc, prev, kind, body, raw, line)


def verify_bytes(data: bytes) -> VerifyResult:
    """Recompute the whole chain; report the first break."""
    preamble, segments = split_segments(data)
    result = VerifyResult(ok=False, preamble_sha256=sha256_hex(preamble))
    problem = _text_problem(preamble, 1)
    if problem:
        result.error, result.line = f"preamble: {problem}", 1
        return result
    if segments == [] and data and not data.endswith(b"\n"):
        result.error, result.line = "file does not end with a newline", data.count(b"\n") + 1
        return result
    expected_prev = result.preamble_sha256
    prev_label = "the preamble"
    seen: dict[str, int] = {}
    for idx, (line, raw) in enumerate(segments, 1):
        where = f"entry #{idx} at line {line}"
        problem = _text_problem(raw, line)
        if problem:
            result.error, result.line = f"{where}: {problem}", line
            return result
        try:
            entry = parse_entry(raw, line)
        except RulesError as exc:
            result.error, result.line = f"{where}: {exc}", line
            return result
        where = f"entry #{idx} {entry.id!r} at line {line}"
        if entry.id in seen:
            result.error = f"{where}: duplicate ID (first used at line {seen[entry.id]})"
            result.line = line
            return result
        if entry.prev_sha256 != expected_prev:
            result.error = (
                f"{where}: chain broken: prev_sha256 is {entry.prev_sha256} but sha256 of "
                f"{prev_label} is {expected_prev} (earlier content was modified, removed, "
                "inserted or reordered)"
            )
            result.line = line
            return result
        seen[entry.id] = line
        result.entries.append(entry)
        expected_prev = entry.sha256
        prev_label = f"entry #{idx} {entry.id!r}"
    result.ok = True
    return result


def verify_file(path: Path) -> VerifyResult:
    return verify_bytes(Path(path).read_bytes())


def utc_now() -> str:
    """UTC timestamp from the system `date -u` command (never Python's clock)."""
    proc = subprocess.run(list(DATE_CMD), capture_output=True, text=True, check=True)
    value = proc.stdout.strip()
    if not UTC_RE.fullmatch(value):
        raise RulesError(f"unexpected output from {' '.join(DATE_CMD)!r}: {value!r}")
    return value


def check_body(body: bytes) -> None:
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RulesError(f"body is not valid UTF-8 (byte {exc.start})") from None
    if not text.strip():
        raise RulesError("body is empty")
    for n, line in enumerate(body.split(b"\n"), 1):
        if line.startswith(HEADER_PREFIX):
            raise RulesError(f"body line {n} starts with '## ', which is reserved for entry "
                             "headers")
    for ln, col, ch in iter_cf(text):
        raise RulesError(f"body contains invisible character {describe(ch)} at line {ln}, "
                         f"col {col}")


def format_entry(entry_id: str, utc: str, prev_sha256: str, kind: str, body: bytes) -> bytes:
    if not body.endswith(b"\n"):
        body += b"\n"
    head = f"## {entry_id}\n- utc: {utc}\n- prev_sha256: {prev_sha256}\n- kind: {kind}\n"
    return head.encode("utf-8") + body + b"\n"


def _validate_request(entry_id: str, kind: str, body: bytes) -> None:
    if not ID_RE.fullmatch(entry_id):
        raise RulesError(f"invalid ID {entry_id!r}: must match {ID_RE.pattern}")
    if kind not in KINDS:
        raise RulesError(f"invalid kind {kind!r}: choose from {', '.join(KINDS)}")
    check_body(body)


def append_entry(path: Path | str, entry_id: str, kind: str, body: bytes) -> Entry:
    """Verify the existing file, then append one entry under an exclusive lock."""
    _validate_request(entry_id, kind, body)
    path = Path(path)
    with open(path, "a+b") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.seek(0)
            data = fh.read()
            prefix = b""
            if not data:
                prefix = PREAMBLE
                data = PREAMBLE
            state = verify_bytes(data)
            if not state.ok:
                raise RulesError(f"refusing to write: {path} fails verify: {state.error}")
            if any(e.id == entry_id for e in state.entries):
                raise RulesError(f"duplicate ID {entry_id!r}: already present in {path}")
            raw = format_entry(entry_id, utc_now(), state.last_sha256, kind, body)
            fh.write(prefix + raw)
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    line = data.count(b"\n") + 1
    return parse_entry(raw, line)


def init_file(path: Path | str) -> bool:
    """Create the file with the standard preamble if missing or empty. True if written."""
    path = Path(path)
    with open(path, "a+b") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.seek(0)
            if fh.read(1):
                return False
            fh.write(PREAMBLE)
            fh.flush()
            os.fsync(fh.fileno())
            return True
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def default_rules_path() -> Path:
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                             text=True, check=True).stdout.strip()
        if top:
            return Path(top) / "RULES.md"
    except (OSError, subprocess.CalledProcessError):
        pass
    return Path.cwd() / "RULES.md"


def _read_body(spec: str) -> bytes:
    if spec == "-":
        return sys.stdin.buffer.read()
    return Path(spec).read_bytes()


def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--file", type=Path, default=None,
                        help="RULES.md path (default: <git top level>/RULES.md)")
    ap = argparse.ArgumentParser(prog="python -m hercules.records.rules_append",
                                 description="Append-only, hash-chained RULES.md log.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_app = sub.add_parser("append", parents=[common], help="append one entry")
    p_app.add_argument("--id", required=True, dest="entry_id")
    p_app.add_argument("--kind", required=True, choices=KINDS)
    p_app.add_argument("--body-file", required=True, help="body file, or '-' for stdin")
    sub.add_parser("verify", parents=[common], help="recompute the whole chain")
    sub.add_parser("last", parents=[common], help="print last entry ID and its sha256")
    sub.add_parser("init", parents=[common], help="create the file with its preamble")
    args = ap.parse_args(argv)
    path = args.file or default_rules_path()

    try:
        if args.cmd == "init":
            written = init_file(path)
            print(f"{'created' if written else 'exists, unchanged'}: {path}")
            return 0
        if args.cmd == "append":
            entry = append_entry(path, args.entry_id, args.kind, _read_body(args.body_file))
            print(f"appended {entry.id} kind={entry.kind} utc={entry.utc} "
                  f"sha256={entry.sha256} line={entry.line}")
            return 0
        if not path.exists():
            print(f"error: {path} does not exist", file=sys.stderr)
            return 2
        state = verify_file(path)
        if not state.ok:
            print(f"FAIL {path}: {state.error}", file=sys.stderr)
            return 1
        if args.cmd == "verify":
            print(f"OK {path}: {len(state.entries)} entries; preamble sha256 "
                  f"{state.preamble_sha256}; last {state.last_id or '(none)'} "
                  f"sha256 {state.last_sha256}")
            return 0
        print(f"{state.last_id or '(preamble)'} {state.last_sha256}")
        return 0
    except RulesError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
