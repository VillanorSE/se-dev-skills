---
name: se-dev-mes-contributing
description: Use this skill whenever you want to send something to Modular Encounters Systems (MES) itself rather than just use it in a mod. For example you found an MES bug or odd behavior and want to report it, want to suggest or add a feature or tag, are writing an issue, opening or updating a pull request, writing or fixing an MES wiki page, replying to the maintainer's review, or wondering whether a fix belongs upstream at all. Covers how to make the case for a change, what gets accepted, MES code and chat-command conventions, wiki style, and tone.
---

# Contributing to Modular Encounters Systems

How to get changes into MES upstream. Built from real issues and reviews; `references/review-log.md` records each one.
**Add every new review outcome to the log and fold any new lesson into this file.**

Repo: `MeridiusIX/Modular-Encounters-Systems`, branch `master`. enenra reviews and merges. The maintainer checks
claims against the code, so every post should read like a modder wrote it after reading the code. A merge is not a
Workshop release.

## 0. Issue first (MES only)

MES prefers agreeing the approach in an issue before code arrives. Other repos (e.g. the `se-dev-mes` skill,
`GV-Server-Mods/se-dev-mes`) take PRs directly.

### Before posting
- Re-check the bug on the latest upstream `master` right before posting, and cite that commit. Confirm an older report
  is still real before commenting on it.
- Trace every code path that could cause the symptom against what was seen in game, including timing. Drop paths that
  can't produce it. Never present a guess as the cause; if two causes are possible, say so or verify first.
- One bug per issue. A second, related bug gets its own issue.
- Draft first. The person posting reviews the draft before anything goes up.

