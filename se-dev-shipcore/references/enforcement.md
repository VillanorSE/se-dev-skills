# Runtime behavior: limits, punishments, grace timers, NPC rules, commands, API

Tags: **[HARD]** verified in SCF source/real files, **[SOFT]** inferred, **[UNVERIFIED]** unchecked.
Paths are under `Data\Scripts\ShipCoreFramework\`.

## Startup gate **[HARD]**

`Session.LoadData` loads the config; on the server it marks the API "config ready" only when a no-core profile is selected, otherwise "config unavailable" with the message
from `GetNoCoreConfigurationError()` (`Session\Session.Run.cs:76-88`). The messages are:
- no no-core profile loaded: "No content-pack no-core profiles were loaded. Ship Core Framework cannot start."
- none selected: "... Use /core listnocores and /core select <name>, then reload the world."
- selected name not loaded: "Selected no-core profile '<name>' was not loaded. Restore its content pack or select another profile, then reload the world."
While no no-core profile is selected, nothing is enforced: `Session.TryInitializeRuntime` returns without starting the runtime, and the per-tick update also returns early. **[HARD]** (`Session\Session.Run.cs:23, 140`) Once a profile is selected, NPC grids are governed too unless `IgnoreAiFactions` is on or their faction tag is in `IgnoredFactionTags`. **[SOFT]** (`GroupComponent.Ownership.cs:14-50`)

## Which grids are checked

- Limits are evaluated per **grid group** (grids linked mechanically/by the framework's group logic), not per single grid. **[HARD]** (`GroupComponent`, `GridComponent.Limits.cs`)
- A group is **ignored** (no limits, no punishment) when any of: `IgnoreAiFactions` is true and the group contains an NPC grid; its owning faction's tag is in `IgnoredFactionTags`;
  it has no owner; or its owner is an admin with "ignore PCU limit" enabled. **[HARD]** (`GroupComponent.Ownership.cs:14-50`) Default ignored tags: `SPRT, ADMIN, FMCA, BORG, TERA`. **[HARD]**
- Limits marked `IgnoredByNpc` are skipped for any group containing an NPC grid, independent of the ignore rules. **[HARD]**
- A block placed by an admin who has both admin rights and "ignore PCU limit" bypasses limits ("Block Was Placed By Admin, Block limits NOT Applied"). **[HARD]** (`GridComponent.Blocks.cs:30-42`)

## When a block is added

`TryApplyLimitsOnAdd` (`Server\Components\GridComponent.Limits.cs`) walks each limit that matches the block:
1. Directional rule violated -> notification "violated directional locking!", punish. **[HARD]**
2. Per-direction cap exceeded -> notification, punish. **[HARD]**
3. `current + weight > effective max` -> notification "violates Block limit <name>: x/y", punish. **[HARD]**
4. Otherwise the weight is added to the grid and group buckets. **[HARD]**

"Punish" uses the limit's `PunishmentType` or `Delete`, depending on the caller's `limitBasedPunish` flag; while the group is under a "force limited blocks off" gate it is `ShutOff`.
**[HARD]** (`GridComponent.Limits.cs:54-56, 81-83, 100-102`) Which callers pass which flag was not traced. **[UNVERIFIED]**
Stop rules: for the count and per-direction checks, `Delete`, `DeleteWithoutRefund` and `Explode` reject the block and stop evaluation while `ShutOff`/`Damage` let it continue; a
directional-lock violation stops evaluation for every punishment type unless the group is under a force-off gate. **[HARD]** (`:57, 85-88, 105-108`)

## Periodic enforcement of existing blocks

`EnforceGroupPunishment` re-checks group totals and queues punishments when a total exceeds the effective max. Candidates are ordered by ascending weight, then grid id, then block position,
and punished until the overage is covered; direction overages are handled first. Connector-linked weight is only ever shut off, never deleted. **[HARD]** (`GroupComponent.Limits.cs:574-752`)
Skipped while the group is deactivated, ignored, in punishment-deferred state, or in "core recovery grace". **[HARD]**

## Punishment types **[HARD]** (`Enforcement\Utils.BlockActions.cs:144-172`)

| Type | Effect |
|---|---|
| `ShutOff` | disables the block (`Enabled = false`); default |
| `Damage` | damages the block down to 50% of its max integrity |
| `Delete` | disables, then removes the block and refunds components |
| `DeleteWithoutRefund` | disables, then removes without refund |
| `Explode` | applies damage equal to the block's current integrity |

## No core, minimum blocks, and grace timers **[HARD]**

- When a group has no core, the selected no-core profile supplies its caps, limits and modifiers. (`LimitEvaluation.cs:145-150` comment and `GroupComponent.ShipCore` resolution)
- Losing the core starts a "core recovery grace" (`NoCoreGraceSeconds`, default 30 s, 0 disables) during which punishments are suspended; a countdown is broadcast; after expiry the no-core state is applied.
  (`GroupComponent.Lifecycle.cs:60-146`, `Limits.cs:277-290`)
- `MinBlocks > 0` and a group below it start a countdown (`MinimumBlocksGraceSeconds`, default 30 s); after it, limited blocks are forced off except `IsCriticalLimit` limits. (`Limits.cs:140-328`)
- MobilityType mismatch, below `MinPlayers`, and at/over `MaxPlayers` are punishment gates that affect speed and modifiers (the "Both" punishment flag). **[HARD]** (`Abilities.cs:100-135`)
  Speed under punishment falls to a quarter of the base cap. **[HARD]** (`SpeedEnforcement.cs:576-577`)

## Ownership and count limits

- New owners are validated against faction/player/manifest-group core-count limits; if a change would break them, ownership reverts to the previous owner (when there is one) or validation is deferred. **[HARD]** (`GroupComponent.Ownership.cs:57-100`)
- Cross-server counting for manifest-group and per-player counts exists in `Server\Network\LimitsNexusSync.cs` (Nexus multi-server setups). **[SOFT]** (not traced; irrelevant to single servers)
- Only admins bypass by "ignore PCU limit"; there is no per-core creative exemption except that per-player/faction core counts are switched by `CreativeCoreCountLimitsEnabled` in Creative-mode worlds. **[HARD]** (`Session.Fields.cs:28-34`)

## Chat commands (prefix `/core`) **[HARD]** (`Shared\Commands\Commands.Dispatch.cs:9`, `Server\Commands\`, `Client\UI\Commands.Chat.cs`)

| Command | Who | Purpose |
|---|---|---|
| `help`, `listcores`, `coreinfo <core>`, `listnocores`, `listnfzs`, `info`, `mass`, `limits` | anyone | inspect config and the grid you are on |
| `select <no-core name or SubtypeId>` | admin | choose the no-core profile (then save and reload) |
| `reloadconfig` | admin | reload content packs |
| `ignoreai` | admin | toggle `IgnoreAiFactions` |
| `ignoretags` (alias `ignoretag`) `list` | anyone | show `IgnoredFactionTags` |
| `ignoretags add <tag>` / `remove <tag>` | admin | edit `IgnoredFactionTags` |
| `corecountlimits on|off` | admin | toggle `CreativeCoreCountLimitsEnabled` |
| `unattachedmodules` | admin | toggle `AllowUnattachedUpgradeModules` |
| `setworldspeed <m/s>` | admin | set `MaxPossibleSpeedMetersPerSecond` |
| `createnfz`, `deletenfz` | admin | manage no-fly zones |
| `debug`, `combatlog`, `loglevel` | admin | diagnostics |
| `inventory` | anyone | inventory helper commands (`faction`/`player`) |
| `/corehud` | anyone | HUD toggles |

Admin = promote level Admin or Owner; in single-player (no multiplayer) every command is allowed. **[HARD]** (`Commands.Dispatch.cs:81-88`)

## Public API (v4) **[HARD]** (`API_USAGE.md`)

Two wrappers: `ShipCoreFrameworkServerApi` (authoritative queries and mutations) and `ShipCoreFrameworkClientApi` (read-only, replica-backed). Install by copying
`API\ApiData.cs` and `API\SCF_ModAPIClient.cs` into the consumer mod; call `Register()` in `LoadData` and `Unregister()` in `UnloadData`; check `ProviderReady`, `ConfigReady`,
`RuntimeSnapshotReady` before querying. Every call returns `ApiReadResult<T>` with statuses `Success`, `ProviderNotReady`, `ConfigPending`, `ConfigurationUnavailable`, `RuntimePending`,
`GridNotReplicated`, `InvalidArgument`, `Unsupported`, `Error`. Grid-targeted calls take `long gridEntityId`. There is no generic client-to-server API. Version-gated fields
(direction budgets v4.5, `DeleteWithoutRefund` and configuration diagnostics v4.4, `IgnoredByNpc` v4.3, direction caps v4.2) are described in that document.
