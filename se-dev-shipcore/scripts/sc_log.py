#!/usr/bin/env python3
"""Summarize what Ship Core Framework logged during a game session.

Usage:
  sc_log.py SpaceEngineers_YYYYMMDD_HHMMSS.log [--all-loads] [--show N]

Reads the game log (streams it; large files are fine) and reports, for the LAST world load in the file
(or every load with --all-loads): the content packs that supplied groups/manifest/no-core, the cores
loaded, config warnings (de-duplicated with counts), the no-core selection status, and any line that
mentions ShipCoreFramework together with an exception/error.
Log line format handled:  2026-09-18 20:34:41.722 - Thread:   1 ->  [Category]: message
Read-only. Stdlib only.
"""
import argparse
import collections
import os
import re
import sys

LOAD_RE = re.compile(r"Script loaded: \d+\.sbm_ShipCoreFramework")
LINE_RE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+) - Thread: *\d+ -> +(.*)$")
CAT_RE = re.compile(r"^\[(Ship Core Config|Config Validation|Config Sync)\]: (.*)$")
LOADED_CORE_RE = re.compile(r"^Loaded Core (.+) From: (.+)$")
GEN_RE = re.compile(r"(\d+)\b")
ERR_RE = re.compile(r"(exception|error|failed)", re.I)


def norm(msg):
    """Collapse repeated warnings that differ only by limit/core names so counts are meaningful."""
    msg = re.sub(r"ShipCore '[^']*'", "ShipCore '<core>'", msg)
    msg = re.sub(r"from [^()]+ \([^)]*\)", "from <mod> (<file>)", msg)
    msg = re.sub(r"limit '[^']*'", "limit '<limit>'", msg)
    return msg


def new_load(ts):
    return {"ts": ts, "packs": collections.OrderedDict(), "cores": [], "counts": {}, "msgs": collections.Counter(),
            "errors": [], "status": []}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("log")
    p.add_argument("--all-loads", action="store_true")
    p.add_argument("--show", type=int, default=10)
    a = p.parse_args()
    try:
        fh = open(a.log, "r", encoding="utf-8", errors="replace")
    except OSError as e:
        sys.stderr.write("error: %s\n" % e)
        return 2
    loads = []
    cur = None
    with fh:
        for raw in fh:
            if "ShipCoreFramework" not in raw and "[Ship Core Config]" not in raw and "[Config Validation]" not in raw \
                    and "[Config Sync]" not in raw:
                continue
            m = LINE_RE.match(raw.rstrip("\n"))
            ts, body = (m.group(1), m.group(2)) if m else ("", raw.strip())
            if LOAD_RE.search(body):
                cur = new_load(ts)
                loads.append(cur)
                continue
            if cur is None:
                cur = new_load(ts)
                loads.append(cur)
            cm = CAT_RE.match(body)
            if cm:
                cat, msg = cm.group(1), cm.group(2)
                lc = LOADED_CORE_RE.match(msg)
                if lc:
                    cur["cores"].append((lc.group(1), lc.group(2)))
                elif msg.startswith("Loaded Groups From:") or msg.startswith("Loaded No-Core Config From:") or \
                        msg.startswith("Found Manifest in:"):
                    kind, src = msg.split(":", 1)
                    cur["packs"].setdefault(src.strip(), []).append(kind)
                elif re.match(r"^\w+(\.\w+)? = \d+$", msg) or re.match(r"^[A-Za-z]+\.Count = \d+$", msg):
                    k, v = msg.split("=")
                    cur["counts"][k.strip()] = v.strip()
                elif "no-core profile" in msg or "no-core" in msg.lower():
                    cur["status"].append(msg)
                else:
                    cur["msgs"][(cat, norm(msg))] += 1
            elif ERR_RE.search(body) and "ShipCoreFramework" in body and "Script loaded" not in body \
                    and "Registered modules" not in body and "Loading Mod Assembly" not in body:
                cur["errors"].append(body[:220])
    if not loads:
        sys.stdout.write("No Ship Core Framework lines found in %s (mod not loaded in that session, or a different log).\n" % a.log)
        return 1
    show = loads if a.all_loads else loads[-1:]
    sys.stdout.write("%s: %d load(s) of Ship Core Framework found\n" % (os.path.basename(a.log), len(loads)))
    for i, ld in enumerate(show, 1):
        sys.stdout.write("\n--- load %s (started %s)\n" % ("#%d" % (loads.index(ld) + 1), ld["ts"] or "?"))
        for src, kinds in ld["packs"].items():
            sys.stdout.write("pack %-30s %s\n" % (src, ", ".join(sorted(set(kinds)))))
        sys.stdout.write("cores loaded: %d\n" % len(ld["cores"]))
        for name, src in ld["cores"][: a.show]:
            sys.stdout.write("  %s  (%s)\n" % (name, src))
        if len(ld["cores"]) > a.show:
            sys.stdout.write("  ... %d more\n" % (len(ld["cores"]) - a.show))
        if ld["counts"]:
            sys.stdout.write("counts: " + ", ".join("%s=%s" % kv for kv in ld["counts"].items()) + "\n")
        if ld["status"]:
            for s in dict.fromkeys(ld["status"]):
                sys.stdout.write("STATUS: %s\n" % s)
        for (cat, msg), n in ld["msgs"].most_common(a.show):
            sys.stdout.write("%5dx [%s] %s\n" % (n, cat, msg[:200]))
        if ld["errors"]:
            sys.stdout.write("error-like lines mentioning ShipCoreFramework: %d\n" % len(ld["errors"]))
            for e in ld["errors"][: a.show]:
                sys.stdout.write("  " + e + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
