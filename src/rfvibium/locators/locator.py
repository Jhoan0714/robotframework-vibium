"""Locator parsing and merging for Vibium's ``Page.find`` API.

Design overview:

- Each target is a single string using the ``strategy:value`` syntax, e.g.
  ``role:button`` or ``xpath://div[@id='x']``. A positional string without a
  known prefix is treated as a CSS selector (Vibium's default), consistent
  with ``Page.find(selector)``. The explicit ``css:`` prefix is accepted as
  a safer alias for ID-based selectors (``css:#foo``), because a bare
  ``#foo`` would be parsed by Robot Framework as a comment.
- The ``:`` separator is split on the first occurrence only so values may
  contain ``=``, ``[``, ``]`` or extra ``:`` characters (essential for XPath).
- Multi-axis queries such as ``role=button + text="Log in"`` are expressed by passing
  several ``strategy:value`` targets as separate Robot Framework arguments.
  The merge step combines them into a single ``page.find(...)`` call.

The ``:`` prefix is preferred over ``=`` deliberately: using ``=`` collides
with Robot Framework's native named-argument syntax, as documented by
SeleniumLibrary. The ``:`` form is unambiguous and safe.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from vibium import Element

from ..errors import LocatorSyntaxError
from ..types import FindScope, Locator

SEMANTIC_PREFIXES = (
    "xpath",
    "role",
    "text",
    "label",
    "placeholder",
    "testid",
    "alt",
    "title",
    "near",
)

CSS_PREFIX = "css"

SUPPORTED_PREFIXES = (CSS_PREFIX, *SEMANTIC_PREFIXES)


def parse_locator(target: str) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Return ``(args, kwargs)`` to forward into ``page.find``.

    - ``role:button`` → ``((), {"role": "button"})``
    - ``input[name='q']`` → ``(("input[name='q']",), {})``
    - ``css:#listing`` → ``(("#listing",), {})``
    - ``xpath://div[@id='x']`` → ``((), {"xpath": "//div[@id='x']"})``

    The explicit ``css:`` prefix is semantically identical to omitting any
    prefix, but it is the recommended form whenever the selector starts
    with ``#`` (ID selector): Robot Framework would otherwise treat the
    leading ``#`` of the cell as the start of a comment.
    """
    _guard_type(target)

    stripped = target.strip()
    if not stripped:
        raise LocatorSyntaxError("Locator cannot be empty.")

    _guard_stringified_sequence(stripped)

    for prefix in SUPPORTED_PREFIXES:
        marker = f"{prefix}:"
        if stripped.startswith(marker):
            value = stripped[len(marker) :]
            if not value:
                raise LocatorSyntaxError(
                    f"Locator prefix '{prefix}:' requires a non-empty value."
                )
            _guard_collapsed_prefixes(stripped, value)
            if prefix == CSS_PREFIX:
                return (value,), {}
            return (), {prefix: value}

    return (stripped,), {}


def _guard_type(target: Any) -> None:
    """Reject non-string locators with an actionable message.

    The common trigger is calling ``Click    ${VAR}`` where ``VAR``
    was defined as ``@{VAR}`` in the Variables section. Robot Framework then
    passes a Python ``list`` instead of a string.
    """
    if isinstance(target, str):
        return

    if isinstance(target, (list, tuple)):
        raise LocatorSyntaxError(
            "Locator received as a Python "
            f"{type(target).__name__} instead of a string: {target!r}. "
            "In Robot Framework this usually means a list variable was "
            "accessed with '${VAR}' instead of '@{VAR}'. Use '@{VAR}' at "
            "the call site to expand the list into separate arguments:\n"
            "    @{LOCATOR}    strategy:value    strategy:value\n"
            "    Click    @{LOCATOR}"
        )

    raise LocatorSyntaxError(f"Locator must be a string, got {type(target).__name__}.")


_STRINGIFIED_SEQUENCE_OPENERS = ("['", '["', "('", '("')


def _guard_stringified_sequence(candidate: str) -> None:
    """Reject strings that look like a stringified Python ``list``/``tuple``.

    Robot Framework applies type conversion based on annotations, so a list
    variable passed as a scalar (``${VAR}`` instead of ``@{VAR}``) to a
    keyword declared as ``*locators: str`` arrives already converted via
    ``str(list)``. We detect that shape so the user sees the same actionable
    hint they would get if the list reached the library untyped.
    """
    if not candidate.startswith(_STRINGIFIED_SEQUENCE_OPENERS):
        return
    closer = "]" if candidate.startswith("[") else ")"
    if not candidate.endswith(closer):
        return

    container = "list" if closer == "]" else "tuple"
    raise LocatorSyntaxError(
        f"Locator looks like a stringified Python {container}: {candidate}. "
        "This usually happens when a list variable is accessed with "
        "'${VAR}' instead of '@{VAR}'. Robot Framework then converts the "
        "list to its string representation before passing it to the keyword. "
        "Expand the variable at the call site:\n"
        "    @{LOCATOR}    strategy:value    strategy:value\n"
        "    Click    @{LOCATOR}"
    )


