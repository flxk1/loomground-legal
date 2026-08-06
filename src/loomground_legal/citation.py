# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The citation model — legal-reference structure, modelled fresh.

Legal is the authority on legal-reference structure (decided 2026-08-04):
this module owns both the typed :class:`Citation` (instrument / article /
paragraph / point / subparagraph / recital / annex) and its parser,
independent of any ingest-side crossref extractor.

The parser reads the common forms — ``Art 3``, ``Article 3(2)``,
``Art 6(1)(a)``, ``Article 4(1)``, ``Recital 26``, ``Annex III`` — into
structured fields. What it cannot parse it leaves unset, and text with no
recognisable citation is ``None``: the parser **never guesses** a locus.

On top of the model sit the two resolution moves the family needs:

* **internal cross-reference** — :func:`resolve_xref` finds the citation
  inside a referring phrase (``"as defined in Art 4(1)"`` → the Citation for
  Article 4(1));
* **definition binding** — :func:`bind_definition` takes a term, its
  referring phrase, and a corpus of definitions keyed by Citation, and binds
  the term to the definition at the resolved locus (``None`` when the xref
  does not resolve or the corpus has no entry — fail-closed, no fabricated
  definition).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Optional

__all__ = ["Citation", "Definition", "parse_citation", "resolve_xref", "bind_definition"]

# ── the parser's grammar (fresh, regex) ──────────────────────────────────────
# Article: "Art 3" / "Article 3(2)" / "Art 6(1)(a)" / "Article 4(1)",
# optionally ", subparagraph 2". Article numbers may carry a letter suffix
# (Art 22a); paragraph is numeric; point is a short letter group.
_ARTICLE = re.compile(
    r"\bArt(?:icle)?\.?\s+(?P<article>\d+[a-z]?)"
    r"(?:\s*\(\s*(?P<paragraph>\d+)\s*\)"
    r"(?:\s*\(\s*(?P<point>[a-z]{1,2})\s*\))?)?"
    r"(?:\s*,\s*subparagraph\s+(?P<subparagraph>\d+))?",
    re.IGNORECASE,
)
_RECITAL = re.compile(r"\bRecital\s+(?P<recital>\d+)", re.IGNORECASE)
_ANNEX = re.compile(r"\bAnnex\s+(?P<annex>[IVXLCDM]+|\d+[A-Za-z]?)\b")


@dataclass(frozen=True)
class Citation:
    """A structural locus in a legal instrument. Unset fields are ``''``.

    Exactly one head is set: an article (with optional paragraph / point /
    subparagraph beneath it), a recital, or an annex — a locus cannot be two
    of those at once, and paragraph-level fields cannot float without an
    article. Hashable, so a definition corpus can key on it directly."""

    instrument: str = ""
    article: str = ""
    paragraph: str = ""
    point: str = ""
    subparagraph: str = ""
    recital: str = ""
    annex: str = ""

    def __post_init__(self) -> None:
        heads = [h for h in (self.article, self.recital, self.annex) if h]
        if len(heads) > 1:
            raise ValueError(
                "a Citation has one head: article, recital, or annex — "
                f"got article={self.article!r} recital={self.recital!r} "
                f"annex={self.annex!r}"
            )
        if not heads and (self.paragraph or self.point or self.subparagraph):
            raise ValueError("paragraph/point/subparagraph need an article")
        if (self.paragraph or self.point or self.subparagraph) and not self.article:
            raise ValueError("paragraph/point/subparagraph need an article")
        if self.point and not self.paragraph:
            raise ValueError("a point needs a paragraph (Art N(p)(x))")

    def canonical(self) -> str:
        """The canonical rendering — round-trips through
        :func:`parse_citation` (with the same ``instrument``)."""
        if self.recital:
            head = f"Recital {self.recital}"
        elif self.annex:
            head = f"Annex {self.annex}"
        else:
            head = f"Article {self.article}"
            if self.paragraph:
                head += f"({self.paragraph})"
            if self.point:
                head += f"({self.point})"
            if self.subparagraph:
                head += f", subparagraph {self.subparagraph}"
        return f"{self.instrument} {head}" if self.instrument else head


def parse_citation(text: str, *, instrument: str = "") -> Optional[Citation]:
    """Parse the first citation in ``text`` into structured fields.

    Handles ``Art N`` / ``Article N``, ``Article N(p)``, ``Art N(p)(x)``,
    ``..., subparagraph s``, ``Recital N``, and ``Annex R``. Fields the text
    does not carry stay unset (``''``); text carrying no recognisable
    citation returns ``None`` — never a guessed locus. ``instrument`` is
    caller-supplied context (the text form does not name it)."""
    m = _ARTICLE.search(text)
    if m:
        return Citation(
            instrument=instrument,
            article=m.group("article").lower(),
            paragraph=m.group("paragraph") or "",
            point=(m.group("point") or "").lower(),
            subparagraph=m.group("subparagraph") or "",
        )
    m = _RECITAL.search(text)
    if m:
        return Citation(instrument=instrument, recital=m.group("recital"))
    m = _ANNEX.search(text)
    if m:
        return Citation(instrument=instrument, annex=m.group("annex"))
    return None


def resolve_xref(text: str, *, instrument: str = "") -> Optional[Citation]:
    """Resolve an internal cross-reference phrase to its target Citation.

    ``"personal data as defined in Art 4(1)"`` → the Citation for Article
    4(1) of ``instrument``. This is :func:`parse_citation` applied to the
    referring phrase — the citation grammar is one grammar; the xref carries
    no extra structure. ``None`` when the phrase holds no citation."""
    return parse_citation(text, instrument=instrument)


@dataclass(frozen=True)
class Definition:
    """A term bound to the definition text at its defining Citation."""

    term: str
    citation: Citation
    text: str


def bind_definition(
    term: str,
    xref: str,
    definitions: Mapping[Citation, str],
    *,
    instrument: str = "",
) -> Optional[Definition]:
    """Bind ``term`` to its definition via a referring phrase.

    Resolves ``xref`` (e.g. ``"as defined in Art 4(1)"``) to a Citation and
    looks that Citation up in ``definitions`` (a corpus keyed by Citation).
    ``None`` when the xref does not resolve or the corpus has no entry at the
    resolved locus — a missing definition is surfaced, never invented."""
    citation = resolve_xref(xref, instrument=instrument)
    if citation is None:
        return None
    text = definitions.get(citation)
    if text is None:
        return None
    return Definition(term=term, citation=citation, text=text)
