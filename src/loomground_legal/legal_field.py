# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Legal-field (branch-of-law) profiles — the second parameterization axis.

``legal_systems`` parameterizes one axis of a legal context: the **jurisdiction
family** (DE/EU/UK/US — authority hierarchy, conflict principles, citation
forms). This module adds the orthogonal axis — the **field / branch of law**
(civil · criminal · administrative · constitutional …). A concrete legal context
is a ``(jurisdiction × field)`` pair: German administrative law = ``(DE,
administrative)``.

The **five factual+intentional dimensions are universal** — they live in
``loomground_solver.Dimension`` (STRUCTURAL · CAUSAL · INTENTIONAL · TEMPORAL ·
RELATIONAL) and stay there; the composition mechanism is the solver's. What a
branch varies is *which dimensions carry the weight* and *the doctrine within a
dimension* — and that is domain content, so it is an injected profile here, not
a fork of the mechanism. Criminal "causation" (objektive Zurechnung) and civil
"causation" (adequate cause) are the **same Dimension, different doctrine** —
which is exactly why a branch is a profile *over* the five, not a sixth kind of
reasoning.

**nD is not a sixth Dimension.** ``solver.Dimension`` has exactly five members.
The *meta-plane* — norms about norms: validity, competence-as-meta-norm, the
legal-basis requirement, proportionality-as-constraint — is modelled as
:class:`MetaDoctrine`, whose *resolution* is delegated to an existing mechanism
(``source_classes``, ``solver.proportionality``), never re-grown. Competence
between actors is a *relation*, so it lives under RELATIONAL and composes through
``legal.connection`` (a ``solver.RelationAlgebra``); the legal-basis and
proportionality constraints are the nD half.

Pure stdlib; data only. Consumes ``solver.Dimension`` + ``source_classes.Effect``;
links actors to the plane's existing ``entities.Body`` / ``world.EntityKind``.
Seeded: civil (baseline) + administrative (the institutional branch, in full).
Register finer packs (criminal, constitutional, tax, …) as verticals need them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from loomground_solver import Dimension

from .source_classes import Effect

__all__ = [
    "DimensionDoctrine",
    "MetaDoctrine",
    "ActorKind",
    "LegalField",
    "get",
    "available",
    "register",
    "DEFAULT",
    "context",
]


@dataclass(frozen=True)
class DimensionDoctrine:
    """The branch-specific doctrine that fills ONE of the five Dimensions for a
    field. The Dimension + its composition are the solver's; only the *rule name*
    and gloss are domain content. ``escalates_when`` names the branch-typical
    open points on this dimension (fed to the [E] router)."""
    dimension: Dimension
    doctrine_id: str
    gloss: str
    escalates_when: tuple[str, ...] = ()


@dataclass(frozen=True)
class MetaDoctrine:
    """An nD (norm-about-norms) doctrine — NOT one of the five Dimensions. The
    meta-plane is modelled here; its *resolution* is delegated to the named
    mechanism (``consumes``), never re-implemented in the profile."""
    doctrine_id: str
    gloss: str
    consumes: str = ""          # the mechanism that resolves it (e.g. "solver.proportionality")
    escalates_when: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActorKind:
    """A role the branch reasons about. For PUBLIC law these are the institutions
    — authorities, offices, supervisory bodies — carrying *competence*. It links
    to the plane's existing ``entities.Body`` / ``world.EntityKind`` via
    ``entity_kind``; it does NOT re-grow an entity model."""
    code: str
    name: str
    entity_kind: str = ""                 # links to legal.world.EntityKind / entities.Body.kind
    competence_axes: tuple[str, ...] = ()  # admin: ("subject_matter","territorial","hierarchical")
    may_produce: tuple[str, ...] = ()      # the act kinds this actor may emit


