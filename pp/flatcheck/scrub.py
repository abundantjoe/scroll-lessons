"""Pre-publication scrub: secrets/keys, local paths, Paris 4 title-search
identifiers, project/governance references, licence. Writes scrub.json."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHECKS = {
    "secrets_keys": [r"-----BEGIN [A-Z ]*PRIVATE KEY", r"AKIA[0-9A-Z]{16}", r"gh[pousr]_[A-Za-z0-9]{20,}", r"sk-[A-Za-z0-9]{20,}",
                     r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}", r"AGE-SECRET-KEY", r"\.agekey"],
    "local_paths": [r"/srv/", r"/work/", r"/tmp/", r"/home/user", r"scratchpad", r"/root/"],
    "paris4_title_search": [r"(?i)paris ?4", r"PHercParis4", r"w010-027", r"w028-037", r"20260701183124", r"20260701183125",
                            r"20260411134726", r"(?i)title[- ]?search", r"(?i)\bp4[_-]"],
    "project_governance_personal": [r"(?i)hercules", r"\bRULES\b", r"DECL-", r"METRIC-HASH", r"(?i)provenance", r"the owner",
                                    r"HRC-JB", r"(?i)orchestrator", r"(?i)sibling", r"(?i)\bseal"],
}
files = [p for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.name != "scrub.json"
         and ".egg-info" not in str(p) and p.name != "scrub.py"]
res = {"n_files": len(files), "files": [str(p.relative_to(ROOT)) for p in files], "hits": {}, "binary_skipped": []}
for p in files:
    try:
        txt = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        res["binary_skipped"].append(str(p.relative_to(ROOT)))
        continue
    for cat, pats in CHECKS.items():
        for pat in pats:
            for m in re.finditer(pat, txt):
                line = txt.count("\n", 0, m.start()) + 1
                res["hits"].setdefault(cat, []).append({"file": str(p.relative_to(ROOT)), "line": line, "pattern": pat,
                                                        "match": m.group(0)[:40]})
cf = [str(p.relative_to(ROOT)) for p in files if p.suffix in (".py", ".md", ".toml", ".cpp", ".json", ".txt")
      and any(0x200B <= ord(ch) <= 0x200F or ord(ch) in (0xFEFF, 0x2060, 0x00AD) for ch in p.read_text(errors="ignore"))]
res["unicode_cf_files"] = cf
lic = (ROOT / "LICENSE").read_text() if (ROOT / "LICENSE").exists() else ""
res["licence_mit_present"] = lic.startswith("MIT License")
res["pass"] = not res["hits"] and not cf and res["licence_mit_present"]
(ROOT / "scrub.json").write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps({"pass": res["pass"], "hits": res["hits"], "unicode_cf_files": cf,
                  "licence": res["licence_mit_present"], "n_files": len(files)}, indent=1))
sys.exit(0 if res["pass"] else 1)
