# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Intertemporal law — WHICH version of a norm governs facts at a given time,
and the temporal INDEX that stamps a conclusion with *which law, as of when*.

``lifecycle`` is purely temporal ("which version exists at T", no doctrine).
This module adds the **doctrine** on top of its ``version_in_force``:

  * **tempus regit actum** — the default: a legal conclusion applies the version
    in force *at the time the facts occurred*, NOT the current consolidated text.
    A statement about a 2018 event is judged under the 2018 law.
  * **the temporal index** — every conclusion is doubly time-indexed:
    ``(event_time, norm_version)``. :class:`TemporalIndex` is that coordinate,
    stamped into the receipt so a verdict *states* which law as of when, and
    replays under it.
  * **retroactivity as a gated question** — applying a *different* (usually
    later) version than the one in force at the facts' time is an intertemporal
    move that must be classified, not done silently: **echte Rückwirkung**
    (reaching facts already completed → presumptively impermissible → ESCALATE)
    vs **unechte Rückwirkung** (reaching still-ongoing facts → permissible,
    subject to Vertrauensschutz / proportionality → selected but flagged).

"Es kommt darauf an" made mechanical: which version applies is itself a step
that can be **determinate** (tempus regit actum) or **contested** (retroactivity,
an ambiguous transitional rule, or no governing version) — and a contested
choice is surfaced, never resolved by picking the current text.

Pure stdlib; consumes ``lifecycle.version_in_force`` and re-grows no version or
date logic. No parallel verdict vocabulary: a selection is either *indexed*
(a governing version) or *contested* (the caller escalates with a bounded set).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Sequence

from .lifecycle import LifecycleEvent, version_in_force

__all__ = [
    "Retroactivity",
    "TemporalIndex",
    "VersionSelection",
    "classify_retroactivity",
    "governing_version",
    "select_version",
    "stamp",
]


class Retroactivity(str, Enum):
    """How a norm's application relates to the time of the facts."""
    NONE = "none"                        # norm already in force at the facts' time
    UNECHTE = "unechte_rueckwirkung"     # retrospective: reaches still-ongoing facts (permissible, flagged)
    ECHTE = "echte_rueckwirkung"         # true retroactivity: reaches completed facts (presumptively impermissible)


@dataclass(frozen=True)
class TemporalIndex:
    """The temporal coordinate a legal conclusion is indexed to: WHICH norm
    version, as of WHICH event time, on WHAT basis. Stamped into a conclusion's
    receipt so the verdict states which law as of when — not the current text."""
    event_time: str                      # T_event — ISO date the facts occurred
    norm_version: str                    # the version selected as governing
    basis: str                           # "tempus regit actum" | a transitional-rule cite
    retroactivity: Retroactivity = Retroactivity.NONE

    def receipt(self) -> dict:
        return {"event_time": self.event_time, "norm_version": self.norm_version,
                "basis": self.basis, "retroactivity": self.retroactivity.value}


@dataclass(frozen=True)
class VersionSelection:
    """The outcome of choosing which version governs facts at the event time.
    ``index`` is the selected coordinate, or ``None`` when the choice is
    **contested** (echte Rückwirkung, an undatable/ambiguous version, or nothing
    in force) — then the caller ESCALATES with ``options``."""
    index: Optional[TemporalIndex]
    contested: bool
    reason: str
    options: tuple[str, ...] = ()

    @property
    def selected(self) -> bool:
        return self.index is not None and not self.contested


def _version_start(version: str, events: Sequence[LifecycleEvent],
                   enacted: Mapping[str, str]) -> Optional[str]:
    """When a version's force starts — an explicit ``enacted`` date wins, else the
    earliest supersession it performs (a successor enters force when it supersedes),
    else None. Public-only mirror of the lifecycle introduction rule."""
    if version in enacted:
        return enacted[version]
    dates = [e.date for e in events
             if e.relation == "supersedes" and e.subject == version]
    return min(dates) if dates else None


