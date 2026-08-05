# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Anchoring — place a rule onto the legal instruments/jurisdictions/regulators
that govern it.

A norm does not float free: a clause that says "erase personal data under the
GDPR" is *governed by* an instrument (the GDPR), which *applies in* a
jurisdiction (the EU) and is *enforced by* a regulator (the EDPB, a national DPA
…). Anchoring is the legal-domain step that resolves those placements. This
module is where that ontology and that resolution logic now live — the legal
plane — lifted from the anchoring behavior RVND wired into loomground-norm's
rule registry (``server/src/workspaces/adapters/norm.py``: ``_anchors_for`` /
``_host_instrument_anchors`` / ``_host_anchor_dicts``), made **norm-independent**.

Two entry points, both **generic in / generic out** — no ``RuleFacet``,
no ``SpanNorm``, no host paths, no folder context:

* :func:`anchor` — resolve a rule (its operative text and/or a facets dict,
  optionally with pre-recognised instrument ``candidates``) to a list of
  :class:`Anchor` against a :class:`~loomground_legal.world.WorldMap`. Candidate
  recognition, when not supplied, is a light built-in match of the text against
  the instruments already in the world; a consumer with a richer recogniser
  (RVND's ``corpus.ingest.candidates_from_text``) bridges its result in through
  ``candidates`` and gets byte-identical placements.
* :func:`place_legal_text` — cut a *law's own text* into provisions (built-in
  :func:`segment_provisions`, overridable) and anchor each to its host
  instrument (that instrument, its jurisdiction(s), its enforcing regulators)
  plus any in-text cross-references.

The world graph and the connection vocabulary are the package's own
(:mod:`loomground_legal.world`, :mod:`loomground_legal.connection`); the
composition mechanism, as everywhere in this plane, stays the solver's. This
module holds no norm dependency and no host coupling.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import List, Literal, Optional

from .connection import is_connection
from .world import EntityKind, WorldMap, seed_world

__all__ = [
    "Anchor",
    "AnchorKind",
    "AnchorRelation",
    "ANCHOR_KINDS",
    "ANCHOR_RELATIONS",
    "TextProvision",
    "segment_provisions",
    "anchor",
    "place_legal_text",
]

# ── the legal anchoring ontology ────────────────────────────────────────────

#: What kind of legal entity a span is placed onto.
AnchorKind = Literal["instrument", "jurisdiction", "regulator"]

#: How the span relates to that entity.
AnchorRelation = Literal["cites", "governed_by", "enforced_by"]

#: The closed kind vocabulary (data; the enum literal above is the type).
ANCHOR_KINDS = frozenset({"instrument", "jurisdiction", "regulator"})

#: The closed relation vocabulary.
ANCHOR_RELATIONS = frozenset({"cites", "governed_by", "enforced_by"})

#: The connection relations anchoring reads off the world graph. Named here as
#: legal-connection vocabulary and validated against the package's connection
#: algebra at import (fail-closed: a vocabulary drift cannot silently degrade
#: anchoring to "no jurisdiction / no regulator").
_APPLIES_IN = "applies_in"
_ENFORCES = "enforces"
for _rel in (_APPLIES_IN, _ENFORCES):
    if not is_connection(_rel):
        raise ValueError(
            f"anchoring expects {_rel!r} in the legal connection vocabulary; "
            "the connection algebra does not know it."
        )


@dataclass
class Anchor:
    """One placement of a rule onto a governing legal entity.

    ``entity`` is the ref/target — the code of the instrument, jurisdiction, or
    regulator in a :class:`~loomground_legal.world.WorldMap`. ``kind`` is one of
    :data:`ANCHOR_KINDS`; ``relation`` one of :data:`ANCHOR_RELATIONS`;
    ``basis`` the supporting reference (a pinpoint, an instrument name, the edge
    basis behind the placement). An empty result set is a legitimate, visible
    answer — no anchoring is invented.
    """

    entity: str                       # ref/target: entity code in the world map
    kind: AnchorKind                  # instrument | jurisdiction | regulator
    relation: AnchorRelation          # cites | governed_by | enforced_by
    basis: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ── generic input helpers ───────────────────────────────────────────────────

def _text_of(text: str, facets: Optional[dict]) -> str:
    """The operative text to anchor from — explicit ``text`` wins, else a
    facets dict's operative/text/raw_sentence field. Generic: never a
    ``RuleFacet``/``SpanNorm``."""
    if text:
        return text
    if facets:
        for key in ("operative", "text", "raw_sentence", "sentence"):
            val = facets.get(key)
            if val:
                return str(val)
    return ""


