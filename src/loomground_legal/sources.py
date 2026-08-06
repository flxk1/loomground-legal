# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Sources-of-law hierarchy — rank data in, solver conflict resolution out.

This module owns exactly two things: the **source-type rank map**
(``artifacts/sources.json`` — which kind of source outranks which, as data)
and the **lowering** of legal provisions into the solver's ``Norm`` form
(deontic modal via :mod:`loomground_legal.effect`, rank via the artifact,
specificity and time as per-provision facts).

Conflict resolution itself — *lex superior* ▷ *lex specialis* ▷ *lex
posterior*, grounded-extension defeat, genuine-collision detection — is the
solver's, whole and entire: :func:`resolve_provisions` builds a
``Scenario`` and calls ``loomground_solver.derive(scenario,
pack=LEX_CONFLICT_PACK)``. No defeat rule, no ordering comparison, and no
contradiction table is implemented here; the winner and the separating rule in
a :class:`ConflictOutcome` are read verbatim off the solver's
``ActResolution``. Two provisions the pack cannot separate come back
``status='open'`` — a genuine collision, escalated, never auto-resolved.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any, Dict, Optional, Sequence, Tuple

from deontic import OP_OBLIGATION, OP_PERMISSION, OP_PROHIBITION
from loomground_solver import LEX_CONFLICT_PACK, ActResolution, Norm, Scenario, derive

from .effect import legal_effect

__all__ = [
    "Provision",
    "ConflictOutcome",
    "load_sources",
    "source_rank",
    "to_norm",
    "resolve_provisions",
]

#: deontic operator → the solver Norm's deontic modal (pure vocabulary bridge).
_DEONTIC_OF_OPERATOR: Dict[str, str] = {
    OP_OBLIGATION: "obligatory",
    OP_PERMISSION: "permitted",
    OP_PROHIBITION: "prohibited",
}


def load_sources() -> Dict[str, Any]:
    """The raw ``sources.json`` payload (parsed, untranslated)."""
    ref = resources.files("loomground_legal").joinpath("artifacts/sources.json")
    return json.loads(ref.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _ranks() -> Dict[str, int]:
    data = load_sources()
    ranks = {k: int(v) for k, v in data["ranks"].items()}
    order = data["rank_order"]
    if set(order) != set(ranks):
        raise ValueError("sources.json rank_order and ranks disagree")
    if [r for r in order] != sorted(order, key=lambda k: -ranks[k]):
        raise ValueError("sources.json rank_order is not in descending rank order")
    return ranks


def source_rank(source_type: str) -> int:
    """The lex-superior rank of a source type (higher wins). Fail-closed:
    an unknown source type is a ``ValueError``, never rank 0 by accident."""
    ranks = _ranks()
    if source_type not in ranks:
        raise ValueError(
            f"unknown source type {source_type!r}; expected one of "
            f"{sorted(ranks)}"
        )
    return ranks[source_type]


@dataclass(frozen=True)
class Provision:
    """One legal provision as conflict input — pure data.

    ``content`` is an operative-content kind accepted by
    :func:`loomground_legal.effect.legal_effect` that carries a deontic modal
    (duty / permission / liberty / prohibition / right); ``source_type`` keys
    into the rank map; ``specificity`` and ``time`` are the per-provision facts
    the *lex specialis* / *lex posterior* defeaters compare (time as a
    monotonic integer, e.g. ``20180525``).
    """

    id: str
    act: str
    content: str
    source_type: str
    specificity: int = 0
    time: int = 0


def to_norm(provision: Provision) -> Norm:
    """Lower a provision to the solver's ``Norm``: modal via the effect
    bridge, rank via ``sources.json``. A provision whose operative content has
    no deontic modal of its own (definition, power, ...) cannot enter a norm
    conflict — ``ValueError``, fail-closed."""
    effect = legal_effect(provision.content)
    if effect.operator is None:
        raise ValueError(
            f"provision {provision.id!r} has operative content "
            f"{provision.content!r} with no deontic modal; it cannot be a Norm"
        )
    return Norm(
        act=provision.act,
        deontic=_DEONTIC_OF_OPERATOR[effect.operator],
        source=provision.id,
        rank=source_rank(provision.source_type),
        specificity=provision.specificity,
        time=provision.time,
    )


@dataclass(frozen=True)
class ConflictOutcome:
    """One act's answer, read verbatim off the solver's ``ActResolution``.

    ``winner``/``rule`` are set only for a determinate answer with a unique
    surviving provision: the winner is that provision's id, the rule is the
    solver-named separating ordering (``'lex-superior'`` | ``'lex-specialis'``
    | ``'lex-posterior'``) taken from the resolution's defeat records.
    ``escalated=True`` mirrors ``status='open'`` — a genuine collision the
    pack could not separate; the open question is surfaced, never resolved
    here. ``resolution`` is the solver's full record (provenance)."""

    act: str
    status: str
    verdict: Optional[str]
    winner: Optional[str]
    rule: Optional[str]
    escalated: bool
    resolution: ActResolution


def _outcome(resolution: ActResolution) -> ConflictOutcome:
    winner: Optional[str] = None
    rule: Optional[str] = None
    if resolution.status == "determinate" and len(resolution.survivors) == 1:
        winner = resolution.survivors[0]
        rules = sorted(
            {d["rule"] for d in resolution.defeats if d["winner"] == winner and d["rule"]}
        )
        rule = rules[0] if rules else None
    return ConflictOutcome(
        act=resolution.act,
        status=resolution.status,
        verdict=resolution.verdict,
        winner=winner,
        rule=rule,
        escalated=resolution.status == "open",
        resolution=resolution,
    )


def resolve_provisions(
    provisions: Sequence[Provision], *, scenario_id: str = "legal-sources"
) -> Dict[str, ConflictOutcome]:
    """Resolve conflicting provisions — by DELEGATION, per act.

    Lowers every provision to a ``Norm``, builds a ``Scenario``, and hands the
    whole conflict to the solver::

        result = derive(scenario, pack=LEX_CONFLICT_PACK)

    ``LEX_CONFLICT_PACK`` applies lex-superior (rank) ▷ lex-specialis
    (specificity) ▷ lex-posterior (time); this module contributes only the
    data those orderings compare. Returns ``act → ConflictOutcome``. An act
    whose collision the pack cannot separate comes back ``status='open'`` /
    ``escalated=True`` with no winner — escalate, don't guess."""
    if not provisions:
        raise ValueError("resolve_provisions needs at least one provision")
    norms = [to_norm(p) for p in provisions]
    scenario = Scenario(id=scenario_id, norms=norms)
    result = derive(scenario, pack=LEX_CONFLICT_PACK)
    return {act: _outcome(res) for act, res in result.acts.items()}
