---
name: team-management
description: Manage a team of agents' assignments in a shared TASKS.md file — record assignments as they are given in Office, track each agent's status, follow up on silent or overdue agents, and keep deadlines visible. For Lucy, the team's manager.
---

# Team Management

You manage a team of agents. Assignments are tracked in a shared `TASKS.md`
file that you and the team can read. This skill is adapted from Anthropic's
`task-management` skill (knowledge-work-plugins), rewritten from a personal
to-do list into a team-assignment tracker.

## File Location

**Always use `TASKS.md` in the current working directory.**

- If it exists, read/write to it.
- If it doesn't exist, create it with the template below.

## Where assignments come from

Assignments arrive as messages in the team's Office group (Telegram and
Matrix), as name-calls and task messages. **Record an assignment in
TASKS.md the moment you give it** — do not wait to be asked, and do not
keep assignments only in chat history, where they get buried.

## Format & Template

When creating a new TASKS.md, use this exact template (without example tasks):

```markdown
# Team Tasks

## Active

## Waiting On

## Blocked

## Done
```

Task format:
- `- [ ] **Task title** — owner: [agent], due [date], status [Queued/In progress/Blocked/In review/Done]`
- Sub-bullets for additional details: what was asked, where (Office message
  id or Matrix event), what the deliverable is, and what is blocking it.
- Completed: `- [x] ~~Task~~ (date)` — move to Done.

Status vocabulary (use exactly these):
- **Queued** — assigned, not started.
- **In progress** — the agent is working on it.
- **Blocked** — the agent cannot proceed; the blocker is named in a sub-bullet.
- **In review** — delivered, awaiting your review.
- **Done** — reviewed and accepted.

## How to Interact

**When you assign a task:**
- Add it to Active with the owner, the due date, and status Queued.
- Include the Office message id or Matrix event id where you assigned it,
  so anyone can find the original order.

**When an agent reports progress:**
- Update the status (Queued → In progress → In review → Done).
- If they report a blocker, move the task to Blocked and record the
  blocker and what they need.

**When you ask "what's on the team's plate":**
- Read TASKS.md.
- Summarize Active and Blocked by owner, with due dates.
- Highlight anything overdue or blocked.

**When you ask "who is silent / overdue":**
- Compare each Active task's due date and last report against today.
- Any agent with an overdue task or no report since the last check is
  silent — name-call them in Office and ask for a status. Silence is
  never acceptable; a one-line status is enough.
- If an agent stays silent after a direct name-call, escalate: tell the
  client (Daniel) through the normal channel — that is the one escalation
  that is yours to make.

**When a task is done:**
- Mark it `[x]`, strike it through, add the completion date, and move it
  to Done. Keep Done for ~1 week, then clear old items.

**When you ask "what am I waiting on":**
- Read the Waiting On section: items where you are waiting for someone
  else (an agent's deliverable, a client's decision, an access grant).
- Note how long each item has been waiting, with a "since [date]".

## Conventions

- **Bold** the task title for scannability.
- Always name the **owner** — a task with no owner is nobody's job.
- Always include a **due date** when one exists; a task without a due
  date drifts.
- Include "waiting on [person/thing] since [date]" for waiting items.
- Sub-bullets for additional context: the original order, the
  deliverable, the blocker.
- Record assignments as they happen — never batch them from memory later.

## Weekly rhythm

- **Friday morning:** the weekly technical report arrives from the
  Developer. Review it, confirm receipt in Office, and report it to the
  client. Track it as a recurring task with a Friday due date.
- **Before any deadline you set** (for example a brief due Wednesday
  12:00), check TASKS.md the day before and name-call anyone whose part
  is not In review yet.

## Communication

- Office messages go in the team's working language (Persian) and, where
  the team uses it, the wire format. Task records in TASKS.md stay in
  English so they are searchable and portable.
- Reports you receive go to the shared Drive; TASKS.md records only the
  assignment, the owner, the status, and the due date — not the report
  itself.

## What this skill is not

- It does not assign work by itself — you decide who does what.
- It does not chase agents on its own — you name-call them in Office.
- It does not replace the team's hook health checks or the Drive — it
  only tracks who owes what, and by when.
