# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Worked reviews — where the branch profile, competence, legal basis, and
intertemporal selection COMPOSE into one graded legal conclusion.

The per-module tests prove each piece in isolation; this is the operational
entry point that runs them together on a real scenario, with the honesty spine
intact: **OPEN (escalate) is a first-class, correct terminal** — the mechanical
form of "es kommt darauf an" — never a fabricated resolution. The verdict
vocabulary and the OPEN-dominant fold are the solver's (``cross_subsumption``),
consumed here, not re-grown; competence composition is the solver's
``compose_paths``; legal force is the plane's own ``source_classes``.

Administrative review answers, grounded: *may this office act (competence),
on what basis (Vorbehalt des Gesetzes), and where is the choice the authority's
to make (Ermessen)* — surfacing the open, never substituting a discretion call.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from loomground_solver import Dimension, ProportionalityResult, compose_paths, proportionality
from loomground_solver.cross_subsumption import (
    AntecedentVerdict, Condition, FactSpace, Verdict, fold_verdicts, subsume_antecedent,
)
from loomground_solver.reasoning import Edge

from . import legal_field
from .source_classes import Effect, SourceClass, max_effect, self_executes

__all__ = [
    "Review", "administrative_review",
    "CriminalReview", "criminal_review",
    "ConstitutionalReview", "constitutional_review",
    "SubsumptionReview", "review_against_facts",
]


@dataclass(frozen=True)
class Review:
    """The graded outcome of an administrative-act review: the folded verdict,
    the per-check verdicts, and the escalation reasons. ``OPEN`` is the honest
    escalate terminal (es kommt darauf an), never a fabricated 'valid'."""
    verdict: Verdict
    competence: Verdict
    legal_basis: Verdict
    reasons: Tuple[str, ...]
    field: str = "administrative"

    @property
    def escalates(self) -> bool:
        return self.verdict is Verdict.OPEN


def administrative_review(*, authorizing_authority: str, acting_office: str,
                          competence_edges: Sequence[Tuple[str, str]],
                          authorizing_source: Optional[SourceClass],
                          ermessen: bool = False) -> Review:
    """Review an administrative act under the ``administrative`` branch profile.

    1. **Competence** — is ``acting_office`` reachable from ``authorizing_authority``
       over the delegation chain (``compose_paths``)? A non-composing chain →
       ``NOT_SATISFIED`` (formell rechtswidrig — a determinate defect, closed-world
       over the supplied chain).
    2. **Legal basis** (Vorbehalt des Gesetzes) — the authorizing norm must be a
       BINDING, self-executing source (``source_classes``); absent or insufficient
       → ``NOT_SATISFIED`` (the act cannot stand).
    3. **Ermessen** — discretion is the authority's; the engine SURFACES it
       (``OPEN``), it does not substitute its own choice.

    Folds via the solver's OPEN-dominant ``fold_verdicts``: a determinate defect →
    ``NOT_SATISFIED`` (the act does not stand); genuine discretion → ``OPEN``
    (escalate); competent + based + no discretion → ``SATISFIED``."""
    field = legal_field.get("administrative")
    reasons: list[str] = []

    # (1) competence: reachability over the delegation edges (RELATIONAL). A
    # non-composing chain is a DETERMINATE defect — the act is formell rechtswidrig
    # (closed-world over the supplied chain), not an escalation.
    if authorizing_authority == acting_office:
        competence = Verdict.SATISFIED
    else:
        edges = [Edge(s, "delegates", o, Dimension.RELATIONAL)
                 for s, o in competence_edges]
        paths = compose_paths(edges, start=authorizing_authority, min_hops=1)
        reached = any(inf.object == acting_office for inf in paths)
        competence = Verdict.SATISFIED if reached else Verdict.NOT_SATISFIED
        if not reached:
            reasons.append(
                f"competence: no delegation chain from {authorizing_authority!r} to "
                f"{acting_office!r} composes — formell rechtswidrig")

    # (2) legal basis: Vorbehalt des Gesetzes — a binding, self-executing source.
    # Absent or insufficient is a DETERMINATE defect (the act cannot stand).
    if authorizing_source is None:
        legal_basis = Verdict.NOT_SATISFIED
        reasons.append("legal basis: no Ermächtigungsgrundlage — Vorbehalt des "
                       "Gesetzes unmet")
    elif max_effect(authorizing_source) is Effect.BINDING and self_executes(authorizing_source):
        legal_basis = Verdict.SATISFIED
    else:
        legal_basis = Verdict.NOT_SATISFIED
        reasons.append(
            f"legal basis: {authorizing_source.value} is not a binding self-executing "
            f"source — insufficient Ermächtigungsgrundlage")

    checks = [competence, legal_basis]
    if ermessen:
        checks.append(Verdict.OPEN)
        reasons.append(f"Ermessen: discretion is the authority's ({field.escalation_bias[0]}) "
                       f"— surfaced, not substituted")

    return Review(fold_verdicts(checks), competence, legal_basis, tuple(reasons))


