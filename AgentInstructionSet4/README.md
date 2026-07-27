# Developer Guide: Using Agent Instruction Set 4

This guide is for **you, the developer** driving an application modernization with the six
instruction documents in this folder. Set 4 is **stack-agnostic** — nothing about the source
or target technology is baked into the instructions. What you're migrating *from* and *to*,
how it ships, and the rules that can't be broken are all captured **once**, up front, in a
Project Context, and every later stage reads them from there.

> **New in Set 4** (vs. Set 3): a **Stage 0 Project Context** that parameterizes stacks /
> CI/CD / constraints and forces a decision on load-bearing questions; a **`state.json`** file
> that holds all machine state (statuses, lineage, change log) so the doc stays readable and
> branching is tractable; **mechanical (falsifiable) phase acceptance**; an explicit
> **phase-vs-post-phase-edit** classification with a **contradiction check**; and an
> independent **Stage 5 Review/QA** that feeds findings back into the loop. See
> §What Changed From Set 3.

---

## The Pipeline at a Glance

```
 Legacy app
      │
      ▼
 [0] Project Context ───► PROJECT_CONTEXT.md   (stacks, CI/CD, constraints, questionnaire)
      │                   state.json           (machine state — initialized here)
      ▼
 [1] Requirements ──────► BUSINESS_/FUNCTIONAL_/TECHNICAL_REQUIREMENTS_<App>.md
      │
      ▼
 [2] Design ────────────► HIGH_LEVEL_DESIGN_<App>.md   (architecture & decisions)
      │                   LOW_LEVEL_DESIGN_<App>.md     (contracts & specifics)
      ▼
 [3] Planning ──────────► PLAN_<App>.md   (phases P-1…P-N)  +  state.json phases[]
      │
      ▼
 [4] Phase Implementation ──┐        [5] Review / QA  (independent agent)
      ▲                     │              │
      │  YOU test & accept  │◄─────────────┘  findings → state.json changeLog[]
      │  Review audits      │
      └─────────────────────┘   … repeat until the final phase is accepted & reviewed
```

Stages 0–3 are each **one agent run** producing documents. Stage 4 is a **loop** — one run per
phase (or per post-phase edit), with you in between. Stage 5 (**Review**) runs independently,
usually after you accept a phase, and its findings loop back into Stage 4.

Every stage supports a **rerun with Additional Instructions** if you're not happy with the
output — see §Reruns.

---

## `state.json` — the machine's memory

The single source of truth for **progress, lineage, and change history**. The Markdown docs
hold human-readable *content*; `state.json` holds *state*. Stage 0 initializes it; later stages
read and append to it. You rarely edit it by hand (accepting a phase is the main exception).

- `context` — stacks, CI/CD mode, and the **constraints** (by ID, e.g. `C1`, `C2`).
- `stages` — status + `rerunCount` for context/requirements/design/plan.
- `phases[]` — each phase's `status` (`pending`/`in progress`/`done`/`accepted`),
  `reviewStatus`, and `branchedFrom` (lineage).
- `changeLog[]` — **append-only** record of every mid-flight change (developer notes,
  reconciliations, review findings). This is what the Implement stage reconciles against.
- `reviews[]` — one entry per Review run, with its verdict.

Keep it in git. Its history is how the Implement stage detects what changed between runs.

---

## Constraints — the heart of Set 4's generality

There is no hardcoded "reuse the DB / use AD / Google Java Style" anymore. In Stage 0 **you
declare the constraints that apply to your project**, each with a stable ID. Every later stage
honors them **by ID**. Common ones you'll likely set:

- A **data/DB-reuse** constraint → the data model gets captured verbatim and the app validates
  against the live schema.
- An **auth** constraint → keep the real IdP, or use a seam + dev stub with the real one deferred.
- A **code-style/quality-gate** constraint → a formatter/linter enforced in the build.

But a green-field-ish target might declare none of these, or entirely different ones (compliance,
data-residency). The instructions adapt to whatever you declare.

---

## Stage-by-Stage

