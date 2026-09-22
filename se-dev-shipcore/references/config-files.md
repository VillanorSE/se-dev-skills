# Config files, loading and merging

Tags: **[HARD]** verified in SCF source/real files, **[SOFT]** inferred, **[UNVERIFIED]** unchecked.
Source paths are under `Data\Scripts\ShipCoreFramework\Config\` (`ModConfig.XmlModels.cs` = `XM`, `ModConfig.Loading.cs` = `LD`,
`ModConfig.Validation.cs` = `VA`).

## Files a content pack provides **[HARD]** (`XM:11-14`)

| Path inside the mod | Root element | Read as | Purpose |
|---|---|---|---|
| `Data\ShipCoreConfig_Manifest.xml` | `CoreManifest` | `CoreManifest` | lists core files, manifest groups, upgrade modules |
| `Data\ShipCoreConfig_Groups.xml` | `ArrayOfBlockGroup` | `List<BlockGroup>` | reusable block groups referenced by limits |
| `Data\ShipCoreConfig_No_Core.xml` | `ShipCore` | `ShipCore` | the profile for grids without a core |
| files named by the manifest | `ShipCore` / `UpgradeModule` | | one per core / upgrade module |

World-level settings live in **world storage**, not in a pack: `ShipCoreConfig_World.xml` (see below). **[HARD]**

The manifest paths may use either slash style and a leading slash; the loader tries several spellings. **[HARD]** (`LD:334-368`)

## How loading works **[HARD]** (`LD:19-63`)

1. On the server/host it first reads (or creates) the world file `ShipCoreConfig_World.xml`.
2. For **every mod in `Session.Mods`** it reads, in this order: groups file, no-core file, manifest (+ each core and upgrade-module file the manifest lists).
3. Everything from all mods is merged into one list; then duplicates are checked and the config **throws** on any of:
   duplicate no-core `UniqueName`, core `UniqueName`, manifest group `Name`, upgrade module `TypeId/SubtypeId`, or BlockGroup `Name`.
4. Cores' `BlockGroups` names are resolved against the merged group list, case-insensitively; unknown names log a warning. **[HARD]** (`LD:454-474`)
5. The selected no-core profile is resolved from the world file's `SelectedNoCoreUniqueName`.

Consequences:
- Groups can live in a different mod from the cores that use them (dependency packs). Lint them together. **[HARD]** (merge behavior)
- A pack cannot override another pack's group, core or no-core: same names throw. **[HARD]**
- A missing file simply means that pack contributes nothing for it. **[HARD]** (`TryReadModTextFile` returns false)

## Manifest (`<CoreManifest>`) **[HARD]** (`XM:79-133`)

```xml
<CoreManifest>
  <ManifestGroups>
    <Group><Name>Heavy</Name><MaxCount>3</MaxCount></Group>
  </ManifestGroups>
  <CrossConnectorPunishmentWhitelist>SomeCoreSubtypeId</CrossConnectorPunishmentWhitelist>
  <ShipCore>
    <Filename>Data\Cores\Cruiser_Core.xml</Filename>
    <Group>Heavy</Group>                       <!-- repeatable; must name a ManifestGroup -->
    <CoreSelectionPriority>40</CoreSelectionPriority>
    <BlacklistedCoreSubtypeId>Fighter_Core</BlacklistedCoreSubtypeId>   <!-- repeatable -->
  </ShipCore>
  <UpgradeModule><Filename>Data\UpgradeModules\Booster.xml</Filename></UpgradeModule>
</CoreManifest>
```

- `ManifestGroups/Group`: `Name` required and `MaxCount` must be `>= 0` (a missing MaxCount is -1 and **throws**). **[HARD]** (`VA:391-395`)
- A core's `<Group>` naming an unknown manifest group **throws**. **[HARD]** (`LD:384-385`)
- Manifest-group counts are kept by group name only (not per player or faction), plus counts from other servers when a Nexus link is active.
  **[HARD]** (`PerManifestGroupManager` dictionary keyed by group name) Whether an over-limit core is punished or refused: see `enforcement.md`.
- When one grid group carries several cores, one becomes the *main* core; candidate comparison uses `CoreSelectionPriority` (integer, default 0) and a
  candidate must have the same orientation as the current main core. **[HARD]** (`GroupComponent.CoreSelection.cs:8-100`) That a higher number wins is inferred from
  the comparison direction, **[SOFT]**; the full tie-break order was not traced. **[UNVERIFIED]**
- `BlacklistedCoreSubtypeId` lists core SubtypeIds that a connected grid's core may not be paired with across connectors: a connected group whose core is
  blacklisted by a higher-ranking connected core is affected by the connector rules. **[SOFT]** (`GroupComponent.Connectors.cs:260-293`; consequences not traced)
- Entries without a `Filename` are dropped with a warning. **[HARD]** (`VA:328-331`)

## Block groups (`ShipCoreConfig_Groups.xml`) **[HARD]** (`XM:866-936`)

```xml
<ArrayOfBlockGroup>
  <BlockGroup>
    <Name>Engines</Name>
    <BlockTypes>
      <TypeId>MyObjectBuilder_Thrust</TypeId>     <!-- prefix optional -->
      <SubtypeId>any</SubtypeId>                  <!-- 'any' (case-insensitive) = every subtype -->
      <CountWeight>1</CountWeight>                <!-- default 1 -->
      <PrimaryDirection>Forward</PrimaryDirection> <!-- default Forward; which block axis counts as its facing -->
    </BlockTypes>
  </BlockGroup>
