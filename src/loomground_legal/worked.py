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

from loomground_solver import Dimension, compose_paths
from loomground_solver.cross_subsumption import Verdict, fold_verdicts
from loomground_solver.reasoning import Edge

from . import legal_field
from .source_classes import Effect, SourceClass, max_effect, self_executes

__all__ = ["Review", "administrative_review"]


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
       ``OPEN`` (formell rechtswidrig — the acting office is not competent).
    2. **Legal basis** (Vorbehalt des Gesetzes) — the authorizing norm must be a
       BINDING, self-executing source (``source_classes``); absent or insufficient
       → ``OPEN``.
    3. **Ermessen** — discretion is the authority's; the engine SURFACES it
       (``OPEN``), it does not substitute its own choice.

    Folds via the solver's OPEN-dominant ``fold_verdicts``: any ``OPEN`` → the
    whole review is ``OPEN`` (escalate)."""
    field = legal_field.get("administrative")
    reasons: list[str] = []

    # (1) competence: reachability over the delegation edges (RELATIONAL)
    if authorizing_authority == acting_office:
        competence = Verdict.SATISFIED
    else:
        edges = [Edge(s, "delegates", o, Dimension.RELATIONAL)
                 for s, o in competence_edges]
        paths = compose_paths(edges, start=authorizing_authority, min_hops=1)
        reached = any(inf.object == acting_office for inf in paths)
        competence = Verdict.SATISFIED if reached else Verdict.OPEN
        if not reached:
            reasons.append(
                f"competence: no delegation chain from {authorizing_authority!r} to "
                f"{acting_office!r} composes — formell rechtswidrig (escalate)")

    # (2) legal basis: Vorbehalt des Gesetzes — a binding, self-executing source
    if authorizing_source is None:
        legal_basis = Verdict.OPEN
        reasons.append("legal basis: no Ermächtigungsgrundlage — Vorbehalt des "
                       "Gesetzes unmet (escalate)")
    elif max_effect(authorizing_source) is Effect.BINDING and self_executes(authorizing_source):
        legal_basis = Verdict.SATISFIED
    else:
        legal_basis = Verdict.OPEN
        reasons.append(
            f"legal basis: {authorizing_source.value} is not a binding self-executing "
            f"source — insufficient Ermächtigungsgrundlage (escalate)")

    checks = [competence, legal_basis]
    if ermessen:
        checks.append(Verdict.OPEN)
        reasons.append(f"Ermessen: discretion is the authority's ({field.escalation_bias[0]}) "
                       f"— surfaced, not substituted")

    return Review(fold_verdicts(checks), competence, legal_basis, tuple(reasons))
