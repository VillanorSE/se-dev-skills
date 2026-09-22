#!/usr/bin/env python3
"""Generate or check a Block Restrictions "default settings" EntityComponent (.sbc).

Usage:
  br_ec.py generate [TYPE/SUBTYPE ...] [--input FILE] [--subtype-id NAME] [--force]
                    [--player true|false] [--npc true|false] [--unowned true|false]
                    [--player-static-only] [--npc-static-only] [--unowned-static-only]
                    [--max-player N] [--max-grid N] [--max-faction N] [--output FILE]
  br_ec.py check FILE.sbc [--cfg BlockRestrictions.cfg]

generate  Writes the .sbc text (stdout, or --output). TYPE/SUBTYPE is 'MyObjectBuilder_Beacon/Name'
          (prefix optional: 'Beacon/Name'). --input reads one entry per line ('#' comments allowed).
check     Parses every BlockRestrictions* EntityComponent in FILE.sbc, converts the [ ] tags back to
          < >, and validates them the way the mod's loader does. With --cfg it also reports which
          entries the mod would skip because the cfg already has a setting for that block.

Stdlib only. Read-only except --output.
"""
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_common import (BOOL_FIELDS, INT_FIELDS, load_cfg, out, parse_xml_text,  # noqa: E402
                       read_text, setting_from_element)

PREFIX = "MyObjectBuilder_"
FIELD_ORDER = ["PlayerMaxCount", "GridMaxCount", "FactionMaxCount", "AllowedForNPC", "AllowedForPlayer",
               "AllowedForUnowned", "AllowedForNPCStaticOnly", "AllowedForPlayerStaticOnly",
               "AllowedForUnownedStaticOnly"]
TYPE_RE = re.compile(r"^MyObjectBuilder_[A-Za-z0-9_]+/[^/\s<>\[\]]+$")


def norm_type(t):
    t = t.strip()
    if "/" in t and not t.startswith(PREFIX):
        t = PREFIX + t
    return t


def tf(v):
    return "true" if v else "false"


def build(types, a):
    vals = {
        "PlayerMaxCount": a.max_player, "GridMaxCount": a.max_grid, "FactionMaxCount": a.max_faction,
        "AllowedForNPC": tf(a.npc == "true"), "AllowedForPlayer": tf(a.player == "true"),
        "AllowedForUnowned": tf(a.unowned == "true"),
        "AllowedForNPCStaticOnly": tf(a.npc_static_only), "AllowedForPlayerStaticOnly": tf(a.player_static_only),
        "AllowedForUnownedStaticOnly": tf(a.unowned_static_only),
    }
    L = []
    L.append('<?xml version="1.0"?>')
    L.append('<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">')
    L.append("\t<EntityComponents>")
    L.append('\t\t<EntityComponent xsi:type="MyObjectBuilder_InventoryComponentDefinition">')
    L.append("\t\t\t<Id>")
    L.append("\t\t\t\t<TypeId>Inventory</TypeId>")
    L.append("\t\t\t\t<SubtypeId>%s</SubtypeId>" % a.subtype_id)
    L.append("\t\t\t</Id>")
    L.append("\t\t\t<Description>")
    L.append('\t\t\t[?xml version="1.0" encoding="utf-16"?]')
    L.append('\t\t\t[DefaultSettings xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"]')
    if a.force:
        L.append("\t\t\t\t[ForceSetting]true[/ForceSetting]")
    for t in types:
        L.append("\t\t\t\t[DefaultSetting]")
        L.append("\t\t\t\t\t[Type]%s[/Type]" % t)
        for f in FIELD_ORDER:
            L.append("\t\t\t\t\t[%s]%s[/%s]" % (f, vals[f], f))
        L.append("\t\t\t\t[/DefaultSetting]")
    L.append("\t\t\t[/DefaultSettings]")
    L.append("\t\t\t</Description>")
    L.append("\t\t</EntityComponent>")
    L.append("\t</EntityComponents>")
    L.append("</Definitions>")
    return "\n".join(L) + "\n"