def _guard_collapsed_prefixes(full: str, value: str) -> None:
    """Reject locators that look like two filters collapsed into one string.

    The common trigger is defining ``${VAR}    role:button    text:Login`` in
    the Variables section. Robot Framework joins multi-value scalars with a
    single space, so the library then receives the single string
    ``"role:button text:Login"`` instead of two separate arguments.
    """
    for prefix in SUPPORTED_PREFIXES:
        marker = f" {prefix}:"
        if marker in value:
            raise LocatorSyntaxError(
                f"Locator '{full}' looks like multiple filters collapsed "
                f"into a single string (detected ' {prefix}:' inside the value). "
                "This usually happens when a scalar '${VAR}' is defined in "
                "Variables with multiple values: Robot Framework joins them "
                "with a space. Use a list variable and expand it with '@{VAR}':\n"
                "    @{LOCATOR}    strategy:value    strategy:value\n"
                "    Click    @{LOCATOR}"
            )


def looks_like_locator(candidate: str) -> bool:
    """Return True if ``candidate`` starts with a known ``strategy:`` prefix.

    Used by keywords that need to disambiguate between a locator and a value
    when both can appear as positional arguments (e.g. ``Fill Text``).
    """
    if not isinstance(candidate, str):
        return False
    stripped = candidate.strip()
    return any(stripped.startswith(f"{prefix}:") for prefix in SUPPORTED_PREFIXES)


def merge_locators(
    targets: Iterable[str],
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Merge several ``strategy:value`` strings into a single ``find`` call.

    Rules:
    - At most one CSS-selector positional (Vibium only accepts one).
    - Each semantic axis (``role``, ``text``, ``xpath``, ...) appears at
      most once. Duplicates raise :class:`~.errors.LocatorSyntaxError`.
    - Empty iterable raises :class:`~.errors.LocatorSyntaxError`.
    """
    merged_args: tuple[Any, ...] = ()
    merged_kwargs: dict[str, Any] = {}
    count = 0

    for target in targets:
        count += 1
        args, kwargs = parse_locator(target)

        if args:
            if merged_args:
                raise LocatorSyntaxError(
                    "Multiple CSS selectors provided; Vibium accepts only one "
                    "positional selector per find() call."
                )
            merged_args = args

        for key, value in kwargs.items():
            if key in merged_kwargs:
                raise LocatorSyntaxError(
                    f"Duplicate locator filter '{key}' (got '{merged_kwargs[key]}' "
                    f"and '{value}')."
                )
            merged_kwargs[key] = value

    if count == 0:
        raise LocatorSyntaxError("At least one locator is required.")

    return merged_args, merged_kwargs


def resolve_required_locators(
    targets: Iterable[str],
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Resolve one-or-more locator tokens for ``page.find`` calls.

    This is the shared helper for keyword modules. It keeps the user-facing
    "missing locator" message consistent across interaction and assertion
    keywords.
    """
    target_list = tuple(targets)
    if not target_list:
        raise LocatorSyntaxError(
            "At least one locator is required "
            "(e.g. 'role:button', 'xpath://div[@id=\"x\"]', or 'input[name=\"q\"]')."
        )
    return merge_locators(target_list)


def is_element_handle(obj: Any) -> bool:
    """Return True if ``obj`` is a Vibium sync ``Element`` handle."""
    return isinstance(obj, Element)


def resolve_element(
    session: Any, *targets: Locator, scope: FindScope = None, timeout: int | None = None
) -> Element:
    """Resolve an action/getter target to a Vibium ``Element``.

    Supported shapes:

    - One element handle alone → return it (no second ``find``).
    - One or more locator strings → ``session.resolve_scope(scope).find(...)``.

    When ``timeout`` is set (milliseconds), it is forwarded to ``find(...)``.
    With a sole element handle there is no ``find``; callers may still apply
    ``timeout`` to the subsequent action.

    Raises:
        LocatorSyntaxError: If no target is given, an element handle is mixed
            with locator tokens, or ``scope=`` is set together with a handle.
    """
    target_list = tuple(targets)
    if not target_list:
        raise LocatorSyntaxError(
            "At least one locator or element handle is required "
            "(e.g. 'role:button', 'css:#save', or an element from Find Element)."
        )

    if len(target_list) == 1 and is_element_handle(target_list[0]):
        if scope is not None:
            raise LocatorSyntaxError(
                "When the target is an element handle, do not pass scope=. "
                "Pass the handle alone to act on it, or use locator tokens "
                "with scope= for nested find."
            )
        return target_list[0]

    for target in target_list:
        if is_element_handle(target):
            raise LocatorSyntaxError(
                "Do not mix an element handle with locator tokens. "
                "Pass the handle alone, or pass only locator strings."
            )

    page = session.resolve_scope(scope)
    args, kwargs = resolve_required_locators(target_list)
    if timeout is not None:
        kwargs = {**kwargs, "timeout": timeout}
    return page.find(*args, **kwargs)


def format_locators(targets: Iterable[Any]) -> str:
    """Return a compact, human-readable string for locator tokens."""
    return " ".join(str(token).strip() for token in targets)
