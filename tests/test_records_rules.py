"""Tests for hercules.records.rules_append (append-only hash-chained RULES.md).

Provenance: Project HERCULES | owner the owner | [id removed]
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from hercules.records import rules_append as ra

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def run_cli(*args: str, stdin: bytes | None = None, cwd: Path | None = None):
    env = dict(os.environ, PYTHONPATH=str(SRC))
    return subprocess.run([sys.executable, "-m", "hercules.records.rules_append", *args],
                          input=stdin, capture_output=True, env=env, cwd=cwd)


@pytest.fixture
def fake_date(monkeypatch):
    """Replace only the `date -u` subprocess call; record every call made."""
    calls: list[list[str]] = []
    real_run = subprocess.run

    def fake_run(args, *a, **kw):
        if list(args[:1]) == ["date"]:
            calls.append(list(args))
            out = f"2026-09-24T12:00:{len(calls):02d}Z\n"
            return subprocess.CompletedProcess(args, 0, stdout=out, stderr="")
        return real_run(args, *a, **kw)

    monkeypatch.setattr(ra.subprocess, "run", fake_run)
    return calls


def make_log(path: Path, n: int = 3) -> list[ra.Entry]:
    kinds = ["declaration", "result", "decision", "metric-hash", "correction", "conflict"]
    return [
        ra.append_entry(path, f"R-{i:04d}", kinds[i % len(kinds)],
                        f"Body of entry {i}.\n\n- item a\n- item b\n".encode())
        for i in range(1, n + 1)
    ]


# ---------------------------------------------------------------- round trip

def test_append_verify_round_trip(tmp_path):
    path = tmp_path / "RULES.md"
    entries = make_log(path, 4)
    data = path.read_bytes()
    assert data.startswith(b"# RULES.md (append-only)\n")
    assert ra.PROVENANCE.encode() in data.split(b"\n")[1]
    state = ra.verify_bytes(data)
    assert state.ok, state.error
    assert [e.id for e in state.entries] == ["R-0001", "R-0002", "R-0003", "R-0004"]
    preamble = data[: data.index(b"\n## ") + 1]
    assert preamble == ra.PREAMBLE
    assert state.entries[0].prev_sha256 == sha(preamble)
    for prev, cur in zip(state.entries, state.entries[1:]):
        assert cur.prev_sha256 == sha(prev.raw)
    # entries tile the file exactly: preamble + raw entries == file bytes
    assert preamble + b"".join(e.raw for e in state.entries) == data
    assert [e.sha256 for e in entries] == [e.sha256 for e in state.entries]
    assert state.last_id == "R-0004" and state.last_sha256 == sha(state.entries[-1].raw)


def test_exact_entry_bytes_and_verbatim_body(tmp_path, fake_date):
    path = tmp_path / "RULES.md"
    body = "Greek: \u03bb\u03cc\u03b3\u03bf\u03c2\n### sub-heading is fine\n```\ncode\n```".encode()
    e1 = ra.append_entry(path, "D-1", "declaration", body)
    e2 = ra.append_entry(path, "D-2", "result", b"second\n")
    expected1 = (b"## D-1\n- utc: 2026-09-24T12:00:01Z\n- prev_sha256: "
                 + sha(ra.PREAMBLE).encode() + b"\n- kind: declaration\n" + body + b"\n\n")
    expected2 = (b"## D-2\n- utc: 2026-09-24T12:00:02Z\n- prev_sha256: "
                 + sha(expected1).encode() + b"\n- kind: result\nsecond\n\n")
    assert path.read_bytes() == ra.PREAMBLE + expected1 + expected2
    assert e1.raw == expected1 and e2.raw == expected2
    assert e1.body == body + b"\n\n"


def test_utc_comes_from_date_command(tmp_path, fake_date):
    path = tmp_path / "RULES.md"
    entry = ra.append_entry(path, "T-1", "decision", b"x\n")
    assert fake_date == [["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]]
    assert entry.utc == "2026-09-24T12:00:01Z"
    assert b"- utc: 2026-09-24T12:00:01Z\n" in path.read_bytes()


def test_module_does_not_use_python_clock():
    src = Path(ra.__file__).read_text()
    assert "datetime" not in src and "import time" not in src
    assert ra.DATE_CMD == ("date", "-u", "+%Y-%m-%dT%H:%M:%SZ")


def test_real_date_output_format(tmp_path):
    entry = ra.append_entry(tmp_path / "RULES.md", "T-2", "result", b"x")
    assert ra.UTC_RE.fullmatch(entry.utc)


def test_bad_date_output_refused(tmp_path, monkeypatch):
    path = tmp_path / "RULES.md"
    make_log(path, 1)
    before = path.read_bytes()
    monkeypatch.setattr(
        ra.subprocess, "run",
        lambda args, *a, **k: subprocess.CompletedProcess(args, 0, stdout="Thu Sep 24\n"),
    )
    with pytest.raises(ra.RulesError, match="unexpected output"):
        ra.append_entry(path, "T-3", "result", b"x")
    assert path.read_bytes() == before


# ------------------------------------------------------------------ tampering

def _tamper_old_byte(data: bytes) -> bytes:
    i = data.index(b"Body of entry 1")
    return data[:i] + b"b" + data[i + 1:]


def _tamper_preamble_byte(data: bytes) -> bytes:
    assert data.index(b"hash-chained log") < data.index(b"\n## ")
    return data.replace(b"hash-chained log", b"hash-chained LOG", 1)


def _tamper_old_utc(data: bytes) -> bytes:
    i = data.index(b"- utc: ") + len(b"- utc: ")
    old = data[i:i + 4]
    return data[:i] + (b"1999" if old != b"1999" else b"2000") + data[i + 4:]


def _delete_line(data: bytes) -> bytes:
    lines = data.split(b"\n")
    idx = lines.index(b"- item a")  # first entry's body
    return b"\n".join(lines[:idx] + lines[idx + 1:])


def _delete_middle_entry(data: bytes) -> bytes:
    pre, segs = ra.split_segments(data)
    return pre + b"".join(raw for i, (_, raw) in enumerate(segs) if i != 1)


def _reorder_entries(data: bytes) -> bytes:
    pre, segs = ra.split_segments(data)
    raws = [raw for _, raw in segs]
    raws[1], raws[2] = raws[2], raws[1]
    return pre + b"".join(raws)


def _drop_final_newline(data: bytes) -> bytes:
    return data.rstrip(b"\n")


def _insert_cf(data: bytes) -> bytes:
    return data.replace(b"Body of entry 3", "Body of\u200b entry 3".encode(), 1)


def _insert_header_in_body(data: bytes) -> bytes:
    return data.replace(b"- item a\n", b"- item a\n## injected\n", 1)


TAMPERS = {
    "edit-byte-old-entry": (_tamper_old_byte, "entry #2", "chain broken"),
    "edit-byte-preamble": (_tamper_preamble_byte, "entry #1", "chain broken"),
    "edit-old-utc": (_tamper_old_utc, "entry #2", "chain broken"),
    "delete-line": (_delete_line, "entry #2", "chain broken"),
    "delete-entry": (_delete_middle_entry, "entry #2", "chain broken"),
    "reorder-entries": (_reorder_entries, "entry #2", "chain broken"),
    "drop-final-newline": (_drop_final_newline, "entry #3", "end with a newline"),
    "insert-cf-char": (_insert_cf, "entry #3", "U+200B"),
    "insert-header-line": (_insert_header_in_body, "entry #2", "entry must have header"),
}


@pytest.mark.parametrize("name", sorted(TAMPERS))
def test_tamper_detected_and_append_refused(tmp_path, name):
    fn, where, what = TAMPERS[name]
    path = tmp_path / "RULES.md"
    make_log(path, 3)
    assert ra.verify_file(path).ok
    bad = fn(path.read_bytes())
    path.write_bytes(bad)
    state = ra.verify_file(path)
    assert not state.ok
    assert where in state.error and what in state.error, state.error
    with pytest.raises(ra.RulesError, match="refusing to write"):
        ra.append_entry(path, "R-9999", "result", b"after tamper\n")
    assert path.read_bytes() == bad


def test_cli_verify_reports_first_break(tmp_path):
    path = tmp_path / "RULES.md"
    make_log(path, 3)
    path.write_bytes(_reorder_entries(path.read_bytes()))
    proc = run_cli("verify", "--file", str(path))
    assert proc.returncode == 1
    assert b"FAIL" in proc.stderr and b"entry #2" in proc.stderr
    proc = run_cli("append", "--file", str(path), "--id", "X-1", "--kind", "result",
                   "--body-file", "-", stdin=b"nope\n")
    assert proc.returncode == 1 and b"refusing to write" in proc.stderr


# ------------------------------------------------------------ input rejection

def test_duplicate_id_rejected(tmp_path):
    path = tmp_path / "RULES.md"
    make_log(path, 2)
    before = path.read_bytes()
    with pytest.raises(ra.RulesError, match="duplicate ID"):
        ra.append_entry(path, "R-0001", "result", b"again\n")
    assert path.read_bytes() == before


def test_hand_written_duplicate_id_fails_verify(tmp_path):
    path = tmp_path / "RULES.md"
    make_log(path, 1)
    data = path.read_bytes()
    state = ra.verify_bytes(data)
    forged = ra.format_entry("R-0001", "2026-09-24T00:00:00Z", state.last_sha256, "result",
                             b"forged\n")
    state = ra.verify_bytes(data + forged)
    assert not state.ok and "duplicate ID" in state.error


@pytest.mark.parametrize("body", [
    b"intro\n## Not allowed\nmore\n",
    b"## starts with header\n",
    b"line\r\n## crlf header\r\n",
])
def test_header_line_in_body_rejected(tmp_path, body):
    path = tmp_path / "RULES.md"
    make_log(path, 1)
    before = path.read_bytes()
    with pytest.raises(ra.RulesError, match="starts with '## '"):
        ra.append_entry(path, "H-1", "result", body)
    assert path.read_bytes() == before


def test_similar_headers_in_body_allowed(tmp_path):
    path = tmp_path / "RULES.md"
    body = b"### level three\n#### four\n##no-space\n text ## mid-line\n"
    ra.append_entry(path, "H-2", "result", body)
    state = ra.verify_file(path)
    assert state.ok and state.entries[0].body == body + b"\n"


@pytest.mark.parametrize("entry_id,kind,body,match", [
    ("bad id", "result", b"x", "invalid ID"),
    ("", "result", b"x", "invalid ID"),
    ("-lead", "result", b"x", "invalid ID"),
    ("A\u200bB", "result", b"x", "invalid ID"),
    ("OK-1", "opinion", b"x", "invalid kind"),
    ("OK-1", "result", b"  \n\n", "empty"),
    ("OK-1", "result", b"\xff\xfe", "UTF-8"),
    ("OK-1", "result", "zero\u200bwidth".encode(), "U\\+200B"),
    ("OK-1", "result", "\ufeffbom".encode(), "U\\+FEFF"),
])
def test_invalid_requests_rejected(tmp_path, entry_id, kind, body, match):
    path = tmp_path / "RULES.md"
    with pytest.raises(ra.RulesError, match=match):
        ra.append_entry(path, entry_id, kind, body)
    assert not path.exists()


def test_concurrent_appends_keep_chain(tmp_path):
    path = tmp_path / "RULES.md"
    errors: list[BaseException] = []

    def worker(w: int) -> None:
        try:
            for i in range(5):
                ra.append_entry(path, f"W{w}-{i}", "result", f"worker {w} item {i}\n".encode())
        except BaseException as exc:  # pragma: no cover - reported below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(w,)) for w in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    state = ra.verify_file(path)
    assert state.ok and len(state.entries) == 20


# ------------------------------------------------------------------------ CLI

def test_cli_append_stdin_verify_last_init(tmp_path):
    path = tmp_path / "RULES.md"
    proc = run_cli("verify", "--file", str(path))
    assert proc.returncode == 2
    proc = run_cli("init", "--file", str(path))
    assert proc.returncode == 0 and path.read_bytes() == ra.PREAMBLE
    proc = run_cli("last", "--file", str(path))
    assert proc.returncode == 0
    assert proc.stdout.decode().split() == ["(preamble)", sha(ra.PREAMBLE)]

    proc = run_cli("append", "--file", str(path), "--id", "C-1", "--kind", "declaration",
                   "--body-file", "-", stdin=b"from stdin\n")
    assert proc.returncode == 0, proc.stderr
    body_file = tmp_path / "body.md"
    body_file.write_bytes(b"from a file\n")
    proc = run_cli("append", "--file", str(path), "--id", "C-2", "--kind", "metric-hash",
                   "--body-file", str(body_file))
    assert proc.returncode == 0, proc.stderr
    assert b"appended C-2" in proc.stdout

    state = ra.verify_file(path)
    assert state.ok and [e.id for e in state.entries] == ["C-1", "C-2"]
    assert state.entries[0].body == b"from stdin\n\n"

    proc = run_cli("verify", "--file", str(path))
    assert proc.returncode == 0 and b"OK" in proc.stdout and b"2 entries" in proc.stdout
    proc = run_cli("last", "--file", str(path))
    assert proc.stdout.decode().split() == ["C-2", state.entries[-1].sha256]

    proc = run_cli("append", "--file", str(path), "--id", "C-2", "--kind", "result",
                   "--body-file", "-", stdin=b"dup\n")
    assert proc.returncode == 1 and b"duplicate ID" in proc.stderr
    proc = run_cli("init", "--file", str(path))
    assert proc.returncode == 0 and b"unchanged" in proc.stdout
    assert ra.verify_file(path).ok and len(ra.verify_file(path).entries) == 2


def test_cli_default_path_is_git_toplevel(tmp_path):
    env = dict(os.environ, GIT_CONFIG_GLOBAL=str(tmp_path / "none"), GIT_CONFIG_NOSYSTEM="1")
    subprocess.run(["git", "init", "-q", str(tmp_path / "r")], check=True, env=env)
    sub = tmp_path / "r" / "deep" / "dir"
    sub.mkdir(parents=True)
    proc = run_cli("append", "--id", "G-1", "--kind", "result", "--body-file", "-",
                   stdin=b"x\n", cwd=sub)
    assert proc.returncode == 0, proc.stderr
    assert ra.verify_file(tmp_path / "r" / "RULES.md").ok
    assert not (sub / "RULES.md").exists()