@dataclass(frozen=True)
class CriminalReview:
    """The graded outcome of a criminal review under the three-tier Aufbau.
    ``verdict``: guilty = ``SATISFIED``, not-guilty = ``NOT_SATISFIED``, and a
    contested element = ``OPEN`` — the engine SURFACES doubt (whether to acquit on
    it is *in dubio pro reo*, the court's call), it never pronounces guilt on a
    contested element (fabrication 0)."""
    verdict: Verdict
    objektiver_tatbestand: Verdict     # conduct + objektive Zurechnung
    mens_rea: Verdict                  # subjektiver Tatbestand
    unlawful: Verdict                  # Rechtswidrigkeit (justification → not unlawful)
    reasons: Tuple[str, ...]
    field: str = "criminal"

    @property
    def escalates(self) -> bool:
        return self.verdict is Verdict.OPEN


def criminal_review(*, conduct_matches: bool, attribution: str, mens_rea: str,
                    offense_requires: str = "vorsatz",
                    justification: bool = False) -> CriminalReview:
    """Review a charge under the ``criminal`` branch profile's three tiers.

    - **objektiver Tatbestand** — ``conduct_matches`` AND objective attribution
      (``attribution`` ∈ ``attributable`` / ``contested`` / ``not_attributable``);
      a contested causal course (objektive Zurechnung) → ``OPEN``.
    - **subjektiver Tatbestand** (``mens_rea`` ∈ ``vorsatz`` / ``fahrlaessigkeit``
      / ``none`` / ``contested``) — must meet ``offense_requires``; a Vorsatzdelikt
      on negligence → ``NOT_SATISFIED``; the dolus-eventualis line → ``OPEN``.
    - **Rechtswidrigkeit** — a justification (Notwehr etc.) makes the deed not
      unlawful → the charge fails.

    Folds via the OPEN-dominant ``fold_verdicts``: any contested tier → the whole
    review is ``OPEN``, so a conviction is never returned on a contested element."""
    field = legal_field.get("criminal")
    reasons: list[str] = []

    # objektiver Tatbestand: conduct + objektive Zurechnung
    if not conduct_matches:
        obj = Verdict.NOT_SATISFIED
        reasons.append("objektiver Tatbestand: conduct does not fit the offence elements")
    elif attribution == "not_attributable":
        obj = Verdict.NOT_SATISFIED
        reasons.append("objektive Zurechnung: the risk did not realise in the result "
                       "(attribution broken)")
    elif attribution == "contested":
        obj = Verdict.OPEN
        reasons.append("objektive Zurechnung contested (atypical causal course) — escalate")
    else:
        obj = Verdict.SATISFIED

    # subjektiver Tatbestand: mens rea vs what the offence requires
    if mens_rea == "contested":
        mr = Verdict.OPEN
        reasons.append(f"mens rea contested ({field.escalation_bias[1]}) — escalate")
    elif mens_rea == "none":
        mr = Verdict.NOT_SATISFIED
        reasons.append("subjektiver Tatbestand: no mens rea")
    elif offense_requires == "vorsatz" and mens_rea == "fahrlaessigkeit":
        mr = Verdict.NOT_SATISFIED
        reasons.append("a Vorsatzdelikt is not made out on Fahrlässigkeit")
    else:
        mr = Verdict.SATISFIED

    # Rechtswidrigkeit: a valid justification (Notwehr etc.) DEFEATS the charge
    # determinately — a defence dominates an inculpatory OPEN, because 'not guilty'
    # is the settled outcome regardless of a contested Tatbestand element. It does
    # NOT fold OPEN-dominant into an escalation.
    if justification:
        reasons.append("Rechtswidrigkeit: a justification (Rechtfertigungsgrund) applies "
                       "— the deed is not unlawful; the charge fails (not guilty)")
        return CriminalReview(Verdict.NOT_SATISFIED, obj, mr, Verdict.NOT_SATISFIED,
                              tuple(reasons))
    # no justification → guilt requires objektiver + subjektiver Tatbestand (any
    # contested tier → OPEN, in dubio pro reo; never a conviction on doubt).
    return CriminalReview(fold_verdicts([obj, mr]), obj, mr, Verdict.SATISFIED,
                          tuple(reasons))


