# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The world map — the graph of legal entities the connection algebra runs over.

Jurisdictions/orders, the instruments that carry the law, the regulators and
standards bodies around them, and (at query time) the legal persons the law
reaches — held as a :class:`WorldMap` graph whose edges are the legal
connection relations of :mod:`loomground_legal.connection`. Each entity carries
a canonical retrievable URL: the map is a *corpus of pointers* to real laws and
organisations, not an abstract graph. The seed (:func:`seed_world`) is real and
cited, lifted verbatim from ``artifacts/world_seed.json``; it is a starting
corpus meant to grow.

**One taxonomy, no schism.** :class:`EntityKind` is the single concrete node
vocabulary (10 kinds); :mod:`loomground_legal.entities` supplies the four
abstract, *dimension-carrying* families (:class:`~loomground_legal.entities.Jurisdiction`,
:class:`~loomground_legal.entities.LegalPerson`,
:class:`~loomground_legal.entities.Instrument`,
:class:`~loomground_legal.entities.Body`). Every concrete kind belongs to
exactly one family and *inherits that family's 5D dimension* — see
:data:`KIND_TO_FAMILY` and :attr:`EntityKind.dimension`. There is no second,
contradictory kind system: the families are the abstract layer, the kinds their
concrete refinements.

**Reach composes; it does not fold.** :meth:`WorldMap.reach` walks the graph
building connection chains, but every applicability question is answered by
:func:`loomground_legal.scope.scope_applies` — which folds the chain through the
solver's :class:`~loomground_solver.RelationAlgebra` (``compose_path``). No
composition, no GOVERNING check, and no left-fold live here: the package keeps
the same no-parallel-mechanism discipline RVND does. ``reach`` is graph walking
plus provenance bookkeeping; the algebra is the solver's, whole and entire.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from importlib import resources
from typing import Dict, FrozenSet, List, Optional, Type

from loomground_solver import Dimension

from .entities import Body, Instrument, Jurisdiction, LegalPerson
from .scope import scope_applies

__all__ = [
    "EntityKind",
    "KIND_TO_FAMILY",
    "JURISDICTION_KINDS",
    "Entity",
    "WorldEdge",
    "GovEntry",
    "ReachResult",
    "WorldMap",
    "seed_world",
    "load_world_seed",
]

#: Any of the four dimension-carrying entity families in
#: :mod:`loomground_legal.entities`.
EntityFamily = Type


class EntityKind(Enum):
    """The concrete node vocabulary of the world map (10 kinds).

    This is the single kind taxonomy. Each member maps, via
    :data:`KIND_TO_FAMILY`, onto exactly one of the four abstract
    dimension-carrying families in :mod:`loomground_legal.entities`, and
    :attr:`dimension` is that family's dimension — so a world-map node still
    projects one-to-one into the 5D knowledge graph, with no competing kind
    system.
    """

    # jurisdictions / legal orders  → entities.Jurisdiction (STRUCTURAL)
    STATE = "state"
    SUPRANATIONAL = "supranational"
    INTERNATIONAL_REGIME = "international_regime"
    # corpus organisations  → entities.Body (INTENTIONAL)
    REGULATOR = "regulator"
    STANDARDS_BODY = "standards_body"
    # corpus instruments (the laws)  → entities.Instrument (CAUSAL)
    INSTRUMENT = "instrument"
    # private instruments (contracts)  → entities.Instrument (CAUSAL)
    CONTRACT = "contract"
    # legal persons (usually added at query time)  → entities.LegalPerson (RELATIONAL)
    LEGAL_PERSON = "legal_person"
    NATURAL_PERSON = "natural_person"
    # a public authority as a party  → entities.Body (INTENTIONAL)
    PUBLIC_BODY = "public_body"

    @property
    def family(self) -> EntityFamily:
        """The abstract dimension-carrying family this concrete kind refines."""
        return KIND_TO_FAMILY[self]

    @property
    def dimension(self) -> Dimension:
        """The 5D dimension of this kind — inherited from its family, so the
        concrete and abstract taxonomies never disagree."""
        return self.family.dimension


#: The unification: each concrete :class:`EntityKind` → the abstract
#: dimension-carrying family it refines (from :mod:`loomground_legal.entities`).
#: The families own the 5D dimension; the kinds inherit it. One taxonomy.
KIND_TO_FAMILY: Dict[EntityKind, EntityFamily] = {
    EntityKind.STATE: Jurisdiction,
    EntityKind.SUPRANATIONAL: Jurisdiction,
    EntityKind.INTERNATIONAL_REGIME: Jurisdiction,
    EntityKind.REGULATOR: Body,
    EntityKind.STANDARDS_BODY: Body,
    EntityKind.PUBLIC_BODY: Body,
    EntityKind.INSTRUMENT: Instrument,
    EntityKind.CONTRACT: Instrument,
    EntityKind.LEGAL_PERSON: LegalPerson,
    EntityKind.NATURAL_PERSON: LegalPerson,
}

