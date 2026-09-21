from types import SimpleNamespace

import pytest

from rfvibium.errors import VibiumLibraryError
from rfvibium.keywords.touch import TouchKeywords


class DummyTouch:
    def __init__(self) -> None:
        self.taps: list[tuple[float, float]] = []

    def tap(self, x: float, y: float) -> None:
        self.taps.append((x, y))


class DummyPage:
    def __init__(self) -> None:
        self.touch = DummyTouch()


class DummySession:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def require_page(self) -> DummyPage:
        return self._page


class TestableTouch(TouchKeywords):
    def __init__(self, page: DummyPage) -> None:
        self.library = SimpleNamespace(_session=DummySession(page))


def test_touch_tap_invokes_page_touch() -> None:
    page = DummyPage()
    kw = TestableTouch(page)

    kw.touch_tap(10, 20)

    assert page.touch.taps == [(10.0, 20.0)]


def test_touch_tap_accepts_string_coordinates() -> None:
    page = DummyPage()
    kw = TestableTouch(page)

    kw.touch_tap("1.5", "2")

    assert page.touch.taps == [(1.5, 2.0)]


def test_touch_tap_requires_coordinates() -> None:
    kw = TestableTouch(DummyPage())
    with pytest.raises(VibiumLibraryError, match="Touch x must be a number"):
        kw.touch_tap()


def test_touch_tap_requires_both_axes() -> None:
    kw = TestableTouch(DummyPage())
    with pytest.raises(VibiumLibraryError, match="Touch y must be a number"):
        kw.touch_tap(1, None)


def test_touch_tap_rejects_empty_string() -> None:
    kw = TestableTouch(DummyPage())
    with pytest.raises(VibiumLibraryError, match="empty string"):
        kw.touch_tap(" ", 1)
