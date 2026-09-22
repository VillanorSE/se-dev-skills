# Core file schema (`<ShipCore>`) and block limits

Tags: **[HARD]** verified in SCF source/real files, **[SOFT]** inferred, **[UNVERIFIED]** unchecked.
Source: `Config\ModConfig.XmlModels.cs` (`XM`). Element names are case-sensitive XML; unknown elements are ignored by XmlSerializer **[SOFT]**
(`scripts/sc_lint.py` flags them). A missing element takes the default below. **[HARD]**

## Identity and hard caps

| Element | Type / default | Meaning |
|---|---|---|
| `SubtypeId` | string, "" | must equal the core block's SubtypeId **[HARD]** |
| `UniqueName` | string, "" | display/selection name; must be unique across all packs (duplicate throws) **[HARD]** |
| `MobilityType` | `Static`/`Mobile`/`Both`, Both | a mismatch with the grid's static state triggers the core's punishment gate **[HARD]** (`Abilities.cs:153-177`) |
| `MaxBlocks`, `MinBlocks` | int, -1 | hard block-count cap and required minimum; values `<= 0` disable the cap in the evaluator **[HARD]** (`LimitEvaluation.cs:164-166`, `MinBlocks > 0`) |
| `MaxPCU` | int, -1 | PCU cap **[HARD]** |
| `MaxMass` | float, -1 | mass cap **[HARD]** |
| `MaxBackupCores` | int, -1 | extra cores allowed on a group; above the number the new core is rejected (only when `> 0`) **[HARD]** (`CoreComponent.Authority.cs:86-89`) |
| `MaxPerPlayer`, `MaxPerFaction` | int, -1 | count of this core type per player / faction; enforced always outside Creative mode, and in Creative-mode worlds only while world `CreativeCoreCountLimitsEnabled` is true **[HARD]** (`Session.Fields.cs:28-34`) |
| `FactionPlayersNeededPerCore` | int, -1 | faction size needed per core **[SOFT]** (name + `ShouldDeferOwnerLimitValidation`) |
| `MinPlayers`, `MaxPlayers` | int, -1 | faction player-count gates; below min / at or over max triggers punishment **[HARD]** (`Abilities.cs:190-199`) |
| `MinFactionRank` | `None`/`Member`/`Leader`/`Founder`, None | rank needed to own the core **[SOFT]** (name only) |
| `ForceBroadCast`, `ForceBroadCastRange` | false, 0 | force the grid to broadcast **[SOFT]** (name only; not traced) |
| `SpeedBoostEnabled` | false | enables boost per `SpeedModifiers.MaxBoost/BoostDuration/BoostCoolDown` **[HARD]** (`Abilities.cs:620`) |

## Multipliers **[HARD]** (`XM:625-684, 938-967`)

- `<Modifiers>`: `AssemblerSpeed`, `DrillHarvestMultiplier`, `GyroEfficiency`, `GyroForce`, `PowerProducersOutput`, `RefineEfficiency`, `RefineSpeed`,
  `ThrusterEfficiency`, `ThrusterForce`. Every one defaults to 1 (multiplicative scale).
- `<PassiveDefenseModifiers>` / `<ActiveDefenseModifiers>` (active applies only with `EnableActiveDefenseModifiers`): `Bullet`, `PostShield`, `Rocket`, `Explosion`,
  `Environment`, `Energy`, `Kinetic` (default 1) and `Duration`, `Cooldown` (default 0).
- `<PowerOverclock*>`: `PowerOverclockEnabled`, `PowerOverclockMultiplier` (1), `PowerOverclockDuration` (10), `PowerOverclockCooldown` (60), `PowerOverclockDamagePerSecond` (0).
- The multiplier fields are values on the whole grid group's blocks; exact stacking with upgrade modules follows `CubeGridModifiers*.cs` (not traced). **[UNVERIFIED]**
- A `Modifiers` field that a fork or older version used but this version lacks (e.g. `MaxSpeed` inside `<Modifiers>`) is ignored. **[SOFT]**

## Speed **[HARD]** (`SpeedEnforcement.cs:560-590`, `XM:506-560`)

- `SpeedLimitType`: `Normal` (hard cap) or `Friction` (deceleration curve). `SpeedOverrideMode` (`None`/`OnlyIfHeavier`/`Priority`/`Any`, default OnlyIfHeavier) and
  `SpeedOverridePriority` decide which core's speed applies when connected groups differ. **[HARD]** for the enum/tier use (`SpeedEnforcement.cs:469-491`); exact semantics **[UNVERIFIED]**.
- Base top speed = `MaxPossibleSpeedMetersPerSecond` (world, default 300) x `SpeedModifiers.MaxSpeed`; boost speed = world speed x `MaxBoost`. `MaxSpeed` is a **fraction**, not m/s.
  `MaxSpeed 0.5` in a 300 m/s world = 150 m/s. When the group is speed-punished the effective cap becomes base / 4. **[HARD]**
