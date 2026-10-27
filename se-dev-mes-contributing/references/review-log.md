# MES review log

One entry per PR: what was submitted, what the maintainer said, and the lesson. Newest first. Fold lessons into
`SKILL.md`.

## MeridiusIX/Modular-Encounters-Systems#460 Count 500 reputation as Friendly in relation and target checks (Mike Dude, 2026-10-27) - open

- **Issue:** #350, enenra: "Good catch. A PR would be appreciated."
- **Submitted:** Aligns MES with vanilla Space Engineers where 500 is `ReputationFriendlyMin`. MES previously used
  `> 500` / `>= 501` in `EntityEvaluator`, `OwnershipHelper`, `ConditionProfile`, `BroadcastSystem`, `FactionHelper`,
  and `ShipyardProfile`.
- **Testing:** In-game test using a non-static faction (`SOBAN`) across all four threshold boundaries (+500, +499,
  -500, -501) with broadcast author colors and damage trigger conditions; all passed.
- **Lesson:** When an issue already contains an agreed root-cause analysis, keep the PR body ultra-lean: `Fixes #n`
  followed directly by `### Change` and `### Testing`, omitting redundant problem essays and avoiding file-by-file line
  bullet lists.

## MeridiusIX/Modular-Encounters-Systems#459 Document missing Debug and Info chat commands in the wiki (Mike Dude, 2026-10-26) - merged 2026-10-26

- **Issue:** #356 (missing chat commands).
- **Submitted:** Documented debug and info commands (`/MES.Debug.GetKnownPlayerLocations`, `/MES.Debug.ForceDespawnMES`,
  etc.) in `AdminConfig_AdminDebugOptions.md`. enenra merged directly without comments.
- **Lesson:** Admin and debug commands should be documented strictly from what their implementation does in source,
  keeping descriptions focused on practical server admin and modder utility.

## MeridiusIX/Modular-Encounters-Systems#458 Fix in-page links in the wiki (Mike Dude, 2026-10-26) - merged 2026-10-26

- **Issue:** #355 (broken anchor links).
- **Submitted:** MkDocs generates lowercase heading ids (`#behaviordebug`), but category lists linked to CamelCase
  heading names (`#BehaviorDebug`), breaking in-page browser jumps. Lowercased all anchor targets.
- **Lesson:** In MkDocs / Python Markdown, heading anchors are generated lowercase; case-sensitive browsers fail to
  jump if links retain mixed-case headings.

## MeridiusIX/Modular-Encounters-Systems#457 Match RecolorGrid colors within 0.001 in manipulations and actions (Mike Dude, 2026-10-26) - merged 2026-10-26

- **Issue:** #328 (color precision matching).
- **Submitted:** Single-precision float discrepancies between prefab SBC files and user color vectors prevented
  RecolorGrid from matching. Replaced exact float equality and 3-decimal rounding with a tolerance comparison
  (`Vector3.DistanceSquared < 0.000001f` / `0.001f` per channel).
- **Lesson:** Floating-point color comparisons (HSV/RGB) in modding must use tolerance deltas rather than strict
  equality or string rounding to account for single-precision rounding differences in prefabs.

## MeridiusIX/Modular-Encounters-Systems#456 Fix RecolorGrid removing the wrong block after part of the grid breaks off (Mike Dude, 2026-10-26) - merged 2026-10-26

- **Issue:** #448 (RecolorGrid index mismatch on broken grids).
- **Submitted:** In `RecolorBlocks`, iterating `AllBlocks` and removing invalid blocks from `AllTerminalBlocks` threw an
  IndexOutOfRangeException or dropped unrelated terminal blocks. Fixed indexing to target the matching collection.
- **Lesson:** Never mutate or remove by index from a secondary collection while iterating a primary collection of
  different length.

## MeridiusIX/Modular-Encounters-Systems#453 Add LimitPitchTurning autopilot tag (Mike Dude, 2026-10-25) - merged 2026-10-26

- **Issue:** #450 (pitch looping when waypoint is behind grid).
- **Submitted:** Adds `LimitPitchTurning` (default false) to autopilot. When true, pitch angle is capped when the target
  is in the rear hemisphere so planes turn with yaw rather than diving into vertical loops. Follow-up commit skipped
  nose-down pitch while the target is behind, preserving nose-up banking into turns.
