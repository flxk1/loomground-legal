# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Intertemporal law: tempus regit actum (the version in force when the facts
occurred governs — NOT the current text), the temporal index that stamps a
conclusion, and retroactivity (echte → escalate; unechte → permissible, flagged)
as a gated choice. Version logic is the lifecycle's; only the doctrine is here."""
from __future__ import annotations

from loomground_legal import (
    Retroactivity,
    classify_retroactivity,
    governing_version,
    select_version,
    stamp,
)
from loomground_legal.lifecycle import LifecycleEvent

# A two-version lineage: reg_v1 enacted 1995; reg_v2 supersedes it on 2018-05-25.
_EVENTS = (LifecycleEvent("supersedes", "reg_v2", "reg_v1", "2018-05-25"),)
_ENACTED = {"reg_v1": "1995-10-24", "reg_v2": "2018-05-25"}


# ── tempus regit actum: the law AS OF THE FACTS, not the current version ─────

def test_governing_version_is_the_one_in_force_at_the_facts_time() -> None:
    # facts in 2000 → the OLD version governs, not the current reg_v2
    assert governing_version("reg_v1", _EVENTS, event_time="2000-01-01",
                             enacted=_ENACTED) == "reg_v1"
    # facts in 2020 → the new version
    assert governing_version("reg_v1", _EVENTS, event_time="2020-01-01",
                             enacted=_ENACTED) == "reg_v2"


def test_select_version_defaults_to_tempus_regit_actum() -> None:
    sel = select_version("reg_v1", _EVENTS, event_time="2000-01-01", enacted=_ENACTED)
    assert sel.selected
    assert sel.index.norm_version == "reg_v1"       # NOT the current reg_v2
    assert sel.index.basis == "tempus regit actum"
    assert sel.index.event_time == "2000-01-01"
    assert sel.index.retroactivity is Retroactivity.NONE


def test_no_governing_version_is_contested() -> None:
    # before reg_v1 was enacted, nothing is in force → escalate, don't guess
    sel = select_version("reg_v1", _EVENTS, event_time="1990-01-01", enacted=_ENACTED)
    assert sel.contested and sel.index is None
    assert sel.options


# ── retroactivity is a gated question, not a silent version swap ─────────────

def test_applying_a_later_version_to_completed_facts_is_echte_and_escalates() -> None:
    # apply reg_v2 (2018) to facts completed in 2000 → echte Rückwirkung → contested
    sel = select_version("reg_v1", _EVENTS, event_time="2000-01-01", enacted=_ENACTED,
                         apply_version="reg_v2", facts_completed=True)
    assert sel.contested and sel.index is None
    assert "echte" in sel.reason
    assert any("tempus regit actum" in o for o in sel.options)


def test_applying_a_later_version_to_ongoing_facts_is_unechte_and_flagged() -> None:
    # facts still ongoing at 2000 → unechte Rückwirkung → permissible but flagged
    sel = select_version("reg_v1", _EVENTS, event_time="2000-01-01", enacted=_ENACTED,
                         apply_version="reg_v2", facts_completed=False)
    assert sel.selected
    assert sel.index.retroactivity is Retroactivity.UNECHTE
    assert "Vertrauensschutz" in sel.reason


def test_classify_retroactivity_three_cases() -> None:
    # already in force at the event
    assert classify_retroactivity(version_start="1995-10-24", event_time="2000-01-01",
                                  facts_completed=True) is Retroactivity.NONE
    # starts after the event, facts closed → echte
    assert classify_retroactivity(version_start="2018-05-25", event_time="2000-01-01",
                                  facts_completed=True) is Retroactivity.ECHTE
    # starts after the event, facts ongoing → unechte
    assert classify_retroactivity(version_start="2018-05-25", event_time="2000-01-01",
                                  facts_completed=False) is Retroactivity.UNECHTE
    # undatable version → None (undecidable)
    assert classify_retroactivity(version_start=None, event_time="2000-01-01",
                                  facts_completed=True) is None


# ── the temporal index stamps a conclusion with which-law-as-of-when ─────────

def test_stamp_attaches_the_temporal_index_to_a_receipt() -> None:
    sel = select_version("reg_v1", _EVENTS, event_time="2000-01-01", enacted=_ENACTED)
    receipt = stamp(sel.index, {"verdict": "SATISFIED"})
    assert receipt["verdict"] == "SATISFIED"          # original preserved
    ti = receipt["temporal_index"]
    assert ti["norm_version"] == "reg_v1" and ti["event_time"] == "2000-01-01"
    assert ti["basis"] == "tempus regit actum"
    assert ti["retroactivity"] == "none"


def test_stamp_does_not_mutate_the_input_receipt() -> None:
    original = {"verdict": "SATISFIED"}
    sel = select_version("reg_v1", _EVENTS, event_time="2020-01-01", enacted=_ENACTED)
    stamp(sel.index, original)
    assert "temporal_index" not in original           # returned a new dict


def test_expression_id_is_a_real_consolidated_celex_not_a_token() -> None:
    # give the lineage members their base CELEX → the index cites the EXPRESSION
    celex_of = {"reg_v1": "31995L0046", "reg_v2": "32016R0679"}
    sel = select_version("reg_v1", _EVENTS, event_time="2020-06-01",
                         enacted=_ENACTED, celex_of=celex_of)
    assert sel.selected
    assert sel.index.norm_version == "reg_v2"                       # the governing WORK
    assert sel.index.expression_id == "02016R0679-20200601"        # the EXPRESSION at T
    # a 2000 fact cites the OLD work's expression, not the current one
    old = select_version("reg_v1", _EVENTS, event_time="2000-01-01",
                         enacted=_ENACTED, celex_of=celex_of)
    assert old.index.expression_id == "01995L0046-20000101"
    # without celex_of, expression_id is empty (honest — no fabricated id)
    plain = select_version("reg_v1", _EVENTS, event_time="2000-01-01", enacted=_ENACTED)
    assert plain.index.expression_id == ""
