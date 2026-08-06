# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Load the world-map reference tables into a populated :class:`WorldMap`.

Four markdown reference tables (global digital laws, harmonized standards,
international law, and international organisations) hold the corpus. This module
parses them and builds a connected :class:`loomground_legal.world.WorldMap` —
countries, federations/blocs, regulators, standards bodies, treaty bodies and
instruments — with the edges derivable from the tables (a law *applies in* its
jurisdiction; a treaty *adopted by* its body; a standard *established by* its
organisation; EU-27 *member of* the EU).

This is the step that turns the four lists from inert reference files into the
graph the rest of the stack reasons over. Pure stdlib.

**Bring your own corpus.** :func:`build_world` takes the reference directory as an
argument — it is *injected*, never resolved here. The host (RVND) owns the
``WORKSPACE_WORLD_MAP_DIR`` / ``~/.workspace`` resolver; the package stays free of
any environment or home-directory assumption. The markdown parser and the
country/``EU27``/body-code maps are lifted verbatim from RVND
``world_corpus_loader``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .world import Entity, EntityKind, WorldMap


# ── markdown table parsing ────────────────────────────────────────────────────

def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_sep(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and set(s.replace("|", "").replace(" ", "")) <= set("-:")


def parse_md(path: Path) -> list[tuple[str, dict]]:
    """Return (section_heading, row_dict) for every data row in a markdown file."""
    rows: list[tuple[str, dict]] = []
    cols: Optional[list[str]] = None
    section = ""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    for i, l in enumerate(lines):
        s = l.strip()
        if s.startswith("#"):
            section = s.lstrip("#").strip()
            continue
        if not s.startswith("|") or _is_sep(l):
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        cell = _cells(l)
        if _is_sep(nxt):                       # this row is a header
            cols = cell
            continue
        if cols and len(cell) >= 2:
            rows.append((section, dict(zip(cols, cell))))
    return rows


# ── normalisers ───────────────────────────────────────────────────────────────

_ACRONYM = re.compile(r"\(([A-Z][A-Za-z0-9/\.\-]{1,12})\)\s*$")
_PARENS = re.compile(r"\s*\([^)]*\)\s*$")


def _slug(name: str, *, prefer_acronym: bool = True) -> str:
    name = name.replace("*", "").strip()
    m = _ACRONYM.search(name)
    if prefer_acronym and m:
        return re.sub(r"[^a-z0-9]+", "-", m.group(1).lower()).strip("-")
    base = _PARENS.sub("", name)
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")[:48] or "x"


def _clean(name: str) -> str:
    return name.replace("*", "").strip()


# country code → readable name + region (continent group)
_COUNTRY = {
    "US": ("United States", "Americas"), "CA": ("Canada", "Americas"),
    "BR": ("Brazil", "Americas"), "AR": ("Argentina", "Americas"),
    "MX": ("Mexico", "Americas"), "CO": ("Colombia", "Americas"),
    "CL": ("Chile", "Americas"), "PE": ("Peru", "Americas"),
    "UK": ("United Kingdom", "Europe"), "CH": ("Switzerland", "Europe"),
    "RU": ("Russia", "Europe"), "UA": ("Ukraine", "Europe"),
    "DE": ("Germany", "Europe"), "FR": ("France", "Europe"),
    "IE": ("Ireland", "Europe"), "NL": ("Netherlands", "Europe"),
    "JP": ("Japan", "Asia-Pacific"), "KR": ("South Korea", "Asia-Pacific"),
    "SG": ("Singapore", "Asia-Pacific"), "PH": ("Philippines", "Asia-Pacific"),
    "TH": ("Thailand", "Asia-Pacific"), "ID": ("Indonesia", "Asia-Pacific"),
    "MY": ("Malaysia", "Asia-Pacific"), "VN": ("Vietnam", "Asia-Pacific"),
    "IN": ("India", "Asia-Pacific"), "CN": ("China", "Asia-Pacific"),
    "AU": ("Australia", "Asia-Pacific"), "NZ": ("New Zealand", "Asia-Pacific"),
    "TR": ("Türkiye", "Middle East"), "SA": ("Saudi Arabia", "Middle East"),
    "AE": ("United Arab Emirates", "Middle East"), "IL": ("Israel", "Middle East"),
    "QA": ("Qatar", "Middle East"), "BH": ("Bahrain", "Middle East"),
    "ZA": ("South Africa", "Africa"), "NG": ("Nigeria", "Africa"),
    "KE": ("Kenya", "Africa"), "EG": ("Egypt", "Africa"),
    "GH": ("Ghana", "Africa"), "RW": ("Rwanda", "Africa"), "UG": ("Uganda", "Africa"),
}

EU27 = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
        "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
        "SI", "ES", "SE"]