@dataclass(frozen=True)
class LegalField:
    code: str                              # "civil" | "criminal" | "administrative" | "constitutional"
    name: str
    # the five Dimensions ordered by how much weight the branch puts on them
    load_bearing: tuple[Dimension, ...]
    # branch doctrine per Dimension (only where it differs from the generic read)
    doctrine: tuple[DimensionDoctrine, ...] = ()
    # the nD / meta-plane doctrines (legal basis, proportionality, competence-as-meta)
    meta_doctrine: tuple[MetaDoctrine, ...] = ()
    # the branch's analytical structure (its Aufbau) — an ordered checklist, not logic
    analysis_structure: tuple[str, ...] = ()
    # the roles / institutions the branch reasons about
    actor_kinds: tuple[ActorKind, ...] = ()
    # the branch's characteristic operative act(s) + the Effect each carries
    characteristic_acts: tuple[tuple[str, Effect], ...] = ()
    # where the branch structurally tends to ESCALATE (feeds the [E] router)
    escalation_bias: tuple[str, ...] = ()

    def doctrine_for(self, dim: Dimension) -> Optional[DimensionDoctrine]:
        """The branch doctrine filling ``dim``, or None if the generic read holds."""
        return next((d for d in self.doctrine if d.dimension is dim), None)

    def meta(self, doctrine_id: str) -> Optional[MetaDoctrine]:
        return next((m for m in self.meta_doctrine if m.doctrine_id == doctrine_id), None)

    def actor(self, code: str) -> Optional[ActorKind]:
        return next((a for a in self.actor_kinds if a.code == code), None)

    def may_emit(self, actor_code: str) -> tuple[str, ...]:
        """The act kinds an actor of ``actor_code`` may produce ('' if unknown)."""
        a = self.actor(code=actor_code)
        return a.may_produce if a is not None else ()

    def leads_with(self, dim: Dimension) -> bool:
        """Is ``dim`` the branch's most load-bearing dimension?"""
        return bool(self.load_bearing) and self.load_bearing[0] is dim


# ── Packs ─────────────────────────────────────────────────────────────────────

# CIVIL / private law — the baseline. Relational (who owes whom) + intentional
# (the obligation) dominate; the meta-plane is light (private autonomy).
CIVIL = LegalField(
    code="civil", name="Civil / private law",
    load_bearing=(Dimension.RELATIONAL, Dimension.INTENTIONAL,
                  Dimension.STRUCTURAL, Dimension.TEMPORAL, Dimension.CAUSAL),
    doctrine=(
        DimensionDoctrine(Dimension.RELATIONAL, "privity_agency",
            "Parties, privity, and agency (Stellvertretung): a declaration binds "
            "the principal only within the agent's authority.",
            escalates_when=("authority scope contested",)),
        DimensionDoctrine(Dimension.INTENTIONAL, "obligation",
            "The claim-right (Anspruch) and its Hohfeldian correlative duty; a "
            "'right' is never a fourth operator — it reduces to a claim or a liberty."),
        DimensionDoctrine(Dimension.CAUSAL, "adequate_cause",
            "Adäquate Kausalität: liability-founding and liability-filling "
            "causation (§ 823 BGB), not the criminal objektive-Zurechnung test."),
        DimensionDoctrine(Dimension.TEMPORAL, "limitation",
            "Verjährung (limitation) and performance time; a time-barred claim "
            "survives as an Anspruch but is no longer durchsetzbar."),
    ),
    analysis_structure=(
        "Anspruch entstanden? (has the claim arisen — Anspruchsgrundlage)",
        "Anspruch untergegangen? (has it lapsed — Einwendungen)",
        "Anspruch durchsetzbar? (is it enforceable — Einreden, e.g. limitation)",
    ),
    actor_kinds=(
        ActorKind("party", "Partei", entity_kind="person"),
        ActorKind("agent", "Vertreter", entity_kind="person", may_produce=("declaration",)),
        ActorKind("third_party", "Dritter", entity_kind="person"),
    ),
    characteristic_acts=(("contract", Effect.BINDING),
                         ("unilateral_declaration", Effect.BINDING)),
    escalation_bias=("unbestimmter Rechtsbegriff (Treu und Glauben § 242; gute Sitten § 138)",),
)


# ── ADMINISTRATIVE / public law — the institutional branch, in full ───────────
# Where 'who may act' is a first-class legal question. Relational (competence)
# leads; the nD half (legal basis + proportionality) is load-bearing meta.

_ADDRESSEE = ActorKind("addressee", "Adressat", entity_kind="person")
_OFFICE = ActorKind(
    "office", "Amt/Dienststelle", entity_kind="public_body",
    competence_axes=("subject_matter", "territorial"))
