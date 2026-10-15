# Provenance: Project HERCULES | owner the owner | [id removed]
"""Pre-publication scrub of a package folder (DECL-PP-1 item 3). Numbers and matches only.
Checks: secrets and keys, local paths, Paris 4 title-search identifiers, project / governance
coupling and personal information, Unicode Cf characters, binaries and size, licence present.
Usage: pp_scrub.py PACKAGE_DIR OUT_JSON"""
import hashlib, json, re, sys, unicodedata
from pathlib import Path

root = Path(sys.argv[1])
CHECKS = {
    "secrets_keys": [r"AKIA[0-9A-Z]{16}", r"ASIA[0-9A-Z]{16}", r"gh[pousr]_[A-Za-z0-9]{20,}", r"github_pat_", r"sk-[A-Za-z0-9]{20,}",
                     r"xox[baprs]-", r"-----BEGIN [A-Z ]*PRIVATE KEY", r"AGE-SECRET-KEY", r"\bage1[0-9a-z]{20,}",
                     r"(?i)(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]{6,}", r"(?i)aws_secret",
                     r"hf_[A-Za-z0-9]{20,}", r"\b[0-9a-f]{64}\b"],
    "local_paths": [r"/srv\b", r"/work\b", r"/tmp/claude", r"(?i)scratchpad", r"/home/user", r"/root\b", r"/opt/hv", r"\.claude"],
    "paris4_search_ids": [r"(?i)paris\s*-?\s*4", r"(?i)parisiv", r"\bw0(10|27|28|37)\b", r"w010-027", r"w028-037",
                          r"20260701183124", r"20260701183125", r"20260623141924", r"20260623142658", r"20260411134726",
                          r"20260608103018", r"(?i)strip-?a\b", r"\bM2[ab]\b", r"(?i)\btitle\b", r"\b[rc]\d+\s*c\d+\b"],
    "project_governance": [r"(?i)hercules", r"HRC-", r"(?i)\bRULES(\.md)?\b", r"\bDECL-", r"(?i)\bseal", r"(?i)scorer",
                           r"(?i)orchestrat", r"logs/sib", r"tools/sib", r"(?i)\bsibling\b", r"(?i)provenance", r"(?i)ledger",
                           r"\bSG ?\d", r"(?i)sealed", r"PHerc0?841"],
    "personal_info": [r"(?i)the owner", r"(?i)\bjoseph\b", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", r"(?i)\bowner\b"],
}
res = {k: [] for k in CHECKS}
files, other = [], dict(cf_chars=[], binary_or_cache=[], over_95mb=[])
for f in sorted(p for p in root.rglob("*") if p.is_file()):
    rel = str(f.relative_to(root))
    b = f.read_bytes()
    files.append(dict(path=rel, bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
    if len(b) > 95e6:
        other["over_95mb"].append(rel)
    if "__pycache__" in rel or f.suffix in (".pyc", ".so", ".tif", ".png", ".jpg", ".npy", ".zarr"):
        other["binary_or_cache"].append(rel); continue
    try:
        t = b.decode("utf-8")
    except UnicodeDecodeError:
        other["binary_or_cache"].append(rel); continue
    if any(unicodedata.category(c) == "Cf" for c in t):
        other["cf_chars"].append(rel)
    for k, pats in CHECKS.items():
        for pat in pats:
            for m in re.finditer(pat, t):
                ln = t.count("\n", 0, m.start()) + 1
                res[k].append(dict(file=rel, line=ln, pattern=pat, match=m.group(0)[:60]))
lic = (root / "LICENSE").read_text() if (root / "LICENSE").exists() else ""
out = dict(package=root.name, n_files=len(files), files=files,
           licence=dict(present=bool(lic), mit=lic.startswith("MIT License")),
           findings=res, other=other,
           pass_=all(not v for v in res.values()) and not any(other.values()) and lic.startswith("MIT License"))
out["pass"] = out.pop("pass_")
json.dump(out, open(sys.argv[2], "w"), indent=1)
print({k: len(v) for k, v in res.items()}, {k: len(v) for k, v in other.items()}, "licence", out["licence"], "PASS" if out["pass"] else "FAIL")
for k, v in res.items():
    for x in v[:15]:
        print(k, x)
