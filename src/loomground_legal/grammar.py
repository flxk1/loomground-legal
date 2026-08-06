# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The legal grammar — the canonical legal STATEMENT, its recognition gate, and
the source-hierarchy partial order. Grammar-first: this is the well-formed unit
the rest of the plane's reasoning operates over.

Legal is the **hub** of a composite algebra; deontic is one *consumed* spoke.
The mathematical spine (reasoning-DoD §0.9) is mostly ALREADY concrete solver
code, and this module **consumes it, re-inventing nothing**:

  * three-valued verdict + weakest-link fold → ``cross_subsumption`` (the
    antecedent is a tuple of its :class:`Condition`s; reasoning evaluates them
    via ``review_against_facts`` — see :mod:`worked`);
  * relation algebra (source relations / competence) → ``solver.relation``;
  * modal / deontic O·P·F + Hohfeld → ``deontic``, reached through
    :func:`effect.legal_effect` (the consequence lowers to an operator, or to a
    constitutive incident with ``operator=None``);
  * temporal validity-at-T → :mod:`intertemporal` / :mod:`lifecycle`
    (the statement carries its ``expression_id``).

The **one genuinely-new algebraic piece** here is the source hierarchy as a
**partial order** (:func:`outranks`) with maximal-element selection
(:func:`lex_superior`) — lex superior. Where two source classes are
**incomparable** the order returns ``None``: an antichain, ⊥, the honest boundary
where lex superior does not settle a collision. Lex specialis / posterior and
full **defeasible** resolution (a Dung argumentation framework) are **NOT**
implemented — that is the solver's conflict pack (``LEX_CONFLICT_PACK``) or an
escalation; this module formalises only the ordering and escalates the rest.

Pure stdlib + the consumed algebras; no norm mechanism re-grown.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from loomground_solver.cross_subsumption import Condition

from . import legal_systems
from .effect import OPERATIVE_CONTENT, legal_effect
from .source_classes import Effect, SourceClass, SourceFinding, check_source, is_relation

__all__ = [
    "LegalStatement",
    "WellFormedness",
    "validate",
    "is_well_formed",
    "outranks",
    "lex_superior",
]


@dataclass(frozen=True)
class LegalStatement:
    """The canonical legal statement — the composite element of the legal algebra,
    unifying the five representations the norm was smeared across (DoD §4.3 #8):

      * **source-context (nD)** — the ``source`` (instrument code / CELEX), its
        ``source_class`` and the ``claimed_effect`` (force), and its ``relations``;
      * **consequence** — the ``operative_content`` (an ``effect.OPERATIVE_CONTENT``
        kind), which lowers to a deontic operator OR a constitutive incident;
      * **antecedent** — the 5D factual predicate (the Tatbestand) as a tuple of
        ``cross_subsumption.Condition``, evaluated at reasoning time, not here;
      * **temporal validity** — the versioned ``expression_id`` (intertemporal).

    Well-formedness is :func:`validate`; the algebra's operations compose
    statements, consuming the solver's concrete algebras."""

    source: str
    source_class: SourceClass
    claimed_effect: Effect
    operative_content: str
    antecedent: Tuple[Condition, ...] = ()
    relations: Tuple[Tuple[str, str], ...] = ()          # (relation, object)
    expression_id: str = ""
    has_incorporation_edge: bool = False
    self_executing_extra: Optional[frozenset] = None

    def label(self) -> str:
        return self.expression_id or self.source


@dataclass(frozen=True)
class WellFormedness:
    """The recognition-gate verdict: is this a well-formed legal statement, the
    SC findings that say why not, and the deontic operator the consequence lowers
    to (``None`` when the effect is constitutive — a power/definition/establishment)."""

    well_formed: bool
    findings: Tuple[SourceFinding, ...]          # SC-2 / SC-3 violations (empty == clean)
    deontic_operator: Optional[str]              # O·P·F, or None for a constitutive effect
    issues: Tuple[str, ...] = ()                 # SC-4 / unrecognised-content issues


def validate(stmt: LegalStatement) -> WellFormedness:
    """The **recognition gate** — Hart's rule of recognition, made a check. Consumes:

      * ``source_classes.check_source`` — SC-2 (claimed force ≤ the class ceiling:
        a technical standard is never BINDING) + SC-3 (a non-self-executing source
        asserted BINDING needs an incorporation edge);
      * ``source_classes.is_relation`` — SC-4 (every relation is in the admissible
        vocabulary);
      * ``effect.legal_effect`` — the operative content lowers to a deontic
        operator or a constitutive incident.

    Fail-closed: an unrecognised operative content or an inadmissible relation is a
    recorded issue, never a guess."""
    findings = tuple(check_source(
        stmt.source_class, claimed_effect=stmt.claimed_effect,
        has_incorporation_edge=stmt.has_incorporation_edge,
        self_executing_extra=stmt.self_executing_extra))

    issues: list[str] = []
    for rel, obj in stmt.relations:
        if not is_relation(rel):
            issues.append(f"relation {rel!r} → {obj!r} is not in the admissible "
                          f"vocabulary (SC-4)")

    operator: Optional[str] = None
    if stmt.operative_content not in OPERATIVE_CONTENT:
        issues.append(f"operative content {stmt.operative_content!r} is not a "
                      f"recognised kind (one of {tuple(OPERATIVE_CONTENT)})")
    else:
        operator = legal_effect(stmt.operative_content).operator

    return WellFormedness(not findings and not issues, findings, operator, tuple(issues))


def is_well_formed(stmt: LegalStatement) -> bool:
    return validate(stmt).well_formed


# ── the source-hierarchy partial order — the one genuinely-new algebraic piece ─

def outranks(higher: SourceClass, lower: SourceClass, *,
             system: Optional[str] = None) -> Optional[bool]:
    """Lex superior as a **partial order** over source classes, per the active
    legal system's ``class_rank`` (highest first). ``True`` if ``higher`` outranks
    ``lower``, ``False`` for the reverse, and **``None`` when the two are
    incomparable** — an antichain: ⊥, the honest boundary where lex superior does
    not settle a collision (the caller escalates, never fabricating a winner)."""
    rank = legal_systems.get(system).class_rank
    if higher not in rank or lower not in rank or higher == lower:
        return None
    return rank.index(higher) < rank.index(lower)


def lex_superior(a: LegalStatement, b: LegalStatement, *,
                 system: Optional[str] = None) -> Optional[LegalStatement]:
    """The prevailing statement of a collision by **lex superior alone** — the
    maximal element of the source-class partial order. Returns the higher-ranked
    statement, or **``None``** when the classes are incomparable (antichain →
    escalate). Lex specialis / posterior and full defeasible (Dung) resolution are
    NOT decided here — that is the solver's ``LEX_CONFLICT_PACK`` or an escalation;
    this composes only the ordering."""
    verdict = outranks(a.source_class, b.source_class, system=system)
    if verdict is True:
        return a
    if verdict is False:
        return b
    return None
