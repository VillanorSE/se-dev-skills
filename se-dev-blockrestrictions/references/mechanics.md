# Mechanics: how the mod enforces restrictions

Tags: **[HARD]** verified in source/real files, **[SOFT]** inferred, **[UNVERIFIED]** unchecked.
File references are to the mod's `Data\Scripts\BlockRestrictions\` folder (`BR` = `BlockRestrictions.cs`).

## Server vs client

- Only the server/host runs the scan; a pure client sends its creative/copy-paste state to the server and returns early
  from `BeforeStart`. **[HARD]** (`BR:560-565`)
- The server relays settings to clients over the mod's secure message channel so clients can hide blocks; the packet
  carries `CreativeModeAllowed`, group settings and block settings. **[HARD]** (`BR:644-648`, `ReceiveSettings`)

## Hiding blocks (G-menu / toolbar)

- At `LoadData`, any cube definition that is already `Public == false` is added to the restricted set. **[HARD]** (`BR:521-529`)
- For non-admin players, restricted definitions get `Public = false`; every terminal definition gets
  `Public = allowAdmin || no setting || AllowedForPlayer`. **[HARD]** (`BR:912-934`)
- Toolbar slots holding restricted blocks are cleared (pages 0-8, slots 0-8), unless the Research Framework mod
  (`2307665159`) is installed, in which case the restricted list is sent to it instead. **[HARD]** (`BR:841-897`)
- `allowAdmin` = copy-paste enabled AND creative enabled AND (world is not Creative mode OR `CreativeModeAllowed`).
  "Creative enabled" = creative game mode, or creative rights plus copy-paste. **[HARD]** (`BR:823`, `Utilities.CheckCreativeTools`)
- Consequence: in a Creative-mode world restrictions still bind unless an admin runs `/br creativeallowed true`. **[SOFT]** (follows from the formula)
- The only chat command is `/br creativeallowed [true|false]` (no value toggles). It requires a promote level >= 4.
  **[HARD]** (`BR:588-655`). That level 4 means Admin is game-enum knowledge, not read here **[SOFT]**.

## Enforcement on grids

- Every grid that enters the world (`OnEntityAdd`) and has physics and is not a preview is queued and scanned, including
  pasted, blueprint-spawned and NPC/encounter-spawned grids. **[HARD]** (`BR:1199-1209`)
- The queue is processed on a background task every 10 ticks; removals happen on the main thread. **[HARD]** (`BR:794-802`)
- Grids are grouped by mechanical connection; owner/static status is per group. **[HARD]** (`Entity.cs:1113-1136`, `GridCollection.cs`)
- Per block, in order (`Entity.cs:477-547`):
  1. **Unowned grid:** removed if `AllowedForUnowned` false, or `AllowedForUnownedStaticOnly` true on a non-static grid.
  2. **Player-owned grid** (skipped entirely when the owner has copy-paste and creative is allowed): removed if `AllowedForPlayer` false; else if
     `AllowedForPlayerStaticOnly` true, removed when the grid is not static.
  3. **NPC-owned grid:** removed if `AllowedForNPC` false, or `AllowedForNPCStaticOnly` true on a non-static grid.
- `...StaticOnly` is only consulted when the matching `Allowed...` is true. **[HARD]** (else-if chains)
- The static-only messages read "Static ... grids are not allowed" although the rule removes blocks on **non-static** grids.
  **[HARD]** (message text vs. condition, `Entity.cs:485-488`)
- Counts, checked only when `> 0`: `PlayerMaxCount` (player-owned only; skipped for creative-allowed players),
  `GridMaxCount` (per grid group), `FactionMaxCount` (only when the owner is in a faction). The block being evaluated that pushes a count over its limit is the one removed. **[HARD]**
  (`Entity.cs:554-664`)
- A block whose owner changes is re-evaluated and counts are moved; faction changes recount. **[HARD]** (`Entity.cs:419-475`)

## Removal and refund

- Removal calls `grid.RemoveBlock(slimBlock, true)`; a mechanical top part is removed with its base. **[HARD]** (`BR:1318-1334`)
- Player-owned removals return the block's components to the player's inventory (via the deconstruct item), unless the block was
  built in creative or the definition is not `Public`; nothing is removed for a copy-paste admin. **[HARD]** (`BR:1311-1316`, `Utilities.ReturnComponentsToPlayer`)
- The builder gets a HUD notification with the reason and an INFO line is logged. **[HARD]** (`Entity.cs:496-498, 520`)
- NPC/unowned removals notify only if the block was built by a player. **[HARD]** (`Entity.cs:493-499, 539-545`)

## Group settings

- A named group lists definitions (`<DefinitionId Type="MyObjectBuilder_X" SubtypeId="Y"/>`) plus the same flags and counts.
  A definition in a group is evaluated by the group setting instead of its own block setting. **[HARD]** (`Entity.cs:391-395`)
- Counts on a group are shared across all its member blocks ("from the X group"). **[HARD]** (`Entity.cs:716-905` messages)
- At load, group definitions that are null, not a loadable terminal block, or `BasicAssembler` are dropped, and groups left empty are removed;
  the cleaned list is saved back. **[HARD]** (`BR:221-284`)
- When no groups remain, the mod writes a template group named `UniqueNameHere` with a placeholder id. **[HARD]** (`BR:280-284`, seen in every real cfg)
- Whether a block set in **both** a group and per-block cfg entry behaves as the code suggests (group wins) in game: **[UNVERIFIED]**.

## Special cases

- `MyObjectBuilder_Assembler/BasicAssembler` can never be restricted; a setting is forced allowed. **[HARD]** (`BR:55-58, 253-258, 304-308`)
  (Real logs show this as "Definition cannot be restricted".)
- Blocks the mod has no setting for get a default (all allowed, counts 0) and it is added to the cfg. **[HARD]** (`Entity.cs:398-406`, `BR:410-421`)

## Timing

- Config is rewritten at the end of `BeforeStart`, after an admin command, and about 100 simulation ticks after new default
  settings were added while running. **[HARD]** (`BR:437, 488, 650, 804-809`)
