# Architecture

## Goals

- Keep the public keyword API stable and easy to understand.
- Isolate Vibium runtime lifecycle from keyword definitions.
- Make contributions low-risk by separating concerns by domain.

## Responsibility boundary

This library is a Robot Framework façade over Vibium’s **sync** browser API:
session lifecycle, locators, page/element interaction, waits, and capture,
plus optional AssertionEngine checks on getters. Keyword modules stay thin
wrappers; behavior and engine quirks belong to Vibium.

User-facing install, locator cookbook, and concurrency notes live in the
[README](../README.md). Libdoc is the keyword API reference.

## Package layout

Import for Robot Framework: `Library    Vibium` (shim at `src/Vibium.py`).

Implementation package: `src/rfvibium/`.

| Path | Role |
|------|------|
| `rfvibium/library.py` | Public `Vibium` library class (`DynamicCore`) |
| `rfvibium/session/browser_session.py` | `SessionPool` + per-browser `BrowserSession` |
| `rfvibium/locators/locator.py` | Locator token parsing / resolution |
| `rfvibium/assertions/helper.py` | AssertionEngine peel / verify helpers |
| `rfvibium/config/settings.py` | `SettingLayers` — scoped library settings (Global / Suite / Test) |
| `rfvibium/keywords/` | Domain keyword components |
| `rfvibium/version.py` | Single package version (`__version__`) |
| `rfvibium/errors.py`, `utils.py`, `types.py` | Shared errors, helpers, typing aliases (`PageScope`, `FindScope`, `Locator`, …) |

Keyword modules under `keywords/`: `navigation`, `interaction`, `assertions`,
`waits`, `capture`, `context` (cookies/storage), `dialogs`, `mouse`, `keyboard`,
`touch`, `emulation`, `document`, `config`.

## Layers (DynamicCore composition)

1. **`rfvibium.library.Vibium`**
   - Public Robot Framework library; inherits `robotlibcore.DynamicCore`.
   - Owns shared session state as `self._session` (`SessionPool`).
   - Owns scoped settings as `self._settings` (`SettingLayers`).
   - Defines top-level lifecycle keywords (`Open Browser`, `Close Browser`,
     `Close All Browsers`).
   - Builds a list of keyword components and passes them to `DynamicCore.__init__`.

2. **Keyword components (`rfvibium.keywords.*`)**
   - One class per domain (for example `WaitKeywords`, `InteractionKeywords`).
   - Each stores `self.library` (the `Vibium` instance) in `__init__(self, library)`.
   - Keywords access the browser session via `self.library._session` (not via mixins).
   - Optional inline assertions on getters go through `rfvibium.assertions.helper`.

3. **`rfvibium.session.browser_session.SessionPool`**
   - Starts/stops browsers and tracks active browser / context / page handles.
   - Provides resolve/require helpers used by keywords.
   - Internally wraps each open browser in a `BrowserSession`.

```text
Vibium (DynamicCore)
├── _session: SessionPool
├── _settings: SettingLayers
└── components: [NavigationKeywords(self), WaitKeywords(self), ...]
                      │
                      └── self.library._session  →  SessionPool
```

## Runtime stack

How a Robot keyword reaches the browser:

```text
Robot Framework (test runner)
        │
        │  Library    Vibium
        ▼
robotframework-vibium
├── DynamicCore (PythonLibCore)     — discovery / dispatch of @keyword
├── keyword components              — Click, Get Text, Wait For …
├── SessionPool / locators / settings
└── Assertion engine ──────────────► robotframework-assertion-engine
        │                               (optional peel / verify on getters)
        ▼
Vibium (sync Python API)
        │
        ▼
Browser (Chrome / Firefox via BiDi)
```

| Piece | Role |
|-------|------|
| **Robot Framework** | Runs the suite and calls keywords |
| **DynamicCore** | From `robotframework-pythonlibcore`: registers and dispatches `@keyword` |
| **robotframework-vibium** | Façade: locators, session, thin wrappers |
| **AssertionEngine** | Optional inline verify on getters only (not on the path to the browser) |
| **Vibium** | Sync browser automation API |
| **Browser** | Chrome / Firefox via BiDi |

## Locators

`rfvibium/locators/locator.py` parses `strategy:value` tokens and CSS strings
into `page.find(...)` arguments. Pierce combinators (`>>` / `>>>`) are part of
the CSS selector string handled by the Vibium engine; this package does not
implement a separate pierce layer. Nested find uses Vibium element handles as
`scope=`. Details and Robot examples: [README](../README.md#locator-syntax).

## Assertions

Getters may optionally verify with
[robotframework-assertion-engine](https://github.com/MarketSquare/AssertionEngine).
`rfvibium/assertions/helper.py` peels trailing operators from locator args and
calls verify; without an operator the getter only returns the value. Keyword
docs / Libdoc cover operators and examples.

## Testing strategy

- Unit tests validate deterministic Python behavior and delegation (often with
  fakes injected on `_session`).
- Acceptance tests exercise real browser wiring under `tests/acceptance/`.

## Evolution

- Prefer additive keywords and new `keywords/*` modules over growing `library.py`.
- Keep `types.py` aliases aligned with Vibium sync types used at the boundary.
