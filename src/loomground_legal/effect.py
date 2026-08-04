# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Legal-effect typing — the bridge from operative content into deontic.

A provision's operative content (what the text *does*: impose a duty, grant a
permission, prohibit conduct, confer a right/power/immunity, define a term,
establish a body) maps to its legal effect in the deontic language: a modal
operator (O/P/F) where one applies, and the Hohfeldian incident borne by the
addressee plus its jural correlative for the counterparty.

The load-bearing rule, enforced here and in deontic itself: **a statutory
"right" is NEVER a fourth "R" operator.** It is either a permission (a
Hohfeld *privilege*/liberty for the holder) or a claim-right — the holder's
*claim* whose jural correlative is the counterparty's *duty*, reached via
``deontic.correlative``, never via a new modal. This module consumes deontic's
operators and incident relations; it reimplements none of them.

Content kinds with no deontic modal of their own (power, immunity, definition,
establishment) come back with ``operator=None`` and, where one exists, the
incident form. Unknown content kinds are a ``ValueError`` — fail-closed, no
guessed effect.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from deontic import (
    OP_OBLIGATION,
    OP_PERMISSION,
    OP_PROHIBITION,
    VALID_OPERATORS,
    correlative,
)

__all__ = ["LegalEffect", "legal_effect", "OPERATIVE_CONTENT"]

#: The operative-content kinds the bridge accepts.
OPERATIVE_CONTENT: Tuple[str, ...] = (
    "duty",
    "permission",
    "liberty",
    "prohibition",
    "right",
    "power",
    "immunity",
    "definition",
    "establishment",
    "conferral-of-right",
)


@dataclass(frozen=True)
class LegalEffect:
    """The deontic shadow of a provision's operative content.

    ``operator`` is one of deontic's O/P/F or ``None`` when the effect has no
    modal of its own (an incident-only effect, a definition, an establishment).
    ``incident`` is the Hohfeld position borne by the addressee/holder ('' when
    none), and ``correlative_incident`` is the counterparty's jural correlative
    (always derived via ``deontic.correlative``, '' when there is no incident).
    """

    content: str
    operator: Optional[str]
    incident: str
    correlative_incident: str

    def __post_init__(self) -> None:
        if self.operator is not None and self.operator not in VALID_OPERATORS:
            raise ValueError(
                f"operator {self.operator!r} is not a deontic operator "
                f"(valid: {VALID_OPERATORS}); a 'right' is never an operator"
            )


def _effect(content: str, operator: Optional[str], incident: str) -> LegalEffect:
    return LegalEffect(
        content=content,
        operator=operator,
        incident=incident,
        correlative_incident=correlative(incident) if incident else "",
    )


def legal_effect(content: str, *, claim_right: bool = False) -> LegalEffect:
    """Map a provision's operative content kind to its legal effect.

    * ``duty`` → O, the addressee bears a *duty* (correlative: *claim*);
    * ``permission`` / ``liberty`` → P, a *privilege* (correlative: *no-right*);
    * ``prohibition`` → F, a *duty* not to act (correlative: *claim*);
    * ``right`` → **never an "R" operator**: by default the liberty reading
      (P + privilege); with ``claim_right=True`` the claim-right form — no
      modal on the holder, incident *claim*, and the counterparty's *duty*
      via ``deontic.correlative``;
    * ``conferral-of-right`` → the claim-right incident form (claim ↔ duty);
    * ``power`` → incident *power* (correlative: *liability*), no modal;
    * ``immunity`` → incident *immunity* (correlative: *disability*), no modal;
    * ``definition`` / ``establishment`` → no operator, no incident.

    Unknown kinds raise ``ValueError`` (fail-closed; never a guessed effect).
    ``claim_right`` is meaningful only for ``content="right"``.
    """
    if content not in OPERATIVE_CONTENT:
        raise ValueError(
            f"unknown operative content {content!r}; expected one of "
            f"{OPERATIVE_CONTENT}"
        )
    if content == "duty":
        return _effect(content, OP_OBLIGATION, "duty")
    if content in ("permission", "liberty"):
        return _effect(content, OP_PERMISSION, "privilege")
    if content == "prohibition":
        return _effect(content, OP_PROHIBITION, "duty")
    if content == "right":
        if claim_right:
            return _effect(content, None, "claim")
        return _effect(content, OP_PERMISSION, "privilege")
    if content == "conferral-of-right":
        return _effect(content, None, "claim")
    if content == "power":
        return _effect(content, None, "power")
    if content == "immunity":
        return _effect(content, None, "immunity")
    # definition / establishment: structural moves, no deontic content.
    return _effect(content, None, "")
