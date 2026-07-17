# Developer Guide: Using Agent Instruction Set 3

This guide is for **you, the developer** driving a legacy .NET → Angular + Spring Boot
modernization using the four instruction documents in this folder. It explains what each
stage does, what to feed the agent at each step, and — most importantly — how to run the
**phase-by-phase build loop** where you test each increment before the next one is built.

---

## The Pipeline at a Glance

```
 .NET codebase
      │
      ▼
 [1] Requirements Extraction ──► BUSINESS_REQUIREMENTS_<App>.md
                                 FUNCTIONAL_REQUIREMENTS_<App>.md
                                 TECHNICAL_REQUIREMENTS_<App>.md
      │
      ▼
 [2] Design ────────────────────► HIGH_LEVEL_DESIGN_<App>.md   (architecture & decisions)
                                 LOW_LEVEL_DESIGN_<App>.md     (contracts & specifics)
      │
      ▼
 [3] Planning ──────────────────► PLAN_<App>.md                (phases P-1 … P-N,
      │                                                         status board, change log)
      ▼
 [4] Phase Implementation ──┐
      ▲                     │  one phase per run
      │   YOU test, accept, │
      │   adjust, relaunch  │
      └─────────────────────┘   … repeat until the final phase is accepted
```

Stages 1–3 are each **one agent run** producing documents. Stage 4 is a **loop**: one
agent run per phase, with you in between every run.

Three project-wide constraints flow through every stage — you don't need to restate them,
but know they exist, because the agents will enforce them:

- **C1** — the existing database is reused as-is (`ddl-auto=validate`, no schema changes).
- **C2** — auth follows the current app: real AD if the .NET app used AD, otherwise an
  auth seam + dev stub with AD deferred as `TODO (AD)`.
- **C3** — backend Java follows the Google Java Style Guide, enforced by
  google-java-format in the Maven build.

---

## Stage 1 — Extract Requirements

**Instructions file:** `REQUIREMENTS_EXTRACTION_INSTRUCTIONS.md`

Launch an agent with those instructions and a prompt like:

> Analyze the .NET application at `<path-to-legacy-app>`. Follow the attached
> instructions. Write the three requirements documents to `<output-folder>`.
> App name: `<AppName>`.

**You get:** `BUSINESS_REQUIREMENTS_<App>.md`, `FUNCTIONAL_REQUIREMENTS_<App>.md`,
`TECHNICAL_REQUIREMENTS_<App>.md`.

**Your job afterwards:** skim all three, and *carefully* review every `OPEN QUESTION:` and
`ASSUMPTION:`. Answer what you can (edit the docs or note answers for the next prompt) —
unresolved questions compound downstream. Pay special attention to the data model
(C1 depends on it being exact) and to whether the app was flagged as AD-based or not (C2
hinges on it).

## Stage 2 — Design

**Instructions file:** `DESIGN_INSTRUCTIONS.md`

Prompt shape:

> Design the modernized replacement. Requirements files: `<paths>`. Original .NET codebase
> (for schema disambiguation only): `<path>`. Write the HLD and LLD to `<output-folder>`.

**You get:** `HIGH_LEVEL_DESIGN_<App>.md` (the architecture story — read this one
end-to-end) and `LOW_LEVEL_DESIGN_<App>.md` (API contracts, entity↔table mappings,
screen specs — review the parts you care about, especially the data mapping table).

**Your job afterwards:** validate the big decisions (layering, API style, auth path,
stored-proc handling) and again clear the open questions. Changing a decision now costs
one document edit; changing it in phase 4 of the build costs rework.

## Stage 3 — Plan

**Instructions file:** `PLAN_INSTRUCTIONS.md`

Prompt shape:

> Create the phased implementation plan. Design docs: `<HLD path>`, `<LLD path>`.
> Requirements: `<paths>`. Write `PLAN_<App>.md` to `<output-folder>`.
> *(Optional: preferred phase count, phase strategy, or priority features.)*

**You get:** `PLAN_<App>.md` containing:

- **Phases P-1 … P-N** — P-1 is deliberately small (typically: scaffold + DB connection +
  entity validation + a couple of endpoints, testable via Swagger). Every phase ends in a
  state you can run and test locally; the final phase completes the app.
- Per phase: goal, tasks, **"what is testable after this phase"**, a numbered
  **Developer test guide**, and exit criteria.
- **§3 Phase Status Board** — the single source of truth for progress.
- **§5 Change Log** — where all mid-flight changes get recorded.

**Your job afterwards:** sanity-check the slicing. Is P-1 genuinely small? Are the
features you most need to see early in early phases? If not, ask the planning agent to
re-slice *now* — the plan is cheapest to change before any code exists.

---

## Stage 4 — The Build Loop (this is where you live)

**Instructions file:** `PHASE_IMPLEMENTATION_INSTRUCTIONS.md`

### Phase status lifecycle

