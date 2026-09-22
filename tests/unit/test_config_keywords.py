"""Unit tests for Set Browser Timeout / optional_timeout_ms library fallback."""

from types import SimpleNamespace

import pytest

from rfvibium.errors import VibiumLibraryError
from rfvibium.keywords.config import ConfigKeywords
from rfvibium.settings_stack import Scope, SettingsStack
from rfvibium.utils import optional_timeout_ms, timeout_ms_to_timestr


class TestableConfig(ConfigKeywords):
    def __init__(self) -> None:
        self.library = SimpleNamespace(timeout_stack=SettingsStack())


def test_optional_timeout_ms_explicit_wins_over_library() -> None:
    lib = SimpleNamespace(timeout_stack=SettingsStack())
    lib.timeout_stack.set(60_000, Scope.Global)
    assert optional_timeout_ms("500ms", library=lib) == 500


def test_optional_timeout_ms_falls_back_to_library_stack() -> None:
    lib = SimpleNamespace(timeout_stack=SettingsStack())
    lib.timeout_stack.set(2500, Scope.Global)
    assert optional_timeout_ms(None, library=lib) == 2500
    assert optional_timeout_ms("", library=lib) == 2500


def test_optional_timeout_ms_none_without_library() -> None:
    assert optional_timeout_ms(None) is None
    assert optional_timeout_ms("") is None


def test_timeout_ms_to_timestr() -> None:
    assert timeout_ms_to_timestr(None) == "None"
    assert timeout_ms_to_timestr(500) == "500 milliseconds"
    assert timeout_ms_to_timestr(5000) == "5 seconds"


def test_set_browser_timeout_returns_previous_and_sets() -> None:
    kw = TestableConfig()
    kw.library.timeout_stack.start_suite("s1")

    old = kw.set_browser_timeout("2s", scope="Suite")
    assert old == "None"
    assert kw.library.timeout_stack.get() == 2000

    old2 = kw.set_browser_timeout("500ms", scope="Suite")
    assert old2 == "2 seconds"
    assert kw.library.timeout_stack.get() == 500


def test_set_browser_timeout_clears_with_none() -> None:
    kw = TestableConfig()
    kw.library.timeout_stack.start_suite("s1")
    kw.set_browser_timeout("1s")
    assert kw.set_browser_timeout("None") == "1 second"
    assert kw.library.timeout_stack.get() is None


def test_set_browser_timeout_test_scope_requires_running_test() -> None:
    kw = TestableConfig()
    kw.library.timeout_stack.start_suite("s1")
    with pytest.raises(VibiumLibraryError, match="while a test is running"):
        kw.set_browser_timeout("1s", scope="Test")
