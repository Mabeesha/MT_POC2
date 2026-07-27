# Agent Instructions: Establish the Project Context (Stage 0)

## Role & Mission

You are a **modernization intake analyst**. Before any requirements are extracted, a
design is drawn, or a line of code is written, this stage pins down the **fixed facts of
the project** so every later stage reads them from one place instead of re-deciding them.

Set4 is **stack-agnostic**: unlike earlier instruction sets, nothing about the source or
target technology is hardcoded. The specifics — what we are migrating *from*, what we are
migrating *to*, how it ships, and which rules are non-negotiable — are captured **here**,
once, and consumed by Stages 1–5.

You produce **two artifacts**:

1. **`PROJECT_CONTEXT.md`** — the human-readable statement of the project: current stack,
   target stack, CI/CD, the constraint set, and the answered intake questionnaire.
2. **`state.json`** — the machine-readable state file that every later stage reads and
   updates. You **initialize** it here (see §state.json Schema).

> **Golden rule: capture decisions, don't invent them.** Where the human has decided
> (target stack, whether to reuse the database), record it. Where they haven't, use the
> questionnaire: apply a stated **default**, or **hard-stop** if the question is
> load-bearing. Never silently guess a load-bearing fact.

---

## Inputs

1. **The intake questionnaire answers** — the human fills in `§Intake Questionnaire`
   (below) and provides it in the prompt, as a filled copy, or as answers to resolve
   during this run. Treat a filled questionnaire as the primary source.
2. **The legacy application** (path in the prompt), if available — you may inspect it to
   *confirm or infer* answers the human left blank (e.g. detect the current stack, detect
   whether it authenticates against AD, detect the database). Inference here is allowed
   **only to propose a default the human can override** — mark every inferred answer
   `ASSUMPTION:`.
3. **Any prior `PROJECT_CONTEXT.md` / `state.json`** — if this is a rerun (see §Rerunning
   this Stage), load and amend them rather than starting over.

---

## Step 1 — Resolve the Intake Questionnaire

Work through every question in §Intake Questionnaire. For each:

1. If the human answered it, record the answer.
2. If blank and the question has a **default**, apply the default and mark it
   `ASSUMPTION: (default applied)`.
3. If blank and the question is marked **load-bearing (hard-stop)**, **stop and ask**. Do
   not proceed to Stage 1 without it — these determine the entire shape of the migration.
4. If the legacy app is available and lets you infer an answer, propose it as
   `ASSUMPTION:` and still let the human confirm.

Record the fully-resolved questionnaire in `PROJECT_CONTEXT.md §5`.

## Step 2 — Derive the Constraint Set

Constraints are the **non-negotiable rules** every downstream stage must honor. In Set4
they are **project-supplied**, not fixed. Build the list from the questionnaire answers.
Give each a stable ID (`C1`, `C2`, …), a title, a one-line statement, and its source
(`human` decision or `derived` from the legacy app).

Common constraint *archetypes* to consider (include only those that apply — a green-field
target may have none of these; a DB-reuse migration will have the first):

- **Data / database reuse** — e.g. "Reuse the existing database as-is; no schema redesign
  or data migration; ORM validates against the live schema." If chosen, the data model
  must later be captured **exactly** (verbatim table/column names). If the target instead
  gets a fresh schema, say so — it changes how requirements capture the data model.
- **Authentication / authorization** — e.g. "Keep real AD-based auth" vs. "auth seam + dev
  stub, real IdP deferred." Capture the *authorization model* in portable terms (roles →
  groups/claims) regardless.
- **Code style / quality gate** — e.g. "Backend follows the Google Java Style Guide,
  enforced by a formatter in the build." Name the guide and the enforcement mechanism.
- **Compliance / security / data-residency** — any regulatory or org rule the build must
  not violate.
- **CI/CD boundary** — what the pipeline must do (see Step 3).

