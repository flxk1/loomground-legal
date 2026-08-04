# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Typed legal entities: construction, kind validation, and the 5D projection."""
from __future__ import annotations

import pytest

from loomground_solver import Dimension

from loomground_legal import Body, Instrument, Jurisdiction, LegalPerson


def test_construction():
    eu = Jurisdiction(id="jur:eu", name="European Union")
    de = Jurisdiction(id="jur:de", name="Germany")
    acme = LegalPerson(id="per:acme", kind="legal", name="ACME GmbH")
    alex = LegalPerson(id="per:alex", kind="natural")
    gdpr = Instrument(id="ins:gdpr", kind="regulation", name="GDPR")
    edpb = Body(id="bod:edpb", kind="authority", name="EDPB")
    assert eu.id == "jur:eu" and de.name == "Germany"
    assert acme.kind == "legal" and alex.kind == "natural"
    assert gdpr.kind == "regulation" and edpb.kind == "authority"


def test_kind_vocabularies():
    assert LegalPerson.KINDS == frozenset({"natural", "legal"})
    assert Instrument.KINDS == frozenset(
        {"regulation", "directive", "treaty", "decision", "standard"}
    )
    assert Body.KINDS == frozenset({"regulator", "court", "authority"})


def test_invalid_kind_fails_closed():
    with pytest.raises(ValueError, match="LegalPerson.kind"):
        LegalPerson(id="per:x", kind="robot")
    with pytest.raises(ValueError, match="Instrument.kind"):
        Instrument(id="ins:x", kind="memo")
    with pytest.raises(ValueError, match="Body.kind"):
        Body(id="bod:x", kind="club")


def test_5d_dimension_projection():
    assert Jurisdiction.dimension is Dimension.STRUCTURAL
    assert LegalPerson.dimension is Dimension.RELATIONAL
    assert Instrument.dimension is Dimension.CAUSAL
    assert Body.dimension is Dimension.INTENTIONAL
    # instances project too
    assert Jurisdiction(id="jur:eu").dimension is Dimension.STRUCTURAL
    assert Instrument(id="ins:gdpr", kind="regulation").dimension is Dimension.CAUSAL


def test_entities_are_frozen_value_objects():
    eu = Jurisdiction(id="jur:eu", name="European Union")
    assert eu == Jurisdiction(id="jur:eu", name="European Union")
    with pytest.raises(Exception):
        eu.name = "EU"  # type: ignore[misc]
