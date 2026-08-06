# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Applicability / scope — does instrument I bind entity E for act A at time T?

Reach is answered by *composition*, not by rules written here: the caller
supplies the connection chain from the entity to the legal order behind the
instrument (e.g. ``ACME —incorporated_in→ DE —member_of→ EU``), and this module
folds it through the legal :class:`~loomground_solver.RelationAlgebra`
(:func:`~loomground_legal.connection.connection_algebra`). The entity is
reached exactly when the chain composes to a *governing* relation
(``subject_to`` / ``bound_by``, the :data:`~loomground_legal.connection.GOVERNING`
set); a legally contested chain surfaces the solver's
:data:`~loomground_solver.ESCALATE` as ``applies=None`` — the
escalate-don't-guess discipline: contested reach is an open question, never a
guessed yes or no.

The four scope axes are covered as follows: **territorial** and **personal**
and **material** grounds are the first link of the chain (classified by the
:data:`GROUND_AXIS` data map — GDPR Art 3(1) establishment is territorial,
Art 3(2) targeting is material/conduct-based); the **temporal** axis is the
instrument's own life and is consumed as a fact (``in_force``, resolved by
:mod:`loomground_legal.lifecycle`) — an instrument not in force at T reaches
nobody, whatever the chain says.

DATA + a thin bridge only: no composition logic lives here (the solver owns
``compose_path``), and no scope doctrine is hardcoded beyond the axis labels.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional, Sequence, Tuple

from .connection import GOVERNING, connection_algebra, is_connection

__all__ = ["ScopeResult", "scope_applies", "GROUND_AXIS"]

#: Scope axis of a *grounding* relation (the first link of a reach chain) —
#: pure classification data. Establishment-type grounds are territorial
#: (GDPR Art 3(1)); nationality is personal; targeting is material /
#: conduct-based (GDPR Art 3(2) offering of goods or services).
GROUND_AXIS: Mapping[str, str] = MappingProxyType(
    {
        "incorporated_in": "territorial",
        "established_in": "territorial",
        "resident_in": "territorial",
        "applies_in": "territorial",
        "national_of": "personal",
        "subject_to": "personal",
        "targets": "material",
    }
)

#: The axis assigned when the instrument is out of force at T.
_TEMPORAL = "temporal"


@dataclass(frozen=True)
class ScopeResult:
    """The answer to a reach question.

    ``applies`` is ``True`` (the chain composes to a governing relation),
    ``False`` (it composes to something else, to nothing, or the instrument is
    out of force), or ``None`` with ``escalated=True`` — contested reach, an
    open legal question that must be surfaced, never guessed. ``basis`` is the
    composed relation the answer rests on ('' when there is none), ``axis`` is
    the scope axis of the grounding link ('' when unclassified), and ``chain``
    is the connection chain as queried (empty for a temporal refusal).
    """

    applies: Optional[bool]
    basis: str
    escalated: bool
    axis: str
    chain: Tuple[str, ...]


def scope_applies(
    chain: Sequence[str], *, in_force: bool = True
) -> ScopeResult:
    """Does the instrument reach the entity along ``chain``?

    ``chain`` is the connection path from the entity to the legal order behind
    the instrument, in walking order (entity-side first). ``in_force`` is the
    temporal axis, resolved upstream (see :mod:`loomground_legal.lifecycle`):
    ``False`` short-circuits to *does not apply* on the temporal axis.

    Fail-closed: a relation name outside the legal connection vocabulary is a
    ``ValueError``, never a silent non-answer. Composition itself is entirely
    the solver's ``compose_path``; an escalated fold returns
    ``applies=None, escalated=True`` (contested reach).
    """
    if not in_force:
        return ScopeResult(
            applies=False, basis="", escalated=False, axis=_TEMPORAL, chain=()
        )
    links = tuple(chain)
    if not links:
        raise ValueError("scope_applies needs a non-empty connection chain")
    for link in links:
        if not is_connection(link):
            raise ValueError(
                f"{link!r} is not a legal connection relation; "
                "scope never guesses over unknown edges"
            )
    result, escalated = connection_algebra().compose_path(links)
    axis = GROUND_AXIS.get(links[0], "")
    if escalated:
        # Contested somewhere in the chain: the whole reach question is open.
        return ScopeResult(
            applies=None, basis="", escalated=True, axis=axis, chain=links
        )
    if result in GOVERNING:
        return ScopeResult(
            applies=True, basis=str(result), escalated=False, axis=axis, chain=links
        )
    return ScopeResult(
        applies=False,
        basis="" if result is None else str(result),
        escalated=False,
        axis=axis,
        chain=links,
    )
