# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The legal connection algebra: LC-1..LC-5 ported from host's
``legal_connection.ALGEBRA_LAWS`` as concrete assertions over the packaged
data, running on the REAL ``loomground_solver.RelationAlgebra`` mechanism.
"""
from __future__ import annotations

from loomground_solver import ESCALATE, Dimension, RelationAlgebra

from loomground_legal import GOVERNING, connection_algebra, is_connection, load_connections


def test_builds_a_real_solver_relation_algebra():
    alg = connection_algebra()
    assert isinstance(alg, RelationAlgebra)
    assert alg is connection_algebra()  # cached singleton


# ── LC-1: composition is partial — Connection | ESCALATE | None ──────────────

def test_lc1_partial_composition_three_outcomes():
    alg = connection_algebra()
    assert alg.compose("member_of", "member_of") == "member_of"     # a relation
    assert alg.compose("incorporated_in", "party_to") is ESCALATE   # contested
    assert alg.compose("subject_to", "has_primacy_over") is None    # explicit None
    assert alg.compose("agent_of", "member_of") is None             # absent pair
    assert alg.compose("recognises", "not_a_relation") is None      # lenient lookup
    assert not is_connection("not_a_relation")


# ── LC-2: establishment + membership ⇒ subject_to (Art 3(1) GDPR logic) ──────

def test_lc2_incorporation_plus_membership_yields_subject_to():
    alg = connection_algebra()
    assert alg.compose("incorporated_in", "member_of") == "subject_to"
    for ground in ("established_in", "resident_in", "national_of", "targets"):
        assert alg.compose(ground, "member_of") == "subject_to", ground


def test_lc2_climb_to_bound_by():
    # company —incorporated_in→ DE —member_of→ EU —bound_by→ GDPR order:
    # subject_to the EU, then bound_by what binds the EU. No escalation.
    alg = connection_algebra()
    result, escalated = alg.compose_path(["incorporated_in", "member_of", "bound_by"])
    assert result == "bound_by"
    assert escalated is False
    assert result in GOVERNING


# ── LC-3: mere party_to a treaty does not reach a private party ──────────────

def test_lc3_party_to_treaty_escalates():
    alg = connection_algebra()
    assert alg.compose("incorporated_in", "party_to") is ESCALATE
    assert alg.compose("established_in", "party_to") is ESCALATE
    assert alg.compose("subject_to", "party_to") is ESCALATE
    result, escalated = alg.compose_path(["incorporated_in", "party_to"])
    assert result is ESCALATE
    assert escalated is True


# ── LC-4: corporate-group reach is contested — never auto-attributed ─────────

def test_lc4_group_reach_escalates():
    alg = connection_algebra()
    assert alg.compose("controls", "subject_to") is ESCALATE
    assert alg.compose("controls", "incorporated_in") is ESCALATE
    assert alg.compose("parent_of", "subject_to") is ESCALATE
    assert alg.compose("parent_of", "incorporated_in") is ESCALATE


# ── LC-5: recognition / adequacy / renvoi are not transitive ─────────────────

def test_lc5_recognition_chains_escalate():
    alg = connection_algebra()
    assert alg.compose("recognises", "recognises") is ESCALATE
    assert alg.compose("equivalent_to", "equivalent_to") is ESCALATE
    assert alg.compose("refers_to", "refers_to") is ESCALATE


# ── transitivity + inverses ───────────────────────────────────────────────────

def test_transitive_relations_fold():
    alg = connection_algebra()
    assert alg.compose_path(["member_of", "member_of", "member_of"]) == ("member_of", False)
    assert alg.compose_path(["controls", "controls"]) == ("controls", False)
    assert alg.compose_path(["parent_of", "parent_of"]) == ("parent_of", False)


def test_inverses():
    alg = connection_algebra()
    assert alg.inverse("parent_of") == "subsidiary_of"
    assert alg.inverse("subsidiary_of") == "parent_of"
    assert alg.inverse("controller_of") == "processor_for"
    assert alg.inverse("processor_for") == "controller_of"
    assert alg.inverse("equivalent_to") == "equivalent_to"   # symmetric
    assert alg.inverse("member_of") is None                  # no clean dual


# ── the JSON round-trips host's legal_connection faithfully ───────────────────

# Every entry of legal_connection._COMPOSE (host @ workspaces/legal_connection.py),
# as (a, b) -> "ESCALATE" | None | relation-name. 25 entries.
_EXPECTED_COMPOSE = {
    ("incorporated_in", "member_of"): "subject_to",
    ("established_in", "member_of"): "subject_to",
    ("resident_in", "member_of"): "subject_to",
    ("national_of", "member_of"): "subject_to",
    ("targets", "member_of"): "subject_to",
    ("subject_to", "member_of"): "subject_to",
    ("subject_to", "has_primacy_over"): None,
    ("subject_to", "bound_by"): "bound_by",
    ("member_of", "bound_by"): "bound_by",
    ("party_to", "bound_by"): "bound_by",
    ("member_of", "member_of"): "member_of",
    ("member_of", "has_primacy_over"): None,
    ("has_primacy_over", "has_primacy_over"): "has_primacy_over",
    ("incorporated_in", "party_to"): "ESCALATE",
    ("established_in", "party_to"): "ESCALATE",
    ("subject_to", "party_to"): "ESCALATE",
    ("controls", "incorporated_in"): "ESCALATE",
    ("controls", "subject_to"): "ESCALATE",
    ("parent_of", "subject_to"): "ESCALATE",
    ("parent_of", "incorporated_in"): "ESCALATE",
    ("controls", "controls"): "controls",
    ("parent_of", "parent_of"): "parent_of",
    ("recognises", "recognises"): "ESCALATE",
    ("equivalent_to", "equivalent_to"): "ESCALATE",
    ("refers_to", "refers_to"): "ESCALATE",
}

_EXPECTED_VOCABULARY = {
    # jurisdiction ↔ jurisdiction
    "member_of", "has_primacy_over", "party_to", "bound_by", "recognises",
    "equivalent_to", "refers_to", "candidate_of", "reserves_against",
    # person ↔ jurisdiction
    "incorporated_in", "established_in", "resident_in", "national_of",
    "targets", "subject_to",
    # person ↔ person
    "controls", "parent_of", "subsidiary_of", "agent_of", "party_to_contract",
    "controller_of", "processor_for",
    # corpus / catalogue edges
    "enforces", "supervises", "applies_in", "established_by", "adopted_by",
    "supersedes", "descends_from", "presumes_conformity", "decides",
}


def test_json_round_trips_every_compose_entry():
    data = load_connections()
    in_json = {(row["a"], row["b"]): row["result"] for row in data["compose"]}
    assert in_json == _EXPECTED_COMPOSE
    assert len(data["compose"]) == len(_EXPECTED_COMPOSE) == 25

    # and the built algebra agrees, with the sentinel/None mapping applied
    alg = connection_algebra()
    for (a, b), expected in _EXPECTED_COMPOSE.items():
        got = alg.compose(a, b)
        if expected == "ESCALATE":
            assert got is ESCALATE, (a, b)
        else:
            assert got == expected, (a, b)


def test_vocabulary_matches_the_connection_enum():
    data = load_connections()
    assert set(data["vocabulary"]) == _EXPECTED_VOCABULARY
    assert len(data["vocabulary"]) == 31
    alg = connection_algebra()
    assert alg.vocabulary == frozenset(_EXPECTED_VOCABULARY)


def test_dimension_projection():
    alg = connection_algebra()
    data = load_connections()
    # every relation carries an explicit dimension in the artifact
    assert set(data["dimensions"]) == _EXPECTED_VOCABULARY
    # spot-check the projection against legal_connection._DIMENSION
    assert alg.dimension("member_of") is Dimension.STRUCTURAL
    assert alg.dimension("subject_to") is Dimension.CAUSAL
    assert alg.dimension("recognises") is Dimension.RELATIONAL
    assert alg.dimension("reserves_against") is Dimension.INTENTIONAL
    assert alg.dimension("candidate_of") is Dimension.TEMPORAL
    assert alg.dimension("supersedes") is Dimension.TEMPORAL
    assert alg.dimension("enforces") is Dimension.INTENTIONAL
    assert alg.dimension("decides") is Dimension.CAUSAL
    # unknown relations fall back to the RELATIONAL floor
    assert alg.dimension("not_a_relation") is Dimension.RELATIONAL


def test_governing_relations():
    assert GOVERNING == frozenset({"subject_to", "bound_by"})
