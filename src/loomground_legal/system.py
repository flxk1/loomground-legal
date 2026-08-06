# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The legal SYSTEM layer — Hart's SECONDARY rules made explicit ops.

The plane's legal grammar/algebra has three layers: **statement** (``grammar``:
the well-formed unit + the rule of RECOGNITION, ``validate``), **algebra**
(``algebra``: apply / derive / resolve — composition), and — here — the
**SYSTEM**: the secondary rules by which a legal order reproduces and applies
*itself*. Hart's three secondary rules, one op-family each:

  * **recognition** — already built: :func:`grammar.validate` is the rule of
    recognition (is this a well-formed member of the system?). This module does
    NOT re-grow it; adjudication assumes its inputs already passed recognition.
  * **change** — :func:`enact` (is a statement in force at a time?) and
    :func:`supersede` (which of two lineage members governs facts at a time?):
    how norms are created, amended, and retired over time. All time logic is
    :mod:`intertemporal` / :mod:`lifecycle`'s; this module only *asks* them.
  * **adjudication** — :func:`adjudicate`: the end-to-end dispute pipeline
    (derive → resolve → terminal). All firing is :func:`algebra.derive`'s and
    all conflict resolution is :func:`algebra.resolve`'s (the solver's
    ``LEX_CONFLICT_PACK``); this module only sequences them and reads the
    terminal.

The honesty spine is load-bearing and shared with every layer: **OPEN /
escalate is a first-class, correct terminal** — the mechanical "es kommt darauf
an". A contested intertemporal choice (echte Rückwirkung / no governing
version) escalates; an OPEN antecedent or a genuine collision the pack cannot
separate escalates. ⊥ → escalate, never a fabricated resolution.

Consumes, re-grows nothing: the verdict vocabulary is the solver's
``cross_subsumption.Verdict``; time is intertemporal/lifecycle; firing and
conflict are the algebra's. Pure stdlib on top of those.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence, Tuple

from loomground_solver.cross_subsumption import FactSpace, Verdict

from . import algebra, intertemporal
from .algebra import Conclusion, Derivation
from .grammar import LegalStatement
from .intertemporal import TemporalIndex
from .lifecycle import LifecycleEvent, in_force
from .sources import ConflictOutcome

__all__ = [
    "Enactment",
    "enact",
    "Supersession",
    "supersede",
    "Adjudication",
    "adjudicate",
]


# ── rule of CHANGE ────────────────────────────────────────────────────────────

def _member(statement: LegalStatement) -> str:
    """The lineage token a statement's temporal validity is keyed on — its
    versioned ``expression_id`` if present, else the bare ``source`` (a norm with
    no recorded versioning is its own single-member lineage)."""
    return statement.expression_id or statement.source


@dataclass(frozen=True)
class Enactment:
    """Whether a statement is in force at a time (the rule of change, side of
    persistence). ``verdict`` is ``SATISFIED`` when the statement's own version
    is the one in force, ``NOT_SATISFIED`` when it is out of force at ``at`` —
    superseded, repealed, or not yet enacted (a determinate answer, closed over
    the recorded lifecycle events). ``governing`` names the version the lineage
    actually puts in force at ``at`` (``None`` if none is), so a NOT_SATISFIED
    can say *which* successor displaced it."""

    statement: LegalStatement
    at: str
    in_force: bool
    verdict: Verdict
    governing: Optional[str]
    reason: str

    @property
    def escalates(self) -> bool:
        return self.verdict is Verdict.OPEN


def enact(statement: LegalStatement, events: Sequence[LifecycleEvent], *,
          at: str, enacted: Optional[Mapping[str, str]] = None) -> Enactment:
    """Is ``statement`` in force at ``at``? Delegates to the lifecycle/intertemporal
    surfaces — no version or date logic re-grown:

      * :func:`lifecycle.in_force` — is this statement's own version out of force
        (superseded/repealed on-or-before ``at``, or not yet enacted)?
      * :func:`intertemporal.governing_version` — which version of the lineage IS
        in force at ``at`` (so a NOT_SATISFIED names the displacing successor).

    A statement whose version is not in force **does not apply** — that is a
    determinate ``NOT_SATISFIED`` (closed-world over the events), never a
    fabricated firing and never an escalation. (A lifecycle record with more than
    one member in force at ``at`` is an inconsistency the consumed
    ``version_in_force`` raises on — fail-closed, not smoothed over here.)"""
    member = _member(statement)
    active = in_force(member, events, at, enacted=enacted)
    governing = intertemporal.governing_version(
        member, events, event_time=at, enacted=enacted)
    if active:
        return Enactment(statement, at, True, Verdict.SATISFIED, governing,
                         f"{member!r} is in force at {at}")
    if governing is None:
        reason = (f"{member!r} is not in force at {at}: no version of its lineage "
                  f"is in force (not yet enacted, or the whole line is retired)")
    else:
        reason = (f"{member!r} is not in force at {at}: displaced — {governing!r} "
                  f"is the version in force")
    return Enactment(statement, at, False, Verdict.NOT_SATISFIED, governing, reason)


