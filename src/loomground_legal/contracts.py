# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""The contract-instance model — contracts as first-class entities on the legal
world map, with typed parties, dates, terms, and a version chain.

This supplies the typed nouns the obligation runtime and the
machine-readable-contract pipeline bind to:

  * :class:`PartyRef`         — a party as a reference to a world-map entity
                                (LEGAL_PERSON / NATURAL_PERSON / PUBLIC_BODY) with
                                a role slug and an optional LEI (ISO 17442,
                                checksum-verified);
  * :class:`ContractInstance` — identity (id + version + document hash), parties,
                                ``effective_date: Date``, ``term: Term``, governing
                                law as an entity code, declared event dates for
                                relative-deadline resolution, and a ``supersedes``
                                link (``contract_id@version``) so amendments form
                                an explicit chain instead of orphaned hashes.

Cold-start discipline: every field except identity is optional. An unextracted
field is honestly ``None`` ("not extracted"), never guessed — but a field that IS
present is typed and validated at construction (the temporal layer rejects
malformed dates; :class:`PartyRef` rejects malformed LEIs). The temporal value
types come from :mod:`loomground_solver.temporal`.

**Model only.** The ``ContractRegistry`` (folder JSONL persistence, signed
mutation-log audit, and the world-map ``_project`` adapter) STAYS in RVND — it is
folder runtime, not domain model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from loomground_solver.temporal import Date, Money, RelativeDeadline, Term

from .world import EntityKind

__all__ = ["PartyRef", "ContractInstance", "ContractError"]


class ContractError(ValueError):
    """Raised when a contract record is malformed. Reject, don't coerce."""


# ── PartyRef ──────────────────────────────────────────────────────────────────

_PERSON_KINDS = frozenset({EntityKind.LEGAL_PERSON.value,
                           EntityKind.NATURAL_PERSON.value,
                           EntityKind.PUBLIC_BODY.value})
_ROLE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_LEI_RE = re.compile(r"^[A-Z0-9]{18}[0-9]{2}$")


def _lei_checksum_ok(lei: str) -> bool:
    """ISO 17442 / ISO 7064 mod-97-10: letters → 10..35, whole string mod 97 == 1."""
    digits = "".join(str(int(c, 36)) for c in lei)
    return int(digits) % 97 == 1


@dataclass(frozen=True)
class PartyRef:
    """A contract party as a *reference* into the world map — not a bare string.
    ``entity_code`` should resolve to a LEGAL_PERSON / NATURAL_PERSON /
    PUBLIC_BODY entity."""

    entity_code: str
    role: str                            # processor | controller | licensor | …
    name: str = ""                       # display name (entity name wins if set)
    lei: Optional[str] = None            # ISO 17442 Legal Entity Identifier
    entity_kind: str = EntityKind.LEGAL_PERSON.value

    def __post_init__(self) -> None:
        if not self.entity_code or not isinstance(self.entity_code, str):
            raise ContractError("party needs a non-empty entity_code")
        if not self.role or not _ROLE_RE.match(self.role):
            raise ContractError(f"party role must be a lowercase slug, got {self.role!r}")
        if self.entity_kind not in _PERSON_KINDS:
            raise ContractError(
                f"party entity_kind must be one of {sorted(_PERSON_KINDS)}, got {self.entity_kind!r}")
        if self.lei is not None:
            if not _LEI_RE.match(self.lei):
                raise ContractError(f"not an ISO 17442 LEI (20 chars): {self.lei!r}")
            if not _lei_checksum_ok(self.lei):
                raise ContractError(f"LEI checksum failed: {self.lei!r}")

    def to_dict(self) -> dict:
        return {"entity_code": self.entity_code, "role": self.role,
                "name": self.name, "lei": self.lei, "entity_kind": self.entity_kind}

    @classmethod
    def from_dict(cls, d: dict) -> "PartyRef":
        return cls(entity_code=d["entity_code"], role=d["role"],
                   name=d.get("name", ""), lei=d.get("lei"),
                   entity_kind=d.get("entity_kind", EntityKind.LEGAL_PERSON.value))


# ── ContractInstance ──────────────────────────────────────────────────────────

_CONTRACT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SUPERSEDES_RE = re.compile(r"^(?P<cid>[a-z0-9][a-z0-9._-]*)@(?P<ver>\d+)$")


