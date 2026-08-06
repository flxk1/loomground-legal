# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Referral classification — Rechtsgrund- vs Rechtsfolgenverweisung.

A referring provision points at another norm, but the two German referral
kinds pull in different things:

* **Rechtsgrundverweisung** — imports the target norm's *conditions*
  (Tatbestand): the referring case only applies when the target's own
  requirements are met. Cued by ``"gilt entsprechend"`` / ``"entsprechende
  Anwendung"`` and kin.
* **Rechtsfolgenverweisung** — imports only the target norm's legal
  *consequence* (Rechtsfolge), regardless of whether the target's conditions
  hold. Cued by ``"mit der Maßgabe"`` / ``"gilt als"`` and kin.

Getting this wrong changes the outcome of a case, so the classifier is
deterministic over closed cue sets and **never guesses**: exactly one cue
family present picks that kind; no cue present escalates as ``uncertain``;
both families present is a genuine conflict and also escalates as
``uncertain``. The referral *target* is resolved by consuming
:func:`loomground_legal.citation.resolve_xref` (or taken from a supplied
:class:`~loomground_legal.citation.Citation`), but the classification itself
never depends on whether a target could be parsed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional

from loomground_legal.citation import Citation, resolve_xref

__all__ = [
    "ReferralKind",
    "RECHTSGRUND_CUES",
    "RECHTSFOLGE_CUES",
    "ReferralClassification",
    "classify_referral",
]

ReferralKind = Literal["rechtsgrundverweisung", "rechtsfolgenverweisung", "uncertain"]

# ── closed cue sets (normalised: casefolded, ß→ss) ───────────────────────────
# A Rechtsgrundverweisung imports the target norm's CONDITIONS (Tatbestand).
RECHTSGRUND_CUES: frozenset = frozenset(
    {
        "gilt entsprechend",
        "gelten entsprechend",
        "entsprechende anwendung",
        "entsprechend anzuwenden",
        "sinngemaess",
        "entsprechend gelten",
    }
)

# A Rechtsfolgenverweisung imports only the target norm's CONSEQUENCE.
RECHTSFOLGE_CUES: frozenset = frozenset(
    {
        "mit der massgabe",
        "gilt als",
        "gelten als",
        "zu behandeln",
        "anwendung mit der massgabe",
    }
)


def _normalise(text: str) -> str:
    """Casefold and fold ``ß`` → ``ss`` so ``Maßgabe`` / ``Massgabe`` and
    ``sinngemäß`` / ``sinngemaess`` compare equal."""
    return text.casefold().replace("ß", "ss")


def _hits(text_cf: str, cues: frozenset) -> List[str]:
    """The cues from ``cues`` that occur as substrings of the already
    normalised ``text_cf`` (see :func:`_normalise`)."""
    return [cue for cue in cues if cue in text_cf]


# Fail-closed on cue drift: the two families must never share a phrase, or a
# single hit would count for both kinds and the disjointness the classifier
# relies on would silently break.
assert RECHTSGRUND_CUES.isdisjoint(RECHTSFOLGE_CUES), (
    "referral cue families must be disjoint; overlap: "
    f"{sorted(RECHTSGRUND_CUES & RECHTSFOLGE_CUES)}"
)


@dataclass(frozen=True)
class ReferralClassification:
    """The classification of a referring provision.

    ``kind`` is one of the three :data:`ReferralKind` literals. ``target`` is
    the resolved referral target (``None`` when the text carries no parseable
    citation and none was supplied). ``cue`` is the matched cue phrase, and is
    ``''`` when ``kind == 'uncertain'``. ``reason`` is a short human-readable
    basis for the decision."""

    kind: ReferralKind
    target: Optional[Citation]
    cue: str
    reason: str


def classify_referral(
    text: str, *, instrument: str = "", target: Optional[Citation] = None
) -> ReferralClassification:
    """Classify a referring provision as Rechtsgrund- or Rechtsfolgenverweisung.

    A **Rechtsgrundverweisung** imports the referenced norm's *conditions*
    (Tatbestand); a **Rechtsfolgenverweisung** imports only its legal
    *consequence* (Rechtsfolge). The distinction is drawn by matching
    casefolded, ``ß``-folded cue phrases in ``text`` against the two closed
    cue sets.

    The referral target is ``target`` when supplied, else
    :func:`loomground_legal.citation.resolve_xref` applied to ``text`` (which
    may be ``None``). The classification does **not** depend on the target.

    Deterministic rule, never a guess:

    * exactly one cue family present → that kind, with the matched cue;
    * no cue present → ``uncertain`` (``reason='no cue'``), escalated;
    * both families present → ``uncertain`` (``reason='conflicting cues'``) —
      the ambiguity is surfaced, never resolved by guessing.
    """
    resolved_target = target if target is not None else resolve_xref(
        text, instrument=instrument
    )

    text_cf = _normalise(text)
    grund_hits = _hits(text_cf, RECHTSGRUND_CUES)
    folge_hits = _hits(text_cf, RECHTSFOLGE_CUES)

    if grund_hits and folge_hits:
        return ReferralClassification(
            kind="uncertain",
            target=resolved_target,
            cue="",
            reason="conflicting cues",
        )
    if grund_hits:
        return ReferralClassification(
            kind="rechtsgrundverweisung",
            target=resolved_target,
            cue=min(grund_hits),
            reason="grund-cue matched",
        )
    if folge_hits:
        return ReferralClassification(
            kind="rechtsfolgenverweisung",
            target=resolved_target,
            cue=min(folge_hits),
            reason="folge-cue matched",
        )
    return ReferralClassification(
        kind="uncertain",
        target=resolved_target,
        cue="",
        reason="no cue",
    )
