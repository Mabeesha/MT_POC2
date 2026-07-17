# Agent Instructions: Design the Modernized Application (HLD + LLD)

## Role & Mission

You are a **software architect**. Given a requirements specification for a legacy .NET
application, produce **two design documents** for its modernized replacement on
**Angular (frontend) + Java/Spring Boot (backend) + the existing relational database**:

1. **`HIGH_LEVEL_DESIGN_<AppName>.md` (HLD)** — the *architecture*: system context,
   technology choices, layering, module boundaries, data design at the entity level, the
   auth approach, integrations, cross-cutting decisions, and key flows. Written for an
   architect/tech-lead audience; it answers **"how is the system shaped, and why"**.
2. **`LOW_LEVEL_DESIGN_<AppName>.md` (LLD)** — the *contracts and specifics*: full REST API
   contract, exact entity↔table mappings, DTO shapes, service responsibilities and key
   methods, per-screen component specs, validation placement, error handling details.
   Written for an implementer; it answers **"exactly what do I build"**.

Your output is consumed by a separate **planning agent** (which will slice the build into
incremental, testable phases) and then a **coding agent** (which builds phase by phase).
The two documents must be detailed and unambiguous enough that those agents can work
without re-deriving decisions — but they are *designs*, not the code itself. Favor clear
contracts (APIs, data mappings, component responsibilities) and **visual diagrams** over
prose.

**Split by altitude, don't duplicate.** Every decision lives in exactly one document:
the HLD holds decisions and rationale; the LLD holds the concrete contracts that realize
them. The LLD references HLD sections instead of restating rationale; the HLD references
LLD sections instead of inlining contracts. Both share the same requirement-ID
traceability.

> **Golden rule: design the target, don't port the source.** This is a functional
> rewrite. Preserve *behavior and rules*; do not carry over WinForms/WPF/.NET structure,
> patterns, or layering. Design idiomatic Angular + Spring Boot.

---

## Inputs

1. **Primary input — the three requirements files**:
   `BUSINESS_REQUIREMENTS_<AppName>.md` (objectives, scope, business rules, roles),
   `FUNCTIONAL_REQUIREMENTS_<AppName>.md` (features, screens, validation, reports), and
   `TECHNICAL_REQUIREMENTS_<AppName>.md` (data model, data access, security, integrations,
   configuration). Together these are your **source of truth**; everything in your design
   must trace back to their requirement IDs. Paths are given in the prompt.

2. **Secondary reference — the original .NET codebase** *(use sparingly, for
   disambiguation only)*. You **may** consult it to:
   - Confirm the **exact database schema** (table/column names, types, keys) the new app
     must map onto — see Constraint C1; accuracy here is critical and the requirements doc
     may not capture every detail.
   - Resolve a requirement marked `OPEN QUESTION:` / `ASSUMPTION:`, or verify exact values
     (formulas, enumerations, validation patterns) when the requirement is ambiguous.

   **Guardrails when reading the .NET code:**
   - Do **not** mirror its class structure, naming, UI layout, or data-access style.
   - Do **not** introduce behavior that isn't in the requirements; if the code reveals
     something the requirements missed, **add it to §Open Questions**, flag it, and design
     conservatively — don't silently absorb it.
   - If you cannot locate the codebase, proceed from the requirements alone and record the
     gaps as open questions. Note in the prompt whether the codebase path is provided.

---

## Project-Wide Constraints (carried from the requirements program)

These are fixed. Honor them; do not re-decide them.

- **Target stack:** Angular + Angular Material (frontend), Java 17+ / Spring Boot, Maven,
  Spring Data JPA, Spring Web, Spring Security.
- **C1 — Reuse the existing database as-is.** No schema redesign, no data migration. JPA
  entities **map onto the current tables** using real table/column names. The backend runs
  with **`spring.jpa.hibernate.ddl-auto=validate`** (never `create`/`update`). Treat the
  schema as a fixed contract; design the mapping around it, including any awkward bits
  (composite keys, triggers, stored procs, computed columns).
