# Pitfalls and open questions

Tags: **[HARD]** verified in source/real files, **[SOFT]** inferred, **[UNVERIFIED]** unchecked.

## Things that fail silently

| Symptom | Cause | Check |
|---|---|---|
| EC changes have no effect | cfg already has entries for those blocks **[HARD]** | `br_log.py` -> "skipped, setting already exists" |
| Restriction on an armor/conveyor/wheel block does nothing | not a terminal block, never listed **[HARD]** | `br_coverage.py CFG MODDIR` |
| EC entry ignored | that block's mod is not loaded in the world **[HARD]** | log: "Unable to retrieve MyCubeBlockDefinition" |
| Restricted block appears in the G-menu for you | you are admin with copy-paste/creative allowed **[HARD]** | see `mechanics.md` (`allowAdmin`) |
| Restriction on `BasicAssembler` does nothing | hard-coded exception **[HARD]** | log: "cannot be restricted" |
| NPC/encounter grids lose blocks on spawn | `AllowedForNPC` or `AllowedForUnowned` false for a block they use **[SOFT]** | `br_cfg.py list --changed` |
| Config edits vanish | mod rewrites cfg from memory **[SOFT]** | edit with the world closed |
| Log missing on a dedicated server | log is in local storage, cfg in world storage **[HARD]** | look in the server's local mod storage |

## Tooling traps

- The cfg declares UTF-16 but is 8-bit text **[HARD]**; naive parsers throw. Use the bundled scripts.
- `SubtypeId` may be empty; the cfg writes `(null)` **[HARD]**. Whether an EC accepts `(null)` in `<Type>` is **[UNVERIFIED]**.
- Some `.sbc` files write `<TypeId>Projector</TypeId>`, others `<TypeId>MyObjectBuilder_Projector</TypeId>` **[HARD]** (observed in mod definitions); normalize before comparing.
- On Windows, Python launched from Git Bash needs Windows-style paths (`C:/...`), not `/tmp/...` **[HARD]** (observed while testing these scripts).

## Observations that are not guarantees

- Terminal-type definitions occasionally have no cfg entry (one vanilla `LargeGatlingTurret/AutoCannonTurret` was absent from a real cfg while all other types in that scan were present). Cause not determined. **[UNVERIFIED]**
- When a restricted block's definition is `Public=false` on the machine doing the removal, `ReturnComponentsToPlayer` returns without refunding (`Utilities.cs`: early return if `!Public`). Whether a player actually loses
  the components in practice depends on that host's state. **[UNVERIFIED]**
- Count limits and static-only flags are enforced by removal after placement, so a player can briefly place the block before it is removed (scan runs every 10 ticks). **[SOFT]**
- A block present in both a group and a per-block entry uses the group setting. **[HARD]** in code, **[UNVERIFIED]** in game.

## What was not examined

- Behavior with the Research Framework mod (`2307665159`) beyond the message hand-off. **[UNVERIFIED]**
- Interaction with other block-gating mods and unlock systems. **[UNVERIFIED]**
- Whether updates to the mod change these findings; re-verify against the installed source. **[UNVERIFIED]**
