# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The legal grammar: the canonical legal statement, its recognition gate
(well-formedness = SC ceilings + admissible relations + a consequence that lowers
to deontic/constitutive), and the source-hierarchy partial order (lex superior;
an incomparable pair is an antichain → escalate). Nothing is re-invented — the
gate consumes source_classes + effect; the order consumes legal_systems.class_rank."""
from __future__ import annotations

from loomground_legal import (
    Effect,
    LegalStatement,
    SourceClass,
    is_well_formed,
    lex_superior,
    outranks,
    validate,
)


def _statute(effect=Effect.BINDING, content="duty", **kw):
    return LegalStatement(source="reg", source_class=SourceClass.NATIONAL_STATUTE,
                          claimed_effect=effect, operative_content=content, **kw)


# ── recognition gate: well-formedness ────────────────────────────────────────

def test_a_binding_statutory_duty_is_well_formed_and_lowers_to_a_deontic_operator() -> None:
    wf = validate(_statute(content="duty",
                           relations=(("transposes", "directive_x"),)))
    assert wf.well_formed and not wf.findings and not wf.issues
    assert wf.deontic_operator is not None            # duty → O


def test_a_constitutive_effect_is_well_formed_with_no_operator() -> None:
    # a definition/establishment carries no modal of its own — operator None
    wf = validate(_statute(content="definition"))
    assert wf.well_formed and wf.deontic_operator is None


def test_sc2_a_standard_claiming_binding_is_not_well_formed() -> None:
    stmt = LegalStatement(source="EN-303", source_class=SourceClass.TECHNICAL_STANDARD,
                          claimed_effect=Effect.BINDING, operative_content="duty")
    wf = validate(stmt)
    assert not wf.well_formed
    assert any(f.invariant == "SC-2" for f in wf.findings)


def test_sc3_directive_binding_without_incorporation_is_not_well_formed() -> None:
    stmt = LegalStatement(source="dir", source_class=SourceClass.SUPRANATIONAL_DIRECTIVE,
                          claimed_effect=Effect.BINDING, operative_content="duty")
    assert not is_well_formed(stmt)
    assert any(f.invariant == "SC-3" for f in validate(stmt).findings)
    # once transposed (an incorporation edge), it is well-formed
    assert is_well_formed(LegalStatement(
        source="dir", source_class=SourceClass.SUPRANATIONAL_DIRECTIVE,
        claimed_effect=Effect.BINDING, operative_content="duty",
        has_incorporation_edge=True))


def test_sc4_an_inadmissible_relation_is_flagged() -> None:
    wf = validate(_statute(relations=(("relates_to", "x"),)))   # not in the vocabulary
    assert not wf.well_formed and any("SC-4" in i for i in wf.issues)


def test_unrecognised_operative_content_fails_closed() -> None:
    wf = validate(_statute(content="vibes"))
    assert not wf.well_formed and any("not a recognised kind" in i for i in wf.issues)


# ── the source-hierarchy partial order (lex superior) ────────────────────────

def test_outranks_is_a_partial_order_over_source_classes() -> None:
    # DE class_rank: constitution > national_statute > national_regulation > case_law
    assert outranks(SourceClass.CONSTITUTION, SourceClass.NATIONAL_STATUTE) is True
    assert outranks(SourceClass.NATIONAL_STATUTE, SourceClass.CONSTITUTION) is False


def test_incomparable_classes_are_an_antichain_open() -> None:
    # a class outside DE's national class_rank is incomparable → None (⊥, escalate)
    assert outranks(SourceClass.CONSTITUTION, SourceClass.SUPRANATIONAL_PRIMARY) is None
    assert outranks(SourceClass.NATIONAL_STATUTE, SourceClass.NATIONAL_STATUTE) is None


def test_lex_superior_selects_the_maximal_element() -> None:
    constitution = LegalStatement(source="GG", source_class=SourceClass.CONSTITUTION,
                                  claimed_effect=Effect.BINDING, operative_content="duty")
    statute = _statute()
    assert lex_superior(constitution, statute) is constitution
    assert lex_superior(statute, constitution) is constitution


def test_lex_superior_escalates_on_an_antichain() -> None:
    a = LegalStatement(source="GG", source_class=SourceClass.CONSTITUTION,
                       claimed_effect=Effect.BINDING, operative_content="duty")
    b = LegalStatement(source="TFEU", source_class=SourceClass.SUPRANATIONAL_PRIMARY,
                       claimed_effect=Effect.BINDING, operative_content="duty")
    # constitution vs supranational-primary is not decided by lex superior alone
    # (BVerfG identity review vs EU primacy) → None, escalate, never a fake winner
    assert lex_superior(a, b) is None
