#!/usr/bin/env python3
"""Lint Ship Core Framework content packs the way the framework's loader reads them.

Usage:
  sc_lint.py PACKDIR [PACKDIR ...] [--world ShipCoreConfig_World.xml] [--blocks MODDIR ...] [--quiet]

PACKDIR is a mod folder that contains Data\\ShipCoreConfig_Manifest.xml (and usually _Groups.xml and
_No_Core.xml). Pass every pack loaded in one world together: duplicate names are only detected
across packs when they are linted together, exactly as the loader sees them.

Severity:
  ERROR  the loader throws or XmlSerializer cannot read the file (config fails to load)
  WARN   the loader logs a warning, or the config is almost certainly not what you meant
  INFO   worth knowing
Exit code 0 = no ERROR, 1 = at least one ERROR, 2 = bad usage/unreadable input. Read-only.
"""
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_common import (ENUMS, load_pack, normalize_type, out, parse_file, scan_cube_blocks, txt)  # noqa: E402

CORE_INT = {"MaxBackupCores", "MaxBlocks", "MinBlocks", "MaxPCU", "MaxPerFaction", "FactionPlayersNeededPerCore",
            "MaxPerPlayer", "MinPlayers", "MaxPlayers", "SpeedOverridePriority"}
CORE_FLOAT = {"ForceBroadCastRange", "MaxMass", "PowerOverclockMultiplier", "PowerOverclockDuration",
              "PowerOverclockCooldown", "PowerOverclockDamagePerSecond"}
CORE_BOOL = {"ForceBroadCast", "SpeedBoostEnabled", "EnableActiveDefenseModifiers", "PowerOverclockEnabled"}
CORE_ENUM = {"MobilityType": "MobilityType", "SpeedLimitType": "SpeedLimitType",
             "SpeedOverrideMode": "SpeedOverrideMode", "MinFactionRank": "FactionRank"}
CORE_KNOWN = (CORE_INT | CORE_FLOAT | CORE_BOOL | set(CORE_ENUM) |
              {"SubtypeId", "UniqueName", "AllowedUpgradeModules", "Modifiers", "PassiveDefenseModifiers",
               "SpeedModifiers", "ActiveDefenseModifiers", "BlockLimits"})
LIMIT_KNOWN = {"Name", "BlockGroups", "ExcludedBlockGroups", "MaxCount", "MaxCountPerDirection", "DirectionBudgets",
               "LimitVisibility", "CrossConnectorPunishment", "PunishByNoFlyZone", "IsCriticalLimit", "IgnoredByNpc",
               "PunishmentType", "AllowedDirections"}
LIMIT_BOOL = {"CrossConnectorPunishment", "PunishByNoFlyZone", "IsCriticalLimit", "IgnoredByNpc"}
MODIFIERS_KNOWN = {"AssemblerSpeed", "DrillHarvestMultiplier", "GyroEfficiency", "GyroForce", "PowerProducersOutput",
                   "RefineEfficiency", "RefineSpeed", "ThrusterEfficiency", "ThrusterForce"}
DEFENSE_KNOWN = {"Bullet", "PostShield", "Duration", "Cooldown", "Rocket", "Explosion", "Environment", "Energy",
                 "Kinetic"}
SPEED_KNOWN = {"MaxSpeed", "MaxAngularVelocity", "MaxBoost", "BoostDuration", "BoostCoolDown",
               "MinimumFrictionSpeedAbsolute", "MaximumFrictionSpeedAbsolute", "MinimumFrictionSpeedModifier",
               "MaximumFrictionSpeedModifier", "MaximumFrictionDeceleration", "CruiseFrictionMultiplier",
               "CruiseAccelerationThreshold", "FrictionCurve", "AtmosphericFriction"}
UPGRADE_ALLOW_KNOWN = {"TypeId", "UniqueName", "SubtypeId", "MaxCount"}

INT_RE = re.compile(r"^[+-]?\d+$")
FLOAT_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


class Report:
    def __init__(self):
        self.items = []

    def add(self, sev, where, msg):
        self.items.append((sev, where, msg))

    def count(self, sev):
        return sum(1 for i in self.items if i[0] == sev)


