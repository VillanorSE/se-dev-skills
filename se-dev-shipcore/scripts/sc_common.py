"""Shared helpers for the se-dev-shipcore scripts (Python 3.8+, stdlib only).

Loads a Ship Core Framework "content pack" (a mod folder that provides Data\\ShipCoreConfig_*.xml)
the same way the framework's loader does (ModConfig.Loading.cs): manifest -> core files, groups file,
no-core file, upgrade modules.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

MANIFEST = os.path.join("Data", "ShipCoreConfig_Manifest.xml")
GROUPS = os.path.join("Data", "ShipCoreConfig_Groups.xml")
NOCORE = os.path.join("Data", "ShipCoreConfig_No_Core.xml")

# Enums exactly as declared in ModConfig.XmlModels.cs
ENUMS = {
    "MobilityType": ["Static", "Mobile", "Both"],
    "SpeedLimitType": ["Normal", "Friction"],
    "SpeedOverrideMode": ["None", "OnlyIfHeavier", "Priority", "Any"],
    "PunishmentType": ["ShutOff", "Damage", "Delete", "Explode", "DeleteWithoutRefund"],
    "DirectionType": ["Forward", "Backward", "Up", "Down", "Left", "Right", "Any"],
    "LimitVisibility": ["Always", "NearLimit", "Hidden"],
    "FactionRank": ["None", "Member", "Leader", "Founder"],
    "UpgradeModifierOperation": ["Additive", "Multiplicative"],
    "FrictionSpeedValueMode": ["Modifier", "Absolute"],
}
DEFAULT_WORLD_SPEED = 300.0  # ModConfig.MaxPossibleSpeedMetersPerSecond default


def read_text(path):
    """The game writes files declaring utf-16 that may actually be 8-bit; sniff the BOM."""
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8", errors="replace")


def parse_file(path):
    text = re.sub(r"^\s*<\?xml[^>]*\?>", "", read_text(path), count=1)
    return ET.fromstring(text)


def normalize_type(t):
    """ModConfig.NormalizeBlockTypeId: trim and strip a leading MyObjectBuilder_ (case-insensitive)."""
    t = (t or "").strip()
    if t.lower().startswith("myobjectbuilder_"):
        t = t[len("MyObjectBuilder_"):]
    return t


def resolve(moddir, rel):
    """Mimic BuildModPathCandidates: accept either slash style, any leading slash."""
    rel = rel.strip().lstrip("/\\")
    p = os.path.join(moddir, rel.replace("\\", os.sep).replace("/", os.sep))
    return p if os.path.isfile(p) else None


def txt(e, tag, default=""):
    v = e.findtext(tag)
    return default if v is None else v.strip()


def num(e, tag, default):
    v = e.findtext(tag)
    if v is None:
        return default
    try:
        return float(v.strip())
    except ValueError:
        return default


def load_groups(path):
    """Return list of dicts: {name, types:[(normalized_type, subtype, weight)]}"""
    root = parse_file(path)
    out = []
    for g in root.findall("BlockGroup"):
        types = []
        for bt in g.findall("BlockTypes"):
            types.append((normalize_type(bt.findtext("TypeId")), txt(bt, "SubtypeId"),
                          num(bt, "CountWeight", 1.0)))
        out.append({"name": txt(g, "Name"), "types": types})
    return out


def load_pack(moddir):
    """Load one content pack. Returns dict with 'errors' (list of str) and parsed content.
    Errors here are load/parse problems; semantic checks live in sc_lint.py."""
    pack = {"dir": moddir, "manifest": None, "groups": None, "nocore": None,
            "cores": [], "errors": [], "manifest_root": None}
    mp = os.path.join(moddir, MANIFEST)
    gp = os.path.join(moddir, GROUPS)
    np_ = os.path.join(moddir, NOCORE)
    if os.path.isfile(gp):
        try:
            pack["groups"] = load_groups(gp)
        except ET.ParseError as e:
            pack["errors"].append("%s: not well-formed XML: %s" % (GROUPS, e))
    if os.path.isfile(np_):
        try:
            pack["nocore"] = parse_file(np_)
        except ET.ParseError as e:
            pack["errors"].append("%s: not well-formed XML: %s" % (NOCORE, e))
    if os.path.isfile(mp):
        try:
            root = parse_file(mp)
        except ET.ParseError as e:
            pack["errors"].append("%s: not well-formed XML: %s" % (MANIFEST, e))
            return pack
        pack["manifest_root"] = root
        entries = []
        for sc in root.findall("ShipCore"):
            entries.append({
                "filename": txt(sc, "Filename"),
                "groups": [g.text.strip() for g in sc.findall("Group") if g.text and g.text.strip()],
                "priority": int(num(sc, "CoreSelectionPriority", 0)),
                "blacklist": [b.text.strip() for b in sc.findall("BlacklistedCoreSubtypeId") if b.text and b.text.strip()],
            })
        pack["manifest"] = {
            "cores": entries,
            "groups": [{"name": txt(g, "Name"), "max": num(g, "MaxCount", -1)}
                       for g in root.findall("./ManifestGroups/Group")],
            "whitelist": [w.text.strip() for w in root.findall("CrossConnectorPunishmentWhitelist") if w.text and w.text.strip()],
            "upgrades": [txt(u, "Filename") for u in root.findall("UpgradeModule")],
        }
        for ent in entries:
            path = resolve(moddir, ent["filename"]) if ent["filename"] else None
            if path is None:
                pack["cores"].append({"entry": ent, "path": None, "root": None})
                continue
            try:
                pack["cores"].append({"entry": ent, "path": path, "root": parse_file(path)})
            except ET.ParseError as e:
                pack["errors"].append("%s: not well-formed XML: %s" % (ent["filename"], e))
                pack["cores"].append({"entry": ent, "path": path, "root": None})
    return pack


def scan_cube_blocks(moddir):
    """Find <CubeBlocks><Definition> entries in every .sbc under moddir.
    Returns (set of (normalized_type, subtype), unparseable_file_count, file_count)."""
    defs, bad, files = set(), 0, 0
    for base, _dirs, names in os.walk(moddir):
        for n in names:
            if not n.lower().endswith(".sbc"):
                continue
            files += 1
            try:
                root = parse_file(os.path.join(base, n))
            except (ET.ParseError, OSError):
                bad += 1
                continue
            for cb in root.iter("CubeBlocks"):
                for d in cb.findall("Definition"):
                    t = normalize_type(d.findtext("./Id/TypeId"))
                    s = (d.findtext("./Id/SubtypeId") or "").strip()
                    if t:
                        defs.add((t, s))
    return defs, bad, files


def out(line=""):
    sys.stdout.write(line + "\n")