_EU27_NAMES = {"AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "HR": "Croatia",
    "CY": "Cyprus", "CZ": "Czechia", "DK": "Denmark", "EE": "Estonia",
    "FI": "Finland", "GR": "Greece", "HU": "Hungary", "IT": "Italy", "LV": "Latvia",
    "LT": "Lithuania", "LU": "Luxembourg", "MT": "Malta", "PL": "Poland",
    "PT": "Portugal", "RO": "Romania", "SK": "Slovakia", "SI": "Slovenia",
    "ES": "Spain", "SE": "Sweden"}


def _norm_jur(j: str) -> str:
    j = j.strip()
    if "-" in j:                # US-CA → US (state laws group under the federation)
        j = j.split("-")[0]
    return {"China": "CN", "EU": "EU"}.get(j, j)


# org section heading → entity kind
def _org_kind(section: str) -> EntityKind:
    s = section.lower()
    if "standard" in s or "registr" in s or "internet governance" in s:
        return EntityKind.STANDARDS_BODY
    if "regulator" in s:
        return EntityKind.REGULATOR
    return EntityKind.INTERNATIONAL_REGIME


# treaty/standards body name → canonical code (so the same body merges)
_BODY_CODE = {
    "un": "un", "united nations": "un", "wipo": "wipo", "wto": "wto", "oecd": "oecd",
    "council of europe": "coe", "uncitral": "uncitral", "unesco": "unesco",
    "itu": "itu", "hcch": "hcch", "african union": "au", "upu": "upu",
    "iso": "iso", "iec": "iec", "iso/iec": "iso-iec", "nist": "nist",
    "ieee": "ieee", "etsi": "etsi", "w3c": "w3c", "ietf": "ietf",
    "cen-cenelec": "cen-cenelec", "oasis": "oasis", "aicpa": "aicpa",
    "csa": "csa", "common criteria": "common-criteria", "g7": "g7", "g20": "g20",
    "fatf": "fatf", "plurilateral": "plurilateral", "regional": "regional",
    "multistakeholder": "multistakeholder", "ilo": "ilo",
}


def _body_code(name: str) -> str:
    return _BODY_CODE.get(name.strip().lower(), _slug(name, prefer_acronym=False))


def _org_code(name: str) -> str:
    """Stable code for an organisation row, in priority order:
    1. canonical map (so 'Council of Europe' merges with the treaty body 'coe');
    2. leading acronym ('CNIL (France)' → cnil — never the country in parens);
    3. parenthetical acronym only if ALL-CAPS ('… (ASEAN)' → asean; '(Germany)' never);
    4. slug of the head."""
    clean = _clean(name)
    head = clean.split("(")[0].strip()
    for key in (clean.lower(), head.lower()):
        if key in _BODY_CODE:
            return _BODY_CODE[key]
    if head and head.upper() == head and len(head) <= 14:
        return re.sub(r"[^a-z0-9]+", "-", head.lower()).strip("-")
    m = re.search(r"\(([A-Z][A-Z0-9\-]{1,11})\)\s*$", clean)
    if m:
        return re.sub(r"[^a-z0-9]+", "-", m.group(1).lower()).strip("-")
    return re.sub(r"[^a-z0-9]+", "-", (head or clean).lower()).strip("-")[:48] or "x"


# ── build ─────────────────────────────────────────────────────────────────────

