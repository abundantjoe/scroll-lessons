# Provenance: Project HERCULES | owner the owner | [id removed]
"""Tests for tools/sib/sg/licence/lineage.py (synthetic metadata)."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "sib" / "sg" / "licence"))
import lineage as L  # noqa: E402


def item(ids, text=None, kind="checkpoint"):
    return {"kind": kind, "id": "x", "source": "s", "licence_ids": ids, "licence_text": text}


@pytest.mark.parametrize("ids", [["mit"], ["license:mit", "MIT"], ["Apache 2.0"], ["cc0"], ["CC BY 4.0"], ["bsd-3-clause"]])
def test_permissive(ids):
    assert L.classify(item(ids))["verdict"] == "PERMITS-RELEASE"


@pytest.mark.parametrize("ids", [["CC BY-NC 4.0"], ["cc-by-nc-sa-4.0"], ["cc-by-nd-4.0"], ["CC BY-SA 4.0"], ["gpl-3.0"],
                                 ["agpl-3.0"], ["All rights reserved"], ["mit", "cc-by-nc-4.0"]])
def test_blocking(ids):
    r = L.classify(item(ids))  # kind checkpoint: must be permissive
    assert r["verdict"] == "BLOCKS" and r["reason"]


@pytest.mark.parametrize("ids", [[], [None], ["none"], ["other"], ["wtfpl-custom"], ["mit", "apache-2.0"]])
def test_unverified(ids):
    assert L.classify(item(ids))["verdict"] == "UNVERIFIED"


def test_permissive_card_naming_nc_data_gets_a_caveat():
    r = L.classify(item(["mit"], "MIT - released by the Vesuvius Challenge. Underlying tomographic data are distributed under CC BY-NC 4.0."))
    assert r["verdict"] == "PERMITS-RELEASE" and "own lineage item" in r["caveat"]


def test_overall_is_the_worst_item():
    lin = {"items": [item(["mit"]), item([], kind="dataset")]}
    assert L.check(lin)["overall"] == "UNVERIFIED"
    lin["items"].append(item(["cc-by-nc-nd-4.0"], kind="dataset"))
    assert L.check(lin)["overall"] == "BLOCKS"
    assert L.check({"items": [item(["mit"]), item(["apache-2.0"])]})["overall"] == "PERMITS-RELEASE"
    assert L.check({"items": []})["overall"] == "UNVERIFIED"


def test_base_lineage_from_catalogue_uses_recorded_metadata_only():
    lin = L.base_lineage_from_catalogue(ROOT)
    r = L.check(lin)
    v = {i["kind"] + ":" + i["id"][:24]: i["verdict"] for i in r["items"]}
    assert r["items"][0]["verdict"] == "PERMITS-RELEASE"  # ink_9um card: MIT
    assert r["items"][1]["verdict"] == "PERMITS-RELEASE"  # bucket CC BY-NC 4.0 dataset: release under the same terms
    assert r["items"][2]["verdict"] == "UNVERIFIED"  # ink_9um labels: no licence stated
    assert r["overall"] == "UNVERIFIED", v


def test_no_network_code():
    import ast
    tree = ast.parse((ROOT / "tools/sib/sg/licence/lineage.py").read_text())
    mods = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    mods |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not mods & {"urllib", "requests", "http", "socket", "httpx", "boto3", "huggingface_hub", "subprocess"}


def test_dataset_nc_permits_same_terms_but_nd_sa_block():
    assert L.classify(item(["CC BY-NC 4.0"], kind="dataset"))["verdict"] == "PERMITS-RELEASE"
    assert L.classify(item(["cc-by-nc-sa-4.0"], kind="dataset"))["verdict"] == "BLOCKS"
    assert L.classify(item(["cc-by-nc-nd-4.0"], kind="dataset"))["verdict"] == "BLOCKS"
    assert L.classify(item(["CC BY-NC 4.0"], kind="checkpoint"))["verdict"] == "BLOCKS"
