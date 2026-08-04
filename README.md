# loomground-legal

The **legal domain plane** of the Loomground family. It owns what no other plane
does — legal *entities*, *jurisdictional* structure, *sources of law*, and
*instrument lifecycle* — and it borrows every *mechanism* from the family:
modality from [`loomground-deontic`](https://github.com/flxk1/loomground-deontic),
rule reasoning from [`loomground-norm`](https://github.com/flxk1/loomground-norm),
and composition / conflict / grounded reasoning from
[`loomground-solver`](https://github.com/flxk1/loomground-solver). It supplies
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
  effect.py              legal-effect -> deontic bridge
  artifacts/
    connections.json     the connection vocabulary + composition table (data)
```

Planned (slice 2): `scope.py` (applicability), `sources.py` (sources-of-law +
lex maxims on the solver's conflict packs), `lifecycle.py` (supersedes/amends),
`citation.py` (article/paragraph/recital model, modelled fresh).

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
