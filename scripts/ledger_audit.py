#!/usr/bin/env python
"""ledger_audit.py -- every read on disk must have a LEDGER line, and every line must parse.

LEDGER.md is the scientific record: one line per read, keyed scroll|surface|depth offset|checkpoint+TTA|order.
A read that happened but was never ledgered is an unrecorded result, which is the one kind of gap that cannot be
reconstructed later once its maps are pruned. This checks the direction that matters (disk -> ledger) and reports
the other direction for information, because a ledgered read whose stats were pruned is normal and expected.

Note on parsing: keys contain PIPES, escaped as \\| so the markdown table keeps its columns. Splitting a row on a
plain "|" shreds every key into fragments -- the first version of this audit did exactly that and reported all 141
reads as unledgered. Rows are split on unescaped pipes only.
"""
import argparse, glob, json, os, re, sys

SPLIT = re.compile(r"(?<!\\)\|")
KEY = re.compile(r"^[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+$")


def ledger_keys(path):
    keys = set()
    for line in open(path):
        if not line.startswith("| 2026-"):
            continue
        cells = [c.strip() for c in SPLIT.split(line)]
        if len(cells) > 2:
            k = cells[2].replace("\\|", "|")
            if KEY.match(k):
                keys.add(k)
    return keys


def disk_keys(data_root):
    out = {}
    for sp in sorted(glob.glob(os.path.join(data_root, "patches", "*", "*", "read_*", "read_stats.json"))):
        try:
            out[json.load(open(sp)).get("key")] = sp
        except Exception as e:
            out["UNREADABLE %s" % sp] = str(e)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "LEDGER.md"))
    ap.add_argument("--data-root", default=os.environ.get("HERCULES_DATA", "/home/user/hercules_data"))
    a = ap.parse_args(argv)
    led, disk = ledger_keys(a.ledger), disk_keys(a.data_root)
    unledgered = sorted(k for k in disk if k and k not in led)
    pruned = sorted(k for k in led if k not in disk)
    print("LEDGER keys %d ; read_stats.json on disk %d" % (len(led), len(disk)))
    print("reads on disk with NO ledger line: %d%s" % (len(unledgered), "" if unledgered else "  (the record is complete)"))
    for k in unledgered:
        print("   UNRECORDED %s   (%s)" % (k, disk.get(k)))
    print("ledgered reads whose stats were pruned: %d  (normal)" % len(pruned))
    return 1 if unledgered else 0


if __name__ == "__main__":
    sys.exit(main())
