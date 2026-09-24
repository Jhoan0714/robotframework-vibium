"""Unit tests for AssertionEngine peel + verify helpers."""

from __future__ import annotations

import pytest
from assertionengine import AssertionOperator

from rfvibium.assertions.assertion_support import (
    assert_list,
    assert_value,
    coerce_int_expected,
    parse_assertion_operator,
    split_locators_and_assertion,
)


def test_parse_operator_symbols_and_aliases() -> None:
    assert parse_assertion_operator("==") is AssertionOperator.equal
    assert parse_assertion_operator("contains") is AssertionOperator.contains
    assert parse_assertion_operator("*=") is AssertionOperator.contains
    assert parse_assertion_operator("not contains") is AssertionOperator["not contains"]
    assert parse_assertion_operator("css:h1") is None
    assert parse_assertion_operator(AssertionOperator.equal) is AssertionOperator.equal


def test_peel_operator_and_expected_from_end() -> None:
    targets, op, expected = split_locators_and_assertion("css:h1", "==", "Welcome")
    assert targets == ("css:h1",)
    assert op is AssertionOperator.equal
    assert expected == "Welcome"


def test_peel_with_multi_locator() -> None:
    targets, op, expected = split_locators_and_assertion(
        "role:button", "text:Save", "*=", "Save"
    )
    assert targets == ("role:button", "text:Save")
    assert op is AssertionOperator.contains
    assert expected == "Save"


def test_no_peel_without_operator() -> None:
    targets, op, expected = split_locators_and_assertion("css:h1", "Welcome")
    assert targets == ("css:h1", "Welcome")
    assert op is None
    assert expected is None


def test_kwargs_win_over_peel() -> None:
    targets, op, expected = split_locators_and_assertion(
        "css:h1",
        "==",
        "ignored",
        assertion_operator=AssertionOperator.contains,
        assertion_expected="Wanted",
    )
    assert targets == ("css:h1", "==", "ignored")
    assert op is AssertionOperator.contains
    assert expected == "Wanted"


def test_kwargs_string_operator() -> None:
    targets, op, expected = split_locators_and_assertion(
        "css:h1",
        assertion_operator="==",
        assertion_expected="Welcome",
    )
    assert targets == ("css:h1",)
    assert op is AssertionOperator.equal
    assert expected == "Welcome"


def test_unknown_kwarg_operator_raises() -> None:
    with pytest.raises(ValueError, match="Unknown assertion_operator"):
        split_locators_and_assertion(
            "css:h1",
            assertion_operator="not-an-op",
            assertion_expected="x",
        )


def test_assert_value_pass_and_fail() -> None:
    assert (
        assert_value("Welcome", AssertionOperator.equal, "Welcome", "Text") == "Welcome"
    )
    with pytest.raises(AssertionError):
        assert_value("Bye", AssertionOperator.equal, "Welcome", "Text")


def test_assert_list_equal() -> None:
    states = ["visible", "enabled"]
    assert assert_list(states, None, None, "Element states") == states
    assert (
        assert_list(
            states, AssertionOperator.equal, ["visible", "enabled"], "Element states"
        )
        == states
    )


def test_coerce_int_expected() -> None:
    assert coerce_int_expected(2) == 2
    assert coerce_int_expected("3") == 3
    assert coerce_int_expected("4.0") == 4
    assert coerce_int_expected(5.0) == 5
    with pytest.raises(ValueError, match="integer"):
        coerce_int_expected("x")
    with pytest.raises(ValueError, match="integer"):
        coerce_int_expected("1.5")