def check_scalar(rep, where, elem, tag, kind):
    v = elem.findtext(tag)
    if v is None:
        return
    v = v.strip()
    if kind == "int" and not INT_RE.match(v):
        rep.add("ERROR", where, "<%s>%s</%s> is not an integer (XmlSerializer cannot read it)" % (tag, v, tag))
    elif kind == "float" and not FLOAT_RE.match(v):
        rep.add("ERROR", where, "<%s>%s</%s> is not a number (XmlSerializer cannot read it)" % (tag, v, tag))
    elif kind == "bool" and v not in ("true", "false", "1", "0"):
        rep.add("ERROR", where, "<%s>%s</%s> is not true/false (XmlSerializer accepts lower-case true/false/1/0)" % (tag, v, tag))


def check_enum(rep, where, tag, value, enum):
    if value not in ENUMS[enum]:
        hint = ""
        if "," in value:
            hint = " - comma-joined values are invalid; repeat the element, one value each"
        elif value.lower() in [x.lower() for x in ENUMS[enum]]:
            hint = " - enum text is case-sensitive"
        rep.add("ERROR", where, "<%s>%s</%s> is not a valid %s (%s)%s" %
                (tag, value, tag, enum, "/".join(ENUMS[enum]), hint))


def unknown_children(rep, where, elem, known, what):
    for c in elem:
        if c.tag not in known:
            rep.add("WARN", where, "unknown element <%s> inside %s is silently ignored by XmlSerializer (typo?)" %
                    (c.tag, what))


