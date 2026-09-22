"""Shared helpers for the se-dev-blockrestrictions scripts (Python 3.8+, stdlib only)."""
import re
import sys
import xml.etree.ElementTree as ET

BOOL_FIELDS = [
    "AllowedForNPC", "AllowedForPlayer", "AllowedForUnowned",
    "AllowedForNPCStaticOnly", "AllowedForPlayerStaticOnly", "AllowedForUnownedStaticOnly",
]
INT_FIELDS = ["PlayerMaxCount", "GridMaxCount", "FactionMaxCount"]
# Defaults used by the mod for a block that has no setting (SerializableBlockSetting ctor).
DEFAULTS = {
    "PlayerMaxCount": 0, "GridMaxCount": 0, "FactionMaxCount": 0,
    "AllowedForNPC": True, "AllowedForPlayer": True, "AllowedForUnowned": True,
    "AllowedForNPCStaticOnly": False, "AllowedForPlayerStaticOnly": False,
    "AllowedForUnownedStaticOnly": False,
}


def read_text(path):
    """Read an XML text file. The mod's .cfg files DECLARE utf-16 but are written as 8-bit
    text, so sniff the BOM instead of trusting the declaration."""
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8", errors="replace")


def parse_xml_text(text):
    """ElementTree cannot parse a str that carries an encoding declaration reliably;
    strip the declaration first."""
    text = re.sub(r"^\s*<\?xml[^>]*\?>", "", text, count=1)
    return ET.fromstring(text)


def _b(elem, name, default):
    node = elem.find(name)
    if node is None or node.text is None:
        return default
    return node.text.strip().lower() == "true"


def _i(elem, name, default):
    node = elem.find(name)
    if node is None or node.text is None:
        return default
    try:
        return int(node.text.strip())
    except ValueError:
        return default


def setting_from_element(elem):
    d = {"Type": (elem.findtext("Type") or "").strip()}
    for f in BOOL_FIELDS:
        d[f] = _b(elem, f, DEFAULTS[f])
    for f in INT_FIELDS:
        d[f] = _i(elem, f, DEFAULTS[f])
    return d


def load_cfg(path):
    """Return dict: {'creative': bool, 'verbose': bool, 'groups': [...], 'settings': [...]}."""
    root = parse_xml_text(read_text(path))
    if root.tag != "BlockSaveData":
        raise ValueError("%s: root element is <%s>, expected <BlockSaveData>" % (path, root.tag))
    groups = []
    for g in root.findall("./GroupSettings/SerializableGroupSetting"):
        gd = setting_from_element(g)
        del gd["Type"]
        gd["GroupName"] = (g.findtext("GroupName") or "").strip()
        gd["Definitions"] = [
            "%s/%s" % (d.get("Type", ""), d.get("SubtypeId", ""))
            for d in g.findall("./Definitions/DefinitionId")
        ]
        groups.append(gd)
    return {
        "creative": _b(root, "CreativeModeAllowed", False),
        "verbose": _b(root, "VerboseMode", False),
        "groups": groups,
        "settings": [setting_from_element(e) for e in root.findall("./Settings/SerializableBlockSetting")],
    }


def split_type(type_string):
    """'MyObjectBuilder_Beacon/Sub' -> ('MyObjectBuilder_Beacon', 'Sub')."""
    if "/" not in type_string:
        return type_string, ""
    t, s = type_string.split("/", 1)
    return t, s


def is_restricted(s):
    return not s["AllowedForPlayer"]


def non_default_fields(s):
    return [f for f in BOOL_FIELDS + INT_FIELDS if s[f] != DEFAULTS[f]]


def out(line=""):
    sys.stdout.write(line + "\n")
