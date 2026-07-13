from types import SimpleNamespace

import pytest

from rfvibium.errors import VibiumLibraryError
from rfvibium.keywords.mouse import MouseKeywords


class DummyMouse:
    def __init__(self) -> None:
        self.clicks: list[tuple[float, float]] = []
        self.moves: list[tuple[float, float]] = []
        self.down_count = 0
        self.up_count = 0

    def click(self, x: float, y: float) -> None:
        self.clicks.append((x, y))

    def move(self, x: float, y: float) -> None:
        self.moves.append((x, y))

    def down(self) -> None:
        self.down_count += 1

    def up(self) -> None:
        self.up_count += 1


class DummyPage:
    def __init__(self) -> None:
        self.mouse = DummyMouse()


class DummySession:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def require_page(self) -> DummyPage:
        return self._page


class TestableMouse(MouseKeywords):
    def __init__(self, page: DummyPage) -> None:
        self.library = SimpleNamespace(_session=DummySession(page))


def test_mouse_click_invokes_page_mouse() -> None:
    page = DummyPage()
    kw = TestableMouse(page)

    kw.mouse_click(10, 20)

    assert page.mouse.clicks == [(10.0, 20.0)]


def test_mouse_click_accepts_string_coordinates() -> None:
    page = DummyPage()
    kw = TestableMouse(page)

    kw.mouse_click("1.5", "2")

    assert page.mouse.clicks == [(1.5, 2.0)]


def test_mouse_click_requires_coordinates() -> None:
    kw = TestableMouse(DummyPage())
    with pytest.raises(VibiumLibraryError, match="Mouse x must be a number"):
        kw.mouse_click()


def test_mouse_click_requires_both_axes() -> None:
    kw = TestableMouse(DummyPage())
    with pytest.raises(VibiumLibraryError, match="Mouse y must be a number"):
        kw.mouse_click(1, None)


def test_mouse_click_rejects_nonzero_button() -> None:
    kw = TestableMouse(DummyPage())
    with pytest.raises(VibiumLibraryError, match="Non-default mouse buttons"):
        kw.mouse_click(1, 2, button=2)


def test_mouse_move_invokes_page_mouse() -> None:
    page = DummyPage()
    kw = TestableMouse(page)

    kw.mouse_move(3, 4)

    assert page.mouse.moves == [(3.0, 4.0)]


def test_mouse_down_and_up() -> None:
    page = DummyPage()
    kw = TestableMouse(page)

    kw.mouse_down()
    kw.mouse_up()

    assert page.mouse.down_count == 1
    assert page.mouse.up_count == 1


def test_mouse_down_rejects_non_default_button() -> None:
    kw = TestableMouse(DummyPage())
    with pytest.raises(VibiumLibraryError, match="not supported"):
        kw.mouse_down(button=1)
