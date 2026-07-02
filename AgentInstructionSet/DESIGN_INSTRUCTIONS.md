# Agent Instructions: Design the Modernized Application

## Mission
Given the requirements spec, produce a **detailed design document** for the replacement on
**Angular + Java/Spring Boot + the existing database**. It must be concrete enough for a
separate implementation agent to build from without re-deciding anything. Favor clear
contracts (APIs, data mappings, component responsibilities) and **diagrams** over prose.

**Golden rule:** design the target, don't port the source. Preserve behavior and rules;
do not carry over .NET/WinForms structure. Design idiomatic Angular + Spring Boot.

## Inputs (authority order: requirements → .NET code)
1. **Requirements** — `BUSINESS_REQUIREMENTS_<App>.md` (features, rules, screens, roles)
   and `TECHNICAL_REQUIREMENTS_<App>.md` (data model, security, integrations, config).
   Together the source of truth; everything traces to their IDs.
2. **Original .NET code** — sparingly, only to confirm the **exact DB schema** (C1) or
   resolve a flagged `OPEN QUESTION:`/ambiguous value. **Guardrails:** don't mirror its
   structure/naming/UI; if the code reveals behavior the requirements missed, add it to
   Open Questions (don't silently absorb it); if no codebase, work from requirements and
   record gaps.

## Constraints (fixed)
- **Stack:** Angular + Angular Material; Java 17+ / Spring Boot, Maven, Spring Data JPA,
  Spring Web, Spring Security.
- **C1 — Reuse the existing DB as-is.** JPA entities map onto current tables with real
  names; backend runs `ddl-auto=validate` (never create/update). Treat the schema as a
  fixed contract; design the mapping around awkward bits (composite keys, triggers, stored
  procs, computed columns).
- **C2 — Auth approach follows the current app.** If the requirements say the .NET app
  **already uses Active Directory**, design **real AD-based authentication** (LDAP / Windows
  Integrated Auth / AD-backed OIDC) as the actual mechanism. If it does **not**, design a
  clean **auth seam** (interface + dev stub) AD will plug into later and mark AD wiring
  `TODO (AD)`. Either way, map roles to **AD-group-mappable** terms.
- **C3 — Java follows the Google Java Style Guide**, enforced via google-java-format
  (Spotless/`fmt-maven-plugin`) in the build. Record this in §3 Technology & Dependencies.

## Hard Rules
1. **Trace everything** to requirement IDs; include a traceability matrix.
2. **Decide, don't defer** — pick a design with a one-line rationale; only truly
   business-level unknowns go to Open Questions.
3. **Be concrete** — exact paths, verbs, request/response shapes, status codes,
   entity→table mappings, component names, routes. No "add appropriate validation."
4. **Diagrams required** (Mermaid) and must agree with the prose.
5. **No code/scaffolding** — design only; small illustrative snippets are fine.
6. **Stay in scope** — design only what requirements + constraints call for.

## Steps
1. **Ingest** — read the full requirements; checklist every ID; list its open questions;
   consult the .NET code only to lock the DB schema (C1).
2. **Decide the core design** (with rationale): architecture & layering (controller →
   service → repository, DTO vs entity); API conventions (resource naming, pagination/
   filtering/sorting, error format); data mapping (each table → entity); the auth seam;
   frontend structure (components, routing, services, screen→component mapping);
   cross-cutting concerns (profiles, CORS, logging, error handling, validation placement).
3. **Write** the document per the template.

## Required Diagrams (Mermaid, each captioned)
1. System context/architecture (Angular ↔ Spring Boot ↔ DB + AD seam + integrations).
2. ER diagram of the existing data model (`erDiagram`).
3. Backend component/package diagram.
4. Frontend component & routing tree.
5. Sequence diagram(s) for the 2–4 key flows (login, primary search/CRUD, export).
6. State diagram — only if there's meaningful workflow.

## Output — `DESIGN_<App>.md`
Sections: 1. Overview & Scope (+ in/out-of-scope, link to requirements) · 2. Architecture
(diagram, layering, cross-cutting decisions) · 3. Technology & Dependencies (with versions)
· 4. Data Design (C1) — ER diagram + table→entity mapping table, `ddl-auto=validate` notes,
mapping risks · 5. Backend Design — component diagram + **REST API contract table**
(method, path, params, request/response, status codes, auth) + DTOs/services/repositories/
validation/error handling · 6. Frontend Design — component & routing tree + per-screen
(component, route, fields, actions, validation, states, APIs called) · 7. Auth/Authz (C2) —
real AD auth if the app was AD-based else seam + dev stub with `TODO (AD)`, role→AD-group
mapping table, enforcement points · 8.
Integrations · 9. Cross-Cutting Concerns · 10. Key Flows (sequence diagrams) · 11. Build,
Run & Deployment (incl. connecting to existing DB — config shape, not secrets) · 12. Open
Questions, Risks & Assumptions · 13. Traceability Matrix (requirement ID → design element)
· 14. Implementation Guidance (build order, module boundaries, sequencing).

**Conventions:** reference requirement IDs inline; tables for API contract, data mapping,
traceability; entity/column names exactly as in the DB (C1); Mermaid for diagrams; mark
`OPEN QUESTION:` / `ASSUMPTION:`.

## Definition of Done
- [ ] Every requirement ID is in the design and the traceability matrix.
- [ ] Data model maps onto the existing schema with exact names, `ddl-auto=validate`-
      compatible; mapping risks flagged (C1).
- [ ] Auth designed per C2: real AD auth if the app was AD-based, else seam + dev stub with
      AD marked `TODO (AD)`; roles AD-mappable either way.
- [ ] Every endpoint has a complete contract; every screen maps to component(s) + route(s).
- [ ] All required diagrams present, captioned, consistent with the prose.
- [ ] No .NET patterns ported; design is idiomatic to the target.
- [ ] Open questions/risks listed; an implementer could build from this without guessing.

## Additional Instructions
*(The prompt may append app-specific guidance — requirements/codebase paths (or none),
focus areas, in/out-of-scope, output location. Treat as overrides/additions.)*