- `SpeedModifiers` defaults: `MaxSpeed 0.3`, `MaxAngularVelocity 0` (0 = off), `MaxBoost 0.5`, `BoostDuration 10`, `BoostCoolDown 60`,
  `MinimumFrictionSpeedAbsolute 100`, `MaximumFrictionSpeedAbsolute 290`, `MinimumFrictionSpeedModifier 0.3`, `MaximumFrictionSpeedModifier 0.8`,
  `MaximumFrictionDeceleration 1`, `CruiseFrictionMultiplier 1`, `CruiseAccelerationThreshold 0.05`; optional `FrictionCurve/Segment` and `AtmosphericFriction`. **[HARD]**
- World `FrictionSpeedValueMode` (`Modifier`/`Absolute`) decides whether friction speeds are fractions of the world speed or absolute m/s. **[HARD]** (`SpeedEnforcement.cs:266-270`)

## Block limits (`<BlockLimits>`, repeatable) **[HARD]** (`XM:698-840`)

```xml
<BlockLimits>
  <Name>Engines</Name>
  <BlockGroups>Engines</BlockGroups>                 <!-- repeatable; optional Directions="Forward,Backward" attribute -->
  <ExcludedBlockGroups>SmallEngines</ExcludedBlockGroups>  <!-- repeatable; subtracted, exclusion wins -->
  <MaxCount>2</MaxCount>                             <!-- float; default 0 = none allowed -->
  <AllowedDirections>Forward</AllowedDirections>     <!-- repeatable, ONE value per element -->
  <AllowedDirections>Backward</AllowedDirections>
  <MaxCountPerDirection>1</MaxCountPerDirection>     <!-- optional, -1 = off -->
  <DirectionBudgets><DirectionBudget Direction="Forward" MaxCount="2"/></DirectionBudgets>
  <PunishmentType>ShutOff</PunishmentType>           <!-- ShutOff (default), Damage, Delete, Explode, DeleteWithoutRefund -->
  <LimitVisibility>Always</LimitVisibility>          <!-- Always, NearLimit, Hidden (HUD only) -->
  <IsCriticalLimit>false</IsCriticalLimit>
  <IgnoredByNpc>false</IgnoredByNpc>
  <PunishByNoFlyZone>false</PunishByNoFlyZone>
  <CrossConnectorPunishment>false</CrossConnectorPunishment>
</BlockLimits>
```

- **Counting:** each block matching a group entry adds its `CountWeight`; a placement violates the limit when `current + weight > MaxCount`. So `MaxCount 0` forbids the blocks
  outright, a fractional MaxCount works with fractional weights, and there is no "unlimited" value - omit the limit to leave a block type unrestricted. **[HARD]**
  (`LimitEvaluation.cs:138`, `GridComponent.Limits.cs:91-92`) A negative MaxCount blocks everything that counts. **[SOFT]** (follows from the comparison)
  Real packs use 0 heavily for outright bans. **[HARD]** (observed: a large share of `MaxCount` values in two packs are 0)
- **No `<BlockGroups>`** -> the limit matches nothing. **[HARD]**
- **Directions:** relative to the core (forward/up of the reference block); a block's facing is the axis of its `PrimaryDirection` classified into the nearest of Forward/Backward/Up/Down/Left/Right.
  **[HARD]** (`ResolveFacing`; the reference is the direction-lock block, normally the main core or cockpit **[SOFT]**)
  - `AllowedDirections` empty or containing `Any` = no rule. A `Directions` attribute on a `<BlockGroups>` entry overrides the limit's list for that group and is parsed
    case-insensitively as a comma list. **[HARD]**
  - `MaxCountPerDirection`/`DirectionBudgets` cap the weight facing each direction; validation throws unless MaxCount is finite and non-negative, each budget names one of the six specific
    directions once with a non-negative MaxCount, and the summed caps (including the inherited per-direction cap for every allowed direction) do not exceed `MaxCount`. **[HARD]** (`Validation.cs:157-199`)
  - Directional placement across subgrids is blocked when world `BlockDirectionalPlacementOnSubgrids` is true. **[HARD]** (`XM:52`, `Limits.cs:75-84`)
- `IgnoredByNpc`: the limit is not evaluated on grid groups that contain an NPC grid. **[HARD]** (`GroupComponent.Ownership.cs:26-30`)
- `IsCriticalLimit`: excluded from the "force limited blocks off" punishment gates (e.g. below minimum blocks, connector punishment). **[HARD]** (`Limits.cs:324-328`, `Connectors.cs`)
- `PunishByNoFlyZone`, `CrossConnectorPunishment`: tie the limit to no-fly-zone shutoff and to connector-linked counting. **[SOFT]** (used in `NoFlyZoneEnforcement.cs`, `Connectors.cs`; not fully traced)
- `LimitVisibility` only affects the HUD (`NearLimit` shows at 80% of max or when failing). **[HARD]** (`LimitEvaluation.cs:76-85`)

## Warnings the loader emits for these files **[HARD]**

Level-2 `[Config Validation]` lines: "had no <BlockLimits>", "had no <SpeedModifiers>", "references unknown BlockGroup", "includes and excludes ... exclusion wins", "has <MaxCountPerDirection> enabled
but no valid direction", and (very noisy) "has a <BlockLimit> with null <ExcludedBlockGroups>; treating as empty" - emitted once per limit that has no `<ExcludedBlockGroups>`
(193 lines per load in one real 12-core pack). The last one is harmless. **[HARD]** (real log + `Validation.cs:78-82`)
