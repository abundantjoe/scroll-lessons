"""Pre-publication scrub of a package tree. Usage: python scrub.py PKG_DIR OUT_JSON
Checks every file: secrets/keys/tokens, private paths, governance references,
Paris 4 title-search identifiers, personal information; licence present.
Exit 0 iff no finding."""
import hashlib
import json
import re
import sys
from pathlib import Path

CHECKS = {
    "secrets": r"(?i)(api[_-]?key|secret|passw(or)?d|token|bearer\s|BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|github_pat_|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|aws_secret|xox[bap]-)",
    "private_paths": r"(/srv/|/work/|/tmp/|scratchpad|/home/user|/root/|/opt/hv|\.ccr)",
    "governance": r"(?i)(\bRULES\b|RULES\.md|HERCULES|governance|orchestrat|\bsibling|\bsib[-_/]|DECL-|STANDING.ORDER|\bSG ?\d|sealed|seal\b|blind.reader|scorer|HRC-)",
    "paris4_title_search": r"(?i)(paris ?4|PHercParis4|w010|w028|w0?10-0?27|w0?28-0?37|20260411134726|20260608103018|20260623141924|2026070118312[45]|strip-a|\bM2a\b|title.search|P4-)",
    "personal": r"(?i)(the owner|the owner|@gmail|\bemail\b.*@|phone|address:)",
}
# reviewed exceptions: (check, file regex, context regex, reason); each use is recorded in the output
ALLOW = [
    ("secrets", r"^src/handcheck/public\.py$", r"(keys, token = \[\], None|if token:|continuation-token|ContinuationToken|token = m\.group)",
     "S3 ListObjectsV2 pagination continuation token of the anonymous public bucket, not a credential"),
    ("paris4_title_search", r"^results/(official_meshes\.(csv|json)|winding_PHerc0139\.json)$", r"(^PHerc0139,|PHerc0139/segments/|\"segment\": \"2025010800000\d-w0)",
     "official PHerc0139 segment ID (winding number in the organizer name), not Paris 4 data"),
]


def main(root: str, out: str) -> int:
    rootp = Path(root)
    files = sorted(p for p in rootp.rglob("*") if p.is_file() and ".git" not in p.parts
                   and "__pycache__" not in p.parts and not p.name.endswith(".egg-info")
                   and ".egg-info" not in str(p))
    findings, allowed = [], []
    for p in files:
        rel = str(p.relative_to(rootp))
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(dict(check="binary_file", file=rel))
            continue
        for name, pat in CHECKS.items():
            for m in re.finditer(pat, text):
                line = text.count("\n", 0, m.start()) + 1
                ctx = text.splitlines()[line - 1]
                why = [r for c, fr, cr, r in ALLOW if c == name and re.search(fr, rel) and re.search(cr, ctx)]
                if why:
                    allowed.append(dict(check=name, file=rel, line=line, match=m.group(0), reason=why[0]))
                    continue
                findings.append(dict(check=name, file=rel, line=line, match=m.group(0),
                                     context=text.splitlines()[line - 1][:160]))
    lic = (rootp / "LICENSE")
    licence_ok = lic.exists() and lic.read_text().startswith("MIT License")
    res = dict(package=str(rootp.name), n_files=len(files),
               files={str(p.relative_to(rootp)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
               checks=list(CHECKS), licence_mit=licence_ok, findings=findings, reviewed_exceptions=allowed,
               scrub_ok=bool(licence_ok and not findings))
    Path(out).write_text(json.dumps(res, indent=1))
    print(json.dumps(dict(n_files=len(files), n_findings=len(findings), n_reviewed_exceptions=len(allowed), licence_mit=licence_ok, scrub_ok=res["scrub_ok"])))
    for f in findings:
        print(f)
    return 0 if res["scrub_ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
