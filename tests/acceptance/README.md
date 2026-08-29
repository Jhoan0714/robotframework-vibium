# Acceptance Tests

Acceptance tests validate the public Robot Framework keywords end-to-end.

## Suites

- `smoke.robot`: minimal import/open/navigation check.
- `navigation.robot`: URL navigation, history, reload, and multi-tab list/switch/close.
- `interaction.robot`: element interaction against an injected test fixture.
- `pierce.robot`: Shadow DOM pierce locators (`>>` / `>>>`; requires Vibium ≥ 26.8.21).
- `engine.robot`: `Open Browser` `engine=` (Chrome default vs Firefox; Firefox needs `vibium install --engine firefox`).
- `artifacts.robot`: full-page and element screenshots plus PDF artifact generation.
- `frames.robot`: object-first frame scope workflows.
- `storage_cookies.robot`: cookie, storage state, and ``Clear Storage`` workflows.
- `negative.robot`: invalid usage and expected error contracts.
- `waits.robot`: wait and synchronization workflows (including load state and deferred visibility).
- `mouse.robot`: low-level mouse command coverage (including ``Mouse Wheel``).
- `document.robot`: ``Set Page Content`` DOM injection.
- `keyboard.robot`: ``Keyboard Type``, ``Keyboard Key``, and element ``Press Keys``.
- `emulation.robot`: viewport and OS window size keywords.
- `dialogs.robot`: browser dialog handling flows.
- `assertions.robot`: read-only getters (`Evaluate JavaScript`, `Get Title`, `Count Elements`).
- `multi_browser.robot`: two `Open Browser` instances with scoped URL reads (Chrome+Chrome and Chrome+Firefox; Firefox needs `vibium install --engine firefox`).
- `connect.robot`: ``Open Browser    url=...`` remote BiDi connect (``no-ci``; needs ``VIBIUM_CONNECT_URL``).

## Tags

- **`no-ci`**: tests that need a display (headed browser) or a remote BiDi URL. Exclude in CI with ``-e no-ci``.
- **`firefox`**: Firefox engine cases; exclude with ``-e firefox`` when Firefox is not installed.

## Run

From repository root:

```bash
robot --pythonpath src -d reports/acceptance tests/acceptance
```

Run only smoke tests:

```bash
robot --pythonpath src -i smoke -d reports/acceptance tests/acceptance
```

Run pierce tests (requires Vibium ≥ 26.8.21):

```bash
robot --pythonpath src -v HEADLESS:True -i pierce -d reports/acceptance tests/acceptance
```

Run engine tests (Firefox case requires `vibium install --engine firefox`; exclude with `-e firefox` if not installed):

```bash
robot --pythonpath src -v HEADLESS:True -i engine -d reports/acceptance tests/acceptance
```

CI-style acceptance run (exclude tests that need a display or remote BiDi URL):

```bash
robot --pythonpath src -v HEADLESS:True -e no-ci -e firefox -d reports/acceptance tests/acceptance
```

Run ``no-ci`` tests locally (headed override and/or remote connect):

```bash
robot --pythonpath src -v HEADLESS:True -i no-ci -d reports/acceptance tests/acceptance
robot --pythonpath src -v HEADLESS:True -v VIBIUM_CONNECT_URL:'wss://...' -i no-ci tests/acceptance/connect.robot
```
