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
    constitutional_review,
    criminal_review,
    select_version,
)
from loomground_legal.lifecycle import LifecycleEvent
from loomground_solver import Alternative, PrincipleWeight
from loomground_solver.cross_subsumption import Verdict


def _prop_inputs(*, suitable=True, side_i_intensity="serious", side_j_intensity="light"):
    """Proportionality kwargs for a rights measure vs a public interest. Triadic
    labels are light/moderate/serious throughout."""
    return dict(
        aim="public safety", legitimate=True, suitable=suitable,
        means_effectiveness="serious", means_intrusiveness="moderate",
        alternatives=(Alternative(label="milder", effectiveness="light",
                                  intrusiveness="light"),),
        # side_i = the promoted public interest; side_j = the burdened right
        side_i=PrincipleWeight(label="public_interest", intensity=side_i_intensity,
                               abstract_weight="moderate", reliability="serious"),
        side_j=PrincipleWeight(label="right", intensity=side_j_intensity,
                               abstract_weight="moderate", reliability="serious"))

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


def test_broken_competence_chain_is_a_determinate_defect() -> None:
    # the acting office is not reachable from the authority → formell rechtswidrig,
    # a determinate defect (the act does not stand), NOT an escalation
    r = administrative_review(
        authorizing_authority="supervisor", acting_office="rogue_office",
        competence_edges=_CHAIN,
        authorizing_source=SourceClass.NATIONAL_STATUTE)
    assert r.competence is Verdict.NOT_SATISFIED
    assert r.verdict is Verdict.NOT_SATISFIED and not r.escalates
    assert any("formell rechtswidrig" in x for x in r.reasons)


def test_missing_legal_basis_is_a_determinate_defect() -> None:
    r = administrative_review(
        authorizing_authority="supervisor", acting_office="office",
        competence_edges=_CHAIN, authorizing_source=None)
    assert r.legal_basis is Verdict.NOT_SATISFIED and r.verdict is Verdict.NOT_SATISFIED
    assert any("Vorbehalt des Gesetzes" in x for x in r.reasons)


def test_soft_law_basis_is_insufficient() -> None:
    # soft law can never carry BINDING force → no valid Ermächtigungsgrundlage
    r = administrative_review(
        authorizing_authority="supervisor", acting_office="office",
        competence_edges=_CHAIN, authorizing_source=SourceClass.SOFT_LAW)
    assert r.legal_basis is Verdict.NOT_SATISFIED and r.verdict is Verdict.NOT_SATISFIED


def test_ermessen_is_surfaced_not_substituted() -> None:
    r = administrative_review(
        authorizing_authority="supervisor", acting_office="office",
        competence_edges=_CHAIN,
        authorizing_source=SourceClass.NATIONAL_STATUTE, ermessen=True)
    assert r.escalates                                     # discretion → OPEN
    assert any("Ermessen" in x for x in r.reasons)


def test_review_never_satisfies_a_defective_act() -> None:
    # the fabrication-0 invariant: a defective act is never SATISFIED — an
    # incompetent authority and/or a missing basis → NOT_SATISFIED (never 'valid')
    for src in (None, SourceClass.SOFT_LAW):
        r = administrative_review(
            authorizing_authority="supervisor", acting_office="rogue_office",
            competence_edges=_CHAIN, authorizing_source=src)
        assert r.verdict is Verdict.NOT_SATISFIED


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


# ── worked criminal review: three-tier, in dubio pro reo = OPEN dominates ─────

def test_vorsatz_attributable_unjustified_is_guilty() -> None:
    r = criminal_review(conduct_matches=True, attribution="attributable",
                        mens_rea="vorsatz")
    assert r.verdict is Verdict.SATISFIED and not r.escalates


def test_contested_mens_rea_escalates_never_convicts() -> None:
    # dolus eventualis vs bewusste Fahrlässigkeit unresolved → OPEN, not a conviction
    r = criminal_review(conduct_matches=True, attribution="attributable",
                        mens_rea="contested")
    assert r.mens_rea is Verdict.OPEN and r.escalates
    assert any("mens rea contested" in x for x in r.reasons)


