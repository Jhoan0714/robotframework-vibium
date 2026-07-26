# Architecture

## Goals

- Keep the public keyword API stable and easy to understand.
- Isolate Vibium runtime lifecycle from keyword definitions.
- Make contributions low-risk by separating concerns by domain.

## Package layout

Import for Robot Framework: `Library    Vibium` (shim at `src/Vibium.py`).

Implementation package: `src/rfvibium/`.

| Path | Role |
|------|------|
| `rfvibium/library.py` | Public `Vibium` library class (`DynamicCore`) |
| `rfvibium/browser_session.py` | `SessionPool` + per-browser `BrowserSession` |
| `rfvibium/locator.py` | Locator token parsing / resolution |
| `rfvibium/keywords/` | Domain keyword components |
| `rfvibium/version.py` | Single package version (`__version__`) |
| `rfvibium/errors.py`, `utils.py`, `types.py` | Shared errors, helpers, typing aliases |

Keyword modules under `keywords/`: `navigation`, `mouse`, `interaction`, `assertions`, `capture`, `context` (cookies/storage), `dialogs`, `waits`.

## Layers (DynamicCore composition)

1. **`rfvibium.library.Vibium`**
   - Public Robot Framework library; inherits `robotlibcore.DynamicCore`.
   - Owns shared session state as `self._session` (`SessionPool`).
   - Defines top-level lifecycle keywords (`Open Browser`, `Close Browser`, `Close All Browsers`).
   - Builds a list of keyword components and passes them to `DynamicCore.__init__`.

2. **Keyword components (`rfvibium.keywords.*`)**
   - One class per domain (for example `WaitKeywords`, `InteractionKeywords`).
   - Each stores `self.library` (the `Vibium` instance) in `__init__(self, library)`.
   - Keywords access the browser session via `self.library._session` (not via mixins).

3. **`rfvibium.browser_session.SessionPool`**
   - Starts/stops browsers and tracks active browser / context / page handles.
   - Provides resolve/require helpers used by keywords.
   - Internally wraps each open browser in a `BrowserSession`.

```text
Vibium (DynamicCore)
├── _session: SessionPool
└── components: [NavigationKeywords(self), WaitKeywords(self), ...]
                      │
                      └── self.library._session  →  SessionPool
```

## Testing strategy

- Unit tests validate deterministic Python behavior and delegation (often with fakes injected on `_session`).
- Acceptance tests validate Robot Framework import and keyword wiring.
- Future integration tests should run against deterministic demo pages.

## Evolution path

- Add async adapter when Vibium async API is needed.
- Add richer selector strategy and typed element reference abstraction.
- Add tracing/network/debug keywords for CI diagnostics.
