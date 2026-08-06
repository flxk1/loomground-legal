# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Instrument identifiers — work-level and expression-level, never the title.

A statute is identified by a **stable machine code**, not its official title
(titles are multilingual, long, get abbreviated and renamed — that is what
``crossref.InstrumentRef.short_names`` absorbs). Two levels of identity, the
FRBR distinction that versioning turns on:

  * **work** — the instrument as such, across all time: the base **CELEX**
    (``32016R0679``) for EU law, the national citation otherwise.
  * **expression** — a specific consolidated text *in force at a date*: the
    **consolidated CELEX** (``02016R0679-20180525``) or the **ELI point-in-time**
    (``…/eli/reg/2016/679/2018-05-25``). This is what an intertemporal selection
    actually names — "which law, as of when" — so a conclusion cites a real,
    resolvable identifier, not a token.

Pure stdlib; string identity only. No network, no registry — it derives the
expression id from a work id + an in-force date.
"""

from __future__ import annotations

__all__ = ["consolidated_celex", "eli_at", "version_id"]


def _check_date(d: str) -> None:
    parts = (d or "").split("-")
    if len(parts) != 3 or not all(p.isdigit() for p in parts) or len(parts[0]) != 4:
        raise ValueError(f"in-force date must be ISO YYYY-MM-DD, got {d!r}")


def consolidated_celex(base_celex: str, in_force_date: str) -> str:
    """The consolidated-CELEX expression id for a base act at a point in time:
    ``32016R0679`` + ``2018-05-25`` → ``02016R0679-20180525``. The consolidated
    family carries sector digit ``0`` and a trailing ``-YYYYMMDD``."""
    if not base_celex:
        raise ValueError("need a base CELEX")
    _check_date(in_force_date)
    body = base_celex[1:] if base_celex[0].isdigit() else base_celex
    return f"0{body}-{in_force_date.replace('-', '')}"


def eli_at(base_eli: str, in_force_date: str) -> str:
    """The ELI point-in-time expression id: ``…/eli/reg/2016/679/oj`` +
    ``2018-05-25`` → ``…/eli/reg/2016/679/2018-05-25``. A trailing ``/oj`` (the
    'as published' segment) is replaced by the date."""
    if not base_eli:
        raise ValueError("need a base ELI")
    _check_date(in_force_date)
    stem = base_eli.rstrip("/")
    if stem.endswith("/oj"):
        stem = stem[:-3].rstrip("/")
    return f"{stem}/{in_force_date}"


def version_id(*, celex: str = "", code: str = "", in_force_date: str) -> str:
    """Expression-level identity — a consolidated version in force at a date.
    NEVER the title. Prefers consolidated CELEX; falls back to ``{code}@{date}``
    for a national law with no CELEX. Raises if neither anchor is given."""
    _check_date(in_force_date)
    if celex:
        return consolidated_celex(celex, in_force_date)
    if code:
        return f"{code}@{in_force_date}"
    raise ValueError("need a celex or code to build a version id (title is not an id)")
