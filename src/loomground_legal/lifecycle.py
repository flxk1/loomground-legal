# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Instrument lifecycle & lineage — which version is in force at time T.

Law is versioned over time: instruments supersede, repeal, and amend each
other, and descend from one another. This module models that life as **dated
lifecycle events** over the lifecycle relations the connection vocabulary
already carries (``supersedes``, ``descends_from``, ``presumes_conformity``,
``applies_in``, ``adopted_by``, ``established_by``) plus two event kinds that
belong to the lifecycle only — ``repeals`` and ``amends``. Those two are
deliberately NOT added to the connection composition algebra: they never
compose (nothing follows from *A repeals B* ∘ anything), so they live here as
event vocabulary, and ``connections.json`` stays exactly the host
``legal_connection`` table.

Resolution is typed and deterministic, and purely temporal — no doctrine:

* an instrument **terminated** (superseded or repealed) by an event dated on
  or before T is out of force at T;
* an instrument **introduced** by a supersession (it appears as the successor)
  is in force only from that event's date; a root instrument's start may be
  given explicitly via ``enacted``;
* ``amends`` (and the other lineage relations) never terminate anything.

:func:`version_in_force` walks a supersession lineage and returns the single
in-force member at T. Fail-closed: unknown event relations are a
``ValueError``, and a lineage with more than one in-force member at T is an
inconsistency that raises rather than picking one.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Mapping, Optional, Sequence, Set

__all__ = [
    "LifecycleEvent",
    "LIFECYCLE_RELATIONS",
    "TERMINATING_RELATIONS",
    "in_force",
    "version_in_force",
]

#: Event kinds terminating the *object* instrument's force from the event date.
TERMINATING_RELATIONS: FrozenSet[str] = frozenset({"supersedes", "repeals"})

#: The full lifecycle event vocabulary: the lifecycle relations already in the
#: connection vocabulary (``connections.json``) + the event-only pair.
LIFECYCLE_RELATIONS: FrozenSet[str] = frozenset(
    {
        "supersedes",
        "descends_from",
        "presumes_conformity",
        "applies_in",
        "adopted_by",
        "established_by",
        "repeals",
        "amends",
    }
)


@dataclass(frozen=True)
class LifecycleEvent:
    """One dated lifecycle edge: ``subject —relation→ object`` at ``date``.

    ``date`` is an ISO calendar date (``YYYY-MM-DD``) — ISO dates compare
    correctly as strings, keeping resolution deterministic with no clock or
    timezone logic. For ``supersedes``/``repeals`` the *subject* is the new /
    repealing instrument and the *object* is the one losing force."""

    relation: str
    subject: str
    object: str
    date: str

    def __post_init__(self) -> None:
        if self.relation not in LIFECYCLE_RELATIONS:
            raise ValueError(
                f"{self.relation!r} is not a lifecycle relation; expected one "
                f"of {sorted(LIFECYCLE_RELATIONS)}"
            )
        if not self.date:
            raise ValueError("a lifecycle event needs a date (YYYY-MM-DD)")


def _effective(events: Sequence[LifecycleEvent], at: str) -> list:
    return [e for e in events if e.date <= at]


def _introduction_date(
    instrument: str,
    events: Sequence[LifecycleEvent],
    enacted: Mapping[str, str],
) -> Optional[str]:
    """When the instrument's force starts: an explicit ``enacted`` date wins;
    else the earliest supersession it performs (a successor enters force when
    it supersedes); else ``None`` — taken as 'always was' (a root with no
    recorded start)."""
    if instrument in enacted:
        return enacted[instrument]
    dates = [
        e.date
        for e in events
        if e.relation == "supersedes" and e.subject == instrument
    ]
    return min(dates) if dates else None


def in_force(
    instrument: str,
    events: Sequence[LifecycleEvent],
    at: str,
    *,
    enacted: Optional[Mapping[str, str]] = None,
) -> bool:
    """Is ``instrument`` in force at ``at``?

    Out of force iff a ``supersedes``/``repeals`` event dated on or before
    ``at`` targets it, or its introduction date (see ``enacted``) lies after
    ``at``. ``amends`` and the lineage relations never terminate."""
    enacted = enacted or {}
    intro = _introduction_date(instrument, events, enacted)
    if intro is not None and intro > at:
        return False
    return not any(
        e.relation in TERMINATING_RELATIONS and e.object == instrument
        for e in _effective(events, at)
    )


def _lineage(member: str, events: Sequence[LifecycleEvent]) -> Set[str]:
    """The supersession lineage containing ``member``: the connected component
    over ``supersedes`` edges (undirected walk, deterministic)."""
    neighbours: dict = {}
    for e in events:
        if e.relation != "supersedes":
            continue
        neighbours.setdefault(e.subject, set()).add(e.object)
        neighbours.setdefault(e.object, set()).add(e.subject)
    seen: Set[str] = {member}
    frontier = [member]
    while frontier:
        nxt = frontier.pop()
        for other in neighbours.get(nxt, ()):
            if other not in seen:
                seen.add(other)
                frontier.append(other)
    return seen


def version_in_force(
    member: str,
    events: Sequence[LifecycleEvent],
    at: str,
    *,
    enacted: Optional[Mapping[str, str]] = None,
) -> Optional[str]:
    """The single in-force version, at ``at``, of the supersession lineage
    containing ``member`` (any member identifies the lineage).

    Returns ``None`` when no member is in force (e.g. the whole line was
    repealed, or nothing has entered force yet). More than one in-force member
    means the recorded lineage is inconsistent — ``ValueError``, fail-closed;
    the resolution never picks a survivor the data cannot justify."""
    current = sorted(
        i
        for i in _lineage(member, events)
        if in_force(i, events, at, enacted=enacted)
    )
    if not current:
        return None
    if len(current) > 1:
        raise ValueError(
            f"lineage of {member!r} has {len(current)} versions in force at "
            f"{at}: {current}; the lifecycle record is inconsistent"
        )
    return current[0]
