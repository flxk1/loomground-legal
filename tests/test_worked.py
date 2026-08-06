# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Worked, graded end-to-end cases — the operational proof that the branch
profile, competence, legal basis, and intertemporal selection COMPOSE with the
honesty spine intact. OPEN (escalate) is the correct terminal where the act is
formell rechtswidrig, lacks a basis, or turns on discretion / the applicable
version; a review never returns SATISFIED while a check is OPEN (fabrication 0).
"""
from __future__ import annotations

from loomground_legal import (
    Retroactivity,
    SourceClass,
    administrative_review,
    select_version,
)
from loomground_legal.lifecycle import LifecycleEvent
from loomground_solver.cross_subsumption import Verdict

# a competence delegation chain: supervisor → authority → office
_CHAIN = (("supervisor", "authority"), ("authority", "office"))


# ── administrative review: competence + legal basis + Ermessen, graded ───────

def test_competent_office_with_binding_basis_stands() -> None:
    r = administrative_review(
        authorizing_authority="supervisor", acting_office="office",
        competence_edges=_CHAIN,
        authorizing_source=SourceClass.NATIONAL_STATUTE)   # binding, self-executing
    assert r.verdict is Verdict.SATISFIED
    assert r.competence is Verdict.SATISFIED and r.legal_basis is Verdict.SATISFIED
    assert not r.escalates


def test_broken_competence_chain_escalates() -> None:
    # the acting office is not reachable from the authority → formell rechtswidrig
    r = administrative_review(
        authorizing_authority="supervisor", acting_office="rogue_office",
        competence_edges=_CHAIN,
        authorizing_source=SourceClass.NATIONAL_STATUTE)
    assert r.competence is Verdict.OPEN
    assert r.escalates                                     # OPEN dominates
    assert any("formell rechtswidrig" in x for x in r.reasons)


def test_missing_legal_basis_escalates() -> None:
    r = administrative_review(
        authorizing_authority="supervisor", acting_office="office",
        competence_edges=_CHAIN, authorizing_source=None)
    assert r.legal_basis is Verdict.OPEN and r.escalates
    assert any("Vorbehalt des Gesetzes" in x for x in r.reasons)


def test_soft_law_basis_is_insufficient() -> None:
    # soft law can never carry BINDING force → no valid Ermächtigungsgrundlage
    r = administrative_review(
        authorizing_authority="supervisor", acting_office="office",
        competence_edges=_CHAIN, authorizing_source=SourceClass.SOFT_LAW)
    assert r.legal_basis is Verdict.OPEN and r.escalates


def test_ermessen_is_surfaced_not_substituted() -> None:
    r = administrative_review(
        authorizing_authority="supervisor", acting_office="office",
        competence_edges=_CHAIN,
        authorizing_source=SourceClass.NATIONAL_STATUTE, ermessen=True)
    assert r.escalates                                     # discretion → OPEN
    assert any("Ermessen" in x for x in r.reasons)


def test_review_never_satisfies_while_a_check_is_open() -> None:
    # the fabrication-0 invariant: OPEN-dominant fold, no confident 'valid'
    for src in (None, SourceClass.SOFT_LAW):
        r = administrative_review(
            authorizing_authority="supervisor", acting_office="rogue_office",
            competence_edges=_CHAIN, authorizing_source=src)
        assert r.verdict is Verdict.OPEN


# ── intertemporal: same facts, different date → different governing law ───────

_EVENTS = (LifecycleEvent("supersedes", "reg_v2", "reg_v1", "2018-05-25"),)
_ENACTED = {"reg_v1": "1995-10-24", "reg_v2": "2018-05-25"}
_CELEX = {"reg_v1": "31995L0046", "reg_v2": "32016R0679"}


def test_es_kommt_darauf_an_which_version_by_date() -> None:
    old = select_version("reg_v1", _EVENTS, event_time="2000-01-01",
                         enacted=_ENACTED, celex_of=_CELEX)
    new = select_version("reg_v1", _EVENTS, event_time="2020-01-01",
                         enacted=_ENACTED, celex_of=_CELEX)
    # same facts-lineage, different date → different governing work AND expression id
    assert old.index.norm_version == "reg_v1" and new.index.norm_version == "reg_v2"
    assert old.index.expression_id == "01995L0046-20000101"
    assert new.index.expression_id == "02016R0679-20200101"
    assert old.index.expression_id != new.index.expression_id


def test_applying_the_current_text_to_old_facts_escalates() -> None:
    # judging a 2000 event under the 2016 Regulation is echte Rückwirkung → contested
    sel = select_version("reg_v1", _EVENTS, event_time="2000-01-01", enacted=_ENACTED,
                         apply_version="reg_v2", facts_completed=True, celex_of=_CELEX)
    assert sel.contested and sel.index is None
    assert "echte" in sel.reason
    # the honest fallback is named: apply the version in force then
    assert any("tempus regit actum" in o for o in sel.options)


def test_temporal_index_carries_no_retroactivity_on_the_governing_version() -> None:
    sel = select_version("reg_v1", _EVENTS, event_time="2000-01-01",
                         enacted=_ENACTED, celex_of=_CELEX)
    assert sel.index.retroactivity is Retroactivity.NONE
