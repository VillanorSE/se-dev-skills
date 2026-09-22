#!/usr/bin/env python3
"""Summarize the cores in one or more Ship Core Framework content packs.

Usage:
  sc_report.py PACKDIR [PACKDIR ...] [--world-speed 300] [--csv]
  sc_report.py PACKDIR [...] --limits "<core UniqueName or SubtypeId>"

Default: one row per core (also the no-core profile) with hard caps, per-player/faction counts, effective
top speed (SpeedModifiers.MaxSpeed x world speed, SpeedLimitType Normal), gyro/thruster multipliers, the
number of block limits and manifest groups.
--limits: list that core's block limits with the groups each one counts, MaxCount, punishment and directions.
Read-only. Stdlib only. Blank cell = element absent (the framework's default applies).
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_common import DEFAULT_WORLD_SPEED, load_pack, out, txt  # noqa: E402


def cell(root, tag):
    v = root.findtext(tag)
    return "" if v is None else v.strip()


def core_row(root, ent, world_speed, nocore=False):
    sm = root.find("SpeedModifiers")
    mods = root.find("Modifiers")
    speed = ""
    if sm is not None and sm.findtext("MaxSpeed") is not None:
        try:
            speed = "%.0f" % (float(sm.findtext("MaxSpeed")) * world_speed)
        except ValueError:
            speed = "?"
    elif sm is None:
        speed = "%.0f" % (0.3 * world_speed)  # SpeedModifiers.MaxSpeed default 0.3
    return {
        "UniqueName": cell(root, "UniqueName") + (" [no-core]" if nocore else ""),
        "SubtypeId": cell(root, "SubtypeId"),
        "Mobility": cell(root, "MobilityType") or "Both",
        "MaxBlocks": cell(root, "MaxBlocks"), "MinBlocks": cell(root, "MinBlocks"),
        "MaxPCU": cell(root, "MaxPCU"), "MaxMass": cell(root, "MaxMass"),
        "PerPlayer": cell(root, "MaxPerPlayer"), "PerFaction": cell(root, "MaxPerFaction"),
        "TopSpeed": speed, "SpeedType": cell(root, "SpeedLimitType") or "Normal",
        "Gyro": cell(mods, "GyroForce") if mods is not None else "",
        "Thrust": cell(mods, "ThrusterForce") if mods is not None else "",
        "Limits": str(len(root.findall("BlockLimits"))),
        "Groups": ",".join(ent["groups"]) if ent else "",
        "Prio": str(ent["priority"]) if ent else "",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("packs", nargs="+")
    p.add_argument("--world-speed", type=float, default=DEFAULT_WORLD_SPEED,
                   help="MaxPossibleSpeedMetersPerSecond of the world (default 300)")
    p.add_argument("--csv", action="store_true")
    p.add_argument("--limits", metavar="CORE")
    a = p.parse_args()
    rows, cores = [], []
    for d in a.packs:
        if not os.path.isdir(d):
            sys.stderr.write("error: not a directory: %s\n" % d)
            return 2
        pk = load_pack(d)
        for e in pk["errors"]:
            sys.stderr.write("warning: %s\n" % e)
        if pk["nocore"] is not None and pk["nocore"].tag == "ShipCore":
            cores.append((pk["nocore"], None, True))
        for c in pk["cores"]:
            if c["root"] is not None and c["root"].tag == "ShipCore":
                cores.append((c["root"], c["entry"], False))
    if a.limits:
        want = a.limits.strip().lower()
        hit = [c for c in cores if txt(c[0], "UniqueName").lower() == want or txt(c[0], "SubtypeId").lower() == want]
        if not hit:
            sys.stderr.write("error: no core with UniqueName/SubtypeId '%s'\n" % a.limits)
            return 2
        root = hit[0][0]
        out("%s (%s)  MaxBlocks=%s MaxPCU=%s MaxMass=%s" % (txt(root, "UniqueName"), txt(root, "SubtypeId"),
                                                            cell(root, "MaxBlocks") or "-", cell(root, "MaxPCU") or "-",
                                                            cell(root, "MaxMass") or "-"))
        out("%-28s %-8s %-10s %-9s %s" % ("Limit", "MaxCount", "Punish", "Flags", "Groups / directions"))
        for bl in root.findall("BlockLimits"):
            groups = [(g.text or "").strip() + ("[" + g.get("Directions") + "]" if g.get("Directions") else "")
                      for g in bl.findall("BlockGroups")]
            excl = [(g.text or "").strip() for g in bl.findall("ExcludedBlockGroups")]
            dirs = [(d.text or "").strip() for d in bl.findall("AllowedDirections")]
            flags = "".join(f for f, t in (("C", "IsCriticalLimit"), ("N", "IgnoredByNpc"), ("F", "PunishByNoFlyZone"),
                                           ("X", "CrossConnectorPunishment")) if cell(bl, t) == "true")
            extra = ""
            if excl:
                extra += " excl=" + ",".join(excl)
            if dirs:
                extra += " dirs=" + ",".join(dirs)
            if cell(bl, "MaxCountPerDirection"):
                extra += " perDir=" + cell(bl, "MaxCountPerDirection")
            out("%-28s %-8s %-10s %-9s %s%s" % (txt(bl, "Name")[:28], cell(bl, "MaxCount") or "0*",
                                                 cell(bl, "PunishmentType") or "ShutOff*", flags or "-",
                                                 ",".join(groups) or "(none)", extra))
        out("* = element absent, framework default.  Flags: C=critical N=ignored-by-NPC F=no-fly-zone X=cross-connector")
        return 0
    for root, ent, nc in cores:
        rows.append(core_row(root, ent, a.world_speed, nc))
    if not rows:
        sys.stderr.write("no cores found\n")
        return 2
    cols = list(rows[0].keys())
    if a.csv:
        w = csv.writer(sys.stdout, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] for c in cols])
        return 0
    widths = {c: max(len(c), max(len(r[c]) for r in rows)) for c in cols}
    out("  ".join(c.ljust(widths[c]) for c in cols))
    for r in sorted(rows, key=lambda r: (r["UniqueName"].endswith("[no-core]"), r["UniqueName"])):
        out("  ".join(r[c].ljust(widths[c]) for c in cols))
    out("TopSpeed = MaxSpeed x %g m/s (world speed); only meaningful when SpeedType is Normal. Blank = default." % a.world_speed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
