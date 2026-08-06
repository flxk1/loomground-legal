# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The legal algebra — the composition OPERATIONS over :class:`LegalStatement`s.

Two operations, built on the confirmed concrete surfaces (nothing re-grown):

  * :func:`apply` — **statement × facts → conclusion**. Subsume the statement's
    antecedent (its 5D ``cross_subsumption.Condition``s) against a ``FactSpace``
    via ``subsume_antecedent``; the consequence fires ONLY when the antecedent is
    SATISFIED. A presupposed/incomplete fact (OPEN) → the conclusion is OPEN
    (escalate), never a fabricated firing — versum's incompleteness propagates.
  * :func:`resolve_conflict` — **statement × statement → the prevailing statement**.
    Lex superior over the source-hierarchy partial order (``grammar.outranks``)
    first; on an antichain, lex posterior by version date (``intertemporal`` /
    ``identifiers`` expression ids). Lex specialis and full defeasible (Dung)
    resolution are NOT decided here — if neither superior nor posterior settles
    it, ⊥ → **escalate**, never a fabricated winner.

The deontic-*modal* clash between two applied consequences (O vs F on the same
act) is the solver's, resolved by ``scenario.derive(…, pack=LEX_CONFLICT_PACK)``
— this module resolves the STATEMENT ordering, not the modal formula.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from loomground_solver.cross_subsumption import FactSpace, Verdict, subsume_antecedent

from .grammar import LegalStatement, outranks

__all__ = ["Conclusion", "apply", "Resolution", "resolve_conflict"]


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


def _version_date(expression_id: str) -> Optional[str]:
    """The YYYYMMDD in-force date carried by an expression id — consolidated CELEX
    ``…-YYYYMMDD`` or ``code@YYYY-MM-DD`` — for lex posterior. ``None`` if absent;
    fixed-width digits compare chronologically as strings."""
    if not expression_id:
        return None
    if "@" in expression_id:
        tail = expression_id.split("@", 1)[1].replace("-", "")
    elif "-" in expression_id:
        tail = expression_id.rsplit("-", 1)[1]
    else:
        return None
    return tail if tail.isdigit() and len(tail) == 8 else None


def resolve_conflict(a: LegalStatement, b: LegalStatement, *,
                     system: Optional[str] = None) -> Resolution:
    """Statement × statement → the prevailing statement.

    Lex superior (the source-hierarchy partial order) first — the higher-ranked
    class prevails. On an **antichain** (incomparable classes, e.g. constitution
    vs supranational-primary), fall to **lex posterior**: the statement with the
    later version date wins. If neither superior nor posterior settles it — no
    ordering, or no comparable dates — ⊥ → **escalate** (lex specialis and full
    defeasible resolution are not built here)."""
    verdict = outranks(a.source_class, b.source_class, system=system)
    if verdict is True:
        return Resolution(a, "lex-superior", False)
    if verdict is False:
        return Resolution(b, "lex-superior", False)

    da, db = _version_date(a.expression_id), _version_date(b.expression_id)
    if da and db and da != db:
        return Resolution(a if da > db else b, "lex-posterior", False)

    return Resolution(None, "escalate", True)
