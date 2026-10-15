"""Pre-commit checks for Project HERCULES (run by tools/hooks/pre-commit).

Provenance: Project HERCULES | owner the owner | [id removed]

All checks read STAGED content (the index git is about to commit), never the
working tree. The commit is rejected when:
  * RULES.md is deleted, or its staged bytes do not start with the exact
    HEAD bytes (append-only), or the staged chain fails verify;
  * any staged path, or staged file content, has a Unicode Cf character, or
    a staged PNG/JPEG/TIFF carries metadata (everything cf_scan reports);
  * a staged path under seals/ does not end with ".age" (seals/README.md is
    allowed);
  * a staged file contains a PEM private-key header or an age secret key;
  * a staged file is larger than MAX_FILE_BYTES.
Every problem is listed; exit status 1 rejects the commit.
"""

from __future__ import annotations

import re
import subprocess
import sys

from hercules.records import cf_scan, rules_append

RULES_PATH = "RULES.md"
MAX_FILE_BYTES = 20 * 1000 * 1000  # "20 MB", decimal (stricter than 20 MiB)
# Built from fragments so this source file does not itself match.
SECRET_PATTERNS = (
    re.compile(b"BEGIN [A-Z0-9 ]{0,40}" + b"PRIVATE KEY"),
    re.compile(b"AGE-SECRET-" + b"KEY-"),
)
GITLINK_MODE = "160000"


def git(*args: str, input: bytes | None = None) -> bytes:
    proc = subprocess.run(["git", *args], input=input, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: "
                           f"{proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout


def diff_base() -> str:
    proc = subprocess.run(["git", "rev-parse", "--verify", "-q", "HEAD^{commit}"],
                          capture_output=True, text=True)
    if proc.returncode == 0:
        return proc.stdout.strip()
    return git("hash-object", "-t", "tree", "--stdin", input=b"").decode().strip()


def staged_changes(base: str) -> list[tuple[str, str, str, str]]:
    """Return [(status, new_mode, new_sha, path)] for index vs base, no rename detection."""
    out = git("diff-index", "--cached", "-z", "--no-renames", "--full-index", base)
    fields = out.split(b"\x00")
    changes = []
    i = 0
    while i + 1 < len(fields) and fields[i]:
        meta = fields[i].decode("ascii").lstrip(":").split()
        path = fields[i + 1].decode("utf-8", "surrogateescape")
        _, new_mode, _, new_sha, status = meta
        changes.append((status[0], new_mode, new_sha, path))
        i += 2
    return changes


class BlobReader:
    """Streams blobs through one `git cat-file --batch` process."""

    def __init__(self) -> None:
        self.proc = subprocess.Popen(["git", "cat-file", "--batch"], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE)

    def read(self, sha: str) -> bytes:
        assert self.proc.stdin and self.proc.stdout
        self.proc.stdin.write(sha.encode("ascii") + b"\n")
        self.proc.stdin.flush()
        header = self.proc.stdout.readline().split()
        if len(header) != 3:
            raise RuntimeError(f"git cat-file: cannot read object {sha}")
        size = int(header[2])
        data = self.proc.stdout.read(size)
        self.proc.stdout.read(1)
        return data

    def close(self) -> None:
        if self.proc.stdin:
            self.proc.stdin.close()
        self.proc.wait()


def blob_sizes(shas: list[str]) -> dict[str, int]:
    if not shas:
        return {}
    out = git("cat-file", "--batch-check", input=("\n".join(shas) + "\n").encode("ascii"))
    sizes = {}
    for line in out.decode("ascii").splitlines():
        parts = line.split()
        if len(parts) == 3:
            sizes[parts[0]] = int(parts[2])
    return sizes


def check_rules(staged: bytes) -> list[str]:
    problems = []
    head_blob = subprocess.run(["git", "cat-file", "blob", f"HEAD:{RULES_PATH}"],
                               capture_output=True)
    if head_blob.returncode == 0:
        head = head_blob.stdout
        if not staged.startswith(head):
            common = 0
            for a, b in zip(staged, head):
                if a != b:
                    break
                common += 1
            line = head.count(b"\n", 0, common) + 1
            problems.append(f"{RULES_PATH}: not append-only: HEAD content changed or removed "
                            f"(first difference at line {line})")
        elif head and not head.endswith(b"\n") and staged != head:
            problems.append(f"{RULES_PATH}: HEAD version lacks a final newline; appending "
                            "would modify its last line")
    state = rules_append.verify_bytes(staged)
    if not state.ok:
        problems.append(f"{RULES_PATH}: verify failed: {state.error}")
    return problems


def check_path(path: str) -> list[str]:
    problems = [f.format() for f in cf_scan.scan_name(path)]
    if path.startswith("seals/") and path != "seals/README.md" and not path.endswith(".age"):
        problems.append(f"{cf_scan.display(path)}: files under seals/ must be age-encrypted "
                        "(*.age); only seals/README.md may be plaintext")
    return problems


def check_content(path: str, data: bytes) -> list[str]:
    problems = [f.format() for f in cf_scan.scan_content(path, data)]
    for pattern in SECRET_PATTERNS:
        m = pattern.search(data)
        if m:
            problems.append(f"{cf_scan.display(path)}: contains private key material "
                            f"({m.group().decode('ascii', 'replace')})")
    return problems


def run_checks() -> list[str]:
    base = diff_base()
    changes = staged_changes(base)
    problems: list[str] = []
    present = [c for c in changes if c[0] != "D"]
    if any(status == "D" and path == RULES_PATH for status, _, _, path in changes):
        problems.append(f"{RULES_PATH}: deleting the append-only log is not allowed")
    sizes = blob_sizes(sorted({sha for _, mode, sha, _ in present if mode != GITLINK_MODE}))
    reader = BlobReader()
    try:
        for status, mode, sha, path in present:
            problems.extend(check_path(path))
            if mode == GITLINK_MODE:
                continue
            if status == "U" or sha not in sizes:
                problems.append(f"{cf_scan.display(path)}: cannot read staged content")
                continue
            if sizes[sha] > MAX_FILE_BYTES:
                problems.append(f"{cf_scan.display(path)}: {sizes[sha]} bytes exceeds the "
                                f"{MAX_FILE_BYTES}-byte limit")
                continue
            data = reader.read(sha)
            problems.extend(check_content(path, data))
            if path == RULES_PATH:
                problems.extend(check_rules(data))
    finally:
        reader.close()
    return problems


def main() -> int:
    try:
        problems = run_checks()
    except Exception as exc:  # noqa: BLE001 - fail closed
        print(f"pre-commit: internal error, rejecting commit: {exc}", file=sys.stderr)
        return 1
    if problems:
        print(f"pre-commit: commit REJECTED ({len(problems)} problem(s)):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
