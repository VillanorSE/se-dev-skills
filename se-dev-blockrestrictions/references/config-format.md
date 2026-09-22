# Config, log and player files

Tags: **[HARD]** verified in source/real files, **[SOFT]** inferred, **[UNVERIFIED]** unchecked.

## Where the files are

| File | Content | Location |
|---|---|---|
| `BlockRestrictions.cfg` | block + group settings | world storage |
| `PlayerData.cfg` | per-player admin/creative/copy-paste flags | world storage |
| `BlockRestrictions.log` | load trace, errors, enforcement lines | world storage on a host/single player; **local storage on a dedicated server** |

**[HARD]** (`Config.cs` uses `...InWorldStorage`; `Logger.cs:30` chooses local storage when `IsDedicated`).

Single-player / host path on Windows: **[HARD]** (observed)

```
%AppData%\SpaceEngineers\Saves\<SteamID64>\<WorldName>\Storage\2053202808.sbm_BlockRestrictions\
```

The folder name is `<WorkshopId>.sbm_<ModName>`. Copies also appear inside Workshop-installed worlds and other mods' `Storage\`
folders. **[HARD]** (observed under the Workshop content directory)

## When it is generated

On first load of a world with the mod active, `BeforeStart` builds a setting for every terminal block definition in the loaded
mod set and saves the cfg. **[HARD]** (`BR:410-437`) Because the list is computed at load, it reflects exactly the mods active in that world.
Add or remove a mod and re-load: new terminal blocks get default entries; entries for blocks no longer loaded stay in the file, but are
ignored ("Unable to retrieve MyCubeBlockDefinition"). **[HARD]** (`BR:297-302`, entries are never deleted from `Settings`)

## cfg schema (`<BlockSaveData>`) **[HARD]**

```xml
<BlockSaveData>
  <CreativeModeAllowed>false</CreativeModeAllowed>
  <VerboseMode>false</VerboseMode>
  <GroupSettings>
    <SerializableGroupSetting>
      <GroupName>UniqueNameHere</GroupName>
      <PlayerMaxCount>0</PlayerMaxCount> <GridMaxCount>0</GridMaxCount> <FactionMaxCount>0</FactionMaxCount>
      <AllowedForNPC>true</AllowedForNPC> <AllowedForPlayer>true</AllowedForPlayer> <AllowedForUnowned>true</AllowedForUnowned>
      <AllowedForNPCStaticOnly>false</AllowedForNPCStaticOnly>
      <AllowedForPlayerStaticOnly>false</AllowedForPlayerStaticOnly>
      <AllowedForUnownedStaticOnly>false</AllowedForUnownedStaticOnly>
      <Definitions><DefinitionId Type="MyObjectBuilder_TypeGoesHere" SubtypeId="SubtypeGoesHere" /></Definitions>
    </SerializableGroupSetting>
  </GroupSettings>
  <Settings>
    <SerializableBlockSetting>
      <Type>MyObjectBuilder_Beacon/SomeSubtype</Type>
      ...same ten fields as above...
    </SerializableBlockSetting>
  </Settings>
</BlockSaveData>
```

- `Type` is `MyObjectBuilder_<TypeId>/<SubtypeId>`; an empty SubtypeId is written `(null)` (e.g. `MyObjectBuilder_LargeGatlingTurret/(null)`
  for a vanilla definition with `<SubtypeId/>`). **[HARD]** (observed in a real cfg and a vanilla `.sbc`)
- `VerboseMode` true makes the log record every count change and removal. **[HARD]** (`BR:1291, 1308, 1336`)
- Per-block defaults when nothing else is said: player/NPC/unowned allowed, static-only false, counts 0. **[HARD]** (`SerializableBlockSetting` ctor)

## Encoding quirk **[HARD]**

Real cfg files begin `<?xml version="1.0" encoding="utf-16"?>` but the bytes are plain 8-bit text (no BOM). Tools that honor the declaration
(strict parsers, `open(..., encoding="utf-16")`) fail. The bundled scripts read the bytes, detect a BOM if present, and strip the declaration
before parsing. Whether the game ever writes true UTF-16 on other platforms is **[UNVERIFIED]**.

## Editing rules

- The server reads the cfg at world load and rewrites it from memory later (`SaveConfig`, delete-then-write). Edit while the world is closed;
  edits made while running are likely overwritten. **[SOFT]** (`Config.cs:58-69`, `BR:440-446`)
- On a dedicated server, edit the server's copy of the world storage, then restart. **[SOFT]**
- Settings changed only in the cfg are not pushed to already-connected clients until they reconnect. **[UNVERIFIED]**

## PlayerData.cfg **[HARD]**

`<PlayerSaveData><PlayerSettings>` holds `PlayerData` rows: `SteamId`, `IsAdmin`, `CreativeEnabled`, `CopyPasteEnabled`. It is maintained by the mod, not configuration.

## Log format **[HARD]**

Lines: `[HH:mm:ss.fff] [T<thread>] [DS=<bool>] <ERROR|WARNING|DEBUG|INFO> | text`. Multi-line traces use `->` prefixes for indent depth.
Every real log observed contains a single `Log Started` header, consistent with the file being recreated on each load **[SOFT]** (`WriteFileIn...Storage` semantics not confirmed).
Key trace phrases: `Checking Group Settings`, `Checking Config for saved settings`, `Checking Entity Components`, `Found EC: Subtype = ...`,
`A setting already exists (skipping this default setting)`, `Unable to retrieve MyCubeBlockDefinition`, `Definition cannot be restricted`,
`Type added to the restricted list`, `Finished with settings`. `scripts/br_log.py` parses these.
