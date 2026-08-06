# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Instrument identity is a stable code, never the title. Work-level = CELEX;
expression-level = a consolidated CELEX / ELI point-in-time (work × in-force
date) — what a versioned conclusion actually cites."""
from __future__ import annotations

import pytest

from loomground_legal import consolidated_celex, eli_at, version_id


def test_consolidated_celex_is_work_plus_point_in_time() -> None:
    # GDPR base act, consolidated as of 2018-05-25
    assert consolidated_celex("32016R0679", "2018-05-25") == "02016R0679-20180525"


def test_eli_point_in_time_replaces_the_oj_segment() -> None:
    assert eli_at("https://eur-lex.europa.eu/eli/reg/2016/679/oj", "2018-05-25") \
        == "https://eur-lex.europa.eu/eli/reg/2016/679/2018-05-25"
    # a bare ELI stem just gets the date appended
    assert eli_at("/eli/reg/2016/679", "2018-05-25") == "/eli/reg/2016/679/2018-05-25"


def test_version_id_prefers_celex_falls_back_to_code() -> None:
    assert version_id(celex="32016R0679", in_force_date="2018-05-25") == "02016R0679-20180525"
    # a national law with no CELEX → code@date, still NOT the title
    assert version_id(code="bdsg", in_force_date="2018-05-25") == "bdsg@2018-05-25"


def test_version_id_needs_an_anchor_and_a_valid_date() -> None:
    with pytest.raises(ValueError):
        version_id(in_force_date="2018-05-25")            # no celex or code
    with pytest.raises(ValueError):
        version_id(celex="32016R0679", in_force_date="2018")  # not ISO YYYY-MM-DD