def lint_core(rep, where, root, group_names, is_nocore=False):
    if root is None:
        return
    if root.tag != "ShipCore":
        rep.add("ERROR", where, "root element is <%s>, expected <ShipCore>" % root.tag)
        return
    unknown_children(rep, where, root, CORE_KNOWN, "<ShipCore>")
    if not txt(root, "UniqueName"):
        rep.add("WARN", where, "no <UniqueName>")
    if not txt(root, "SubtypeId"):
        rep.add("WARN", where, "no <SubtypeId>: the core cannot be matched to a block")
    for t in CORE_INT:
        check_scalar(rep, where, root, t, "int")
    for t in CORE_FLOAT:
        check_scalar(rep, where, root, t, "float")
    for t in CORE_BOOL:
        check_scalar(rep, where, root, t, "bool")
    for tag, enum in CORE_ENUM.items():
        v = root.findtext(tag)
        if v is not None:
            check_enum(rep, where, tag, v.strip(), enum)
    for tag, known in (("Modifiers", MODIFIERS_KNOWN), ("PassiveDefenseModifiers", DEFENSE_KNOWN),
                       ("ActiveDefenseModifiers", DEFENSE_KNOWN), ("SpeedModifiers", SPEED_KNOWN)):
        sub = root.find(tag)
        if sub is None:
            continue
        unknown_children(rep, where, sub, known, "<%s>" % tag)
        for c in sub:
            if c.tag in known and len(c) == 0:
                check_scalar(rep, where, sub, c.tag, "float")
    # AllowedUpgradeModules: duplicates throw
    seen = {}
    for a in root.findall("AllowedUpgradeModules"):
        unknown_children(rep, where, a, UPGRADE_ALLOW_KNOWN, "<AllowedUpgradeModules>")
        key = (txt(a, "TypeId") or "UpgradeModule", txt(a, "SubtypeId")) if txt(a, "SubtypeId") else ("", txt(a, "UniqueName"))
        if key[1] and key in seen:
            rep.add("ERROR", where, "duplicate <AllowedUpgradeModules> entry for %s (loader throws)" % "/".join(k for k in key if k))
        seen[key] = True
    # BlockLimits
    limit_names = {}
    for bl in root.findall("BlockLimits"):
        lname = txt(bl, "Name") or "(unnamed)"
        lw = "%s / limit '%s'" % (where, lname)
        unknown_children(rep, lw, bl, LIMIT_KNOWN, "<BlockLimits>")
        if not txt(bl, "Name"):
            rep.add("WARN", lw, "no <Name>")
        limit_names[lname] = limit_names.get(lname, 0) + 1
        for t in LIMIT_BOOL:
            check_scalar(rep, lw, bl, t, "bool")
        for t in ("MaxCount", "MaxCountPerDirection"):
            check_scalar(rep, lw, bl, t, "float")
        v = bl.findtext("PunishmentType")
        if v is not None:
            check_enum(rep, lw, "PunishmentType", v.strip(), "PunishmentType")
        v = bl.findtext("LimitVisibility")
        if v is not None:
            check_enum(rep, lw, "LimitVisibility", v.strip(), "LimitVisibility")
        allowed = []
        for ad in bl.findall("AllowedDirections"):
            val = (ad.text or "").strip()
            check_enum(rep, lw, "AllowedDirections", val, "DirectionType")
            if val in ENUMS["DirectionType"]:
                allowed.append(val)
        # group references
        refs = bl.findall("BlockGroups")
        excl = bl.findall("ExcludedBlockGroups")
        if not refs:
            rep.add("WARN", lw, "no <BlockGroups>: the limit matches no block, so it never counts or restricts anything")
        ref_names = []
        override_dirs = []
        for r in refs:
            nm = (r.text or "").strip()
            ref_names.append(nm)
            d = r.get("Directions")
            if d is not None:
                bad = [t.strip() for t in d.split(",") if t.strip() and t.strip().lower() not in [x.lower() for x in ENUMS["DirectionType"]]]
                if bad:
                    rep.add("WARN", lw, "Directions attribute on '%s' has invalid value(s) %s; loader ignores them" % (nm, ", ".join(bad)))
                override_dirs += [t.strip().capitalize() for t in d.split(",") if t.strip()]
            if group_names is not None and nm and nm.lower() not in group_names:
                rep.add("WARN", lw, "references unknown BlockGroup '%s' (loader logs a warning and the group is ignored)" % nm)
        excl_names = [(e.text or "").strip() for e in excl]
        for nm in excl_names:
            if group_names is not None and nm and nm.lower() not in group_names:
                rep.add("WARN", lw, "ExcludedBlockGroups references unknown BlockGroup '%s'" % nm)
        both = {n.lower() for n in ref_names} & {n.lower() for n in excl_names}
        if both:
            rep.add("INFO", lw, "includes and excludes %s; exclusion wins" % ", ".join(sorted(both)))
        # MaxCount semantics
        mc = bl.findtext("MaxCount")
        if mc is None:
            rep.add("INFO", lw, "no <MaxCount>: defaults to 0, i.e. zero of these blocks allowed")
        else:
            try:
                if float(mc) < 0:
                    rep.add("WARN", lw, "negative MaxCount: every counted block exceeds it (this is not 'unlimited'; omit the limit instead)")
            except ValueError:
                pass
        # direction budgets (ModConfig.ValidateDirectionBudgets)
        budgets = bl.findall("./DirectionBudgets/DirectionBudget")
        mpd = bl.findtext("MaxCountPerDirection")
        try:
            mpd_f = float(mpd) if mpd is not None else -1.0
        except ValueError:
            mpd_f = -1.0
        if budgets or mpd_f >= 0:
            try:
                mc_f = float(mc) if mc is not None else 0.0
            except ValueError:
                mc_f = 0.0
            if mc_f < 0:
                rep.add("ERROR", lw, "DirectionBudgets/MaxCountPerDirection require a finite, non-negative MaxCount (loader throws)")
            if mpd_f < 0 and mpd_f != -1.0:
                rep.add("ERROR", lw, "MaxCountPerDirection must be -1 or non-negative (loader throws)")
            dirs = {}
            for b in budgets:
                d = b.get("Direction", "Any")
                try:
                    mcv = float(b.get("MaxCount", "-1"))
                except ValueError:
                    mcv = -1.0
                if d not in ENUMS["DirectionType"] or d == "Any":
                    rep.add("ERROR", lw, "DirectionBudget Direction '%s' invalid; use one of the six specific directions (loader throws)" % d)
                    continue
                if d in dirs:
                    rep.add("ERROR", lw, "duplicate DirectionBudget for %s (loader throws)" % d)
                if mcv < 0:
                    rep.add("ERROR", lw, "DirectionBudget for %s needs a non-negative MaxCount (loader throws)" % d)
                dirs[d] = mcv
            # directions that share the budget: those allowed by AllowedDirections / per-group overrides
            six = ["Forward", "Backward", "Up", "Down", "Left", "Right"]

            def expand(lst):
                if not lst or "Any" in lst:
                    return set(six)
                return {x for x in lst if x in six}
            union = set()
            if not refs:
                union |= expand(allowed)
            else:
                for r in refs:
                    d = r.get("Directions")
                    union |= expand([t.strip().capitalize() for t in d.split(",")]) if d is not None else expand(allowed)
            union |= set(dirs)
            total = sum((dirs[d] if d in dirs else mpd_f) for d in union if (dirs.get(d, mpd_f) >= 0))
            if total > mc_f:
                rep.add("ERROR", lw, "direction caps total %g (including inherited caps) exceed MaxCount %g (loader throws)" % (total, mc_f))
            if mpd_f >= 0 and not (set(allowed) - {"Any"} or override_dirs):
                rep.add("WARN", lw, "MaxCountPerDirection set but no specific direction in AllowedDirections or a Directions attribute")
    return


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("packs", nargs="+")
    p.add_argument("--world", help="a ShipCoreConfig_World.xml to check against the loaded no-core profiles")
    p.add_argument("--blocks", nargs="*", default=[], help="mod folders to scan for cube block definitions (core SubtypeIds are checked against them)")
    p.add_argument("--quiet", action="store_true", help="only print WARN/ERROR")
    a = p.parse_args()

    rep = Report()
    packs = []
    for d in a.packs:
        if not os.path.isdir(d):
            sys.stderr.write("error: not a directory: %s\n" % d)
            return 2
        pk = load_pack(d)
        packs.append(pk)
        for e in pk["errors"]:
            rep.add("ERROR", d, e)
        if pk["manifest"] is None and not os.path.isfile(os.path.join(d, "Data", "ShipCoreConfig_Manifest.xml")):
            rep.add("INFO", d, "no Data\\ShipCoreConfig_Manifest.xml: this pack contributes no cores")

    # ---- block groups (global names; duplicates throw)
    group_names = None
    all_groups = []
    for pk in packs:
        if pk["groups"] is not None:
            group_names = group_names or set()
            for g in pk["groups"]:
                all_groups.append((pk["dir"], g))
    if all_groups:
        counts = {}
        for d, g in all_groups:
            n = g["name"]
            if not n:
                rep.add("WARN", d, "a <BlockGroup> has no <Name>")
            counts.setdefault(n.lower(), []).append(d)
            group_names.add(n.lower())
            if not g["types"]:
                rep.add("WARN", "%s / group '%s'" % (d, n), "no <BlockTypes>: group is empty")
            for (t, s, w) in g["types"]:
                if not t:
                    rep.add("WARN", "%s / group '%s'" % (d, n), "a <BlockTypes> entry has no <TypeId>")
                if w <= 0:
                    rep.add("INFO", "%s / group '%s'" % (d, n), "%s/%s has CountWeight %g; weight <= 0 never counts" % (t, s, w))
        for n, where in counts.items():
            if len(where) > 1:
                rep.add("ERROR", ", ".join(sorted(set(where))), "duplicate BlockGroup Name '%s' x%d (loader throws)" % (n, len(where)))

    # ---- manifest groups, cores, no-cores
    manifest_groups = {}
    for pk in packs:
        if pk["manifest"]:
            for g in pk["manifest"]["groups"]:
                where = "%s manifest group '%s'" % (pk["dir"], g["name"])
                if not g["name"]:
                    rep.add("ERROR", pk["dir"], "manifest group with no <Name> (loader throws)")
                if g["max"] < 0:
                    rep.add("ERROR", where, "needs a non-negative <MaxCount> (loader throws; a missing element counts as -1)")
                manifest_groups.setdefault(g["name"].lower(), []).append(pk["dir"])
    for n, w in manifest_groups.items():
        if len(w) > 1:
            rep.add("ERROR", ", ".join(sorted(set(w))), "duplicate manifest group '%s' (loader throws)" % n)

    unique_names, subtype_ids, nocore_names = {}, {}, {}
    all_core_subtypes = set()
    for pk in packs:
        if pk["nocore"] is not None:
            w = "%s no-core" % pk["dir"]
            lint_core(rep, w, pk["nocore"], group_names, True)
            nn = txt(pk["nocore"], "UniqueName")
            nocore_names.setdefault(nn.lower(), []).append(pk["dir"])
        if not pk["manifest"]:
            continue
        for c in pk["cores"]:
            ent = c["entry"]
            if not ent["filename"]:
                rep.add("WARN", pk["dir"], "manifest <ShipCore> entry without <Filename> is ignored")
                continue
            if c["path"] is None:
                rep.add("WARN", pk["dir"], "core file '%s' is listed in the manifest but cannot be found (loader logs a warning and skips it)" % ent["filename"])
                continue
            w = "%s core %s" % (pk["dir"], ent["filename"])
            for g in ent["groups"]:
                if g.lower() not in manifest_groups:
                    rep.add("ERROR", w, "references unknown manifest group '%s' (loader throws)" % g)
            lint_core(rep, w, c["root"], group_names)
            if c["root"] is not None and c["root"].tag == "ShipCore":
                un = txt(c["root"], "UniqueName")
                st = txt(c["root"], "SubtypeId")
                unique_names.setdefault(un, []).append(w)
                subtype_ids.setdefault(st, []).append(w)
                if st:
                    all_core_subtypes.add(st)
    for un, where in unique_names.items():
        if len(where) > 1:
            rep.add("ERROR", "; ".join(where), "duplicate ShipCore UniqueName '%s' (loader throws)" % un)
    for st, where in subtype_ids.items():
        if st and len(where) > 1:
            rep.add("WARN", "; ".join(where), "SubtypeId '%s' used by %d cores; lookups by SubtypeId return the first" % (st, len(where)))
    for nn, where in nocore_names.items():
        if len(where) > 1:
            rep.add("ERROR", ", ".join(where), "duplicate no-core UniqueName '%s' (loader throws)" % nn)
    # blacklist references
    for pk in packs:
        if pk["manifest"]:
            for ent in pk["manifest"]["cores"]:
                for b in ent["blacklist"]:
                    if b not in all_core_subtypes:
                        rep.add("INFO", "%s core %s" % (pk["dir"], ent["filename"]), "BlacklistedCoreSubtypeId '%s' matches no loaded core (may live in another pack)" % b)

    # ---- optional: core SubtypeIds against block definitions
    if a.blocks:
        defs = set()
        for d in a.blocks:
            if not os.path.isdir(d):
                sys.stderr.write("error: not a directory: %s\n" % d)
                return 2
            got, _bad, _n = scan_cube_blocks(d)
            defs |= got
        subs = {s for (_t, s) in defs}
        for st, where in subtype_ids.items():
            if st and st not in subs:
                rep.add("WARN", where[0], "core SubtypeId '%s' matches no cube block definition in the scanned folders" % st)

    # ---- optional: world file
    if a.world:
        try:
            wr = parse_file(a.world)
        except (OSError, ET.ParseError) as e:
            sys.stderr.write("error: %s\n" % e)
            return 2
        w = "world config"
        if wr.tag != "ModConfig":
            rep.add("ERROR", w, "root element is <%s>, expected <ModConfig>" % wr.tag)
        else:
            sel = txt(wr, "SelectedNoCoreUniqueName")
            if not sel:
                rep.add("WARN", w, "SelectedNoCoreUniqueName is empty: the framework reports its configuration as unavailable "
                                   "('No content-pack no-core profile is selected') until an admin runs /core select <name> and reloads")
            elif sel.lower() not in nocore_names:
                rep.add("WARN", w, "SelectedNoCoreUniqueName '%s' matches no no-core profile in the linted packs (%s)" %
                        (sel, ", ".join(sorted(nocore_names)) or "none"))
            for tag, lo, hi in (("MaxPossibleSpeedMetersPerSecond", 0.0000001, 10000), ("SpeedRampDownPercentage", 0, 100),
                                ("NoCoreGraceSeconds", 0, 3600), ("MinimumBlocksGraceSeconds", 0, 3600)):
                v = wr.findtext(tag)
                if v is None:
                    continue
                try:
                    f = float(v)
                    if f < lo or f > hi:
                        rep.add("WARN", w, "%s=%s is outside the accepted range (framework falls back to/clamps to a default)" % (tag, v))
                except ValueError:
                    rep.add("ERROR", w, "<%s>%s</%s> is not a number" % (tag, v, tag))

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    shown = 0
    for sev, where, msg in sorted(rep.items, key=lambda x: (order[x[0]], x[1])):
        if a.quiet and sev == "INFO":
            continue
        out("%-5s %s: %s" % (sev, where, msg))
        shown += 1
    out("Packs: %d | BlockGroups: %d | cores: %d | no-core profiles: %d | ERROR %d, WARN %d, INFO %d" % (
        len(packs), len(all_groups), sum(len(v) for v in unique_names.values()), len(nocore_names),
        rep.count("ERROR"), rep.count("WARN"), rep.count("INFO")))
    return 1 if rep.count("ERROR") else 0


if __name__ == "__main__":
    sys.exit(main())
