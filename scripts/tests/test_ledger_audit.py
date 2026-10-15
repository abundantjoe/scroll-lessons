"""LEDGER.md is the scientific record; a read that happened but was never ledgered cannot be reconstructed."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ledger_audit as la


def test_keys_are_split_on_unescaped_pipes_only(tmp_path):
    """Keys contain pipes, escaped as \\| to keep the table's columns. Splitting on a plain pipe shreds every key -
    the first version of this audit did that and reported all 141 reads as unledgered."""
    p = tmp_path / "L.md"
    p.write_text("| 2026-09-18 | PHerc1203\\|team_x\\|0\\|ink9um_seed42+plain\\|both | 0.4 | ... |\n")
    assert la.ledger_keys(str(p)) == {"PHerc1203|team_x|0|ink9um_seed42+plain|both"}


def test_summary_rows_are_not_mistaken_for_keys(tmp_path):
    p = tmp_path / "L.md"
    p.write_text("| 2026-09-18 | 94.5 on-sheet (50.5 in valid units) | 90 | 5 |\n")
    assert la.ledger_keys(str(p)) == set()


def test_an_unledgered_read_makes_the_audit_fail(tmp_path):
    import json
    d = tmp_path / "patches" / "PHerc0826" / "auto_grown_1" / "read_t"
    d.mkdir(parents=True)
    (d / "read_stats.json").write_text(json.dumps({"key": "PHerc0826|auto_grown_1|0|t|both"}))
    led = tmp_path / "L.md"; led.write_text("")
    assert la.main(["--ledger", str(led), "--data-root", str(tmp_path)]) == 1


def test_a_ledgered_read_whose_stats_were_pruned_is_not_a_failure(tmp_path):
    led = tmp_path / "L.md"
    led.write_text("| 2026-09-18 | PHerc0826\\|gone\\|0\\|t\\|both | 0.4 |\n")
    (tmp_path / "patches").mkdir()
    assert la.main(["--ledger", str(led), "--data-root", str(tmp_path)]) == 0