@dataclass(frozen=True)
class ConstitutionalReview:
    """The graded outcome of fundamental-rights review (Schutzbereich → Eingriff →
    Rechtfertigung). ``verdict``: the state measure is CONSTITUTIONAL = ``SATISFIED``
    (justified, or the right is not engaged); ``NOT_SATISFIED`` = unconstitutional
    (the Wesensgehalt is touched); ``OPEN`` = the Abwägung did not settle — the
    proportionality op escalates on a tie / failed prong, and the balancing is the
    court's, surfaced not decided (never a coin-flipped winner)."""
    verdict: Verdict
    schutzbereich: Verdict
    eingriff: bool
    proportionality: Optional[ProportionalityResult]   # None if not reached
    reasons: Tuple[str, ...]
    field: str = "constitutional"

    @property
    def escalates(self) -> bool:
        return self.verdict is Verdict.OPEN


def constitutional_review(*, in_schutzbereich: bool, eingriff: bool,
                          touches_wesensgehalt: bool = False,
                          proportionality_inputs: Optional[dict] = None
                          ) -> ConstitutionalReview:
    """Review a state measure against a fundamental right under the three-step
    Aufbau, delegating the justification balance to ``solver.proportionality``.

    1. **Schutzbereich** — outside the scope → the right is not engaged (the
       measure stands).
    2. **Eingriff** — no state intrusion → no infringement (the measure stands).
    3. **Rechtfertigung** — the Wesensgehalt (Art. 19(2)) is an absolute bar
       (touched → unconstitutional); otherwise run the real proportionality op —
       proportionate → justified (SATISFIED), a tie / failed prong → ``OPEN``
       (the Abwägung is the court's)."""
    field = legal_field.get("constitutional")

    if not in_schutzbereich:
        return ConstitutionalReview(
            Verdict.SATISFIED, Verdict.NOT_SATISFIED, eingriff, None,
            ("Schutzbereich: the conduct is outside the right's scope — the right is "
             "not engaged",))
    if not eingriff:
        return ConstitutionalReview(
            Verdict.SATISFIED, Verdict.SATISFIED, False, None,
            ("Eingriff: no state intrusion into the protected scope — no infringement",))
    if touches_wesensgehalt:
        return ConstitutionalReview(
            Verdict.NOT_SATISFIED, Verdict.SATISFIED, True, None,
            ("Wesensgehalt (Art. 19(2) GG): the measure touches the essence of the "
             "right — unconstitutional regardless of proportionality",))
    if proportionality_inputs is None:
        return ConstitutionalReview(
            Verdict.OPEN, Verdict.SATISFIED, True, None,
            ("Verhältnismäßigkeit: no proportionality inputs — the Abwägung cannot be "
             "run (escalate)",))

    pr = proportionality(**proportionality_inputs)
    if pr.escalated():
        failed = next((p.prong for p in pr.prongs if not p.passed), "stricto-sensu tie")
        return ConstitutionalReview(
            Verdict.OPEN, Verdict.SATISFIED, True, pr,
            (f"Verhältnismäßigkeit: the Abwägung did not settle ({field.escalation_bias[0]}; "
             f"at {failed}) — escalate; balancing is the court's, not the engine's",))
    return ConstitutionalReview(
        Verdict.SATISFIED, Verdict.SATISFIED, True, pr,
        (f"Verhältnismäßigkeit: proportionate ({pr.prevailing} prevails) — the measure "
         f"is justified",))


@dataclass(frozen=True)
class SubsumptionReview:
    """A branch antecedent subsumed against a 5D+nD ``FactSpace`` — the folded
    verdict plus every per-condition :class:`DimVerdict`. ``OPEN`` propagates:
    one condition resting on presupposed-but-ungrounded data opens the whole."""
    verdict: Verdict
    per_condition: Tuple                        # tuple[DimVerdict]
    field: str

    @property
    def escalates(self) -> bool:
        return self.verdict is Verdict.OPEN


def review_against_facts(field_code: str, conditions: Sequence[Condition],
                         facts: FactSpace) -> SubsumptionReview:
    """Subsume a branch's antecedent ``conditions`` against a 5D+nD ``FactSpace``
    — the dimension-tagged, grounded data that **versum** produces — using the
    solver's cross-dimensional subsumption. This is the seam where *versum's data
    lives in solver's reasoning*: each condition is routed to its dimension's
    evaluator (structural reachability, causal grounded-edges, temporal Date,
    relational algebra, else the closed-world literal) over the matching field of
    the FactSpace.

    The honesty spine is versum's incompleteness, propagated: the FactSpace's
    ``incomplete_causal`` / ``incomplete_structural`` channels mark what a
    construction *presupposed but never grounded*, so a condition resting on such
    a region is **OPEN** — never a fabricated SATISFIED, and (crucially) distinct
    from a closed-world **NOT_SATISFIED** where the taxonomy is known-complete.
    The antecedent folds OPEN-dominant (``subsume_antecedent``); the branch
    profile (``field_code``) selects which conditions and dimensions apply."""
    legal_field.get(field_code)                 # fail-closed: unknown branch → KeyError
    av: AntecedentVerdict = subsume_antecedent(conditions, facts)
    return SubsumptionReview(av.verdict, av.conditions, field_code)
