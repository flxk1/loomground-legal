# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""End-to-end: a scenario driven through the WHOLE legal stack via `analyse`
(recognition → adjudication). Proves grammar → algebra → system compose, with the
honesty spine intact: a well-formed norm fires on grounded facts; a presupposed
fact escalates; a collision resolves by lex superior; an ill-formed statement is
excluded from the reasoning, never reasoned over; and nothing-recognisable → OPEN."""
from __future__ import annotations

from loomground_legal import Effect, LegalStatement, SourceClass, analyse
from loomground_solver import Dimension
from loomground_solver.cross_subsumption import Condition, FactSpace, Verdict
from loomground_solver.reasoning import Edge


def _duty(subject: str, object: str) -> LegalStatement:
    return LegalStatement(
        source="reg", source_class=SourceClass.NATIONAL_STATUTE,
        claimed_effect=Effect.BINDING, operative_content="duty",
        antecedent=(Condition(name="is_addressee", dimension=Dimension.STRUCTURAL,
                              subject=subject, object=object),))


def test_e2e_well_formed_norm_fires_on_grounded_facts() -> None:
    facts = FactSpace(structural_edges=(
        Edge("controller", "is_a", "addressee", Dimension.STRUCTURAL),))
    r = analyse([_duty("controller", "addressee")], facts)
    assert r.verdict is Verdict.SATISFIED and not r.ill_formed
    assert r.adjudication is not None and r.adjudication.fired


def test_e2e_presupposed_fact_escalates() -> None:
    # the addressee relation is presupposed-not-grounded (versum-incomplete) → the
    # antecedent is OPEN → the whole analysis escalates, never a fabricated firing
    facts = FactSpace(structural_edges=(),
                      incomplete_structural=(("controller", "addressee"),))
    r = analyse([_duty("controller", "addressee")], facts)
    assert r.verdict is Verdict.OPEN and r.escalates


def test_e2e_collision_resolved_by_lex_superior() -> None:
    # a constitutional permission vs a statutory prohibition on the same act, both
    # unconditional (fire) → the collision is resolved lex superior (constitution)
    con = LegalStatement(source="GG", source_class=SourceClass.CONSTITUTION,
                         claimed_effect=Effect.BINDING, operative_content="permission")
    sta = LegalStatement(source="reg", source_class=SourceClass.NATIONAL_STATUTE,
                         claimed_effect=Effect.BINDING, operative_content="prohibition")
    r = analyse([con, sta], FactSpace(), act="drive")
    assert r.verdict is Verdict.SATISFIED
    assert r.adjudication.conflict is not None
    assert r.adjudication.conflict.rule == "lex-superior"


def test_e2e_ill_formed_statement_is_excluded_not_reasoned_over() -> None:
    # a technical standard claiming BINDING is ill-formed (SC-2) → excluded from the
    # reasoning; the analysis proceeds on the well-formed statute
    standard = LegalStatement(source="EN-303", source_class=SourceClass.TECHNICAL_STANDARD,
                              claimed_effect=Effect.BINDING, operative_content="duty")
    facts = FactSpace(structural_edges=(
        Edge("controller", "is_a", "addressee", Dimension.STRUCTURAL),))
    r = analyse([standard, _duty("controller", "addressee")], facts)
    assert standard in r.ill_formed
    assert r.verdict is Verdict.SATISFIED               # proceeds on the well-formed statute


def test_e2e_no_recognisable_law_escalates() -> None:
    # only an ill-formed statement → nothing recognisable to apply → OPEN, never a
    # verdict reasoned over law the engine could not recognise
    standard = LegalStatement(source="EN", source_class=SourceClass.TECHNICAL_STANDARD,
                              claimed_effect=Effect.BINDING, operative_content="duty")
    r = analyse([standard], FactSpace())
    assert r.verdict is Verdict.OPEN and r.adjudication is None
