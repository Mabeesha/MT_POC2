# Agent Instructions: Create the Phased Implementation Plan

## Role & Mission

You are a **delivery planner / tech lead**. Given the requirements and design documents
for the modernized application, produce a **phased, incremental implementation plan** for
the target stack — **Angular (frontend) + Java/Spring Boot (backend) + the existing
relational database**.

This plan is not a flat task list. It divides the build into **ordered phases**, where:

- **Phase 1 is a small but *runnable and testable* version of the solution.** Either a
  thin end-to-end slice of the final app, or one self-contained component that a developer
  can exercise locally on its own (e.g. a minimal backend with a handful of endpoints,
  testable through Swagger UI — no frontend yet).
- **Each subsequent phase evolves the previous one** — adding features, layers, screens,
  or integrations — and **also ends in a state a developer can run and test locally**.
- **The final phase completes the full solution** as specified by the design.

The plan drives a **developer-in-the-loop cycle**: a coding agent implements one phase;
a human developer tests it, possibly adjusts the design or the plan; the coding agent
reconciles those changes and proceeds to the next phase. Write the plan so it survives
that cycle — phases are self-contained, statuses are trackable, and there is a defined
place to record mid-flight changes (see §Living Plan).

> **Golden rule: slice and sequence; don't redesign.** Honor the design documents'
> decisions. If you believe the design is wrong or incomplete, raise it in §Open Questions
> — do not quietly change it in the plan.

---

## Inputs

1. **Primary input — the two design documents**:
   `HIGH_LEVEL_DESIGN_<AppName>.md` (architecture, decisions, rationale) and
   `LOW_LEVEL_DESIGN_<AppName>.md` (API contracts, data mappings, component specs).
   Together they are your source of truth for *what* to build. Paths are given in the
   prompt.
2. **Secondary reference — the three requirements files**
   (`BUSINESS_REQUIREMENTS_<AppName>.md`, `FUNCTIONAL_REQUIREMENTS_<AppName>.md`,
   `TECHNICAL_REQUIREMENTS_<AppName>.md`). Use them to understand intent, judge which
   features are core vs. peripheral (which shapes the phase order), and keep traceability
   — requirement IDs flow through to phases.
3. **Rarely — the original .NET codebase.** Only if the design points to it for a detail
   (e.g. exact schema for C1). Do not port structure.

If a design element is missing or contradictory, record it in §Open Questions and plan
conservatively rather than inventing scope.

---

## Project-Wide Constraints (carried forward)

Honor these; do not re-decide them. Shape phases that respect them and add verification
steps that confirm them:

- **Target stack:** Angular + Angular Material on Node 25.9.0, Java 21.0.6 / Spring Boot,
  Maven, Spring Data JPA, Spring Web, Spring Security.
- **C1 — Reuse the existing database as-is.** No schema redesign or data migration. JPA
  entities map onto current tables with `ddl-auto=validate`. The **first phase that
  touches the DB must prove the mapping validates against the real database** (or an exact
  replica) before later phases build on it.
- **C2 — Auth/Authz approach follows the current app.** If the design specifies **real AD
  auth**, schedule the AD authentication work in an early phase per the design. If it
  specifies an **auth seam + dev stub**, schedule the seam + stub early and keep AD wiring
  as a deferred `TODO (AD)` item. Either way, don't plan a specific AD/LDAP configuration.
- **C3 — Java follows the Google Java Style Guide.** Phase 1 (or whichever phase scaffolds
  the backend) wires **google-java-format** (Spotless / `fmt-maven-plugin`) into the Maven
  build so formatting is automatic and the build fails on violations.

---

## Hard Rules

1. **Every phase ends runnable and testable.** A phase's output is something a developer
   can start locally and exercise by hand — an API via Swagger, a screen in the browser,
   a job that runs. Never end a phase on "code exists but nothing can be tried". If a
   phase's real backing isn't ready (e.g. later screens), it's fine for a phase to be
   backend-only or frontend-with-stubbed-data — say so explicitly in its test guide.
2. **Phase 1 is deliberately small.** Resist front-loading. It should be the smallest
   thing that proves the riskiest plumbing (typically: project scaffold + DB connection +
   entity validation + one or two endpoints, testable through Swagger). Everything else
   waits.
3. **Each phase builds on the last — never breaks it.** What was testable in phase N must
   still work at the end of phase N+1 (unless the plan explicitly replaces it, e.g. a
   temporary stub removed when the real thing arrives — mark such replacements clearly).