### Stage 0 — Project Context  · `PROJECT_CONTEXT_INSTRUCTIONS.md`
Fill in the **Intake Questionnaire** (in that file) and launch the agent. It resolves your
answers — applying stated **defaults** or **hard-stopping** on load-bearing blanks (current
stack, target stack, DB reuse, auth) — derives the constraint set, pins the CI/CD boundary,
writes `PROJECT_CONTEXT.md`, and initializes `state.json`.
**Your job after:** confirm the stacks, constraints, and any `ASSUMPTION:`/`OPEN QUESTION:`.

### Stage 1 — Requirements  · `REQUIREMENTS_EXTRACTION_INSTRUCTIONS.md`
Produces the three requirements docs (business / functional / technical) from the legacy app,
with depth steered by your constraints (exact data model if DB-reuse; full authz model if an
auth constraint; NFRs expanded from the context).
**Your job after:** skim all three; answer every `OPEN QUESTION:`/`ASSUMPTION:` — unresolved
questions compound downstream.

### Stage 2 — Design  · `DESIGN_INSTRUCTIONS.md`
Produces the HLD (architecture + rationale) and LLD (exact contracts), designing *within* the
target stack and constraints.
**Your job after:** validate the big decisions (layering, API style, auth path, data handling)
and clear the open questions. Changing a decision now costs a doc edit; changing it mid-build
costs rework.

### Stage 3 — Plan  · `PLAN_INSTRUCTIONS.md`
Produces `PLAN_<App>.md` (phases P-1…P-N, each runnable & testable, with a developer test guide
and **mechanical exit criteria**) and populates `state.json phases[]`.
**Your job after:** sanity-check the slicing. Is P-1 genuinely small? Are the features you need
to see early actually early? If not, rerun the planner now — it's cheapest before any code exists.

### Stage 4 — Phase Implementation (the loop)  · `PHASE_IMPLEMENTATION_INSTRUCTIONS.md`
One run builds one phase **or** one post-phase edit. Every run: **classifies** the work,
**reconciles** changes from `state.json`, runs the **contradiction check**, implements on a
**branch** with **small commits**, updates **tests + docs + state**, opens a **PR** with a
descriptive body, marks the phase `done`, and **stops**. It never sets `accepted` (that's you)
and never rolls into the next phase.

### Stage 5 — Review / QA  · `REVIEW_INSTRUCTIONS.md`
An **independent** agent audits a phase (or the whole build) on four axes — requirements
coverage, tests, security, static performance — plus constraint compliance. It returns
**PASS** or **CHANGES REQUESTED**; actionable findings become `changeLog[]` entries the next
Implement run fixes. It changes no code.

---

## The Build Loop (Stage 4 + 5) — how you live in it

**Phase status lifecycle** (in `state.json phases[]`):

| Status | Meaning | Who sets it |
|---|---|---|
| `pending` | not started (or reopened by you) | planner / you |
| `in progress` | agent is building it | agent |
| `done` | built and self-verified against **mechanical exit criteria** | agent |
| `accepted` | **you** tested it and approved | **you only** |

Two rules keep the loop safe: **only you write `accepted`**, and the agent **refuses to start
phase N+1 while phase N is merely `done`**.

**When a phase lands on your desk (`done`):**

1. **Test it** — follow the phase's Developer test guide in `PLAN_<App>.md`.
2. **Decide:**
   - **A. Good, no changes** → set the phase `accepted` in `state.json`. Optionally run
     **Review** on it. Launch the next phase.
   - **B. Works, but you want a change** → this is a **post-phase edit**. Either edit the
     owning doc yourself (LLD for contracts, HLD for architecture, plan for sequencing) and add
     a `changeLog` note, or just describe the change in the next run's prompt and tell the agent
     **"this is a post-phase edit"**. The agent runs the **contradiction check**: if it's
     additive it does it on top; if it's a requirement/design change it presents options and
     **waits for your call** on anything large.
   - **C. Fails your testing** → set the phase back to `pending` with a note, and re-run the
     agent **on the same phase** with the failure details.
3. **Repeat** until the final phase is `accepted` (and, if you want, whole-build Review is PASS).

**Big course-corrections:** if your feedback amounts to "the design is wrong", don't funnel it
through a prompt note — rerun the Design stage, then rerun the Planner to re-slice the remaining
phases. The Implement agent will itself recommend this when a change is too large to absorb —
listen to it. Only future (non-`accepted`) phases get re-planned.

---

## Reruns (any stage)

Every stage document ends with an **Additional Instructions** block. If you're unhappy with an
output, relaunch that stage's agent with your change requests appended there — e.g. *"Design:
use a modular monolith, not microservices"* or *"Plan: make P-1 smaller and pull reporting
earlier."* The agent amends the existing artifacts in place (rather than regenerating from
scratch), bumps that stage's `rerunCount`, and — if later stages already consumed the old
output — logs a `changeLog` entry so the downstream work gets reconciled or replanned.

