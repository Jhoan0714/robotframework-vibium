# robotframework-vibium

[Robot Framework](https://robotframework.org) library based on
[Vibium](https://github.com/VibiumDev/vibium) for AI-native browser automation.

**Status:** early development (PyPI `0.x`, Alpha). The public keyword set may still evolve; pin versions in production suites if you need stability.

## Vision

`robotframework-vibium` brings Vibium's modern browser interaction model into Robot Framework through clean, composable, and maintainable keywords.

## Documentation

Use this README as a quick guide and examples, and Libdoc as the source of truth
for the complete API.

See [keyword documentation](https://jhoan0714.github.io/robotframework-vibium/VibiumLibrary.html) for more details.

## Installation

```bash
pip install robotframework-vibium
```

## Compatibility

| Component | Supported Version |
| --- | --- |
| Python | `>=3.9` |
| Robot Framework | `>=5.0` |
| Vibium | `>=26.8.21,<26.9` |

Although Robot Framework supports older Python versions, this library follows Vibium's runtime requirements and therefore requires Python 3.9 or newer.

## Quick Start

```robot
*** Settings ***
Library    Vibium

*** Test Cases ***
Basic Navigation
    Open Browser
    Go To    https://example.com
    ${text}=    Get Page Text
    Should Contain    ${text}    Example Domain
    Close Browser
```

## Locator Syntax

Targets passed to `Click`, `Fill Text` and `Find Element` use a
prefix-based contract that maps directly to Vibium's `Page.find(...)` API.
The `:` separator is preferred over `=` deliberately, following
SeleniumLibrary's guidance, because `=` collides with Robot Framework's
named-argument syntax.

### Single locator

Two forms:

1. **CSS selector (default, no prefix)** — forwarded as the positional
   `selector` argument of `page.find`. CSS is Vibium's default strategy.
2. **Semantic strategy (`strategy:value`)** — forwarded as the matching
   keyword argument. The prefix is split on the first `:` only, so values
   may contain `=`, `[`, `]` or extra `:` characters (essential for XPath).

Supported strategies: `xpath`, `role`, `text`, `label`, `placeholder`,
`testid`, `alt`, `title`, `near`.

```robot
*** Test Cases ***
Single Locator Examples
    Click    input[name='q']
    Click    role:button
    Click    text:Log in
    Click    xpath:(//*[@name='q'])[1]
    Click    xpath://input[@id='email' and @type='text']
```

### Combining multiple strategies

Every keyword accepts one or more locator tokens as separate Robot Framework
arguments. They are merged into a single `page.find(...)` call—the same idea as combining
role plus accessible name in richer browser automation APIs—and matches the
Vibium CLI pattern `vibium find role button --name "Log in"`.

Rules:

- At most one CSS-selector positional (Vibium accepts only one).
- Each semantic axis may appear at most once; duplicates raise an error.

```robot
*** Test Cases ***
Combined Locators
    Click    role:button    text:Log in
    Click    role:textbox   label:E-mail
    Click    .nav           role:link       text:Home
```

### Fill Text: value rules

`Fill Text` supports two modes:

1. **Ergonomic** — the last positional is the value.
2. **Explicit** — use `value=...` as a Robot Framework keyword argument.

To prevent silent foot-guns, the ergonomic mode raises an error when the
last positional *looks like a locator* (starts with a known `strategy:`
prefix). Use `value=...` to disambiguate.

```robot
*** Test Cases ***
Fill Examples
    # Ergonomic: value as last positional
    Fill Text    input#email                            user@example.com
    Fill Text    role:textbox    label:E-mail           user@example.com

    # Explicit: value= kwarg
    Fill Text    role:textbox                           value=user@example.com
    Fill Text    input#password                         value=secret

    # Required when the value itself looks like a locator
    Fill Text    input#comment                          value=role:admin

    # Clear a field
    Fill Text    input#search                           value=${EMPTY}
```

The following is rejected with a clear error (ambiguous last positional):

```robot
Fill Text    role:textbox    label:E-mail        # ERROR: looks like 2 locators, value missing
```

## Development

```bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

End-to-end checks with real browser (from repository root):

```bash
robot --pythonpath src -d reports/acceptance tests/acceptance
```

Smoke-only run:

```bash
robot --pythonpath src -i smoke -d reports/acceptance tests/acceptance
```

See [tests/acceptance/README.md](tests/acceptance/README.md) for suite coverage and details.

## Project Principles

- Stable and explicit public keyword API
- High-quality error messages for test users
- Clean separation between session management and keyword layers
- Fast feedback loop with unit + acceptance tests

## License

Apache-2.0