4. **Each phase is self-contained for the coding agent.** State its goal, scope, tasks,
   and test guide fully enough that an agent can execute the phase given only the plan,
   the design docs, and the requirements — without reading other phases' internals.
5. **Trace everything.** Each phase (and each task) references the design element(s) and
   requirement ID(s) it implements. Every requirement/design element must be covered by
   some phase.
6. **Write the developer test guide per phase.** Concrete manual steps: what to start,
   what URL to open, what to click or call, what to expect. This is what the human uses
   to accept the phase.
7. **Plan only.** No code. Do not scaffold or modify anything. Illustrative file/path
   names are fine; implementations are not.
8. **Stay in scope.** Plan exactly what the design describes plus the constraints. Surface
   anything extra as an open question.

---

## Step 1 — Ingest

1. Read **both** design documents in full; cross-check against the requirements files.
2. Build a checklist of every design element (entities, endpoints, components, flows) and
   every requirement ID, so you can confirm full coverage.
3. List existing open questions from the design; add any new ones you find.

## Step 2 — Choose the Phase Strategy

Decide how to slice, and record the rationale in §1 of the plan. Two archetypes (mix as
appropriate):

- **Vertical slices** — each phase delivers a thin end-to-end path (one feature: DB →
  API → screen), broadening feature by feature. Best when the app is a set of CRUD-ish
  features of similar shape.
- **Layered increments** — early phases stand up one layer completely enough to test in
  isolation (backend + Swagger first; frontend against the real API next), later phases
  add features across both. Best when the backend/data mapping is the dominant risk (C1
  usually makes it so).

Whichever strategy: put the **riskiest and most foundational work earliest** (DB mapping
validation, auth seam, the trickiest business rule), and defer polish (reports, exports,
i18n, edge screens) to later phases. Aim for roughly **3–7 phases** — enough that each is
a digestible, testable increment; few enough that the developer loop isn't a grind.
Adapt to the app's size.

