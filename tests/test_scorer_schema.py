# Provenance: Project HERCULES | owner the owner | [id removed]
"""Tests for spec A: reader output schema and validate_reader_output."""

import copy
import json

import jsonschema
import pytest

from hercules.scorer.schema import SCHEMA_PATH, load_schema, validate_reader_output

PROVENANCE = "Provenance: Project HERCULES | owner the owner | [id removed]"


def _letter(ch="\u0391", conf="firm"):
    return {"ch": ch, "x": 10.0, "y": 20, "box": [5, 15, 15.5, 25], "conf": conf}


def _valid():
    return {
        "items": [
            {
                "id": "item-1",
                "left": {"rows": "Y", "letters": [_letter(), _letter("\u03C3", "tentative")]},
                "right": {"rows": "N", "letters": []},
            },
            {
                "id": "item-2",
                "left": {"rows": "N", "letters": []},
                "right": {"rows": "Y", "letters": [_letter("A")]},
            },
        ]
    }


def test_schema_file_is_valid_draft_2020_12_with_provenance():
    text = SCHEMA_PATH.read_text(encoding="utf-8")
    assert PROVENANCE in text.splitlines()[0]
    schema = load_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    jsonschema.Draft202012Validator.check_schema(schema)


def test_valid_object_passes():
    ok, errors = validate_reader_output(_valid())
    assert ok, errors
    assert errors == []


def test_empty_items_list_is_valid():
    assert validate_reader_output({"items": []})[0]


@pytest.mark.parametrize(
    "path",
    [
        ("items",),
        ("items", 0, "id"),
        ("items", 0, "left"),
        ("items", 0, "right"),
        ("items", 0, "left", "rows"),
        ("items", 0, "left", "letters"),
        ("items", 0, "left", "letters", 0, "ch"),
        ("items", 0, "left", "letters", 0, "x"),
        ("items", 0, "left", "letters", 0, "y"),
        ("items", 0, "left", "letters", 0, "box"),
        ("items", 0, "left", "letters", 0, "conf"),
    ],
)
def test_missing_fields_rejected(path):
    obj = _valid()
    target = obj
    for key in path[:-1]:
        target = target[key]
    del target[path[-1]]
    ok, errors = validate_reader_output(obj)
    assert not ok
    assert errors


@pytest.mark.parametrize("conf", ["maybe", "FIRM", "", None, 1])
def test_bad_conf_rejected(conf):
    obj = _valid()
    obj["items"][0]["left"]["letters"][0]["conf"] = conf
    assert not validate_reader_output(obj)[0]


@pytest.mark.parametrize("rows", ["y", "yes", "", None, True])
def test_bad_rows_rejected(rows):
    obj = _valid()
    obj["items"][0]["left"]["rows"] = rows
    assert not validate_reader_output(obj)[0]


@pytest.mark.parametrize("box", [[1, 2, 3], [1, 2, 3, 4, 5], [1, 2, "3", 4], "1,2,3,4", None, [1, 2, True, 4]])
def test_bad_box_rejected(box):
    obj = _valid()
    obj["items"][0]["left"]["letters"][0]["box"] = box
    assert not validate_reader_output(obj)[0]


@pytest.mark.parametrize("ch", ["", "\u0391\u0392", "AB", 7, None])
def test_bad_ch_rejected(ch):
    obj = _valid()
    obj["items"][0]["left"]["letters"][0]["ch"] = ch
    assert not validate_reader_output(obj)[0]


def test_ch_single_char_after_nfc_accepted():
    obj = _valid()
    obj["items"][0]["left"]["letters"][0]["ch"] = "\u0391\u0301"  # composes to one char
    assert validate_reader_output(obj)[0]


def test_unknown_but_single_char_is_valid():
    obj = _valid()
    obj["items"][0]["left"]["letters"][0]["ch"] = "?"
    assert validate_reader_output(obj)[0]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "10", True])
def test_bad_coordinates_rejected(value):
    obj = _valid()
    obj["items"][0]["left"]["letters"][0]["x"] = value
    assert not validate_reader_output(obj)[0]


def test_nan_in_box_rejected():
    obj = _valid()
    obj["items"][0]["left"]["letters"][0]["box"] = [0, 0, float("nan"), 1]
    assert not validate_reader_output(obj)[0]


def test_additional_properties_rejected():
    for where in ("root", "item", "side", "letter"):
        obj = _valid()
        target = {
            "root": obj,
            "item": obj["items"][0],
            "side": obj["items"][0]["left"],
            "letter": obj["items"][0]["left"]["letters"][0],
        }[where]
        target["note"] = "extra"
        assert not validate_reader_output(obj)[0], where


def test_duplicate_item_ids_rejected():
    obj = _valid()
    obj["items"][1]["id"] = "item-1"
    ok, errors = validate_reader_output(obj)
    assert not ok
    assert any("duplicate" in e for e in errors)


@pytest.mark.parametrize("obj", [None, [], "items", 3, {"items": {}}])
def test_non_objects_rejected(obj):
    ok, errors = validate_reader_output(obj)
    assert not ok and errors


def test_validation_does_not_mutate_or_repair():
    obj = _valid()
    obj["items"][0]["left"]["letters"][0]["conf"] = "maybe"
    before = copy.deepcopy(obj)
    validate_reader_output(obj)
    assert obj == before


def test_errors_are_deterministic_strings():
    obj = _valid()
    obj["items"][0]["left"]["letters"][0]["conf"] = "maybe"
    obj["items"][1]["right"]["rows"] = "maybe"
    e1 = validate_reader_output(obj)[1]
    e2 = validate_reader_output(json.loads(json.dumps(obj)))[1]
    assert e1 == e2
    assert all(isinstance(e, str) for e in e1)
    assert len(e1) >= 2