def cmd_generate(a):
    if not a.subtype_id.startswith("BlockRestrictions"):
        sys.stderr.write("error: --subtype-id must start with 'BlockRestrictions' (the mod only reads ECs whose "
                         "SubtypeId starts with that text)\n")
        return 2
    raw = list(a.types)
    if a.input:
        for line in read_text(a.input).splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                raw.append(line)
    types, bad, seen = [], [], set()
    for t in raw:
        n = norm_type(t)
        if not TYPE_RE.match(n):
            bad.append(t)
        elif n not in seen:
            seen.add(n)
            types.append(n)
    if bad:
        sys.stderr.write("error: not a TypeId/SubtypeId pair: %s\n" % ", ".join(bad))
        return 2
    if not types:
        sys.stderr.write("error: no block types given\n")
        return 2
    text = build(types, a)
    if a.output:
        with open(a.output, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        sys.stderr.write("wrote %d entr%s to %s\n" % (len(types), "y" if len(types) == 1 else "ies", a.output))
    else:
        sys.stdout.write(text)
    return 0


def cmd_check(a):
    problems = 0
    try:
        root = parse_xml_text(read_text(a.file))
    except (OSError, ET.ParseError) as e:
        sys.stderr.write("error: %s\n" % e)
        return 2
    existing = None
    if a.cfg:
        existing = {s["Type"] for s in load_cfg(a.cfg)["settings"]}
    found = 0
    for ec in root.iter("EntityComponent"):
        sid = (ec.findtext("./Id/SubtypeId") or "").strip()
        if not sid.startswith("BlockRestrictions"):
            continue
        found += 1
        out("EntityComponent %s" % sid)
        desc = ec.findtext("Description") or ""
        # The mod turns '[' into '<' and ']' into '>' before deserializing (BlockRestrictions.cs, BeforeStart).
        xml = desc.replace("[", "<").replace("]", ">").strip()
        try:
            ds = parse_xml_text(xml)
        except ET.ParseError as e:
            out("  ERROR: description does not deserialize as XML after [ ]->< > conversion: %s" % e)
            problems += 1
            continue
        if ds.tag != "DefaultSettings":
            out("  ERROR: root element is <%s>, expected <DefaultSettings>" % ds.tag)
            problems += 1
            continue
        force = (ds.findtext("ForceSetting") or "false").strip().lower() == "true"
        entries = ds.findall("DefaultSetting")
        out("  ForceSetting=%s, %d DefaultSetting entries" % (tf(force), len(entries)))
        seen = {}
        for e in entries:
            t = (e.findtext("Type") or "").strip()
            if not TYPE_RE.match(t):
                out("  ERROR: bad <Type> '%s' (need MyObjectBuilder_X/Subtype)" % t)
                problems += 1
                continue
            for f in BOOL_FIELDS:
                v = e.findtext(f)
                if v is not None and v.strip().lower() not in ("true", "false"):
                    out("  ERROR: %s <%s> is '%s', not true/false" % (t, f, v.strip()))
                    problems += 1
            for f in INT_FIELDS:
                v = e.findtext(f)
                if v is not None and not re.fullmatch(r"-?\d+", v.strip()):
                    out("  ERROR: %s <%s> is '%s', not an integer" % (t, f, v.strip()))
                    problems += 1
            if t in seen:
                out("  WARN: %s listed more than once in this EC" % t)
            seen[t] = setting_from_element(e)
        if existing is not None:
            skipped = [t for t in seen if t in existing]
            out("  vs cfg: %d already have a setting (skipped unless ForceSetting=true), %d have no cfg entry "
                "(applied only if that block definition is loaded in the world)"
                % (len(skipped), len(seen) - len(skipped)))
            if skipped and not force:
                out("  NOTE: delete the cfg (or set ForceSetting) for those to take effect")
    if not found:
        out("No EntityComponent with SubtypeId starting 'BlockRestrictions' found")
        return 1
    out("Problems: %d" % problems)
    return 1 if problems else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("types", nargs="*")
    g.add_argument("--input")
    g.add_argument("--subtype-id", default="BlockRestrictions_Settings")
    g.add_argument("--force", action="store_true")
    g.add_argument("--player", choices=["true", "false"], default="false")
    g.add_argument("--npc", choices=["true", "false"], default="true")
    g.add_argument("--unowned", choices=["true", "false"], default="true")
    g.add_argument("--player-static-only", action="store_true")
    g.add_argument("--npc-static-only", action="store_true")
    g.add_argument("--unowned-static-only", action="store_true")
    g.add_argument("--max-player", type=int, default=0)
    g.add_argument("--max-grid", type=int, default=0)
    g.add_argument("--max-faction", type=int, default=0)
    g.add_argument("--output")
    g.set_defaults(fn=cmd_generate)
    c = sub.add_parser("check")
    c.add_argument("file")
    c.add_argument("--cfg")
    c.set_defaults(fn=cmd_check)
    a = p.parse_args()
    try:
        sys.exit(a.fn(a))
    except (OSError, ValueError, ET.ParseError) as e:
        sys.stderr.write("error: %s\n" % e)
        sys.exit(2)


if __name__ == "__main__":
    main()
