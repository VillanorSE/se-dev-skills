#!/usr/bin/env python3
"""Compare Ship Core block groups with the cube block definitions that actually exist.

Usage:
  sc_coverage.py PACKDIR [PACKDIR ...] --blocks MODDIR [MODDIR ...] [--uncovered TYPEID [TYPEID ...]] [--show N]

PACKDIR    content pack(s) whose Data\\ShipCoreConfig_Groups.xml is read (all groups are merged, as the loader does)
--blocks   mod/game folders whose .sbc files are scanned for <CubeBlocks><Definition> (e.g. the pack itself,
           dependency mods, the game's Content\\Data\\CubeBlocks)
Reports, per group: entries, entries that match no scanned definition ("dangling"), definitions matched.
--uncovered lists definitions of the given TypeIds (with or without MyObjectBuilder_) that no group counts,
i.e. blocks that no BlockLimit can ever restrict.
Matching is the framework's: TypeId exact (MyObjectBuilder_ prefix ignored), SubtypeId exact or 'any'.
Dangling entries are expected when a dependency mod is not in --blocks. Read-only. Stdlib only.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_common import load_pack, normalize_type, out, scan_cube_blocks  # noqa: E402


def matches(entry, definition):
    t, s, _w = entry
    dt, ds = definition
    if t != dt:
        return False
    if s.lower() == "any":
        return True
    return s == ds


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("packs", nargs="+")
    p.add_argument("--blocks", nargs="+", required=True)
    p.add_argument("--uncovered", nargs="*", default=[])
    p.add_argument("--show", type=int, default=15, help="max rows per list")
    a = p.parse_args()

    groups = []
    for d in a.packs:
        if not os.path.isdir(d):
            sys.stderr.write("error: not a directory: %s\n" % d)
            return 2
        pk = load_pack(d)
        for e in pk["errors"]:
            sys.stderr.write("warning: %s\n" % e)
        groups += pk["groups"] or []
    if not groups:
        sys.stderr.write("error: no ShipCoreConfig_Groups.xml groups found in the given packs\n")
        return 2

    defs = set()
    for d in a.blocks:
        if not os.path.isdir(d):
            sys.stderr.write("error: not a directory: %s\n" % d)
            return 2
        got, bad, n = scan_cube_blocks(d)
        out("scanned %s: %d .sbc files (%d unparseable), %d cube block definitions" % (d, n, bad, len(got)))
        defs |= got
    out("%d distinct definitions; %d groups" % (len(defs), len(groups)))
    out("")
    out("%-30s %7s %9s %8s" % ("Group", "entries", "dangling", "matched"))
    covered = set()
    dangling_report = []
    for g in groups:
        dang, matched = [], set()
        for entry in g["types"]:
            hit = {d for d in defs if matches(entry, d)}
            if not hit:
                dang.append(entry)
            matched |= hit
        covered |= matched
        out("%-30s %7d %9d %8d" % (g["name"][:30], len(g["types"]), len(dang), len(matched)))
        if dang:
            dangling_report.append((g["name"], dang))
    if dangling_report:
        out("")
        out("Dangling entries (no scanned definition; a dependency mod may be missing from --blocks):")
        for name, dang in dangling_report:
            for (t, s, _w) in dang[: a.show]:
                out("  [%s] %s/%s" % (name, t, s or "(empty)"))
            if len(dang) > a.show:
                out("  [%s] ... %d more" % (name, len(dang) - a.show))
    if a.uncovered:
        want = {normalize_type(t) for t in a.uncovered}
        un = sorted(d for d in defs if d[0] in want and d not in covered)
        out("")
        out("Definitions of %s not counted by any group: %d" % (", ".join(sorted(want)), len(un)))
        for t in sorted(want):
            total = sum(1 for d in defs if d[0] == t)
            miss = sum(1 for d in un if d[0] == t)
            out("  %-24s %4d of %4d scanned definitions uncovered" % (t, miss, total))
        for t, s in un[: a.show]:
            out("  %s/%s" % (t, s or "(empty)"))
        if len(un) > a.show:
            out("  ... %d more" % (len(un) - a.show))
    return 0


if __name__ == "__main__":
    sys.exit(main())
