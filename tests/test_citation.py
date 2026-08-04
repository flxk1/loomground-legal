# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The fresh citation model: structured parsing of the common forms, canonical
round-trip, internal cross-reference resolution, and definition binding —
with the never-guess discipline on everything unparseable."""
from __future__ import annotations

import pytest

from loomground_legal import (
    Citation,
    Definition,
    bind_definition,
    parse_citation,
    resolve_xref,
)


# ── parsing the common forms ─────────────────────────────────────────────────

def test_parse_bare_article():
    c = parse_citation("Art 3")
    assert c == Citation(article="3")
    assert (c.paragraph, c.point, c.recital, c.annex) == ("", "", "", "")


def test_parse_article_with_paragraph():
    assert parse_citation("Article 3(2)") == Citation(article="3", paragraph="2")
    assert parse_citation("Article 4(1)") == Citation(article="4", paragraph="1")


def test_parse_article_paragraph_point():
    c = parse_citation("Art 6(1)(a)")
    assert c == Citation(article="6", paragraph="1", point="a")


def test_parse_recital():
    assert parse_citation("Recital 26") == Citation(recital="26")


def test_parse_annex():
    assert parse_citation("Annex III") == Citation(annex="III")


def test_parse_subparagraph_and_letter_suffix():
    c = parse_citation("Article 22a(2), subparagraph 1")
    assert c == Citation(article="22a", paragraph="2", subparagraph="1")


def test_instrument_is_caller_context():
    c = parse_citation("Article 3(2)", instrument="GDPR")
    assert c.instrument == "GDPR"


def test_unparseable_text_is_none_never_a_guess():
    assert parse_citation("the second sentence of the preamble") is None
    assert parse_citation("") is None


def test_partial_forms_leave_fields_unset():
    c = parse_citation("pursuant to Article 9")
    assert c.article == "9"
    assert c.paragraph == "" and c.point == "" and c.subparagraph == ""


# ── the Citation type is fail-closed on impossible loci ──────────────────────

def test_a_citation_has_one_head():
    with pytest.raises(ValueError):
        Citation(article="3", recital="26")
    with pytest.raises(ValueError):
        Citation(recital="1", annex="I")


def test_paragraph_fields_need_an_article():
    with pytest.raises(ValueError):
        Citation(paragraph="2")
    with pytest.raises(ValueError):
        Citation(article="6", point="a")  # a point needs a paragraph


# ── canonical round-trip ─────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "citation",
    [
        Citation(article="3"),
        Citation(article="3", paragraph="2"),
        Citation(article="6", paragraph="1", point="a"),
        Citation(article="22a", paragraph="2", subparagraph="1"),
        Citation(recital="26"),
        Citation(annex="III"),
        Citation(instrument="GDPR", article="4", paragraph="1"),
    ],
)
def test_canonical_string_round_trips(citation):
    assert parse_citation(
        citation.canonical(), instrument=citation.instrument
    ) == citation


# ── internal xref + definition binding ───────────────────────────────────────

def test_resolve_definitional_xref():
    c = resolve_xref("as defined in Art 4(1)", instrument="GDPR")
    assert c == Citation(instrument="GDPR", article="4", paragraph="1")


def test_bind_term_to_its_definition():
    corpus = {
        Citation(instrument="GDPR", article="4", paragraph="1"):
            "'personal data' means any information relating to an identified "
            "or identifiable natural person",
        Citation(instrument="GDPR", article="4", paragraph="7"):
            "'controller' means the natural or legal person which determines "
            "the purposes and means of the processing",
    }
    d = bind_definition(
        "personal data", "as defined in Art 4(1)", corpus, instrument="GDPR"
    )
    assert isinstance(d, Definition)
    assert d.term == "personal data"
    assert d.citation == Citation(instrument="GDPR", article="4", paragraph="1")
    assert "identifiable natural person" in d.text


def test_binding_fails_closed():
    corpus = {Citation(instrument="GDPR", article="4", paragraph="1"): "…"}
    # Xref that resolves to a locus the corpus lacks: no invented definition.
    assert bind_definition("controller", "as defined in Art 4(7)", corpus,
                           instrument="GDPR") is None
    # Xref that does not resolve at all.
    assert bind_definition("controller", "as defined elsewhere", corpus,
                           instrument="GDPR") is None
