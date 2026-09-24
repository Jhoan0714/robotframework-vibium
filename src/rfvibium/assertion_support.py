"""AssertionEngine helpers for getter keywords.

Design (issue #18):

- Prefer explicit ``assertion_operator=`` / ``assertion_expected=`` kwargs.
- Otherwise peel from the end of positional ``*locators``: if the penultimate
  token is an assertion operator, treat ``(op, expected)`` as the assertion and
  the preceding tokens as locators / element handle.
- ``scope=``, ``timeout=``, and ``message=`` stay keyword-only and never enter
  the peel.
"""

from __future__ import annotations

from typing import Any

from assertionengine import AssertionOperator, list_verify_assertion, verify_assertion

# Robot-friendly aliases (values + names + Browser-style spellings).
_OPERATOR_ALIASES: dict[str, AssertionOperator] = {}
for _member in AssertionOperator:
    _OPERATOR_ALIASES[_member.value] = _member
    _OPERATOR_ALIASES[_member.name] = _member
    _OPERATOR_ALIASES[_member.name.replace(" ", "_")] = _member

for _alias, _name in (
    ("equal", "equal"),
    ("equals", "equal"),
    ("should be", "equal"),
    ("inequal", "inequal"),
    ("should not be", "inequal"),
    ("contains", "contains"),
    ("not contains", "not contains"),
    ("starts", "starts"),
    ("ends", "ends"),
    ("matches", "matches"),
    ("evaluate", "then"),
    ("then", "then"),
    ("validate", "validate"),
):
    for _member in AssertionOperator:
        if _member.name == _name:
            _OPERATOR_ALIASES[_alias] = _member
            break


def parse_assertion_operator(token: Any) -> AssertionOperator | None:
    """Return an ``AssertionOperator`` if ``token`` names one, else ``None``."""
    if isinstance(token, AssertionOperator):
        return token
    if not isinstance(token, str):
        return None
    return _OPERATOR_ALIASES.get(token.strip())


def split_locators_and_assertion(
    *raw: Any,
    assertion_operator: AssertionOperator | str | None = None,
    assertion_expected: Any = None,
) -> tuple[tuple[Any, ...], AssertionOperator | None, Any]:
    """Split positional args into ``(targets, operator, expected)``.

    Kwargs win: when either assertion kwarg is set, ``raw`` is left intact and
    no peel is performed. ``assertion_operator`` may be an enum or string.
    """
    if assertion_operator is not None or assertion_expected is not None:
        op = (
            parse_assertion_operator(assertion_operator)
            if not isinstance(assertion_operator, AssertionOperator)
            else assertion_operator
        )
        if assertion_operator is not None and op is None:
            raise ValueError(
                f"Unknown assertion_operator: {assertion_operator!r}. "
                "Use AssertionEngine operators such as ==, !=, contains, *=."
            )
        return raw, op, assertion_expected

    if len(raw) >= 2:
        op = parse_assertion_operator(raw[-2])
        if op is not None:
            return raw[:-2], op, raw[-1]

    return raw, None, None


def coerce_int_expected(expected: Any) -> Any:
    """Coerce Robot string/float counts to ``int`` for AssertionEngine 3.0.x.

    ``int_str_verify_assertion`` exists only in AssertionEngine ≥5 (Python ≥3.10).
    This keeps ``Count Elements … == ${2}`` / ``== 2`` working on 3.9 + AE 3.0.3.
    """
    if expected is None or isinstance(expected, bool):
        return expected
    if isinstance(expected, int):
        return expected
    if isinstance(expected, float) and expected.is_integer():
        return int(expected)
    if isinstance(expected, str):
        stripped = expected.strip()
        try:
            return int(stripped)
        except ValueError:
            try:
                as_float = float(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"Expected count must be an integer, got {expected!r}."
                ) from exc
            if as_float.is_integer():
                return int(as_float)
            raise ValueError(
                f"Expected count must be an integer, got {expected!r}."
            ) from None
    return expected


def assert_value(
    value: Any,
    operator: AssertionOperator | str | None,
    expected: Any,
    prefix: str,
    message: str | None = None,
) -> Any:
    """Run ``verify_assertion`` when ``operator`` is set; otherwise return ``value``."""
    if operator is None:
        return value
    if not isinstance(operator, AssertionOperator):
        parsed = parse_assertion_operator(operator)
        if parsed is None:
            raise ValueError(
                f"Unknown assertion_operator: {operator!r}. "
                "Use AssertionEngine operators such as ==, !=, contains, *=."
            )
        operator = parsed
    return verify_assertion(value, operator, expected, prefix, message)


def assert_list(
    value: list,
    operator: AssertionOperator | str | None,
    expected: Any,
    prefix: str,
    message: str | None = None,
) -> list:
    """List assertion helper for ``Get Element States``."""
    if operator is None:
        return value
    if not isinstance(operator, AssertionOperator):
        parsed = parse_assertion_operator(operator)
        if parsed is None:
            raise ValueError(
                f"Unknown assertion_operator: {operator!r}. "
                "Use AssertionEngine operators such as ==, !=, contains, *=."
            )
        operator = parsed
    expected_list = expected if isinstance(expected, list) else [expected]
    return list_verify_assertion(value, operator, expected_list, prefix, message or "")
