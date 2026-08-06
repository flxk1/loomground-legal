# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Instrument lifecycle: dated supersession/repeal events, deterministic
"which version is in force at T", and the fail-closed edges."""
from __future__ import annotations

import pytest

from loomground_legal import (
    LIFECYCLE_RELATIONS,
    LifecycleEvent,
    in_force,
    version_in_force,
)

# The reference lineage: DPD (95/46/EC) —superseded by→ GDPR on 2018-05-25.
_DPD_GDPR = [
    LifecycleEvent("supersedes", "gdpr", "dpd", "2018-05-25"),
    LifecycleEvent("descends_from", "gdpr", "dpd", "2018-05-25"),
]


# ── supersession chain resolves to the in-force instrument at T ──────────────

def test_before_supersession_the_old_law_is_in_force():
    assert version_in_force("gdpr", _DPD_GDPR, "2016-01-01") == "dpd"
    assert in_force("dpd", _DPD_GDPR, "2016-01-01") is True
    assert in_force("gdpr", _DPD_GDPR, "2016-01-01") is False  # not yet introduced


def test_after_supersession_the_new_law_is_in_force():
    assert version_in_force("dpd", _DPD_GDPR, "2019-01-01") == "gdpr"
    assert in_force("dpd", _DPD_GDPR, "2019-01-01") is False
    assert in_force("gdpr", _DPD_GDPR, "2019-01-01") is True


def test_supersession_is_effective_on_its_date():
    assert version_in_force("dpd", _DPD_GDPR, "2018-05-25") == "gdpr"


def test_three_link_chain_resolves_each_era():
    chain = [
        LifecycleEvent("supersedes", "v2", "v1", "2000-01-01"),
        LifecycleEvent("supersedes", "v3", "v2", "2010-01-01"),
    ]
    enacted = {"v1": "1990-01-01"}
    assert version_in_force("v1", chain, "1995-06-01", enacted=enacted) == "v1"
    assert version_in_force("v1", chain, "2005-06-01", enacted=enacted) == "v2"
    assert version_in_force("v1", chain, "2020-06-01", enacted=enacted) == "v3"
    # Any member identifies the lineage.
    assert version_in_force("v3", chain, "2005-06-01", enacted=enacted) == "v2"


def test_before_enactment_nothing_is_in_force():
    chain = [LifecycleEvent("supersedes", "v2", "v1", "2000-01-01")]
    assert version_in_force("v1", chain, "1980-01-01",
                            enacted={"v1": "1990-01-01"}) is None


# ── repeal terminates; amendment does not ────────────────────────────────────

def test_a_repealed_instrument_is_out_of_force():
    events = [LifecycleEvent("repeals", "repealing-act", "old-act", "2005-03-01")]
    assert in_force("old-act", events, "2004-12-31") is True
    assert in_force("old-act", events, "2005-03-01") is False
    assert in_force("old-act", events, "2010-01-01") is False


def test_amendment_never_terminates():
    events = [LifecycleEvent("amends", "novelle", "act", "2005-03-01")]
    assert in_force("act", events, "2010-01-01") is True


# ── typed, deterministic, fail-closed ────────────────────────────────────────

def test_lifecycle_vocabulary_is_the_connection_relations_plus_event_pair():
    assert {"supersedes", "descends_from", "presumes_conformity", "applies_in",
            "adopted_by", "established_by"} < LIFECYCLE_RELATIONS
    assert {"repeals", "amends"} < LIFECYCLE_RELATIONS


def test_unknown_event_relation_is_an_error():
    with pytest.raises(ValueError):
        LifecycleEvent("revokes", "a", "b", "2000-01-01")


def test_undated_event_is_an_error():
    with pytest.raises(ValueError):
        LifecycleEvent("supersedes", "a", "b", "")


def test_inconsistent_lineage_raises_instead_of_picking():
    # Two live successors of one instrument: the record cannot justify a
    # single answer, so resolution refuses to pick one.
    events = [
        LifecycleEvent("supersedes", "b", "a", "2000-01-01"),
        LifecycleEvent("supersedes", "c", "a", "2000-01-01"),
    ]
    with pytest.raises(ValueError):
        version_in_force("a", events, "2005-01-01")
