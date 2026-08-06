# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Universal source-class map — the jurisdiction-agnostic effect ceilings,
relation vocabulary, and the SC-2/SC-3 invariants. Force ceilings are absolute
(a technical standard is never BINDING); incorporation is required for
non-self-executing classes. No jurisdiction data lives here."""
from __future__ import annotations

from loomground_legal import (
    Effect,
    Relation,
    SourceClass,
    check_source,
    is_relation,
    max_effect,
    requires_incorporation,
    self_executes,
)
from loomground_legal.source_classes import VOCABULARY, catalogue


# ── Effect is ordered, weakest→strongest ─────────────────────────────────────

def test_effect_is_ordered() -> None:
    assert Effect.PERSUASIVE < Effect.INTERPRETIVE < Effect.PRESUMPTION < Effect.BINDING
    assert Effect.PRESUMPTION <= Effect.PRESUMPTION


# ── ceilings: a standard is NEVER binding; soft law never above interpretive ──

def test_technical_standard_ceiling_is_presumption() -> None:
    assert max_effect(SourceClass.TECHNICAL_STANDARD) is Effect.PRESUMPTION
    assert max_effect(SourceClass.TECHNICAL_STANDARD) < Effect.BINDING


def test_soft_law_ceiling_is_interpretive() -> None:
    assert max_effect(SourceClass.SOFT_LAW) is Effect.INTERPRETIVE


def test_enacted_and_case_law_can_bind() -> None:
    for cls in (SourceClass.CONSTITUTION, SourceClass.NATIONAL_STATUTE,
                SourceClass.CASE_LAW, SourceClass.SUPRANATIONAL_REGULATION):
        assert max_effect(cls) is Effect.BINDING


# ── self-execution defaults ──────────────────────────────────────────────────

def test_directive_and_treaty_require_incorporation_by_default() -> None:
    assert requires_incorporation(SourceClass.SUPRANATIONAL_DIRECTIVE)
    assert requires_incorporation(SourceClass.INTERNATIONAL_TREATY)
    assert not self_executes(SourceClass.SUPRANATIONAL_DIRECTIVE)


def test_pack_may_widen_self_execution() -> None:
    extra = frozenset({SourceClass.CUSTOMARY_INTERNATIONAL})
    assert not self_executes(SourceClass.CUSTOMARY_INTERNATIONAL)
    assert self_executes(SourceClass.CUSTOMARY_INTERNATIONAL, extra)


# ── SC-2: claimed effect above the ceiling is a violation ────────────────────

def test_sc2_standard_claiming_binding_is_a_violation() -> None:
    findings = check_source(SourceClass.TECHNICAL_STANDARD, claimed_effect=Effect.BINDING)
    assert any(f.invariant == "SC-2" for f in findings)


def test_sc2_within_ceiling_is_clean() -> None:
    assert check_source(SourceClass.NATIONAL_STATUTE, claimed_effect=Effect.BINDING) == []


# ── SC-3: non-self-executing source asserted BINDING without an edge ─────────

def test_sc3_directive_binding_without_edge_is_a_violation() -> None:
    findings = check_source(SourceClass.SUPRANATIONAL_DIRECTIVE,
                            claimed_effect=Effect.BINDING)
    assert any(f.invariant == "SC-3" for f in findings)


def test_sc3_satisfied_once_incorporated() -> None:
    findings = check_source(SourceClass.SUPRANATIONAL_DIRECTIVE,
                            claimed_effect=Effect.BINDING,
                            has_incorporation_edge=True)
    assert findings == []


# ── relation vocabulary is closed ────────────────────────────────────────────

def test_relation_vocabulary_is_closed() -> None:
    assert is_relation(Relation.TRANSPOSES.value)
    assert not is_relation("relates_to")
    assert VOCABULARY == frozenset(r.value for r in Relation)


# ── catalogue is self-describing ─────────────────────────────────────────────

def test_catalogue_dumps_the_map() -> None:
    cat = catalogue()
    assert cat["ceilings"]["technical_standard"] == "PRESUMPTION"
    assert set(cat["source_classes"]) == {c.value for c in SourceClass}
    assert {i["id"] for i in cat["invariants"]} >= {"SC-1", "SC-2", "SC-3"}
