# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The legal algebra — the composition OPERATIONS over :class:`LegalStatement`s.

Two operations, built on the confirmed concrete surfaces (nothing re-grown):

  * :func:`apply` — **statement × facts → conclusion**. Subsume the statement's
    antecedent (its 5D ``cross_subsumption.Condition``s) against a ``FactSpace``
    via ``subsume_antecedent``; the consequence fires ONLY when the antecedent is
    SATISFIED. A presupposed/incomplete fact (OPEN) → the conclusion is OPEN
    (escalate), never a fabricated firing — versum's incompleteness propagates.
  * :func:`resolve_conflict` — **statement × statement → the prevailing statement
    by lex superior ONLY** — the maximal element of the source-hierarchy partial
    order (``grammar.outranks``, the piece this plane owns). When neither outranks
    the other — equal rank OR a genuine antichain — it ⊥ → **escalate**. It does
    NOT resolve lex posterior / specialis or the deontic-modal clash: those are
    the solver's full pack, reached via :func:`resolve` (resolving an antichain by
    recency would fabricate a winner, so it never does).

The deontic-*modal* clash between two applied consequences (O vs F on the same
act) is the solver's, resolved by ``scenario.derive(…, pack=LEX_CONFLICT_PACK)``
— this module resolves the STATEMENT ordering, not the modal formula.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from loomground_solver.cross_subsumption import FactSpace, Verdict, subsume_antecedent

from .grammar import LegalStatement, outranks
from .source_classes import SourceClass
from .sources import ConflictOutcome, Provision, resolve_provisions

__all__ = [
    "Conclusion", "apply",
    "Resolution", "resolve_conflict",
    "Derivation", "derive",
    "to_provision", "resolve",
]


@dataclass(frozen=True)
class Conclusion:
    """Applying a statement to facts: the antecedent's folded verdict, whether the
    consequence therefore fires, and — when it does — the operative content that
    attaches. ``OPEN`` antecedent → escalate; ``NOT_SATISFIED`` → the norm does
    not apply to these facts."""
    verdict: Verdict
    fires: bool
    operative_content: str
    statement: LegalStatement
    per_condition: Tuple = ()

    @property
    def escalates(self) -> bool:
        return self.verdict is Verdict.OPEN


def apply(statement: LegalStatement, facts: FactSpace) -> Conclusion:
    """Statement × facts → conclusion. The antecedent (the statement's 5D
    ``Condition``s) is subsumed against ``facts`` (``subsume_antecedent``, OPEN-
    dominant); the consequence fires iff the antecedent is SATISFIED. An empty
    antecedent is vacuously SATISFIED (an unconditional norm). OPEN → the
    conclusion is OPEN (escalate)."""
    av = subsume_antecedent(statement.antecedent, facts)
    fires = av.verdict is Verdict.SATISFIED
    return Conclusion(av.verdict, fires,
                      statement.operative_content if fires else "",
                      statement, av.conditions)


@dataclass(frozen=True)
class Resolution:
    """The resolution of a collision between two statements: the ``prevailing``
    statement and the ``rule`` that settled it (``lex-superior`` | ``lex-posterior``),
    or ``escalated`` when neither settles it (⊥) — never a fabricated winner."""
    prevailing: Optional[LegalStatement]
    rule: str
    escalated: bool


def resolve_conflict(a: LegalStatement, b: LegalStatement, *,
                     system: Optional[str] = None) -> Resolution:
    """Statement × statement → the prevailing statement by **lex superior only**.

    The higher-ranked class prevails (the maximal element of the source-hierarchy
    partial order). When neither outranks the other — **equal rank** OR a
    **genuine antichain** (e.g. constitutional-identity review vs EU primacy) —
    this is ⊥ → **escalate**. It deliberately does NOT decide lex posterior /
    specialis or the deontic-modal clash: resolving an antichain by recency would
    fabricate a winner. For the full resolution (posterior ▷ specialis, per act,
    with the modal), use :func:`resolve` — the solver's ``LEX_CONFLICT_PACK``."""
    verdict = outranks(a.source_class, b.source_class, system=system)
    if verdict is True:
        return Resolution(a, "lex-superior", False)
    if verdict is False:
        return Resolution(b, "lex-superior", False)
    return Resolution(None, "escalate", True)


# ── derivation / effect-firing (forward-chaining, one pass) ───────────────────

@dataclass(frozen=True)
class Derivation:
    """Firing a set of statements against facts (one forward-chaining pass): the
    statements that FIRED (antecedent SATISFIED → consequence attaches), those
    that ESCALATE (OPEN antecedent — a presupposed/incomplete fact), and those
    that do not apply (NOT_SATISFIED). Full least-fixpoint chaining (a fired
    consequence becoming a new fact) and the deontic-modal clash among fired
    consequences are the solver's (``solve`` / ``resolve``), not re-grown here."""
    fired: Tuple[Conclusion, ...]
    open: Tuple[Conclusion, ...]
    inapplicable: Tuple[Conclusion, ...]

    @property
    def escalates(self) -> bool:
        return bool(self.open)


