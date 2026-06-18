# Agent Instructions: Requirements Extraction from a .NET Application

## Mission
Read a legacy .NET application and produce a complete, technology-neutral **requirements
spec** describing *what the app does* — the first step in modernizing it to **Angular +
Java/Spring Boot + a relational database**. A later agent builds from your output.

**Golden rule:** describe behavior, not implementation. Capture the *rule* (the formula,
the validation, the filter logic), cite where it lives, but don't prescribe how the new
stack implements it.

## Project-Wide Constraints (fixed — they shape what you capture)
- **C1 — Existing DB is reused as-is** (no redesign, no migration). So the **Data Model
  section must be exact and authoritative**: real table/column names verbatim, types,
  sizes, nullability, defaults, keys, indexes, unique/check constraints, relationships, and
  seed/reference data. Flag anything awkward for JPA mapping (composite keys, triggers,
  stored procs, computed columns). Note where the schema lives; mark `OPEN QUESTION:` if
  the code doesn't reveal the live schema. (The new backend runs `ddl-auto=validate`, so
  accuracy here decides whether it starts.)
- **C2 — Auth/Authz via Active Directory (later)**. Document current auth fully, but capture
  the authorization model in **AD-mappable terms**: every role/permission/group, what each
  can do, and where it's enforced. Mark AD as a `TODO (AD)` placeholder; don't design it.

## Hard Rules
1. **Survey before you write** — inventory the whole codebase first.
2. **Cite evidence** — every requirement references a `path:line`.
3. **Don't invent** — if it's not in the code, it's not a requirement; unclear intent →
   open question.
4. **Flag, don't fix** — record bugs/security issues/contradictions; don't "correct" them.
5. **Read-only** — no source changes.
6. **Label inferences** `ASSUMPTION:` and unknowns `OPEN QUESTION:`.

## Step 1 — Survey
Map the solution: project layout & app type (WinForms/WPF/ASP.NET/WCF/service/console),
entry points & top-level flow, dependencies & framework version, layers (note where UI
touches the DB directly), configuration & connection strings, and external touch points
(DBs, services, files, queues, email, jobs). Write a 3–6 sentence **System Overview**.

## Step 2 — Extract by Category
Cover each; if one doesn't apply, say so explicitly.
- **Functional** — each feature: trigger, inputs, outputs, business rules (exact
  formulas/logic), and step-by-step flow incl. branches.
- **UI / Screens** — every screen and its fields/controls/actions/navigation; field-level
  detail (types, formatting, required/optional, dropdown values verbatim, defaults);
  meaningful behaviors (conditional show/enable, color coding and meaning, sort/page).
- **Data Model (C1)** — see C1 above; this section must be exact.
- **Business Logic & Validation** — all rules with precise constraints (lengths, ranges,
  regex); calculations & rounding; workflow/state transitions; authorization rules.
- **Data Access** — ORM/raw SQL/stored procs; intent of significant (esp. dynamic) queries;
  transactions, concurrency, caching.
- **Auth & Security (C2)** — authentication method, password hashing, sessions, roles;
  flag insecure handling (plaintext, secrets in source, injection) — still document it.
- **Integrations** — each external system: direction, data, format, protocol, auth, failure
  behavior (capture endpoints and file formats, e.g. CSV column order).
- **Background/Scheduled** — timers, jobs, services, consumers: what, how often, deps.
- **Non-Functional** (when evidenced) — performance, concurrency, logging/auditing, error
  messages, i18n, deployment/runtime assumptions.
- **Reports & Exports** — content, columns, formatting, filters, triggers.

## Step 3 — Goes Away / New Concerns (brief)
Note implementation details that won't carry over (e.g. `*.Designer.cs`, single-process
packaging, direct UI-to-DB calls) and web-stack concerns the desktop app lacked (auth
tokens/sessions, CORS, statelessness). Orientation for the planner, not a design.

## Output — `REQUIREMENTS_<App>.md`
Sections: 1. System Overview · 2. Functional Requirements (FR-n) · 3. UI/Screens (field
tables) · 4. Data Model (entities, relationships, constraints, seed data) · 5. Business
Logic & Validation (BR-n) · 6. Data Access · 7. Auth/Authz/Security (+ separate Risks list)
· 8. Integrations · 9. Background/Scheduled · 10. Non-Functional · 11. Reports & Exports ·
12. Goes Away / New Concerns · 13. Open Questions & Assumptions · 14. Traceability Index
(requirement ID → `path:line`).

**Conventions:** stable IDs (`FR-1`, `BR-3`, `UI-2`); tables for fields/data/enums; cite
`path:line`; capture exact values (dropdowns, defaults, formulas, seed data) verbatim;
keep the requirements technology-neutral.

## Definition of Done
- [ ] Every screen, feature, entity, and external dependency accounted for (or marked N/A).
- [ ] Every requirement has a stable ID and a source citation.
- [ ] Dropdown values, defaults, formulas, seed data captured **exactly**.
- [ ] Validation rules include precise constraints; security risks flagged.
- [ ] Assumptions/open questions listed, not silently resolved.
- [ ] Reads as *what the app does*, understandable without seeing the .NET code.

## Additional Instructions
*(The prompt may append app-specific guidance — focus areas, known problem modules,
in/out-of-scope features, output location. Treat as overrides/additions.)*