- **C2 — Authentication/Authorization approach follows the current app.** If the
  requirements state the .NET app **already uses Active Directory**, design **real AD-based
  authentication** (LDAP / Windows Integrated Auth / AD-backed OIDC) as the actual mechanism.
  If it does **not**, design a clean **auth seam** (interface + a temporary/dev stub) that AD
  will plug into later, and mark the AD wiring as `TODO (AD)`. Either way, map current
  roles/permissions to **AD-group-mappable** terms and do **not** commit to a specific
  AD/LDAP configuration (host, base DN, etc.) — that is deployment config. Note that the
  concrete AD *mechanism* may differ from the desktop app's: a browser SPA + stateless
  backend usually cannot reuse Windows Integrated/Kerberos SSO directly, so prefer an LDAP
  bind or AD-backed OIDC and keep the identity/group model stable even when the mechanism changes.
- **C3 — Java follows the [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html).**
  Backend Java conforms to it, enforced mechanically via **google-java-format** (Spotless or
  `fmt-maven-plugin`) wired into the Maven build. Record this in the HLD's Technology &
  Dependencies section. (Frontend stays idiomatic Angular.)

---

## Hard Rules

1. **Trace everything.** Every design element references the requirement ID(s) it
   satisfies (`FR-3`, `BR-1`, `UI-2`…). Each document carries a traceability matrix for
   the elements it owns (see templates); together the two matrices must cover every
   requirement ID.
2. **Decide, don't defer.** Where the requirements allow multiple valid designs, make a
   choice and give a one-line rationale. Only leave something open if it genuinely needs a
   human/business decision — put those in §Open Questions.
3. **Be concrete.** Specify endpoint paths, HTTP verbs, request/response shapes, status
   codes, entity-to-table mappings, component names, and routes (in the LLD). Avoid vague
   guidance like "add appropriate validation" — state the rule.
4. **Visuals are required.** Use **Mermaid** diagrams (see §Required Diagrams). Diagrams
   must agree with the prose.
5. **No code, no scaffolding.** Produce design documents only. Illustrative snippets
   (a DTO shape, a key signature, a properties block) are fine; full implementations are
   not. Do not modify the source app or generate the new project.
6. **Stay within scope.** Design only what the requirements describe, plus the constraints
   above. Flag gold-plating temptations as open questions instead of building them in.
7. **One home per decision.** Never state the same decision or contract in both documents;
   cross-reference by section instead (e.g. LLD: "error body shape per HLD §2.3").

---

## Step 1 — Ingest & Reconcile

1. Read **all three** requirements files in full. Build a checklist of every requirement ID.
2. List the open questions/assumptions already flagged in them.
3. Only where a design decision genuinely depends on it, consult the .NET codebase per the
   guardrails above — primarily to lock down the **exact DB schema** (C1).
4. Confirm you can account for **every** requirement across the two documents. Anything
   you can't maps to §Open Questions.

## Step 2 — Make the Core Design Decisions (HLD material)

Decide and record (with brief rationale) at least:
- **Architecture & layering** — frontend/backend split, backend layers (controller →
  service → repository), DTO vs. entity boundaries.
- **API style & conventions** — REST resource naming, pagination/filtering/sorting
  approach, error response format, versioning if needed.
- **Data mapping strategy** — how the existing schema is mapped under `ddl-auto=validate`;
  how relationships, keys, and awkward types are handled. For stored procedures / DB
  functions / triggers, **decide explicitly** whether to call them (JPA
  `@Query(nativeQuery=true)` / `@Procedure`) or reimplement the logic in a Java service,
  and record the choice with rationale.
- **Auth approach** — where authentication/authorization is enforced; the interface AD
  will implement (or the real AD mechanism); how roles map to AD groups.
- **Frontend structure** — module/standalone-component organization, routing, state
  management approach, shared services, how the requirements screens group into features.
- **Cross-cutting concerns** — config/profiles, CORS, logging, error handling, validation
  strategy (where each rule lives).

## Step 3 — Elaborate the Contracts (LLD material)

