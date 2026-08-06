# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The seam where versum's data lives in solver's reasoning: a branch antecedent
subsumed against a 5D+nD FactSpace via cross-dimensional subsumption. The three
honest outcomes turn on versum's own completeness marks — grounded → SATISFIED,
unreachable-but-taxonomy-complete → NOT_SATISFIED (closed-world), unreachable-
but-known-incomplete → OPEN (never deny what versum admits it has not grounded).
"""
from __future__ import annotations

from loomground_legal import review_against_facts
from loomground_solver import Dimension
from loomground_solver.cross_subsumption import Condition, FactSpace, Verdict
from loomground_solver.reasoning import Edge

# an administrative antecedent: the office must be competent (STRUCTURAL: reachable
# from the authority over the delegation chain) AND a legal basis must exist
# (INTENTIONAL: a closed-world literal).
_CONDS = (
    Condition(name="competence", dimension=Dimension.STRUCTURAL,
              subject="authority", object="office"),
    Condition(name="legal_basis", dimension=Dimension.INTENTIONAL,
              literal="ermaechtigungsgrundlage"),
)
_BASIS = frozenset({"ermaechtigungsgrundlage"})


def test_grounded_facts_satisfy_the_antecedent() -> None:
    facts = FactSpace(
        structural_edges=(Edge("authority", "delegates", "office", Dimension.STRUCTURAL),),
        literals=_BASIS)
    r = review_against_facts("administrative", _CONDS, facts)
    assert r.verdict is Verdict.SATISFIED and not r.escalates


def test_unreachable_with_complete_taxonomy_is_not_satisfied() -> None:
    # the delegation chain is absent and the taxonomy is NOT flagged incomplete →
    # closed-world: unproven competence is NOT_SATISFIED, not a fabricated pass
    facts = FactSpace(structural_edges=(), literals=_BASIS)
    r = review_against_facts("administrative", _CONDS, facts)
    assert r.verdict is Verdict.NOT_SATISFIED and not r.escalates


def test_versum_incompleteness_propagates_to_open() -> None:
    # versum marks the (authority, office) region of the taxonomy as under-specified
    # (presupposed, not grounded) → the competence condition is OPEN, and OPEN
    # dominates the antecedent. This is the whole point: absence of a path is not
    # proof of non-competence when versum itself admits the taxonomy is incomplete.
    facts = FactSpace(structural_edges=(), literals=_BASIS,
                      incomplete_structural=(("authority", "office"),))
    r = review_against_facts("administrative", _CONDS, facts)
    assert r.verdict is Verdict.OPEN and r.escalates


def test_per_condition_verdicts_are_carried_through() -> None:
    facts = FactSpace(
        structural_edges=(Edge("authority", "delegates", "office", Dimension.STRUCTURAL),),
        literals=frozenset())                       # basis missing
    r = review_against_facts("administrative", _CONDS, facts)
    by_name = {d.condition: d.verdict for d in r.per_condition}
    assert by_name["competence"] is Verdict.SATISFIED
    assert by_name["legal_basis"] is Verdict.NOT_SATISFIED   # closed-world literal absent
    assert r.verdict is Verdict.NOT_SATISFIED


def test_unknown_branch_fails_closed() -> None:
    import pytest
    with pytest.raises(KeyError):
        review_against_facts("maritime", _CONDS, FactSpace())
