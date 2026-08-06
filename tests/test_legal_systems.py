# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Legal-system packs + the applicable-law resolver. A jurisdiction selection
closes over its supranational overlays (DE → DE+EU); the resolver lists every
governing source class with its ceiling and incorporation rule, and records the
membership + primacy edges as annotations that ESCALATE — never auto-resolved.
Unknown codes fail closed."""
from __future__ import annotations

import pytest

from loomground_legal import (
    ApplicableLaw,
    Relation,
    SourceClass,
    applicable_law,
    applicable_systems,
)
from loomground_legal import legal_systems as ls


# ── registry access is fail-closed ──────────────────────────────────────────

def test_default_is_de_and_known_codes_resolve() -> None:
    assert ls.DEFAULT == "DE"
    assert ls.get().code == "DE"
    assert {"DE", "EU", "UK", "US"} <= set(ls.available())


def test_unknown_code_raises_not_silent_fallback() -> None:
    with pytest.raises(KeyError):
        ls.get("ZZ")


# ── overlay closure: Germany is in the EU ────────────────────────────────────

def test_de_closes_over_eu() -> None:
    assert applicable_systems("DE") == ["DE", "EU"]


def test_eu_has_no_further_overlay() -> None:
    assert applicable_systems("EU") == ["EU"]


# ── applicable_law: full governing set + escalating primacy edge ─────────────

def test_applicable_law_spans_de_and_eu_sources() -> None:
    al = applicable_law("DE")
    assert isinstance(al, ApplicableLaw)
    assert al.systems == ("DE", "EU")
    origins = {s.origin for s in al.sources}
    assert origins == {"DE", "EU"}


def test_primacy_edge_is_recorded_and_flagged_as_escalating() -> None:
    al = applicable_law("DE")
    outranks = [r for r in al.relations if r.relation is Relation.OUTRANKS]
    assert outranks, "EU primacy edge must be recorded"
    assert outranks[0].subject == "EU" and outranks[0].object == "DE"
    assert "escalates" in outranks[0].note
    member = [r for r in al.relations if r.relation is Relation.MEMBER_OF]
    assert member and member[0].subject == "DE" and member[0].object == "EU"


def test_source_effect_never_exceeds_the_universal_ceiling() -> None:
    # every SourceEntry's effect equals the class ceiling (pack ≤ universal)
    from loomground_legal import max_effect
    for s in applicable_law("DE").sources:
        assert s.effect is max_effect(s.source_class)


def test_in_scope_filter_narrows_the_source_set() -> None:
    only = {SourceClass.SUPRANATIONAL_REGULATION}
    al = applicable_law("DE", in_scope=only)
    assert {s.source_class for s in al.sources} <= only


# ── authority ranking never silently top-ranks an unknown type ───────────────

def test_unknown_source_type_gets_weakest_rank() -> None:
    de = ls.get("DE")
    weakest = len(de.authority_hierarchy) + 1
    assert de.authority_rank("something unrecognised") == weakest
    assert de.authority_rank("Grundgesetz") == 1
