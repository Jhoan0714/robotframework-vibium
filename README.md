# robotframework-vibium

[![PyPI version](https://img.shields.io/pypi/v/robotframework-vibium.svg?logo=pypi&logoColor=white)](https://pypi.org/project/robotframework-vibium/)
[![Continuous integration](https://github.com/Jhoan0714/robotframework-vibium/actions/workflows/on-pull.yml/badge.svg)](https://github.com/Jhoan0714/robotframework-vibium/actions/workflows/on-pull.yml)

[Robot Framework](https://robotframework.org) library based on
[Vibium](https://github.com/VibiumDev/vibium) for AI-native browser automation.

## Vision

`robotframework-vibium` brings Vibium's modern browser interaction model into Robot Framework through clean, composable, and maintainable keywords.

## Keyword Documentation

See [keyword documentation](https://jhoan0714.github.io/robotframework-vibium/VibiumLibrary.html) for available keywords and more information about the library in general.

This README is a quick guide; Libdoc is the source of truth for the full API.

## Installation

The recommended installation method is using pip:

```bash
pip install --upgrade robotframework-vibium
```

The `--upgrade` option can be omitted when installing for the first time.
This installs the library and its dependencies (including Robot Framework and
Vibium).

To install from the GitHub repository (latest `main`):

```bash
pip install git+https://github.com/Jhoan0714/robotframework-vibium.git
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

`Open Browser` accepts optional launch arguments aligned with Vibium
``browser.start()``: ``url=`` (remote BiDi WebSocket), ``engine=`` (`chrome` or
`firefox`), ``channel=`` (`release` or `beta`, Firefox only), ``headless=`` (per
browser; defaults to the library import ``headless=${TRUE/FALSE}``), and
``headers=`` (HTTP headers for remote connect). When ``engine`` is omitted,
Chrome is used unless ``VIBIUM_ENGINE`` is set. Without ``url=``, Vibium may
still connect via the ``VIBIUM_CONNECT_URL`` environment variable.

## Locator Syntax

Locators use `strategy:value` (for example `role:button` or `css:#login`) and
pass through to Vibium's `Page.find(...)`. Use `:` rather than `=`, because `=`
is Robot Framework's named-argument syntax and would not be treated as part of
the locator.

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

### Shadow DOM pierce (`>>` / `>>>`)

To reach elements inside an *open* shadow root, use a pierce combinator in the
locator string (same keywords as usual—no dedicated pierce keyword). Plain CSS
without `>>` / `>>>` does not enter shadow trees.

| Combinator | Meaning |
| --- | --- |
| `>>` | Cross **one** shadow boundary |
| `>>>` | Cross **any depth** of nested open shadows |

Prefer `>>` for one hop under a known host; `>>>` when shadows nest. Combinators
chain (`host >> nested >> target`). CSS child `>` is not pierce.

```robot
*** Test Cases ***
Pierce Examples
    Get Text    my-card >> #shadow-text
    Click       my-card >> #shadow-btn
    Get Text    outer-host >>> #deep
    Get Text    outer-host >> inner-host >> #deep
```

Closed shadow roots are never entered. Nested find with `scope=${element}` is
separate from pierce. See Libdoc and
[Vibium selectors](https://github.com/VibiumDev/vibium/blob/main/docs/reference/selectors.md).

### Ergonomic value argument

`Fill Text`, `Type Text`, and `Select Option` accept a trailing value in two
ways:

1. **Ergonomic** — the last positional is the value / text / option.
2. **Explicit** — pass it as a named argument (`value=` or `text=` for
   `Type Text`).

Ergonomic mode raises an error when the last positional *looks like a locator*
(starts with a known `strategy:` prefix). Use the named form to disambiguate.

```robot
*** Test Cases ***
Ergonomic Value Examples
    # Ergonomic: value as last positional
    Fill Text       input#email                   user@example.com
    Fill Text       role:textbox    label:E-mail  user@example.com
    Type Text       css:#notes                    more text
    Select Option   css:#country                  US

    # Explicit named args
    Fill Text       role:textbox                  value=user@example.com
    Type Text       css:#notes                    text=more text
    Select Option   css:#country                  value=US

    # Required when the value itself looks like a locator
    Fill Text       input#comment                 value=role:admin

    # Clear a field
    Fill Text       input#search                  value=${EMPTY}
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

The library scope is `GLOBAL` (one instance per Robot process).
[Pabot](https://pabot.org/) works with process isolation—each worker gets its
own browser session pool. Details:
[#26](https://github.com/Jhoan0714/robotframework-vibium/issues/26).

## License

Apache-2.0