def test_contested_attribution_escalates() -> None:
    # atypical causal course → objektive Zurechnung open → OPEN
    r = criminal_review(conduct_matches=True, attribution="contested",
                        mens_rea="vorsatz")
    assert r.objektiver_tatbestand is Verdict.OPEN and r.escalates


def test_negligence_for_a_vorsatzdelikt_is_not_guilty() -> None:
    r = criminal_review(conduct_matches=True, attribution="attributable",
                        mens_rea="fahrlaessigkeit", offense_requires="vorsatz")
    assert r.mens_rea is Verdict.NOT_SATISFIED
    assert r.verdict is Verdict.NOT_SATISFIED         # not guilty, not 'open'


def test_justification_defeats_the_charge() -> None:
    # Notwehr etc. → not unlawful → charge fails (NOT_SATISFIED)
    r = criminal_review(conduct_matches=True, attribution="attributable",
                        mens_rea="vorsatz", justification=True)
    assert r.unlawful is Verdict.NOT_SATISFIED and r.verdict is Verdict.NOT_SATISFIED


def test_broken_attribution_is_not_guilty_not_open() -> None:
    r = criminal_review(conduct_matches=True, attribution="not_attributable",
                        mens_rea="vorsatz")
    assert r.objektiver_tatbestand is Verdict.NOT_SATISFIED
    assert r.verdict is Verdict.NOT_SATISFIED


def test_justification_dominates_a_contested_tatbestand() -> None:
    # a valid defence acquits determinately — even with a contested objektive
    # Zurechnung, the charge fails NOT_SATISFIED (not guilty), not OPEN (escalate)
    r = criminal_review(conduct_matches=True, attribution="contested",
                        mens_rea="contested", justification=True)
    assert r.verdict is Verdict.NOT_SATISFIED and not r.escalates


def test_criminal_never_convicts_while_a_tier_is_open() -> None:
    # the fabrication-0 invariant, criminal edition: a contested element can never
    # yield SATISFIED (guilty) — doubt is surfaced, guilt is never fabricated
    r = criminal_review(conduct_matches=True, attribution="contested",
                        mens_rea="contested")
    assert r.verdict is Verdict.OPEN


# ── worked constitutional review: runs the REAL proportionality op ───────────

def test_outside_schutzbereich_the_right_is_not_engaged() -> None:
    r = constitutional_review(in_schutzbereich=False, eingriff=True)
    assert r.verdict is Verdict.SATISFIED and r.proportionality is None


def test_no_eingriff_no_infringement() -> None:
    r = constitutional_review(in_schutzbereich=True, eingriff=False)
    assert r.verdict is Verdict.SATISFIED


def test_wesensgehalt_touched_is_unconstitutional() -> None:
    r = constitutional_review(in_schutzbereich=True, eingriff=True,
                              touches_wesensgehalt=True)
    assert r.verdict is Verdict.NOT_SATISFIED         # absolute bar, no balancing
    assert any("Wesensgehalt" in x for x in r.reasons)


def test_proportionate_measure_is_justified() -> None:
    # public interest clearly outweighs the burdened right → op does NOT escalate
    r = constitutional_review(in_schutzbereich=True, eingriff=True,
                              proportionality_inputs=_prop_inputs())
    assert r.verdict is Verdict.SATISFIED
    assert r.proportionality is not None and not r.proportionality.escalated()


def test_balancing_tie_escalates_never_a_coin_flip() -> None:
    # equal weights → W == 1 → the op escalates → the review is OPEN (court's call)
    r = constitutional_review(
        in_schutzbereich=True, eingriff=True,
        proportionality_inputs=_prop_inputs(side_i_intensity="light",
                                            side_j_intensity="light"))
    assert r.verdict is Verdict.OPEN and r.proportionality.escalated()
    assert any("did not settle" in x for x in r.reasons)


def test_failed_prong_escalates() -> None:
    # an unsuitable means fails a prong → the op escalates → OPEN
    r = constitutional_review(in_schutzbereich=True, eingriff=True,
                              proportionality_inputs=_prop_inputs(suitable=False))
    assert r.verdict is Verdict.OPEN


def test_no_proportionality_inputs_escalates_honestly() -> None:
    r = constitutional_review(in_schutzbereich=True, eingriff=True)
    assert r.verdict is Verdict.OPEN                  # cannot run the Abwägung → escalate
