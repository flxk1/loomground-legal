# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The legal-effect → deontic bridge: O/P/F mapping, Hohfeld incident forms,
and the load-bearing rule that a statutory "right" is NEVER an "R" operator —
all against the REAL deontic vocabulary (no stubs).
"""
from __future__ import annotations

import pytest

from deontic import (
    OP_OBLIGATION,
    OP_PERMISSION,
    OP_PROHIBITION,
    VALID_OPERATORS,
    correlative,
)

from loomground_legal import LegalEffect, OPERATIVE_CONTENT, legal_effect


# ── the three modals ──────────────────────────────────────────────────────────

def test_duty_maps_to_obligation():
    eff = legal_effect("duty")
    assert eff.operator == OP_OBLIGATION == "O"
    assert eff.incident == "duty"
    assert eff.correlative_incident == correlative("duty") == "claim"


def test_permission_and_liberty_map_to_permission():
    for content in ("permission", "liberty"):
        eff = legal_effect(content)
        assert eff.operator == OP_PERMISSION == "P"
        assert eff.incident == "privilege"
        assert eff.correlative_incident == correlative("privilege") == "no-right"


def test_prohibition_maps_to_prohibition():
    eff = legal_effect("prohibition")
    assert eff.operator == OP_PROHIBITION == "F"
    # a prohibition places a duty not to act on the addressee
    assert eff.incident == "duty"
    assert eff.correlative_incident == "claim"


# ── the key rule: a "right" is NEVER an "R" operator ─────────────────────────

def test_r_is_not_in_the_deontic_operator_vocabulary():
    assert "R" not in VALID_OPERATORS
    assert set(VALID_OPERATORS) == {"O", "P", "F"}


def test_right_defaults_to_permission_liberty_reading():
    eff = legal_effect("right")
    assert eff.operator != "R"
    assert eff.operator == OP_PERMISSION
    assert eff.incident == "privilege"


def test_right_as_claim_right_uses_correlative_not_an_operator():
    eff = legal_effect("right", claim_right=True)
    assert eff.operator is None            # no modal minted for the holder
    assert eff.incident == "claim"
    # the counterparty's duty comes from deontic's correlative, not a new "R"
    assert eff.correlative_incident == correlative("claim") == "duty"


def test_right_never_yields_an_r_operator_either_way():
    for claim_right in (False, True):
        eff = legal_effect("right", claim_right=claim_right)
        assert eff.operator != "R"
        assert eff.operator in (OP_PERMISSION, None)
        assert eff.operator is None or eff.operator in VALID_OPERATORS


def test_legal_effect_refuses_to_carry_a_non_deontic_operator():
    with pytest.raises(ValueError, match="never an operator"):
        LegalEffect(content="right", operator="R", incident="claim",
                    correlative_incident="duty")


# ── power / immunity → Hohfeld incidents ─────────────────────────────────────

def test_power_maps_to_power_incident():
    eff = legal_effect("power")
    assert eff.operator is None
    assert eff.incident == "power"
    assert eff.correlative_incident == correlative("power") == "liability"


def test_immunity_maps_to_immunity_incident():
    eff = legal_effect("immunity")
    assert eff.operator is None
    assert eff.incident == "immunity"
    assert eff.correlative_incident == correlative("immunity") == "disability"


# ── definition / establishment / conferral-of-right ──────────────────────────

def test_definition_and_establishment_carry_no_deontic_content():
    for content in ("definition", "establishment"):
        eff = legal_effect(content)
        assert eff.operator is None
        assert eff.incident == ""
        assert eff.correlative_incident == ""


def test_conferral_of_right_is_the_claim_right_incident_form():
    eff = legal_effect("conferral-of-right")
    assert eff.operator is None
    assert eff.incident == "claim"
    assert eff.correlative_incident == "duty"


# ── fail-closed surface ───────────────────────────────────────────────────────

def test_unknown_content_raises():
    with pytest.raises(ValueError, match="unknown operative content"):
        legal_effect("vibe")


def test_operative_content_vocabulary_is_closed():
    assert "right" in OPERATIVE_CONTENT
    for content in OPERATIVE_CONTENT:
        eff = legal_effect(content)
        assert eff.operator is None or eff.operator in VALID_OPERATORS
