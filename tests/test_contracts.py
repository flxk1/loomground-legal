# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The contract-instance model — PartyRef (ISO 17442 LEI checksum) and
ContractInstance (typed temporal bindings), lifted verbatim from RVND
contracts/instance. The ContractRegistry (folder JSONL + audit) stays in RVND."""
from __future__ import annotations

import pytest

from loomground_solver.temporal import Date, Money, Term

from loomground_legal import ContractError, ContractInstance, PartyRef


# ── PartyRef: role slug + ISO 17442 LEI checksum ──────────────────────────────

def test_partyref_valid_lei_checksum():
    p = PartyRef(entity_code="acme", role="controller", name="ACME GmbH",
                 lei="5493001KJTIIGC8Y1R12")
    assert p.lei == "5493001KJTIIGC8Y1R12"
    assert p.entity_kind == "legal_person"


def test_partyref_rejects_bad_lei_checksum():
    # well-formed (20 chars, matches the regex) but fails the mod-97-10 checksum
    with pytest.raises(ContractError):
        PartyRef(entity_code="acme", role="controller", lei="5493001KJTIIGC8Y1R13")


def test_partyref_rejects_malformed_lei_and_bad_role_and_kind():
    with pytest.raises(ContractError):
        PartyRef(entity_code="acme", role="controller", lei="TOO-SHORT")
    with pytest.raises(ContractError):
        PartyRef(entity_code="acme", role="Controller")          # not a lowercase slug
    with pytest.raises(ContractError):
        PartyRef(entity_code="acme", role="controller", entity_kind="instrument")
    with pytest.raises(ContractError):
        PartyRef(entity_code="", role="controller")              # empty code


def test_partyref_roundtrip():
    p = PartyRef(entity_code="acme", role="processor", lei="7LTWFZYICNSX8D621K86")
    assert PartyRef.from_dict(p.to_dict()) == p


# ── ContractInstance: identity, typed bindings, supersession ──────────────────

def test_contract_instance_construction_and_defaults():
    c = ContractInstance(contract_id="dpa-2026")
    assert c.version == 1
    assert c.ref == "dpa-2026@1"
    # cold-start: everything optional is honestly "not extracted"
    assert set(c.missing_fields()) == {
        "parties", "effective_date", "term", "governing_law",
        "contract_type", "language"}


def test_contract_instance_typed_temporal_bindings():
    c = ContractInstance(
        contract_id="msa-1", contract_type="msa",
        parties=(PartyRef(entity_code="acme", role="customer"),),
        effective_date=Date("2026-01-01"),
        term=Term.from_dict({"kind": "fixed", "start": "2026-01-01", "duration": "P1Y"}),
        governing_law="DE", language="en",
        total_value=Money.from_dict({"amount": "1000.00", "currency": "EUR"}))
    assert c.governing_law == "DE"
    assert c.party_by_role("customer")[0].entity_code == "acme"
    # effective_date is available as a resolvable event
    assert "effective_date" in c.event_dates()
    assert c.missing_fields() == []


def test_contract_instance_rejects_untyped_dates():
    with pytest.raises(ContractError):
        ContractInstance(contract_id="x", effective_date="2026-01-01")   # str, not Date
    with pytest.raises(ContractError):
        ContractInstance(contract_id="x", term="P1Y")                     # str, not Term


def test_contract_id_and_version_validation():
    with pytest.raises(ContractError):
        ContractInstance(contract_id="Not A Slug")
    with pytest.raises(ContractError):
        ContractInstance(contract_id="ok", version=0)


def test_supersedes_format_and_self_supersession():
    # valid: a later version supersedes an earlier one of itself
    c = ContractInstance(contract_id="dpa", version=2, supersedes="dpa@1")
    assert c.supersedes == "dpa@1"
    # malformed supersedes ref
    with pytest.raises(ContractError):
        ContractInstance(contract_id="dpa", version=2, supersedes="dpa-v1")
    # a version cannot supersede itself or a later version of itself
    with pytest.raises(ContractError):
        ContractInstance(contract_id="dpa", version=2, supersedes="dpa@2")


def test_contract_instance_roundtrip():
    c = ContractInstance(
        contract_id="dpa-2026", version=3, title="Data Processing Agreement",
        contract_type="dpa",
        parties=(PartyRef(entity_code="acme", role="controller"),
                 PartyRef(entity_code="proc", role="processor")),
        effective_date=Date("2026-05-25"), governing_law="EU",
        supersedes="dpa-2026@2", document_hash="sha256:abc", language="en")
    back = ContractInstance.from_dict(c.to_dict())
    assert back == c
    assert back.ref == "dpa-2026@3"
