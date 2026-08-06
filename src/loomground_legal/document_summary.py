# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Document-level summary — one structured overview per legal document.

Answers "what is this document?" once per document (not per rule): its **kind**
(regulation / directive / case-law / case-study / document), its **identifier**
(the regulation/directive number, the case citation, or the source name), the
**instrument** it is (a canonical code), and a short **excerpt**.

The instrument identity is not re-derived here — it is **consumed** from
:func:`loomground_legal.crossref.infer_host_instrument` (the single regulation-name
inference in the family; two RVND twins of it retire onto this one). This module
adds only the document-kind classification, the identifier extraction, and the
excerpt. Data + detection, deterministic, no inference of its own.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from .crossref import infer_host_instrument

__all__ = ["DocumentSummary", "summarize_document"]

# A document header naming a regulation/directive: "REGULATION (EU) 2016/679 OF
# THE EUROPEAN PARLIAMENT …" / "DIRECTIVE (EU) 2019/790 OF THE …".
_REG_NAME_RE = re.compile(
    r"REGULATION\s*(?:\(EU\))?\s*(?P<num>\d+/\d+)\s+OF\s+THE\s+[A-Z]+\s+(?:PARLIAMENT)?",
    re.IGNORECASE)
_DIR_NAME_RE = re.compile(
    r"DIRECTIVE\s*(?:\(EU\))?\s*(?P<num>\d+/\d+)\s+OF\s+THE\s+[A-Z]+", re.IGNORECASE)
# A case citation: an EU Court docket (C-…/…, T-…/…) or a US reporter cite.
_CASE_NAME_RE = re.compile(r"\b(C-\d+/\d+|T-\d+/\d+|\d+\s+U\.?S\.?\s+\d+)\b")
_CASE_STUDY_RE = re.compile(r"\b(?:Case Study|Scenario)\b", re.IGNORECASE)

_EXCERPT_LIMIT = 600


@dataclass(frozen=True)
class DocumentSummary:
    """A one-per-document overview: kind, identifier, instrument code, excerpt."""

    doc_kind: str        # regulation | directive | case-law | case-study | document
    doc_id: str          # regulation/directive number, case citation, or source name
    instrument: str      # canonical instrument code (crossref), "" if not inferable
    excerpt: str         # a short leading excerpt of the document

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _tail_name(source_name: str, fallback: str) -> str:
    return (source_name or fallback).split("/")[-1][:60]


def _summary_excerpt(content: str, limit: int = _EXCERPT_LIMIT) -> str:
    """A short leading excerpt: whitespace-collapsed, cut at a sentence or word
    boundary so it never ends mid-word."""
    text = " ".join((content or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    dot = cut.rfind(". ")
    if dot > limit // 2:
        return cut[:dot + 1]
    space = cut.rfind(" ")
    return (cut[:space] if space > 0 else cut).rstrip() + "…"


def summarize_document(content: str, *, source_name: str = "") -> DocumentSummary:
    """Summarise a document once: its kind, identifier, instrument, and excerpt.

    Document kind is read from leading header patterns (a regulation/directive
    naming line, a case citation, a case-study marker), falling back to a generic
    ``document``. The instrument code is **consumed** from
    :func:`crossref.infer_host_instrument`. Invents nothing — an unknown instrument
    is ``""``, an unnamed document takes its source name.
    """
    content = content or ""
    head = content[:8000]
    reg, directive = _REG_NAME_RE.search(head), _DIR_NAME_RE.search(head)
    case = _CASE_NAME_RE.search(content[:4000])
    if reg:
        doc_kind, doc_id = "regulation", reg.group("num")
    elif directive:
        doc_kind, doc_id = "directive", directive.group("num")
    elif case:
        doc_kind, doc_id = "case-law", case.group(0)
    elif _CASE_STUDY_RE.search(content[:500]):
        doc_kind, doc_id = "case-study", _tail_name(source_name, "case")
    else:
        doc_kind, doc_id = "document", _tail_name(source_name, "doc")
    return DocumentSummary(
        doc_kind=doc_kind, doc_id=doc_id,
        instrument=infer_host_instrument(content),
        excerpt=_summary_excerpt(content))