#: Kinds whose family is :class:`~loomground_legal.entities.Jurisdiction` — the
#: legal orders a reach chain can terminate on.
JURISDICTION_KINDS: FrozenSet[EntityKind] = frozenset(
    k for k, fam in KIND_TO_FAMILY.items() if fam is Jurisdiction
)


@dataclass
class Entity:
    """A node on the world map — a jurisdiction, instrument, body, or person.

    ``code`` is a unique slug (an ISO code for states, a slug otherwise);
    ``url`` is the canonical retrievable pointer that makes the map a corpus.
    """

    code: str
    name: str
    kind: EntityKind
    url: Optional[str] = None
    jurisdiction: Optional[str] = None  # owning legal order (e.g. "EU", "DE")
    domains: tuple = ()  # data/platform/ai/cyber/digital-markets/…
    region: str = ""
    source: str = "seed"  # provenance: seed | user | ingest
    facets: dict = field(default_factory=dict)

    @property
    def dimension(self) -> Dimension:
        """The 5D dimension of this node — its kind's family dimension."""
        return self.kind.dimension

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "kind": self.kind.value,
            "url": self.url,
            "jurisdiction": self.jurisdiction,
            "domains": list(self.domains),
            "region": self.region,
            "source": self.source,
            "facets": self.facets,
        }


@dataclass
class WorldEdge:
    """A directed connection edge between two entities.

    ``connection`` is a legal connection relation name (the vocabulary of
    :mod:`loomground_legal.connection`); the composition of a chain of these is
    the solver algebra's business, never this edge's.
    """

    subject: str  # entity code
    connection: str  # legal connection relation name
    object: str  # entity code
    basis: str = ""  # the legal instrument / agreement behind the edge
    url: str = ""  # source for the relation
    source: str = "seed"

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "connection": self.connection,
            "object": self.object,
            "basis": self.basis,
            "url": self.url,
            "source": self.source,
        }


@dataclass
class GovEntry:
    """One legal order that governs (or contestedly might govern) the person."""

    jurisdiction: str
    relation: str  # subject_to | bound_by | escalate
    escalated: bool
    via: List[dict]  # provenance edges (walking order)
    instruments: List[dict]  # laws applying in that jurisdiction (with URLs)


@dataclass
class ReachResult:
    """The answer to :meth:`WorldMap.reach` — the orders governing a person."""

    person: str
    governed_by: List[GovEntry]

    def to_dict(self) -> dict:
        return {
            "person": self.person,
            "governed_by": [
                {
                    "jurisdiction": g.jurisdiction,
                    "relation": g.relation,
                    "escalated": g.escalated,
                    "via": g.via,
                    "instruments": g.instruments,
                }
                for g in self.governed_by
            ],
        }


