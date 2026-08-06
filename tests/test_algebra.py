# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The legal algebra's composition operations. apply: a statement's consequence
fires only when its antecedent is SATISFIED against the facts — OPEN (a
presupposed fact) escalates, never fires. resolve_conflict: lex superior over the
source-hierarchy partial order, then lex posterior by version date; an antichain
with no comparable dates is ⊥ → escalate, never a fabricated winner."""
from __future__ import annotations

import pytest

from loomground_legal import (
    Effect,
    LegalStatement,
    SourceClass,
    apply,
    derive,
    resolve,
    resolve_conflict,
    to_provision,
)
from loomground_solver import Dimension
from loomground_solver.cross_subsumption import Condition, FactSpace, Verdict
from loomground_solver.reasoning import Edge


def _cond(subject, object):
    return (Condition(name=f"{subject}->{object}", dimension=Dimension.STRUCTURAL,
                      subject=subject, object=object),)

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


def test_genuine_antichain_escalates_even_with_dates() -> None:
    # constitutional-identity review vs EU primacy is a GENUINE collision — it is
    # NOT resolved by recency. lex posterior never crosses the antichain: even with
    # version dates present, resolve_conflict escalates (the fix — a fabricated
    # recency-winner here would break the honesty spine).
    older = _stmt(SourceClass.CONSTITUTION, expr="0constitution-19950101")
    newer = _stmt(SourceClass.SUPRANATIONAL_PRIMARY, expr="0primary-20200101")
    r = resolve_conflict(older, newer)
    assert r.escalated and r.prevailing is None and r.rule == "escalate"


def test_antichain_with_no_dates_escalates() -> None:
    r = resolve_conflict(_stmt(SourceClass.CONSTITUTION),
                         _stmt(SourceClass.SUPRANATIONAL_PRIMARY))
    assert r.escalated and r.prevailing is None and r.rule == "escalate"


# ── derive: fire a set of statements against facts (one pass) ─────────────────

def _statute_over(subject, object):
    return LegalStatement(source=f"{subject}->{object}",
                          source_class=SourceClass.NATIONAL_STATUTE,
                          claimed_effect=Effect.BINDING, operative_content="duty",
                          antecedent=_cond(subject, object))


def test_derive_partitions_fired_open_and_inapplicable() -> None:
    facts = FactSpace(
        structural_edges=(Edge("authority", "delegates", "office", Dimension.STRUCTURAL),),
        incomplete_structural=(("authority", "ghost"),))
    fires = _statute_over("authority", "office")       # reachable → SATISFIED
    opens = _statute_over("authority", "ghost")        # unreachable but flagged → OPEN
    inappl = _statute_over("authority", "nowhere")     # unreachable, complete → NOT_SAT
    d = derive([fires, opens, inappl], facts)
    assert [c.statement for c in d.fired] == [fires]
    assert [c.statement for c in d.open] == [opens]
    assert [c.statement for c in d.inapplicable] == [inappl]
    assert d.escalates                                 # an OPEN statement present


# ── resolve: deontic-modal conflict on an act (delegated to the LEX pack) ─────

def _rankable(cls, content, expr=""):
    return LegalStatement(source=cls.value, source_class=cls,
                          claimed_effect=Effect.BINDING, operative_content=content,
                          expression_id=expr)


def test_resolve_delegates_full_lex_resolution_higher_source_wins() -> None:
    # constitution PERMISSION vs statute PROHIBITION on the same act → clash;
    # the solver's LEX_CONFLICT_PACK settles it lex-superior (constitution = p0)
    con = _rankable(SourceClass.CONSTITUTION, "permission")
    sta = _rankable(SourceClass.NATIONAL_STATUTE, "prohibition")
    oc = resolve([con, sta], act="drive")
    assert oc.status == "determinate" and oc.winner == "p0" and oc.rule == "lex-superior"


def test_resolve_lex_posterior_uses_explicit_enactment_time() -> None:
    # equal rank; without explicit enactment `times` both are undated (0) → the pack
    # cannot separate → open (no fabricated posterior). Explicit `times` settle it by
    # lex posterior (the later prevails). Posterior lives HERE, not in resolve_conflict.
    a = _rankable(SourceClass.NATIONAL_STATUTE, "permission")
    b = _rankable(SourceClass.NATIONAL_STATUTE, "prohibition")
    assert resolve([a, b], act="drive").status == "open"            # undated → can't separate
    oc = resolve([a, b], act="drive", times=[19950101, 20200101])   # explicit enactment
    assert oc.status == "determinate" and oc.rule == "lex-posterior"


def test_resolve_non_rankable_escalates_not_crashes() -> None:
    # review F1: a non-rankable statement (case law) makes the collision inseparable —
    # resolve escalates GRACEFULLY (⊥), it does not raise ValueError
    cl = _rankable(SourceClass.CASE_LAW, "permission")
    st = _rankable(SourceClass.NATIONAL_STATUTE, "prohibition")
    oc = resolve([cl, st], act="drive")
    assert oc is not None and oc.status == "open" and oc.escalated
    assert oc.winner is None and oc.rule == "escalate"


def test_resolve_posterior_on_unknown_date_escalates() -> None:
    # review F2: a lex-posterior decision that turned on an UNKNOWN (0) enactment
    # date is a fabricated loss (undated == oldest) — resolve escalates instead of
    # letting the undated statement lose on the merits it does not have
    a = _rankable(SourceClass.NATIONAL_STATUTE, "permission")     # unknown enactment (0)
    b = _rankable(SourceClass.NATIONAL_STATUTE, "prohibition")
    oc = resolve([a, b], act="drive", times=[0, 20200101])
    assert oc.status == "open" and oc.escalated                  # not a determinate posterior


def test_resolve_unseparable_conflict_is_open() -> None:
    # two national statutes, permission vs prohibition, no separating rank/spec/time
    # → the pack cannot separate them → status 'open' (escalate)
    a = _rankable(SourceClass.NATIONAL_STATUTE, "permission")
    b = _rankable(SourceClass.NATIONAL_STATUTE, "prohibition")
    oc = resolve([a, b], act="drive")
    assert oc.status == "open"


def test_a_non_rankable_class_cannot_enter_the_conflict() -> None:
    # case law is not in the source-type rank map → to_provision fails closed
    with pytest.raises(ValueError):
        to_provision(_rankable(SourceClass.CASE_LAW, "duty"), act="drive")
