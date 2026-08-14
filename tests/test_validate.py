# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Corpus validation at the WorldMap level — authority tiers + official-host
allow-list (lifted verbatim from host corpus/validate). The validate_registry
wrapper (EntityRegistry) stays in host."""
from __future__ import annotations

from loomground_legal import Entity, EntityKind, WorldMap, validate_corpus
from loomground_legal.validate import (
    INSTITUTIONAL, PRIMARY_LAW, SECONDARY, _host_ok, _is_eli,
)


def _world() -> WorldMap:
    w = WorldMap()
    # a clean, official instrument (ELI on EUR-Lex → primary-law, reachable)
    w.add(Entity("gdpr", "GDPR", EntityKind.INSTRUMENT,
                 url="https://eur-lex.europa.eu/eli/reg/2016/679/oj",
                 domains=("data",), source="seed"))
    # the superseded predecessor, still listed
    w.add(Entity("dpd-95", "Data Protection Directive", EntityKind.INSTRUMENT,
                 url="https://eur-lex.europa.eu/eli/dir/1995/46/oj", source="seed"))
    w.connect("gdpr", "supersedes", "dpd-95")
    # a regulator on an official host → institutional
    w.add(Entity("cnil", "CNIL", EntityKind.REGULATOR, url="https://www.cnil.fr", source="seed"))
    # an instrument on an OFF-allow-list host → unverified-host + secondary
    w.add(Entity("shady", "Some Law", EntityKind.INSTRUMENT,
                 url="https://random-blog.example.com/law", source="user"))
    # an instrument with NO url at all → missing
    w.add(Entity("nourl", "Unlinked Law", EntityKind.INSTRUMENT, source="ingest"))
    return w


def test_host_allow_list_helpers():
    assert _host_ok("https://eur-lex.europa.eu/x")        # exact
    assert _host_ok("https://www.legislation.gov.uk/x")   # suffix .gov.uk
    assert _host_ok("https://foo.europa.eu/x")            # suffix .europa.eu
    assert not _host_ok("https://random-blog.example.com/x")
    assert not _host_ok("ftp://eur-lex.europa.eu/x")      # wrong scheme
    assert _is_eli("https://eur-lex.europa.eu/eli/reg/2016/679/oj")


def test_authority_tiers():
    rep = validate_corpus(_world())
    by = {f["code"]: f for f in rep["findings"]}
    assert by["gdpr"]["authority"] == PRIMARY_LAW        # ELI instrument
    assert by["cnil"]["authority"] == INSTITUTIONAL      # regulator on official host
    assert by["shady"]["authority"] == SECONDARY         # off-allow-list instrument


def test_flags_bad_authority_and_off_allow_list_host():
    rep = validate_corpus(_world())
    by = {f["code"]: f for f in rep["findings"]}
    # off-allow-list host is flagged unverified with an issue recorded
    assert by["shady"]["reachability"] == "unverified-host"
    assert any("unverified-host" in i for i in by["shady"]["issues"])
    # missing URL for a corpus entity is flagged
    assert by["nourl"]["reachability"] == "missing"
    assert "shady" in rep["summary"]["unverified_hosts"]
    assert "nourl" in rep["summary"]["missing_url"]


def test_flags_superseded_but_still_listed():
    rep = validate_corpus(_world())
    by = {f["code"]: f for f in rep["findings"]}
    assert by["dpd-95"]["currency"] == "superseded"
    assert by["gdpr"]["currency"] == "current"
    assert "dpd-95" in rep["summary"]["superseded"]


def test_summary_by_authority_and_clean_count():
    rep = validate_corpus(_world())
    s = rep["summary"]
    assert s["entities"] == 5
    assert "gdpr" in s["by_authority"][PRIMARY_LAW]
    assert "cnil" in s["by_authority"][INSTITUTIONAL]
    # gdpr and cnil are clean (no issues); the other three have issues
    assert s["clean"] == 2


def test_probe_injection_overrides_structural_reachability():
    w = WorldMap()
    w.add(Entity("gdpr", "GDPR", EntityKind.INSTRUMENT,
                 url="https://eur-lex.europa.eu/eli/reg/2016/679/oj", source="seed"))
    rep = validate_corpus(w, probe=lambda url: False)   # live probe says unreachable
    f = rep["findings"][0]
    assert f["reachability"] == "unreachable"
    assert "gdpr" in rep["summary"]["unverified_hosts"]