From the HLD decisions, specify concretely:
- Every **table → JPA entity** mapping with exact names, types, keys, relationships.
- Every **REST endpoint** with full contract (verb, path, params, bodies, statuses, auth).
- Every **DTO** shape, **service** (responsibilities + key methods), and **repository**.
- Every **screen** → component(s), route, fields, actions, validation, states, and the
  API(s) it calls.
- Validation rule placement (frontend / backend / DB), error handling specifics,
  transaction boundaries.

## Step 4 — Write the Two Documents

Produce both documents per the templates below, with diagrams embedded in the relevant
sections. Write the HLD first; derive the LLD from it.

---

## Required Diagrams (Mermaid)

**In the HLD:**
1. **System context / architecture** — Angular ↔ Spring Boot ↔ existing DB (+ AD seam,
   external integrations). `flowchart` or C4-style.
2. **Entity-Relationship diagram** of the (existing) data model. `erDiagram`.
3. **Sequence diagram(s)** for the 2–4 most important flows (e.g. login, primary
   search/CRUD, export). `sequenceDiagram`.
4. **State diagram** — only if the app has meaningful workflow/state transitions
   (`stateDiagram-v2`).

**In the LLD:**
5. **Backend component/package diagram** — controllers, services, repositories, config.
   `flowchart`.
6. **Frontend component & routing tree** — components, services, guards, routes.
   `flowchart`.

Keep diagrams readable (split large ones). Every diagram needs a one-line caption.

---

## Output Format

Save **two** Markdown files in the location given in the prompt (or alongside the
requirements files). Both share the same `<AppName>`.

### File 1 — `HIGH_LEVEL_DESIGN_<AppName>.md`  (*architecture & decisions*)
```markdown
# High-Level Design: <Application Name>

## 1. Overview & Scope
   - What is being built, the target stack, and a summary of key design decisions.
   - In-scope / out-of-scope. Link to the source requirements files (business,
     functional & technical) and to the LLD.

## 2. Architecture
   - System context/architecture diagram + narrative.
   - Layering and the responsibilities of each tier/layer.
   - Key cross-cutting decisions (config/profiles, CORS, error model, logging) —
     the decisions and rationale; concrete formats live in the LLD.

## 3. Technology & Dependencies
   - Backend & frontend stack with versions; notable libraries and why. C3 tooling
     (google-java-format via Spotless / fmt-maven-plugin).

## 4. Data Design  (honors C1 — existing DB)
   - ER diagram of the existing schema.
   - The mapping strategy: how entities map on under `ddl-auto=validate`, how awkward
     constructs (composite keys, stored procs, triggers, computed columns) are handled —
     as decisions with rationale. Field-by-field mappings live in the LLD.
   - Notes on schema/owner and any mapping risks.

## 5. Authentication & Authorization  (honors C2)
   - The chosen path per C2: **real AD auth** (if the .NET app was AD-based) or an
     **auth seam + dev stub** with AD deferred (if it was not), with rationale.
   - The auth seam concept; for the AD path, the AD integration approach (bind/query
     flow); for the non-AD path, the dev stub concept and `TODO (AD)` items.
   - Role/permission → AD-group mapping table.
   - Where authz is enforced (backend + frontend guard) — as an architectural decision.

## 6. Integrations & External Dependencies
   - Each external system: how it's reached in the new design, protocol, failure
     handling approach.

## 7. Cross-Cutting Concerns
   - Config & Spring profiles, environment variables, CORS, logging/auditing,
     i18n/localization, non-functional targets from requirements.
   - **Testing strategy:** unit vs. integration boundaries, how business rules and
     validation (VR-n) are covered, and how the DB is provided for tests that depend on
     `ddl-auto=validate` (real schema / exact replica vs. throwaway local DB).

## 8. Key Flows (Sequence Diagrams)
   - Diagram + short walkthrough for each major flow.

## 9. Build, Run & Deployment
   - How backend and frontend are built/run; profiles; packaging; how the app connects
     to the existing DB (config shape, not secrets).

## 10. Open Questions, Risks & Assumptions
   - Decisions needing human/business input; mapping risks (esp. DB & AD); anything the
     .NET code revealed that the requirements didn't cover.

## 11. Traceability Matrix (architecture-level)
   - Table: requirement ID → HLD decision/section that addresses it. Requirements
     realized purely by LLD contracts may point to the LLD matrix instead.
```

