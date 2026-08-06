# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Competing-definition detection over a corpus of citation records.

A single term is often defined in more than one place — the same term
carrying two distinct authoritative definitions at two different loci
(``'controller'`` in Art 4(7) of the GDPR and in Art 4 of the UK-GDPR, say).
That collision is a fact the corpus already asserts; this op only *reports*
it. It is deterministic and pure: it groups :class:`~loomground_legal.
citation.Definition` records by term and flags every term that carries more
than one distinct definition.

It never picks a winner. Choosing which of several competing definitions
governs a given locus is a resolution move (O35) that needs ordering and
precedence rules this op deliberately does not have. Detection stops at
"these compete"; it invents nothing beyond what the records state.

Distinctness is ``(definition.citation, normalised definition.text)``: two
records at the *same* locus with the *same* text are the same definition and
are deduplicated; two records at *different* loci compete. The term key is
:func:`str.casefold`/whitespace-normalised so ``"Personal Data"`` and
``"personal data"`` collide onto one entry.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from loomground_legal.citation import Citation, Definition, bind_definition

__all__ = [
    "CompetingSet",
    "detect_competing",
    "competing_for_term",
    "bind_definition",
]


@dataclass(frozen=True)
class CompetingSet:
    """Every distinct definition the corpus asserts for one term.

    ``term`` is the normalised term key. ``definitions`` are the distinct
    competing :class:`Definition` records, order-stable by
    ``(citation.canonical(), text)``. ``competing`` is ``True`` iff the term
    carries more than one distinct definition."""

    term: str
    definitions: tuple[Definition, ...]
    competing: bool


def _norm_term(term: str) -> str:
    """Casefold, strip, and collapse internal whitespace to single spaces."""
    return " ".join(term.split()).casefold()


def _norm_text(text: str) -> str:
    """Whitespace-normalise definition text for the distinctness key."""
    return " ".join(text.split())


def _distinct_key(definition: Definition) -> tuple[Citation, str]:
    """The distinctness key: the (hashable, frozen) Citation plus the
    whitespace-normalised text. Two records with an equal key are the same
    definition; unequal keys compete."""
    return (definition.citation, _norm_text(definition.text))


def _order_key(definition: Definition) -> tuple[str, str]:
    """The order key used to make ``definitions`` order-stable, independent of
    input order: ``(citation.canonical(), text)``."""
    return (definition.citation.canonical(), definition.text)


def detect_competing(definitions: Iterable[Definition]) -> dict[str, CompetingSet]:
    """Group a corpus of :class:`Definition` records by term and flag every
    term that carries more than one distinct authoritative definition.

    Distinctness key = ``(definition.citation, normalised definition.text)``:
    two records at the same locus with the same text are the same definition
    (deduplicated); two records at different loci are competing. The term key
    is casefold/whitespace-normalised so ``"Personal Data"`` and
    ``"personal data"`` collide. Returns one :class:`CompetingSet` per term.
    Empty in -> empty dict. Invents nothing: it reports only what the records
    already assert."""
    # Preserve first-seen term-key order for a stable mapping; within a term,
    # deduplicate on the distinctness key.
    grouped: dict[str, dict[tuple[Citation, str], Definition]] = {}
    for definition in definitions:
        key = _norm_term(definition.term)
        distinct = grouped.setdefault(key, {})
        dkey = _distinct_key(definition)
        if dkey not in distinct:
            distinct[dkey] = definition

    result: dict[str, CompetingSet] = {}
    for term_key, distinct in grouped.items():
        ordered = tuple(sorted(distinct.values(), key=_order_key))
        result[term_key] = CompetingSet(
            term=term_key,
            definitions=ordered,
            competing=len(ordered) > 1,
        )
    return result


def competing_for_term(
    term: str, definitions: Iterable[Definition]
) -> CompetingSet:
    """The :class:`CompetingSet` for a single term (convenience over
    :func:`detect_competing`).

    A term absent from the corpus yields
    ``CompetingSet(term=<normalised>, definitions=(), competing=False)``."""
    normalised = _norm_term(term)
    found = detect_competing(definitions).get(normalised)
    if found is not None:
        return found
    return CompetingSet(term=normalised, definitions=(), competing=False)
