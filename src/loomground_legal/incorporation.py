# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Legal INCORPORATION / cross-reference — two composition operations of the legal
algebra, one for *force*, one for *identity*.

A source of law does not always bind by its own weight. A supranational directive,
or a treaty in a dualist order, is **non-self-executing**: it binds the facts only
once an *incorporating* instrument (a national statute transposing the directive, a
ratification act incorporating the treaty) carries it into the domestic order. That
is the SC-3 invariant of :mod:`source_classes`, made an operation here:

  * :func:`incorporate` composes ``source × incorporating → Incorporation`` — does
    the incorporating statement *validly* carry the source into binding force? The
    honesty spine is SC-3: a source that requires incorporation and has **no**
    admissible ``transposes`` / ``incorporates`` edge from a BINDING incorporator is
    **OPEN — not yet binding**, never a fabricated "binding". A self-executing
    source needs no edge (SATISFIED, it already binds).

  * :func:`resolve_reference` composes ``citation → InstrumentRef`` — resolves a
    citation string to a concrete instrument, consuming :mod:`crossref`'s resolvers
    (CELEX → citation-number → short-name) and ``infer_host_instrument`` for the
    host. An unresolvable citation is **None**, never a guessed instrument.

This module **consumes and re-grows nothing**: citation parsing is ``crossref``'s;
source force / self-execution / relation admissibility is ``source_classes``'; the
verdict vocabulary is the solver's ``cross_subsumption.Verdict``. It adds only the
two compositions and their honest terminals (unincorporated → OPEN, unresolved →
None).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from loomground_solver.cross_subsumption import Verdict

from .crossref import (
    InstrumentRef,
    infer_host_instrument,
    resolve_celex,
    resolve_citation_number,
    resolve_short_name,
)
from .grammar import LegalStatement
from .source_classes import (
    Effect,
    Relation,
    is_relation,
    max_effect,
    self_executes,
)

__all__ = [
    "Incorporation",
    "incorporate",
    "resolve_reference",
    "INCORPORATION_RELATIONS",
]


# The admissible *incorporation* relations — the subset of the universal Relation
# vocabulary that carries a non-self-executing source into binding force. Every
# member is in ``source_classes.VOCABULARY`` (guarded via ``is_relation`` at call
# time); ``outranks`` / ``supersedes`` / ``member_of`` / ``presumes_conformity`` are
# admissible edges but do NOT incorporate.
INCORPORATION_RELATIONS: frozenset = frozenset(
    {Relation.TRANSPOSES.value, Relation.INCORPORATES.value}
)


@dataclass(frozen=True)
class Incorporation:
    """The outcome of composing ``source × incorporating``.

    ``verdict``: **SATISFIED** = the source binds (it self-executes, or a BINDING
    incorporator carries an admissible incorporation edge to it); **OPEN** = it does
    **not (yet) bind** — the honest SC-3 terminal (a directive without transposition,
    a treaty without a ratifying act, an incorporator that cannot itself bind). There
    is no fabricated "binding": OPEN says *incorporate it, then it binds*.

    ``binds`` mirrors the verdict (True iff SATISFIED). ``incorporating`` is the id
    of the incorporating instrument (``None`` for a self-executing source that needed
    none); ``relation`` is the incorporation relation that actually carried it
    (``None`` when none did)."""

    verdict: Verdict
    binds: bool
    incorporating: Optional[str]
    reason: str
    relation: Optional[str] = None

    @property
    def escalates(self) -> bool:
        """OPEN is the escalate terminal — not-yet-binding, surfaced not fabricated."""
        return self.verdict is Verdict.OPEN


