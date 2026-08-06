# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Referral classification: Rechtsgrundverweisung (imports the target's
CONDITIONS) vs Rechtsfolgenverweisung (imports only its CONSEQUENCE), drawn
deterministically over closed cue sets — with explicit UNCERTAIN escalation
on both no-cue and conflicting-cue text, never a guessed kind."""
from __future__ import annotations

from loomground_legal.citation import Citation
from loomground_legal.referral import (
    RECHTSFOLGE_CUES,
    RECHTSGRUND_CUES,
    ReferralClassification,
    classify_referral,
)


# ── Rechtsgrundverweisung: imports the target norm's CONDITIONS ───────────────

def test_gilt_entsprechend_is_rechtsgrundverweisung():
    r = classify_referral("Art 823 gilt entsprechend.")
    assert r.kind == "rechtsgrundverweisung"
    assert r.cue == "gilt entsprechend"
    assert r.reason == "grund-cue matched"
    # Target resolved via the consumed citation.resolve_xref.
    assert r.target == Citation(article="823")


def test_entsprechende_anwendung_is_rechtsgrund():
    r = classify_referral("Auf diesen Fall findet Art 433 entsprechende Anwendung.")
    assert r.kind == "rechtsgrundverweisung"
    assert r.target == Citation(article="433")


# ── Rechtsfolgenverweisung: imports only the CONSEQUENCE ──────────────────────

def test_mit_der_massgabe_is_rechtsfolgenverweisung():
    r = classify_referral("Art 249 gilt mit der Maßgabe, dass ...")
    assert r.kind == "rechtsfolgenverweisung"
    assert r.reason == "folge-cue matched"
    # ß-folding: the "Maßgabe" surface matches the "massgabe" cue.
    assert r.cue in RECHTSFOLGE_CUES
    assert "massgabe" in r.cue


def test_ss_folding_is_symmetric():
    # The ss-spelling of the same cue classifies identically.
    r = classify_referral("Art 249 gilt mit der Massgabe, dass ...")
    assert r.kind == "rechtsfolgenverweisung"
    assert "massgabe" in r.cue


# ── explicit UNCERTAIN escalation (never a guess) ─────────────────────────────

def test_no_cue_is_uncertain_escalate():
    r = classify_referral("Es gelten die Vorschriften des Art 1004.")
    assert r.kind == "uncertain"
    assert r.cue == ""
    assert r.reason == "no cue"
    # Escalation does not suppress a resolvable target.
    assert r.target == Citation(article="1004")


def test_conflicting_cues_are_uncertain():
    r = classify_referral(
        "Art 249 gilt entsprechend, jedoch mit der Maßgabe, dass ..."
    )
    assert r.kind == "uncertain"
    assert r.cue == ""
    assert r.reason == "conflicting cues"


# ── target sourcing: supplied target vs resolve_xref ──────────────────────────

def test_explicit_target_overrides_resolution_and_unparseable_target_is_none():
    # § 823 is not in the citation grammar, so resolve_xref returns None; the
    # supplied target is used instead, and the classification is unaffected.
    supplied = Citation(article="823")
    r = classify_referral("§ 823 gilt entsprechend", target=supplied)
    assert r.kind == "rechtsgrundverweisung"
    assert r.target is supplied

    # No parseable citation and no supplied target: kind still classifies,
    # target is None (resolve_xref returned None).
    r2 = classify_referral("gilt entsprechend")
    assert r2.kind == "rechtsgrundverweisung"
    assert r2.target is None


def test_instrument_flows_into_resolved_target():
    r = classify_referral("Art 4(1) gilt entsprechend", instrument="GDPR")
    assert r.kind == "rechtsgrundverweisung"
    assert r.target == Citation(instrument="GDPR", article="4", paragraph="1")


# ── the cue sets are a fail-closed, closed vocabulary ─────────────────────────

def test_cue_families_are_disjoint():
    # The import-time assert guards this; assert it here too so drift is caught
    # by the suite, not only at import.
    assert RECHTSGRUND_CUES.isdisjoint(RECHTSFOLGE_CUES)


def test_classification_is_frozen():
    r = classify_referral("Art 823 gilt entsprechend.")
    assert isinstance(r, ReferralClassification)
    import dataclasses

    try:
        r.kind = "uncertain"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        pass
    else:  # pragma: no cover
        raise AssertionError("ReferralClassification must be frozen")