| Status | Meaning | Who sets it |
|---|---|---|
| `pending` | not started (or reopened by you) | planner / you |
| `in progress` | agent is building it | agent |
| `done` | implemented and self-verified by the agent | agent |
| `accepted` | **you** tested it and approved | **you only** |

Two rules make the loop safe: **only you write `accepted`**, and **the agent refuses to
start phase N+1 while phase N is merely `done`**. Your testing round can't be skipped.

### Starting a phase

> Implement the next phase. Plan: `PLAN_<App>.md`. Designs: `<HLD>`, `<LLD>`.
> Requirements: `<paths>`.
> *(Optionally name the phase explicitly: "Implement P-3".)*

Every run, the agent first performs **reconciliation (its Step 0)**: it reads the change
log, the status board, and any notes in your prompt, folds changes into the plan and the
already-built code, and only then builds the phase. At the end it marks the phase `done`,
walks the phase's test guide itself, and hands you a report. It then **stops** — it will
not roll into the next phase.

### When a phase lands on your desk (`done`)

1. **Test it.** Open the phase's section in `PLAN_<App>.md` and follow the **Developer
   test guide** step by step. That guide is the acceptance contract for the phase.
2. **Decide** — one of three outcomes:

**A. It's good, no changes** →
   - Set the phase to `accepted` on the status board (date + optional note).
   - Launch the next run. Done — the agent will find an empty change log and proceed.

**B. It works, but you want changes** (a design tweak, a new field, different behavior) →
   - **Edit the document that owns the decision**: API contracts / mappings / screen specs
     → the **LLD**; architecture, auth approach, cross-cutting policies → the **HLD**;
     pure sequencing/scope-of-a-future-phase → the **plan** itself.
   - **Add a Change Log row** (plan §5): date, author "developer", what changed, docs
     touched, phases affected. This row is what the next run reconciles against — a design
     edit without a change-log row is easy to miss.
   - Set the phase to `accepted` (the increment itself passed) and launch the next run.
     The agent will do any rework of already-built code *first*, then build the new phase.

   *Shortcut:* you may skip the edits and just write the changes in the next run's
   prompt ("Implement P-3. Also add a `department` filter to employee search."). The
   agent is required to record your prompt notes into the change log and reconcile the
   documents itself. Use the shortcut for small tweaks; edit the docs yourself for
   anything you'd want stated precisely.

**C. It fails your testing** →
   - Set the phase back to `pending` on the status board with a note describing the
     failure.
   - Re-run the agent **on the same phase**, putting the failure details in the prompt
     (what step failed, expected vs. actual). It fixes, re-verifies, and hands off again.

3. **Repeat** until the final phase is `accepted`.

### Big course-corrections

If your feedback amounts to "the design is wrong" or invalidates several phases, don't
funnel it through a prompt note. Update the HLD/LLD (or ask the design agent to), then
**rerun the planning agent** to re-slice the remaining phases. The implementation agent
will itself recommend this if a change is too large to absorb — listen to it. Completed
`accepted` phases are history; only future phases get re-planned, and any rework of built
code lands as tasks in the next phase.

---

## Ground Rules & Tips

- **One phase per agent run.** Never ask the agent to "just finish the rest" — the loop
  exists so every increment gets human eyes.
- **The plan is a living document; the designs are the contract.** The agent may edit the
  plan (statuses, reconciliation tasks, stale test-guide steps) but never the design.
  Design changes are yours to make or commission.
- **Keep everything in git.** Commit the documents and the generated code at each phase
  boundary. The agent uses git history of the HLD/LLD/plan to detect changes during
  reconciliation, and you get a clean rollback point per phase.
- **The change log is the loop's memory.** When in doubt whether something needs a row:
  if a future run would behave differently knowing it, log it.
- **Expect blockers, don't fear them.** The agent is instructed to stop and report rather
  than improvise when the DB schema surprises it (C1), AD details are missing (C2), or
  your feedback contradicts the design. A blocker report is the system working — answer
  it and relaunch.
- **Never let the agent (or yourself) "fix" the database.** The schema is fixed (C1). If
  mapping fails, the mapping changes, not the DB.
- **Secrets stay out of everything.** DB and AD credentials live in env vars / profiles.
  If you spot one in a document or in code, flag it in the next run.

## Quick Reference — Who Writes What

| Artifact | Created by | You edit? | Agent edits? |
|---|---|---|---|
| 3 requirements docs | Stage 1 agent | to answer open questions | no (later stages read only) |
| HLD / LLD | Stage 2 agent | **yes — design changes** | no |
| Plan: phases & tasks | Stage 3 agent | future phases only | reconciliation edits only |
| Plan: status board | Stage 3 agent (init) | `accepted` / reopen | `in progress` / `done` |
| Plan: change log | Stage 3 agent (init) | **yes — every change** | logs its reconciliations & your prompt notes |
| Application code | Stage 4 agent | hotfixes → log them | yes |

*(If you hotfix code by hand, add a change-log row so the next run knows the baseline
moved.)*