def derive(statements: Sequence[LegalStatement], facts: FactSpace) -> Derivation:
    """Fire a set of statements against ``facts`` (one forward-chaining pass) —
    :func:`apply` over the set, partitioned by verdict. Honest boundary: a single
    pass; recursive fixpoint and the deontic-modal clash between fired
    consequences are delegated (``solver.subsumption.solve`` / :func:`resolve`)."""
    cs = [apply(s, facts) for s in statements]
    return Derivation(
        tuple(c for c in cs if c.fires),
        tuple(c for c in cs if c.verdict is Verdict.OPEN),
        tuple(c for c in cs if c.verdict is Verdict.NOT_SATISFIED))


# ── deontic-modal conflict on an act → delegated to the solver's LEX pack ─────

# SourceClass → the sources.json rank-map source_type (the lex-superior key).
# Classes with no rank entry (case law, soft law, standards, treaties) are not
# rankable by the source-type map — they cannot enter this conflict → escalate.
_SOURCE_TYPE = {
    SourceClass.CONSTITUTION: "national_constitution",
    SourceClass.NATIONAL_STATUTE: "national_statute",
    SourceClass.NATIONAL_REGULATION: "national_regulation",
    SourceClass.SUPRANATIONAL_PRIMARY: "eu_primary_law",
    SourceClass.SUPRANATIONAL_REGULATION: "eu_regulation",
    SourceClass.SUPRANATIONAL_DIRECTIVE: "eu_directive",
}


def to_provision(statement: LegalStatement, *, act: str,
                 provision_id: Optional[str] = None, specificity: int = 0,
                 time: Optional[int] = None) -> Provision:
    """Bridge a :class:`LegalStatement` to a ``sources.Provision`` for the
    solver-delegated conflict resolution: ``source_type`` from the class rank-map,
    ``content`` from the operative content. ``act`` and ``specificity`` are supplied.

    ``time`` is the norm's **enactment/adoption** date (a monotonic int, e.g.
    ``20180525``) — the lex-*posterior* key. Supply it explicitly; an unknown date
    is ``0``, which the pack treats as "no date" (it cannot be separated by
    posterior — :func:`resolve` escalates rather than let a fabricated epoch decide
    it). It is NOT inferred from the ``expression_id`` (that encodes the
    event/consolidation date, not enactment — an unreliable posterior key). A
    non-rankable class raises ``ValueError``."""
    st = _SOURCE_TYPE.get(statement.source_class)
    if st is None:
        raise ValueError(
            f"{statement.source_class.value} is not rankable in the source-type "
            f"map; it cannot enter a lex conflict (escalate)")
    return Provision(id=provision_id or statement.label(), act=act,
                     content=statement.operative_content, source_type=st,
                     specificity=specificity, time=time if time is not None else 0)


def _escalate_outcome(act: str) -> ConflictOutcome:
    """A graceful escalate outcome (⊥) — no fabricated winner, no crash."""
    return ConflictOutcome(act=act, status="open", verdict="", winner=None,
                           rule="escalate", escalated=True, resolution=None)


def resolve(statements: Sequence[LegalStatement], *, act: str,
            specificity: Optional[Sequence[int]] = None,
            times: Optional[Sequence[int]] = None) -> Optional[ConflictOutcome]:
    """Statements colliding on one ``act`` → the solver's FULL lex resolution
    (superior ▷ specialis ▷ posterior), delegated to ``sources.resolve_provisions``
    (which runs ``LEX_CONFLICT_PACK``). Returns the act's :class:`ConflictOutcome`
    — ``status='open'`` when the pack cannot separate a genuine clash (escalate,
    never a fabricated winner) — or **``None`` when there is no collision on the
    act** (the provisions agree, so there is nothing to resolve).

    Fail-SAFE, never fail-hard or fabricate:
      * a **non-rankable** statement (case law / soft law / standards / treaty)
        → a graceful escalate outcome, NOT a raised ``ValueError``;
      * a **lex-posterior** decision that turned on an **unknown enactment date**
        (a statement with no explicit ``time`` → ``0``) → escalate, because the
        loser lost for being undated, not on the merits.

    ``times`` are the per-statement **enactment** dates (int ``YYYYMMDD``) — supply
    them for a correct lex posterior."""
    n = len(statements)
    specs = list(specificity) if specificity is not None else [0] * n
    tms = list(times) if times is not None else [None] * n
    try:
        provisions = [to_provision(s, act=act, provision_id=f"p{i}",
                                   specificity=specs[i], time=tms[i])
                      for i, s in enumerate(statements)]
    except ValueError:
        return _escalate_outcome(act)          # F1: non-rankable → escalate, not crash
    outcome = resolve_provisions(provisions).get(act)
    if outcome is None:
        return None
    # F2/F3: don't trust a posterior decision made on an unknown (0) enactment date
    if outcome.rule == "lex-posterior" and any(p.time == 0 for p in provisions):
        return _escalate_outcome(act)
    return outcome
