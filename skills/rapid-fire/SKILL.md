---
name: rapid-fire
description: "Reach a user-provided goal through small, verified commits. Activate only on an explicit user request, or acceptance of an offer to use 'rapid-fire'; creating or discussing the skill does not activate it."
---

# Rapid Fire

## Plan

A **destination** is the user's desired final state of the project: the behavior,
capabilities, or the finalized spec to be satisfied. Use the goal, if supplied,
in the request; ask only about missing or ambiguous outcomes and scope.

Inspect repository instructions, relevant code and documentation, and Git state
to establish what the project currently does, and the gaps that remain for the
intended state. Define an observable acceptance criteria, to demonstrate this
goal is met.

Present the current state, destination, acceptance criteria, and a path between
them through ordered **checkpoints**. Each checkpoint resolves part of the gap
and leaves a useful, stable project state suitable for a small, clean, reviewable
commit. Explain its scope, dependencies, validation, and contribution to the goal.
Wait for plan approval before implementation; approval starts **auto mode**, the
checkpoint loop below.

## Checkpoint loop

Keep exactly one checkpoint 'In Progress' during auto mode, including when you are
awaiting approval. Preserve unrelated user work and staging throughout.

1. **Implement** the next Planned checkpoint autonomously within the agreed scope.
2. **Verify** using the project's required tests, lint, style, syntax/build checks,
   hooks, applicable upstream CI variants, and any necessary focused checks.
   Record commands, outcomes, and verified source/configuration/dependency inputs.
   Reuse passing results when the inputs are unchanged; otherwise rerun affected
   checks. Resolve failures; if required checks cannot run, report unfinished
   verification and stop rather than presenting the checkpoint as ready for approval.
3. **Prepare** the complete diff and planned commit boundary. Use `git-commit` skill
   if available, otherwise prepare a commit message directly. Use scope-free titles
   in normal sentence case, preserving acronym and identifier casing over the skill.
4. **Stop for approval** with checkpoint changes unstaged and send the report
   described below. Wait for clear approval of both changes and message before
   staging, committing, or working ahead. An unambiguous "go ahead" in this
   context approves this checkpoint; questions, silence, and elapsed time do not.
5. **Commit** by confirming the reviewed diff, message, and verification remain
   current, and that the commit boundary excludes unrelated existing staging.
   Resolve overlapping boundaries before staging only the approved files or hunks
   and committing directly. Run normal commit hooks; any material change to the
   reviewed result, including hook edits, requires affected verification and
   renewed approval. Verify that the resulting commit contains only the approved
   work and mark it 'Completed'.
6. **Continue** immediately to the next checkpoint in the same session, without
   another implementation-permission request.

## Reports

Maintain the destination and a traceable checkpoint list across turns and context
compaction: "Completed", "In Progress", "Planned", and "Won't Do", including
additions and splits. Show this list once at the end of each final session reply;
at checkpoint approval stops, follow it with the exact proposed commit message,
also once. Reserve these artifacts for final replies rather than commentary.

An approval report explains what changed, why, relevant file references, how it
fits the 'destination', material trade-offs, verification results / limitations.
Ask the user to approve the changes and message.

## Steering and completion

- Retain the objective while answering questions or incorporating corrections.
  Ask for missing information when it blocks sound progress. Changes to the
  agreed scope or destination need approval. Beware of scope creep.
- Use read-only subagents for useful research or validation, continuing independent
  work while they run. Evaluate findings yourself, and queue important follow-ups
  rather than silently expanding the current checkpoint.
- Explicit pause, stop, or research-only requests halt implementation, staging,
  and commits. Perform requested read-only work and wait for explicit resumption;
  ending the session requires a fresh activation for future use.
- When asked to drop a checkpoint, remove only its rejected changes and record
  "Won't Do" with the reason. Requests for revisions keep it active. Expose any
  resulting gap to the destination and continue as directed.
- After the last planned commit, verify the destination's acceptance criteria.
  Continue unmet work within scope through the same loop. Once the criteria are
  satisfied, give a completion report covering outcomes, commit references,
  validation, and limitations, with no active checkpoint; end auto mode and stop.
