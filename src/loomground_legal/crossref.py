# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Instrument cross-reference resolution — citations between legal instruments.

When one instrument cites another ("without prejudice to Regulation (EU)
2016/679", "as referred to in the DSA", a bare CELEX like ``32024R1689``), this
module resolves the citation to a canonical instrument (code · CELEX · human
label) and types the *relationship* the citing verb expresses onto a 5D
:class:`~loomground_solver.Dimension`:

  * ``without-prejudice`` / ``in-accordance-with`` / ``refers-to`` / ``pursuant-to``
    / ``complements`` → **RELATIONAL** (a link, not a hierarchy);
  * ``lex-specialis-to`` / ``amends`` / ``repeals`` / ``supersedes`` →
    **STRUCTURAL** (a norm-hierarchy relationship).

Instrument identity is the package's — the CELEX↔code index is
:data:`loomground_legal.instruments.CODE`, which this module **consumes** (an
import-time assertion keeps the label/alias registry below aligned with it, so the
two never drift). This module adds only the human labels + short-name aliases that
``CODE`` does not carry, the citation-form matchers, and the relation typing. It is
a data/bridge layer: no inference of its own.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Optional

from loomground_solver import Dimension

from .instruments import CODE

__all__ = [
    "InstrumentRef", "INSTRUMENTS", "CrossReference",
    "resolve_celex", "resolve_citation_number", "resolve_short_name",
    "infer_host_instrument", "extract_cross_references",
]


@dataclass(frozen=True)
class InstrumentRef:
    """A cited instrument: its canonical code (aligned with
    :data:`instruments.CODE`), a human label, its CELEX (``""`` for a national law
    with no CELEX), and the short-name aliases it is cited by."""

    code: str
    canonical: str
    celex: str = ""
    short_names: tuple[str, ...] = ()


# The label + alias layer over instruments.CODE. Codes match CODE; the CELEX for a
# code is CODE's (asserted below). National laws without a CELEX (BDSG, UrhG) live
# only here — CODE is CELEX-keyed — and resolve by short name.
INSTRUMENTS: tuple[InstrumentRef, ...] = (
    InstrumentRef("gdpr", "Regulation (EU) 2016/679 (GDPR)", "32016R0679",
                  ("GDPR", "DSGVO", "DS-GVO", "General Data Protection Regulation")),
    InstrumentRef("ai-act", "Regulation (EU) 2024/1689 (AI Act)", "32024R1689",
                  ("AI Act", "AIA", "Artificial Intelligence Act")),
    InstrumentRef("dsa", "Regulation (EU) 2022/2065 (DSA)", "32022R2065",
                  ("DSA", "Digital Services Act")),
    InstrumentRef("dma", "Regulation (EU) 2022/1925 (DMA)", "32022R1925",
                  ("DMA", "Digital Markets Act")),
    InstrumentRef("nis2", "Directive (EU) 2022/2555 (NIS2)", "32022L2555",
                  ("NIS2", "NIS 2", "NIS2 Directive")),
    InstrumentRef("cra", "Regulation (EU) 2024/2847 (Cyber Resilience Act)", "32024R2847",
                  ("CRA", "Cyber Resilience Act")),
    InstrumentRef("dora", "Regulation (EU) 2022/2554 (DORA)", "32022R2554",
                  ("DORA", "Digital Operational Resilience Act")),
    InstrumentRef("data-act", "Regulation (EU) 2023/2854 (Data Act)", "32023R2854",
                  ("Data Act",)),
    InstrumentRef("dga", "Regulation (EU) 2022/868 (Data Governance Act)", "32022R0868",
                  ("Data Governance Act", "DGA")),
    InstrumentRef("software-directive", "Directive 2009/24/EC (Software Directive)",
                  "32009L0024", ("Software Directive", "Computer Programs Directive")),
    InstrumentRef("dsm-directive", "Directive (EU) 2019/790 (DSM Directive)", "32019L0790",
                  ("DSM Directive", "Copyright Directive", "CDSM")),
    InstrumentRef("eidas", "Regulation (EU) 910/2014 (eIDAS)", "32014R0910", ("eIDAS",)),
    InstrumentRef("bdsg", "Bundesdatenschutzgesetz (BDSG)", "", ("BDSG",)),
    InstrumentRef("urhg", "Urheberrechtsgesetz (UrhG)", "", ("UrhG",)),
)

# Consume CODE as the authority: any CELEX-bearing row must agree with CODE where
# CODE knows it. This is the anti-drift gate — the registry may cover instruments
# CODE does not yet index, but must never contradict it.
assert all(CODE[i.celex] == i.code for i in INSTRUMENTS if i.celex and i.celex in CODE)

_BY_CODE: dict[str, InstrumentRef] = {i.code: i for i in INSTRUMENTS}


# ── citation-form matchers ─────────────────────────────────────────────────────

# "Regulation (EU) 2016/679" / "Regulation (EC) No 45/2001" / "Directive (EU) …"
_REG_CITE_RE = re.compile(
    r"\b(?P<kind>Regulation|Directive)\s*\((?:EU|EC|EEC)\)\s*(?:No\.?\s*)?"
    r"(?P<num>\d{1,4}/\d{2,4})", re.IGNORECASE)
# "Directive 2009/24/EC" — kind, number, /EC suffix, no parenthetical.
_DIR_CITE_RE = re.compile(
    r"\b(?P<kind>Directive|Regulation)\s+(?P<num>\d{1,4}/\d{1,4})(?:/(?:EU|EC|EEC))\b",
    re.IGNORECASE)
# CELEX: sector 3 (legislation) + year + type letter + number, e.g. 32016R0679.
_CELEX_RE = re.compile(r"\b(?P<celex>3\d{4}[A-Z]\d{4})\b")

# Relation verbs that introduce a cross-reference → (relation label, dimension).
_RELATIONS: tuple[tuple[re.Pattern[str], str, Dimension], ...] = (
    (re.compile(r"without\s+prejudice\s+to", re.I), "without-prejudice", Dimension.RELATIONAL),
    (re.compile(r"in\s+accordance\s+with", re.I), "in-accordance-with", Dimension.RELATIONAL),
    (re.compile(r"as\s+(?:defined|referred\s+to|laid\s+down)\s+in", re.I), "refers-to", Dimension.RELATIONAL),
    (re.compile(r"pursuant\s+to", re.I), "pursuant-to", Dimension.RELATIONAL),
    (re.compile(r"lex\s+specialis", re.I), "lex-specialis-to", Dimension.STRUCTURAL),
    (re.compile(r"\bamend(?:s|ing|ment\s+to)?\b", re.I), "amends", Dimension.STRUCTURAL),
    (re.compile(r"\brepeal(?:s|ing|ed)?\b", re.I), "repeals", Dimension.STRUCTURAL),
    (re.compile(r"\bsupersed(?:es|ing|ed)\b", re.I), "supersedes", Dimension.STRUCTURAL),
    (re.compile(r"complement(?:s|ary\s+to|ing)?", re.I), "complements", Dimension.RELATIONAL),
)
_RELATION_WINDOW = 80   # chars before a citation to look for its relation verb


@dataclass
class CrossReference:
    """A resolved reference to another instrument."""

    target_code: str                 # instrument code, or "" if unresolved
    target_canonical: str            # best human label of the target
    target_celex: str = ""
    relation: str = "refers-to"
    dimension: str = Dimension.RELATIONAL.value
    matched_text: str = ""           # the citation as it appeared
    count: int = 1                   # how many times this target was cited

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ── resolution ─────────────────────────────────────────────────────────────────

def resolve_celex(celex: str) -> Optional[InstrumentRef]:
    """The instrument for a CELEX id, or ``None``."""
    return _BY_CODE.get(CODE.get(celex, "")) or next(
        (i for i in INSTRUMENTS if i.celex and i.celex == celex), None)


def resolve_citation_number(num: str) -> Optional[InstrumentRef]:
    """Map a 'YYYY/NN' citation number to an instrument by canonical containment."""
    norm = num.strip()
    return next((i for i in INSTRUMENTS if norm in i.canonical), None)


def resolve_short_name(name: str) -> Optional[InstrumentRef]:
    """The instrument a short-name alias names (case-insensitive), or ``None``."""
    low = name.strip().lower()
    return next((i for i in INSTRUMENTS
                 if any(sn.lower() == low for sn in i.short_names)), None)


def infer_host_instrument(content: str) -> str:
    """Best-effort code of the instrument the document *is* (``""`` if unknown), so
    a self-reference can be filtered out.

    A CELEX self-id near the top wins outright. Otherwise the instrument whose
    identifier appears **earliest** wins — the document's own identity sits in its
    header/title, so an instrument merely cited later in the body never displaces
    it (registry order must not decide the host)."""
    snippet = content[:8000]
    for m in _CELEX_RE.finditer(snippet):
        inst = resolve_celex(m.group("celex"))
        if inst is not None:
            return inst.code
    low = snippet.lower()
    best_pos: Optional[int] = None
    best_code = ""
    for inst in INSTRUMENTS:
        positions: list[int] = []
        num = re.search(r"\d+/\d+", inst.canonical)
        if num:
            p = low.find(num.group(0))
            if p != -1:
                positions.append(p)
        for sn in inst.short_names:
            if len(sn) >= 4:                    # keep GDPR/DORA/NIS2; skip only the
                p = low.find(sn.lower())        # 3-char ambiguous aliases (DSA/DMA/CRA/DGA)
                if p != -1:
                    positions.append(p)
        if positions:
            earliest = min(positions)
            if best_pos is None or earliest < best_pos:
                best_pos, best_code = earliest, inst.code
    return best_code


def _nearest_relation(content: str, pos: int) -> tuple[str, Dimension]:
    """The relation verb closest *before* a citation at ``pos`` (default refers-to)."""
    window = content[max(0, pos - _RELATION_WINDOW):pos]
    best: Optional[tuple[int, str, Dimension]] = None
    for pat, rel, dim in _RELATIONS:
        for m in pat.finditer(window):
            dist = len(window) - m.end()   # distance to the citation
            if best is None or dist < best[0]:
                best = (dist, rel, dim)
    return (best[1], best[2]) if best else ("refers-to", Dimension.RELATIONAL)


def extract_cross_references(content: str, *,
                             host_code: Optional[str] = None) -> list[CrossReference]:
    """References to OTHER instruments in ``content``.

    Deduplicates by target code (or by raw citation when unresolved); the closest
    relation verb wins and a STRUCTURAL relation is preferred over a RELATIONAL one
    for the same target; counts accumulate. Self-references (to ``host_code``,
    inferred if not given) are dropped. Invents nothing.
    """
    content = content or ""
    if host_code is None:
        host_code = infer_host_instrument(content)
    found: dict[str, CrossReference] = {}

    def _add(inst: Optional[InstrumentRef], matched: str, pos: int,
             raw_celex: str = "") -> None:
        if inst is not None and host_code and inst.code == host_code:
            return                                   # drop self-reference
        if inst is not None:
            key, canonical, celex = inst.code, inst.canonical, (inst.celex or raw_celex)
        else:
            key, canonical, celex = f"raw:{matched.lower()}", matched, raw_celex
        rel, dim = _nearest_relation(content, pos)
        existing = found.get(key)
        if existing is None:
            found[key] = CrossReference(
                target_code=(inst.code if inst else ""), target_canonical=canonical,
                target_celex=celex, relation=rel, dimension=dim.value,
                matched_text=matched, count=1)
        else:
            existing.count += 1
            if dim is Dimension.STRUCTURAL and existing.dimension == Dimension.RELATIONAL.value:
                existing.relation, existing.dimension = rel, dim.value

    # 1. Full "Regulation (EU) NNNN/NN" / "Directive NNNN/NN/EC" citations.
    for pat in (_REG_CITE_RE, _DIR_CITE_RE):
        for m in pat.finditer(content):
            _add(resolve_citation_number(m.group("num")), m.group(0), m.start())
    # 2. Bare CELEX ids.
    for m in _CELEX_RE.finditer(content):
        _add(resolve_celex(m.group("celex")), m.group(0), m.start(),
             raw_celex=m.group("celex"))
    # 3. Short-name aliases (word-boundaried, case-insensitive).
    for inst in INSTRUMENTS:
        for sn in inst.short_names:
            for m in re.finditer(r"\b" + re.escape(sn) + r"\b", content, re.I):
                _add(inst, m.group(0), m.start())
    return list(found.values())
