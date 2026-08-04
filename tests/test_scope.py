# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Scope / applicability: reach by composition on the REAL solver
``RelationAlgebra`` — GDPR Art 3(1) establishment, Art 3(2) targeting, and
contested reach escalating (never guessed)."""
from __future__ import annotations

import pytest

from loomground_legal import GOVERNING, ScopeResult, scope_applies


# ── GDPR Art 3(1): establishment ─────────────────────────────────────────────

def test_art_3_1_establishment_reaches():
    # ACME —incorporated_in→ DE —member_of→ EU  ⇒  subject_to the EU order.
    r = scope_applies(["incorporated_in", "member_of"])
    assert isinstance(r, ScopeResult)
    assert r.applies is True
    assert r.basis == "subject_to"
    assert r.basis in GOVERNING
    assert r.escalated is False
    assert r.axis == "territorial"
    assert r.chain == ("incorporated_in", "member_of")


def test_art_3_1_variants_all_reach():
    for ground in ("established_in", "resident_in"):
        r = scope_applies([ground, "member_of"])
        assert r.applies is True and r.basis == "subject_to", ground
        assert r.axis == "territorial"


# ── GDPR Art 3(2): targeting (extraterritorial, conduct-based) ───────────────

def test_art_3_2_targeting_reaches():
    # US Corp —targets→ DE market —member_of→ EU  ⇒  subject_to.
    r = scope_applies(["targets", "member_of"])
    assert r.applies is True
    assert r.basis == "subject_to"
    assert r.escalated is False
    assert r.axis == "material"


def test_reach_climbs_to_bound_by():
    r = scope_applies(["incorporated_in", "member_of", "bound_by"])
    assert r.applies is True
    assert r.basis == "bound_by"


# ── contested reach escalates — never a guessed yes/no ───────────────────────

def test_contested_reach_escalates():
    # Incorporation + mere treaty party: contested in the composition table.
    r = scope_applies(["incorporated_in", "party_to"])
    assert r.applies is None
    assert r.escalated is True
    assert r.basis == ""


def test_escalation_mid_chain_keeps_the_question_open():
    r = scope_applies(["controls", "incorporated_in", "member_of"])
    assert r.applies is None
    assert r.escalated is True


# ── non-reach and the temporal axis ──────────────────────────────────────────

def test_chain_composing_to_nothing_does_not_apply():
    # agent_of ∘ member_of is absent from the table: nothing follows.
    r = scope_applies(["agent_of", "member_of"])
    assert r.applies is False
    assert r.escalated is False
    assert r.basis == ""


def test_non_governing_result_does_not_apply():
    # member_of ∘ member_of ⇒ member_of — a real relation, but not governing.
    r = scope_applies(["member_of", "member_of"])
    assert r.applies is False
    assert r.basis == "member_of"
    assert r.basis not in GOVERNING


def test_out_of_force_instrument_reaches_nobody():
    r = scope_applies(["incorporated_in", "member_of"], in_force=False)
    assert r.applies is False
    assert r.axis == "temporal"
    assert r.chain == ()


# ── fail-closed ──────────────────────────────────────────────────────────────

def test_unknown_relation_is_an_error():
    with pytest.raises(ValueError):
        scope_applies(["incorporated_in", "vibes_with"])


def test_empty_chain_is_an_error():
    with pytest.raises(ValueError):
        scope_applies([])
