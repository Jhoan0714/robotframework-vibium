"""Unit tests for SettingsStack / Scope."""

import pytest

from rfvibium.errors import VibiumLibraryError
from rfvibium.settings_stack import Scope, SettingsStack, parse_scope


def test_parse_scope_accepts_aliases() -> None:
    assert parse_scope("Global") is Scope.Global
    assert parse_scope("suite") is Scope.Suite
    assert parse_scope("Test") is Scope.Test
    assert parse_scope("task") is Scope.Test


def test_parse_scope_rejects_invalid() -> None:
    with pytest.raises(VibiumLibraryError, match="Invalid scope"):
        parse_scope("case")


def test_stack_global_default_is_none() -> None:
    stack = SettingsStack()
    assert stack.get() is None


def test_stack_global_set_updates_all_frames() -> None:
    stack = SettingsStack()
    stack.start_suite("s1")
    stack.start_test("t1")
    stack.set(5000, Scope.Global)
    assert stack.get() == 5000
    stack.end_test("t1")
    assert stack.get() == 5000
    stack.end_suite("s1")
    assert stack.get() == 5000


def test_stack_suite_set_restores_on_end() -> None:
    stack = SettingsStack()
    stack.start_suite("s1")
    stack.set(2000, Scope.Suite)
    assert stack.get() == 2000
    stack.end_suite("s1")
    assert stack.get() is None


def test_stack_test_set_restores_on_end() -> None:
    stack = SettingsStack()
    stack.start_suite("s1")
    stack.set(10_000, Scope.Suite)
    stack.start_test("t1")
    stack.set(500, Scope.Test)
    assert stack.get() == 500
    stack.end_test("t1")
    assert stack.get() == 10_000
    stack.end_suite("s1")
    assert stack.get() is None


def test_stack_test_set_outside_test_raises() -> None:
    stack = SettingsStack()
    stack.start_suite("s1")
    with pytest.raises(VibiumLibraryError, match="while a test is running"):
        stack.set(1000, Scope.Test)