def _match_candidates(text: str, world: WorldMap) -> List[dict]:
    """Built-in candidate recognition: the instruments already in ``world`` whose
    canonical name or code is named in ``text``. Deliberately light — a consumer
    with a richer recogniser passes ``candidates`` to :func:`anchor` instead. The
    candidate shape (``code`` / ``name`` / ``jurisdiction``) matches what such a
    recogniser produces, so resolution is identical on either path."""
    if not text:
        return []
    lowered = text.lower()
    out: List[dict] = []
    for ent in world.search(kind=EntityKind.INSTRUMENT):
        name = (ent.name or "").lower()
        code = (ent.code or "").lower()
        hit = (name and name in lowered) or (code and code in lowered)
        if not hit:
            # code as a whitespace/punctuation-delimited token
            hit = code and any(tok.strip(".,;:()[]") == code for tok in lowered.split())
        if hit:
            out.append({"code": ent.code, "name": ent.name,
                        "jurisdiction": ent.jurisdiction})
    return out


# ── anchor: resolve a rule to legal anchors ─────────────────────────────────

def anchor(text: str = "", world: Optional[WorldMap] = None, *,
           facets: Optional[dict] = None,
           candidates: Optional[list] = None) -> List[Anchor]:
    """Resolve a rule to the legal entities that govern it.

    ``text`` is the rule's operative text; ``facets`` a generic dict is accepted
    as an alternative source of that text (``operative`` / ``text`` /
    ``raw_sentence``) and of ``candidates``. ``world`` is the
    :class:`~loomground_legal.world.WorldMap` to resolve against (the packaged
    seed when omitted). ``candidates`` — a list of instrument dicts (``code``,
    optional ``name`` / ``jurisdiction`` / ``pinpoint``) — lets a caller inject a
    richer recogniser's output; without it the instruments named in ``text`` are
    matched against the world.

    For each recognised instrument: the instrument is *cited*; its owning
    jurisdiction is *governed_by*; and, walked over the world graph, every
    jurisdiction it ``applies_in`` is *governed_by* and every regulator that
    ``enforces`` it is *enforced_by*. Deduplicated by (entity, relation), first
    basis kept. Empty in → empty out; nothing is invented.
    """
    if world is None:
        world = seed_world()
    if candidates is None and facets is not None:
        candidates = facets.get("candidates")
    resolved = _text_of(text, facets)
    if candidates is None:
        candidates = _match_candidates(resolved, world)

    out: List[Anchor] = []
    seen: set = set()

    def _add(entity: str, kind: AnchorKind, relation: AnchorRelation,
             basis: str = "") -> None:
        key = (entity, relation)
        if entity and key not in seen:
            seen.add(key)
            out.append(Anchor(entity, kind, relation, basis))

    for cand in candidates:
        code = cand["code"]
        _add(code, "instrument", "cites",
             cand.get("pinpoint") or cand.get("name", ""))
        if cand.get("jurisdiction"):
            _add(cand["jurisdiction"], "jurisdiction", "governed_by",
                 "owning order")
        ent = world.get(code)
        if ent is None:
            continue
        for ed in world.edges:
            if ed.subject == code and ed.connection == _APPLIES_IN:
                _add(ed.object, "jurisdiction", "governed_by", ed.basis)
        for ed in world.edges:
            if ed.object == code and ed.connection == _ENFORCES:
                _add(ed.subject, "regulator", "enforced_by", ed.basis)
    return out


# ── place_legal_text: a law's own text → anchored provisions ─────────────────

import re as _re

# Article header: "Article 17", "Art. 17", "Artikel 17", "§ 286" (+ optional letter)
_ARTICLE_RE = _re.compile(
    r"(?im)^[ \t]*(?:(?:Article|Artikel|Art\.)\s+(\d+[a-z]?)"
    r"|§{1,2}\s*(\d+[a-z]?))\b")

# Numbered paragraph at line start: "1." or "(1)" (EU drafting style)
_PARA_RE = _re.compile(r"(?m)^[ \t]*(?:\((\d+[a-z]?)\)|(\d+[a-z]?)\.)\s")


@dataclass
class TextProvision:
    """One provision-level unit of a legal instrument, with its pinpoint."""

    article: str                       # "17"
    paragraph: Optional[str]           # "3" or None
    pinpoint: str                      # "Art. 17(3)" / "§ 286"
    text: str

    def to_dict(self) -> dict:
        return {"article": self.article, "paragraph": self.paragraph,
                "pinpoint": self.pinpoint, "text": self.text}


def _marker(prefix: str, article: str, paragraph: Optional[str]) -> str:
    base = f"{prefix} {article}"
    return f"{base}({paragraph})" if paragraph else base


