# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The relational pass — curated membership/treaty/adequacy/regulator DATA
(lifted verbatim from RVND world_relations) and enrich()'s edge derivation over
a seeded WorldMap. Instruments are injected, not env-resolved."""
from __future__ import annotations

from loomground_legal import Entity, EntityKind, WorldMap, enrich
from loomground_legal import relations as R


def _seed() -> WorldMap:
    w = WorldMap()
    w.add(Entity("EU", "European Union", EntityKind.SUPRANATIONAL))
    for c, n in [("DE", "Germany"), ("FR", "France"), ("US", "United States"),
                 ("UK", "United Kingdom"), ("JP", "Japan")]:
        w.add(Entity(c, n, EntityKind.STATE, jurisdiction=c))
    w.add(Entity("coe", "Council of Europe", EntityKind.INTERNATIONAL_REGIME))
    w.add(Entity("oecd", "OECD", EntityKind.INTERNATIONAL_REGIME))
    w.add(Entity("un", "UN", EntityKind.INTERNATIONAL_REGIME))
    w.add(Entity("wto", "WTO", EntityKind.INTERNATIONAL_REGIME))
    w.add(Entity("au", "African Union", EntityKind.INTERNATIONAL_REGIME))
    w.add(Entity("gdpr", "GDPR", EntityKind.INSTRUMENT, jurisdiction="EU", domains=("data",)))
    w.add(Entity("cnil", "CNIL", EntityKind.REGULATOR))
    w.add(Entity("ftc", "FTC", EntityKind.REGULATOR))
    w.add(Entity("echr", "European Convention on Human Rights (ECHR)", EntityKind.INSTRUMENT))
    w.add(Entity("berne", "Berne Convention", EntityKind.INSTRUMENT))
    w.add(Entity("trips", "TRIPS Agreement", EntityKind.INSTRUMENT))
    w.add(Entity("budapest", "Budapest Convention", EntityKind.INSTRUMENT))
    return w


def _edgeset(w: WorldMap):
    return {(e.subject, e.connection, e.object) for e in w.edges}


# ── curated data parity (byte-identical lift from RVND world_relations) ────────

def test_curated_membership_set_values():
    # Council of Europe = EU27 + these four; Russia expelled 2022.
    assert R._COE == set(R.EU27) | {"UK", "CH", "TR", "UA"}
    assert len(R._COE) == 31
    assert len(R._OECD) == 35 and "RU" not in R._OECD
    assert len(R._WTO) == 64 and "RU" in R._WTO
    assert len(R._BERNE) == 60
    assert len(R._BUDAPEST) == 34
    assert R._ADEQUACY == {"JP", "UK", "CH", "NZ", "AR", "IL", "KR", "CA", "US"}
    assert R._ASEAN == {"SG", "TH", "ID", "MY", "VN", "PH"}
    assert R._AFRICAN_UNION == {"ZA", "NG", "KE", "EG", "GH", "RW", "UG"}
    assert R._DPA_DOMAINS == {"privacy", "data"}


def test_curated_regulator_table():
    assert len(R._REGULATORS) == 26
    assert R._REGULATORS["cnil"] == ("FR", {"privacy", "data"})
    assert R._REGULATORS["ftc"] == ("US", {"privacy"})
    assert R._REGULATORS["cac"] == ("CN", {"privacy", "data", "cyber", "ai", "platform"})
    assert R._REGULATORS["edpb"] == ("EU", {"privacy", "data"})


# ── enrich(): derived edges over a seeded WorldMap ────────────────────────────

def test_enrich_derives_memberships():
    w = _seed()
    enrich(w)
    es = _edgeset(w)
    assert ("DE", "member_of", "coe") in es       # EU27 ⊆ CoE
    assert ("FR", "member_of", "coe") in es
    assert ("US", "member_of", "oecd") in es
    assert ("DE", "member_of", "un") in es         # every state is a UN member
    assert ("JP", "member_of", "wto") in es
    # US is not a CoE member → no such edge
    assert ("US", "member_of", "coe") not in es


def test_enrich_derives_regulator_edges():
    w = _seed()
    enrich(w)
    es = _edgeset(w)
    # a national DPA supervises its jurisdiction and enforces the GDPR
    assert ("cnil", "supervises", "FR") in es
    assert ("cnil", "enforces", "gdpr") in es      # GDPR Art. 51/55 (FR ∈ EU27)
    # the US FTC supervises the US but does NOT enforce the EU GDPR
    assert ("ftc", "supervises", "US") in es
    assert ("ftc", "enforces", "gdpr") not in es


def test_enrich_derives_treaties_and_adequacy():
    w = _seed()
    enrich(w)
    es = _edgeset(w)
    assert ("DE", "party_to", "echr") in es        # CoE membership → ECHR
    assert ("US", "party_to", "berne") in es       # Berne Union
    assert ("DE", "bound_by", "trips") in es       # TRIPS binds WTO members
    assert ("EU", "equivalent_to", "US") in es     # Art. 45 adequacy (DPF)
    assert ("EU", "equivalent_to", "JP") in es
    # DE is not in the adequacy set (it is inside the EU) → no adequacy edge to DE
    assert ("EU", "equivalent_to", "DE") not in es


def test_enrich_merges_injected_acquis_with_supersession():
    w = _seed()
    # celex → row, as load_instruments() returns; the 1995 Directive is
    # superseded_by the GDPR.
    instruments = {
        "31995L0046": {"short": "Data Protection Directive",
                       "source": "https://eur-lex.europa.eu/eli/dir/1995/46/oj",
                       "superseded_by": "32016R0679", "note": "GDPR repealed the DPD"},
    }
    enrich(w, instruments=instruments)
    es = _edgeset(w)
    assert "dpd-95" in w.entities                    # acquis instrument created
    assert w.get("dpd-95").jurisdiction == "EU"
    assert ("dpd-95", "applies_in", "EU") in es
    assert ("gdpr", "supersedes", "dpd-95") in es    # CODE-mapped supersession


def test_enrich_without_instruments_skips_acquis():
    w = _seed()
    stats = enrich(w)                               # instruments=None
    assert "acquis_instruments" not in stats
    assert stats["total_edges"] == len(w.edges)


def test_enrich_returns_stats_dict():
    w = _seed()
    stats = enrich(w)
    assert stats["member_of"] > 0
    assert stats["party_to"] > 0
    assert stats["total_edges"] == len(w.edges)