### Writing the issue
- Short: what is broken, where (file and line), what was seen, the fix.
- Open with who it affects in general ("MES encounter mods that mix land and water spawns ..."), not with your own mod.
  Your setup goes under "Seen in game" as the concrete example (MeridiusIX/Modular-Encounters-Systems#397).
- Say honestly how much it matters, even when that's "minor; doing nothing isn't really a problem, but the fix is
  small too". It reads as a fair report, not a demand.
- Leave out numbers from your own analysis or simulation that the maintainer can't check ("one sea check in eight");
  describe the mechanism and what you saw instead.
- Simple headings when they help ("Problem", "Seen in game", "Fix"); short, clear wording under each. A one-paragraph
  bug doesn't need them.
- Brief reasoning: a sentence or two on why the fix is right or safe ("other mods are unaffected because the old path
  still runs when the tag is absent"). Not an essay.
- Plain language. Keep tag and method names out of code formatting in the prose where you can.
- Link the code, don't paste it: a permalink at a full commit SHA (`.../blob/<sha>/path/File.cs#L47`) on its own line,
  so GitHub renders the snippet.
- Realistic example values (an extreme number pulls attention to the number instead of the problem).
- A concrete fix: say exactly what to change. A simpler fallback option is fine.
- After the fix, a short plain "result" paragraph: what changes for people who don't use the tag (nothing) and for
  those who do, plus one example of how you'd use it ("I would set my land installations to MaxWaterCoverage:0.6").
- Tie the fix to code that already works, and link the working code next to the broken code. It shows the fix is
  consistent with MES and is easy to verify:
  - a sibling path already does it right ("the hover thrust path already uses the forward component of velocity; use
    the same in the direct thrust path", MeridiusIX/Modular-Encounters-Systems#392);
  - similar checks behave differently ("the BehaviorTrigger checks only read their flag; the four target checks also
    clear it, so only the first trigger sees the event"): the inconsistency is the evidence.
- Say when it started if git history shows it ("added in 2.1.22").
- For features: the need, one or two possible approaches, and which questions the maintainer should decide (naming,
  where the code lives, a master tag).
- Keep a feature issue to a few short paragraphs: the need, the cause in one sentence, the ask. Explain an example
  value in plain words where it appears ("one entry per prefab, so here the second prefab turns 90 degrees");
  an 8-paragraph draft was cut as too wordy (MeridiusIX/Modular-Encounters-Systems#452).
- End with "If you are open to it, I'm happy to open a small PR for this." Then wait for the maintainer to agree.
- Don't hard-wrap paragraphs in text for GitHub: one line per paragraph (GitHub reflows it).

## 1. Scope: what gets accepted

- Small, obviously correct fixes merge fast. Most merged PRs are 1-70 lines.
- Smallest diff that fixes it. No drive-by refactors, renames or style changes.
- Follow the surrounding code's patterns (naming, tag parsing, structure) so the change looks like it belongs; reuse an
  existing method instead of adding a new one where possible.
- Every line serves the stated purpose. Anything "useful later" (an API hook, an unused option, a helper for your own
  mod) is unrelated and comes out (MeridiusIX/Modular-Encounters-Systems#389).
- New behavior is opt-in: new tags whose defaults leave the existing code path untouched, so grids without the tags run
  exactly the old code. Defaults that only take effect once the feature is switched on are fine; say so.
- Large changes to central systems (autopilot, rotation, spawning) need a reviewer who knows the code and someone
  available to maintain it (MeridiusIX/Modular-Encounters-Systems#390). To make one reviewable: one master tag that defaults off; all new logic in its own
  file (a `partial class`); existing methods untouched; the PR lists exactly which existing lines change; in-game
  evidence with the flag off (ideally a dedicated server) and before/after with it on; a second modder tests it.
- Don't duplicate an existing command or tag; search `ChatMessage.cs` and the wiki first.
- Name a numeric tag by what the number is, with a suffix MES already uses (`RotationMultiplier`, `StrafeSpeedCutOff`);
  a bare phrase like `RollIntoTurns` reads as true/false, and `MinSpeed` implies a `MaxSpeed` (MeridiusIX/Modular-Encounters-Systems#390).
- Name a new tag for what the modder sees and which grid runs it, not after an internal field: `ClearParentEscort`
  became `LeaveEscortSlot`, since "parent" didn't say whether it runs on the escort or the leader
  (MeridiusIX/Modular-Encounters-Systems#408).
- When an existing tag or check is fundamentally broken or useless in practice, maintainers prefer fixing the core tag directly rather than adding a new opt-in tag (e.g. `MatchTerrainType` evaluating ground under the grid instead of player spawn coords, MeridiusIX/Modular-Encounters-Systems#440).
- A bug fix found while building a feature goes in its own commit or issue.

## 2. Code conventions

- C# 6, SE mod whitelist. Build and run the whitelist check before pushing.
- Match surrounding style: tabs, braces on the same line, blank line after `{` and before `}` in methods, `this.` as the
  file uses it. Keep method order consistent with the file.
- No new code comments, unless continuing a pattern the file already has (e.g. the `//TagName` line above each tag
  parse). Put the reasoning in the PR description.
- Use MES's own helpers: `FactionHelper` for player/NPC identity. A player check is `IsIdentityPlayer`, never the
  negation of `IsIdentityNPC` ("not NPC" is not "player"), and never `IsBot`; check names at HEAD;
  `TagParse.*Check` in the profile's `InitTags`.
- Long-running work goes in its own class in `Tasks/`.
- Multi-grid encounters: keep lifecycle tracking, despawn counters, and linked grid lists isolated per grid instance rather than shared across watcher objects (MeridiusIX/Modular-Encounters-Systems#431, MeridiusIX/Modular-Encounters-Systems#432).
- Event flags: do not clear event/trigger flags during evaluation checks; clear them after all triggers in the update loop have finished evaluating (MeridiusIX/Modular-Encounters-Systems#405).
- Floating-point comparisons: use tolerance deltas (e.g. `Vector3.DistanceSquared < 0.000001f` for color matching) rather than strict equality or string rounding to handle single-precision serialization differences (MeridiusIX/Modular-Encounters-Systems#457).
- Operator precedence: always group mixed `&&` and `||` clauses with explicit parentheses (MeridiusIX/Modular-Encounters-Systems#421, MeridiusIX/Modular-Encounters-Systems#422).
- No per-update allocations in autopilot/behavior code.

## 3. Chat commands

- Dots separate everything: `/MES.Debug.Thing.Value`.
- Follow existing verbs: next to `ResetThisStaticEncounters`, the new one is `ResetStaticEncounters`.
- A report variant is `.Info` on the action command (`/MES.Debug.ResetStaticEncounters.Info`). The `/MES.Info.`
  family holds only `Get...` state reports. No `.Go`.
- Player-visible messages say what happened in plain words: "Successful Reset: <group>".

## 4. WebWiki entries (`WebWiki/docs/*.md`)

Audience: encounter modders and server admins.

- Only document what the PR's code implements; the maintainer checks wiki lines against the code.
- A new page or explainer needs its structure agreed with the maintainer first, and stays short and written by a
  person: long generated prose is rejected outright, "90% less text" (MeridiusIX/Modular-Encounters-Systems#363).
  Single tag cards in the existing format are fine.
- Terms: a bare "Tag" means any MES parameter, so the TriggerTag/EventTag feature is the "Tagging" system and the
  singular is always "Trigger Tag" or "Event Tag". Not "Tokens"; the maintainer suggested "Variables" (#363).
- No programming or insider terms ("closing" a grid, "watchers", "re-arm", "ramp frames", "API"). Say what the player
  or modder sees.
- Behavior and default in a few sentences; what the tag is for and not for; one example value if it helps.
- If a new tag sounds like an existing one, say how it differs in its entry (e.g. MaxRotationStep vs MaxRotationMagnitude).
  The maintainer will ask otherwise (MeridiusIX/Modular-Encounters-Systems#390).
- When one entry covers several commands or values, tie every consequence to the one that causes it ("When an old grid
  is removed using chat command 1, ..."). A sentence with no subject after a report-only variant reads as if that
  variant does it too (MeridiusIX/Modular-Encounters-Systems#389 wiki wording).
- Edit only `WebWiki/docs` (not `WebWiki/site` or `patch_notes.md`). Keep the file's CRLF line endings.
- Copy the format of a neighbouring entry (the `Tag:` cell is padded with `&nbsp;` to the same width):

```
<!--TagName-->
|Tag:&nbsp;...&nbsp;|TagName|
|:----|:----|
|Tag Format:|`[TagName:Value]`|
|Description:|What it does, in modder terms. Default value is `x`.|
|Allowed Values:|`true`<br>`false` / Any Number Greater or Equal to `0` / ...|
|Multiple Tag Allowed:|No|
```

```
|Setting:|Readable Name|
|:----|:----|
|XML:|`N/A`|
|Chat Command:|`/MES.Debug.Command`|
|Description:|What it does and when to use it.|
|Allowed Value:|...|
```

## 5. PR text and commits

- Title: what changes, in MES terms (`Fix X for Y`, `Add Z`).
- Description: `Fixes #n`, then short headed sections (e.g. Problem, Change, Testing) with a few clear lines each:
  what changed and why, and how it was tested in game (say what wasn't: dedicated server, multiplayer).
- When a PR directly fixes an issue that already has an agreed root cause and analysis, omit the redundant "Problem"
  recap. Lead with `Fixes #n` followed directly by `### Change` and `### Testing` (MeridiusIX/Modular-Encounters-Systems#460).
- Under `### Change`: keep it high-level (the logical mechanism in a few sentences). Do not list out file-by-file line
  diffs or granular code edits — the maintainer can view the GitHub "Files changed" diff directly.
- In-game testing: describe the concrete test setup, values tested, and observed results.
- Credit testers and whoever suggested the approach.
- Before pushing: `git fetch upstream` and rebase onto current `master`. Work from a fork (`gh repo sync`), one branch
  per PR from the fork's `master`.

## 6. Tone and voice (issues, PRs, replies, commit messages)

- First person singular: "I", "my scenario mod". Never "we"/"our".
- No AI tells: no "Generated with" footers or `Co-Authored-By` trailers, no emoji, no bold-label bullets ("Gotcha:"),
  no parenthetical size hints ("(~20 lines)"), no polished filler.
- Keep the poster's own wording when editing their draft; fix facts and typos, don't rewrite.
- Frame claims as findings ("I looked at X and found Y"). Don't volunteer statements about AI use.
- Check every factual claim against the source or the wiki before it goes in.
- Outside the MES repo, qualify references: `MeridiusIX/Modular-Encounters-Systems#392`, never a bare `#392`.

## 7. Answering review

- Reply to every line comment briefly: what changed, or why not. Agree when the point is right.
- Push as new commits or a clean rewrite (`--force-with-lease`) and say which.
- Close every thread you answered with "I'll update" once it's done, replace the PR description if it describes
  an older version, and re-request review (the circular arrow next to the reviewer).
- Retest in game after changes and update the testing line.
- If the maintainer declines, ask what would make it acceptable before reworking.

## 8. After posting

- Don't build your own content on a tag or behavior until it's merged and released upstream.
- Docs, skills and tag lists describe released MES only, never an open PR or fork branch. Remove workarounds only
  after the fix ships.
- Keep the draft (title, body, replies) in a notes file named with the PR number once it exists:
  `mes-pr-<number>-<topic>.md`, first line `# MES PR #<number>: <topic>`.

## References

- `references/review-log.md`: every PR and issue, the review, and the lesson.
