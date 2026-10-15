"""Tests for tools/hooks/pre-commit, run inside throwaway git repositories.

Provenance: Project HERCULES | owner the owner | [id removed]

Each test copies the real hook scripts and the hercules.records package into
a fresh `git init` repo under tmp_path, installs the hook with
tools/hooks/install.sh and drives it through real `git commit` calls.
Secret markers are assembled from fragments so this file never contains one.
"""

from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from hercules.records import precommit
from hercules.records import rules_append as ra

REPO = Path(__file__).resolve().parents[1]
PROVENANCE = "Provenance: Project HERCULES | owner the owner | [id removed]"


class Repo:
    def __init__(self, root: Path, env: dict[str, str]):
        self.root = root
        self.env = env

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=self.root, env=self.env,
                              capture_output=True, text=True, check=check)

    def write(self, rel: str, data: bytes | str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
        return p

    def commit(self, *paths: str, msg: str = "test") -> subprocess.CompletedProcess:
        if paths:
            self.git("add", "--", *paths)
        return self.git("commit", "-q", "-m", msg, check=False)

    def head_count(self) -> int:
        return int(self.git("rev-list", "--count", "HEAD").stdout.strip())

    @property
    def rules(self) -> Path:
        return self.root / "RULES.md"


@pytest.fixture
def repo(tmp_path) -> Repo:
    root = tmp_path / "repo"
    root.mkdir()
    gitconfig = tmp_path / "gitconfig"
    gitconfig.write_text("")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.pop("PYTHONPATH", None)
    env.update(GIT_CONFIG_GLOBAL=str(gitconfig), GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="[email removed]",
               GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="[email removed]")
    r = Repo(root, env)
    r.git("init", "-q", "-b", "main")
    r.git("config", "commit.gpgsign", "false")
    # Mirror the real layout: tools/hooks + src/hercules/records (left untracked).
    shutil.copytree(REPO / "tools" / "hooks", root / "tools" / "hooks")
    pkg = root / "src" / "hercules"
    (pkg / "records").mkdir(parents=True)
    shutil.copy2(REPO / "src" / "hercules" / "__init__.py", pkg / "__init__.py")
    for f in (REPO / "src" / "hercules" / "records").glob("*.py"):
        shutil.copy2(f, pkg / "records" / f.name)
    proc = subprocess.run(["bash", "tools/hooks/install.sh"], cwd=root, env=env,
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert r.git("config", "core.hooksPath").stdout.strip() == "tools/hooks"

    ra.append_entry(r.rules, "INIT-1", "declaration", b"first entry\n")
    r.write("README.md", "hello\n")
    proc = r.commit("RULES.md", "README.md", msg="initial")  # unborn HEAD case
    assert proc.returncode == 0, proc.stderr
    assert r.head_count() == 1
    return r


def assert_rejected(repo: Repo, proc: subprocess.CompletedProcess, *needles: str) -> None:
    assert proc.returncode != 0, "commit unexpectedly accepted"
    assert "REJECTED" in proc.stderr, proc.stderr
    for n in needles:
        assert n in proc.stderr, proc.stderr
    assert repo.head_count() == 1


# ------------------------------------------------------------------ RULES.md

def test_accepts_clean_append(repo):
    ra.append_entry(repo.rules, "R-2", "result", b"second entry\n")
    ra.append_entry(repo.rules, "R-3", "decision", b"third entry\n")
    proc = repo.commit("RULES.md")
    assert proc.returncode == 0, proc.stderr
    assert repo.head_count() == 2
    ra.append_entry(repo.rules, "R-4", "correction", b"fourth\n")
    assert repo.commit("RULES.md").returncode == 0


def _edit_last_body(data: bytes) -> bytes:
    assert data.count(b"\nfirst entry\n") == 1
    out = data.replace(b"\nfirst entry\n", b"\nfirst ENTRY\n")
    assert ra.verify_bytes(out).ok  # the unchained last entry: only the HEAD check sees it
    return out


def _edit_preamble(data: bytes) -> bytes:
    return data.replace(b"hash-chained log", b"hash-chained LOG")  # chain breaks too


def _delete_blank_line(data: bytes) -> bytes:
    return data[:-1]  # removes the final blank separator line


def _delete_preamble_line(data: bytes) -> bytes:
    lines = data.split(b"\n")
    return b"\n".join(lines[:2] + lines[3:])


@pytest.mark.parametrize("mutate", [_edit_last_body, _edit_preamble, _delete_blank_line,
                                    _delete_preamble_line])
def test_rejects_modified_or_removed_rules_line(repo, mutate):
    repo.rules.write_bytes(mutate(repo.rules.read_bytes()))
    ra_ok = ra.verify_file(repo.rules).ok
    proc = repo.commit("RULES.md")
    assert_rejected(repo, proc, "RULES.md: not append-only")
    if not ra_ok:
        assert "verify failed" in proc.stderr


def test_rejects_modification_hidden_behind_new_entry(repo):
    repo.rules.write_bytes(_edit_last_body(repo.rules.read_bytes()))
    ra.append_entry(repo.rules, "R-2", "result", b"cover-up\n")  # chains over the edit
    assert ra.verify_file(repo.rules).ok
    assert_rejected(repo, repo.commit("RULES.md"), "not append-only")


def test_rejects_appended_entry_with_broken_chain(repo):
    forged = ra.format_entry("R-2", "2026-09-24T00:00:00Z", "0" * 64, "result", b"forged\n")
    repo.rules.write_bytes(repo.rules.read_bytes() + forged)
    proc = repo.commit("RULES.md")
    assert_rejected(repo, proc, "verify failed", "chain broken")
    assert "not append-only" not in proc.stderr


def test_rejects_deleting_rules(repo):
    repo.git("rm", "-q", "RULES.md")
    assert_rejected(repo, repo.commit(), "RULES.md: deleting")


# ------------------------------------------------------------ Cf characters

@pytest.mark.parametrize("ch", ["\u200b", "\u2060", "\ufeff"])
def test_rejects_cf_in_content(repo, ch):
    repo.write("notes.md", f"hello{ch}world\n")
    assert_rejected(repo, repo.commit("notes.md"), "notes.md:1:6", f"U+{ord(ch):04X}")


def test_rejects_cf_in_path(repo):
    repo.write("docs/re\u200bport.md", "clean content\n")
    proc = repo.commit("docs")
    assert_rejected(repo, proc, "docs/re<U+200B>port.md", "in path name")


def test_rejects_png_metadata(repo):
    info = PngInfo()
    info.add_text("Software", "plotting library")
    buf = io.BytesIO()
    Image.new("L", (4, 4)).save(buf, "PNG", pnginfo=info)
    repo.write("figs/plot.png", buf.getvalue())
    assert_rejected(repo, repo.commit("figs/plot.png"), "PNG tEXt chunk")


def test_checks_staged_content_not_worktree(repo):
    repo.write("a.md", "bad\u200b\n")
    repo.git("add", "a.md")
    repo.write("a.md", "fixed but not staged\n")
    assert_rejected(repo, repo.commit(), "a.md:1:4")
    repo.git("add", "a.md")
    repo.write("a.md", "dirty\u200b worktree only\n")
    proc = repo.commit()
    assert proc.returncode == 0, proc.stderr


# ------------------------------------------------------------------- seals/

@pytest.mark.parametrize("rel", ["seals/key.json", "seals/notes.txt", "seals/sub/README.md",
                                 "seals/answer.age.txt"])
def test_rejects_plaintext_under_seals(repo, rel):
    repo.write(rel, "plaintext\n")
    assert_rejected(repo, repo.commit(rel), "must be age-encrypted")


def test_accepts_age_files_and_seals_readme(repo):
    repo.write("seals/README.md", "Sealed answers live here.\n")
    repo.write("seals/answers.json.age", b"age-encryption.org/v1\n\x00\x9f\x88binary")
    proc = repo.commit("seals/README.md", "seals/answers.json.age")
    assert proc.returncode == 0, proc.stderr


# ------------------------------------------------------------ secrets, size

SECRET_MARKERS = [
    "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
    "-----BEGIN " + "RSA PRIVATE KEY-----",
    "-----BEGIN " + "PRIVATE KEY-----",
    "AGE-SECRET-" + "KEY-1QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ",
]


@pytest.mark.parametrize("marker", SECRET_MARKERS)
def test_rejects_private_key_material(repo, marker):
    repo.write("config/deploy.txt", f"settings\n{marker}\nabc\n")
    assert_rejected(repo, repo.commit("config/deploy.txt"), "private key material")


def test_rejects_private_key_inside_binary(repo):
    repo.write("blob.bin", b"\x00\xff" + SECRET_MARKERS[0].encode() + b"\x00")
    assert_rejected(repo, repo.commit("blob.bin"), "private key material")


def test_rejects_file_over_20mb(repo):
    p = repo.root / "big.bin"
    with open(p, "wb") as fh:
        fh.truncate(precommit.MAX_FILE_BYTES + 1)
    assert_rejected(repo, repo.commit("big.bin"), "exceeds the 20000000-byte limit")


def test_accepts_ordinary_files(repo):
    repo.write("src/mod.py", "# Provenance line\nprint('\u03bb')\n")
    buf = io.BytesIO()
    Image.new("L", (4, 4)).save(buf, "PNG")
    repo.write("figs/clean.png", buf.getvalue())
    proc = repo.commit("src/mod.py", "figs/clean.png")
    assert proc.returncode == 0, proc.stderr


def test_fails_closed_when_checker_missing(repo):
    shutil.rmtree(repo.root / "src" / "hercules" / "records")
    repo.write("ok.md", "fine\n")
    proc = repo.commit("ok.md")
    assert proc.returncode != 0 and repo.head_count() == 1


def test_reports_every_problem_at_once(repo):
    repo.write("seals/plain.txt", "x\n")
    repo.write("n.md", "a\u200bb\n")
    proc = repo.commit("seals/plain.txt", "n.md")
    assert_rejected(repo, proc, "(2 problem(s))", "age-encrypted", "U+200B")


# ------------------------------------------- hygiene of this deliverable

OWN_FILES = sorted(
    [*(REPO / "src" / "hercules" / "records").glob("*.py"),
     *(p for p in (REPO / "tools" / "hooks").iterdir() if p.is_file()),
     *(REPO / "tests").glob("test_records_*.py")]
)


@pytest.mark.parametrize("path", OWN_FILES, ids=lambda p: p.name)
def test_own_files_clean(path):
    data = path.read_bytes()
    text = data.decode("utf-8")
    assert not [c for c in text if unicodedata.category(c) == "Cf"]
    assert PROVENANCE in "\n".join(text.splitlines()[:5])
    assert not any(p.search(data) for p in precommit.SECRET_PATTERNS)


def test_hook_scripts_executable_and_use_expected_python():
    hook = REPO / "tools" / "hooks" / "pre-commit"
    assert os.access(hook, os.X_OK) and os.access(REPO / "tools/hooks/install.sh", os.X_OK)
    text = hook.read_text()
    assert "/opt/hv/bin/python" in text and "python3" in text
    assert re.search(r"export PYTHONPATH=.*/src", text)
