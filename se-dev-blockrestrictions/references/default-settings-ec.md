# Default-settings EntityComponent

A mod (or a world-support mod) sets restrictions without touching the player's cfg by defining an EntityComponent. Tags: **[HARD]**
verified in source/real files, **[SOFT]** inferred, **[UNVERIFIED]** unchecked.

## Format **[HARD]** (matches the loader at `BR:322-405` and real published files)

```xml
<Definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <EntityComponents>
    <EntityComponent xsi:type="MyObjectBuilder_InventoryComponentDefinition">
      <Id>
        <TypeId>Inventory</TypeId>
        <SubtypeId>BlockRestrictions_YourName</SubtypeId>   <!-- must START WITH "BlockRestrictions" -->
      </Id>
      <Description>
        [?xml version="1.0" encoding="utf-16"?]
        [DefaultSettings xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"]
          [DefaultSetting]
            [Type]MyObjectBuilder_Beacon/SomeSubtype[/Type]
            [PlayerMaxCount]0[/PlayerMaxCount]
            [GridMaxCount]0[/GridMaxCount]
            [FactionMaxCount]0[/FactionMaxCount]
            [AllowedForNPC]true[/AllowedForNPC]
            [AllowedForPlayer]false[/AllowedForPlayer]
            [AllowedForUnowned]true[/AllowedForUnowned]
            [AllowedForNPCStaticOnly]false[/AllowedForNPCStaticOnly]
            [AllowedForPlayerStaticOnly]false[/AllowedForPlayerStaticOnly]
            [AllowedForUnownedStaticOnly]false[/AllowedForUnownedStaticOnly]
          [/DefaultSetting]
        [/DefaultSettings]
      </Description>
    </EntityComponent>
  </EntityComponents>
</Definitions>
```

- The mod replaces `[` with `<` and `]` with `>` throughout the Description, trims it, and deserializes it as `DefaultSettings`. **[HARD]** (`BR:329-342`)
  So the Description must use square brackets, and no literal `[` or `]` may appear in it for any other purpose.
- Only the SubtypeId prefix is checked (`StartsWith("BlockRestrictions")`); every EC definition in the game is scanned. **[HARD]** (`BR:323-325`)
  The published examples all use `<TypeId>Inventory</TypeId>`. **[HARD]**
- Field order in the examples: `Type`, three counts, `AllowedForNPC`, `AllowedForPlayer`, `AllowedForUnowned`, three `...StaticOnly`. `scripts/br_ec.py generate`
  reproduces an existing entry byte-for-byte apart from whitespace. **[HARD]** (compared against a published file)
- `<ForceSetting>true</ForceSetting>` is a boolean element of `DefaultSettings`; no published example sets it. Placement before the first
  `DefaultSetting` follows the class's field order. **[SOFT]** (`Settings/DefaultSettings.cs`)
- An XML comment inside `Description` is a hazard for many SBC description parsers; whether this mod's EC tolerates one is **[UNVERIFIED]**. Put comments outside the
  `<Description>` element (the published examples do).

## Precedence and application rules **[HARD]** (`BR:208-421`)

1. The cfg is read first, so every block already in it is in `SettingsDict` before any EC runs.
2. For each `DefaultSetting`: unparseable `Type` -> skipped; existing setting and `ForceSetting` false -> skipped; block definition not loaded -> skipped; otherwise added.
3. Blocks still without a setting afterwards get all-allowed defaults.
4. Result: **a default-settings EC only takes effect on a block the world's cfg has never seen** (fresh world, deleted cfg, newly added mod block), or with `ForceSetting`.
5. The same block listed twice in one EC is harmless: the second is skipped as "already exists". (One published EC lists a single block four times.)

## `ForceSetting` side effect **[SOFT]**

The add path (`BR:379`) appends the EC entry to the cfg's `Settings` list even when a setting for that block already exists, replacing the in-memory one. The cfg may therefore contain two
entries for one block; on the next load the later entry wins. Detect with `scripts/br_cfg.py dups`. Growth per load with `ForceSetting` left on is
**[UNVERIFIED]** - test on a copy.

## Non-terminal blocks in an EC **[UNVERIFIED]**

The EC path only requires that the definition exists, not that it is a terminal block. Reading the code, such an entry would hide the block via `Public=false` for non-admins
but never be enforced on placed grids (enforcement looks the block up in the terminal-only list). Not observed in game.

## Real examples worth reading

- The Modular Encounters Systems mod ships `BlockRestrictions_MES_Blocks` (48 entries) in `Data\Blocks\jTurpProgressionMod.sbc`: NPC-only thrusters, suppressor antennas and
  "Proprietary" blocks are `AllowedForPlayer=false`, `AllowedForNPC=true`. **[HARD]**
- A published server-config pair (`BlockRestrictions_GVKSettings`, 43 entries; `BlockRestrictions_GVKHovers`, 60 entries) sets NPC-only blocks with `AllowedForUnowned=false`. **[HARD]**
- MES's own NPC blocks must stay `AllowedForNPC=true` or the encounter grids lose those blocks on spawn. **[SOFT]** (follows from the enforcement rules)

## Testing

`scripts/br_ec.py check EC.sbc --cfg BlockRestrictions.cfg` (static), then load the world and run `scripts/br_log.py BlockRestrictions.log`.
Expect `Found EC: Subtype = <yours>` and a per-entry result. If the EC is not found at all, the SubtypeId prefix or the file location is wrong.
