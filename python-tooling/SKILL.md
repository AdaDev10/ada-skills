---
name: python-tooling
description: Write team tools in stdlib-only Python — small CLIs with argparse, offline self-tests with printed evidence, and state files as proof — the way Ada's hooks, watchdog, video tools and trader connector are built.
---

# Python Tooling

You write the team's tools in Python. Every tool is small, testable, and
ships with its own test evidence. Standard library only — no new dependency
without a reason written down.

## Stdlib first

- Use only the standard library (`argparse`, `json`, `hashlib`, `hmac`,
  `subprocess`, `urllib`/`curl` via subprocess) unless the task genuinely
  needs more — the trader connector (`bybit.py`) and the hook tooling are
  stdlib-only and run anywhere on the team's hosts.
- Put secrets in environment variables or mode-600 files only. Never write
  a key, token, or secret into code, a log, or chat. Keys come from the
  environment at runtime, never from a default in the source.
- Give every tool an `argparse` CLI with one verb per action
  (`balance`, `place`, `status`, `test`) and a `--help` that shows them.
  A tool with no CLI is a script nobody else can run.

## Test before you deliver

- Every tool ships with an offline self-test (`test` verb or
  `tests/test_<tool>.py`) that runs with no network and no keys, and prints
  PASS/FAIL per case. An untested deliverable is not a deliverable.
- Report the test result in the handoff: what you ran, what it printed,
  and whether it passed (e.g. "329/329 PASS"). A bare "it works" is not
  evidence.
- Keep fixtures small and real: the trader tests use real TSLA October
  2026 fixtures; a test that only exercises its own mocks proves nothing.

## One process, one client

- Never open a second client on a shared session while a hook or poller is
  running. A second Telethon client invalidates the shared Telegram
  session (`AuthKeyDuplicatedError`) and kills the hook for hours.
- For a one-off action: stop the hook first, do the action, then let the
  watchdog restart it. Verify by the state file advancing, never by
  process liveness alone.
- Guard against duplicate instances: check for a running copy of the same
  script before starting, and kill-verify-retry when a stale one is found.

## Prove health with state files

- A live process proves nothing. Judge a hook or poller only by its state
  file advancing (`hook_state.json`, `matrix_state.json`): record the last
  message id before and after a poll cycle.
- Merge, don't overwrite, shared state: when several runs write one file
  (e.g. `pending.json`), merge by message id and remove an entry only
  after it has been acted on — overwriting drops older calls.
- Ack after waking, dedup by id, and make every action fire once.

## Ship it

- Keep the tool, its test, and a short README together in one folder
  under `~/workspace/custom-skills/` (or the matching team repo folder),
  so one `npx skills add` installs the whole thing.
- Frontmatter first: every `SKILL.md` starts with `name` and
  `description` — without them the skills CLI does not see the skill at
  all.
