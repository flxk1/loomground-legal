# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Legal-field (branch-of-law) profiles. A field declares which of the five
solver Dimensions carry its weight and the branch doctrine per dimension; nD is
modelled as MetaDoctrine, NOT a sixth Dimension. Administrative law is the
institutional branch — authorities/offices carrying competence, the
Verwaltungsakt, legal basis + proportionality as the meta-plane. The mechanism
(Dimension, composition, proportionality) is the solver's and is only referenced,
never re-grown."""
from __future__ import annotations

import pytest

from loomground_solver import Dimension

from loomground_legal import LegalField, context
from loomground_legal import legal_field as lf
from loomground_legal.source_classes import Effect


# ── registry is fail-closed ──────────────────────────────────────────────────

def test_default_is_civil_and_known_fields_resolve() -> None:
    assert lf.DEFAULT == "civil"
    assert lf.get().code == "civil"
    assert {"civil", "administrative"} <= set(lf.available())


def test_unknown_field_raises() -> None:
    with pytest.raises(KeyError):
        lf.get("maritime")


def test_register_adds_a_pack() -> None:
    probe = LegalField(code="probe_field", name="probe",
                       load_bearing=(Dimension.STRUCTURAL,))
    try:
        lf.register(probe)
        assert lf.get("probe_field").name == "probe"
    finally:
        lf._REGISTRY.pop("probe_field", None)


# ── the five Dimensions are universal; nD is NOT a sixth ─────────────────────

def test_load_bearing_are_only_the_five_solver_dimensions() -> None:
    for code in lf.available():
        for dim in lf.get(code).load_bearing:
            assert isinstance(dim, Dimension), "load_bearing must be solver.Dimension"
    # nD is carried by meta_doctrine, never as a Dimension member
    assert not hasattr(Dimension, "ND")


def test_meta_doctrine_is_the_nd_plane() -> None:
    admin = lf.get("administrative")
    ids = {m.doctrine_id for m in admin.meta_doctrine}
    assert {"legal_basis", "proportionality"} <= ids
    # each meta-doctrine delegates its resolution, never re-implements it
    assert admin.meta("proportionality").consumes == "solver.proportionality"
    assert admin.meta("legal_basis").consumes == "source_classes"


# ── administrative law — the institutional deep read ─────────────────────────

def test_administrative_leads_with_competence_relational() -> None:
    admin = lf.get("administrative")
    assert admin.leads_with(Dimension.RELATIONAL)
    comp = admin.doctrine_for(Dimension.RELATIONAL)
    assert comp is not None and comp.doctrine_id == "competence"
    assert "competence contested" in comp.escalates_when


def test_authorities_carry_competence_and_emit_acts() -> None:
    admin = lf.get("administrative")
    auth = admin.actor("authority")
    assert auth is not None and auth.entity_kind == "public_body"
    # hierarchical competence distinguishes an authority from a bare office
    assert "hierarchical" in auth.competence_axes
    assert "hierarchical" not in admin.actor("office").competence_axes
    assert "administrative_act" in admin.may_emit("authority")


def test_verwaltungsakt_is_the_characteristic_binding_act() -> None:
    admin = lf.get("administrative")
    acts = dict(admin.characteristic_acts)
    assert acts["administrative_act"] is Effect.BINDING
    assert acts["real_act"] is Effect.INTERPRETIVE   # a Realakt does not bind


def test_administrative_escalates_on_discretion() -> None:
    admin = lf.get("administrative")
    assert any("Ermessen" in e for e in admin.escalation_bias)
    va = admin.doctrine_for(Dimension.INTENTIONAL)
    assert any("Ermessen" in e for e in va.escalates_when)


# ── civil contrasts with administrative on the same dimensions ───────────────

def test_civil_causation_differs_from_the_criminal_test() -> None:
    civil = lf.get("civil")
    causal = civil.doctrine_for(Dimension.CAUSAL)
    assert causal.doctrine_id == "adequate_cause"   # NOT objektive_zurechnung
    assert civil.leads_with(Dimension.RELATIONAL)


# ── criminal law — same dimensions, branch-unique doctrine ───────────────────

def test_criminal_leads_with_mens_rea_and_uses_objektive_zurechnung() -> None:
    crim = lf.get("criminal")
    assert crim.leads_with(Dimension.INTENTIONAL)
    # the branch-unique causal test — distinct from civil adequate_cause
    assert crim.doctrine_for(Dimension.CAUSAL).doctrine_id == "objektive_zurechnung"
    assert crim.doctrine_for(Dimension.INTENTIONAL).doctrine_id == "mens_rea"
    assert crim.doctrine_for(Dimension.RELATIONAL).doctrine_id == "taeterschaft_teilnahme"


def test_criminal_three_tier_aufbau_and_strict_legality() -> None:
    crim = lf.get("criminal")
    assert crim.analysis_structure[0].startswith("Tatbestand")
    assert "Rechtswidrigkeit" in crim.analysis_structure[1]
    assert "Schuld" in crim.analysis_structure[2]
    # nulla poena sine lege — an ABSOLUTE retroactivity bar (vs the admin balance)
    npsl = crim.meta("nulla_poena_sine_lege")
    assert npsl is not None and npsl.consumes == "source_classes"
    assert any("in dubio pro reo" in e for e in crim.escalation_bias)


# ── constitutional law — the nD-dominant branch, proportionality-driven ──────

def test_constitutional_is_proportionality_driven() -> None:
    const = lf.get("constitutional")
    # a fundamental right is a PRINCIPLE (weighed), led by the intentional dimension
    assert const.leads_with(Dimension.INTENTIONAL)
    assert const.doctrine_for(Dimension.INTENTIONAL).doctrine_id == "grundrecht"
    # proportionality delegates to the solver op; Wesensgehalt is an absolute bar
    prop = const.meta("proportionality")
    assert prop is not None and prop.consumes == "solver.proportionality"
    assert const.meta("wesensgehalt") is not None
    assert const.analysis_structure[0].startswith("Schutzbereich")


# ── (jurisdiction × field) context composes with legal_systems ───────────────

def test_context_pairs_jurisdiction_and_field() -> None:
    system, fld = context("DE", "administrative")
    assert system.code == "DE"
    assert fld.code == "administrative"
    # default context = DE civil
    sys0, fld0 = context()
    assert sys0.code == "DE" and fld0.code == "civil"