_AUTHORITY = ActorKind(
    "authority", "Behörde", entity_kind="public_body",
    competence_axes=("subject_matter", "territorial", "hierarchical"),
    may_produce=("administrative_act", "by_law", "real_act"))
_SUPERVISORY = ActorKind(
    "supervisory_body", "Aufsichtsbehörde", entity_kind="public_body",
    competence_axes=("hierarchical",),
    may_produce=("supervisory_measure",))

ADMINISTRATIVE = LegalField(
    code="administrative", name="Administrative / public law",
    # relational (competence) + intentional (the act) + temporal (finality) lead;
    # the nD weight lives in meta_doctrine below (nD is not a sixth Dimension).
    load_bearing=(Dimension.RELATIONAL, Dimension.INTENTIONAL, Dimension.TEMPORAL,
                  Dimension.STRUCTURAL, Dimension.CAUSAL),
    doctrine=(
        DimensionDoctrine(Dimension.RELATIONAL, "competence",
            "Zuständigkeit: sachlich (subject-matter) · örtlich (territorial) · "
            "instanziell (hierarchical). An act by an incompetent authority is "
            "formell rechtswidrig. Competence composes as a relation through the "
            "connection algebra; a non-composing chain escalates.",
            escalates_when=("competence contested", "delegation chain does not compose")),
        DimensionDoctrine(Dimension.INTENTIONAL, "administrative_act",
            "Verwaltungsakt: unilateral · individual · external · regulatory. "
            "Binding on the addressee. Ermessen (discretion) and unbestimmte "
            "Rechtsbegriffe are decided by the authority within limits — the "
            "engine surfaces them, never substitutes its own choice.",
            escalates_when=("Ermessen (discretion)", "unbestimmter Rechtsbegriff")),
        DimensionDoctrine(Dimension.TEMPORAL, "bestandskraft",
            "Finality once the appeal deadline lapses; Rücknahme (§ 48 VwVfG) and "
            "Widerruf (§ 49) reopen a final act only on stated grounds.",
            escalates_when=("Rücknahme/Widerruf grounds contested",)),
        DimensionDoctrine(Dimension.STRUCTURAL, "act_qualification",
            "Is the measure a Verwaltungsakt at all (vs a Realakt, a by-law, or an "
            "internal instruction)? The qualification gates the whole review.",
            escalates_when=("act qualification unclear",)),
        DimensionDoctrine(Dimension.CAUSAL, "gefahr",
            "For hazard-prevention (Gefahrenabwehr): the causal risk the measure "
            "addresses. Often only presupposed by the record → open, not asserted.",
            escalates_when=("causal risk only presupposed",)),
    ),
    meta_doctrine=(
        MetaDoctrine("legal_basis",
            "Vorbehalt des Gesetzes: a burdening act requires an "
            "Ermächtigungsgrundlage. The authorizing norm must itself be BINDING "
            "and in force — checked via the source-class map; no basis → the act "
            "cannot stand.",
            consumes="source_classes",
            escalates_when=("legal basis absent or unclear",)),
        MetaDoctrine("proportionality",
            "Verhältnismäßigkeit as a meta-constraint on every discretionary "
            "measure: legitimate aim · Geeignetheit · Erforderlichkeit · "
            "Angemessenheit. Delegated whole to the solver's proportionality op; "
            "a failed prong or a genuine tie escalates, never a coin-flip.",
            consumes="solver.proportionality",
            escalates_when=("failed prong", "genuine balancing tie")),
    ),
    analysis_structure=(
        "Ermächtigungsgrundlage (is there a legal basis?)",
        "formelle Rechtmäßigkeit: Zuständigkeit · Verfahren · Form",
        "materielle Rechtmäßigkeit: Tatbestand · Rechtsfolge · Ermessen/Verhältnismäßigkeit",
    ),
    actor_kinds=(_AUTHORITY, _OFFICE, _SUPERVISORY, _ADDRESSEE),
    characteristic_acts=(("administrative_act", Effect.BINDING),
                         ("by_law", Effect.BINDING),
                         ("real_act", Effect.INTERPRETIVE)),
    escalation_bias=("Ermessen (discretion)", "unbestimmter Rechtsbegriff",
                     "competence dispute", "proportionality tie"),
)


# ── CRIMINAL law — intentional (mens rea) + causal (attribution) lead ─────────
# The branch where the *subjective* side and a branch-unique causal test carry
# the weight, under a strict legality meta-rule and in dubio pro reo.

