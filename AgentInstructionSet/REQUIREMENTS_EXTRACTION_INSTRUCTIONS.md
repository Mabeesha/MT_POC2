# Agent Instructions: Requirements Extraction from a .NET Application

## Mission
Read a legacy .NET application and produce **three requirements documents** — the first step
in modernizing it to **Angular + Java/Spring Boot + a relational database**. A later agent
builds from your output. Produce:

1. **`BUSINESS_REQUIREMENTS_<App>.md`** — *why the app exists*: business purpose,
   objectives, scope, user classes, business rules/policies, and roles. High-level,
   stakeholder-readable, technology-neutral.
2. **`FUNCTIONAL_REQUIREMENTS_<App>.md`** — *what the system does*: detailed features and
   behaviors, screens, inputs/outputs, workflows, functional validation, and reports. The
   detailed "what" that realizes the business requirements.
3. **`TECHNICAL_REQUIREMENTS_<App>.md`** — *how it is built today and the technical
   constraints the rebuild must honor*: data model, data access, security mechanics,
   integrations, background jobs, non-functional, configuration.

All three come from the same survey. The split is by **audience and altitude** (why → what
→ how), not by doing the analysis three times: capture each fact once, in the document it
belongs to, and cross-reference between them by ID.

**Golden rule:** describe behavior, not implementation. Capture the *rule* (the formula,
the validation, the filter logic), cite where it lives, but don't prescribe how the new
stack implements it. (The .NET *how* is recorded in the technical doc as a **constraint to
honor**, not as a design to keep.)

## Project-Wide Constraints (fixed — they shape what you capture)
- **C1 — Existing DB is reused as-is** (no redesign, no migration). So the **Data Model
  section must be exact and authoritative**: real table/column names verbatim, types,
  sizes, nullability, defaults, keys, indexes, unique/check constraints, relationships, and
  seed/reference data. Also capture the **DB engine and version** and the schema/owner name
  (they drive JPA dialect selection). Flag anything awkward for JPA mapping (composite keys,
  triggers, stored procs, computed columns). Note where the schema lives; mark
  `OPEN QUESTION:` if the code doesn't reveal the live schema. (The new backend runs
  `ddl-auto=validate`, so accuracy here decides whether it starts.)
- **C2 — Auth approach depends on the current app.** Document current auth fully and
  **state explicitly whether the .NET app already uses Active Directory** (LDAP / Windows
  Integrated Auth / Kerberos / AD-backed OIDC). Capture the authorization model in
  **AD-mappable terms**: every role/permission/group, what each can do, and where it's
  enforced. Then flag which path applies: **if it is already AD-based**, the modernized app
  keeps real AD authentication; **if it is not** (local users table, forms login, etc.), the
  modernized app uses an auth seam + dev stub with AD deferred as `TODO (AD)`. Record the
  facts and the path — don't design the mechanism here.

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
Cover each; if one doesn't apply, say so explicitly. The tag shows which document each
category feeds — **[BUS]** = Business, **[FUNC]** = Functional, **[TECH]** = Technical.

- **[BUS] Business Purpose & Objectives** — why the app exists, the goals it serves, and
  success criteria if evidenced.
- **[BUS] Scope & User Classes** — what's in/out of scope; the classes of users/actors.
- **[BUS] Business Rules & Policies** — domain-level rules and policies independent of any
  one screen (e.g. "salaries are confidential", "a record can't be deleted once approved").
  The business *meaning*; precise/field-level enforcement is captured functionally.
- **[BUS] Roles & Permissions** — who can do what: every role/permission/group and the
  actions it gates (the AD-mappable model from C2, stated in business terms).
- **[FUNC] Functional Requirements** — each feature: trigger, inputs, outputs, the business
  logic it applies (noting *that* a calculation occurs and where it fits the flow — the exact
  formula is captured once as a Validation Rule and cited by ID), and step-by-step flow incl.
  branches. The detailed "what".
- **[FUNC] UI / Screens** — every screen and its fields/controls/actions/navigation;
  field-level detail (labels, required/optional, dropdown values verbatim, defaults,
  formatting); meaningful behaviors (conditional show/enable, color coding and meaning,
  sort/page). Describe what the *user* sees and does, not the control types.
- **[FUNC] Validation Rules** — all functional validation with precise constraints
  (lengths, ranges, regex, allowed chars); calculations & rounding (**the single home** for
  exact formulas — FR items cite these by ID rather than restating them); workflow/state
  transitions. (DB-level constraints that *enforce* these go in the Data Model — link them.)
- **[FUNC] Reports & Exports** — content, columns, formatting, filters, triggers.
- **[TECH] Technical Overview** — app type, framework version, key dependencies, layers and
  architecture (e.g. UI calling the DB directly), entry points.
- **[TECH] Data Model (C1)** — see C1 above; this section must be exact and authoritative.
- **[TECH] Data Access** — ORM/raw SQL/stored procs; intent of significant (esp. dynamic)
  queries; transactions, concurrency, caching.
