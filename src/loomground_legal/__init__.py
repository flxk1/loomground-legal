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

__all__ = [
    # entities
    "Jurisdiction", "LegalPerson", "Instrument", "Body",
    # connection algebra (data + accessors; mechanism is the solver's)
    "connection_algebra", "load_connections", "is_connection", "GOVERNING",
    # legal-effect -> deontic bridge
    "legal_effect", "LegalEffect", "OPERATIVE_CONTENT",
    "__version__",
]