### File 2 — `LOW_LEVEL_DESIGN_<AppName>.md`  (*contracts & specifics*)
```markdown
# Low-Level Design: <Application Name>

## 1. Overview
   - One-paragraph orientation; link to the HLD (whose decisions this document
     realizes) and the requirements files.

## 2. Data Mapping  (honors C1 — existing DB)
   - Table → JPA entity mapping table: entity, table name, fields → columns, types,
     keys, relationships, and how each awkward construct is handled (per the HLD §4
     strategy). Exact names as they exist in the DB.

## 3. Backend Design
   - Component/package diagram.
   - **REST API contract**: one entry per endpoint — method, path, query/path params,
     request body, response body, status codes, errors, and auth required. Use tables.
   - DTO shapes (fields + types), services (responsibilities + key method signatures),
     repositories (query methods + intent), transaction boundaries.
   - Validation rules: for each VR-n, where it is enforced (frontend / backend / DB)
     and its exact constraint.
   - Error handling: the concrete error body shape, exception → status mapping.

## 4. Frontend Design
   - Component & routing tree diagram.
   - Per screen (mapped from requirements UI section): component(s), route, fields,
     actions, validation, states (loading/empty/error), and which API(s) it calls.
   - Services, guards, state approach, shared/reusable components.

## 5. Auth Implementation Detail  (per HLD §5)
   - The seam interface (name + key method signatures); the dev stub behavior (users,
     roles) for the non-AD path, or the AD bind/query specifics (shape, not host
     config) for the AD path. Security filter/guard placement.

## 6. Integration Contracts
   - Per external system: exact request/response or file formats, retry/failure
     behavior, configuration keys.

## 7. Open Questions & Assumptions  (implementation-level)

## 8. Traceability Matrix (contract-level)
   - Table: requirement ID → LLD element(s) (endpoint/entity/component) that satisfy
     it. Together with the HLD matrix, every requirement ID must appear.
```

### Conventions
- Reference requirement IDs inline so both documents are traceable.
- Use **tables** for the API contract, data mapping, and traceability matrices.
- Keep entity/column names **exactly** as they exist in the DB (C1).
- Prefix unresolved items with `OPEN QUESTION:` and inferred ones with `ASSUMPTION:`.
- Diagrams in Mermaid, fenced as ```mermaid; each with a caption.
- Cross-reference between the documents by section (`HLD §4`, `LLD §3`) — never duplicate
  content between them.

---

## Definition of Done

Before finishing, verify:
- [ ] **Both documents** are produced; every design decision/contract lives in exactly one
      of them, cross-referenced rather than duplicated.
- [ ] Every requirement ID is accounted for across the two traceability matrices.
- [ ] The data mapping targets the **existing** schema with exact names, compatible with
      `ddl-auto=validate` (C1); mapping risks are flagged in the HLD.
- [ ] Auth is designed per C2: **real AD auth** if the .NET app was AD-based, else an auth
      seam + dev stub with AD marked `TODO (AD)`; role model is AD-mappable either way.
- [ ] Every API endpoint has a complete contract in the LLD (verb, path, params, bodies,
      statuses, auth).
- [ ] Every requirements screen maps to named frontend component(s) and route(s) in the LLD.
- [ ] All required diagrams are present in the right document, captioned, and consistent
      with the prose.
- [ ] No .NET implementation patterns were ported; the design is idiomatic to the target.
- [ ] A testing strategy is stated in the HLD, including how the DB is provided for
      `validate`-dependent tests.
- [ ] Open questions/assumptions/risks are listed rather than silently resolved.
- [ ] The HLD is readable stand-alone as the architecture story; an implementer could
      build the app from the LLD (with the HLD for context) without guessing.

---

## Additional Instructions

*(The prompt may append app-specific guidance here — e.g. the requirements file paths, the
.NET codebase path (or that none is provided), focus areas, in/out-of-scope features, or a
required output location. Treat those as overrides/additions to the above.)*
