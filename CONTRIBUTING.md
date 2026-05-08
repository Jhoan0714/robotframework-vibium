# Contributing to robotframework-vibium

Thanks for your interest in contributing.

## Prerequisites

- Python `>=3.9`
- `pip` available in your environment (`python -m pip --version`)
- A virtual environment tool (`venv` is recommended)
- Chrome or Chromium installed for local acceptance tests
- Git configured locally (`git --version`)

## Development setup

From repository root:

```bash
python3.9 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

## Branching and commits

- Do not commit directly to `main`.
- Create a feature branch from `main` (for example: `feat/new-keyword`).
- Keep commits focused and readable.
- Use clear commit messages (Conventional Commits are recommended):
  - `feat: ...`
  - `fix: ...`
  - `docs: ...`
  - `test: ...`
  - `chore: ...`

## Code style

- Python style is enforced with `black`.
- Keep keyword API changes explicit and backward-compatible when possible.
- Add or update tests with every behavior change.
- Prefer small, reviewable pull requests.

## Running checks locally

Run lint and unit tests before opening a PR:

```bash
black --check .
pytest tests/unit
```

Acceptance tests (headless, CI-like):

```bash
robot --pythonpath src -v HEADLESS:True -d reports/acceptance tests/acceptance
```

Run acceptance tests with visible browser:

```bash
robot --pythonpath src -v HEADLESS:False -d reports/acceptance tests/acceptance
```

Smoke-only acceptance run:

```bash
robot --pythonpath src -v HEADLESS:True -i smoke -d reports/acceptance tests/acceptance
```

## Submitting Changes

- **Team members**: push directly to `Jhoan0714/robotframework-vibium` using a feature branch (do not push directly to `main`).
- **External contributors**: fork the repository, push to your fork, then open a PR to `Jhoan0714/robotframework-vibium`.

## Pull requests

Please include:

- What changed and why.
- How you tested it (commands, output, or screenshots when relevant).
- Any backward-compatibility impact.
- Documentation updates when behavior or keywords changed.

CI runs on pull requests and currently validates formatting and unit tests.

## Security reports

Please do not open public issues for vulnerabilities.
Use GitHub Security Advisories for private reporting:

- https://github.com/Jhoan0714/robotframework-vibium/security/advisories/new