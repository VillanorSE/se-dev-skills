#!/usr/bin/env python3
"""Inspect a Block Restrictions world config (BlockRestrictions.cfg).

Usage:
  br_cfg.py summary CFG
  br_cfg.py list    CFG [--restricted] [--changed] [--typeid TYPEID] [--contains TEXT]
  br_cfg.py dups    CFG
  br_cfg.py diff    OLD_CFG NEW_CFG

Read-only. Input: the world-storage file
  Saves\\<steamid>\\<world>\\Storage\\2053202808.sbm_BlockRestrictions\\BlockRestrictions.cfg
Output: plain text on stdout (list output is tab-separated). Needs only Python 3.8+.
"""
import argparse
import collections
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_common import load_cfg, non_default_fields, is_restricted, split_type, out, BOOL_FIELDS  # noqa: E402

PLACEHOLDER_GROUP = "UniqueNameHere"  # the mod writes this template group when none exist


def cmd_summary(a):
    cfg = load_cfg(a.cfg)
    st = cfg["settings"]
    out("File: %s" % a.cfg)
    out("CreativeModeAllowed=%s VerboseMode=%s" % (cfg["creative"], cfg["verbose"]))
    out("Block settings: %d" % len(st))
    groups = [g for g in cfg["groups"] if g["GroupName"] != PLACEHOLDER_GROUP]
    out("Group settings (excluding the '%s' template): %d" % (PLACEHOLDER_GROUP, len(groups)))
    out("Blocks with AllowedForPlayer=false: %d" % sum(1 for s in st if is_restricted(s)))
    for f in BOOL_FIELDS:
        default = f in ("AllowedForNPC", "AllowedForPlayer", "AllowedForUnowned")
        n = sum(1 for s in st if s[f] != default)
        out("  %-28s differs from default (%s) in %d" % (f, str(default).lower(), n))
    for f in ("PlayerMaxCount", "GridMaxCount", "FactionMaxCount"):
        out("  %-28s > 0 in %d" % (f, sum(1 for s in st if s[f] > 0)))
    out("Entries by TypeId (top 15):")
    c = collections.Counter(split_type(s["Type"])[0] for s in st)
    for t, n in c.most_common(15):
        out("  %5d  %s" % (n, t))


def cmd_list(a):
    cfg = load_cfg(a.cfg)
    rows = 0
    for s in cfg["settings"]:
        t, sub = split_type(s["Type"])
        if a.restricted and not is_restricted(s):
            continue
        if a.changed and not non_default_fields(s):
            continue
        if a.typeid and t != a.typeid and t != "MyObjectBuilder_" + a.typeid:
            continue
        if a.contains and a.contains.lower() not in s["Type"].lower():
            continue
        out("%s\t%s\t%s" % (t, sub, ",".join("%s=%s" % (f, str(s[f]).lower()) for f in non_default_fields(s)) or "(defaults)"))
        rows += 1
    sys.stderr.write("%d row(s)\n" % rows)


def cmd_dups(a):
    cfg = load_cfg(a.cfg)
    c = collections.Counter(s["Type"] for s in cfg["settings"])
    d = sorted(k for k, v in c.items() if v > 1)
    out("Duplicate Type entries: %d" % len(d))
    for k in d:
        out("  %dx %s" % (c[k], k))
    return 1 if d else 0


def cmd_diff(a):
    old = {s["Type"]: s for s in load_cfg(a.old)["settings"]}
    new = {s["Type"]: s for s in load_cfg(a.new)["settings"]}
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = []
    for k in sorted(set(old) & set(new)):
        diffs = [f for f in old[k] if old[k][f] != new[k][f]]
        if diffs:
            changed.append((k, ["%s: %s -> %s" % (f, str(old[k][f]).lower(), str(new[k][f]).lower()) for f in diffs]))
    out("Only in NEW (%d):" % len(added))
    for k in added:
        out("  + %s" % k)
    out("Only in OLD (%d):" % len(removed))
    for k in removed:
        out("  - %s" % k)
    out("Changed (%d):" % len(changed))
    for k, dd in changed:
        out("  ~ %s  [%s]" % (k, "; ".join(dd)))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("summary"); s.add_argument("cfg"); s.set_defaults(fn=cmd_summary)
    s = sub.add_parser("list"); s.add_argument("cfg")
    s.add_argument("--restricted", action="store_true", help="only AllowedForPlayer=false")
    s.add_argument("--changed", action="store_true", help="only entries that differ from the mod defaults")
    s.add_argument("--typeid", help="exact TypeId, with or without the MyObjectBuilder_ prefix")
    s.add_argument("--contains", help="case-insensitive substring of 'TypeId/SubtypeId'")
    s.set_defaults(fn=cmd_list)
    s = sub.add_parser("dups"); s.add_argument("cfg"); s.set_defaults(fn=cmd_dups)
    s = sub.add_parser("diff"); s.add_argument("old"); s.add_argument("new"); s.set_defaults(fn=cmd_diff)
    a = p.parse_args()
    try:
        sys.exit(a.fn(a) or 0)
    except (OSError, ValueError, ET.ParseError) as e:
        sys.stderr.write("error: %s\n" % e)
        sys.exit(2)


if __name__ == "__main__":
    main()