CRIMINAL = LegalField(
    code="criminal", name="Criminal law",
    load_bearing=(Dimension.INTENTIONAL, Dimension.CAUSAL, Dimension.STRUCTURAL,
                  Dimension.RELATIONAL, Dimension.TEMPORAL),
    doctrine=(
        DimensionDoctrine(Dimension.INTENTIONAL, "mens_rea",
            "The subjective Tatbestand: Vorsatz (dolus directus 1./2. Grades, "
            "dolus eventualis) vs Fahrlässigkeit. A Vorsatzdelikt is not made out "
            "on negligence; the dolus-eventualis / bewusste-Fahrlässigkeit line is "
            "the classic contested point.",
            escalates_when=("dolus eventualis vs bewusste Fahrlässigkeit",)),
        DimensionDoctrine(Dimension.CAUSAL, "objektive_zurechnung",
            "Objective attribution — beyond but-for (Äquivalenz): the actor must "
            "have created a legally disapproved risk that realised in the result. "
            "An atypical causal course or eigenverantwortliche Selbstgefährdung "
            "breaks attribution — the branch-unique causal test.",
            escalates_when=("risk realisation contested", "atypical causal course")),
        DimensionDoctrine(Dimension.RELATIONAL, "taeterschaft_teilnahme",
            "Perpetration (Täterschaft: Allein-, Mit-, mittelbare — by Tatherrschaft) "
            "vs participation (Teilnahme: Anstiftung, Beihilfe). The boundary "
            "governs the offender's role and is often contested.",
            escalates_when=("Täterschaft vs Teilnahme contested",)),
        DimensionDoctrine(Dimension.STRUCTURAL, "tatbestand",
            "The objective Tatbestand — the offence's defining elements; the "
            "conduct must be classified under them (strict, no analogy to the "
            "defendant's detriment)."),
        DimensionDoctrine(Dimension.TEMPORAL, "lex_mitior",
            "Tatzeit + Verjährung, and § 2 StGB lex mitior: the MILDER law between "
            "act and judgment applies — criminal law's own intertemporal rule, "
            "distinct from the civil/administrative tempus regit actum default."),
    ),
    meta_doctrine=(
        MetaDoctrine("nulla_poena_sine_lege",
            "Art. 103(2) GG / § 1 StGB: no punishment without a prior WRITTEN "
            "statute — Bestimmtheitsgebot (definiteness), Analogieverbot (no "
            "analogy against the accused), and an ABSOLUTE Rückwirkungsverbot "
            "(retroactive criminalisation is categorically barred, unlike the "
            "administrative echte-Rückwirkung balance). The penal norm must be a "
            "binding statute.",
            consumes="source_classes",
            escalates_when=("analogy to the accused's detriment", "norm too vague")),
    ),
    analysis_structure=(
        "Tatbestand (objektiv: conduct · objektive Zurechnung; subjektiv: mens rea)",
        "Rechtswidrigkeit (Rechtfertigungsgründe, e.g. Notwehr § 32)",
        "Schuld (Schuldfähigkeit, Unrechtsbewusstsein, Entschuldigungsgründe)",
    ),
    actor_kinds=(
        ActorKind("perpetrator", "Täter", entity_kind="person"),
        ActorKind("accomplice", "Teilnehmer (Anstifter/Gehilfe)", entity_kind="person"),
        ActorKind("victim", "Verletzter/Opfer", entity_kind="person"),
    ),
    characteristic_acts=(("criminal_judgment", Effect.BINDING),),
    escalation_bias=("in dubio pro reo (doubt favours the accused)",
                     "dolus eventualis vs bewusste Fahrlässigkeit",
                     "objektive Zurechnung (risk realisation)",
                     "Täterschaft vs Teilnahme"),
)


# ── CONSTITUTIONAL law — the nD-dominant branch (reasoning ABOUT other norms) ─
# Fundamental-rights review is mostly meta: a right is a PRINCIPLE applied by
# weighing (proportionality), and the review tests a state measure against it.