Write the constraint set into `PROJECT_CONTEXT.md §4` **and** into `state.json`
(`context.constraints`). Downstream stages refer to constraints **by ID** — so once set,
IDs are stable; add new ones with new IDs rather than renumbering.

## Step 3 — Pin the CI/CD Boundary

CI/CD is an input in Set4, but its *scope must be explicit* or every stage interprets it
differently. Record, in `PROJECT_CONTEXT.md §3`:

- **What exists today** — pipeline platform (GitHub Actions, GitLab CI, Azure DevOps,
  Jenkins…), and what it does (build, test, scan, deploy targets, environments).
- **What the modernized app must do** — pick one and state it plainly:
  - **Respect existing** — the build slots into a pipeline that already exists; agents
    must not author pipeline files, only keep the app buildable/testable by it.
  - **Generate** — an implementation phase wires up pipeline files (build, test, quality
    gate, package). If so, note the platform and the required stages.
  - **None yet** — no CI/CD in scope; local build/test only. (Default if unanswered.)

## Step 4 — Write the Artifacts

Produce `PROJECT_CONTEXT.md` (template below) and initialize `state.json` (schema below)
in the location given in the prompt (default: the output folder alongside the other
stages' documents).

---

## Output 1 — `PROJECT_CONTEXT.md`

```markdown
# Project Context: <AppName>

## 1. Summary
- One paragraph: what is being modernized and why, at a glance.

## 2. Stacks
- **Current stack:** languages, frameworks, UI tech, runtime/versions, data store,
  notable libraries. (Confirmed from the legacy app where possible — cite what you saw.)
- **Target stack:** frontend, backend, runtime/versions, build tool, data layer, auth
  libraries, anything mandated. This is the authoritative statement of "what we build in".

## 3. CI/CD
- Current pipeline (platform + what it does).
- Target expectation: Respect existing / Generate / None yet — with specifics.

## 4. Constraints (non-negotiable)
| ID | Title | Statement | Source |
|----|-------|-----------|--------|
| C1 | …     | …         | human / derived |
- One row per constraint. These flow, by ID, through every later stage.

## 5. Intake Questionnaire (resolved)
- The full questionnaire with every answer filled in. Mark defaults as
  `ASSUMPTION: (default applied)` and inferred answers as `ASSUMPTION:`.

## 6. Non-Functional / Quality Requirements (initial)
- Performance, scalability, availability, security posture, accessibility, i18n,
  observability, data-residency — as far as known now. (Requirements Stage deepens these;
  this section seeds them so they aren't forgotten.)

## 7. Open Questions
- Anything unresolved that isn't a hard-stop but should be answered before it compounds.
  Prefix `OPEN QUESTION:`.
```

---

## Output 2 — `state.json` (initialize)

This is the **single source of truth for progress, lineage, and change history** across
all stages. Markdown documents hold human-readable *content*; `state.json` holds
*machine state*. Initialize it with the context filled in and the stage/phase machinery
empty:

```json
{
  "project": "<AppName>",
  "schemaVersion": 1,
  "createdUtc": "<ISO-8601>",
  "updatedUtc": "<ISO-8601>",
  "context": {
    "currentStack": "<short string>",
    "targetStack": "<short string>",
    "cicd": { "mode": "respect | generate | none", "platform": "<or null>", "notes": "" },
    "constraints": [
      { "id": "C1", "title": "", "statement": "", "source": "human | derived" }
    ]
  },
  "stages": {
    "context":      { "status": "complete", "rerunCount": 0, "updatedUtc": "<ISO-8601>" },
    "requirements": { "status": "pending",  "rerunCount": 0 },
    "design":       { "status": "pending",  "rerunCount": 0 },
    "plan":         { "status": "pending",  "rerunCount": 0 }
  },
  "phases": [],
  "changeLog": [],
  "reviews": []
}
```

Field notes (the later stages depend on these; keep them exact):

- **`stages.<name>.status`** — `pending` → `in progress` → `complete`. `rerunCount`
  increments each time a stage is rerun with additional instructions.
- **`phases[]`** — created by the Plan stage. Each: `{ "id": "P-1", "name": "...",
  "status": "pending|in progress|done|accepted", "branchedFrom": "<phase id or null>",
  "acceptedUtc": "<or null>", "reviewStatus": "none|pass|changes-requested",
  "notes": "" }`.
- **`changeLog[]`** — the loop's memory. Each: `{ "id": <int>, "utc": "...",
  "author": "developer|implement-agent|review-agent", "origin":
  "developer-prompt|reconcile|review-<Rid>", "summary": "...", "docsTouched":
  ["requirements|design|plan|context"], "phasesAffected": ["P-3"] }`.
- **`reviews[]`** — created by the Review stage. Each: `{ "id": "R-1", "target": "P-3 |
  whole-build", "utc": "...", "result": "pass|changes-requested", "findingsCount": <int> }`.

Only ever **append** to `changeLog` and `reviews`; never rewrite history.

---

## Intake Questionnaire

The human answers these before Stage 0 runs (or during it). **Load-bearing (hard-stop)**
questions block the pipeline if unanswered; others fall back to the stated default.

**A. Stacks & Scope**
1. **Current stack?** (load-bearing) — languages/frameworks/UI/data store of the legacy
   app. *(Inferable from the legacy app; confirm.)*
2. **Target stack?** (load-bearing) — frontend, backend, runtime + versions, build tool,
   data layer, auth approach.
3. What is explicitly **out of scope** for the modernization? *(Default: nothing — full
   parity.)*

**B. Data**
4. **Reuse the existing database, or create a new schema?** (load-bearing) — drives
   whether the data model is captured verbatim and validated, or redesigned.
5. If reusing: is data **migration** in scope, or connect-as-is? *(Default: connect
   as-is, no migration.)*

**C. Auth**
6. **How does the app authenticate today**, and should the target keep it? (load-bearing
   if the app is access-controlled) — e.g. keep real AD/SSO, or seam + dev stub with the
   real IdP deferred. *(Inferable; confirm.)*

**D. Delivery**
7. **CI/CD expectation?** — Respect existing / Generate / None. *(Default: None yet.)*
8. **Preferred phase count or slicing strategy** for the build? *(Default: agent decides,
   3–7 phases.)*

**E. Quality**
9. **Code style / quality gates** the target must enforce? *(Default: idiomatic style for
   the target stack, formatter in the build if one is standard.)*
10. **Non-functional priorities** — the top 3 of {performance, security, availability,
    accessibility, scalability, observability, i18n}? *(Default: security + correctness.)*
11. **Compliance/regulatory** constraints? *(Default: none stated.)*

*(Add project-specific questions here as needed. Any question the team wants to force an
answer to should be marked load-bearing.)*

---

## Rerunning this Stage

If the human is unhappy with the context, or a decision changes early, rerun with
**Additional Instructions** (see below). On rerun: load the existing `PROJECT_CONTEXT.md`
and `state.json`, apply the changes, **increment `stages.context.rerunCount`**, and — if
a constraint changed after later stages ran — **add a `changeLog` entry** describing the
change and which downstream docs it invalidates, so the affected stages get rerun.

---

## Definition of Done

- [ ] Every load-bearing questionnaire item is answered (not defaulted); no hard-stop is
      outstanding.
- [ ] Current stack and target stack are stated authoritatively.
- [ ] The CI/CD mode is one of respect / generate / none, with specifics.
- [ ] The constraint set is written with stable IDs, in both `PROJECT_CONTEXT.md` and
      `state.json`.
- [ ] `state.json` is initialized per schema, with `phases`, `changeLog`, `reviews` empty.
- [ ] Defaults and inferences are marked `ASSUMPTION:`; unresolved non-blockers are
      `OPEN QUESTION:`.

---

## Additional Instructions

*(The prompt may append project-specific guidance here — the legacy app path, a filled
questionnaire, an output location, or overrides. On a rerun, put the human's change
requests here. Treat these as overrides/additions to the above.)*
