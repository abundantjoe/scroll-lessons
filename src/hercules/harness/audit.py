"""Reader transcript audit (DECL-HARNESS, DECL-HARNESS-A1).

Provenance: Project HERCULES | owner the owner | [id removed]

A blind agent is VALID only if its tool calls are: Read calls on its listed image paths
(each at most twice), at most one Bash call that writes its answer encrypted to the
scorer recipient at its assigned output path (sealed-output mode), and the final
hand-back. The audit never prints the content of any tool call, so answers never
reach the orchestrator through it.
"""
import json
import re
import sys

HANDBACK_TOOLS = {"SubagentHandback"}
MAX_READS_PER_IMAGE = 2
# age -r <recipient> -o <path> <<'EOF' ... EOF   (nothing before `age`, nothing after EOF)
SEALED_WRITE = re.compile(
    r"\Aage -r (?P<rcpt>age1[0-9a-z]{58}) -o (?P<out>/work/sealed_io/[0-9a-f-]{36}\.age) <<'EOF'\n"
    r"(?P<body>.*)\nEOF\n?\Z", re.S)


def tool_calls(transcript_path):
    """Yield (name, input_dict) for every tool_use block in a JSONL transcript."""
    with open(transcript_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = rec.get("message") if isinstance(rec, dict) else None
            if not isinstance(msg, dict) or msg.get("role") != "assistant":
                continue
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    yield block.get("name"), block.get("input") or {}


def audit(transcript_path, allowed_images, sealed_output=None, recipient=None):
    """sealed_output: the one path the agent may write (sealed-output mode) or None."""
    allowed = set(allowed_images)
    counts = {p: 0 for p in allowed}
    violations, calls = [], []
    writes = 0
    for name, inp in tool_calls(transcript_path):
        if name == "Read" and inp.get("file_path") in allowed:
            calls.append({"name": name, "path": inp["file_path"]})
            counts[inp["file_path"]] += 1
            if counts[inp["file_path"]] > MAX_READS_PER_IMAGE:
                violations.append("image read too often")
        elif name in HANDBACK_TOOLS:
            calls.append({"name": name})
        elif name == "Bash" and sealed_output is not None:
            m = SEALED_WRITE.match(inp.get("command", ""))
            ok = bool(m) and m.group("out") == sealed_output and m.group("rcpt") == recipient
            if ok:
                body = m.group("body")
                # the heredoc must end at the final EOF only, and hold one JSON object
                if any(line.strip() == "EOF" for line in body.split("\n")):
                    ok = False
                else:
                    try:
                        ok = isinstance(json.loads(body), dict)
                    except json.JSONDecodeError:
                        ok = False
            calls.append({"name": "Bash", "sealed_write_ok": ok})
            writes += 1
            if not ok:
                violations.append("Bash call is not the permitted sealed write")
            if writes > 1:
                violations.append("more than one sealed write")
        else:
            calls.append({"name": name})
            violations.append(f"forbidden call: {name}")
    if sealed_output is not None and writes == 0:
        violations.append("no sealed write")
    unread = [p for p, c in counts.items() if c == 0]
    return {"valid": not violations, "violations": violations, "calls": calls,
            "unread_images": unread}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("images", nargs="*")
    ap.add_argument("--sealed-output")
    ap.add_argument("--recipient")
    a = ap.parse_args()
    res = audit(a.transcript, a.images, a.sealed_output, a.recipient)
    print(json.dumps(res, indent=1))
    sys.exit(0 if res["valid"] else 1)
