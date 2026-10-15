# Provenance: Project HERCULES | owner the owner | [id removed]
"""Tests for tools/sib/sg/submit_kit (draft-only generator; synthetic data only)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "sib" / "sg" / "submit_kit"))

import fl_requirements as FLR  # noqa: E402


def test_fl_quotes_are_verbatim_on_the_live_page():
    page = (ROOT / "logs/sib/sg/submit_kit/prizes_20260925_live.rendered.txt").read_text(encoding="utf-8")
    flat = " ".join(page.split())
    ids = [f[0] for f in FLR.FL]
    assert ids == [f"FL-{i:02d}" for i in range(1, 26)]
    for fid, _, quote, _ in FLR.FL:
        assert " ".join(quote.split()) in flat, fid


import ast  # noqa: E402
import copy  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import unicodedata  # noqa: E402

import pytest  # noqa: E402

import generate as GEN  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "sib" / "sg" / "pkg" / "src" / "hercules"))
from sg import gate as SGG  # noqa: E402
from sg import synth as SGS  # noqa: E402
from sg import constants as SGC  # noqa: E402

MANIFEST = json.loads((ROOT / "tools/sib/sg/submit_kit/dryrun_manifest.json").read_text())
BAR = {k: (list(v) if isinstance(v, tuple) else v) for k, v in vars(SGC).items() if k.isupper()}
OUTPUT_FILES = ("answer_sheet.json", "answer_sheet.md", "methodology.md", "fp_mitigation.md", "heldout_table.md",
                "disclosure.md", "fl_checklist.md", "trace.json")


@pytest.fixture(scope="module")
def sg_pass():
    inp = SGS.passing_inputs()
    inp.pop("_sealers_for_band")
    r = SGG.sg_check(inp)
    assert r["overall"] == "PASS"
    return json.loads(json.dumps(SGG._hashable(r)))


def gen(tmp_path, sg, man=MANIFEST):
    t = GEN.generate(sg, man, BAR, tmp_path)
    return t, {f: (tmp_path / f).read_text(encoding="utf-8") for f in OUTPUT_FILES}


def test_all_files_drafted_with_headers(tmp_path, sg_pass):
    t, out = gen(tmp_path, sg_pass)
    for f, text in out.items():
        if f.endswith(".md"):
            lines = text.splitlines()
            assert lines[0] == GEN.PROVENANCE and GEN.DRAFT in lines[2] and GEN.DRY in lines[3], f
    assert t["missing_fields"] == []


def test_owner_only_fields_empty_and_marked(tmp_path, sg_pass):
    _, out = gen(tmp_path, sg_pass)
    sheet = json.loads(out["answer_sheet.json"])["entries"]
    by_q = {e["question"]: e for e in sheet}
    for q in ("Email", "Your full name", "Team name", "Terms and Conditions",
              "Additional information as described on https://scrollprize.org/prizes"):
        assert by_q[q]["owner_only"] and by_q[q]["answer"] == "" and by_q[q]["status"].startswith("OWNER-ONLY")
    s = by_q["Scroll / Volume with evidence of letters"]
    assert s["status"] == "FILLED FROM DATA" and MANIFEST["scroll"] in s["answer"]


def test_form_entries_match_the_official_form(tmp_path, sg_pass):
    form = json.loads((ROOT / "logs/sib/sg/submit_kit/form_questions.json").read_text())
    titles = [i["title"] for i in form["items"]]
    for e in GEN.FORM[1:]:
        assert any(t.startswith(e["question"]) for t in titles), e["question"]
    assert len(GEN.FORM) == len(titles) + 1  # + the form-level required Email field


def test_every_number_comes_from_a_named_field(tmp_path, sg_pass):
    t, out = gen(tmp_path, sg_pass)
    values = " ".join(GEN.fmt(u["value"]) for u in t["used_fields"])
    for f in ("methodology.md", "fp_mitigation.md", "heldout_table.md", "disclosure.md"):
        body = "\n".join(out[f].splitlines()[4:])  # after provenance and draft headers
        body = re.sub(r"SG \d{1,2}-\d{1,2}|FL-\d{2}|SG \d{1,2}|\bK7\b|\bsha256\b|\b[0-9a-f]{64}\b", "", body)
        for num in re.findall(r"\d+(?:\.\d+)?", body):
            assert num in values, (f, num)


def test_templates_hold_no_literal_numbers():
    for name, tpl in GEN.TEMPLATES.items():
        assert GEN._digits_ok(tpl), name
    assert not GEN._digits_ok("area 4 cm2")  # the check itself works


def test_perturbing_a_field_changes_the_text(tmp_path, sg_pass):
    man = copy.deepcopy(MANIFEST)
    man["reading"]["tiles_read"] = 987654
    _, out = gen(tmp_path, sg_pass, man)
    assert "987654" in out["disclosure.md"]


def test_missing_field_is_marked_not_invented(tmp_path, sg_pass):
    man = copy.deepcopy(MANIFEST)
    del man["reading"]["candidates_failed"]
    del man["heldout"]
    t, out = gen(tmp_path, sg_pass, man)
    assert "[MISSING: man:reading.candidates_failed]" in out["disclosure.md"]
    assert "man:heldout" in t["missing_fields"]
    st = {f["id"]: f["status"] for f in t["fl"]}
    assert st["FL-15"] == "MISSING DATA" and st["FL-20"] == "MISSING DATA"


def test_not_met_is_reported(tmp_path, sg_pass):
    man = copy.deepcopy(MANIFEST)
    man["image"]["scale_bar_1cm"] = False
    t, _ = gen(tmp_path, sg_pass, man)
    assert {f["id"]: f["status"] for f in t["fl"]}["FL-11"] == "NOT MET"


def test_refuses_without_sg_pass_unless_dry_run(tmp_path, sg_pass):
    bad = dict(sg_pass, overall="FAIL")
    real = dict(MANIFEST, dry_run=False)
    with pytest.raises(GEN.Refused):
        GEN.generate(bad, real, BAR, tmp_path)
    GEN.generate(bad, MANIFEST, BAR, tmp_path / "dry")  # DRY RUN is allowed, and stamped
    assert GEN.DRY in (tmp_path / "dry" / "methodology.md").read_text()


def test_real_pass_is_still_only_a_draft(tmp_path, sg_pass):
    _, out = gen(tmp_path, sg_pass, dict(MANIFEST, dry_run=False))
    assert GEN.DRAFT in out["methodology.md"] and GEN.DRY not in out["methodology.md"]


def test_no_network_or_submission_code():
    tree = ast.parse((ROOT / "tools/sib/sg/submit_kit/generate.py").read_text())
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module.split(".")[0])
    assert not mods & {"urllib", "requests", "http", "socket", "httpx", "selenium", "playwright", "smtplib", "webbrowser",
                       "subprocess", "boto3", "aiohttp"}
    src = (ROOT / "tools/sib/sg/submit_kit/generate.py").read_text()
    assert "formResponse" not in src and "docs.google.com" not in src


def test_outputs_clean(tmp_path, sg_pass):
    _, out = gen(tmp_path, sg_pass)
    names = re.compile(r"(?i)\b(claude|fable|opus|sonnet|haiku|gpt|gemini|llama|mistral)\b")
    for f, text in out.items():
        assert not any(unicodedata.category(c) == "Cf" for c in text), f
        assert not names.search(text), f
        assert "ignore previous" not in text.lower() and "reviewer" not in text.lower().replace("review teams", "")


def test_disclosure_has_every_required_statement(tmp_path, sg_pass):
    _, out = gen(tmp_path, sg_pass)
    d = out["disclosure.md"]
    for phrase in ("built and run by AI agents for Project HERCULES", "blind machine (LLM) readers", "correlated",
                   "machine proposal, not a papyrological reading", "Area read", "tiles", "candidates escalated",
                   "candidates that failed", "Rescans used", "Training on this scroll", "Mesh trimming", "Mirroring",
                   "agent-run procedural control"):
        assert phrase in d, phrase


import tp_requirements as TPR  # noqa: E402


def test_tp_quotes_are_verbatim_on_the_live_page():
    page = (ROOT / "logs/sib/sg/submit_kit/prizes_20260926_live.rendered.txt").read_text(encoding="utf-8")
    flat = " ".join(page.split())
    i = flat.find("PHerc. Paris 4’s Title Prize")
    assert i > 0
    section = flat[i:]
    assert [t[0] for t in TPR.TP] == [f"TP-{k:02d}" for k in range(1, 23)]
    for tid, _, quote, _ in TPR.TP:
        assert " ".join(quote.split()) in section, tid


def test_pkg_rows_in_fl_checklist(tmp_path, sg_pass):
    t, out = gen(tmp_path, sg_pass)
    st = {f["id"]: f["status"] for f in t["fl"]}
    assert st["PKG-01"] == "BLOCKED (owner decision)" and st["PKG-02"] == "DRAFTED" and st["PKG-03"].startswith("SEPARATE")
    assert "PKG-01" in out["fl_checklist.md"] and "Licence lineage" in out["disclosure.md"]
    man = copy.deepcopy(MANIFEST)
    man["licence_lineage"]["overall"] = "PERMITS-RELEASE"
    del man["sg11_refcal"]
    t, _ = gen(tmp_path / "b", sg_pass, man)
    st = {f["id"]: f["status"] for f in t["fl"]}
    assert st["PKG-01"] == "DRAFTED" and st["PKG-02"] == "MISSING DATA"


import p4_generate as P4  # noqa: E402

P4MAN = json.loads((ROOT / "tools/sib/sg/submit_kit/dryrun_p4_manifest.json").read_text())
P4REC = json.loads((ROOT / "tools/sib/sg/submit_kit/dryrun_p4_record.json").read_text())
P4FILES = ("answer_sheet.json", "answer_sheet.md", "methodology.md", "fp_mitigation.md", "disclosure.md",
           "tp_checklist.md", "trace.json")


def p4gen(tmp_path, rec=P4REC, man=P4MAN):
    t = P4.generate(rec, man, tmp_path)
    return t, {f: (tmp_path / f).read_text(encoding="utf-8") for f in P4FILES}


def test_p4_drafts_with_headers_and_owner_fields(tmp_path):
    t, out = p4gen(tmp_path)
    for f in P4FILES:
        if f.endswith(".md"):
            ls = out[f].splitlines()
            assert ls[0] == GEN.PROVENANCE and P4.DRAFT_P4 in ls[2] and GEN.DRY in ls[3]
    sheet = {e["question"]: e for e in json.loads(out["answer_sheet.json"])["entries"]}
    for q in ("Email", "Your full name", "Team name", "Terms and Conditions",
              "Additional information as described on https://scrollprize.org/prizes"):
        assert sheet[q]["answer"] == "" and sheet[q]["status"].startswith("OWNER-ONLY")
    assert t["missing_fields"] == []


def test_p4_form_entries_match_the_title_form():
    form = json.loads((ROOT / "logs/sib/sg/submit_kit/p4_form_questions.json").read_text())
    titles = [i["title"] for i in form["items"]]
    for e in P4.FORM_P4[1:5]:
        assert any(t.startswith(e["question"]) for t in titles), e["question"]
    assert form["collects_email_field"] is True


def test_p4_numbers_come_from_named_fields(tmp_path):
    t, out = p4gen(tmp_path)
    values = " ".join(GEN.fmt(u["value"]) for u in t["used_fields"])
    for f in ("methodology.md", "fp_mitigation.md", "disclosure.md"):
        body = "\n".join(out[f].splitlines()[4:])
        body = re.sub(r"(?:FL|TP|PKG)-\d{2}|\bDECL-[A-Z0-9-]*[A-Z0-9]|Paris 4|Scroll 1|\bN0\b|\bsha256\b|\b[0-9a-f]{64}\b", "", body)
        for num in re.findall(r"\d+(?:\.\d+)?", body):
            assert num in values, (f, num)


def test_p4_refuses_reader_text_and_greek():
    for bad in ({**P4REC, "namings": [{"x": 1}]}, {**P4REC, "phase2": {**P4REC["phase2"], "letters": 3}},
                {**P4REC, "note": "ΑΒ"}):
        with pytest.raises(GEN.Refused):
            P4.generate(bad, P4MAN, "/nonexistent-never-written")


def test_p4_output_has_no_greek_and_no_model_names(tmp_path):
    _, out = p4gen(tmp_path)
    names = re.compile(r"(?i)\b(claude|fable|opus|sonnet|haiku|gpt|gemini|llama|mistral)\b")
    for f, text in out.items():
        assert not any("GREEK" in unicodedata.name(c, "") for c in text), f
        assert not names.search(text), f
        assert not any(unicodedata.category(c) == "Cf" for c in text), f


def test_p4_disclosure_statements(tmp_path):
    _, out = p4gen(tmp_path)
    d = out["disclosure.md"]
    for phrase in ("built and run by AI agents for Project HERCULES", "blind machine (LLM) readers", "correlated",
                   "not calibrated (DECL-P4-2-A1)", "official model output, not the project's",
                   "not sealed against a reference, because no reference exists", "names no title words",
                   "Area read", "candidates escalated", "procedural control", "Licence lineage"):
        assert phrase in d, phrase


def test_p4_refuses_without_candidate_unless_dry(tmp_path):
    with pytest.raises(GEN.Refused):
        P4.generate({**P4REC, "status": "NO_CANDIDATE"}, {**P4MAN, "dry_run": False}, tmp_path)
    with pytest.raises(GEN.Refused):  # a phase-2 candidate is not enough: only EXT-CONFIRMED counts
        P4.generate({**P4REC, "status": "P4_CANDIDATE"}, {**P4MAN, "dry_run": False}, tmp_path)
    P4.generate(P4REC, {**P4MAN, "dry_run": False}, tmp_path / "ext")  # EXT-CONFIRMED: a real (non-dry) draft
    P4.generate({**P4REC, "status": "NO_CANDIDATE"}, P4MAN, tmp_path / "dry")


def test_p4_checklist_statuses(tmp_path):
    t, _ = p4gen(tmp_path)
    st = {x["id"]: x["status"] for x in t["tp"]}
    assert st["TP-16"] == "MISSING DATA"  # no held-out ground truth exists for the title region
    assert st["TP-15"] == "DRAFTED" and st["TP-12"] == "OWNER" and st["PKG-01"].startswith("BLOCKED")
    near = {**P4REC, "tile": {**P4REC["tile"], "min_dist_to_labelled_mm": 0.5}}
    t, _ = p4gen(tmp_path / "near", near)
    assert {x["id"]: x["status"] for x in t["tp"]}["TP-15"] == "NOT MET"


def test_p4_templates_hold_no_literal_numbers():
    for name, tpl in P4.TEMPLATES.items():
        assert GEN._digits_ok(tpl), name


def test_p4_no_network_code():
    src = (ROOT / "tools/sib/sg/submit_kit/p4_generate.py").read_text()
    tree = ast.parse(src)
    mods = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    mods |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not mods & {"urllib", "requests", "http", "socket", "httpx", "selenium", "playwright", "subprocess", "boto3"}
    assert "formResponse" not in src and "docs.google.com" not in src


def test_p4_methodology_names_key_sheet_variant(tmp_path):
    _, out = p4gen(tmp_path)
    assert "Reader key sheet: sigma2" in out["methodology.md"] and "DECL-P4-2-A2" in out["methodology.md"]
    man = copy.deepcopy(P4MAN)
    del man["reading"]
    t, out = p4gen(tmp_path / "m", P4REC, man)
    assert "[MISSING: man:reading.key_sheet_variant]" in out["methodology.md"]


@pytest.mark.parametrize("kind,must,must_not", [
    ("official_prediction", "official model output, not the project's", "applies no trained model"),
    ("raw_ct_channel", "multiplicity is disclosed", "official model output"),
    ("cross_scroll_model", "highly correlated materials", "official model output"),
])
def test_p4_material_selects_truthful_sentences(tmp_path, kind, must, must_not):
    man = copy.deepcopy(P4MAN)
    man["material"]["kind"] = kind
    t, out = p4gen(tmp_path, P4REC, man)
    text = out["methodology.md"] + out["fp_mitigation.md"] + out["disclosure.md"]
    assert must in text and must_not not in text and t["missing_fields"] == []


def test_p4_unknown_material_refused(tmp_path):
    man = copy.deepcopy(P4MAN)
    man["material"]["kind"] = "guess"
    with pytest.raises(GEN.Refused):
        P4.generate(P4REC, man, tmp_path)