@dataclass(frozen=True)
class Supersession:
    """Which of two lineage members (``old`` vs ``new``) governs facts at a time.
    ``governing`` is the prevailing statement and ``index`` the
    :class:`TemporalIndex` it is stamped with (which law, as of when); ``verdict``
    is ``SATISFIED`` for a settled tempus-regit-actum (or flagged-unechte) choice.
    A **contested** intertemporal choice — echte Rückwirkung (reaching completed
    facts), an undatable applied version, or no governing version at all — is
    ``OPEN``: ``governing``/``index`` are ``None`` and ``options`` carries the
    bounded escalation set surfaced from the underlying ``VersionSelection``."""

    old: LegalStatement
    new: LegalStatement
    at: str
    governing: Optional[LegalStatement]
    index: Optional[TemporalIndex]
    verdict: Verdict
    contested: bool
    reason: str
    options: Tuple[str, ...] = ()

    @property
    def escalates(self) -> bool:
        return self.verdict is Verdict.OPEN


def supersede(old: LegalStatement, new: LegalStatement,
              events: Sequence[LifecycleEvent], *, at: str,
              enacted: Optional[Mapping[str, str]] = None,
              apply: Optional[LegalStatement] = None,
              facts_completed: bool = True,
              celex_of: Optional[Mapping[str, str]] = None) -> Supersession:
    """Which of ``old`` / ``new`` (two members of one supersession lineage) governs
    facts at ``at``? Delegates the whole choice to :func:`intertemporal.select_version`
    (tempus regit actum) — no version, date, or retroactivity logic re-grown.

    Default (``apply`` is None): the version **in force at the facts' time**
    governs; the result carries its :class:`TemporalIndex`. Pass ``apply`` to force
    applying a *particular* member's version instead — then the retroactivity gate
    fires: **echte Rückwirkung** (reaching completed facts) → contested (escalate);
    **unechte** (still-ongoing facts) → selected but flagged. No governing version
    at ``at`` → contested. Every contested branch surfaces the underlying
    ``VersionSelection`` reason + options — ⊥ → escalate, never a silent swap to
    the current text.

    The governing member token is mapped back to ``old`` / ``new``. If the version
    in force is *neither* (a third member of the lineage governs), that is a
    determinate ``NOT_SATISFIED`` — these two do not govern; not a fabrication."""
    sel = intertemporal.select_version(
        _member(old), events, event_time=at, enacted=enacted,
        apply_version=(_member(apply) if apply is not None else None),
        facts_completed=facts_completed, celex_of=celex_of)

    if sel.contested:
        return Supersession(old, new, at, None, None, Verdict.OPEN, True,
                            sel.reason, sel.options)

    gv = sel.index.norm_version
    if gv == _member(new):
        governing = new
    elif gv == _member(old):
        governing = old
    else:
        # the lifecycle names a definite in-force version, but it is neither of
        # the two statements offered — a determinate 'neither governs', honest.
        return Supersession(
            old, new, at, None, sel.index, Verdict.NOT_SATISFIED, False,
            f"the version in force at {at} is {gv!r} — neither of the two "
            f"statements offered governs")

    return Supersession(old, new, at, governing, sel.index, Verdict.SATISFIED,
                        False, sel.reason)


# ── rule of ADJUDICATION ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class Adjudication:
    """A dispute resolved end-to-end (derive → resolve → terminal). ``verdict`` is
    the terminal:

      * ``OPEN`` (escalate) — **any** OPEN antecedent in the derivation (a
        presupposed/incomplete fact), OR a genuine collision on ``act`` the
        solver's pack could not separate. The honest "es kommt darauf an".
      * ``SATISFIED`` — at least one consequence fired (and any collision on
        ``act`` was determinately resolved); the fired/prevailing consequence
        stands.
      * ``NOT_SATISFIED`` — nothing fired and nothing is open: no norm applies to
        these facts.

    ``fired`` are the fired conclusions; ``open`` the escalating ones; ``conflict``
    the solver's per-act :class:`ConflictOutcome` (``None`` when no ``act`` was
    given or the fired consequences did not collide); ``prevailing`` the winning
    statement when a collision was determinately resolved."""

    verdict: Verdict
    fired: Tuple[Conclusion, ...]
    open: Tuple[Conclusion, ...]
    conflict: Optional[ConflictOutcome]
    prevailing: Optional[LegalStatement]
    derivation: Derivation
    reasons: Tuple[str, ...]

    @property
    def escalates(self) -> bool:
        return self.verdict is Verdict.OPEN


