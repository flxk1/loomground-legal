# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Instrument-registry metadata (CODE/DOMAIN/TRANCHES, lifted verbatim from RVND
regulatory_population) + the load_instruments CSV parser. The csv_path is
injected; the env resolver + populate_* stay in RVND."""
from __future__ import annotations

import pytest

from loomground_legal import CODE, DOMAIN, TRANCHES, load_instruments


# ── curated data parity ────────────────────────────────────────────────────────

def test_code_map_values():
    assert len(CODE) == 12
    assert CODE["32016R0679"] == "gdpr"
    assert CODE["32024R1689"] == "ai-act"
    assert CODE["31995L0046"] == "dpd-95"
    assert CODE["32022L2555"] == "nis2"
    assert CODE["32014R0910"] == "eidas"


def test_domain_map_values():
    assert DOMAIN["gdpr"] == ("data",)
    assert DOMAIN["ai-act"] == ("ai",)
    assert DOMAIN["dsa"] == ("platform",)
    assert DOMAIN["dma"] == ("digital-markets",)
    assert DOMAIN["eidas"] == ("digital-identity",)


def test_tranches_order_and_membership():
    assert [name for name, _ in TRANCHES] == [
        "data-protection", "cybersecurity", "ai-governance",
        "platform-content", "digital-markets", "data-economy"]
    assert TRANCHES[0][1] == ["31995L0046", "32016R0679", "32002L0058"]
    assert TRANCHES[2][1] == ["32024R1689"]


# ── load_instruments CSV parser ────────────────────────────────────────────────

_CSV = ("celex,short,source,in_force_from,superseded_by,note\n"
        "32016R0679,GDPR,https://eur-lex.europa.eu/eli/reg/2016/679/oj,2018-05-25,,\n"
        "31995L0046,Data Protection Directive,https://eur-lex.europa.eu/eli/dir/1995/46/oj,"
        "1995-12-13,32016R0679,repealed by the GDPR\n")


def test_load_instruments_parses_rows(tmp_path):
    p = tmp_path / "instruments.csv"
    p.write_text(_CSV, encoding="utf-8")
    inst = load_instruments(p)
    assert set(inst) == {"32016R0679", "31995L0046"}
    gdpr = inst["32016R0679"]
    assert gdpr["short"] == "GDPR"
    assert gdpr["in_force_from"] == "2018-05-25"
    assert inst["31995L0046"]["superseded_by"] == "32016R0679"


def test_load_instruments_requires_path():
    with pytest.raises(FileNotFoundError):
        load_instruments(None)


def test_load_instruments_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_instruments(tmp_path / "nope.csv")
