# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The legal connection algebra — data in, solver mechanism out.

This module loads ``artifacts/connections.json`` (the connection vocabulary,
the partial composition table, the inverse map, and the connection → 5D
projection — lifted verbatim from host's ``legal_connection``) and builds a
:class:`loomground_solver.RelationAlgebra` over it.

Deliberately NO composition logic lives here: ``compose`` / ``compose_path`` /
:data:`~loomground_solver.ESCALATE` are the solver's mechanism, and the
escalate-don't-guess discipline (a chain yields a relation, ESCALATE for a
legally contested step, or ``None`` when nothing follows) is enforced there.
Legal supplies the *data*; the algebra's laws (LC-1..LC-5) hold because the
table says so, not because this module computes anything.

In the JSON, the string ``"ESCALATE"`` marks a contested composition and is
mapped back to the solver's sentinel on load; ``null`` maps to ``None``;
dimension strings map to :class:`~loomground_solver.Dimension` values.
"""
from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any, Dict, FrozenSet

from loomground_solver import ESCALATE, Dimension, RelationAlgebra

__all__ = [
    "load_connections",
    "connection_algebra",
    "is_connection",
    "GOVERNING",
]

_ESCALATE_TOKEN = "ESCALATE"


def load_connections() -> Dict[str, Any]:
    """The raw ``connections.json`` payload (parsed, untranslated)."""
    ref = resources.files("loomground_legal").joinpath("artifacts/connections.json")
    return json.loads(ref.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def connection_algebra() -> RelationAlgebra:
    """The legal :class:`~loomground_solver.RelationAlgebra`, built once from
    the packaged data. Construction is fail-closed in the solver: any relation
    named in the table/inverses/dimensions but missing from the vocabulary is
    a ``ValueError`` — a typo in the artifact cannot silently degrade to
    "no inference"."""
    data = load_connections()
    table = {
        (row["a"], row["b"]): (
            ESCALATE if row["result"] == _ESCALATE_TOKEN else row["result"]
        )
        for row in data["compose"]
    }
    return RelationAlgebra(
        vocabulary=data["vocabulary"],
        table=table,
        inverses=data["inverses"],
        dimensions={r: Dimension(d) for r, d in data["dimensions"].items()},
        default_dimension=Dimension.RELATIONAL,
    )


def is_connection(name: str) -> bool:
    """True if ``name`` is a relation in the legal connection vocabulary."""
    return connection_algebra().is_relation(name)


#: Relations that, when they are the *result* of a reach computation, mean a
#: legal order actually governs the entity (data, mirrored from the artifact).
GOVERNING: FrozenSet[str] = frozenset(load_connections()["governing"])
