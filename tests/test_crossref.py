# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Instrument cross-reference resolution — branch-level tests.

Resolve a citation (full form, CELEX, or short name) to a canonical instrument;
type the citing relation verb onto a Dimension; drop self-references; dedupe by
target with STRUCTURAL preferred over RELATIONAL; invent nothing. Identity stays
aligned with instruments.CODE.
"""
from __future__ import annotations

from loomground_solver import Dimension

from loomground_legal.crossref import (
    INSTRUMENTS,
    extract_cross_references,
    infer_host_instrument,
    resolve_celex,
    resolve_citation_number,
    resolve_short_name,
)
from loomground_legal.instruments import CODE


def _by_code(refs):
    return {r.target_code: r for r in refs}


def test_registry_is_aligned_with_code():
    # Every CELEX-bearing row agrees with the CODE authority where CODE knows it.
    for inst in INSTRUMENTS:
        if inst.celex and inst.celex in CODE:
            assert CODE[inst.celex] == inst.code


def test_resolve_full_citation():
    r = resolve_citation_number("2016/679")
    assert r is not None and r.code == "gdpr" and r.celex == "32016R0679"


def test_resolve_celex_via_code():
    assert resolve_celex("32024R1689").code == "ai-act"


def test_resolve_short_name_case_insensitive():
    assert resolve_short_name("gdpr").code == "gdpr"
    assert resolve_short_name("Digital Services Act").code == "dsa"


def test_relation_verb_types_the_dimension():
    # "without prejudice to" → RELATIONAL link.
    refs = _by_code(extract_cross_references(
        "This Regulation applies without prejudice to Regulation (EU) 2016/679.",
        host_code="ai-act"))
    assert refs["gdpr"].relation == "without-prejudice"
    assert refs["gdpr"].dimension == Dimension.RELATIONAL.value


def test_structural_relation_verb():
    refs = _by_code(extract_cross_references(
        "This Directive amends Regulation (EU) 2016/679.", host_code="ai-act"))
    assert refs["gdpr"].relation == "amends"
    assert refs["gdpr"].dimension == Dimension.STRUCTURAL.value


def test_self_reference_is_dropped():
    # A GDPR document citing its own number must not emit a self cross-reference.
    refs = extract_cross_references(
        "Regulation (EU) 2016/679 lays down rules on the protection of natural persons.",
        host_code="gdpr")
    assert all(r.target_code != "gdpr" for r in refs)


def test_host_is_inferred_when_not_given():
    # CELEX self-id in the header → host inferred → own citation dropped.
    refs = extract_cross_references(
        "32016R0679\nThis Regulation (EU) 2016/679 governs personal data.")
    assert infer_host_instrument("32016R0679 ...") == "gdpr"
    assert all(r.target_code != "gdpr" for r in refs)


def test_host_from_bare_short_name():
    # A 4-char meaningful alias (GDPR, DORA, NIS2) must infer the host even with no
    # citation number — only the 3-char ambiguous ones (DSA/DMA/CRA) are skipped.
    assert infer_host_instrument("This document explains how the GDPR applies.") == "gdpr"
    assert infer_host_instrument("DORA governs ICT risk for financial entities.") == "dora"


def test_host_is_the_earliest_appearing_instrument():
    # The document IS the AI Act (header) but cites the GDPR in its body. The host
    # must be ai-act (earliest), NOT gdpr (registry order / a body citation).
    text = ("REGULATION (EU) 2024/1689 (AI Act). This applies without prejudice to "
            "Regulation (EU) 2016/679.")
    assert infer_host_instrument(text) == "ai-act"
    codes = {r.target_code for r in extract_cross_references(text)}
    assert "ai-act" not in codes and "gdpr" in codes   # own citation dropped, GDPR kept


def test_dedup_accumulates_count_and_prefers_structural():
    text = ("As referred to in the GDPR, and further, this Act amends "
            "Regulation (EU) 2016/679.")
    refs = _by_code(extract_cross_references(text, host_code="ai-act"))
    gdpr = refs["gdpr"]
    assert gdpr.count >= 2
    assert gdpr.dimension == Dimension.STRUCTURAL.value   # 'amends' wins over 'refers-to'


def test_unresolved_citation_is_raw_not_invented():
    refs = extract_cross_references(
        "See Regulation (EU) 9999/99 for details.", host_code="ai-act")
    # 9999/99 is a well-formed citation absent from the registry → a raw,
    # unresolved entry (target_code == ""), never guessed onto a known instrument.
    assert any(r.target_code == "" and "9999/99" in r.matched_text for r in refs)


def test_absent_references_yield_nothing():
    assert extract_cross_references("The weather is fine today.", host_code="ai-act") == []


def test_to_dict_shape():
    r = extract_cross_references("without prejudice to the GDPR", host_code="ai-act")[0]
    d = r.to_dict()
    assert set(d) == {"target_code", "target_canonical", "target_celex",
                      "relation", "dimension", "matched_text", "count"}
