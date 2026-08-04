<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# Security policy

## Supported versions

loomground-legal is currently pre-1.0. Security fixes are made on the latest
release line only.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private
vulnerability reporting for this repository. Include the affected version or
commit, reproduction steps, impact, and any suggested mitigation. Please allow
the maintainer time to investigate before public disclosure.

This repository ships a standard-library-only legal **domain plane** — typed
legal entities, a jurisdictional connection table consumed through the solver's
`RelationAlgebra`, and a legal-effect → deontic bridge. It has no network
service of its own and grows no reasoning: composition and inference run on
`loomground-solver`, the modal vocabulary on `loomground-deontic`. A
vulnerability report against this repository is most likely to concern the
connection/effect data artifacts (`src/loomground_legal/artifacts/`), the
effect→deontic bridge, or the build and release pipeline; please say which of
these is affected.
