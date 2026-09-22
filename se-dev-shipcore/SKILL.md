---
name: se-dev-shipcore
description: Use this skill when authoring or debugging Space Engineers Ship Core Framework (3552595651) content: core XMLs, manifest, block groups, no-core profile, block limits, world config, or load failures.
---

# Ship Core Framework (Space Engineers mod 3552595651)

General guide to writing and debugging Ship Core Framework (SCF) content packs. It contains nothing specific to any one
project. Each claim carries a confidence tag:

- **[HARD]** verified in a file or source I opened (SCF's `.cs` source, a real log, or a published content pack)
- **[SOFT]** inferred from code or behavior of a standard component, not observed running
- **[UNVERIFIED]** plausible but unchecked - test before relying on it

Source examined: Workshop item `3552595651`, `Data\Scripts\ShipCoreFramework\**` and `API_USAGE.md` **[HARD]**. The mod is
actively changing (its API doc mentions v4.5); re-check against the installed version before trusting field lists.
`Config\ModConfig.XmlModels.cs` is the authoritative schema.

## Core model (read this first)

1. **SCF ships no cores.** Content comes from *content packs*: any mod in the world that provides `Data\ShipCoreConfig_Manifest.xml`,
   `Data\ShipCoreConfig_Groups.xml` and/or `Data\ShipCoreConfig_No_Core.xml`. The loader visits every loaded mod and merges them. **[HARD]**
   (`ModConfig.Loading.cs:29-34`) See `references/config-files.md`.
2. **A core is a block.** A block is a core when it is a functional (terminal) block whose **SubtypeId** equals a core file's `<SubtypeId>`;
   the block's TypeId is not checked. **[HARD]** (`Utils.Grid.cs:50-55`). Published packs use `TypeId FunctionalBlock`. **[HARD]** (observed)
3. **A core file defines rules** for every grid group that carries it: hard caps (blocks/PCU/mass), per-player/faction counts,
   speed and stat multipliers, defense multipliers, and a list of `BlockLimits` that count weighted blocks from named `BlockGroups`.
   See `references/core-schema.md`.
4. **Grids without a core** are governed by one *no-core profile*, which an admin must **select** per world. **[HARD]**
5. **Enforcement is server-side**; violating blocks are shut off, damaged, deleted or exploded per each limit's `PunishmentType`.
   See `references/enforcement.md`.

## The traps that cost the most time

- **Nothing runs until a no-core profile is selected.** With `<SelectedNoCoreUniqueName/>` empty, the framework reports its config as unavailable:
  "No content-pack no-core profile is selected. Use /core listnocores and /core select <name>, then reload the world." **[HARD]**
  (`ModConfig.Loading.cs:108-119`, seen in a real log once per world load). Run `/core select <name>`, save, reload. **[HARD]**
- **One bad value can stop the whole config from loading.** Duplicate names, an unknown manifest group, a bad direction budget, or an
  XML value XmlSerializer cannot read make the loader throw. **[HARD]** (throws in `ModConfig.Loading/Validation.cs`; whether the world then refuses to
  open is **[SOFT]**). Run `scripts/sc_lint.py` on *every pack in the world together* before loading.
- **Silent no-ops:**
  - A `<BlockLimits>` with no `<BlockGroups>` matches no block, so it never counts or restricts anything. **[HARD]** (`GetWeight` returns 0 with no groups)
  - An unknown group name only logs a warning and is ignored. **[HARD]** (`ModConfig.Loading.cs:472-473`)
  - A core file listed in the manifest but not found is skipped with a warning. **[HARD]** (`Loading.cs:269-273`)
  - A mistyped element name is ignored by XmlSerializer. **[SOFT]** (standard .NET behavior; a real published pack contains elements this version's schema
    does not define, e.g. `ReloadModifier`; whether that pack loads cleanly was not tested)
- **Multiple `<AllowedDirections>`, not comma-joined.** It is a `List<DirectionType>`; each value is its own element. **[HARD]** (declared type) - a comma list
  is an invalid enum value. **[SOFT]**
- **Group-name collisions across packs throw.** Two packs that both define a group called `Drills` cannot be loaded together. **[HARD]**

## Workflow

1. **Layout the pack**: manifest, groups, no-core file, one file per core (`references/config-files.md`).
2. **Lint**: `python scripts/sc_lint.py <pack> [<other packs in the world> ...] --world ShipCoreConfig_World.xml --blocks <mod dirs>`.
3. **Check block coverage**: `python scripts/sc_coverage.py <pack> --blocks <game+mod CubeBlocks dirs> --uncovered Thrust Gyro`
   - dangling group entries (wrong TypeId, missing mod) and blocks no limit can ever touch.
4. **Review numbers**: `python scripts/sc_report.py <pack>` and `--limits "<core>"`.
5. **Load the world**, then `python scripts/sc_log.py SpaceEngineers_*.log` to confirm cores loaded and see the config warnings.
6. In game: `/core select <name>` (admin) once; `/core listcores`, `/core limits`, `/core info` to inspect (`references/enforcement.md`).

## Scripts (Python 3.8+, stdlib only; all tested on real packs, logs and world configs)

| Script | Purpose |
|---|---|
| `scripts/sc_lint.py` | Loader-faithful validation of packs (+ optional world config and block definitions) |
| `scripts/sc_report.py` | One-row-per-core table (CSV optional) and per-core limit listing |
| `scripts/sc_coverage.py` | Group entries vs real block definitions: dangling entries, uncovered blocks |
| `scripts/sc_log.py` | Summarize SCF's load trace, warnings and errors in a game log |
| `scripts/sc_common.py` | Shared loader (imported by the others) |

## References

- `references/config-files.md` - file names, load order/merging, manifest, groups, no-core, world config, type normalization
- `references/core-schema.md` - every `<ShipCore>`/`<BlockLimits>` field, defaults, enums, direction rules, speed model
- `references/enforcement.md` - how limits, punishments, grace timers, NPC/ignore rules and commands behave; API summary
- `references/pitfalls.md` - failure modes and open [UNVERIFIED] questions

## Boundaries

- Covers content authoring/config. The C# API (`ShipCoreFrameworkServerApi` / `ClientApi`, install by copying `ApiData.cs` and `SCF_ModAPIClient.cs`) is
  summarized in `references/enforcement.md` only. **[HARD]** (`API_USAGE.md`)
- Behavior was read from code and real logs, not verified in a live multiplayer session. **[SOFT]**
