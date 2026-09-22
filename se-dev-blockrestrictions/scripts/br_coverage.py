#!/usr/bin/env python3
"""Which of a mod's cube blocks can Block Restrictions see?

Usage:
  br_coverage.py CFG MODDIR [MODDIR ...] [--missing] [--limit N]

Scans every .sbc under each MODDIR (recursively) for <CubeBlocks><Definition> entries and compares
'MyObjectBuilder_<TypeId>/<SubtypeId>' with the entries in a world's BlockRestrictions.cfg.
  in cfg      -> the block is a terminal-capable block the mod manages (restrictable).
  not in cfg  -> either (a) non-terminal (armor, plain CubeBlock, LCD-panel types are ignored by the
                 mod), or (b) the mod that defines it was not loaded in the world that produced the cfg.
Also reports cfg entries whose definition was not found in the scanned folders (informational only:
they may come from other mods or the base game).

Read-only. Stdlib only. Malformed .sbc files are skipped and counted.
"""
import argparse
import collections
import glob
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_common import load_cfg, out, parse_xml_text, read_text, split_type  # noqa: E402


def scan_defs(moddir):
    """Return (set of 'MyObjectBuilder_X/Sub', skipped_file_count, file_count)."""
    defs, skipped, files = set(), 0, 0
    for path in glob.glob(os.path.join(moddir, "**", "*.sbc"), recursive=True):
        files += 1
        try:
            root = parse_xml_text(read_text(path))
        except (OSError, ET.ParseError):
            skipped += 1
            continue
        # Only definitions nested directly under a CubeBlocks element are cube blocks.
        for cb in root.iter("CubeBlocks"):
            for d in cb.findall("Definition"):
                t = (d.findtext("./Id/TypeId") or "").strip()
                s = (d.findtext("./Id/SubtypeId") or "").strip()
                if t:
                    # Some files already write the full 'MyObjectBuilder_X' in <TypeId>.
                    if not t.startswith("MyObjectBuilder_"):
                        t = "MyObjectBuilder_" + t
                    # The cfg spells an empty SubtypeId as '(null)' (e.g. vanilla LargeGatlingTurret).
                    defs.add("%s/%s" % (t, s or "(null)"))
    return defs, skipped, files


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cfg")
    p.add_argument("moddirs", nargs="+")
    p.add_argument("--missing", action="store_true", help="list every block that is not in the cfg")
    p.add_argument("--limit", type=int, default=25, help="max rows per list (default 25)")
    a = p.parse_args()
    try:
        cfg_types = {s["Type"] for s in load_cfg(a.cfg)["settings"]}
    except (OSError, ValueError, ET.ParseError) as e:
        sys.stderr.write("error: %s\n" % e)
        return 2
    all_defs = set()
    for d in a.moddirs:
        if not os.path.isdir(d):
            sys.stderr.write("error: not a directory: %s\n" % d)
            return 2
        defs, skipped, files = scan_defs(d)
        inn = defs & cfg_types
        out("%s" % d)
        out("  %d .sbc files (%d unparseable, skipped); %d cube block definitions" % (files, skipped, len(defs)))
        out("  in cfg (restrictable): %d   not in cfg: %d" % (len(inn), len(defs) - len(inn)))
        miss = sorted(defs - cfg_types)
        c = collections.Counter(split_type(t)[0] for t in miss)
        if c:
            out("  not-in-cfg by TypeId: " + ", ".join("%s x%d" % (k.replace("MyObjectBuilder_", ""), v) for k, v in c.most_common(10)))
        if a.missing:
            for t in miss[: a.limit]:
                out("    - %s" % t)
            if len(miss) > a.limit:
                out("    ... %d more" % (len(miss) - a.limit))
        all_defs |= defs
    orphan = sorted(cfg_types - all_defs)
    out("cfg entries with no definition in the scanned folders: %d (of %d)" % (len(orphan), len(cfg_types)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