---

## Ground Rules & Tips

- **One unit of work per run.** One phase, or one edit — never "just finish the rest".
- **The designs are the contract; the plan is living; `state.json` is the memory.** The agent
  may edit the plan's bookkeeping and statuses (via state.json) but never the design. Design
  changes are yours to make or commission.
- **Keep everything in git.** Commit docs, `state.json`, and code at each phase boundary. The
  agent uses git history to detect changes during reconciliation, and you get clean rollback
  points and reviewable PRs.
- **The change log is the loop's memory.** If a future run would behave differently knowing
  something, it belongs in `changeLog[]`.
- **Blockers are the system working.** The agent stops and reports rather than improvising when
  the schema surprises it, auth details are missing, or your change contradicts the design.
  Answer and relaunch.
- **Never let anyone "fix" a reused database.** If a DB-reuse constraint applies, the mapping
  changes, not the schema.
- **Secrets stay out of everything** — config/env only.
- **Review is independent.** Don't run it in the same session that built the code.

---

## Worked Examples

The examples below show the **prompts** you'd give the agent at each step. Replace bracketed
values. Assume everything lives under `./out/` and the legacy app under `./legacy/`.

### Example A — A .NET → Angular + Spring Boot migration that reuses the database

**Stage 0 — Project Context** (fill the questionnaire in the prompt):

> Follow `PROJECT_CONTEXT_INSTRUCTIONS.md`. Legacy app: `./legacy/`. App name: `EmployeeSearch`.
> Write `PROJECT_CONTEXT.md` and `state.json` to `./out/`.
> Questionnaire answers:
> 1. Current stack: **.NET WinForms + SQL Server** (confirm from the app).
> 2. Target stack: **Angular (Node 25.9.0) + Java 21 / Spring Boot, Maven, Spring Data JPA**.
> 4. Data: **reuse the existing database as-is** — no schema changes, no migration.
> 6. Auth: the app uses a local users table → **auth seam + dev stub, real AD deferred**.
> 7. CI/CD: **none yet** (local build/test only).
> 9. Quality gate: **Google Java Style Guide, enforced by google-java-format in Maven**.
> 10. NFR priorities: security, correctness, performance.

*→ You get `PROJECT_CONTEXT.md` (with constraints C1 = DB reuse, C2 = auth seam, C3 = Java
style) and an initialized `state.json`. Confirm the constraints look right.*

**Stage 1 — Requirements:**

> Follow `REQUIREMENTS_EXTRACTION_INSTRUCTIONS.md`. Context: `./out/PROJECT_CONTEXT.md`,
> `./out/state.json`. Legacy app: `./legacy/`. Write the three requirements docs to `./out/`.
> App name: `EmployeeSearch`.

**Stage 2 — Design:**

> Follow `DESIGN_INSTRUCTIONS.md`. Context + requirements in `./out/`. Legacy app `./legacy/`
> for schema disambiguation only. Write the HLD and LLD to `./out/`.

**Stage 3 — Plan:**

> Follow `PLAN_INSTRUCTIONS.md`. Designs + requirements + context in `./out/`. Write
> `PLAN_EmployeeSearch.md` to `./out/` and populate `state.json phases[]`. Prefer ~5 phases.

**Stage 4 — Implement phase 1:**

> Follow `PHASE_IMPLEMENTATION_INSTRUCTIONS.md`. Plan/designs/requirements/context/state in
> `./out/`. **This is a phase.** Implement the next pending phase (P-1). Repo is this git
> repo; branch and open a PR.