def build_world(refdir: str | Path) -> WorldMap:
    """Build a :class:`WorldMap` from the four markdown reference tables in
    ``refdir``.

    ``refdir`` is injected by the caller — the package does not resolve it from
    the environment or the home directory. RVND owns the
    ``WORKSPACE_WORLD_MAP_DIR`` / ``~/.workspace`` resolver and passes the path in.
    """
    if refdir is None:
        raise ValueError(
            "build_world requires a reference directory (refdir); the package "
            "does not resolve WORKSPACE_WORLD_MAP_DIR — the host injects the path")
    refdir = Path(refdir)
    w = WorldMap()
    seen: set[str] = set()

    def add(code, name, kind, **kw):
        if code and code not in seen:
            seen.add(code)
            w.add(Entity(code=code, name=_clean(name), kind=kind, **kw))
        return code

    def ensure_country(code: str):
        if code == "EU":
            return add("EU", "European Union", EntityKind.SUPRANATIONAL, region="Europe")
        if code in _COUNTRY:
            nm, region = _COUNTRY[code]
        elif code in _EU27_NAMES:
            nm, region = _EU27_NAMES[code], "Europe"
        else:
            nm, region = code, ""
        return add(code, nm, EntityKind.STATE, jurisdiction=code, region=region)

    # EU + EU-27 membership
    ensure_country("EU")
    for c in EU27:
        ensure_country(c)
        w.connect(c, "member_of", "EU", basis="TEU Art. 1 / Accession Treaty")

    # 1. organisations
    for section, r in parse_md(refdir / "international-organisations.md"):
        name = r.get("Name") or ""
        if not name:
            continue
        code = _org_code(name)
        add(code, name, _org_kind(section), url=r.get("Homepage URL") or r.get("URL"),
            facets={"role": r.get("Role", ""), "seat": r.get("Main Seat") or r.get("Seat", "")})

    # 2. instruments — global digital laws → applies_in jurisdiction
    for _section, r in parse_md(refdir / "digital-laws-global.md"):
        name = r.get("Name")
        jur = _norm_jur(r.get("Jurisdiction", "") or "")
        if not jur and "china" in _section.lower():
            jur = "CN"            # the China subtable carries no Jurisdiction column
        if not name or not jur:
            continue
        code = _slug(name)
        add(code, name, EntityKind.INSTRUMENT, url=r.get("URL"), jurisdiction=jur,
            domains=tuple(x.strip() for x in (r.get("Category", "") or "").split("/") if x.strip()))
        ensure_country(jur if jur != "EU" else "EU")
        w.connect(code, "applies_in", jur, basis="national/sub-national law")

    # 3. international law — treaty/soft-law → adopted_by body
    for section, r in parse_md(refdir / "international-law.md"):
        name = r.get("Name")
        if not name:
            continue
        code = _slug(name)
        soft = "soft" in section.lower()
        add(code, name, EntityKind.INSTRUMENT, url=r.get("URL"),
            facets={"type": r.get("Type", ""), "register": "soft-law" if soft else "binding"})
        body = (r.get("Body") or "").strip()
        if body:
            bc = _body_code(body)
            add(bc, body, EntityKind.INTERNATIONAL_REGIME)
            w.connect(code, "adopted_by", bc, basis=r.get("Type", "instrument"))

    # 4. harmonized standards → established_by organisation
    for section, r in parse_md(refdir / "harmonized-standards.md"):
        std = r.get("Standard")
        if not std:
            continue
        org = (r.get("Org") or "").strip()
        if not org:                     # subtables without an Org column: org is the section
            org = section.split("/")[0].strip()
        oc = _body_code(org) if org else ""
        code = _slug(std, prefer_acronym=False)
        add(code, std, EntityKind.INSTRUMENT, url=r.get("URL"),
            facets={"kind": "technical_standard", "org": org, "focus": r.get("Focus", "")})
        if oc:
            add(oc, org, EntityKind.STANDARDS_BODY)
            w.connect(code, "established_by", oc, basis="issued by")
    return w