CONSTITUTIONAL = LegalField(
    code="constitutional", name="Constitutional law",
    load_bearing=(Dimension.INTENTIONAL, Dimension.STRUCTURAL, Dimension.RELATIONAL,
                  Dimension.CAUSAL, Dimension.TEMPORAL),
    doctrine=(
        DimensionDoctrine(Dimension.INTENTIONAL, "grundrecht",
            "A fundamental right is a PRINCIPLE, not a rule — applied by weighing, "
            "not subsumption (a value in the deontic mode). Routing it through "
            "rule-subsumption is a category error; its limitation is decided by "
            "proportionality.",
            escalates_when=("balancing tie (Abwägung)",)),
        DimensionDoctrine(Dimension.STRUCTURAL, "schutzbereich",
            "Schutzbereich: is the conduct within the right's scope of protection? "
            "The structural gate before any Eingriff/Rechtfertigung question.",
            escalates_when=("scope of protection contested",)),
        DimensionDoctrine(Dimension.RELATIONAL, "state_citizen",
            "The vertical state↔citizen relation — an Eingriff is a state intrusion "
            "into the protected scope; horizontal effect reaches private relations "
            "only mittelbar (indirect Drittwirkung)."),
    ),
    meta_doctrine=(
        MetaDoctrine("proportionality",
            "Verhältnismäßigkeit is THE justification test: legitimate aim · "
            "Geeignetheit · Erforderlichkeit · Angemessenheit (Abwägung). Delegated "
            "whole to the solver's proportionality op (Alexy Weight Formula); a "
            "failed prong or a genuine tie → escalate, never a coin-flipped winner.",
            consumes="solver.proportionality",
            escalates_when=("failed prong", "genuine balancing tie")),
        MetaDoctrine("wesensgehalt",
            "Art. 19(2) GG: the essence of a right may NEVER be touched — an "
            "absolute limit that defeats a measure regardless of proportionality.",
            consumes="",
            escalates_when=("essence boundary contested",)),
        MetaDoctrine("schranken_schranken",
            "Limits-on-limits: a limiting law must itself be constitutional "
            "(formell + materiell), general (Art. 19(1) GG), and respect the "
            "Zitiergebot.",
            consumes="source_classes"),
    ),
    analysis_structure=(
        "Schutzbereich (is the conduct within the right's scope?)",
        "Eingriff (is there a state intrusion?)",
        "verfassungsrechtliche Rechtfertigung (Schranke · Schranken-Schranke · "
        "Verhältnismäßigkeit)",
    ),
    actor_kinds=(
        ActorKind("bearer", "Grundrechtsträger", entity_kind="person"),
        ActorKind("state", "Hoheitsträger/Staat", entity_kind="public_body",
                  may_produce=("state_measure",)),
        ActorKind("legislator", "Gesetzgeber", entity_kind="public_body",
                  may_produce=("limiting_law",)),
    ),
    characteristic_acts=(("limiting_law", Effect.BINDING),
                         ("state_measure", Effect.BINDING)),
    escalation_bias=("Verhältnismäßigkeit tie (Abwägung)", "Wesensgehalt boundary",
                     "Schutzbereich scope contested"),
)


_REGISTRY: dict[str, LegalField] = {
    "civil": CIVIL,
    "administrative": ADMINISTRATIVE,
    "criminal": CRIMINAL,
    "constitutional": CONSTITUTIONAL,
}

DEFAULT = "civil"


def get(code: Optional[str] = None) -> LegalField:
    """Return the field pack for ``code`` (default civil). Unknown code → KeyError,
    so a typo never silently falls back to the wrong branch of law."""
    code = (code or DEFAULT).lower()
    if code not in _REGISTRY:
        raise KeyError(f"unknown legal field {code!r}; available: {available()}")
    return _REGISTRY[code]


def available() -> list[str]:
    return sorted(_REGISTRY)


def register(field_pack: LegalField) -> None:
    """Add or override a field pack (e.g. a vertical contributing tax/social law)."""
    _REGISTRY[field_pack.code.lower()] = field_pack


def context(system_code: Optional[str] = None, field_code: Optional[str] = None):
    """The concrete legal context as a ``(LegalSystem, LegalField)`` pair — the
    (jurisdiction × field) cell, e.g. ``context("DE", "administrative")`` = German
    administrative law. Consumes ``legal_systems``; defines no jurisdiction data."""
    from . import legal_systems
    return (legal_systems.get(system_code), get(field_code))
