# Acceptance Tests

Acceptance tests validate the public Robot Framework keywords end-to-end.

## Suites

- `smoke.robot`: minimal import/open/navigation check.
- `navigation.robot`: URL navigation, history, reload, and multi-tab list/switch/close.
- `interaction.robot`: element interaction against an injected test fixture.
- `artifacts.robot`: full-page and element screenshots plus PDF artifact generation.
- `frames.robot`: object-first frame scope workflows.
- `storage_cookies.robot`: cookie and storage state workflows.
- `negative.robot`: invalid usage and expected error contracts.
- `waits_acceptance.robot`: wait and synchronization workflows (including load state and deferred visibility).
- `mouse_acceptance.robot`: low-level mouse command coverage.
- `dialogs_acceptance.robot`: browser dialog handling flows.
- `assertions_acceptance.robot`: read-only getters (`Evaluate JavaScript`, `Get Title`, `Count Elements`).
- `multi_browser_acceptance.robot`: two `Open Browser` instances with scoped URL reads (no suite browser setup).

## Run

From repository root:

```bash
robot --pythonpath src -d reports/acceptance tests/acceptance
```

Run only smoke tests:

```bash
robot --pythonpath src -i smoke -d reports/acceptance tests/acceptance
```
