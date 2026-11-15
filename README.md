# ada-skills

Team skill packs for Ada's agents, in the open Agent Skills format
(`SKILL.md`). Install with the `skills` CLI:

```bash
npx skills add AdaDev10/ada-skills
```

Or install a single skill:

```bash
npx skills add AdaDev10/ada-skills --skill trader-scanner -a claude-code
```

Skills install to the agent's skills directory (for example
`~/.claude/skills/` for Claude Code / Muse). Requires Node.js 22.20+.

## Skills in this repo

### Day-trader pack (11 skills)

Intraday stock-trading workflow: scan for opening-range breakouts, check
news, compute entry/exit (take-profit / stop-loss), size the position,
check risk, build a ticket, and monitor the trade. Flat by 15:55 New York
time; nothing held overnight.

| Skill | What it does |
|---|---|
| `trader-scanner` | Opening-range breakout scan (ORB) |
| `trader-news` | News check for a symbol |
| `trader-entry` | Entry computation |
| `trader-exit` | Take-profit / stop-loss targets |
| `trader-budget` | Position sizing |
| `trader-risk` | Risk check (rejects trades below 1:1 reward:risk) |
| `trader-broker` | Order execution — **Bybit demo only** (xStocks spot, see below) |
| `trader-alerts` | Trade monitoring / alerts |
| `trader-analyst` | Post-trade analysis |
| `trader-pelosi` | Congressional-trading disclosure lookup |
| `trader-timemachine` | Backtest a rule over past sessions |

**Safety gates (non-negotiable):** demo trading only (Bybit demo API,
`api-demo.bybit.com`; mainnet is refused in code), no leverage, no
overnight positions, and every order needs the user's explicit yes.
No API keys are in this repo — `trader-broker` reads
`BYBIT_DEMO_API_KEY` / `BYBIT_DEMO_API_SECRET` from environment variables.

### `telegram_hook_health`

Diagnose, repair and prove a Telegram polling hook healthy — from a deaf
guard to a verified live name-call. Ada's own playbook, written from the
team's real hook outages.

### `cartoon-3d-short`

Build a cartoon 3D story short with three.js + Remotion: storyboard,
characters, bridge scene, voice (Piper TTS + whisper timings), render and
sound mix. Includes the style bible text and the bridge/audio templates.

Note: the skill's reference frames and storyboard sheets (JPEG images)
are **not** included in this repo — binary assets are outside the text
snapshot used for publishing. The style bible (`references/STYLE_BIBLE.md`),
the style reports (`references/reports/*.md`) and all templates are
included.

### `team-management`

Manage a team of agents' assignments in a shared `TASKS.md` file — record
assignments as they are given in Office, track each agent's status
(Queued / In progress / Blocked / In review / Done), follow up on silent
or overdue agents, and keep deadlines visible. Written for Lucy, the
team's manager. Adapted from Anthropic's `task-management` skill
(knowledge-work-plugins), rewritten from a personal to-do list into a
team-assignment tracker: the Claude Code dashboard and slash command were
removed (they do not exist in Muse), and team ownership, follow-up on
silence, and the weekly rhythm were added.

## Sources and attribution

- The day-trader skills are adapted from the
  [day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill)
  (v2.0.0, MIT). The Bybit demo connector in `trader-broker` (`bybit.py`,
  `BYBIT.md`) is Ada's own addition.
- `cartoon-3d-short` is adapted from
  [Claude Animated Shorts](https://github.com/mromidev/claude-animated-shorts).
- `telegram_hook_health` is Ada's own work.
- `team-management` is adapted from Anthropic's `task-management` skill
  ([knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)),
  rewritten for team management (see the skill for what changed).

## License

MIT — see the upstream projects for their own licences. The Bybit demo
connector and the hook-health skill are Ada's own code, MIT.
