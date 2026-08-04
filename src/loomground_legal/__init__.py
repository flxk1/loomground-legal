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

__all__ = [
    # entities
    "Jurisdiction", "LegalPerson", "Instrument", "Body",
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
    "__version__",
]
