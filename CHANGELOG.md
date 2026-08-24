# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Acceptance coverage for Shadow DOM pierce locators (`>>` / `>>>`) in
  `tests/acceptance/pierce.robot`, including negative cases for light-DOM
  selectors and single-hop vs deep pierce (requires Vibium ≥ 26.8.21). (#50)
- Optional ``engine=`` and ``channel=`` arguments on ``Open Browser`` for
  Chrome and Firefox launch (Vibium multi-engine support). (#53)
- Acceptance coverage for ``Open Browser`` ``engine=`` in
  ``tests/acceptance/engine.robot`` (Chrome default vs Firefox user-agent). (#53)
- Acceptance coverage for Chrome + Firefox multi-browser sessions in
  ``tests/acceptance/multi_browser.robot``. (#53)

### Changed
- Require `vibium>=26.8.21,<26.9` (was `>=26.5.31`). (#47)
- Migrate page waits from deprecated ``page.wait_until`` to
  ``wait_for_function`` / ``wait_for_url`` / ``wait_for_load`` in wait keywords
  and screenshot retry. Element ``wait_until`` for ``Wait For Element`` is
  unchanged. (#48)

## [0.3.0] - 2026-07-26
### Changed
- Renamed interaction/navigation/capture keywords to a concise convention
  (breaking; no deprecated aliases):
  `Click Element`→`Click`, `Double Click Element`→`Double Click`,
  `Hover Element`→`Hover`, `Focus Element`→`Focus`,
  `Clear Element`→`Clear Text`, `Fill Element`→`Fill Text`,
  `Check Element`→`Check`, `Uncheck Element`→`Uncheck`,
  `Scroll Element Into View`→`Scroll Into View`,
  `Get Element Text`→`Get Text`, `Get Element Inner Text`→`Get Inner Text`,
  `Get Element Value`→`Get Value`, `Get Element Role`→`Get Role`,
  `Get Element Label`→`Get Label`, `Reload Page`→`Reload`,
  `Save Pdf`→`Save Page As Pdf`. (#19)
- Unified duplicate getters (breaking): `Get Element Attr` /
  `Get Element Attribute`→`Get Attribute`; `Get Element Bounds` /
  `Get Element Bounding Box`→`Get Bounds`; removed `Get Element Html`
  (use `Get Html`). (#19, #22)
- Unified screenshots (breaking): `Take Screenshot` now accepts optional
  locators for element capture; removed `Take Element Screenshot`. With
  locators, `full_page` and `clip` are ignored. (#19)
- Single version source in `src/rfvibium/version.py` (Hatch dynamic version). (#12)
- Require `vibium>=26.5.31` and remove the local asyncio stdout monkeypatch. (#25)
- Publish Libdoc / GitHub Pages on GitHub Release only (not every push to `main`).

### Fixed
- Harden `parse_timeout_ms`: clear `VibiumLibraryError`s, reject negatives,
  support minutes. (#13)
- Make `SessionPool.close()` failure-safe (de-index in `finally`). (#14)
- Escape `Wait For Text` search text with `json.dumps` for safe JS. (#15)

### Added
- CI gates: ruff, mypy, and coverage (`fail_under=80`) on pull requests. (#10, #17)
- Pin Robot Framework 7.4.2 for Libdoc generation. (#9)

### Documentation
- Rewrite `docs/architecture.md` for DynamicCore composition. (#11)

## [0.2.0] - 2026-07-13
### Changed
- Refactored the library from multiple mixin inheritance to composition using
  PythonLibCore's `DynamicCore`. Each keyword component now receives the library
  instance and shares state via `self.library._session`. Purely internal; no
  keyword names or signatures changed. (#5, #6)

## [0.1.1] - 2026-05-08
### Fixed
- Avoid a `Vibium`/`vibium` import collision on case-insensitive filesystems by
  renaming the package from `Vibium` to `rfvibium` and adding a `Vibium.py`
  compatibility shim. (#4)

## [0.1.0] - 2026-05-08
### Added
- Initial alpha release of the Robot Framework library powered by Vibium.
- Browser lifecycle keywords (`Open Browser`, `Close Browser`,
  `Close All Browsers`) and keyword groups for navigation, mouse, interaction,
  assertions, capture, cookies, storage, dialogs and waits.
- Project scaffolding: packaging, docs and contributing guide.

[0.3.0]: https://github.com/Jhoan0714/robotframework-vibium/releases/tag/v0.3.0
[0.2.0]: https://github.com/Jhoan0714/robotframework-vibium/releases/tag/v0.2.0
[0.1.1]: https://github.com/Jhoan0714/robotframework-vibium/releases/tag/v0.1.1
[0.1.0]: https://github.com/Jhoan0714/robotframework-vibium/releases/tag/v0.1.0
