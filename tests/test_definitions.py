# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Competing-definition detection: a term carrying more than one distinct
authoritative definition is flagged, identical records at one locus are
deduplicated, term keys are case-insensitive, and the op picks no winner —
it only reports what the :class:`Definition` records already assert."""
from __future__ import annotations

from loomground_legal.citation import Citation, Definition, bind_definition
from loomground_legal.definitions import (
    CompetingSet,
    competing_for_term,
    detect_competing,
)


# ── single definition is not competing ───────────────────────────────────────

def test_single_definition_is_not_competing():
    defs = [
        Definition(
            term="controller",
            citation=Citation(instrument="GDPR", article="4", paragraph="7"),
            text="'controller' means the natural or legal person which "
            "determines the purposes and means of the processing",
        )
    ]
    result = detect_competing(defs)
    assert set(result) == {"controller"}
    cs = result["controller"]
    assert isinstance(cs, CompetingSet)
    assert cs.competing is False
    assert len(cs.definitions) == 1


# ── two loci for the same term compete ───────────────────────────────────────

def test_two_loci_same_term_compete():
    defs = [
        Definition(
            term="controller",
            citation=Citation(instrument="GDPR", article="4", paragraph="7"),
            text="EU-GDPR controller definition",
        ),
        Definition(
            term="controller",
            citation=Citation(instrument="UK-GDPR", article="4"),
            text="UK-GDPR controller definition",
        ),
    ]
    cs = detect_competing(defs)["controller"]
    assert cs.competing is True
    citations = {d.citation for d in cs.definitions}
    assert Citation(instrument="GDPR", article="4", paragraph="7") in citations
    assert Citation(instrument="UK-GDPR", article="4") in citations
    assert len(cs.definitions) == 2


# ── identical records collapse ───────────────────────────────────────────────

def test_identical_definitions_deduplicated():
    citation = Citation(instrument="GDPR", article="4", paragraph="1")
    text = "'personal data' means any information relating to an identified " \
        "or identifiable natural person"
    defs = [
        Definition(term="personal data", citation=citation, text=text),
        Definition(term="personal data", citation=citation, text=text),
    ]
    cs = detect_competing(defs)["personal data"]
    assert cs.competing is False
    assert len(cs.definitions) == 1


# ── term key is case-insensitive ─────────────────────────────────────────────

def test_term_key_is_case_insensitive():
    defs = [
        Definition(
            term="Personal Data",
            citation=Citation(instrument="GDPR", article="4", paragraph="1"),
            text="capitalised-term definition",
        ),
        Definition(
            term="personal data",
            citation=Citation(instrument="UK-GDPR", article="3", paragraph="2"),
            text="lowercase-term definition",
        ),
    ]
    result = detect_competing(defs)
    assert set(result) == {"personal data"}
    cs = result["personal data"]
    assert cs.term == "personal data"
    assert cs.competing is True
    assert len(cs.definitions) == 2


# ── multiple terms flagged independently ─────────────────────────────────────

def test_multiple_terms_flagged_independently():
    defs = [
        Definition(
            term="controller",
            citation=Citation(instrument="GDPR", article="4", paragraph="7"),
            text="controller here",
        ),
        Definition(
            term="controller",
            citation=Citation(instrument="UK-GDPR", article="4"),
            text="controller there",
        ),
        Definition(
            term="processor",
            citation=Citation(instrument="GDPR", article="4", paragraph="8"),
            text="processor only here",
        ),
    ]
    result = detect_competing(defs)
    assert result["controller"].competing is True
    assert result["processor"].competing is False
    assert len(result["processor"].definitions) == 1


# ── empty corpus ─────────────────────────────────────────────────────────────

def test_empty_corpus_returns_empty_mapping():
    assert detect_competing([]) == {}
    cs = competing_for_term("x", [])
    assert cs.competing is False
    assert cs.definitions == ()
    assert cs.term == "x"


# ── convenience: competing_for_term over the consumed producer ───────────────

def test_competing_for_term_uses_bound_definitions():
    # Build the Definition inputs via the documented producer, bind_definition,
    # to prove the op ingests exactly what citation.bind_definition emits.
    corpus_eu = {
        Citation(instrument="GDPR", article="4", paragraph="7"):
            "'controller' means the natural or legal person which determines "
            "the purposes and means of the processing",
    }
    corpus_uk = {
        Citation(instrument="UK-GDPR", article="4"):
            "'controller' has the meaning given in the UK GDPR",
    }
    eu = bind_definition(
        "controller", "as defined in Art 4(7)", corpus_eu, instrument="GDPR"
    )
    uk = bind_definition(
        "controller", "as defined in Art 4", corpus_uk, instrument="UK-GDPR"
    )
    assert isinstance(eu, Definition) and isinstance(uk, Definition)

    cs = competing_for_term("Controller", [eu, uk])
    assert cs.term == "controller"
    assert cs.competing is True
    assert len(cs.definitions) == 2
    # Order-stable by (citation.canonical(), text): GDPR sorts before UK-GDPR.
    assert [d.citation.instrument for d in cs.definitions] == ["GDPR", "UK-GDPR"]


def test_competing_for_term_absent_is_empty():
    eu = Definition(
        term="controller",
        citation=Citation(instrument="GDPR", article="4", paragraph="7"),
        text="controller here",
    )
    cs = competing_for_term("processor", [eu])
    assert cs.competing is False
    assert cs.definitions == ()
    assert cs.term == "processor"
