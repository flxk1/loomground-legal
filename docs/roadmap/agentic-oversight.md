# Roadmap slice — the legal plane and agentic oversight

Status: **draft, not committed scope.** Non-normative.

A set of open problems in agentic oversight reaches this plane as one question:
**how do you reconstruct a legally meaningful chain of agency after an autonomous
multi-agent decision?**

That question is this plane's business precisely because it is not a technical
one. A signed record of who called what is an engineering artefact; whether the
resulting act is attributable to a principal is a doctrinal one, and the doctrine
is old. This slice records where the existing plane already reaches and where it
does not.

The plane discipline holds throughout: **data and bridges only, no reasoning of
its own.** Composition runs on the solver's `RelationAlgebra`, conflict on its
`LEX_CONFLICT_PACK`, modality on deontic. Anything below that looks like
inference belongs to the solver, and the escalate-don't-guess rule applies
without exception — contested attribution surfaces as `ESCALATE`, never as a
fabricated holder.

---

## L1 · Delegation has a technical chain and no authority doctrine

An acyclic principal chain, attenuated so that no delegate holds more than its
delegator, is a good technical model. It answers *what was permitted*. It does
not answer the question that decides a dispute: **when a delegate acts outside
what it was authorised to achieve, whose act is it?**

Law has answered that for a long time, and the answer is not "nobody's". Actual
authority, apparent authority, ratification, and acting beyond authority are
distinct doctrines with distinct consequences, and a chain that records only
grants cannot distinguish them. The distinction matters most in exactly the case
the technical model handles worst: a delegate that stayed inside its permissions
and outside its purpose.

*Candidate shape.* A typed authority vocabulary as **data** — the kinds of
authority, and their consequence for attribution — with the composition it needs
expressed as relation entries the solver's algebra evaluates. No `compose` logic
here, matching how the connection algebra is already carried.

*Open, and stated as open.* Apparent authority turns on what a third party
reasonably believed. Whether that has any counterpart when the third party is
itself an automated system is genuinely unsettled, and this slice does not
pretend to settle it. It is a candidate for the `ESCALATE` treatment rather than
for a rule.

---

## L2 · Attribution along a chain is a composition, and the table is missing

The connection algebra composes an entity's chain — `incorporated_in ∘ member_of
→ subject_to`, with contested reach escalating. The structure needed for
attribution is the same shape: compose a delegation chain and ask what the
composition yields for responsibility.

For a chain of the form

```
board → employee → enterprise agent → planning agent → procurement agent
```

the technical record shows five hops. What a reviewer needs is which of them are
attribution-bearing — and that is a partial function, with genuine gaps, exactly
like the connection table.

*Candidate shape.* A delegation-relation vocabulary and a **partial** composition
table, in the shape `connections.json` already uses. Partial is the point: the
entries that do not compose must escalate, because a total table here would be a
fabricated answer to a contested question.

---

## L3 · Causation is the solver's, and the doctrine is not

Attributing an outcome along a chain needs causal reasoning, and the solver has
`causal_construction`. What it does not have — correctly — is the legal overlay:
the distinction between factual and legal causation, intervening acts, and the
foreseeability limits that stop a chain from extending indefinitely.

That overlay is doctrinal data, and an autonomous multi-agent chain is where its
absence bites: without a limiting principle, every upstream principal is
implicated in every downstream effect, which is both useless and wrong.

*Candidate shape.* The limiting doctrines as data, lowered into the solver the
way provisions already lower into `Norm`s. The reasoning stays there.

---

## L4 · Instrument lifecycle already answers "which rules applied when"

Worth recording as **present, not missing.** A decision taken by an autonomous
chain months ago was governed by whatever was in force at the time, and
reconstructing that is exactly what the lifecycle module does: dated `supersedes`
/ `repeals` / `amends` over lineage relations, and a deterministic answer to
which version was in force at T.

Nothing needs building. What is needed is that the agency record produced
downstream **carries the time** at which each hop occurred, so the existing
answer can be used. That is a requirement this plane places on a consumer, not
work this plane does.

---

## L5 · Cross-border chains are already an escalate case

A delegation chain that crosses jurisdictions raises the reach question the scope
module already handles — establishment and targeting, with contested reach
returning `applies=None` and escalating.

The temptation, when an agent chain crosses a border mid-run, is to resolve reach
so the run can continue. That would invert the plane's discipline for
convenience. A chain whose reach is contested escalates, and the run waits or the
host decides; it does not receive an invented answer because a machine was
mid-task.

---

## Sequencing

| Step | Item | Reach |
|---|---|---|
| 1 | L4 | no code — a documented requirement on the record's shape |
| 2 | L2 | `artifacts/` delegation vocabulary + partial composition table |
| 3 | L1 | authority-kind vocabulary as data; apparent authority left open |
| 4 | L3 | limiting doctrines as data, lowered to the solver |

## Gates

`python3 -m pytest` green from a fresh checkout. Every step must add **data and a
bridge only**; a step that grows a `compose`, a conflict resolver, or any
inference of its own has left the plane. Contested attribution escalates —
a composition table that resolves every pair is evidence of a bug, not of
completeness.
