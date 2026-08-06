# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The markdown reference-table parser + code maps (lifted verbatim from RVND
world_corpus_loader). build_world(refdir) is injected — the package resolves no
env or home directory."""
from __future__ import annotations

import pytest

from loomground_legal import EU27, EntityKind, build_world, parse_md
from loomground_legal import corpus_loader as CL


# ── curated maps parity ────────────────────────────────────────────────────────

def test_eu27_and_country_maps():
    assert len(EU27) == 27
    assert EU27[:3] == ["AT", "BE", "BG"] and EU27[-1] == "SE"
    assert CL._COUNTRY["US"] == ("United States", "Americas")
    assert CL._COUNTRY["JP"] == ("Japan", "Asia-Pacific")
    assert CL._BODY_CODE["council of europe"] == "coe"
    assert CL._BODY_CODE["iso/iec"] == "iso-iec"


def test_org_code_prefers_leading_acronym_not_country():
    assert CL._org_code("CNIL (France)") == "cnil"
    assert CL._org_code("Council of Europe") == "coe"           # canonical map
    assert CL._slug("General Data Protection Regulation (GDPR)") == "gdpr"


# ── parse_md + build_world over a small on-disk corpus ─────────────────────────

_ORGS = """# Regulators
| Name | Homepage URL | Role | Main Seat |
| --- | --- | --- | --- |
| CNIL (France) | https://www.cnil.fr | DPA | Paris |
"""

_LAWS = """# EU
| Name | URL | Jurisdiction | Category |
| --- | --- | --- | --- |
| General Data Protection Regulation (GDPR) | https://eur-lex.europa.eu/eli/reg/2016/679/oj | EU | data |
"""

_INTLAW = """# Binding treaties
| Name | URL | Type | Body |
| --- | --- | --- | --- |
| Berne Convention | https://wipo.int/berne | Treaty | WIPO |
"""

_STDS = """# ISO
| Standard | URL | Org | Focus |
| --- | --- | --- | --- |
| ISO/IEC 27001 | https://iso.org/27001 | ISO/IEC | infosec |
"""


def _write_corpus(d):
    (d / "international-organisations.md").write_text(_ORGS, encoding="utf-8")
    (d / "digital-laws-global.md").write_text(_LAWS, encoding="utf-8")
    (d / "international-law.md").write_text(_INTLAW, encoding="utf-8")
    (d / "harmonized-standards.md").write_text(_STDS, encoding="utf-8")


def test_parse_md_reads_section_and_rows(tmp_path):
    p = tmp_path / "orgs.md"
    p.write_text(_ORGS, encoding="utf-8")
    rows = parse_md(p)
    assert len(rows) == 1
    section, row = rows[0]
    assert section == "Regulators"
    assert row["Name"] == "CNIL (France)"
    assert row["Homepage URL"] == "https://www.cnil.fr"


def test_build_world_requires_injected_refdir():
    with pytest.raises(ValueError):
        build_world(None)


def test_build_world_assembles_the_graph(tmp_path):
    _write_corpus(tmp_path)
    w = build_world(tmp_path)
    # EU + all 27 members present, each member_of EU
    assert w.get("EU").kind is EntityKind.SUPRANATIONAL
    assert all(w.get(c) is not None for c in EU27)
    member_edges = {(e.subject, e.object) for e in w.edges if e.connection == "member_of"}
    assert ("DE", "EU") in member_edges and len(member_edges) == 27
    # organisation → regulator (kind from the "Regulators" section)
    assert w.get("cnil").kind is EntityKind.REGULATOR
    # instrument applies_in its jurisdiction
    assert w.get("gdpr").kind is EntityKind.INSTRUMENT
    assert ("gdpr", "applies_in", "EU") in {(e.subject, e.connection, e.object) for e in w.edges}
    # treaty adopted_by its body; standard established_by its org
    es = {(e.subject, e.connection, e.object) for e in w.edges}
    assert ("berne-convention", "adopted_by", "wipo") in es
    assert ("iso-iec-27001", "established_by", "iso-iec") in es
