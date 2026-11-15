---
name: telegram_hook_health
description: Diagnose, repair and prove a Telegram polling hook healthy, from a deaf guard to a verified live name-call, when a hook misses calls or dies.
---

# Telegram Hook Health

## Diagnose in order

- Check the hook process and its schedule first and record what you find before you change anything.

- Test the name matcher next with a fresh name-call and read the hook log to see whether the call was seen, skipped, or never logged.

- Inspect the own-post guard after the matcher and treat a guard that skips a real name-call as the prime suspect.

- Check the wake schedule last and compare it with the standard of 10 minutes while idle and 5 minutes while open work is held.

- Call a repair done only after a live name-call is answered from the hook itself.

## Fix the shared-account guard

- Replace any own-post test that uses msg.out or sender_id with a test against a recorded list of message ids you actually sent.

- Keep that list in own_message_ids.json and update it through ~/workspace/custom.telegram-team/own_ids.py right after every send.

- Test the guard offline before you restart the hook and feed it a name-call, a name-call marked as sent from the shared account, your own sent ids, and a message with no name-call.

- Accept the offline test only when it queues both name-calls and skips only your own sent ids and the message with no name-call.

- Restart the hook after the guard test passes and watch one poll cycle for a false trigger on your own posts.

## Prove health with state files

- Treat a live hook process as no proof at all and judge health only by the state file advancing.

- Read hook_state.json and record its last message id before and after a poll cycle.

- Count a watchdog restart as a success only when the state file advances after the restart.

- Run a live kill test when you install or change a watchdog and kill the hook, wait for the next 2 minute cron run, and verify polling resumes within about 2 minutes.

- Report the before and after state values with every repair so a later reader can check the proof.

## Keep one client and one watchdog

- Never open a second Telegram client on the shared session while the hook is running.

- Stop the hook first when you need a one-off Telegram action, do the action, and let the 2 minute watchdog restart the hook.

- Verify the restart by the state file advancing and never by process liveness alone.

- Re-authenticate the session when Telegram rejects it as used from two places at once and treat a restart alone as insufficient for that fault.

- Adapt a watchdog to the layout it will supervise before you install it and set its hook script and state file to that layout first.

## Fix a file-watch hook

- Treat a hook that only reads a local pending file as a file watcher and not a live poller.

- Make the poller read Telegram itself with last_seen_id as the minimum id on every run.

- Merge new calls into the pending file by message id and remove an entry only after the hook has acted on it.

- Mark each acted-on entry so it fires once and never wakes the hook again on the same file.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Use the runtime cron every 2 minutes for the watchdog instead of a system service when the user bus is absent and system units do not survive a VM replacement.

- Ask the supervisor to send a fresh name-call for the retest instead of trusting a report that a file was installed.

- Send the repair report with the changed files and the log lines so the supervisor can check the proof without another diagnostic round.
