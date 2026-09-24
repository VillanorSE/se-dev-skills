# se-dev-skills

Claude Code skills for Space Engineers modding, written for AI coding agents (and useful as plain reference docs for humans too).

Each skill is general-purpose: no project-specific content, nothing tied to any particular mod or server. Claims are tagged by confidence:

- **[HARD]** verified in a file or source that was actually opened (mod `.cs` source, a real config/log, or a published mod's `.sbc`)
- **[SOFT]** inferred from code or comments, not observed running
- **[UNVERIFIED]** plausible but unchecked — test before relying on it

## Skills

| Skill | Covers |
| :--- | :--- |
| [`se-dev-blockrestrictions`](se-dev-blockrestrictions/) | The Space Engineers [Block Restrictions](https://steamcommunity.com/sharedfiles/filedetails/?id=2053202808) mod: restricting blocks, default-settings ECs, the world cfg and log, debugging why a restriction didn't apply. |
| [`se-dev-shipcore`](se-dev-shipcore/) | The Space Engineers [Ship Core Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3552595651) mod: core XMLs, manifest, block groups, no-core profile, block limits, world config, load failures. |
| [`se-dev-reputation`](se-dev-reputation/) | Space Engineers faction reputation and NPC faction lifecycle: `StaticReputation`, vanilla damage/decay reputation, economy thresholds, MES reputation actions, why unwanted factions (e.g. `SPRT`) appear and removing them from a save. |

## Installing

Each skill folder is self-contained (`SKILL.md` + `references/` + `scripts/`). Copy the one you want into your skills directory, e.g.:

```bash
cp -r se-dev-blockrestrictions ~/.claude/skills/
```

## License

MIT — see [LICENSE](LICENSE).
