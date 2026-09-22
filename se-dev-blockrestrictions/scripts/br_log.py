#!/usr/bin/env python3
"""Summarize a Block Restrictions log (BlockRestrictions.log) - did my default-settings EC apply?

Usage:
  br_log.py LOG [--show N]

Reports, from the load-time trace the mod writes on every world load:
  - config stage: how many cfg entries were accepted / had no loadable definition / cannot be restricted
  - per EntityComponent (BlockRestrictions*): entries seen, and how each was handled
      skipped (a setting already exists) / no definition loaded / added / restricted / parse errors
  - ERROR / WARNING lines and enforcement messages (blocks removed from grids)
The log is overwritten each world load, so it describes the most recent load only.
Read-only. Stdlib only.
"""
import argparse
import collections
import re
import sys

LINE_RE = re.compile(r"^\[[0-9:.]+\] \[T\d+\] \[DS=\w+\] (ERROR|WARNING|DEBUG|INFO) \| ?(.*)$")
SETTING_RE = re.compile(r"^(->)+ Setting = (\S+)")
EC_RE = re.compile(r"^-> Found EC: Subtype = (\S+)")
EC_COUNT_RE = re.compile(r"EC contains (\d+) settings")

EC_RESULTS = [
    ("skipped, setting already exists", "A setting already exists"),
    ("no definition loaded", "Unable to retrieve MyCubeBlockDefinition"),
    ("unparseable id", "Unable to parse MyDefinitionId"),
    ("empty type", "Type was null or empty"),
    ("cannot be restricted", "Type cannot be restricted"),
    ("added to restricted list", "Type added to the restricted list"),
    ("added", "Setting added successfully"),
]
CFG_RESULTS = [
    ("no definition loaded", "Unable to retrieve MyCubeBlockDefinition"),
    ("unparseable id", "Unable to parse MyDefinitionId"),
    ("cannot be restricted", "Definition cannot be restricted"),
    ("added to restricted list", "Definition added to restricted list"),
    ("accepted", "Setting added successfully"),
]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("log")
    p.add_argument("--show", type=int, default=5, help="max ERROR/WARNING/enforcement lines to print")
    a = p.parse_args()
    try:
        with open(a.log, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError as e:
        sys.stderr.write("error: %s\n" % e)
        return 2

    stage = None
    ec = None
    ecs = collections.OrderedDict()   # name -> {'declared': n, 'seen': n, 'res': Counter}
    cfg = collections.Counter()
    cfg_seen = 0
    problems, enforcement = [], []
    for raw in lines:
        m = LINE_RE.match(raw)
        text = m.group(2) if m else raw
        level = m.group(1) if m else None
        if level in ("ERROR", "WARNING"):
            problems.append(raw)
        if "Checking Config for saved settings" in text:
            stage = "cfg"
        elif "Checking Entity Components" in text:
            stage = "ec"
        elif "Finished with settings" in text:
            stage = None
        if level == "INFO" and re.search(r"not allowed|cannot have more|may only place", text):
            enforcement.append(raw)
        if stage == "cfg":
            if SETTING_RE.match(text) and text.startswith("-> "):
                cfg_seen += 1
            for label, needle in CFG_RESULTS:
                if needle in text:
                    cfg[label] += 1
        elif stage == "ec":
            mm = EC_RE.match(text)
            if mm:
                ec = mm.group(1)
                ecs[ec] = {"declared": None, "seen": 0, "res": collections.Counter()}
                continue
            if ec is None:
                continue
            mm = EC_COUNT_RE.search(text)
            if mm:
                ecs[ec]["declared"] = int(mm.group(1))
                continue
            if text.startswith("->->-> Setting = "):
                ecs[ec]["seen"] += 1
                continue
            for label, needle in EC_RESULTS:
                if needle in text:
                    ecs[ec]["res"][label] += 1
            if "Failed to deserialize XML" in text or "Error trying to deserialize" in text:
                ecs[ec]["res"]["DESERIALIZE FAILED"] += 1

    sys.stdout.write("Log: %s (%d lines)\n" % (a.log, len(lines)))
    sys.stdout.write("Config stage: %d cfg entries traced\n" % cfg_seen)
    for k, v in cfg.items():
        sys.stdout.write("  %-32s %d\n" % (k, v))
    if not ecs:
        sys.stdout.write("No BlockRestrictions* EntityComponent was found by the mod in this load.\n")
    for name, d in ecs.items():
        sys.stdout.write("EntityComponent %s: %s declared, %d traced\n" % (name, d["declared"], d["seen"]))
        for k, v in d["res"].items():
            sys.stdout.write("  %-32s %d\n" % (k, v))
    sys.stdout.write("ERROR/WARNING lines: %d\n" % len(problems))
    for l in problems[: a.show]:
        sys.stdout.write("  " + l[:200] + "\n")
    sys.stdout.write("Enforcement (block removed) messages: %d\n" % len(enforcement))
    for l in enforcement[: a.show]:
        sys.stdout.write("  " + l[:200] + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
