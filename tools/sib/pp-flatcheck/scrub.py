#!/usr/bin/env python3
"""Pre-publication scrub of a package directory (git-tracked-to-be files only; .gitignore'd dirs skipped).
Usage: scrub.py PKG_DIR OUT_JSON"""
import hashlib, json, re, sys, datetime
from pathlib import Path

SKIP_DIRS = {"data_cache", "__pycache__", ".pytest_cache", ".git"}
CHECKS = {
    "secrets": [r"AKIA[0-9A-Z]{16}", r"gh[pousr]_[A-Za-z0-9]{20,}", r"github_pat_", r"\bsk-[A-Za-z0-9]{20,}",
                r"BEGIN [A-Z ]*PRIVATE KEY", r"(?i)(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*\S+",
                r"(?i)aws_(access|secret)", r"xox[bpas]-"],
    "paths": [r"/srv\b", r"/work\b", r"/tmp\b", r"(?i)scratchpad", r"/home/", r"/root\b", r"/opt/"],
    "governance": [r"(?i)\bRULES(\.md)?\b", r"(?i)hercules", r"(?i)governance", r"(?i)orchestrat", r"(?i)sibling",
                   r"\bDECL", r"(?i)provenance", r"HRC-", r"\bsib/", r"(?i)\bflat1\b", r"(?i)standing.order", r"\bSG[ -]?\d"],
    "paris4": [r"(?i)\bparis\b", r"(?i)PHercParis", r"\bP4\b", r"w010\s*-\s*0?27", r"w028\s*-\s*0?37", r"(?i)title", r"(?i)\btiles?\b",
               r"(?i)\bstrips?\b", r"(?<![0-9]-)\bw0(1[0-9]|2[0-9]|3[0-7])\b"],
    "personal": [r"(?i)the owner", r"(?i)the owner", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", r"\+\d{1,3}[ .-]?\(?\d{2,4}\)?[ .-]\d{3}[ .-]\d{3,4}", r"\(\d{3}\) ?\d{3}-\d{4}", r"\b\d{3}-\d{3}-\d{4}\b"],
}
# allowed: the public repo URL/copyright handle, and w0NN only as part of a full official PHerc segment id
ALLOW = [r"github\.com/abundantjoe/flatcheck", r"Copyright \(c\) 2026 abundantjoe"]

def main():
    pkg, out = Path(sys.argv[1]), Path(sys.argv[2])
    files = sorted(p for p in pkg.rglob("*") if p.is_file() and not (set(p.relative_to(pkg).parts) & SKIP_DIRS))
    hits, inv = [], []
    for p in files:
        rel = str(p.relative_to(pkg))
        b = p.read_bytes()
        inv.append({"file": rel, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
        t = b.decode("utf-8", "replace")
        for a in ALLOW:
            t = re.sub(a, "", t)
        for cat, pats in CHECKS.items():
            for pat in pats:
                for m in re.finditer(pat, t):
                    line = t.count("\n", 0, m.start()) + 1
                    hits.append({"category": cat, "pattern": pat, "file": rel, "line": line, "match": m.group(0)[:60]})
    lic = (pkg / "LICENSE").exists() and "MIT License" in (pkg / "LICENSE").read_text()
    res = {"utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "package": str(pkg.name),
           "n_files": len(files), "licence_mit_present": lic, "hits": hits,
           "hit_counts": {c: sum(h["category"] == c for h in hits) for c in CHECKS}, "files": inv}
    res["scrub_ok"] = lic and not hits
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("n_files", "licence_mit_present", "hit_counts", "scrub_ok")}))
    for h in hits[:40]:
        print(h["category"], h["file"], h["line"], repr(h["match"]))

main()
