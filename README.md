# loomground-legal

The **legal domain plane** of the Loomground family. It owns what no other plane
does — legal *entities*, *jurisdictional* structure, *sources of law*, and
*instrument lifecycle* — and it borrows every *mechanism* from the family:
modality from [`loomground-deontic`](https://github.com/flxk1/loomground-deontic),
and composition / conflict / grounded reasoning from
[`loomground-solver`](https://github.com/flxk1/loomground-solver) — provisions
lower to solver `Norm`s and the lex maxims run in the solver's
`LEX_CONFLICT_PACK`. It supplies
**data and bridges only** and grows no reasoning of its own.

## What it is (and is not)

- **Connection algebra** — a jurisdiction/legal-person/instrument relation
  vocabulary and a *partial* composition table (`incorporated_in ∘ member_of →
  subject_to`; contested reach → `ESCALATE`). The table is **data**; the engine
  is the solver's `RelationAlgebra`. Legal carries no `compose` logic.
- **Legal-effect → deontic bridge** — maps a provision's operative content to
  its legal effect: duty → **O**, permission/liberty → **P**, prohibition →
  **F**, power/immunity → the Hohfeld incidents. A statutory *right* is **never**
  a fourth "R" operator — it is a permission, or a claim-right via
  `deontic.correlative` (claim ↔ duty).
- **Scope / applicability** — "does instrument I bind entity E for act A at
  time T?" answered by *composing* the entity's connection chain on the
  solver's algebra (GDPR Art 3(1) establishment / Art 3(2) targeting are the
  reference cases); contested reach comes back `applies=None` + escalated.
- **Sources of law** — a source-type rank map (`artifacts/sources.json`,
  data) and a lowering of provisions into solver `Norm`s; *lex superior /
  specialis / posterior* run entirely in the solver's `LEX_CONFLICT_PACK`
  via `derive(...)` — a conflict the pack cannot separate escalates as a
  genuine collision.
- **Instrument lifecycle** — dated `supersedes` / `repeals` / `amends` events
  over the lineage relations; deterministic "which version is in force at T".
- **Citation model** — a typed `Citation` (article / paragraph / point /
  subparagraph / recital / annex), a fresh parser for the common forms,
  internal cross-reference resolution, and definition binding ("as defined in
  Art 4(1)"). What it cannot parse it leaves unset — never a guessed locus.
- **Not** governance (agent oversight), **not** norm (generic rule reasoning),
  **not** the solver (domain-agnostic engine). Legal is the domain those planes
  deliberately exclude.

The escalate-don't-guess discipline runs through it: contested law
(extraterritorial reach, treaty self-execution, corporate-group attribution)
surfaces as `ESCALATE`, never a fabricated resolution.

## Layout

```
src/loomground_legal/
  entities.py            typed legal entities (Jurisdiction, LegalPerson, Instrument, Body)
  connection.py          builds a solver RelationAlgebra from artifacts/connections.json
  scope.py               applicability/reach by composition (contested -> ESCALATE)
  sources.py             sources-of-law rank + lex maxims, delegated to the solver
  lifecycle.py           instrument lifecycle & lineage; in-force-at-T
  citation.py            citation model + parser, xref + definition binding (fresh)
  effect.py              legal-effect -> deontic bridge
  artifacts/
    connections.json     the connection vocabulary + composition table (data)
    sources.json         the source-type rank map + conflict notes (data)
```

## Development

The family is a set of sibling repositories. For local development, check them
out beside this one and either install the pinned dev set

```
python3 -m pip install -r requirements-dev.txt
python3 -m pytest
```

or, if the sibling packages are present but not installed, `conftest.py` adds
their `src/` directories to the path so `pytest` runs from a fresh checkout with
no install step. Canonical resolution for CI is the git-tag pin set in
`requirements-dev.txt`. Release mechanics are in `RELEASING.md`.
