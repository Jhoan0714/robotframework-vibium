from types import SimpleNamespace

import pytest

from rfvibium.errors import VibiumLibraryError
from rfvibium.keywords.emulation import EmulationKeywords


class DummyPage:
    def __init__(self) -> None:
        self.viewport_calls: list[dict[str, int]] = []
        self.window_calls: list[dict[str, int]] = []
        self._viewport = {"width": 800, "height": 600}
        self._window = {"width": 1280, "height": 800, "x": 0, "y": 0}

    def set_viewport(self, size: dict[str, int]) -> None:
        self.viewport_calls.append(dict(size))
        self._viewport = dict(size)

    def viewport(self) -> dict[str, int]:
        return dict(self._viewport)

    def set_window(self, **options: object) -> None:
        self.window_calls.append(dict(options))
        self._window.update(options)

    def window(self) -> dict[str, int]:
        return dict(self._window)


class DummySession:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def require_page(self) -> DummyPage:
        return self._page


class TestableEmulation(EmulationKeywords):
    def __init__(self, page: DummyPage) -> None:
        self.library = SimpleNamespace(_session=DummySession(page))


def test_set_viewport_size() -> None:
    page = DummyPage()
    kw = TestableEmulation(page)

    kw.set_viewport_size(1280, 720)

    assert page.viewport_calls == [{"width": 1280, "height": 720}]


def test_set_viewport_size_accepts_string_dimensions() -> None:
    page = DummyPage()
    kw = TestableEmulation(page)

    kw.set_viewport_size("1024", "768")

    assert page.viewport_calls == [{"width": 1024, "height": 768}]


def test_set_viewport_size_rejects_non_integer() -> None:
    kw = TestableEmulation(DummyPage())
    with pytest.raises(VibiumLibraryError, match="must be an integer"):
        kw.set_viewport_size("abc", 100)


def test_get_viewport_size() -> None:
    page = DummyPage()
    kw = TestableEmulation(page)

    assert kw.get_viewport_size() == {"width": 800, "height": 600}


def test_set_window_size_and_position() -> None:
    page = DummyPage()
    kw = TestableEmulation(page)

    kw.set_window(width=1280, height=800, x=10, y=20)

    assert page.window_calls == [{"width": 1280, "height": 800, "x": 10, "y": 20}]


def test_set_window_accepts_string_values() -> None:
    page = DummyPage()
    kw = TestableEmulation(page)

    kw.set_window(width="1024", height="768")

    assert page.window_calls == [{"width": 1024, "height": 768}]


def test_set_window_passes_state_through() -> None:
    page = DummyPage()
    kw = TestableEmulation(page)

    kw.set_window(state="maximized")

    assert page.window_calls == [{"state": "maximized"}]


def test_set_window_requires_at_least_one_option() -> None:
    kw = TestableEmulation(DummyPage())
    with pytest.raises(VibiumLibraryError, match="at least one"):
        kw.set_window()


def test_get_window_info() -> None:
    page = DummyPage()
    kw = TestableEmulation(page)

    assert kw.get_window_info() == {"width": 1280, "height": 800, "x": 0, "y": 0}
