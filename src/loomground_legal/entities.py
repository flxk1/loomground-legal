# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Typed legal entities — the nodes of the legal world map.

Four node types cover the layers the connection algebra runs over: legal
orders (:class:`Jurisdiction`), the persons the law reaches
(:class:`LegalPerson`), the instruments that carry it (:class:`Instrument`),
and the bodies that make/apply/enforce it (:class:`Body`). Simple dataclasses,
data only — every edge *between* them is a connection relation and lives in
:mod:`loomground_legal.connection`; nothing here composes or infers.

Each entity projects to a 5D :class:`~loomground_solver.Dimension` so a
world-map node maps one-to-one into a dimensioned knowledge graph:

* ``Jurisdiction`` → STRUCTURAL — a legal order is how the map is *built*;
* ``LegalPerson``  → RELATIONAL — the person is what the law is *linked to*;
* ``Instrument``   → CAUSAL — the instrument is what brings the law to bear;
* ``Body``         → INTENTIONAL — a body is defined by its mandate/purpose.

Kinds are validated fail-closed at construction: a typo'd kind is a
``ValueError``, never a silently unclassified node.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, FrozenSet

from loomground_solver import Dimension

__all__ = ["Jurisdiction", "LegalPerson", "Instrument", "Body"]


def _check_kind(kind: str, allowed: FrozenSet[str], entity: str) -> None:
    if kind not in allowed:
        raise ValueError(
            f"{entity}.kind must be one of {sorted(allowed)}, got {kind!r}"
        )


@dataclass(frozen=True)
class Jurisdiction:
    """A legal order — a state, a union, a subnational order, a treaty regime."""

    id: str
    name: str = ""

    dimension: ClassVar[Dimension] = Dimension.STRUCTURAL


@dataclass(frozen=True)
class LegalPerson:
    """A person the law reaches — natural or legal (company, association, ...)."""

    KINDS: ClassVar[FrozenSet[str]] = frozenset({"natural", "legal"})

    id: str
    kind: str = "legal"
    name: str = ""

    dimension: ClassVar[Dimension] = Dimension.RELATIONAL

    def __post_init__(self) -> None:
        _check_kind(self.kind, self.KINDS, "LegalPerson")


@dataclass(frozen=True)
class Instrument:
    """A carrier of legal content — regulation, directive, treaty, decision,
    or (harmonised/technical) standard."""

    KINDS: ClassVar[FrozenSet[str]] = frozenset(
        {"regulation", "directive", "treaty", "decision", "standard"}
    )

    id: str
    kind: str = "regulation"
    name: str = ""

    dimension: ClassVar[Dimension] = Dimension.CAUSAL

    def __post_init__(self) -> None:
        _check_kind(self.kind, self.KINDS, "Instrument")


@dataclass(frozen=True)
class Body:
    """An institution with a mandate — regulator, court, or other authority."""

    KINDS: ClassVar[FrozenSet[str]] = frozenset({"regulator", "court", "authority"})

    id: str
    kind: str = "authority"
    name: str = ""

    dimension: ClassVar[Dimension] = Dimension.INTENTIONAL

    def __post_init__(self) -> None:
        _check_kind(self.kind, self.KINDS, "Body")
