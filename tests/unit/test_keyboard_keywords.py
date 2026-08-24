from types import SimpleNamespace

import pytest

from rfvibium.errors import VibiumLibraryError
from rfvibium.keywords.keyboard import KeyboardKeywords


class DummyKeyboard:
    def __init__(self) -> None:
        self.downs: list[str] = []
        self.ups: list[str] = []
        self.typed: list[str] = []
        self.pressed: list[str] = []

    def down(self, key: str) -> None:
        self.downs.append(key)

    def up(self, key: str) -> None:
        self.ups.append(key)

    def type(self, text: str) -> None:
        self.typed.append(text)

    def press(self, combo: str) -> None:
        self.pressed.append(combo)


class DummyPage:
    def __init__(self) -> None:
        self.keyboard = DummyKeyboard()


class DummySession:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def resolve_scope(self, scope=None):
        return self._page if scope is None else scope


class TestableKeyboard(KeyboardKeywords):
    def __init__(self, page: DummyPage) -> None:
        self.library = SimpleNamespace(_session=DummySession(page))


def test_keyboard_key_down_up_and_type() -> None:
    page = DummyPage()
    kw = TestableKeyboard(page)

    kw.keyboard_key("down", "Shift")
    kw.keyboard_type("Hi")
    kw.keyboard_key("up", "Shift")

    assert page.keyboard.downs == ["Shift"]
    assert page.keyboard.typed == ["Hi"]
    assert page.keyboard.ups == ["Shift"]


def test_keyboard_key_press_combo() -> None:
    page = DummyPage()
    kw = TestableKeyboard(page)

    kw.keyboard_key("press", "Control+a")

    assert page.keyboard.pressed == ["Control+a"]


def test_keyboard_key_action_is_case_insensitive() -> None:
    page = DummyPage()
    kw = TestableKeyboard(page)

    kw.keyboard_key("PRESS", "Enter")

    assert page.keyboard.pressed == ["Enter"]


def test_keyboard_key_rejects_unknown_action() -> None:
    kw = TestableKeyboard(DummyPage())
    with pytest.raises(VibiumLibraryError, match="action must be one of"):
        kw.keyboard_key("hold", "Shift")
