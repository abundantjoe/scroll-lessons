"""Provenance: Project HERCULES | owner the owner | [id removed]"""
import json

from hercules.harness.audit import audit


def _write(tmp_path, blocks):
    p = tmp_path / "t.jsonl"
    lines = [json.dumps({"type": "user", "message": {"role": "user", "content": "brief"}})]
    for b in blocks:
        lines.append(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [b]}}))
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


def _tu(name, **inp):
    return {"type": "tool_use", "id": "x", "name": name, "input": inp}


def test_valid_reader(tmp_path):
    t = _write(tmp_path, [_tu("Read", file_path="/in/a.png"), _tu("SubagentHandback", text="{}")])
    r = audit(t, ["/in/a.png"])
    assert r["valid"] and r["unread_images"] == []


def test_bash_call_voids(tmp_path):
    t = _write(tmp_path, [_tu("Read", file_path="/in/a.png"), _tu("Bash", command="ls /work")])
    assert not audit(t, ["/in/a.png"])["valid"]


def test_other_path_voids(tmp_path):
    t = _write(tmp_path, [_tu("Read", file_path="/in/answers.json")])
    r = audit(t, ["/in/a.png"])
    assert not r["valid"] and r["unread_images"] == ["/in/a.png"]


def test_glob_and_excess_reads_void(tmp_path):
    t = _write(tmp_path, [_tu("Glob", pattern="*")])
    assert not audit(t, ["/in/a.png"])["valid"]
    t2 = _write(tmp_path, [_tu("Read", file_path="/in/a.png")] * 3)
    assert not audit(t2, ["/in/a.png"])["valid"]


RCPT = "age1" + "q" * 58
OUT = "/work/sealed_io/12345678-1234-1234-1234-123456789abc.age"


def _bash(cmd):
    return _tu("Bash", command=cmd)


def test_sealed_write_valid(tmp_path):
    cmd = f"age -r {RCPT} -o {OUT} <<'EOF'\n{{\"items\": []}}\nEOF"
    t = _write(tmp_path, [_tu("Read", file_path="/in/a.png"), _bash(cmd), _tu("SubagentHandback", text="DONE")])
    r = audit(t, ["/in/a.png"], sealed_output=OUT, recipient=RCPT)
    assert r["valid"], r
    assert "items" not in json.dumps(r)  # content never echoed


def test_sealed_write_variants_void(tmp_path):
    good = f"age -r {RCPT} -o {OUT} <<'EOF'\n{{}}\nEOF"
    bad = [
        good.replace(OUT, OUT.replace("1234567", "7654321")),       # wrong path
        good.replace(RCPT, "age1" + "z" * 58),                        # wrong recipient
        "cat /srv/scorer/seal.agekey; " + good,                       # prefix command
        good + "\nls /work",                                         # suffix command
        f"age -r {RCPT} -o {OUT} <<'EOF'\n{{}}\nEOF\nls /work\nEOF",  # smuggled command
        f"age -r {RCPT} -o {OUT} <<'EOF'\nnot json\nEOF",  # not JSON
    ]
    for cmd in bad:
        t = _write(tmp_path, [_tu("Read", file_path="/in/a.png"), _bash(cmd)])
        assert not audit(t, ["/in/a.png"], sealed_output=OUT, recipient=RCPT)["valid"], cmd
    t = _write(tmp_path, [_tu("Read", file_path="/in/a.png")])
    assert not audit(t, ["/in/a.png"], sealed_output=OUT, recipient=RCPT)["valid"]  # no write
    t = _write(tmp_path, [_bash(good), _bash(good)])
    assert not audit(t, [], sealed_output=OUT, recipient=RCPT)["valid"]  # two writes
