# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Anchoring — resolve a rule to the legal instruments/jurisdictions/regulators
that govern it, and cut a law's own text into anchored provisions."""

from __future__ import annotations

from loomground_legal import (
    ANCHOR_KINDS,
    ANCHOR_RELATIONS,
    Anchor,
    TextProvision,
    anchor,
    place_legal_text,
    seed_world,
    segment_provisions,
)


# ── anchor() ────────────────────────────────────────────────────────────────

def test_anchor_places_a_rule_on_the_instrument_that_governs_it():
    # A clause naming the GDPR anchors onto the instrument, its jurisdiction, and
    # its enforcing regulator(s) — resolved against the seeded world.
    world = seed_world()
    text = ("The controller shall erase personal data under the "
            "General Data Protection Regulation unless a retention duty applies.")
    anchors = anchor(text, world)
    pairs = {(a.entity, a.relation) for a in anchors}
    assert ("gdpr", "cites") in pairs                    # cited instrument
    assert ("EU", "governed_by") in pairs                # its jurisdiction
    assert any(rel == "enforced_by" for _, rel in pairs)  # an enforcing regulator
    # regulators come from ``enforces`` edges (edpb / cnil / bfdi on the seed)
    assert any(e == "edpb" and rel == "enforced_by" for e, rel in pairs)


def test_anchor_kinds_and_relations_are_the_closed_vocabulary():
    world = seed_world()
    anchors = anchor("Obligations under the AI Act apply.", world)
    assert anchors, "AI Act should be recognised in the seeded world"
    for a in anchors:
        assert isinstance(a, Anchor)
        assert a.kind in ANCHOR_KINDS
        assert a.relation in ANCHOR_RELATIONS
    assert any(a.entity == "ai-act" and a.kind == "instrument" for a in anchors)


def test_anchor_accepts_injected_candidates_and_a_facets_dict():
    # A consumer with its own recogniser bridges candidates in; the world-walk is
    # identical to the built-in path.
    world = seed_world()
    cands = [{"code": "gdpr", "name": "GDPR", "jurisdiction": "EU",
              "pinpoint": "Art. 17"}]
    from_cands = anchor("", world, candidates=cands)
    # cite basis is the pinpoint when supplied
    cite = next(a for a in from_cands if a.entity == "gdpr" and a.relation == "cites")
    assert cite.basis == "Art. 17"
    # facets dict carries the operative text
    from_facets = anchor(facets={"operative": "Erasure under the "
                                 "General Data Protection Regulation."},
                         world=world)
    assert any(a.entity == "gdpr" and a.relation == "cites" for a in from_facets)


def test_anchor_is_deduplicated_and_empty_in_empty_out():
    world = seed_world()
    assert anchor("", world) == []
    assert anchor("nothing legal is named here at all", world) == []
    anchors = anchor("General Data Protection Regulation", world)
    keys = [(a.entity, a.relation) for a in anchors]
    assert len(keys) == len(set(keys))                   # no duplicate placements


def test_anchor_to_dict_is_the_stable_wire_shape():
    a = Anchor("gdpr", "instrument", "cites", "Art. 17")
    assert a.to_dict() == {"entity": "gdpr", "kind": "instrument",
                           "relation": "cites", "basis": "Art. 17"}


# ── place_legal_text() ──────────────────────────────────────────────────────

_LAW = """\
Article 1
This Regulation lays down rules relating to the protection of natural persons.

Article 17
1. The data subject shall have the right to obtain erasure of personal data.
2. Where the controller has made the personal data public, it shall take steps.
"""


def test_place_legal_text_splits_provisions_and_anchors_each_to_its_host():
    world = seed_world()
    provs = place_legal_text(_LAW, world, "gdpr")
    # Art. 1 (no numbered paragraphs) + Art. 17(1) + Art. 17(2)
    pinpoints = [p["pinpoint"] for p in provs]
    assert pinpoints == ["Art. 1", "Art. 17(1)", "Art. 17(2)"]
    for p in provs:
        entities = {(a.entity, a.relation) for a in p["anchors"]}
        # every provision is cited to the host instrument at its own pinpoint
        assert ("gdpr", "cites") in entities
        # and anchored to the host's jurisdiction + enforcing regulator(s)
        assert ("EU", "governed_by") in entities
        assert any(rel == "enforced_by" for _, rel in entities)
        cite = next(a for a in p["anchors"]
                    if a.entity == "gdpr" and a.relation == "cites")
        assert cite.basis == p["pinpoint"]               # pinpoint is the basis


def test_place_legal_text_accepts_a_custom_splitter():
    world = seed_world()
    provs = place_legal_text("ignored", world, "ai-act",
                             splitter=lambda t: [{"pinpoint": "Art. 5",
                                                  "text": "Prohibited practices.",
                                                  "article": "5",
                                                  "paragraph": None}])
    assert len(provs) == 1
    assert provs[0]["pinpoint"] == "Art. 5"
    assert any(a.entity == "ai-act" and a.relation == "cites"
               for a in provs[0]["anchors"])


def test_segment_provisions_is_a_reusable_builtin():
    provs = segment_provisions(_LAW)
    assert all(isinstance(p, TextProvision) for p in provs)
    assert [p.pinpoint for p in provs] == ["Art. 1", "Art. 17(1)", "Art. 17(2)"]
    assert segment_provisions("no articles here") == []