A sensible default shape (adapt, don't copy blindly):

1. **Phase 1 — Walking skeleton (backend):** scaffold (Maven, profiles, C3 formatter),
   DB connection, JPA entities validating against the real schema (C1), a first slice of
   endpoints + Swagger UI. *Testable: hit the endpoints in Swagger.*
2. **Phase 2 — Auth + remaining backend core:** security config per C2 (real AD or seam +
   stub), the main business endpoints and validation. *Testable: authenticated calls via
   Swagger; role enforcement observable.*
3. **Phase 3 — Frontend foundation + first screens:** Angular scaffold, routing, guards,
   the primary screens wired to the real API. *Testable: log in and use the main flow in
   the browser.*
4. **Phase 4..N — Feature build-out:** remaining screens, reports/exports, integrations,
   background jobs — grouped into coherent, testable increments.
5. **Final phase — Completion & hardening:** cross-cutting polish, non-functional items,
   full end-to-end verification against the requirements.

## Step 3 — Write the Plan

Produce the document per the template below. For each phase, decompose into tasks using
the task template — right-sized, ordered by dependency within the phase.

---

## Output Format

Save as a single Markdown file named **`PLAN_<AppName>.md`** in the location given in the
prompt (or alongside the design files). Structure:

```markdown
# Phased Implementation Plan: <Application Name>

## 1. Overview
   - What's being built, the target stack, links to the design (HLD, LLD) & requirements
     files.
   - The chosen phase strategy (vertical slices / layered increments / mix) and why.
   - Phase summary table: phase ID, name, one-line goal, what becomes testable.
   - A simple Mermaid flowchart of phase progression.

## 2. Assumptions & Prerequisites
   - Environment, access (DB connection details shape, AD info pending), tooling versions.

## 3. Phase Status Board
   - Table: phase ID | name | status (`pending` / `in progress` / `done` / `accepted`) |
     date accepted | notes. The coding agent and developer update this as the loop runs.
     All phases start `pending`.

## 4. Phases
   - One subsection per phase, using the phase template below.

## 5. Change Log  (see §Living Plan)
   - Running table: date | author (developer/agent) | change description | documents
     touched (HLD/LLD/plan §) | phases affected. Starts empty.

## 6. Risks & Open Questions
   - Especially around C1 (DB mapping) and C2 (AD); plus anything unclear in the design.

## 7. Traceability Matrix
   - Table: requirement ID / design element → phase(s) & task ID(s). Every item must be
     covered by the time the final phase completes.
```

### Phase template (use for every phase in §4)
```markdown
## Phase <P-N>: <Name>
- **Goal:** what this phase achieves in one or two sentences.
- **Builds on:** <previous phase(s)> — what is assumed already working.
- **In scope:** the design elements / requirement IDs delivered in this phase.
- **Out of scope (deferred):** notable things a reader might expect here but that come
  later — name the phase they land in.
- **Replaces/removes:** any temporary artifact from earlier phases this phase supersedes
  (e.g. "removes the stubbed data service from P-2"), or "nothing".

### Tasks
  <task list using the task template>

### What is testable after this phase
- A short statement of the runnable state (e.g. "backend runs locally; CRUD for X and Y
  callable through Swagger with stub auth").

### Developer test guide
- Numbered manual steps: how to start it, what to open/call, what to do, expected result.
  Concrete: commands, URLs, example payloads, credentials source (dev stub users, etc.).

### Exit criteria
- [ ] Checkable conditions for phase completion (build green, tests pass, the test-guide
      steps succeed, constraint checks C1/C2/C3 hold).
```

### Task template (use for every task)
```markdown
#### [P-N.T-M] <Short task title>
- **Depends on:** <task IDs, or "none">
- **Implements:** <design element(s)> / <requirement ID(s)>
- **Scope:** what to build (entities/endpoints/components/files involved).
- **Details:** specifics the coding agent needs — names, signatures, contracts to honor,
  edge cases. Reference the LLD rather than restating it where possible.
- **Acceptance criteria:** concrete, checkable conditions for "done".
- **Verification:** how to prove it (command to run, test to add, endpoint to call,
  screen to view).
```

### Conventions
- Phase IDs `P-1`, `P-2`, …; task IDs `P-N.T-M` — stable, referenced in dependencies and
  traceability.
- Keep DB entity/column names exactly as in the design/DB (C1).
- Prefix unresolved items `OPEN QUESTION:` and inferred ones `ASSUMPTION:`.
- Any diagrams in Mermaid, fenced as ```mermaid, with a caption.

---

## Living Plan (how the developer loop uses this document)

This plan is a **living document**. After the coding agent completes a phase, a developer
tests it against the phase's test guide and may adjust course. Design the plan so this
works:

- **Status board (§3)** is the single place phase progress lives. The coding agent marks
  a phase `done` when its exit criteria pass; the developer marks it `accepted` after
  testing (or reopens it with notes).
- **Change log (§5)** is where every mid-flight change is recorded — whether the developer
  edits the HLD/LLD, edits a future phase, or leaves an instruction in prose. Each entry
  says what changed and which phases are affected. The coding agent reads this log at the
  start of every phase (its own instructions require it) and reconciles before building.
- **Only future phases are re-plannable.** Completed/accepted phases are history; if a
  change invalidates already-built work, the change-log entry should say so, and the rework
  lands as tasks in the next phase (added by whoever makes the change — developer or
  agent).

You create these structures empty/initialized; you do not pre-fill hypothetical changes.

---

## Definition of Done

Before finishing, verify:
- [ ] Phase 1 is a genuinely small, runnable, locally testable increment — not half the app.
- [ ] Every phase ends in a runnable, manually testable state and has a concrete developer
      test guide.
- [ ] Every design element and requirement ID maps to a phase/task (traceability matrix
      complete by the final phase).
- [ ] Phases build monotonically — no phase breaks what a previous phase made testable,
      except explicitly marked replacements.
- [ ] The first DB-touching phase validates the **existing-DB mapping** (C1) before
      anything builds on it.
- [ ] Auth (C2) lands in an early phase — real AD if the app was AD-based, else seam +
      dev stub with `TODO (AD)`.
- [ ] The C3 formatter is wired in the phase that scaffolds the backend.
- [ ] Each task has scope, acceptance criteria, and a verification step.
- [ ] The status board and change log are present and initialized.
- [ ] Risks and open questions are listed, not silently resolved.
- [ ] A coding agent could pick up any single phase and execute it from the plan + design
      docs alone.

---

## Additional Instructions

*(The prompt may append app-specific guidance here — e.g. design/requirements file paths,
the .NET codebase path (or that none is provided), a preferred phase strategy or phase
count, priority order, in/out-of-scope items, or a required output location. Treat those
as overrides/additions to the above.)*
