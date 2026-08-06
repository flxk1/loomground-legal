# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Sources-of-law: rank data + lowering to solver ``Norm``s, with conflict
resolution DELEGATED whole to the REAL solver (``derive`` under
``LEX_CONFLICT_PACK``). The winner and the separating rule in every test are
the solver's own — this package must contain no defeat logic of its own."""
from __future__ import annotations

import inspect

import pytest
from loomground_solver import ActResolution, Norm

import loomground_legal.sources as sources_module
from loomground_legal import (
    ConflictOutcome,
    Provision,
    load_sources,
    resolve_provisions,
    source_rank,
    to_norm,
)


# ── the rank map is data, loaded fail-closed ─────────────────────────────────

def test_rank_order_is_the_declared_hierarchy():
    data = load_sources()
    assert data["rank_order"] == [
        "eu_primary_law",
        "eu_regulation",
        "eu_directive",
        "national_constitution",
        "national_statute",
        "national_regulation",
        "administrative_act",
    ]
    ranks = [source_rank(t) for t in data["rank_order"]]
    assert ranks == sorted(ranks, reverse=True)  # strictly higher-wins order
    assert len(set(ranks)) == len(ranks)


def test_unknown_source_type_is_an_error():
    with pytest.raises(ValueError):
        source_rank("papal_bull")


# ── lowering: provision → solver Norm via the effect bridge ──────────────────

def test_to_norm_builds_a_real_solver_norm():
    n = to_norm(
        Provision(
            id="gdpr-art-6", act="process_personal_data", content="prohibition",
            source_type="eu_regulation", specificity=2, time=20160427,
        )
    )
    assert isinstance(n, Norm)
    assert n.deontic == "prohibited"
    assert n.rank == source_rank("eu_regulation")
    assert (n.specificity, n.time, n.source) == (2, 20160427, "gdpr-art-6")


def test_modal_free_content_cannot_enter_a_conflict():
    with pytest.raises(ValueError):
        to_norm(Provision(id="d", act="x", content="definition",
                          source_type="national_statute"))


# ── the three lex maxims, decided BY THE SOLVER ──────────────────────────────

def _resolve_pair(a: Provision, b: Provision) -> ConflictOutcome:
    outcomes = resolve_provisions([a, b])
    assert set(outcomes) == {a.act}
    return outcomes[a.act]


def test_lex_superior_higher_ranked_source_wins():
    out = _resolve_pair(
        Provision(id="eu-reg", act="transfer_data", content="prohibition",
                  source_type="eu_regulation", specificity=1, time=2016),
        Provision(id="de-statute", act="transfer_data", content="permission",
                  source_type="national_statute", specificity=5, time=2024),
    )
    assert out.status == "determinate" and not out.escalated
    assert out.winner == "eu-reg"
    assert out.verdict == "prohibited"
    assert out.rule == "lex-superior"


def test_lex_specialis_more_specific_wins_at_equal_rank():
    out = _resolve_pair(
        Provision(id="general", act="record_call", content="prohibition",
                  source_type="national_statute", specificity=1, time=2020),
        Provision(id="special", act="record_call", content="permission",
                  source_type="national_statute", specificity=7, time=2010),
    )
    assert out.winner == "special"
    assert out.verdict == "permitted"
    assert out.rule == "lex-specialis"


def test_lex_posterior_later_wins_at_equal_rank_and_specificity():
    out = _resolve_pair(
        Provision(id="old", act="sell_widget", content="permission",
                  source_type="national_regulation", specificity=3, time=20100101),
        Provision(id="new", act="sell_widget", content="prohibition",
                  source_type="national_regulation", specificity=3, time=20240101),
    )
    assert out.winner == "new"
    assert out.verdict == "prohibited"
    assert out.rule == "lex-posterior"


def test_genuine_collision_escalates_never_auto_resolves():
    out = _resolve_pair(
        Provision(id="norm-a", act="disclose", content="duty",
                  source_type="national_statute", specificity=2, time=2020),
        Provision(id="norm-b", act="disclose", content="prohibition",
                  source_type="national_statute", specificity=2, time=2020),
    )
    assert out.status == "open"
    assert out.escalated is True
    assert out.winner is None and out.rule is None and out.verdict is None
    assert ("norm-a", "norm-b") in out.resolution.collisions or \
           ("norm-b", "norm-a") in out.resolution.collisions


# ── the answer comes FROM the solver, provenance intact ──────────────────────

def test_winner_and_rule_are_read_off_the_solver_resolution():
    out = _resolve_pair(
        Provision(id="hi", act="a", content="duty", source_type="eu_directive"),
        Provision(id="lo", act="a", content="prohibition",
                  source_type="administrative_act"),
    )
    assert isinstance(out.resolution, ActResolution)  # the solver's own record
    assert out.winner in out.resolution.survivors
    assert any(
        d["winner"] == out.winner and d["rule"] == out.rule
        for d in out.resolution.defeats
    )


def test_sources_module_contains_no_hand_rolled_defeat_logic():
    src = inspect.getsource(sources_module)
    # It delegates…
    assert "derive(scenario, pack=LEX_CONFLICT_PACK)" in src
    # …and implements no ordering/contradiction machinery of its own.
    for forbidden in (".rank >", ".rank <", ".specificity >", ".specificity <",
                      ".time >", ".time <", "contradicts", "separating_rule(",
                      "def resolve("):
        assert forbidden not in src, forbidden


def test_empty_provision_set_is_an_error():
    with pytest.raises(ValueError):
        resolve_provisions([])
