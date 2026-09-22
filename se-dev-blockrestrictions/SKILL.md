---
name: se-dev-blockrestrictions
description: Use this skill when configuring the Space Engineers Block Restrictions mod (2053202808): restricting blocks, default-settings ECs, the world cfg and log, or debugging why a restriction didn't apply.
---

# Block Restrictions (Space Engineers mod 2053202808)

General guide to configuring and debugging the Block Restrictions mod. It contains nothing specific to any one
project. Each claim carries a confidence tag:

- **[HARD]** verified in a file or source I opened (the mod's `.cs` source, a real config or log, or a published mod's `.sbc`)
- **[SOFT]** inferred from code or comments, not observed running
- **[UNVERIFIED]** plausible but unchecked - test before relying on it

Source examined: Workshop item `2053202808`, `Data\Scripts\BlockRestrictions\*.cs` **[HARD]**. Its own error
message tells users to send `BlockRestrictions.log` to "jTurp" **[HARD]** (`BlockRestrictions.cs:814`). Line numbers below
refer to that file unless noted. The mod can change; re-check against the installed version.

## Core model (read this first)

1. **What can be restricted:** only block definitions whose object builder is a `MyObjectBuilder_TerminalBlock`
   (anything with a terminal). `CubeBlock` (plain armor), `LCDPanelsBlock` and debug spheres are skipped. **[HARD]** (`Init`, 184-206)
   Conveyors, wheels, rotor tops, emissive blocks and ladders also never appear in a cfg. **[HARD]** (observed by scanning ~1,500 vanilla and ~740 mod
   definitions against a real cfg with `scripts/br_coverage.py`)
2. **Two layers:** (a) hiding the block from the G-menu/toolbar for non-admin players via the definition's `Public` flag;
   (b) a server-side scan of every grid that removes and refunds disallowed blocks. **[HARD]** (`CheckToolbarLocal`, `Entity.cs`)
3. **Per-category rules per block:** allowed for `Player`, `NPC`, `Unowned`; optional `...StaticOnly`; optional
   `PlayerMaxCount`/`GridMaxCount`/`FactionMaxCount` (0 = unlimited). **[HARD]**
4. **Category is decided per grid, not per block:** owner = first big owner, else first small owner; no owner =
   Unowned; owner that maps to a Steam ID = Player; any other owner = NPC. A grid is "static" if any grid in
   its mechanical group is static. **[HARD]** (`Entity.UpdateOwner`, `GridCollection`)
5. **Settings file:** `BlockRestrictions.cfg` in **world storage**, generated on first load with one entry per
   terminal block (default: everything allowed). **[HARD]** See `references/config-format.md`.
6. **A mod ships its own restrictions** by adding an EntityComponent whose SubtypeId starts with `BlockRestrictions`;
   this is read at load, and only fills in blocks the cfg does not already know. **[HARD]** See `references/default-settings-ec.md`.

## The trap that costs the most time

**An existing cfg entry beats a default-settings EC.** If the world has ever loaded before, every terminal block
already has an entry, so a new or edited EC is skipped unless it sets `ForceSetting` true or the cfg is deleted.
**[HARD]** (`BeforeStart` 366-369; a published restriction mod carries the comment "server block restrictions config needs to be deleted to
accept new changes", and a real log shows 45 of 48 entries "already exists (skipping this default setting)").
Always verify with `scripts/br_log.py` instead of assuming it applied.

## Workflow

1. **Find candidates.** Load the world once with the mod active, then read the generated cfg
   (`scripts/br_cfg.py summary|list`). It is the authoritative list of restrictable blocks for that world's mod set.
   To see which of a mod's blocks are restrictable at all: `scripts/br_coverage.py CFG MODDIR`.
2. **Write the defaults** as an EC: `scripts/br_ec.py generate --input list.txt --output MyRestrictions.sbc`
   (put the file in the mod's `Data\` folder). Types are `MyObjectBuilder_<TypeId>/<SubtypeId>` exactly as in the cfg.
3. **Lint before loading:** `scripts/br_ec.py check MyRestrictions.sbc --cfg <cfg>` - reports bad ids, non-boolean values, duplicates,
   and how many entries the existing cfg would shadow.
4. **Apply:** either delete the world's `BlockRestrictions.cfg` (loses hand edits) or generate with `--force`.
   `--force` appends a second entry for an already-configured block, so cfgs can grow duplicates. **[SOFT]** (`BeforeStart` 366-379;
   check with `br_cfg.py dups`).
5. **Verify** after loading: `scripts/br_log.py <log>` (per-EC counts of applied/skipped/unresolved entries), then
   `scripts/br_cfg.py list <cfg> --restricted`. Finally test in game as a normal (non-creative) player and as an NPC-owned grid.

## Scripts (Python 3.8+, stdlib only; all tested on real cfg/log/EC files)

| Script | Purpose |
|---|---|
| `scripts/br_cfg.py` | `summary`, `list` (filters), `dups`, `diff` on a `BlockRestrictions.cfg` |
| `scripts/br_ec.py` | `generate` a default-settings `.sbc`; `check` an existing one (optionally against a cfg) |
| `scripts/br_coverage.py` | Which of a mod's `CubeBlocks` definitions appear in a cfg (restrictable) and which do not |
| `scripts/br_log.py` | Summarize a `BlockRestrictions.log` load trace |
| `scripts/br_common.py` | Shared parsing helpers (imported by the others) |

## References

- `references/mechanics.md` - enforcement rules, G-menu hiding, creative/admin bypass, refunds, group settings, timing
- `references/config-format.md` - cfg/log/PlayerData files, locations, schema, defaults, encoding quirk
- `references/default-settings-ec.md` - the EntityComponent format, precedence rules, ForceSetting, real-world examples
- `references/pitfalls.md` - failure modes and the open [UNVERIFIED] questions

## Boundaries

- This skill covers the mod's configuration, not writing mods that call it. The mod exposes no public API in the source examined; it talks to
  the Research Framework mod (`2307665159`) through a message packet. **[HARD]** (`BlockRestrictions.cs:552, 846-848`)
- Player-facing behavior (HUD messages, refunds) was read from code, not observed in a running game. **[SOFT]**