</ArrayOfBlockGroup>
```

- `<BlockTypes>` is repeated once per definition. Note the plural element name for a single entry. **[HARD]** (`[XmlElement("BlockTypes")] List<BlockType>`)
- **TypeId** is normalized by stripping `MyObjectBuilder_` (case-insensitive) on load; matching is then exact and **case-sensitive**. **[HARD]** (`ModConfig.cs:82-92`, `XM:924-935`)
  The TypeId must be the definition's real TypeId: e.g. the vanilla programmable block is `MyProgrammableBlock`, and the vanilla autocannon turret is `LargeGatlingTurret`. **[HARD]** (verified in vanilla `.sbc`)
- **SubtypeId** matches exactly (case-sensitive) or `any`. An empty SubtypeId matches only blocks whose definition has an empty SubtypeId. **[HARD]**
- The first matching entry across a limit's groups supplies the `CountWeight`; excluded groups are checked first and win. **[HARD]** (`XM:784-839`)
- `CountWeight <= 0` never counts. **[HARD]** (weight `<= 0` skipped in `LimitEvaluation`/`GridComponent.Limits`)

## No-core profile (`ShipCoreConfig_No_Core.xml`) **[HARD]**

Same schema as a core (`<ShipCore>`). Its `UniqueName` is what admins select. At least one no-core profile must be loaded and one selected, or SCF
reports "Ship Core Framework cannot start" / "No content-pack no-core profile is selected". **[HARD]** (`LD:108-119`) The retired built-in profile name
`DEFAULT-NO-CORE-ALL-GRID-TYPES` is auto-migrated only when exactly one no-core profile exists. **[HARD]** (`LD:85-94`)

## World config (`ShipCoreConfig_World.xml`) **[HARD]** (`XM:31-57`, `WorldSettings.cs`)

Location: `<world>\Storage\3552595651.sbm_ShipCoreFramework\ShipCoreConfig_World.xml` (world storage). **[HARD]** (observed path in saved worlds; created on first load)

| Element | Default | Validation |
|---|---|---|
| `IgnoreAiFactions` | false | |
| `IgnoredFactionTags/Tag` | `SPRT, ADMIN, FMCA, BORG, TERA` when the element is absent and empty | trimmed, de-duplicated |
| `SelectedNoCoreUniqueName` | empty | must match a loaded no-core `UniqueName` (case-insensitive) |
| `DebugMode`, `CombatLogging` (true), `CombatLoggingBroadcastRangeMeters` (20000), `LOG_LEVEL` (2), `CLIENT_OUTPUT_LOG_LEVEL` (2) | | broadcast range must be finite and > 0 |
| `MaxPossibleSpeedMetersPerSecond` | 300 | must be in (0, 10000] else 300 |
| `SpeedRampDownPercentage` | 5 | 0-100 else 5 |
| `FrictionSpeedValueMode` | Modifier | Modifier / Absolute |
| `BlockDirectionalPlacementOnSubgrids` | true | |
| `AllowUnattachedUpgradeModules` | false | |
| `CreativeCoreCountLimitsEnabled` | true | |
| `NoCoreGraceSeconds`, `MinimumBlocksGraceSeconds` | 30 | 0-3600 (negative -> 30, above 3600 -> clamped) |
| `NoFlyZones/Zones` | none | `ID`, `Position`, `Radius`, `AllowedCoresSubtype`, `OverideBlockLimitsForceShutOff` (sic) |

- The file is edited by chat commands and rewritten by the mod; edit only with the world closed. **[SOFT]**
- Legacy settings stored in the save's sandbox variables are imported only if the world file lacks the element. **[HARD]** (`WorldLoading.cs`)
- The world-settings payload sent to joining clients is capped at 1,048,576 characters; larger fails with "exceeds the synchronization size limit". **[HARD]**
  (`ServerServices.cs:51`, `DirectionalPacketContracts.cs:120`). Only these settings and the no-fly zones are in that payload, since the core lists are `XmlIgnore`. **[HARD]** (`XM:23-27`)

## Type-name normalization

`NormalizeBlockTypeId` strips a leading `MyObjectBuilder_` (any case). `FormatBlockDefinitionId` yields `Type/Subtype`. Upgrade modules default to TypeId `UpgradeModule`. **[HARD]** (`ModConfig.cs`)

## Upgrade modules (brief)

`UpgradeModule` files carry `TypeId` (default `UpgradeModule`), `SubtypeId` (required), `UniqueName` (defaults to SubtypeId), and lists of `Modifiers` (`Stat`, `Value`,
`ModifierType` Additive/Multiplicative), `BlockLimitModifiers` (`BlockLimitName`, `Value`) and `CapacityModifiers`. A core allows modules via
`<AllowedUpgradeModules>` (`TypeId`/`SubtypeId` or `UniqueName`, `MaxCount`); duplicate entries throw. **[HARD]** (`XM:416-504`, `VA:433-460`)
The list of valid `Stat` names was not enumerated here. **[UNVERIFIED]**
