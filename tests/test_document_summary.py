# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Document-level summary — branch-level tests.

One overview per document: doc-kind from leading header patterns, identifier,
the instrument code consumed from crossref, and a boundary-safe excerpt. Invents
nothing — unknown instrument is "", an unnamed doc takes its source name.
"""
from __future__ import annotations

from loomground_legal import DocumentSummary, summarize_document


def test_regulation_header_is_classified():
    s = summarize_document(
        "REGULATION (EU) 2016/679 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL "
        "on the protection of natural persons with regard to the processing of "
        "personal data (General Data Protection Regulation).")
    assert s.doc_kind == "regulation"
    assert s.doc_id == "2016/679"
    assert s.instrument == "gdpr"          # consumed from crossref.infer_host_instrument


def test_instrument_is_the_host_not_a_cited_one():
    # AI Act document that cites the GDPR — instrument must be the host (ai-act).
    s = summarize_document(
        "REGULATION (EU) 2024/1689 OF THE EUROPEAN PARLIAMENT (AI Act). This "
        "applies without prejudice to Regulation (EU) 2016/679.")
    assert s.instrument == "ai-act"


def test_directive_header_is_classified():
    s = summarize_document(
        "DIRECTIVE (EU) 2019/790 OF THE EUROPEAN PARLIAMENT on copyright in the "
        "Digital Single Market.")
    assert s.doc_kind == "directive"
    assert s.doc_id == "2019/790"


def test_case_law_citation_is_classified():
    s = summarize_document(
        "Judgment of the Court in Case C-311/18 Data Protection Commissioner v "
        "Facebook Ireland (Schrems II).")
    assert s.doc_kind == "case-law"
    assert s.doc_id == "C-311/18"


def test_case_study_marker_is_classified():
    s = summarize_document(
        "Case Study: a start-up deploys an AI hiring tool across three EU states.",
        source_name="/docs/hiring-case.md")
    assert s.doc_kind == "case-study"
    assert s.doc_id == "hiring-case.md"    # source tail, not invented


def test_generic_document_falls_back_to_source_name():
    s = summarize_document("Some ordinary prose without a legal header.",
                           source_name="notes/memo.txt")
    assert s.doc_kind == "document"
    assert s.doc_id == "memo.txt"
    assert s.instrument == ""              # no instrument inferable → not guessed


def test_excerpt_is_boundary_safe_and_bounded():
    body = ("This Regulation lays down rules relating to the protection of natural "
            "persons. " * 40)
    s = summarize_document(body)
    assert len(s.excerpt) <= 601           # limit + trailing char
    assert not s.excerpt.endswith(" ")     # trimmed
    # collapsed whitespace: no double spaces
    assert "  " not in s.excerpt


def test_short_document_excerpt_is_whole_text():
    s = summarize_document("A short note.")
    assert s.excerpt == "A short note."


def test_to_dict_shape():
    d = summarize_document("REGULATION (EU) 2016/679 OF THE COUNCIL").to_dict()
    assert set(d) == {"doc_kind", "doc_id", "instrument", "excerpt"}


def test_empty_content_is_safe():
    s = summarize_document("")
    assert s.doc_kind == "document" and s.instrument == "" and s.excerpt == ""
    assert isinstance(s, DocumentSummary)