def incorporate(source: LegalStatement, incorporating: LegalStatement, *,
                relation: str = "transposes") -> Incorporation:
    """Does ``incorporating`` validly carry ``source`` into binding force?

    Consumes ``source_classes`` for every force/relation judgement — regrows none:

    1. **Self-executing source** — if ``source``'s class binds without an
       incorporation step (``self_executes``, widened by its ``self_executing_extra``),
       it already binds; incorporation is a no-op → **SATISFIED** (``incorporating``
       is ``None``).
    2. **Non-self-executing source** — it requires an incorporation edge (SC-3). The
       ``incorporating`` statement must carry a ``(rel, <source id>)`` in its
       ``relations`` where ``rel`` is an admissible incorporation relation
       (``transposes`` / ``incorporates`` — in the universal vocabulary via
       ``is_relation`` **and** in :data:`INCORPORATION_RELATIONS`), pointing at
       ``source.source``; **and** ``incorporating`` must itself be BINDING
       (``claimed_effect`` is ``Effect.BINDING`` and its class ceiling
       ``max_effect`` is ``Effect.BINDING`` — a soft-law or interpretive instrument
       cannot confer force it does not have). Both hold → the source is incorporated
       → **SATISFIED** (it binds). Otherwise → **OPEN**: it does not bind the facts
       until incorporated — never fabricated as binding.

    The asserted ``relation`` is validated as an admissible incorporation relation
    (an inadmissible assertion, e.g. ``"supersedes"``, → OPEN) and is *preferred*
    when several admissible edges exist; a valid edge in the other admissible mode
    still incorporates."""
    src_id = source.source

    # (1) self-executing → already binds, no edge needed.
    if self_executes(source.source_class, source.self_executing_extra):
        return Incorporation(
            Verdict.SATISFIED, True, None,
            f"{src_id} ({source.source_class.value}) is self-executing — it binds "
            f"the facts directly; incorporation is a no-op.",
            relation=None)

    # (2) requires an incorporation edge (SC-3).
    # The asserted mode must itself be an admissible incorporation relation.
    if not (is_relation(relation) and relation in INCORPORATION_RELATIONS):
        return Incorporation(
            Verdict.OPEN, False, incorporating.source,
            f"asserted relation {relation!r} is not an admissible incorporation "
            f"relation (transposes/incorporates) — {src_id} is NOT YET binding (SC-3).",
            relation=None)

    # Find every admissible incorporation edge from `incorporating` to `source`.
    edges = [(rel, obj) for rel, obj in incorporating.relations
             if obj == src_id and is_relation(rel) and rel in INCORPORATION_RELATIONS]
    if not edges:
        return Incorporation(
            Verdict.OPEN, False, incorporating.source,
            f"{src_id} ({source.source_class.value}) is non-self-executing and "
            f"{incorporating.source} carries no transposes/incorporates edge to it — "
            f"NOT YET binding (SC-3): incorporate it, then it binds.",
            relation=None)

    # Prefer the asserted mode; any admissible incorporation edge otherwise.
    rel, _ = next((e for e in edges if e[0] == relation), edges[0])

    # The incorporator must itself carry binding force — it cannot confer force it
    # does not have (a soft-law/interpretive instrument cannot transpose a directive).
    if not (incorporating.claimed_effect is Effect.BINDING
            and max_effect(incorporating.source_class) is Effect.BINDING):
        return Incorporation(
            Verdict.OPEN, False, incorporating.source,
            f"{incorporating.source} ({incorporating.source_class.value}) is not "
            f"itself a BINDING instrument (claimed {incorporating.claimed_effect.name}, "
            f"ceiling {max_effect(incorporating.source_class).name}) — it cannot "
            f"confer binding force; {src_id} is NOT YET binding (SC-3).",
            relation=rel)

    # Valid incorporation: the source is carried into binding force.
    return Incorporation(
        Verdict.SATISFIED, True, incorporating.source,
        f"{src_id} ({source.source_class.value}) is incorporated by "
        f"{incorporating.source} via {rel} → it binds the facts.",
        relation=rel)


def resolve_reference(citation: str, *, host: Optional[str] = None
                      ) -> Optional[InstrumentRef]:
    """Resolve a citation string to a concrete :class:`~crossref.InstrumentRef`.

    Citation parsing is ``crossref``'s, not re-implemented here: the raw citation is
    tried against ``resolve_celex`` (an exact CELEX id), then
    ``resolve_citation_number`` (a ``YYYY/NN`` number by canonical containment), then
    ``resolve_short_name`` (a registered alias). The first hit wins; if all miss the
    result is **None** — an unresolvable citation is honestly unresolved, never
    guessed at.

    ``host``, when given, is the *citing document's content*: its host instrument is
    inferred (``crossref.infer_host_instrument``) and a citation that resolves to the
    host itself is a **self-reference** — there is no outbound instrument to resolve
    to, so the result is **None** (mirroring ``crossref.extract_cross_references``,
    which drops self-references)."""
    if not citation or not citation.strip():
        return None
    text = citation.strip()

    ref = (resolve_celex(text)
           or resolve_citation_number(text)
           or resolve_short_name(text))
    if ref is None:
        return None                      # honest: unresolved, never guessed

    if host:
        host_code = infer_host_instrument(host)
        if host_code and ref.code == host_code:
            return None                  # self-reference: names the host, not an outbound instrument

    return ref