@dataclass(frozen=True)
class ContractInstance:
    """One version of one contract. Identity = (contract_id, version); content
    identity = document_hash. Every substantive field optional (cold-start:
    "not extracted" beats invented), every present field typed."""

    contract_id: str
    version: int = 1
    title: str = ""
    contract_type: str = ""              # dpa | nda | msa | licence | … (slug or "")
    parties: tuple[PartyRef, ...] = ()
    effective_date: Optional[Date] = None
    term: Optional[Term] = None
    governing_law: Optional[str] = None  # entity code of the legal order (e.g. "DE")
    jurisdiction_anchors: tuple[str, ...] = ()
    events: dict[str, Date] = field(default_factory=dict)  # signing, delivery, …
    total_value: Optional[Money] = None
    supersedes: Optional[str] = None     # "contract_id@version"
    document_hash: str = ""              # sha256:<hex> of the source bytes
    language: str = ""                   # ISO 639-1
    source_document: str = ""            # path/URL of the ingested document
    facets: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _CONTRACT_ID_RE.match(self.contract_id or ""):
            raise ContractError(f"contract_id must be a slug, got {self.contract_id!r}")
        if not isinstance(self.version, int) or self.version < 1:
            raise ContractError(f"version must be an int >= 1, got {self.version!r}")
        if self.supersedes is not None:
            m = _SUPERSEDES_RE.match(self.supersedes)
            if not m:
                raise ContractError(
                    f"supersedes must be 'contract_id@version', got {self.supersedes!r}")
            if m["cid"] == self.contract_id and int(m["ver"]) >= self.version:
                raise ContractError(
                    f"a version can only supersede an earlier version of itself "
                    f"({self.supersedes!r} vs version {self.version})")
        if self.effective_date is not None and not isinstance(self.effective_date, Date):
            raise ContractError("effective_date must be a temporal.Date")
        if self.term is not None and not isinstance(self.term, Term):
            raise ContractError("term must be a temporal.Term")
        if self.total_value is not None and not isinstance(self.total_value, Money):
            raise ContractError("total_value must be a temporal.Money")
        for k, v in self.events.items():
            if not isinstance(v, Date):
                raise ContractError(f"event {k!r} must map to a temporal.Date")
        roles_seen = {}
        for p in self.parties:
            if not isinstance(p, PartyRef):
                raise ContractError("parties must be PartyRef instances")
            roles_seen.setdefault(p.role, []).append(p.entity_code)

    # ── derived ───────────────────────────────────────────────────────────────
    @property
    def ref(self) -> str:
        return f"{self.contract_id}@{self.version}"

    def event_dates(self) -> dict[str, Date]:
        """Events for RelativeDeadline.resolve(): declared events + the
        canonical ``effective_date`` / ``term_end`` aliases when known."""
        out = dict(self.events)
        if self.effective_date is not None:
            out.setdefault("effective_date", self.effective_date)
        if self.term is not None:
            end = self.term.end_date()
            if end is not None:
                out.setdefault("term_end", end)
        return out

    def resolve_deadline(self, deadline: RelativeDeadline) -> Optional[Date]:
        return deadline.resolve(self.event_dates())

    def party_by_role(self, role: str) -> tuple[PartyRef, ...]:
        return tuple(p for p in self.parties if p.role == role)

    def missing_fields(self) -> list[str]:
        """The honest "not extracted" list the intake UI renders."""
        out = []
        if not self.parties:
            out.append("parties")
        if self.effective_date is None:
            out.append("effective_date")
        if self.term is None:
            out.append("term")
        if self.governing_law is None:
            out.append("governing_law")
        if not self.contract_type:
            out.append("contract_type")
        if not self.language:
            out.append("language")
        return out

    # ── serde ─────────────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "contract_id": self.contract_id, "version": self.version,
            "title": self.title, "contract_type": self.contract_type,
            "parties": [p.to_dict() for p in self.parties],
            "effective_date": self.effective_date.iso if self.effective_date else None,
            "term": self.term.to_dict() if self.term else None,
            "governing_law": self.governing_law,
            "jurisdiction_anchors": list(self.jurisdiction_anchors),
            "events": {k: v.iso for k, v in self.events.items()},
            "total_value": self.total_value.to_dict() if self.total_value else None,
            "supersedes": self.supersedes,
            "document_hash": self.document_hash, "language": self.language,
            "source_document": self.source_document, "facets": self.facets,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContractInstance":
        return cls(
            contract_id=d["contract_id"], version=int(d.get("version", 1)),
            title=d.get("title", ""), contract_type=d.get("contract_type", ""),
            parties=tuple(PartyRef.from_dict(p) for p in d.get("parties", [])),
            effective_date=Date(d["effective_date"]) if d.get("effective_date") else None,
            term=Term.from_dict(d["term"]) if d.get("term") else None,
            governing_law=d.get("governing_law"),
            jurisdiction_anchors=tuple(d.get("jurisdiction_anchors", [])),
            events={k: Date(v) for k, v in d.get("events", {}).items()},
            total_value=Money.from_dict(d["total_value"]) if d.get("total_value") else None,
            supersedes=d.get("supersedes"),
            document_hash=d.get("document_hash", ""), language=d.get("language", ""),
            source_document=d.get("source_document", ""), facets=d.get("facets", {}),
        )