*→ Agent builds P-1 on a branch, marks it `done`, opens a PR. You test it via the plan's P-1
test guide, then set P-1 `accepted` in `state.json`.*

**Stage 5 — Review P-1** (independent run):

> Follow `REVIEW_INSTRUCTIONS.md`. Target: **P-1**. State/plan/design/requirements/context in
> `./out/`. Codebase is this repo. Write the review report to `./out/`.

*→ PASS → launch P-2. CHANGES REQUESTED → the findings are now in `state.json changeLog[]`;
your next Implement run reconciles and fixes them before/at P-2.*

### Example B — A post-phase edit (after P-2 was accepted)

You've accepted P-2 but realize you want a `department` filter on employee search:

> Follow `PHASE_IMPLEMENTATION_INSTRUCTIONS.md`. **This is a post-phase edit, not a new phase.**
> Add a `department` filter to the employee-search endpoint and screen. Plan/designs/
> requirements/context/state in `./out/`. Branch and open a PR.

*→ The agent runs the contradiction check. If the LLD already allows for it, it implements on
top (updating tests/docs/state, PR). If it's actually a requirement change, it tells you the
impact and the options (change-on-top / branch-from-a-stage / redo) and waits for your call.*

### Example C — Rerunning a stage you're unhappy with

The plan front-loaded too much into P-1:

> Follow `PLAN_INSTRUCTIONS.md`. **Rerun.** Existing plan + state in `./out/`. Additional
> Instructions: P-1 is too big — split the frontend out into its own later phase; keep P-1 to
> backend scaffold + DB validation + two endpoints only. Re-slice future phases only; leave any
> accepted phases untouched.

### Example D — Whole-build final review

After the final phase is accepted:

> Follow `REVIEW_INSTRUCTIONS.md`. Target: **whole-build**. All docs + state in `./out/`.
> Codebase is this repo. Emphasize security and requirements coverage. Write the report to `./out/`.

---

## Quick Reference — Who Writes What

| Artifact | Created by | You edit? | Agent edits? |
|---|---|---|---|
| `PROJECT_CONTEXT.md` | Stage 0 | to fix stacks/constraints (rerun) | on rerun |
| 3 requirements docs | Stage 1 | to answer open questions | rerun / no later |
| HLD / LLD | Stage 2 | **yes — design changes** | rerun only |
| `PLAN_<App>.md` (phase content) | Stage 3 | future phases only | reconciliation edits |
| `state.json` phases[] status | Stage 3 (init) | `accepted` / reopen | `in progress`/`done` |
| `state.json` changeLog[] | Stage 0 (init) | **yes — your change notes** | reconciliations + review findings |
| `state.json` reviews[] | Review stage | no | Review appends |
| Application code | Stage 4 | hotfixes → log them | yes (on a branch, via PR) |
| Review reports | Stage 5 | no | yes |

*(If you hotfix code or edit a design doc by hand, add a `changeLog` entry so the next run knows
the baseline moved.)*

---

## What Changed From Set 3

| Concern | Set 3 | Set 4 |
|---|---|---|
| Source/target stack | Hardcoded (.NET → Angular/Spring) | **Declared in Stage 0**, stack-agnostic |
| Constraints | Fixed C1/C2/C3 in every doc | **Project-supplied, by ID**, in `PROJECT_CONTEXT.md` |
| CI/CD | Not addressed | **Explicit boundary** (respect / generate / none) |
| Load-bearing questions | Surfaced as open questions | **Questionnaire with defaults-or-hard-stop** |
| Status board & change log | Markdown tables in the plan | **`state.json`** (enables branching / lineage) |
| Phase acceptance | `done` (self) + `accepted` (human) | Same, but **exit criteria must be mechanical/falsifiable** |
| Post-phase edits | Absorbed via prompt notes | **Explicit phase-vs-edit classification + contradiction check** |
| Big changes | Agent recommends re-plan | Same, plus **change-on-top / branch / redo** options, **human-authorized** |
| Git workflow | "keep it in git" | **Mandated: branch + small commits + PR with descriptive body** |
| QA / Review | None | **Independent Stage 5** feeding findings back into the loop |
| Reruns | Plan/Implement footers | **Uniform Additional-Instructions rerun on every stage** |
