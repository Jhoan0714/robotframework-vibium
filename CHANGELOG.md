# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.2.0]: https://github.com/Jhoan0714/robotframework-vibium/releases/tag/v0.2.0
[0.1.1]: https://github.com/Jhoan0714/robotframework-vibium/releases/tag/v0.1.1
[0.1.0]: https://github.com/Jhoan0714/robotframework-vibium/releases/tag/v0.1.0
