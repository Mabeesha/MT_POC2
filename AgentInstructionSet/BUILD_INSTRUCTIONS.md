# Agent Instructions: Plan & Build the Application

## Mission
Given the design document, **plan the work as ordered tasks, then build the app** on
**Angular + Java/Spring Boot + the existing database**. You both plan and implement:
produce a short task plan, then execute it task by task into working, verified code.

**Golden rule:** implement the design's contracts (APIs, entity↔table mappings, components,
auth seam) exactly. Don't redesign or expand scope. If the design is wrong, blocked, or
missing something material, **stop and report** — don't improvise.

## Inputs (authority order: design → requirements → .NET code)
1. **Design** (`DESIGN_<App>.md`) — primary; the authoritative contracts.
2. **Requirements** (`REQUIREMENTS_<App>.md`) — intent, business rules, exact values.
3. **Original .NET code** — only to confirm a detail the design defers to it (e.g. exact
   schema). Never copy its structure or patterns.

## Constraints (must hold in the running app)
- **Stack:** Angular + Angular Material; Java 17+ / Spring Boot, Maven, Spring Data JPA,
  Spring Web, Spring Security.
- **C1 — Reuse the existing DB as-is.** Map JPA entities to current tables with exact
  names; run `ddl-auto=validate` (never create/update against the real DB). Fix the
  *mapping* if validation fails, never the schema. (A throwaway DB for unit tests is fine.)
- **C2 — Auth via Active Directory (placeholder).** Build an auth seam (interface) + dev
  stub that enforces roles now; leave AD wiring as `TODO (AD)`. No AD/LDAP config or
  secrets in code.

## Step 1 — Plan
Read the design (cross-check requirements). Produce a brief `PLAN_<App>.md`: an ordered
task list grouped into phases, each task with an ID, dependencies, scope, the design/
requirement IDs it implements, and acceptance criteria. Default phase order:

1. **Setup** — backend + frontend scaffolds, profiles, build baseline.
2. **Data layer (C1)** — JPA entities on existing tables, repositories, **validate mapping
   against the real DB**.
3. **Auth seam (C2)** — interface + dev stub, security config, role→AD-group model, CORS.
4. **Backend features** — services, validation, endpoints per the API contract, tests.
5. **Frontend** — routing, services/guards/models, then screens wired to the API.
6. **Cross-cutting & e2e** — logging, config, exports, end-to-end checks.

Every task and phase must trace to design/requirement IDs and have a verifiable exit.

## Step 2 — Build (per task, in dependency order)
1. **Implement** the smallest correct change for the task, honoring the contracts.
2. **Test** — add automated tests covering the rules and edge cases from requirements.
3. **Verify** — build + tests pass; exercise the acceptance criteria (call the endpoint,
   render the screen). For the data layer, confirm it **validates against the existing
   schema** (C1).
4. **Report** what was built and how it was verified; mark the task done; move on.

## Hard Rules
- Follow the plan in dependency order; honor design contracts (paths, verbs, shapes, status
  codes, entity/column names, validation rules) exactly.
- Verify every task before moving on; a task isn't done until verified.
- Write idiomatic Angular/Spring Boot — do not reproduce .NET/WinForms structure.
- Stay in scope; no secrets in code (config via profiles/env vars).
- Read-only on the legacy app; non-destructive on the DB.

## When Blocked — stop and report (don't improvise)
Design contradictory/ambiguous on a material point; DB schema doesn't match and the
mapping can't be reconciled (C1); a task needs AD specifics (C2 — build the stub, mark
`TODO (AD)`); or access/credentials unavailable. State the blocker, what you tried, and the
options. Record unresolved items as `OPEN QUESTION:` / `ASSUMPTION:`.

## Definition of Done
- [ ] Every plan task done & verified, or reported as blocked.
- [ ] Backend and frontend build, run, and integrate end to end.
- [ ] App starts and **validates cleanly against the existing DB** with matching names (C1).
- [ ] Auth seam + dev stub enforces roles; AD marked `TODO (AD)` (C2).
- [ ] Every endpoint matches the design contract and is covered by a test.
- [ ] Every requirements screen is implemented with its validation and states.
- [ ] Tests pass; no secrets in source; CORS configured.
- [ ] All requirement IDs satisfied; blockers/questions reported, not silently resolved.

## Additional Instructions
*(The prompt may append app-specific guidance — file paths, the .NET codebase path (or
none), DB connection details, output repo/branch conventions, or in-scope phases. Treat
those as overrides/additions.)*