def segment_provisions(text: str, *, max_provisions: int = 5000) -> List[TextProvision]:
    """Cut ``text`` into provision units — one :class:`TextProvision` per
    article-paragraph (or per article when it has no numbered paragraphs). Text
    before the first article header (recitals/preamble) is ignored. Pure regex,
    stdlib only; it locates provisions and pinpoints, it does not extract norms.

    Ported from the legal-norm splitter so a consumer that swaps in its own
    splitter (via the ``splitter`` argument of :func:`place_legal_text`) gets the
    same cut it did before."""
    heads = list(_ARTICLE_RE.finditer(text))
    if not heads:
        return []
    out: List[TextProvision] = []
    for i, m in enumerate(heads):
        art = m.group(1) or m.group(2)
        prefix = "Art." if m.group(1) else "§"
        start = m.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[start:end]
        paras = list(_PARA_RE.finditer(body))
        if not paras:
            prov_text = body.strip()
            if prov_text:
                out.append(TextProvision(art, None, _marker(prefix, art, None), prov_text))
        else:
            for j, pm in enumerate(paras):
                par = pm.group(1) or pm.group(2)
                p_start = pm.end()
                p_end = paras[j + 1].start() if j + 1 < len(paras) else len(body)
                prov_text = body[p_start:p_end].strip()
                if prov_text:
                    out.append(TextProvision(art, par, _marker(prefix, art, par), prov_text))
        if len(out) >= max_provisions:
            break
    return out[:max_provisions]


def _host_instrument_anchors(code: str, world: WorldMap) -> dict:
    """Resolve a host instrument's jurisdiction(s) and enforcing regulators once —
    from the instrument's own owning order plus its ``applies_in`` / ``enforces``
    edges on the world graph."""
    jurisdictions: List[str] = []
    regulators: List[str] = []
    ent = world.get(code)
    if ent is not None and ent.jurisdiction:
        jurisdictions.append(ent.jurisdiction)
    for ed in world.edges:
        if (ed.subject == code and ed.connection == _APPLIES_IN
                and ed.object not in jurisdictions):
            jurisdictions.append(ed.object)
        if (ed.object == code and ed.connection == _ENFORCES
                and ed.subject not in regulators):
            regulators.append(ed.subject)
    return {"code": code, "jurisdictions": jurisdictions, "regulators": regulators}


def _host_anchor_list(host: dict, pinpoint: str) -> List[Anchor]:
    """The anchors for one provision of the host instrument: the instrument
    itself (cited at the pinpoint), each of its jurisdictions, each enforcing
    regulator."""
    out = [Anchor(host["code"], "instrument", "cites", pinpoint)]
    for j in host["jurisdictions"]:
        out.append(Anchor(j, "jurisdiction", "governed_by", "owning order"))
    for r in host["regulators"]:
        out.append(Anchor(r, "regulator", "enforced_by", "mandate"))
    return out


def place_legal_text(text: str, world: Optional[WorldMap] = None,
                     instrument_code: str = "", *,
                     splitter=None) -> List[dict]:
    """Ingest a law's *own* text: cut it into provisions and anchor each to its
    host instrument (that instrument at the provision's pinpoint, its
    jurisdiction(s), its enforcing regulators) plus any in-text cross-references.

    ``instrument_code`` is the host instrument's code in ``world``. ``splitter``
    is a ``str -> list`` provision splitter — each provision must expose
    ``.text`` / ``["text"]`` and ``.pinpoint`` / ``["pinpoint"]`` — defaulting to
    the built-in :func:`segment_provisions`. Generic out: a list of provision
    dicts, each ``{article, paragraph, pinpoint, text, anchors}`` where
    ``anchors`` is a list of :class:`Anchor`. No norm extraction, no host paths.
    """
    if world is None:
        world = seed_world()
    split = splitter or segment_provisions
    host = _host_instrument_anchors(instrument_code, world)

    out: List[dict] = []
    for prov in split(text):
        ptext = _prov_field(prov, "text")
        pinpoint = _prov_field(prov, "pinpoint")
        anchors = _host_anchor_list(host, pinpoint)
        for a in anchor(ptext, world):        # in-text cross-references
            if a.entity != instrument_code:
                anchors.append(a)
        out.append({
            "article": _prov_field(prov, "article"),
            "paragraph": _prov_field(prov, "paragraph") or None,
            "pinpoint": pinpoint,
            "text": ptext,
            "anchors": anchors,
        })
    return out


def _prov_field(prov, name: str) -> str:
    if isinstance(prov, dict):
        return prov.get(name, "") or ""
    return getattr(prov, name, "") or ""
