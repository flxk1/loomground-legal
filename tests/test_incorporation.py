# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Tests for the legal INCORPORATION / cross-reference ops.

Honesty spine under test: a non-self-executing source with no transposition is
OPEN (not yet binding), never fabricated as binding; an unresolvable citation is
None, never guessed.
"""
from __future__ import annotations

from loomground_solver.cross_subsumption import Verdict

from loomground_legal.incorporation import (
    INCORPORATION_RELATIONS,
    incorporate,
    resolve_reference,
)
from loomground_legal.grammar import LegalStatement
from loomground_legal.source_classes import Effect, SourceClass


# ── builders ──────────────────────────────────────────────────────────────────

def _stmt(source, cls, *, effect=Effect.BINDING, relations=()):
    return LegalStatement(
        source=source, source_class=cls, claimed_effect=effect,
        operative_content="obligation", relations=tuple(relations))


def _directive(source="32019L0790"):
    return _stmt(source, SourceClass.SUPRANATIONAL_DIRECTIVE)


def _statute(source="UrhG", *, effect=Effect.BINDING, relations=()):
    return _stmt(source, SourceClass.NATIONAL_STATUTE, effect=effect, relations=relations)


# ── incorporate: self-executing sources need no edge ────────────────────────────

def test_self_executing_national_statute_binds_directly():
    src = _statute("BDSG")
    out = incorporate(src, _statute("irrelevant"))
    assert out.verdict is Verdict.SATISFIED
    assert out.binds is True
    assert out.incorporating is None
    assert out.relation is None
    assert not out.escalates


def test_self_executing_supranational_regulation_binds_directly():
    src = _stmt("32016R0679", SourceClass.SUPRANATIONAL_REGULATION)
    out = incorporate(src, _statute())
    assert out.verdict is Verdict.SATISFIED
    assert out.binds is True
    assert out.incorporating is None


def test_pack_widened_self_execution_binds_directly():
    # A treaty is non-self-executing by default, but a monist pack may widen it.
    treaty = LegalStatement(
        source="ECHR", source_class=SourceClass.INTERNATIONAL_TREATY,
        claimed_effect=Effect.BINDING, operative_content="obligation",
        self_executing_extra=frozenset({SourceClass.INTERNATIONAL_TREATY}))
    out = incorporate(treaty, _statute())
    assert out.verdict is Verdict.SATISFIED
    assert out.binds is True
    assert out.incorporating is None


# ── incorporate: a valid transposition/incorporation carries force ──────────────

def test_directive_validly_transposed_binds():
    directive = _directive("32019L0790")
    statute = _statute("UrhG", relations=[("transposes", "32019L0790")])
    out = incorporate(directive, statute)
    assert out.verdict is Verdict.SATISFIED
    assert out.binds is True
    assert out.incorporating == "UrhG"
    assert out.relation == "transposes"


def test_treaty_validly_incorporated_binds():
    treaty = _stmt("some-treaty", SourceClass.INTERNATIONAL_TREATY)
    ratifying = _statute("ratification-act", relations=[("incorporates", "some-treaty")])
    out = incorporate(treaty, ratifying, relation="incorporates")
    assert out.verdict is Verdict.SATISFIED
    assert out.binds is True
    assert out.incorporating == "ratification-act"
    assert out.relation == "incorporates"


def test_edge_in_other_admissible_mode_still_incorporates():
    # Asserted mode is the default "transposes" but the edge is "incorporates" —
    # still an admissible incorporation relation, so it binds and reports the edge.
    directive = _directive()
    statute = _statute(relations=[("incorporates", "32019L0790")])
    out = incorporate(directive, statute)  # default relation="transposes"
    assert out.verdict is Verdict.SATISFIED
    assert out.relation == "incorporates"


def test_asserted_mode_preferred_when_multiple_edges():
    directive = _directive()
    statute = _statute(relations=[("incorporates", "32019L0790"),
                                  ("transposes", "32019L0790")])
    out = incorporate(directive, statute, relation="transposes")
    assert out.verdict is Verdict.SATISFIED
    assert out.relation == "transposes"


# ── incorporate: the honesty spine — unincorporated → OPEN, never binding ───────

def test_directive_without_transposition_is_open_not_binding():
    directive = _directive("32019L0790")
    statute = _statute("UnrelatedAct")  # no relations at all
    out = incorporate(directive, statute)
    assert out.verdict is Verdict.OPEN
    assert out.binds is False
    assert out.escalates is True
    assert "NOT YET binding" in out.reason


def test_edge_to_wrong_target_does_not_incorporate():
    directive = _directive("32019L0790")
    # transposes a DIFFERENT directive, not ours.
    statute = _statute(relations=[("transposes", "32022L2555")])
    out = incorporate(directive, statute)
    assert out.verdict is Verdict.OPEN
    assert out.binds is False


def test_non_incorporation_relation_does_not_carry_force():
    directive = _directive("32019L0790")
    # "outranks" is in the vocabulary but is NOT an incorporation relation.
    statute = _statute(relations=[("outranks", "32019L0790")])
    out = incorporate(directive, statute)
    assert out.verdict is Verdict.OPEN
    assert out.binds is False


def test_inadmissible_asserted_relation_is_open():
    directive = _directive("32019L0790")
    statute = _statute(relations=[("transposes", "32019L0790")])
    # "supersedes" is admissible vocabulary but not an incorporation relation.
    out = incorporate(directive, statute, relation="supersedes")
    assert out.verdict is Verdict.OPEN
    assert out.binds is False


def test_ad_hoc_asserted_relation_is_open():
    directive = _directive("32019L0790")
    statute = _statute(relations=[("transposes", "32019L0790")])
    out = incorporate(directive, statute, relation="teleports")  # not in vocabulary
    assert out.verdict is Verdict.OPEN
    assert out.binds is False


def test_non_binding_incorporator_cannot_confer_force():
    directive = _directive("32019L0790")
    # Right edge, but the incorporator only claims interpretive force.
    statute = _statute(effect=Effect.INTERPRETIVE, relations=[("transposes", "32019L0790")])
    out = incorporate(directive, statute)
    assert out.verdict is Verdict.OPEN
    assert out.binds is False
    assert out.relation == "transposes"       # the edge was found...
    assert "cannot" in out.reason.lower()     # ...but the incorporator can't bind


def test_soft_law_incorporator_ceiling_blocks_binding():
    directive = _directive("32019L0790")
    # A soft-law "incorporator" claims BINDING, but its class ceiling is INTERPRETIVE.
    soft = _stmt("guidance", SourceClass.SOFT_LAW, effect=Effect.INTERPRETIVE,
                 relations=[("transposes", "32019L0790")])
    out = incorporate(directive, soft)
    assert out.verdict is Verdict.OPEN
    assert out.binds is False


def test_incorporation_relations_are_the_transposes_incorporates_subset():
    assert INCORPORATION_RELATIONS == frozenset({"transposes", "incorporates"})


# ── resolve_reference: consume crossref's resolvers, honest on a miss ────────────

def test_resolve_by_celex():
    ref = resolve_reference("32024R1689")
    assert ref is not None
    assert ref.code == "ai-act"


def test_resolve_by_short_name():
    ref = resolve_reference("GDPR")
    assert ref is not None
    assert ref.code == "gdpr"


def test_resolve_by_full_citation_number():
    ref = resolve_reference("Regulation (EU) 2016/679")
    assert ref is not None
    assert ref.code == "gdpr"


def test_resolve_national_law_without_celex():
    ref = resolve_reference("UrhG")
    assert ref is not None
    assert ref.code == "urhg"
    assert ref.celex == ""


def test_unresolvable_citation_is_none():
    assert resolve_reference("Regulation (EU) 9999/99") is None


def test_blank_citation_is_none():
    assert resolve_reference("") is None
    assert resolve_reference("   ") is None


def test_host_self_reference_yields_none():
    host = "This Regulation (EU) 2016/679 (GDPR) lays down rules on data protection."
    assert resolve_reference("GDPR", host=host) is None


def test_host_does_not_drop_outbound_reference():
    host = "This Regulation (EU) 2016/679 (GDPR) lays down rules on data protection."
    ref = resolve_reference("AI Act", host=host)
    assert ref is not None
    assert ref.code == "ai-act"
