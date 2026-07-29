# AGENTS.md — Template

**Copy this file to the root of your project repository as `AGENTS.md`.** It is loaded into
every agent session automatically, so it carries only the rules that apply to *every* request —
including plain chat that never invokes a stage. Keep it short; stage-specific process lives in
the numbered instruction files.

---

## Before you write anything

Classify what you are about to do **at the moment you are about to write** — not when you read
the prompt. Investigation frequently turns into editing partway through a conversation, and the
gate belongs in front of the edit, not in front of the question.

- **Reading, explaining, diagnosing, running tests** → just do it. No gate, no ceremony.
- **About to change target application code** → this is a phase or a post-phase edit. Stop and
  ask:
  > "This changes built code. Run it through `4_PHASE_IMPLEMENTATION_INSTRUCTIONS.md` — branch,
  > tests, docs, state, PR — or make the change directly?"

  Then follow their answer.
- **About to change a pipeline document** (requirements, HLD, LLD, or the plan) → **don't.**
  Name the stage that owns it and offer to rerun that stage. These documents are the contract
  that later stages are judged against; editing them casually breaks that contract.

**If they choose "directly", still append a `changeLog[]` entry** in `state.json` (author:
`developer`, origin: `out-of-band`) naming what changed. Skipping the process is their call;
skipping the record is not — the next Implement run reconciles against this log, and an
unrecorded change makes its baseline silently wrong.

---

## Invariants — never violate these, in any stage or ad-hoc request

1. **The legacy source is read-only.** Never modify, move, or delete it — in any stage, even
   when it shares a repository with the target code. Build the new tree beside it.
2. **`INTAKE.md` and the `*_TEMPLATE.md` files are inputs — never write to them.** Resolved
   answers belong in `PROJECT_CONTEXT.md §5`.
3. **`state.json`'s `changeLog[]` and `reviews[]` are append-only.** Never rewrite or delete
   history; correct the record by appending to it.
4. **Only the developer marks a phase `accepted`.** An agent may set `in progress` and `done`,
   never `accepted` — that mark means a human tested it.
5. **No secrets anywhere** — not in code, documents, `state.json`, commit messages, or PR
   bodies. Connection strings, IdP config, and credentials come from environment or profiles.
6. **Never mutate a reused database's schema.** Where a data-reuse constraint is in force, fix
   the mapping, never the database.

---

## Constraints

The project's constraints live in `PROJECT_CONTEXT.md §4`, each with a stable ID and its
**per-stage obligations**. Honor every constraint that states an obligation for the work you are
doing, and follow that obligation as written.

Never re-derive constraint rules from first principles: if a constraint should change how
something is done and no obligation says so, raise it as an `OPEN QUESTION:` rather than
inventing the rule. A constraint with no obligation for your stage does not affect it.

---

## Authority when sources conflict

1. **A constraint in `PROJECT_CONTEXT.md §4` always wins.** If honoring it would break a design
   contract, that is a blocker for a human to resolve — not a choice you may make.
2. **For everything else**, in descending order: **plan → LLD → HLD → requirements → the rest of
   `PROJECT_CONTEXT.md`**.
3. **A material conflict is reported, not resolved.** Say what conflicts and stop; do not pick a
   side silently.

---

## Notation

- `ASSUMPTION:` — anything inferred rather than observed or decided by a human.
- `OPEN QUESTION:` — anything unresolved. Never resolve one by guessing.
- Cite evidence as `path:line` (clickable), e.g. `src/data/UserRepository.cs:110`.
- Diagrams in Mermaid, fenced as ```mermaid, with a caption.

---

## When in doubt

**Raise it; don't resolve it silently.** Across every stage the same rule holds: if the inputs
are ambiguous, contradictory, or incomplete, say so and stop — state the blocker, what you
tried, and the options, and let the developer decide. Flag problems rather than fixing them
outside your scope, and never expand scope, redo completed work, or re-decide an upstream
decision without explicit authorization.
