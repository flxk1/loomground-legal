# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The legal-analysis front door — one call that runs a scenario through the whole
grammar → algebra → system stack: **recognition then adjudication**.

`analyse(statements, facts)` sequences the two secondary-rule steps that bracket
the reasoning, re-growing nothing:

  1. **recognition** (Hart's rule of recognition) — every statement is passed
     through ``grammar.validate``. An **ill-formed** statement (a standard claiming
     BINDING, a directive asserted binding with no incorporation edge, an
     inadmissible relation, an unrecognised operative content) is **excluded from
     the reasoning** and recorded — the engine never reasons over law it cannot
     recognise as well-formed.
  2. **adjudication** — the well-formed statements are adjudicated against the
     facts by ``system.adjudicate`` (derive → resolve → terminal). The terminal is
     that adjudication's, with the honesty spine intact end-to-end: an OPEN
     antecedent (a presupposed/incomplete fact) or an unseparable collision → OPEN
     (escalate); nothing well-formed to apply → OPEN.

This is the operational proof that the three layers COMPOSE into a legal analysis:
statements are recognised, applied to facts, and disputes resolved — every
unsettled point ⊥ → escalate, never a fabricated result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence, Tuple

from loomground_solver.cross_subsumption import FactSpace, Verdict

from .grammar import LegalStatement, WellFormedness, validate
from .system import Adjudication, adjudicate

__all__ = ["Analysis", "analyse"]


@dataclass(frozen=True)
class Analysis:
    """A full legal analysis of a scenario. ``verdict`` is the terminal:

      * ``SATISFIED`` — a consequence fired (and any collision was determinately
        resolved) over the recognised statements;
      * ``NOT_SATISFIED`` — recognised statements exist but none applies to the facts;
      * ``OPEN`` (escalate) — an OPEN antecedent / an unseparable collision, OR no
        statement was well-formed enough to reason with.

    ``recognised`` pairs each statement with its :class:`WellFormedness`;
    ``ill_formed`` are the ones excluded from the reasoning; ``adjudication`` is the
    :class:`Adjudication` over the well-formed ones (``None`` when none were)."""
    verdict: Verdict
    recognised: Tuple[Tuple[LegalStatement, WellFormedness], ...]
    ill_formed: Tuple[LegalStatement, ...]
    adjudication: Optional[Adjudication]

    @property
    def escalates(self) -> bool:
        return self.verdict is Verdict.OPEN


def analyse(statements: Sequence[LegalStatement], facts: FactSpace, *,
            act: Optional[str] = None,
            specificity: Optional[Mapping[str, int]] = None,
            times: Optional[Mapping[str, int]] = None,
            system: Optional[str] = None) -> Analysis:
    """Run a scenario through recognition → adjudication (see the module docstring).
    ``act`` / ``specificity`` / ``times`` / ``system`` are forwarded to
    ``system.adjudicate`` for the conflict step. Nothing is re-grown: recognition
    is ``grammar.validate``, adjudication is ``system.adjudicate`` over the
    algebra."""
    recognised: list = []
    ill_formed: list = []
    well_formed: list = []
    for s in statements:
        wf = validate(s)
        recognised.append((s, wf))
        (well_formed if wf.well_formed else ill_formed).append(s)

    if not well_formed:
        # no recognisable law to apply → escalate; never reason over ill-formed law
        return Analysis(Verdict.OPEN, tuple(recognised), tuple(ill_formed), None)

    adj = adjudicate(well_formed, facts, act=act, specificity=specificity,
                     times=times, system=system)
    return Analysis(adj.verdict, tuple(recognised), tuple(ill_formed), adj)
