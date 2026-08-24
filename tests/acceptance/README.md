# Acceptance Tests

Acceptance tests validate the public Robot Framework keywords end-to-end.

## Suites

- `smoke.robot`: minimal import/open/navigation check.
- `navigation.robot`: URL navigation, history, reload, and multi-tab list/switch/close.
- `interaction.robot`: element interaction against an injected test fixture.
- `pierce.robot`: Shadow DOM pierce locators (`>>` / `>>>`; requires Vibium ≥ 26.8.21).
- `artifacts.robot`: full-page and element screenshots plus PDF artifact generation.
- `frames.robot`: object-first frame scope workflows.
- `storage_cookies.robot`: cookie and storage state workflows.
- `negative.robot`: invalid usage and expected error contracts.
- `waits.robot`: wait and synchronization workflows (including load state and deferred visibility).
- `mouse.robot`: low-level mouse command coverage.
- `dialogs.robot`: browser dialog handling flows.
- `assertions.robot`: read-only getters (`Evaluate JavaScript`, `Get Title`, `Count Elements`).
- `multi_browser.robot`: two `Open Browser` instances with scoped URL reads (no suite browser setup).

## Run

From repository root:

```bash
robot --pythonpath src -d reports/acceptance tests/acceptance
```

Run only smoke tests:

```bash
robot --pythonpath src -i smoke -d reports/acceptance tests/acceptance
```

Run pierce tests (requires Vibium ≥ 26.8.21; exclude from CI until dependency floor is raised — #47):

```bash
robot --pythonpath src -v HEADLESS:True -i pierce -d reports/acceptance tests/acceptance
```