def classify_retroactivity(*, version_start: Optional[str], event_time: str,
                           facts_completed: bool) -> Optional[Retroactivity]:
    """Classify applying a version whose force starts at ``version_start`` to facts
    at ``event_time``. Returns None when the version cannot be dated (undecidable).

    - ``version_start <= event_time`` → NONE (already in force; no retroactivity).
    - start after the event, facts already COMPLETED → ECHTE (reaches closed facts).
    - start after the event, facts still ONGOING → UNECHTE (retrospective)."""
    if version_start is None:
        return None
    if version_start <= event_time:
        return Retroactivity.NONE
    return Retroactivity.ECHTE if facts_completed else Retroactivity.UNECHTE


def governing_version(member: str, events: Sequence[LifecycleEvent], *,
                      event_time: str,
                      enacted: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """The version in force at the FACTS' time (tempus regit actum) — delegated to
    ``lifecycle.version_in_force``; no version logic re-grown. ``None`` if none."""
    return version_in_force(member, events, at=event_time, enacted=enacted)


def select_version(member: str, events: Sequence[LifecycleEvent], *,
                   event_time: str,
                   enacted: Optional[Mapping[str, str]] = None,
                   apply_version: Optional[str] = None,
                   facts_completed: bool = True) -> VersionSelection:
    """Choose which version governs facts at ``event_time``.

    Default (``apply_version`` None or == the governing version): **tempus regit
    actum** — the version in force at the facts' time governs, and the result is
    a :class:`TemporalIndex`. When a *different* version is applied, classify the
    retroactivity: ECHTE → contested (escalate); UNECHTE → selected but flagged;
    undatable → contested. Nothing in force at ``event_time`` → contested."""
    enacted = enacted or {}
    governing = version_in_force(member, events, at=event_time, enacted=enacted)
    if governing is None:
        return VersionSelection(
            None, True,
            f"no version of the lineage containing {member!r} is in force at {event_time}",
            options=("apply the earliest enacted version, if that is intended",
                     "hold non-applicable — no governing law at that time"))

    if apply_version is None or apply_version == governing:
        return VersionSelection(
            TemporalIndex(event_time, governing, "tempus regit actum"),
            False,
            f"the version in force at {event_time} governs (tempus regit actum)")

    # a different version is being applied → an intertemporal / retroactivity call
    start = _version_start(apply_version, events, enacted)
    retro = classify_retroactivity(version_start=start, event_time=event_time,
                                   facts_completed=facts_completed)
    if retro is None:
        return VersionSelection(
            None, True,
            f"cannot date {apply_version!r}; intertemporal application is undecidable",
            options=(f"apply the governing version {governing!r} (tempus regit actum)",
                     "supply the applied version's enacted date"))
    if retro is Retroactivity.ECHTE:
        return VersionSelection(
            None, True,
            f"applying {apply_version!r} to facts at {event_time} is echte "
            f"Rückwirkung (reaches completed facts) — presumptively impermissible",
            options=(f"apply the governing version {governing!r} (tempus regit actum)",
                     "escalate to retroactivity review (Vertrauensschutz / constitutional)"))
    # UNECHTE — permissible, but flagged
    return VersionSelection(
        TemporalIndex(event_time, apply_version,
                      f"unechte Rückwirkung of {apply_version!r} (retrospective)",
                      Retroactivity.UNECHTE),
        False,
        "retrospective application to still-ongoing facts — permissible, subject "
        "to Vertrauensschutz / Verhältnismäßigkeit")


def stamp(index: TemporalIndex, receipt: Optional[dict] = None) -> dict:
    """Attach the temporal index to a conclusion's provenance receipt, so the
    verdict carries *which law, as of when*. Returns a new dict; does not mutate."""
    out = dict(receipt or {})
    out["temporal_index"] = index.receipt()
    return out