def adjudicate(statements: Sequence[LegalStatement], facts: FactSpace, *,
               act: Optional[str] = None,
               specificity: Optional[Mapping[str, int]] = None,
               times: Optional[Mapping[str, int]] = None,
               system: Optional[str] = None) -> Adjudication:
    """Resolve a dispute end-to-end, sequencing the algebra's ops — no firing or
    conflict logic re-grown:

      (a) :func:`algebra.derive` — fire the statements against ``facts``, splitting
          them into fired / open / inapplicable.
      (b) if an ``act`` is given and two-or-more consequences fired, hand the fired
          statements to :func:`algebra.resolve` (the solver's ``LEX_CONFLICT_PACK``,
          superior ▷ specialis ▷ posterior) to pick the prevailing one. When the
          fired consequences *agree*, the pack returns a determinate outcome with
          no unique winner (or ``None``) — no genuine collision, so no prevailing
          is picked and both stand.
      (c) the terminal: **any** OPEN antecedent OR an ``'open'`` resolve →
          ``OPEN`` (escalate); else, if anything fired, ``SATISFIED`` (the
          fired/prevailing consequence stands); else ``NOT_SATISFIED``.

    Never fabricates a resolution: an open collision or an OPEN antecedent
    escalates. ``specificity`` / ``times`` are optional maps keyed by
    ``statement.label()`` (the lex-specialis / lex-posterior keys for the fired
    subset). A fired statement whose source class is not rankable for a lex
    conflict makes the collision inseparable → escalate (never a guessed winner).
    Inputs are assumed already recognised (:func:`grammar.validate`); this is the
    rule of adjudication, not recognition."""
    derivation = algebra.derive(statements, facts)
    reasons: list[str] = []

    # (c-i) an OPEN antecedent is the honest escalate terminal — before any
    # conflict resolution; a presupposed/incomplete fact opens the whole dispute.
    if derivation.open:
        reasons.append(
            f"{len(derivation.open)} antecedent(s) OPEN (presupposed/incomplete "
            f"fact) — escalate; never fired on doubt")
        return Adjudication(Verdict.OPEN, derivation.fired, derivation.open,
                            None, None, derivation, tuple(reasons))

    conflict: Optional[ConflictOutcome] = None
    prevailing: Optional[LegalStatement] = None

    # (b) a collision on the act among the fired consequences → the solver's pack.
    if act is not None and len(derivation.fired) >= 2:
        fired_statements = [c.statement for c in derivation.fired]
        specs = ([int(specificity.get(s.label(), 0)) for s in fired_statements]
                 if specificity is not None else None)
        tms = ([times.get(s.label()) for s in fired_statements]
               if times is not None else None)
        try:
            conflict = algebra.resolve(fired_statements, act=act,
                                       specificity=specs, times=tms)
        except ValueError as exc:
            # a fired statement's class is not rankable for a lex conflict — the
            # collision cannot be separated → escalate (never a guessed winner).
            reasons.append(f"collision on {act!r} is inseparable: {exc} — escalate")
            return Adjudication(Verdict.OPEN, derivation.fired, derivation.open,
                                None, None, derivation, tuple(reasons))

        if conflict is not None and conflict.escalated:
            reasons.append(
                f"genuine collision on {act!r} the pack could not separate — "
                f"escalate; the winner is not fabricated")
            return Adjudication(Verdict.OPEN, derivation.fired, derivation.open,
                                conflict, None, derivation, tuple(reasons))
        if conflict is not None and conflict.winner is not None:
            # algebra.resolve assigns provision ids 'p{i}' positionally over the
            # fired statements it is handed — map the winner back to its statement.
            by_position = {f"p{i}": s for i, s in enumerate(fired_statements)}
            prevailing = by_position.get(conflict.winner)
            reasons.append(
                f"collision on {act!r} resolved by {conflict.rule} — "
                f"{(prevailing.label() if prevailing else conflict.winner)!r} prevails")

    # (c-ii) settled terminal.
    if derivation.fired:
        if conflict is None and act is not None and len(derivation.fired) >= 2:
            reasons.append(f"the fired consequences on {act!r} agree — no collision")
        verdict = Verdict.SATISFIED
    else:
        verdict = Verdict.NOT_SATISFIED
        reasons.append("no statement fired and none is open — no norm applies")

    return Adjudication(verdict, derivation.fired, derivation.open, conflict,
                        prevailing, derivation, tuple(reasons))
