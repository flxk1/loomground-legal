# Changelog

## [0.2.2](https://github.com/flxk1/loomground-legal/compare/legal-v0.2.1...legal-v0.2.2) (2026-08-18)


### Bug Fixes

* **deps:** lift the solver cap to &lt;0.6 ([#8](https://github.com/flxk1/loomground-legal/issues/8)) ([c955033](https://github.com/flxk1/loomground-legal/commit/c955033c4c75a5f8fa31c5989b850967da089636))
* **deps:** pin solver so CI can install, and correct two stale notes ([22ef769](https://github.com/flxk1/loomground-legal/commit/22ef769be659e39b286a0364228dae2ef28dc989))


### Documentation

* **roadmap:** reconstructing a chain of agency ([af051cb](https://github.com/flxk1/loomground-legal/commit/af051cb069a9856e447de56640d74ceb1554a817))
* **roadmap:** reconstructing a chain of agency ([0126135](https://github.com/flxk1/loomground-legal/commit/0126135fd5e7eca0c8631796bc2d2feb14ea6990))

## [0.2.1](https://github.com/flxk1/loomground-legal/compare/legal-v0.2.0...legal-v0.2.1) (2026-08-07)


### Bug Fixes

* correct the loomground-solver constraint from an unsatisfiable `>=0.3,<0.4` to `>=0.2,<0.3` — solver is 0.2.x (every consumed symbol ships there) and the phantom 0.3 floor made a shared install with loomground-ingest (solver<0.3) unresolvable ([f756221](https://github.com/flxk1/loomground-legal/commit/f756221216f79f55f703642d8d574cd7d3667291))

## [0.2.0](https://github.com/flxk1/loomground-legal/compare/legal-v0.1.0...legal-v0.2.0) (2026-08-06)


### Features

* analyse() — the legal-analysis front door (recognition → adjudication) ([f2a02d6](https://github.com/flxk1/loomground-legal/commit/f2a02d670714a5b6917ea984f88c837884b1386b))
* anchoring — map a rule/text to legal instruments (norm-independent) ([9aa97dd](https://github.com/flxk1/loomground-legal/commit/9aa97dddbe23f12adbdbdcd25bd1623719a79248))
* constitutional field pack + worked case running solver.proportionality ([00ca25b](https://github.com/flxk1/loomground-legal/commit/00ca25bebb3a1496e9e7d3b20f7b2e7348541f96))
* criminal field pack + worked criminal review (three-tier, in dubio) ([764a4da](https://github.com/flxk1/loomground-legal/commit/764a4da0c84461d0dfe042cbf48ec0264cf2e5e6))
* cross-references, document summary, competing definitions, referral classification ([1991a63](https://github.com/flxk1/loomground-legal/commit/1991a63e72b029c575e06d474e9654d941857141))
* expression-level instrument identity (versioning is not the title) ([f46470c](https://github.com/flxk1/loomground-legal/commit/f46470c99f2f3856d0b6b1243552b2aaa41432fc))
* graded worked reviews — administrative competence + intertemporal ([072722b](https://github.com/flxk1/loomground-legal/commit/072722b125b4ef6173bddd9d9c9a8990a323eab9))
* intertemporal version-selection + temporal index + retroactivity ([c42c3cb](https://github.com/flxk1/loomground-legal/commit/c42c3cb723753d5abe152c202f239e75f5bebd0e))
* legal grammar — statement + recognition gate + source-hierarchy order ([5addde7](https://github.com/flxk1/loomground-legal/commit/5addde7d516ac9513ae6d4811d198cba649bd8b9))
* legal relations, corpus, instruments, validate, contracts ([3e146b5](https://github.com/flxk1/loomground-legal/commit/3e146b519428042007560c2793c45f2c819cd16b))
* legal slice 2 - scope, sources, lifecycle, citation ([3bf8962](https://github.com/flxk1/loomground-legal/commit/3bf89624fc72688dfb1e94d0e1cbcde5f9a39891))
* legal system layer + incorporation ops (parallel sub-agents) ([a835347](https://github.com/flxk1/loomground-legal/commit/a8353478a58b04a971fba782ee21db0faf581c77))
* legal world layer - WorldMap + reach (on solver algebra) + seed ([28d3fa8](https://github.com/flxk1/loomground-legal/commit/28d3fa8e6c7a85d423634d21779f3ee7a80fac14))
* legal-algebra composition ops — apply + resolve_conflict ([16c4b22](https://github.com/flxk1/loomground-legal/commit/16c4b22ee355404bd201939eebce0f3318f417a9))
* legal-algebra derive + resolve (effect-firing + deontic conflict) ([b358f4b](https://github.com/flxk1/loomground-legal/commit/b358f4b3502a89277209c1cf3eb5a2b22aa70f0a))
* legal-field (branch-of-law) profiles + administrative pack ([89372e7](https://github.com/flxk1/loomground-legal/commit/89372e7a41afaea08f3dfad6806fe29790d0e098))
* loomground-legal MVP + publishable repo scaffold ([fec24bc](https://github.com/flxk1/loomground-legal/commit/fec24bca6a66cb6ba08b272ef47f9da27ceceddc))
* source-class map + legal-system packs (applicable-law theory) ([056fdb3](https://github.com/flxk1/loomground-legal/commit/056fdb344c8ecdb455bda44c728155ebe8bb30ea))
* subsume branch antecedents over a FactSpace (versum data in solver) ([f967914](https://github.com/flxk1/loomground-legal/commit/f96791418ac8562355c5ddb8aae4a2fa6bd10db3))


### Bug Fixes

* five self-review findings (lex-posterior time, determinate defects, dates) ([849dcee](https://github.com/flxk1/loomground-legal/commit/849dcee2ca3e3e3970e37bb508f9bd7dc977ab17))
* resolve_conflict lex-superior-only — no fabricated antichain winner ([092a66f](https://github.com/flxk1/loomground-legal/commit/092a66f78eba84cd4ed732478475acc46cb57f45))
* resolve() fail-safe — escalate on non-rankable + unknown-date posterior ([977e59c](https://github.com/flxk1/loomground-legal/commit/977e59c16d10438121e121b18f5b8d9765c94af5))

## Changelog

All notable changes to this project are documented here. This project adheres
to [Semantic Versioning](https://semver.org) and its releases are administered
by [Release Please](https://github.com/googleapis/release-please).