- **[TECH] Auth & Security (C2)** — authentication mechanics, password hashing, sessions,
  how role checks are enforced; **state whether auth is AD-based** (decides the C2 path);
  flag insecure handling (plaintext, secrets in source, injection) — still document it.
- **[TECH] Integrations** — each external system: direction, data, format, protocol, auth,
  failure behavior (capture endpoints and file formats, e.g. CSV column order).
- **[TECH] Background/Scheduled** — timers, jobs, services, consumers: what, how often, deps.
- **[TECH] Non-Functional** (when evidenced) — performance, concurrency, logging/auditing,
  error messages, i18n, deployment/runtime assumptions.
- **[TECH] Configuration** — connection strings (shape, not secrets), feature flags,
  environment-specific settings.

If a fact spans documents (e.g. a rule that's a business policy, a functional validation,
and a DB constraint), record it **once at its home altitude** and cross-reference by ID:
the business *policy* → Business (`BR-n`); the enforceable *validation* → Functional
(`VR-n`); the *column constraint* → Technical Data Model (`DM-n`). Don't duplicate the prose.

## Step 3 — Goes Away / New Concerns (brief, → Technical doc)
Note implementation details that won't carry over (e.g. `*.Designer.cs`, single-process
packaging, direct UI-to-DB calls) and web-stack concerns the desktop app lacked (auth
tokens/sessions, CORS, statelessness). Orientation for the planner, not a design.

## Output — three documents

### `BUSINESS_REQUIREMENTS_<App>.md`  (*why & scope*)
1. **System Overview** — business purpose, primary users, core capabilities.
2. **Business Objectives** — goals the app serves; success criteria if evidenced (`BO-n`).
3. **Scope & User Classes** — in/out of scope; classes of users/actors.
4. **Business Rules & Policies** (`BR-n`).
5. **Roles & Permissions** — who can do what (`ROLE-n`).
6. **Glossary** — domain terms a non-technical reader needs.
7. **Open Questions & Assumptions** (business-facing).
8. **Traceability Index** — business ID → `path:line`.

### `FUNCTIONAL_REQUIREMENTS_<App>.md`  (*what the system does*)
1. **Overview** — the feature set at a glance; link to the business doc.
2. **Functional Requirements** — per feature: trigger, inputs, outputs, logic, flow (`FR-n`).
3. **UI / Screens** — one subsection per screen with field tables and behaviors (`UI-n`).
4. **Validation Rules** — field-level constraints, calculations, state transitions (`VR-n`).
5. **Reports & Exports** — content, columns, formatting, filters, triggers (`RPT-n`).
6. **Open Questions & Assumptions** (functional).
7. **Traceability Index** — functional ID → `path:line`.

### `TECHNICAL_REQUIREMENTS_<App>.md`  (*how it's built / constraints*)
1. **Technical Overview** — app type, framework, dependencies, layers/architecture.
2. **Data Model (C1)** — entities, columns (exact names/types/keys), relationships,
   constraints, seed data (`DM-n`).
3. **Data Access** — query intent, transactions, concurrency, caching (`DA-n`).
4. **Authentication & Security (C2)** — mechanics + a separate **Risks** list (`SEC-n`).
5. **Integrations & External Dependencies** (`INT-n`).
6. **Background / Scheduled Processing** (`BG-n`).
7. **Non-Functional Requirements** (`NFR-n`).
8. **Configuration** — connection-string shape, flags, env settings (`CFG-n`).
9. **Goes Away / New Concerns** (from Step 3).
10. **Open Questions & Assumptions** (technical).
11. **Traceability Index** — technical ID → `path:line`.

**Cross-reference, don't duplicate:** functional items (`FR/UI/VR/RPT`) cite the `BR-n`/
`BO-n` they realize; technical items cite the `FR-n`/`BR-n` they support; the Data Model
cites the `VR-n`/`BR-n` each constraint enforces.

**Conventions:** stable IDs per the schemes above; tables for fields/data/enums; cite
`path:line`; capture exact values (dropdowns, defaults, formulas, seed data) verbatim;
keep the **Business** and **Functional** docs technology-neutral; the **Technical** doc
records the .NET *how* as constraints to honor. All three files share the same `<App>` name.

## Definition of Done
- [ ] All three documents produced; every fact lives in exactly one of them
      (cross-referenced by ID, not duplicated).
- [ ] Every screen, feature, entity, and external dependency accounted for (or marked N/A).
- [ ] Every requirement has a stable ID and a source citation; each doc has a traceability
      index.
- [ ] Dropdown values, defaults, formulas, seed data captured **exactly**; validation rules
      include precise constraints; security risks flagged.
- [ ] Assumptions/open questions listed, not silently resolved.
- [ ] Business reads as *why*, Functional as *what the system does* (understandable without
      seeing the .NET code); Technical captures the schema and mechanics accurately (C1/C2).

## Additional Instructions
*(The prompt may append app-specific guidance — focus areas, known problem modules,
in/out-of-scope features, output location. Treat as overrides/additions.)*
