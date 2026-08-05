# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Instrument-registry metadata and CSV loader — the EU digital-acquis lookups.

The curated CELEX → canonical-code map (:data:`CODE`), the code → domain-tags map
(:data:`DOMAIN`), and the ordered ingest tranches (:data:`TRANCHES`) are lifted
verbatim from RVND ``regulatory_population``. :func:`load_instruments` is the CSV
parser that reads a "bring your own" instrument registry (CELEX, dates,
supersession, official source URL) into a ``{celex: row}`` dict.

**Data + parser only.** The ``populate_*`` functions (which write RVND's
``EntityRegistry``) and the ``default_csv()`` environment resolver
(``WORKSPACE_INSTRUMENTS_CSV`` / ``~/.workspace``) STAY in RVND — the package ships
no corpus and resolves no path. The caller injects ``csv_path``.
"""

from __future__ import annotations

import csv
from pathlib import Path

__all__ = ["CODE", "DOMAIN", "TRANCHES", "load_instruments"]


# CELEX → canonical corpus code (aligned with the seed + crossref registries)
CODE: dict[str, str] = {
    "31995L0046": "dpd-95", "32016R0679": "gdpr", "32016L1148": "nis1",
    "32022L2555": "nis2", "32024R1689": "ai-act",
    "32022R2065": "dsa", "32022R1925": "dma", "32022R0868": "dga",
    "32023R2854": "data-act", "32024R2847": "cra", "32014R0910": "eidas",
    "32002L0058": "eprivacy",
}
DOMAIN: dict[str, tuple[str, ...]] = {
    "dpd-95": ("data",), "gdpr": ("data",), "eprivacy": ("data",),
    "nis1": ("cyber",), "nis2": ("cyber",), "cra": ("cyber",),
    "ai-act": ("ai",), "dsa": ("platform",), "dma": ("digital-markets",),
    "dga": ("data",), "data-act": ("data",), "eidas": ("digital-identity",),
}

# Ordered tranches, mirroring the companion's domain skills.
TRANCHES: list[tuple[str, list[str]]] = [
    ("data-protection", ["31995L0046", "32016R0679", "32002L0058"]),
    ("cybersecurity",   ["32016L1148", "32022L2555", "32024R2847"]),
    ("ai-governance",   ["32024R1689"]),
    ("platform-content", ["32022R2065"]),
    ("digital-markets", ["32022R1925"]),
    ("data-economy",    ["32022R0868", "32023R2854", "32014R0910"]),
]


def load_instruments(csv_path: str | Path) -> dict[str, dict]:
    """CELEX → row dict, from a "bring your own" instrument registry CSV.

    ``csv_path`` is injected by the caller — the package does not resolve
    ``WORKSPACE_INSTRUMENTS_CSV`` or ``~/.workspace``; that resolver stays in the
    host (RVND ``regulatory_population.default_csv``).
    """
    if csv_path is None:
        raise FileNotFoundError(
            "load_instruments requires a csv_path; the package does not resolve "
            "WORKSPACE_INSTRUMENTS_CSV — the host injects the path")
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"instruments CSV not found: {path}")
    with open(path, encoding="utf-8") as fh:
        return {r["celex"]: r for r in csv.DictReader(fh)}