- **Lesson:** For 6-DOF vs aircraft steering quirks, provide opt-in autopilot tags (`LimitPitchTurning`) defaulting to
  false; test both level flight and banked turns with waypoints directly behind and below.

## MeridiusIX/Modular-Encounters-Systems#452 RotateInstallations in degrees (VillanorSE, 2026-10-25) - issue, open

- **Submitted:** feature issue: values are atan(value/45), so 90 needs a huge number and 180 is unreachable; asked
  for an opt-in degrees tag, existing tag unchanged. Need: a vehicle factory with a truck parked sideways.
- **Owner:** first draft (8 paragraphs: mechanism detail, code links, result, decisions list) was "too wordy"; the
  posted version is 4 short paragraphs. The owner said the half sentence explaining the example ("one entry per
  prefab, so here the second prefab turns 90 degrees") helped a lot.
- **Lesson:** for a feature issue, keep the need, the cause in one sentence, and the ask; explain any example value
  in plain words right where it appears.

## MeridiusIX/Modular-Encounters-Systems#451 RotateInstallationsMin/Max read the wrong entry (VillanorSE, 2026-10-25) - issue, open

- **Submitted:** bug issue only (found reading code, not seen in game): the Min/Max branch in PrefabSpawner checks
  PrefabIndexes[i] but reads the lists with the loop counter i, so Random/SelectedIndexes spawning modes get another
  slot's range. Linked the working RotateInstallations branch next to it, said it's minor, offered a small PR.
- **Owner:** posted as drafted. A companion feature draft (RotateInstallations in degrees) was held back as "too
  wordy": cut it to the need, the mechanism in one line and the proposed tag.

## MeridiusIX/Modular-Encounters-Systems#449 Fix OffsetMaxAngleFromTarget picking a new direction on every autopilot update (Mike Dude, 2026-10-24) - merged 2026-10-24

- **Issue:** #418 (offset direction jitter).
- **Submitted:** `OffsetMaxAngleFromTarget` picked a new random direction on every tick, causing the waypoint to thrash
  wildly. Fixed to select a random direction only when a new offset is requested.
- **Lesson:** Autopilot offset randomization must persist across updates until a new waypoint or offset maneuver is
  explicitly requested.

## MeridiusIX/Modular-Encounters-Systems#447 Add the /MES.Spawn.StaticEncounter chat command (Mike Dude, 2026-10-24) - merged 2026-10-24

- **Issue:** #334 (command alias `/MES.SSE` existed without a command handler).
- **Submitted:** Implemented `/MES.Spawn.StaticEncounter.<GroupName>` using `ProcessStaticEncountersAtLocation` so
  unspawned static encounters can be spawned immediately for testing without waiting for player proximity.
- **Lesson:** When implementing missing admin command aliases, route through the exact execution pathway used by
  natural triggers and existing reset commands.

## MeridiusIX/Modular-Encounters-Systems#446 Add the vanilla TargetingGroups and TieredUpdateTimes to the older NPC thrusters (Mike Dude, 2026-10-23) - merged 2026-10-24

- **Context:** Follow-up requested by enenra in #443 review ("A separate PR for the missing tags would be good").
- **Submitted:** Added `TargetingGroups` and `TieredUpdateTimes` definitions to older MES NPC thrusters to match vanilla
  thruster behavior and SE combat AI targeting.
- **Lesson:** Keep cube block definition updates in dedicated PRs separate from new block additions; keep definitions
  synchronized with vanilla SE updates.

## MeridiusIX/Modular-Encounters-Systems#445 Skip weapon lead steering while escorting (Mike Dude, 2026-10-23) - merged 2026-10-24

- **Issue:** #434 (escorts breaking formation when tracking moving targets).
- **Submitted:** Autopilot weapon lead prediction steps (`UseProjectileLeadPrediction` and `UseCollisionLeadPrediction`)
  overrode escort slot waypoints with predicted intercept coordinates. Added check to skip lead steering in escort mode.
- **Lesson:** Autonomous behaviors (escorts, patrols) must explicitly gate low-level autopilot overrides that would
  pull grids out of their assigned formation or path.

## MeridiusIX/Modular-Encounters-Systems#444 Use EscortSpeedMatch distances to scale escort speed (Mike Dude, 2026-10-23) - merged 2026-10-24

- **Issue:** #435 (escort speed scaling ignored config tags).
- **Submitted:** Linked escort speed ramping directly to configured `EscortSpeedMatchMinDistance` and
  `EscortSpeedMatchMaxDistance` tags rather than hardcoded distance thresholds.
- **Lesson:** Verify configuration tags drive the underlying calculation; hardcoded fallback numbers in subsystem
  math make tuning tags ineffective.

## MeridiusIX/Modular-Encounters-Systems#443 Add NPC versions of the Core Systems Sci-Fi hydrogen and flat atmospheric thrusters (Mike Dude, 2026-10-23) - merged 2026-10-23

- **Issue:** #428 (missing NPC variants of newer vanilla DLC thrusters).
- **Submitted:** Added zero-fuel/zero-power NPC cube block definitions for Warfare 2 and Heavy Industry thruster subtypes.
- **Lesson:** NPC cube block definitions should mirror vanilla mechanics while setting resource requirements
  consistently with existing MES NPC block profiles.

## MeridiusIX/Modular-Encounters-Systems#442 Match the vanilla remote control subtypes in ConvertAllRemoteControlBlocks (Mike Dude, 2026-10-23) - merged 2026-10-23

- **Issue:** #433 (subtypes mismatched vanilla remote control definitions).
- **Submitted:** Corrected subtype checks from `RemoteControlLarge`/`RemoteControlSmall` to
  `LargeBlockRemoteControl`/`SmallBlockRemoteControl`.
- **Lesson:** Always verify vanilla SBC `SubtypeId` strings against game definitions rather than relying on intuitive names.

## MeridiusIX/Modular-Encounters-Systems#441 Add UseCommandWaypointAsPatrolReference and UseWaypointAsPatrolReference (Mike Dude, 2026-10-23) - merged 2026-10-23

- **Issue:** #388 (patrol behavior fixed to initial spawn coordinate).
- **Submitted:** Added tags allowing patrol reference anchors to follow command waypoints or custom waypoints, enabling
  escorts and defenders to patrol around moving convoys or flagships.
- **Lesson:** Anchor-based behaviors (patrol, wander) require dynamic reference points to support moving encounters.

## MeridiusIX/Modular-Encounters-Systems#440 Check the terrain under the NPC in MatchTerrainType (Mike Dude, 2026-10-23) - merged 2026-10-24

- **Issue:** #438 (terrain evaluation checked player position instead of NPC position).
- **Review:** First draft proposed a new tag `MatchTerrainTypeAtCurrentPosition`. enenra asked to fix `MatchTerrainType`
  directly: "In my mind, MatchTerrainType should *already* match at the current position. If that is not the case, that
  sounds more like that should be fixed instead of a separate tag be added. ... As it is, without checking the current
  position's terrain, it's pretty useless."
- **Submitted (Rework):** Dropped the new tag and updated `MatchTerrainType` to evaluate the planetary voxel material
  directly under the grid.
- **Lesson:** When existing behavior is fundamentally flawed or useless, maintainers prefer fixing the core tag directly
  rather than adding a new opt-in tag. Pivot cleanly when reviewer guidance favors modifying the original tag.

## MeridiusIX/Modular-Encounters-Systems#437 Fix MatchTerrainType when the autopilot has no planet (Mike Dude, 2026-10-22) - merged 2026-10-22

- **Submitted:** Added null guard for `PlanetEntity` in `MatchTerrainType` to prevent NullReferenceExceptions when
  evaluating encounters in deep space.
- **Lesson:** Any planet-relative check must guard against null `PlanetEntity`, as encounters frequently operate or
  transition outside planetary gravity.

## MeridiusIX/Modular-Encounters-Systems#432 Give each grid its own LinkedGrids list (Mike Dude, 2026-10-20) - merged 2026-10-21

- **Issue:** #427 (shared linked grid lists caused duplicate entries and collection corruption).
- **Submitted:** Instantiated a separate `LinkedGrids` list per grid in `GridWatchers`.
- **Lesson:** Subgrid tracking collections must be allocated per instance, never shallow-copied or shared across
  watcher objects.

## MeridiusIX/Modular-Encounters-Systems#431 Track despawn attempts and DespawnMES actions per grid (Mike Dude, 2026-10-20) - merged 2026-10-21

- **Issue:** #412 (despawn counters and actions leaking across subgrids).
- **Submitted:** Scoped despawn attempt counters and action executions per grid rather than sharing state across
  multi-grid assemblies.
- **Lesson:** Multi-grid encounters require clean per-grid isolation for lifecycle actions (damage, despawn, triggers).

## MeridiusIX/Modular-Encounters-Systems#430 Detect WeaponCore 2 flare ammo for UseAntiSmartWeapons (Mike Dude, 2026-10-20) - merged 2026-10-20

- **Issue:** #380 (WeaponCore 2 countermeasure ammo changes).
- **Submitted:** Added ammo subtype and definition checks for WeaponCore 2 flare and decoy projectiles in
  `UseAntiSmartWeapons`.
- **Lesson:** Third-party integrations (WeaponCore, Water Mod) need updates when external mods refactor internal
  definitions; isolate mod-specific checks behind availability guards.

## MeridiusIX/Modular-Encounters-Systems#429 Fix MatchTerrainType not counting as a used condition (Mike Dude, 2026-10-20) - merged 2026-10-20

- **Issue:** #425 (`MatchTerrainType` did not increment `usedConditions` counter in `ConditionProfile`).
- **Submitted:** Added counter increment when `MatchTerrainType` is configured.
- **Lesson:** Whenever a condition check tag is implemented or refactored, verify it increments the condition evaluation
  counter; otherwise triggers can evaluate true unconditionally.

## MeridiusIX/Modular-Encounters-Systems#424 Fix ReportProfileError logging the same error on every call (Mike Dude, 2026-10-18) - merged 2026-10-19

- **Submitted:** `ReportProfileError` checked `profileIdSafe` against `ErrorProfiles` using a mismatched string format
  (`reason + ": [" + profileIdSafe + "]"` vs checked key), causing every call to miss the deduplication check and spam
  the log. Aligned key formatting.
- **Lesson:** Deduplication sets must use identical string formatting between key lookup and key insertion.

## MeridiusIX/Modular-Encounters-Systems#423 Fix swapped green and blue channels in GPSColors and GPSColorVariables (Mike Dude, 2026-10-18) - merged 2026-10-19

- **Issue:** #413 (GPS colors inverted green and blue channels).
- **Submitted:** Corrected `color.B` and `color.G` assignments in `ActionSystem.cs` and `EventActionExecution.cs` where
  vector Y and Z components were swapped.
- **Lesson:** Vector3 to Color conversions: X=R, Y=G, Z=B. Double check component mappings when deserializing colors.

## MeridiusIX/Modular-Encounters-Systems#422 Fix SendToAllOnlinePlayers skipping players with no character (Mike Dude, 2026-10-18) - merged 2026-10-19

- **Issue:** #414 (operator precedence bug in chat broadcast).
- **Submitted:** `!chat.SendToAllOnlinePlayers && FactionHelper.IsIdentityNPC(...) || player.Character == null` evaluated
  `&&` before `||`, skipping dead or respawning players. Added grouping parentheses.
- **Lesson:** Always group mixed boolean clauses (`&&` vs `||`) with parentheses to prevent operator precedence from
  bypassing conditions.

## MeridiusIX/Modular-Encounters-Systems#421 Fix StaticEncounterSpace check in SpawningTypeAllowedForGroup (Mike Dude, 2026-10-18) - merged 2026-10-19

- **Issue:** #417 (operator precedence bug in static space encounter check).
- **Submitted:** Missing parentheses in `type.HasFlag(StaticEncounterSpace) || type.HasFlag(StaticEncounterPlanet) && conditions.StaticEncounter`
  caused planetary conditions to be bypassed in space. Grouped flag checks.
- **Lesson:** Flag check expressions combining bitwise tests with logical operators must be grouped explicitly.

## MeridiusIX/Modular-Encounters-Systems#420 Skip invalid events in EventActionExecution loops (Mike Dude, 2026-10-18) - merged 2026-10-19

- **Issue:** #415 (NullReferenceException when loaded mods removed event templates).
- **Submitted:** Checked `Event.Valid` before accessing `Event.Profile` in `EventActionExecution` loops.
- **Lesson:** In persistent event/state managers, always guard against missing profile definitions by checking validity
  flags before dereferencing.

## MeridiusIX/Modular-Encounters-Systems#411 Fix DespawnMES trigger ignoring CleanUp and PathEnd (Mike Dude, 2026-10-17) - merged 2026-10-18

- **Issue:** #387 (despawn trigger string matching failed for CleanUp and PathEnd).
- **Submitted:** `ProcessMESDespawnTriggers` calculated category match flags for `CleanUp` and `PathEnd`, but the trigger
  execution check only tested exact string equality on the full despawn source name (e.g. `CleanUp-Distance`). Fixed check
  to use the computed match flag.
- **Lesson:** When categorizing enum or string subtypes, ensure conditional logic checks the computed category flag
  rather than requiring an exact string match on sub-types.

## MeridiusIX/Modular-Encounters-Systems#410 Fix AllowTargetFarWithoutTarget evaluation in CheckTargetFar (Mike Dude, 2026-10-17) - merged 2026-10-17

- **Issue:** #393 (tag checked in wrong method).
- **Submitted:** `AllowTargetFarWithoutTarget` was checked inside `CheckTargetNear` instead of `CheckTargetFar`. Moved to
  the correct method.
- **Lesson:** Paired near/far or min/max methods are prone to copy-paste placement errors; check method signatures and
  callers carefully.

## MeridiusIX/Modular-Encounters-Systems#408 Clean up invalid escort slots, ClearParentEscort action (Mike Dude, 2026-10-17) - merged 2026-10-18

- **Review:** enenra asked for a rename: `ClearParentEscort` matched the internal field but didn't say whether it
  runs on the escort or the leader, and "parent" means nothing to a modder. Renamed to `LeaveEscortSlot` (run on the
  escort; the leader can fill the slot again), wiki says "leader". enenra also asked whether a null check on `Escort`
  was needed; the answer linked where every behavior creates its Escort subsystem and noted the action returns early
  with no leader, so no check was added.
- **Lesson:** folded into SKILL.md section 1 (name a tag for what the modder sees and which grid runs it).
- **Lesson:** answer a "does this need a safety check" question with the line that guarantees it, not just "no".

## MeridiusIX/Modular-Encounters-Systems#406 Populate NPC identities before EntityWatcher scans world grids (Mike Dude, 2026-10-17) - merged 2026-10-17

- **Issue:** #403 (NPC thrusters shut off on server reload with thrust restrictions).
- **Submitted:** Grid entity scan on session reload occurred before NPC faction identities were cached, causing NPC
  grids to be classified as non-NPC and shutting off thrusters. Ensured identity cache population runs first.
- **Lesson:** Initialization order matters: ensure identity and cache population completes before entity watchers
  evaluate grid rules or block restrictions.

## MeridiusIX/Modular-Encounters-Systems#405 Do not clear target trigger flags during check (Mike Dude, 2026-10-17) - merged 2026-10-17

- **Issue:** #394 (target trigger flags cleared on read, breaking multi-trigger setups).
- **Submitted:** `AcquiredTarget`, `LostTarget`, `SwitchedTarget`, and `ChangedTarget` flags were cleared inside the check
  itself, so only the first trigger in the list fired. Moved flag clearing to the end of the trigger update loop.
- **Lesson:** Never clear event/state flags during trigger evaluation; clear them only after all active triggers have
  completed their evaluation step.

## MeridiusIX/Modular-Encounters-Systems#404 Clear escort relative dampening when parent invalid or leaving escort subclass (Mike Dude, 2026-10-17) - merged 2026-10-17

- **Submitted:** Reset `RelativeDampeningEntity` to `null` when parent escort becomes invalid or grid transitions out of
  escort mode.
- **Lesson:** State variables linking an entity to a parent must be explicitly cleaned up when the parent entity is
  despawned or destroyed.

## MeridiusIX/Modular-Encounters-Systems#402 Use forward velocity in direct thrust speed checks (Mike Dude, 2026-10-17) - merged 2026-10-17

- **Issue:** #392 (direct thrust runaway loop when moving backwards).
- **Submitted:** `CalculateDirectForwardThrust` compared total velocity magnitude (`velocity.Length()`) to `MaxSpeed`.
  Moving backwards triggered reverse thrusters to "slow down", which accelerated backwards infinitely. Changed to dot
  product forward velocity.
- **Lesson:** Velocity-based throttle control must use signed forward projection (dot product with heading vector),
  never raw scalar speed magnitude.

## MeridiusIX/Modular-Encounters-Systems#363 Tags & Tokens wiki pages (Mike Dude, 2026-09-23) - open, start over

- **Review:** enenra wants the pages but rejected the text: about 300 generated lines, "way too wordy while not being
  clear enough"; asked for 90% less, human-written text, with the page structure agreed first. Terms: not "Tokens"
  (suggested "Variables"); "Tag" means any MES parameter, so call the feature the "Tagging" system and always say
  Trigger Tag / Event Tag in the singular.
- **Lesson:** folded into SKILL.md section 4 (agree structure first, keep it short, Tagging terms).

## MeridiusIX/Modular-Encounters-Systems#400 MaxWaterCoverage for every spawn group (VillanorSE, 2026-10-16) - merged 2026-10-17, released in MES 2.75.00

- **Issue:** #397, enenra: "Yes, sounds good. Please submit a PR."
- **Submitted:** the MaxWaterCoverage check moved out of the requiresWater block (still only when > 0, default -1),
  plus a first wiki entry for MaxWaterCoverage. Owner reviewed, edited the wiki wording and opened the PR themself.
- **Testing:** in game with a low test value (0.1) so a coastal spot inside a territory exceeds it; /MES.GESAP shows
  the water ratio and the eligible list, so no waiting for spawns.
- **Lesson:** to test a threshold tag where the natural trigger is hard to reach, set the threshold low enough that a
  reachable spot crosses it, and read eligibility with /MES.GESAP.

## MeridiusIX/Modular-Encounters-Systems#399 Random waypoint altitude respects water (VillanorSE, 2026-10-16) - open, waiting on an in-game test

- **Issue:** #366 (2026-09-24). enenra first wanted a way to respect or ignore water, then said on Discord that just
  respecting it is fine.
- **Submitted:** GetRandomCoords uses the water-aware PlanetEntity.SurfaceCoordsAtPosition (old terrain lookup as
  fallback), plus waypoint tag `[IgnoreWater]` (default false) passed into its existing ignoreWater parameter; wiki
  entry in Waypoint.md. A deliberate default change, agreed with the maintainer, not opt-in. Build-only, no in-game test.
- **Process slip:** "push and open it" was meant as local prep; the PR went up before the owner had reviewed the
  body and wiki text. Owner then edited both on GitHub: dropped "as agreed on Discord" for a plain reason ("the
  likely more common use case") and rewrote the wiki entry to lead with what the tag does.
- **Lesson:** confirm explicitly before opening anything public on the MES repo, even after a "push and open"; the
  owner reviews the final PR body and wiki wording first.
- **Review:** enenra: "wait with this one until you've tested it", and asked whether `[IgnoreWater]` should also
  cover waypoint placement so the two match.
- **Lesson:** a build-only PR waits; test in game before opening.
- **Lesson:** when the maintainer agrees a default change, reuse an existing parameter for the opt-out so the tag
  costs one line of logic.

## MeridiusIX/Modular-Encounters-Systems#397 Let MaxWaterCoverage apply to dry-land installations (VillanorSE, 2026-10-15) - issue posted

- **Owner's edits to the draft before posting:** opened with who it affects in general instead of "my scenario mod";
  added that it's minor and doing nothing is fine; cut a simulated "one in eight" figure; described the Small/Medium
  pool setup concretely; added a plain "result of this fix" paragraph and a usage example (MaxWaterCoverage:0.6);
  closed with "If you are open to it, I'm happy to open a small PR for this."; paragraphs not hard-wrapped.
- **Lesson:** folded into SKILL.md section 0 (general framing first, honest stakes, no unverifiable numbers, result +
  example after the fix, softer close, no hard wraps).

## GV-Server-Mods/se-dev-mes#10 Clarify when inline spawn condition tags apply (VillanorSE, 2026-10-15) - merged 2026-10-18

- **Not an MES PR:** a fix to the shared se-dev-mes skill, which takes PRs directly (no issue first).
- **Why:** the skill said condition tags written inline in a spawn group's Description "are honored". In my mod, 36
  spawn groups had `[PlanetaryInstallationType:]` next to `[SpawnConditionsProfiles:]`, and every installation
  spawned Small.
- **Submitted:** one bullet in `references/spawning_and_conditions.md`. The Description is conditions profile 0, the
  referenced profiles are appended after it rather than merged, and profile 0 without a spawn type never matches. So
  inline condition tags are ignored next to `[SpawnConditionsProfiles:]`. The bullet also covers
  `[UseFirstConditionsAsPersistent:]` and the `Small` default. Branch based on upstream `main`. Problem / What MES
  does / Change / Testing headings. Testing says docs only, checked against the Workshop MES source, no in-game test.
- **Lesson:** when a skill's wording causes a mod bug, fix the skill upstream as well as the mod, and cite the
  source lines that prove the corrected wording.

## MeridiusIX/Modular-Encounters-Systems#395 issue and #396 fix (VillanorSE, 2026-10-13) - merged 2026-10-14, released in 2.75.00

- **Issue:** short, Problem / Seen in game / Fix headings, permalinks at a full SHA, measured numbers (ports raised
  0.8-9.2 m, two resets 1 m apart = waves), the fix tied to existing code (PathPlacements already ignores water),
  ended with "Happy to open a PR for this".
- **enenra:** "Yes, a PR would be welcome for this." within the day.
- **PR #396:** one line, `Fixes #395`, tested in game before opening (re-created encounter lands at its world-start
  height).
- **Lesson:** the issue-first route works when the issue carries measured evidence and a fix that matches existing
  code.

## MeridiusIX/Modular-Encounters-Systems#390 Add autopilot flight rules (VillanorSE, 2026-10-12) - declined, restructured, merged 2026-10-15

- **Submitted:** 6 autopilot tags (MaxAngleFromVelocity, RollIntoTurns, MaxBankAngle, ReturnToLevel,
  ReturnToLevelMinSpeed, MaxRotationStep), each default off, ~150 lines inside `RotationSystem.cs`.
- **enenra:** declined: the change was too large to review for code that isn't widely known, and needs someone
  available to review and maintain it.
- **Blaylock1988 (Mike Dude):** supportive, offered to test; suggested one master tag and a separate file.
- **Restructure:** `[UseAircraftFlightModel:true]` master tag; all logic in new `AircraftFlightModel.cs` (partial
  class); 6 gated lines in `RotationSystem.cs`; new `GyroscopeProfile.UpdateRotationWorld`, `UpdateRotation`
  untouched.
- **Lesson:** big core changes need isolation (master tag + own file), in-game proof with the flag off, and a second
  reviewer/tester. Size alone is a reason to decline.
- **Revision 2 (2026-10-13):** restructured as above, rebased, explanatory code comments and co-author trailers
  removed, retested (flag off: an NPC cargo ship unchanged; flag on: fighters smooth), description replaced, reply
  posted. A declined PR has no formal review, so there is no re-request button; the reply notifies the maintainer.
- **enenra on revision 2 (2026-10-13):** the wiki entries were "pretty much indecipherable" (they explained the math:
  override targets, angular velocity, formulas), and asked whether MaxRotationMagnitude and AngleAllowedForForwardThrust
  already do the same as MaxRotationStep and MaxAngleFromVelocity. Lesson: wiki entries say what the tag does to the
  grid in play, and a new tag that sounds like an existing one states the difference. Check every claim in a reply
  against the source before posting; correcting a mistaken reply plainly is fine.

- **enenra review (2026-10-15, changes requested):** three naming comments in `AutoPilotProfile.cs`: RollIntoTurns
  and ReturnToLevel take numbers but read like true/false (suggested e.g. RollIntoTurnsRate); ReturnToLevelMinSpeed
  implies a MaxSpeed that doesn't exist (suggested ReturnToLevelCutoff/CutoffSpeed). Answer: renamed to
  RollIntoTurnsMultiplier and ReturnToLevelMultiplier (as RotationMultiplier; chosen over his Rate suggestion for
  consistency with existing tags) and ReturnToLevelSpeedCutOff (as StrafeSpeedCutOff), each reply citing the existing tag at a permalink. Lesson: a
  numeric tag's name says what the number is; reuse the suffixes MES already has (Multiplier, CutOff) and cite them.
- **Merged (2026-10-15):** after the renames, enenra approved without further comments and merged the same day
  (merge commit `fc5cb29`), as "Add optional aircraft flight model for gyro-steered planes ([UseAircraftFlightModel])".
  Lesson: a large central change that was declined can still merge once it's isolated behind a master tag in its
  own file, a second modder has tested it, and every review point is answered. A merge is not a Workshop release:
  don't build on the tags until a release ships them.

## MeridiusIX/Modular-Encounters-Systems#389 Reset static encounters (VillanorSE, 2026-10-12) - merged 2026-10-14, released in 2.75.00

- **Submitted:** ResetThisStaticEncounter fix + `/MES.Debug.RefreshStaticEncounters` (dry run, `.Go`, `.Go.<group>`)
  + a mod API to trigger it.
- **enenra's comments:**
  - note should read "Successful Reset: ...";
  - the API addition "has no relation to the PR and is not used" -> removed;
  - wiki: "re-arm" unclear; no programming terms like "closing" a grid or "watchers";
  - command naming: use "reset" like the existing command; `/MES.Debug.ResetStaticEncounters` does it,
    `.Info` for the report; no "Go"; the per-group form duplicates `ResetThisStaticEncounters.<group>`;
  - "armed" terminology in player-facing text;
  - use FactionHelper's identity functions ("Not NPC does not mean it's a player");
  - the task class belongs in its own file in `Tasks/`.
- **Lesson:** no extras beyond the purpose; follow existing command verbs and `.Info`; plain words in all text; use
  MES helpers; one class per file in the right folder.
- **Revision 2 (2026-10-13):** all points addressed; replied on every thread (including a closing "Done" on the ones
  first answered with "I'll update"); re-requested review; replaced the description, which still described revision 1.
- **Found while retesting:** placement over water differs between world start and a reset; filed separately as
  MeridiusIX/Modular-Encounters-Systems#395 (one bug per issue).
- **enenra on revision 2 (2026-10-13):** the owner check must use `IsIdentityPlayer`, not the negation of
  `IsIdentityNPC` ("checking for player owned by negating NPC owned again. That is not correct"), and `IsBot` should
  never be used ("not accurate"); use the negation of `IsIdentityPlayer`. Revision 2 had switched to `!IsIdentityNPC`
  after a test plane looked like an NPC, but that plane was ownerless; `IsIdentityPlayer` was correct all along.
  Lesson: rule out the test setup (ownership, who is where) before changing code that the reviewer asked for.

## MeridiusIX/Modular-Encounters-Systems#377 Default MaxWaterDepth to -1 (VillanorSE, 2026-09-27) - merged

- **Submitted:** +15/-5. Problem section with file/line evidence of the behavior change from 48869a4.
- **enenra:** one logic issue, fixed with a suggested change (`useMaxDepth` guard); then approved.
- **Lesson:** small, evidence-led fixes to a recent regression merge quickly. Check boundary logic carefully; accept
  suggested changes.

## Field notes from Blaylock1988 (Mike Dude), 2026-10-12

- Drawn from his issues and PRs (MeridiusIX/Modular-Encounters-Systems MeridiusIX/Modular-Encounters-Systems#380, MeridiusIX/Modular-Encounters-Systems#384, MeridiusIX/Modular-Encounters-Systems#386, MeridiusIX/Modular-Encounters-Systems#388, MeridiusIX/Modular-Encounters-Systems#392, MeridiusIX/Modular-Encounters-Systems#393) and the MeridiusIX/Modular-Encounters-Systems#390
  review. Folded into SKILL.md sections 0, 1, 2, 5, 6 and 8: verify on current master, one bug per issue, permalinks at
  a SHA, concrete fixes reusing MES patterns, smallest diff, no new code comments, no AI tells or co-author trailers,
  qualified cross-repo references, document released MES only.
- Short headings in issues and PRs are kept (VillanorSE preference, 2026-10-12).

## Other contributors (patterns seen)

- MeridiusIX/Modular-Encounters-Systems#358 (jayph, zone admin commands): enenra asked to keep dot separators instead of spaces, to move a method for
  consistent ordering, and checked that a wiki line had code behind it. Approved after changes and an in-game test.
- MeridiusIX/Modular-Encounters-Systems#386 (Blaylock1988, +149): `Fixes #384`, explains the root cause, adds tags the issue asked for plus two more with a
  concrete reason ("I need these for my convoys"), includes the wiki file. Approved without comments.