class WorldMap:
    """A graph of :class:`Entity` nodes joined by :class:`WorldEdge` relations."""

    def __init__(self) -> None:
        self.entities: Dict[str, Entity] = {}
        self.edges: List[WorldEdge] = []
        self._adj: Dict[str, List[WorldEdge]] = {}

    # ── construction ──────────────────────────────────────────────────────
    def add(self, e: Entity) -> Entity:
        self.entities[e.code] = e
        return e

    def connect(
        self,
        subject: str,
        connection: str,
        obj: str,
        *,
        basis: str = "",
        url: str = "",
        source: str = "seed",
    ) -> WorldEdge:
        edge = WorldEdge(subject, connection, obj, basis=basis, url=url, source=source)
        self.edges.append(edge)
        self._adj.setdefault(subject, []).append(edge)
        return edge

    # ── queries ───────────────────────────────────────────────────────────
    def get(self, code: str) -> Optional[Entity]:
        return self.entities.get(code)

    def neighbours(self, code: str) -> List[WorldEdge]:
        return list(self._adj.get(code, ()))

    def search(
        self,
        *,
        kind: Optional[EntityKind] = None,
        domain: Optional[str] = None,
        jurisdiction: Optional[str] = None,
    ) -> List[Entity]:
        out = []
        for e in self.entities.values():
            if kind is not None and e.kind is not kind:
                continue
            if domain is not None and domain not in e.domains:
                continue
            if jurisdiction is not None and e.jurisdiction != jurisdiction:
                continue
            out.append(e)
        return out

    def instruments_in(self, jurisdiction: str) -> List[Entity]:
        """Instruments that ``applies_in`` the given jurisdiction (the
        governing-law set)."""
        out = []
        for ed in self.edges:
            if ed.connection == "applies_in" and ed.object == jurisdiction:
                inst = self.entities.get(ed.subject)
                if inst is not None:
                    out.append(inst)
        return out

    def urls(self) -> List[dict]:
        """The retrievable corpus: every entity that carries a URL."""
        return [
            {
                "code": e.code,
                "kind": e.kind.value,
                "name": e.name,
                "url": e.url,
                "domains": list(e.domains),
            }
            for e in self.entities.values()
            if e.url
        ]

    # ── reach: which law governs a person ──────────────────────────────────
    def reach(self, person: str, *, max_depth: int = 6) -> ReachResult:
        """Which legal orders govern ``person`` — and the instruments that apply
        there — climbing the connection ladder from the person up.

        The graph is walked here; every reach *decision* is delegated to
        :func:`loomground_legal.scope.scope_applies`, which composes the chain
        through the solver's :class:`~loomground_solver.RelationAlgebra`. This
        method holds no composition table, no ``GOVERNING`` test, and no fold:
        an order is recorded when ``scope_applies`` says the chain governs
        (``applies is True``) or leaves reach legally contested
        (``escalated``) — the escalate-don't-guess discipline, owned upstream.
        """
        found: Dict[str, GovEntry] = {}

        def walk(
            node: str,
            chain: List[str],
            path: List[WorldEdge],
            visited: FrozenSet[str],
        ) -> None:
            if len(path) >= max_depth:
                return
            for ed in self._adj.get(node, ()):
                if ed.object in visited:
                    continue
                new_chain = chain + [ed.connection]
                new_path = path + [ed]
                target = self.entities.get(ed.object)
                if target is not None and target.kind in JURISDICTION_KINDS:
                    # Composition is entirely scope_applies' (→ the solver
                    # algebra's compose_path). No local fold.
                    res = scope_applies(new_chain)
                    if res.applies is True or res.escalated:
                        rel = res.basis if res.applies is True else "escalate"
                        prev = found.get(ed.object)
                        # keep the shortest clean path; prefer non-escalated
                        if prev is None or (prev.escalated and not res.escalated):
                            found[ed.object] = GovEntry(
                                jurisdiction=ed.object,
                                relation=rel,
                                escalated=bool(res.escalated),
                                via=[e.to_dict() for e in new_path],
                                instruments=[
                                    {
                                        "code": i.code,
                                        "name": i.name,
                                        "url": i.url,
                                        "domains": list(i.domains),
                                    }
                                    for i in self.instruments_in(ed.object)
                                ],
                            )
                walk(ed.object, new_chain, new_path, visited | {ed.object})

        walk(person, [], [], frozenset({person}))
        return ReachResult(
            person=person,
            governed_by=sorted(
                found.values(), key=lambda g: (g.escalated, g.jurisdiction)
            ),
        )


# ── the seed corpus ────────────────────────────────────────────────────────

def load_world_seed() -> dict:
    """The raw ``world_seed.json`` payload (parsed, untranslated)."""
    ref = resources.files("loomground_legal").joinpath("artifacts/world_seed.json")
    return json.loads(ref.read_text(encoding="utf-8"))


def seed_world() -> WorldMap:
    """Build the seed :class:`WorldMap` from packaged ``world_seed.json`` data.

    A real, citable starting corpus of the digital-law stack (EU + members, the
    EU digital acquis with ELI URLs, Council-of-Europe/OECD, the regulators and
    standards bodies), marked ``seed`` and meant to grow. The DATA is lifted
    verbatim from RVND ``legal_world.seed_world`` — this loader only rebuilds the
    graph from it.
    """
    data = load_world_seed()
    w = WorldMap()
    for row in data["entities"]:
        w.add(
            Entity(
                code=row["code"],
                name=row["name"],
                kind=EntityKind(row["kind"]),
                url=row.get("url"),
                jurisdiction=row.get("jurisdiction"),
                domains=tuple(row.get("domains", ())),
                region=row.get("region", ""),
                source=row.get("source", "seed"),
                facets=dict(row.get("facets", {})),
            )
        )
    for row in data["edges"]:
        w.connect(
            row["subject"],
            row["connection"],
            row["object"],
            basis=row.get("basis", ""),
            url=row.get("url", ""),
            source=row.get("source", "seed"),
        )
    return w
