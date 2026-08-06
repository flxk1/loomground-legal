# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The legal algebra's composition operations. apply: a statement's consequence
fires only when its antecedent is SATISFIED against the facts — OPEN (a
presupposed fact) escalates, never fires. resolve_conflict: lex superior over the
source-hierarchy partial order, then lex posterior by version date; an antichain
with no comparable dates is ⊥ → escalate, never a fabricated winner."""
from __future__ import annotations

from loomground_legal import (
    Effect,
    LegalStatement,
    SourceClass,
    apply,
    resolve_conflict,
)
from loomground_solver import Dimension
from loomground_solver.cross_subsumption import Condition, FactSpace, Verdict
from loomground_solver.reasoning import Edge

# a statute whose antecedent is one structural condition: authority ⟶ office
_ANTECEDENT = (Condition(name="competent", dimension=Dimension.STRUCTURAL,
                         subject="authority", object="office"),)


def _statute(**kw):
    return LegalStatement(source="reg", source_class=SourceClass.NATIONAL_STATUTE,
                          claimed_effect=Effect.BINDING, operative_content="duty",
                          antecedent=_ANTECEDENT, **kw)


# ── apply: statement × facts → conclusion ────────────────────────────────────

def test_consequence_fires_when_the_antecedent_is_satisfied() -> None:
    facts = FactSpace(structural_edges=(
        Edge("authority", "delegates", "office", Dimension.STRUCTURAL),))
    c = apply(_statute(), facts)
    assert c.verdict is Verdict.SATISFIED and c.fires
    assert c.operative_content == "duty"


def test_consequence_does_not_fire_when_the_antecedent_is_not_met() -> None:
    facts = FactSpace(structural_edges=())               # unreachable, taxonomy complete
    c = apply(_statute(), facts)
    assert c.verdict is Verdict.NOT_SATISFIED and not c.fires
    assert c.operative_content == ""


def test_presupposed_fact_escalates_never_fires() -> None:
    # versum marks the region incomplete → OPEN → the consequence must NOT fire
    facts = FactSpace(structural_edges=(),
                      incomplete_structural=(("authority", "office"),))
    c = apply(_statute(), facts)
    assert c.verdict is Verdict.OPEN and c.escalates and not c.fires


def test_an_unconditional_norm_fires_vacuously() -> None:
    unconditional = LegalStatement(
        source="reg", source_class=SourceClass.NATIONAL_STATUTE,
        claimed_effect=Effect.BINDING, operative_content="duty", antecedent=())
    c = apply(unconditional, FactSpace())
    assert c.verdict is Verdict.SATISFIED and c.fires


# ── resolve_conflict: statement × statement → prevailing / escalate ──────────

def _stmt(cls, expr=""):
    return LegalStatement(source=cls.value, source_class=cls,
                          claimed_effect=Effect.BINDING, operative_content="duty",
                          expression_id=expr)


def test_lex_superior_the_higher_class_prevails() -> None:
    r = resolve_conflict(_stmt(SourceClass.CONSTITUTION), _stmt(SourceClass.NATIONAL_STATUTE))
    assert r.rule == "lex-superior" and not r.escalated
    assert r.prevailing.source_class is SourceClass.CONSTITUTION


def test_antichain_falls_to_lex_posterior_by_version_date() -> None:
    # incomparable classes (constitution vs supranational-primary), but datable →
    # the later version prevails (lex posterior)
    older = _stmt(SourceClass.CONSTITUTION, expr="0constitution-19950101")
    newer = _stmt(SourceClass.SUPRANATIONAL_PRIMARY, expr="0primary-20200101")
    r = resolve_conflict(older, newer)
    assert r.rule == "lex-posterior" and r.prevailing is newer


def test_antichain_with_no_dates_escalates() -> None:
    # incomparable classes AND no version dates → neither superior nor posterior
    # settles it → ⊥ escalate, never a fabricated winner
    r = resolve_conflict(_stmt(SourceClass.CONSTITUTION),
                         _stmt(SourceClass.SUPRANATIONAL_PRIMARY))
    assert r.escalated and r.prevailing is None and r.rule == "escalate"
