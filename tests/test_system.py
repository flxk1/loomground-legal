# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The legal SYSTEM layer — Hart's secondary rules as ops. CHANGE: enact (is a
statement in force at a time?) and supersede (which lineage member governs facts
at a time — tempus regit actum; echte Rückwirkung escalates). ADJUDICATION: the
end-to-end pipeline (derive → resolve → terminal), where any OPEN antecedent or a
genuine collision the pack cannot separate escalates — never a fabricated
resolution. Every op consumes; no time, conflict, or verdict logic is re-grown."""
from __future__ import annotations

from loomground_legal import intertemporal
from loomground_legal.grammar import LegalStatement
from loomground_legal.effect import OPERATIVE_CONTENT  # noqa: F401 (documents the surface)
from loomground_legal.lifecycle import LifecycleEvent
from loomground_legal.source_classes import Effect, SourceClass
from loomground_legal.system import (
    Adjudication,
    Enactment,
    Supersession,
    adjudicate,
    enact,
    supersede,
)
from loomground_solver.cross_subsumption import Condition, FactSpace, Verdict
from loomground_solver import Dimension
from loomground_solver.reasoning import Edge


# ── fixtures ──────────────────────────────────────────────────────────────────

# A two-version lineage: reg_v1 enacted 1995; reg_v2 supersedes it 2018-05-25.
_EVENTS = (LifecycleEvent("supersedes", "reg_v2", "reg_v1", "2018-05-25"),)
_ENACTED = {"reg_v1": "1995-10-24", "reg_v2": "2018-05-25"}

# one structural antecedent: authority ⟶ office
_ANTECEDENT = (Condition(name="competent", dimension=Dimension.STRUCTURAL,
                         subject="authority", object="office"),)
_FACTS_MET = FactSpace(structural_edges=(
    Edge("authority", "delegates", "office", Dimension.STRUCTURAL),))


def _stmt(member, *, source_class=SourceClass.NATIONAL_STATUTE,
          content="duty", antecedent=_ANTECEDENT):
    return LegalStatement(source=member, source_class=source_class,
                          claimed_effect=Effect.BINDING, operative_content=content,
                          antecedent=antecedent, expression_id=member)


# ── rule of CHANGE: enact — is a statement in force at a time? ────────────────

def test_enact_in_force_is_satisfied() -> None:
    e = enact(_stmt("reg_v1"), _EVENTS, at="2000-01-01", enacted=_ENACTED)
    assert isinstance(e, Enactment)
    assert e.in_force and e.verdict is Verdict.SATISFIED and not e.escalates
    assert e.governing == "reg_v1"


def test_enact_superseded_version_does_not_apply() -> None:
    # by 2020 reg_v1 has been superseded → NOT_SATISFIED, and it names reg_v2.
    e = enact(_stmt("reg_v1"), _EVENTS, at="2020-01-01", enacted=_ENACTED)
    assert not e.in_force and e.verdict is Verdict.NOT_SATISFIED
    assert e.governing == "reg_v2" and "reg_v2" in e.reason


def test_enact_before_enactment_is_not_in_force() -> None:
    # before reg_v1 existed nothing is in force → NOT_SATISFIED (determinate), not OPEN.
    e = enact(_stmt("reg_v1"), _EVENTS, at="1990-01-01", enacted=_ENACTED)
    assert not e.in_force and e.verdict is Verdict.NOT_SATISFIED
    assert e.governing is None


def test_enact_matches_the_consumed_lifecycle_surface() -> None:
    # enact re-grows nothing: its verdict tracks intertemporal.governing_version.
    for at in ("2000-01-01", "2019-01-01", "1990-01-01"):
        gv = intertemporal.governing_version("reg_v1", _EVENTS, event_time=at,
                                              enacted=_ENACTED)
        e = enact(_stmt("reg_v1"), _EVENTS, at=at, enacted=_ENACTED)
        assert e.in_force == (gv == "reg_v1")


# ── rule of CHANGE: supersede — which member governs facts at a time? ─────────

def test_supersede_old_governs_facts_before_the_change() -> None:
    old, new = _stmt("reg_v1"), _stmt("reg_v2")
    s = supersede(old, new, _EVENTS, at="2000-01-01", enacted=_ENACTED)
    assert isinstance(s, Supersession)
    assert s.verdict is Verdict.SATISFIED and not s.escalates
    assert s.governing is old               # tempus regit actum: the OLD law
    assert s.index is not None and s.index.norm_version == "reg_v1"
    assert s.index.basis == "tempus regit actum"


def test_supersede_new_governs_facts_after_the_change() -> None:
    old, new = _stmt("reg_v1"), _stmt("reg_v2")
    s = supersede(old, new, _EVENTS, at="2020-01-01", enacted=_ENACTED)
    assert s.verdict is Verdict.SATISFIED and s.governing is new
    assert s.index.norm_version == "reg_v2"


def test_supersede_no_governing_version_escalates() -> None:
    old, new = _stmt("reg_v1"), _stmt("reg_v2")
    s = supersede(old, new, _EVENTS, at="1990-01-01", enacted=_ENACTED)
    assert s.escalates and s.verdict is Verdict.OPEN
    assert s.governing is None and s.index is None and s.options


def test_supersede_echte_rueckwirkung_escalates() -> None:
    # forcing the 2018 version onto facts completed in 2000 is echte Rückwirkung —
    # contested; the choice is surfaced, never a silent swap to the current text.
    old, new = _stmt("reg_v1"), _stmt("reg_v2")
    s = supersede(old, new, _EVENTS, at="2000-01-01", enacted=_ENACTED,
                  apply=new, facts_completed=True)
    assert s.escalates and s.verdict is Verdict.OPEN
    assert "echte" in s.reason and s.governing is None


def test_supersede_unechte_rueckwirkung_is_flagged_not_escalated() -> None:
    # onto still-ongoing facts the retrospective application is permissible, flagged.
    old, new = _stmt("reg_v1"), _stmt("reg_v2")
    s = supersede(old, new, _EVENTS, at="2000-01-01", enacted=_ENACTED,
                  apply=new, facts_completed=False)
    assert s.verdict is Verdict.SATISFIED and s.governing is new
    assert s.index.retroactivity is intertemporal.Retroactivity.UNECHTE


# ── rule of ADJUDICATION: the end-to-end pipeline ─────────────────────────────

def test_adjudicate_single_norm_fires_and_stands() -> None:
    a = adjudicate([_stmt("s1")], _FACTS_MET)
    assert isinstance(a, Adjudication)
    assert a.verdict is Verdict.SATISFIED and not a.escalates
    assert len(a.fired) == 1 and a.conflict is None and a.prevailing is None


def test_adjudicate_no_norm_applies_is_not_satisfied() -> None:
    # antecedent not met (taxonomy complete) → nothing fires, nothing open.
    a = adjudicate([_stmt("s1")], FactSpace(structural_edges=()))
    assert a.verdict is Verdict.NOT_SATISFIED and not a.fired and not a.open


def test_adjudicate_open_antecedent_escalates_never_fires() -> None:
    # versum marks the region incomplete → OPEN antecedent → escalate terminal.
    facts = FactSpace(structural_edges=(),
                      incomplete_structural=(("authority", "office"),))
    a = adjudicate([_stmt("s1")], facts, act="drive")
    assert a.escalates and a.verdict is Verdict.OPEN
    assert a.open and a.conflict is None       # OPEN is caught before conflict resolution


def test_adjudicate_collision_resolved_by_lex_superior() -> None:
    # constitution 'duty' vs national statute 'prohibition' on 'drive' → both fire,
    # the pack separates by lex superior → the constitution prevails; SATISFIED.
    con = _stmt("c", source_class=SourceClass.CONSTITUTION, content="duty")
    sta = _stmt("s", source_class=SourceClass.NATIONAL_STATUTE, content="prohibition")
    a = adjudicate([con, sta], _FACTS_MET, act="drive")
    assert a.verdict is Verdict.SATISFIED and not a.escalates
    assert a.conflict is not None and a.conflict.status == "determinate"
    assert a.prevailing is con                 # positional winner mapped back correctly


def test_adjudicate_genuine_collision_escalates_no_fabricated_winner() -> None:
    # two national statutes, duty vs prohibition, no separating rank/spec/time →
    # the pack cannot separate them → escalate; the winner is NOT fabricated.
    a1 = _stmt("a", source_class=SourceClass.NATIONAL_STATUTE, content="duty")
    b1 = _stmt("b", source_class=SourceClass.NATIONAL_STATUTE, content="prohibition")
    a = adjudicate([a1, b1], _FACTS_MET, act="drive")
    assert a.escalates and a.verdict is Verdict.OPEN
    assert a.conflict is not None and a.conflict.escalated
    assert a.prevailing is None


def test_adjudicate_agreeing_consequences_have_no_prevailing() -> None:
    # two fired statutes with the SAME operative content agree → the pack returns a
    # determinate outcome with no unique winner (no collision) → both stand together,
    # no prevailing is picked; SATISFIED, not escalated.
    a1 = _stmt("a", source_class=SourceClass.NATIONAL_STATUTE, content="duty")
    b1 = _stmt("b", source_class=SourceClass.NATIONAL_STATUTE, content="duty")
    a = adjudicate([a1, b1], _FACTS_MET, act="drive")
    assert a.verdict is Verdict.SATISFIED and not a.escalates and len(a.fired) == 2
    assert a.conflict is not None and not a.conflict.escalated
    assert a.conflict.winner is None and a.prevailing is None


def test_adjudicate_non_rankable_class_in_collision_escalates() -> None:
    # a fired case-law statement is not rankable for a lex conflict → the collision
    # is inseparable → escalate (ValueError from to_provision is caught, not raised).
    law = _stmt("cl", source_class=SourceClass.CASE_LAW, content="duty")
    sta = _stmt("s", source_class=SourceClass.NATIONAL_STATUTE, content="prohibition")
    a = adjudicate([law, sta], _FACTS_MET, act="drive")
    assert a.escalates and a.verdict is Verdict.OPEN and a.prevailing is None


def test_adjudicate_no_act_skips_conflict_resolution() -> None:
    # without an act, adjudicate does not attempt per-act conflict resolution:
    # both fire and stand (the modal clash is not adjudicated).
    con = _stmt("c", source_class=SourceClass.CONSTITUTION, content="duty")
    sta = _stmt("s", source_class=SourceClass.NATIONAL_STATUTE, content="prohibition")
    a = adjudicate([con, sta], _FACTS_MET)
    assert a.verdict is Verdict.SATISFIED and a.conflict is None and len(a.fired) == 2
