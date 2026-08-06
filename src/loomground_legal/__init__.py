# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""loomground-legal — the legal domain plane of the Loomground family.

Legal entities, the jurisdictional connection algebra (data over the solver's
:class:`~loomground_solver.RelationAlgebra`), and legal-effect typing bridged
into deontic O/P/F + Hohfeld incidents. This plane supplies data and bridges
only; all composition, conflict, and inference run on the family's engines.
"""
from ._version import __version__
from .entities import Body, Instrument, Jurisdiction, LegalPerson
from .connection import GOVERNING, connection_algebra, is_connection, load_connections
from .effect import OPERATIVE_CONTENT, LegalEffect, legal_effect
from .scope import GROUND_AXIS, ScopeResult, scope_applies
from .sources import (
    ConflictOutcome,
    Provision,
    load_sources,
    resolve_provisions,
    source_rank,
    to_norm,
)
from .lifecycle import (
    LIFECYCLE_RELATIONS,
    TERMINATING_RELATIONS,
    LifecycleEvent,
    in_force,
    version_in_force,
)
from .citation import Citation, Definition, bind_definition, parse_citation, resolve_xref
from .world import (
    Entity,
    EntityKind,
    GovEntry,
    JURISDICTION_KINDS,
    KIND_TO_FAMILY,
    ReachResult,
    WorldEdge,
    WorldMap,
    load_world_seed,
    seed_world,
)
from .corpus_loader import EU27, build_world, parse_md
from .instruments import CODE, DOMAIN, TRANCHES, load_instruments
from .relations import enrich
from .validate import (
    GENERAL,
    INSTITUTIONAL,
    PRIMARY_LAW,
    SECONDARY,
    SUPPORTING,
    Finding,
    validate_corpus,
)
from .contracts import ContractError, ContractInstance, PartyRef
from .anchoring import (
    ANCHOR_KINDS,
    ANCHOR_RELATIONS,
    Anchor,
    AnchorKind,
    AnchorRelation,
    TextProvision,
    anchor,
    place_legal_text,
    segment_provisions,
)
# competing-definition detection (O34) — consumes citation.Definition
from .definitions import CompetingSet, detect_competing, competing_for_term
# referral-kind classification (O14) — consumes citation.resolve_xref; escalates UNCERTAIN
from .referral import (
    ReferralKind, ReferralClassification, classify_referral,
    RECHTSGRUND_CUES, RECHTSFOLGE_CUES,
)
# instrument cross-reference resolution — consumes instruments.CODE + solver.Dimension;
# resolves a citation to (code · CELEX · label) and types the relation verb onto a Dimension
from .crossref import (
    InstrumentRef, INSTRUMENTS, CrossReference,
    resolve_celex, resolve_citation_number, resolve_short_name,
    infer_host_instrument, extract_cross_references,
)
# document-level summary — consumes crossref.infer_host_instrument for the instrument;
# adds doc-kind classification + identifier + excerpt (one overview per document)
from .document_summary import DocumentSummary, summarize_document
# universal source-class map — the jurisdiction-agnostic half of applicable-law
# theory (source KINDS, effect ceilings, relation vocabulary, incorporation
# invariant). ``Effect`` here is legal FORCE (persuasive→binding), distinct from
# ``effect.LegalEffect`` (the deontic shadow). generic accessors (get/available/
# register/DEFAULT/catalogue) stay submodule-only.
from .source_classes import (
    Effect, SourceClass, Relation, VOCABULARY, SourceFinding,
    is_relation, max_effect, self_executes, requires_incorporation, check_source,
)
# legal-system meta-layer — switchable jurisdiction-family packs (DE/EU/UK/US) +
# the applicable-law resolver (selection → full governing source set; conflicts
# escalate, never auto-resolved). consumes .source_classes.
from .legal_systems import (
    LegalSystem, SourceEntry, SourceRelation, ApplicableLaw,
    applicable_systems, applicable_law,
)
# legal-field (branch-of-law) profiles — the orthogonal axis to legal_systems:
# civil/criminal/administrative/constitutional, each declaring which of the five
# solver Dimensions carry its weight + the branch doctrine per dimension. nD is
# modelled as MetaDoctrine (not a sixth Dimension). generic accessors (get/
# available/register/DEFAULT) stay submodule-only; `context()` pairs it with a
# jurisdiction (legal_systems).
from .legal_field import (
    LegalField, DimensionDoctrine, MetaDoctrine, ActorKind, context,
)
# intertemporal law — which version of a norm governs facts at a time (tempus
# regit actum), the temporal INDEX stamping a conclusion with which-law-as-of-when,
# and retroactivity (echte/unechte Rückwirkung) as a gated question. Consumes
# lifecycle.version_in_force; a contested intertemporal choice escalates.
from .intertemporal import (
    Retroactivity, TemporalIndex, VersionSelection,
    classify_retroactivity, governing_version, select_version, stamp,
)
# instrument identifiers — work-level (CELEX/code) vs expression-level
# (consolidated CELEX / ELI point-in-time). Identity is a stable code, NEVER the
# official title; a version is a work × in-force-date.
from .identifiers import consolidated_celex, eli_at, version_id
# worked reviews — where the branch profile, competence (compose_paths), legal
# basis (source_classes) and intertemporal selection COMPOSE into one graded
# conclusion, folded by the solver's OPEN-dominant fold_verdicts. Operational
# entry point; OPEN (escalate) is the honest terminal, never fabricated.
from .worked import (
    Review, administrative_review, CriminalReview, criminal_review,
    ConstitutionalReview, constitutional_review,
    SubsumptionReview, review_against_facts,
)
# the legal grammar — grammar-first foundation: the canonical legal STATEMENT
# (the composite element unifying the five smeared norm-objects), its recognition
# gate (validate), and the source-hierarchy PARTIAL ORDER (outranks / lex_superior,
# antichain → escalate). Consumes the concrete solver algebras; the lex ordering is
# the one new algebraic piece. Full defeasible (Dung) resolution is NOT here.
from .grammar import (
    LegalStatement, WellFormedness, validate, is_well_formed, outranks, lex_superior,
)
# the legal ALGEBRA — the composition operations over statements: apply (statement
# × facts → conclusion, via subsume_antecedent) and resolve_conflict (statement ×
# statement → the prevailing statement by lex superior → posterior, antichain →
# escalate). Consumes the confirmed solver/legal surfaces; Dung defeasibility NOT here.
from .algebra import (
    Conclusion, apply, Resolution, resolve_conflict,
    Derivation, derive, to_provision, resolve,
)
# legal INCORPORATION / cross-reference — incorporate (source × incorporating →
# does it validly bind? SC-3 honesty: unincorporated directive/treaty → OPEN,
# never fabricated binding) + resolve_reference (citation → InstrumentRef, else
# None). Consumes source_classes force/relations + crossref resolvers.
from .incorporation import (
    Incorporation, incorporate, resolve_reference, INCORPORATION_RELATIONS,
)
# the legal SYSTEM layer — Hart's secondary rules as ops (recognition = validate,
# already built): change (enact/supersede via lifecycle/intertemporal) +
# adjudication (derive → resolve → terminal; any OPEN antecedent or an unseparable
# collision → escalate). Consumes algebra + intertemporal + lifecycle.
from .system import (
    Adjudication, Enactment, Supersession, adjudicate, enact, supersede,
)
# the legal-analysis FRONT DOOR — analyse(statements, facts) runs a scenario through
# the whole stack: recognition (validate; ill-formed law excluded) → adjudication
# (system.adjudicate over the algebra). Every unsettled point ⊥ → escalate.
from .analysis import Analysis, analyse

__all__ = [
    # entities
    "Jurisdiction", "LegalPerson", "Instrument", "Body",
    # world map (graph container + seed corpus; reach via WorldMap.reach,
    # which composes through scope_applies → the solver algebra)
    "WorldMap", "Entity", "EntityKind", "WorldEdge", "GovEntry", "ReachResult",
    "seed_world", "load_world_seed", "KIND_TO_FAMILY", "JURISDICTION_KINDS",
    # connection algebra (data + accessors; mechanism is the solver's)
    "connection_algebra", "load_connections", "is_connection", "GOVERNING",
    # legal-effect -> deontic bridge
    "legal_effect", "LegalEffect", "OPERATIVE_CONTENT",
    # scope / applicability (reach by composition; contested reach escalates)
    "scope_applies", "ScopeResult", "GROUND_AXIS",
    # sources of law (rank data; conflict resolution delegated to the solver)
    "Provision", "ConflictOutcome", "resolve_provisions", "to_norm",
    "source_rank", "load_sources",
    # instrument lifecycle (in-force-at-T, supersession lineage)
    "LifecycleEvent", "in_force", "version_in_force",
    "LIFECYCLE_RELATIONS", "TERMINATING_RELATIONS",
    # citation model (fresh: parse, xref, definition binding)
    "Citation", "Definition", "parse_citation", "resolve_xref",
    "bind_definition",
    # competing-definition detection (O34)
    "CompetingSet", "detect_competing", "competing_for_term",
    # referral-kind classification (O14; UNCERTAIN = escalate)
    "ReferralKind", "ReferralClassification", "classify_referral",
    "RECHTSGRUND_CUES", "RECHTSFOLGE_CUES",
    # instrument cross-reference resolution (citation → code/CELEX/label + relation typing)
    "InstrumentRef", "INSTRUMENTS", "CrossReference",
    "resolve_celex", "resolve_citation_number", "resolve_short_name",
    "infer_host_instrument", "extract_cross_references",
    # document-level summary (doc-kind + identifier + instrument + excerpt)
    "DocumentSummary", "summarize_document",
    # universal source-class map (source KINDS, effect ceilings, relation vocab,
    # incorporation invariant). Effect = legal force, distinct from LegalEffect.
    "Effect", "SourceClass", "Relation", "VOCABULARY", "SourceFinding",
    "is_relation", "max_effect", "self_executes", "requires_incorporation",
    "check_source",
    # legal-system packs + applicable-law resolver (conflicts escalate)
    "LegalSystem", "SourceEntry", "SourceRelation", "ApplicableLaw",
    "applicable_systems", "applicable_law",
    # legal-field (branch-of-law) profiles + the (jurisdiction × field) context
    "LegalField", "DimensionDoctrine", "MetaDoctrine", "ActorKind", "context",
    # intertemporal law: tempus regit actum, the temporal index, retroactivity
    "Retroactivity", "TemporalIndex", "VersionSelection",
    "classify_retroactivity", "governing_version", "select_version", "stamp",
    # instrument identifiers: work (CELEX) vs expression (consolidated CELEX / ELI)
    "consolidated_celex", "eli_at", "version_id",
    # worked reviews (branch profile + competence + legal basis + intertemporal, graded)
    "Review", "administrative_review", "CriminalReview", "criminal_review",
    "ConstitutionalReview", "constitutional_review",
    "SubsumptionReview", "review_against_facts",
    # the legal grammar (statement + recognition gate + source-hierarchy order)
    "LegalStatement", "WellFormedness", "validate", "is_well_formed",
    "outranks", "lex_superior",
    # the legal algebra (composition operations: apply, resolve_conflict, derive, resolve)
    "Conclusion", "apply", "Resolution", "resolve_conflict",
    "Derivation", "derive", "to_provision", "resolve",
    # legal incorporation / cross-reference (force via transposition; citation → instrument)
    "Incorporation", "incorporate", "resolve_reference", "INCORPORATION_RELATIONS",
    # the legal system layer (Hart secondary rules: change + adjudication)
    "Adjudication", "Enactment", "Supersession", "adjudicate", "enact", "supersede",
    # the legal-analysis front door (recognition → adjudication over a scenario)
    "Analysis", "analyse",
    # corpus loader (md reference-table parser → WorldMap; refdir injected)
    "build_world", "parse_md", "EU27",
    # instrument-registry metadata + CSV loader (csv_path injected)
    "load_instruments", "CODE", "DOMAIN", "TRANCHES",
    # relational enrichment pass (curated memberships/treaties/adequacy/regulators)
    "enrich",
    # corpus validation (WorldMap-level; authority tiers + host allow-list)
    "validate_corpus", "Finding",
    "PRIMARY_LAW", "INSTITUTIONAL", "SUPPORTING", "SECONDARY", "GENERAL",
    # contract-instance model (PartyRef + ContractInstance; registry stays in RVND)
    "PartyRef", "ContractInstance", "ContractError",
    # anchoring (rule → legal instruments/jurisdictions/regulators; generic in/out)
    "anchor", "place_legal_text", "Anchor", "AnchorKind", "AnchorRelation",
    "ANCHOR_KINDS", "ANCHOR_RELATIONS", "TextProvision", "segment_provisions",
    "__version__",
]
