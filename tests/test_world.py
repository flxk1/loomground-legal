# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The world map — graph container, the unified EntityKind taxonomy, the seed
corpus (with its ELI URLs intact), and multi-hop reach() that composes through
the solver algebra (via scope_applies) rather than a local fold."""
from __future__ import annotations

import ast
import inspect
import textwrap

from loomground_solver import Dimension

import loomground_legal.world as world_mod
from loomground_legal import (
    Body,
    Entity,
    EntityKind,
    Instrument,
    Jurisdiction,
    JURISDICTION_KINDS,
    KIND_TO_FAMILY,
    LegalPerson,
    ReachResult,
    WorldEdge,
    WorldMap,
    seed_world,
)


# ── graph container: add / connect / search / neighbours ─────────────────────

def test_add_and_get():
    w = WorldMap()
    e = w.add(Entity("acme", "ACME GmbH", EntityKind.LEGAL_PERSON, jurisdiction="DE"))
    assert w.get("acme") is e
    assert w.get("missing") is None


def test_connect_and_neighbours():
    w = WorldMap()
    w.add(Entity("acme", "ACME", EntityKind.LEGAL_PERSON))
    w.add(Entity("DE", "Germany", EntityKind.STATE))
    edge = w.connect("acme", "incorporated_in", "DE", basis="HRB")
    assert isinstance(edge, WorldEdge)
    ns = w.neighbours("acme")
    assert [e.object for e in ns] == ["DE"]
    assert w.neighbours("DE") == []  # no outgoing edges


def test_search_by_kind_domain_jurisdiction():
    w = WorldMap()
    w.add(Entity("gdpr", "GDPR", EntityKind.INSTRUMENT, jurisdiction="EU", domains=("data",)))
    w.add(Entity("ai-act", "AI Act", EntityKind.INSTRUMENT, jurisdiction="EU", domains=("ai",)))
    w.add(Entity("DE", "Germany", EntityKind.STATE, jurisdiction="EU"))
    assert {e.code for e in w.search(kind=EntityKind.INSTRUMENT)} == {"gdpr", "ai-act"}
    assert [e.code for e in w.search(domain="data")] == ["gdpr"]
    assert {e.code for e in w.search(jurisdiction="EU")} == {"gdpr", "ai-act", "DE"}


def test_instruments_in_and_urls():
    w = WorldMap()
    w.add(Entity("EU", "European Union", EntityKind.SUPRANATIONAL, url="https://eu"))
    w.add(Entity("gdpr", "GDPR", EntityKind.INSTRUMENT, url="https://gdpr", domains=("data",)))
    w.add(Entity("DE", "Germany", EntityKind.STATE))  # no url
    w.connect("gdpr", "applies_in", "EU")
    assert [e.code for e in w.instruments_in("EU")] == ["gdpr"]
    assert w.instruments_in("DE") == []
    codes_with_url = {row["code"] for row in w.urls()}
    assert codes_with_url == {"EU", "gdpr"}  # DE carries no URL → not in corpus


# ── EntityKind unification: one taxonomy, kinds inherit family dimension ──────

def test_entitykind_maps_onto_the_four_families():
    # every concrete kind belongs to exactly one abstract dimension-carrying family
    assert set(KIND_TO_FAMILY) == set(EntityKind)
    assert set(KIND_TO_FAMILY.values()) == {Jurisdiction, LegalPerson, Instrument, Body}


def test_kind_dimension_is_inherited_from_family():
    # the concrete and abstract taxonomies never disagree on the 5D dimension
    for kind, family in KIND_TO_FAMILY.items():
        assert kind.dimension == family.dimension
        assert kind.family is family
    # spot-check the four expected dimensions
    assert EntityKind.STATE.dimension is Dimension.STRUCTURAL
    assert EntityKind.SUPRANATIONAL.dimension is Dimension.STRUCTURAL
    assert EntityKind.LEGAL_PERSON.dimension is Dimension.RELATIONAL
    assert EntityKind.INSTRUMENT.dimension is Dimension.CAUSAL
    assert EntityKind.CONTRACT.dimension is Dimension.CAUSAL
    assert EntityKind.REGULATOR.dimension is Dimension.INTENTIONAL
    assert EntityKind.STANDARDS_BODY.dimension is Dimension.INTENTIONAL


def test_jurisdiction_kinds_are_exactly_the_order_kinds():
    assert JURISDICTION_KINDS == frozenset(
        {EntityKind.STATE, EntityKind.SUPRANATIONAL, EntityKind.INTERNATIONAL_REGIME}
    )


def test_entity_projects_to_its_kind_dimension():
    e = Entity("DE", "Germany", EntityKind.STATE)
    assert e.dimension is Dimension.STRUCTURAL
    assert Entity("acme", "ACME", EntityKind.LEGAL_PERSON).dimension is Dimension.RELATIONAL


# ── reach() composes via the solver algebra, not a local fold ────────────────

def test_reach_delegates_composition_to_scope_applies_no_local_fold():
    # Structural guarantee: reach holds no composition table / fold / GOVERNING
    # test — it calls scope_applies, which calls connection_algebra().compose_path.
    # Inspect executable code only — strip the docstring and comment lines so the
    # guarantee is about what reach *does*, not what its prose mentions.
    raw = inspect.getsource(WorldMap.reach)
    tree = ast.parse(textwrap.dedent(raw))
    body = tree.body[0]
    if (
        body.body
        and isinstance(body.body[0], ast.Expr)
        and isinstance(getattr(body.body[0], "value", None), ast.Constant)
        and isinstance(body.body[0].value.value, str)
    ):
        body.body = body.body[1:]  # drop the docstring node
    code = ast.unparse(body)
    assert "scope_applies(" in code
    # no re-implemented fold in reach: it never touches the algebra mechanism
    # directly (that is scope_applies' job), nor re-tests the governing set.
    assert ".compose_path(" not in code
    assert "connection_algebra" not in code
    assert "GOVERNING" not in code  # the governing test lives in scope.py
    # and scope_applies itself is the seam onto the solver algebra
    scope_src = inspect.getsource(world_mod.scope_applies)
    assert "connection_algebra().compose_path(" in scope_src


def _acme_in_de_world() -> WorldMap:
    w = seed_world()
    w.add(Entity("acme", "ACME GmbH", EntityKind.LEGAL_PERSON, jurisdiction="DE"))
    w.connect("acme", "incorporated_in", "DE", basis="HRB 12345")
    return w


def test_reach_de_company_reaches_eu_acquis():
    # ACME —incorporated_in→ DE —member_of→ EU  ⇒  subject_to EU, and the EU
    # digital acquis applies there (gdpr / ai-act / dsa among them).
    w = _acme_in_de_world()
    res = w.reach("acme")
    assert isinstance(res, ReachResult)
    by_juris = {g.jurisdiction: g for g in res.governed_by}
    assert "EU" in by_juris
    eu = by_juris["EU"]
    assert eu.relation == "subject_to"
    assert eu.escalated is False
    instrument_codes = {i["code"] for i in eu.instruments}
    assert {"gdpr", "ai-act", "dsa"} <= instrument_codes


def test_reach_provenance_carries_eli_urls():
    w = _acme_in_de_world()
    eu = {g.jurisdiction: g for g in w.reach("acme").governed_by}["EU"]
    urls = {i["code"]: i["url"] for i in eu.instruments}
    assert urls["gdpr"] == "https://eur-lex.europa.eu/eli/reg/2016/679/oj"
    assert urls["ai-act"] == "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"


def test_reach_corporate_group_chain_escalates():
    # ParentCo —parent_of→ SubCo —incorporated_in→ DE : corporate-group reach is
    # legally contested (LC-4) → the chain composes to ESCALATE, never a guessed yes.
    w = seed_world()
    w.add(Entity("parentco", "Parent Holdings", EntityKind.LEGAL_PERSON))
    w.add(Entity("subco", "Sub GmbH", EntityKind.LEGAL_PERSON, jurisdiction="DE"))
    w.connect("parentco", "parent_of", "subco", basis="100% shareholding")
    w.connect("subco", "incorporated_in", "DE", basis="HRB 67890")
    res = w.reach("parentco")
    de = {g.jurisdiction: g for g in res.governed_by}.get("DE")
    assert de is not None
    assert de.escalated is True
    assert de.relation == "escalate"


def test_reach_unknown_person_is_empty():
    assert seed_world().reach("nobody").governed_by == []


# ── seed_world(): the corpus loads with data + URLs intact ───────────────────

def test_seed_world_entity_and_edge_counts():
    w = seed_world()
    assert len(w.entities) == 39
    assert len(w.edges) == 32


def test_seed_world_eli_urls_intact():
    w = seed_world()
    assert w.get("gdpr").url == "https://eur-lex.europa.eu/eli/reg/2016/679/oj"
    assert w.get("ai-act").url == "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
    assert w.get("dsa").url == "https://eur-lex.europa.eu/eli/reg/2022/2065/oj"
    assert w.get("nis2").url == "https://eur-lex.europa.eu/eli/dir/2022/2555/oj"
    assert (
        w.get("convention-108-plus").url
        == "https://www.coe.int/en/web/data-protection/convention108-and-protocol"
    )


def test_seed_world_structure_spot_checks():
    w = seed_world()
    # EU is a supranational order carrying its portal URL
    eu = w.get("EU")
    assert eu.kind is EntityKind.SUPRANATIONAL and eu.url == "https://european-union.europa.eu"
    # DE is a member state of EU
    assert w.get("DE").kind is EntityKind.STATE and w.get("DE").jurisdiction == "EU"
    assert any(e.object == "EU" and e.connection == "member_of" for e in w.neighbours("DE"))
    # the full EU digital acquis applies in EU (10 seeded instruments applies_in EU)
    assert len(w.instruments_in("EU")) == 10
    # supersession lineage present
    assert any(
        e.object == "dpd-95" and e.connection == "supersedes" for e in w.neighbours("gdpr")
    )
    # standards-body equivalence + harmonised-standards descent
    conns = {(e.connection, e.object) for e in w.neighbours("cen-cenelec")}
    assert ("equivalent_to", "iso") in conns
    assert ("descends_from", "ai-act") in conns


def test_every_seed_edge_uses_a_known_connection_relation():
    from loomground_legal import is_connection

    for e in seed_world().edges:
        assert is_connection(e.connection), e.connection
