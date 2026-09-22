# Pitfalls and open questions

Tags: **[HARD]** verified in SCF source/real files, **[SOFT]** inferred, **[UNVERIFIED]** unchecked.

## Config that fails or silently does nothing

| Symptom | Cause | How to check |
|---|---|---|
| "No content-pack no-core profile is selected" in the log | `SelectedNoCoreUniqueName` is empty **[HARD]** | `sc_log.py` STATUS line; `sc_lint.py --world`; run `/core select <name>` and reload |
| Config throws at load (duplicate ...) | same `UniqueName`/group name in two packs **[HARD]** | `sc_lint.py` with all packs together |
| Config throws: manifest group | core `<Group>` names an undefined manifest group, or `ManifestGroups/Group` lacks a non-negative `MaxCount` **[HARD]** | `sc_lint.py` |
| Load fails on a core file | XML value not readable: comma-joined `AllowedDirections`, bad enum spelling/case, non-integer in an int field **[SOFT]** (XmlSerializer) | `sc_lint.py` |
| A limit never triggers | no `<BlockGroups>`, wrong group name, or group entry with wrong TypeId/SubtypeId **[HARD]** | `sc_lint.py`, `sc_coverage.py` (dangling entries) |
| A block is restricted by no limit | the block is not in any group **[HARD]** | `sc_coverage.py --uncovered <TypeId ...>` |
| Core block is not recognized as a core | its SubtypeId differs from the core file's `<SubtypeId>`, or it is not a functional block **[HARD]** | `sc_lint.py --blocks <dirs>` |
| Core file "listed in the manifest but could not be read" | wrong path/case in `<Filename>` **[HARD]** | `sc_lint.py` |
| 100+ "null <ExcludedBlockGroups>" warnings | limits without `<ExcludedBlockGroups>`; harmless **[HARD]** | ignore |
| Two packs cannot be used together | both define the same group or core name **[HARD]** | rename in one pack |

## Semantics that surprise people

- `MaxCount` 0 forbids; there is no unlimited value for a limit (omit the limit). Hard caps `MaxBlocks`/`MaxPCU`/`MaxMass` use `-1` (or any value `<= 0`) for "no cap". **[HARD]**
- `MaxSpeed` in `SpeedModifiers` is a fraction of the world speed, not m/s. The world default is 300 m/s (`/core setworldspeed` changes it). **[HARD]**
- TypeIds are the definition's real TypeId minus `MyObjectBuilder_`: a "programmable block" group entry needs `MyProgrammableBlock`, not `ProgrammableBlock`. **[HARD]** (vanilla `.sbc`)
  A published pack in this environment has group entries with `ProgrammableBlock`/`LargeMissileTurret` TypeIds that match no vanilla definition. **[HARD]** (found with `sc_coverage.py`)
- The `Directions` attribute on a `<BlockGroups>` entry is a comma list; the `<AllowedDirections>` element is one value per element. **[HARD]**
- Group matching takes the first hit; put more specific entries in earlier groups if you rely on different `CountWeight`s. **[HARD]** (`FindMatchingBlockType`)
- Counting is per grid group. Splitting a build into several unconnected grids splits nothing: only mechanically/connector-linked grids share totals. Connector-linked counting has
  its own rules (`CrossConnectorPunishment`, blacklists). **[SOFT]** (`GroupComponent.Connectors.cs` not fully traced)
- Placing a block that breaks a limit is punished at placement; existing overages are trimmed later by a periodic pass. Deleted blocks refund unless `DeleteWithoutRefund`. **[HARD]**

## Tooling traps

- The game-written `ShipCoreConfig_World.xml` declares `encoding="utf-16"` but its bytes are plain 8-bit text (no BOM); strict UTF-16 readers fail on it. The scripts read bytes, honor a real BOM
  if present, and ignore the declaration. **[HARD]** (observed on a saved world's file)
- The log format is `YYYY-MM-DD HH:MM:SS.mmm - Thread:   N ->  [Category]: message`; SCF categories are `[Ship Core Config]`, `[Config Validation]`, `[Config Sync]`. **[HARD]** (real log)
  Log level 2 (default) prints warnings; raise `LOG_LEVEL` (world config or `/core loglevel`) for more. **[SOFT]**
- On Windows, launch the scripts from Git Bash with Windows-style paths (`C:/...`), not `/tmp/...`. **[HARD]** (observed while testing)
- Linting one pack alone reports "unknown BlockGroup" for groups defined in a dependency pack; lint all packs of the world together. **[HARD]** (observed on a real pack)

## Not examined

- The exact ordering in `CompareCoreCandidates` when priorities tie. **[UNVERIFIED]**
- `SpeedOverrideMode` behavior across connected grids. **[UNVERIFIED]**
- Valid `Stat` names for upgrade modules. **[UNVERIFIED]**
- Whether loading another pack's elements this version does not define causes any error beyond being ignored. **[UNVERIFIED]**
- Nexus/multi-server behavior. **[UNVERIFIED]**
- Behavior in a live multiplayer session; everything here is from code and logs. **[SOFT]**
