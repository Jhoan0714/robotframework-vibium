import json
from types import SimpleNamespace

import pytest

from rfvibium.errors import LocatorSyntaxError, VibiumLibraryError
from rfvibium.keywords.waits import WaitKeywords


class DummyElement:
    def __init__(self) -> None:
        self.wait_until_calls: list = []

    def wait_until(self, state=None, timeout=None) -> None:
        self.wait_until_calls.append((state, timeout))


class DummyPage:
    def __init__(self) -> None:
        self.wait_for_function_calls: list = []
        self.wait_for_url_calls: list = []
        self.wait_for_load_calls: list = []
        self.wait_calls: list = []
        self.element = DummyElement()
        self.last_find_args = None
        self.last_find_kwargs = None

    def wait_for_function(self, fn, timeout=None) -> None:
        self.wait_for_function_calls.append((fn, timeout))

    def wait_for_url(self, pattern, timeout=None) -> None:
        self.wait_for_url_calls.append((pattern, timeout))

    def wait_for_load(self, state=None, timeout=None) -> None:
        self.wait_for_load_calls.append((state, timeout))

    def find(self, *args, **kwargs):
        self.last_find_args = args
        self.last_find_kwargs = kwargs
        return self.element

    def wait(self, ms: int) -> None:
        self.wait_calls.append(ms)


class DummySession:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def require_page(self) -> DummyPage:
        return self._page


class TestableWait(WaitKeywords):
    def __init__(self, page: DummyPage) -> None:
        self.library = SimpleNamespace(_session=DummySession(page))


def test_wait_for_text_escapes_special_characters() -> None:
    page = DummyPage()
    kw = TestableWait(page)
    text = "line1\nline2 path\\to año"

    kw.wait_for_text(text, timeout="1s")

    fn, timeout_ms = page.wait_for_function_calls[0]
    assert json.dumps(text) in fn
    assert fn.startswith("() => document.body && document.body.innerText.includes(")
    assert timeout_ms == 1000


def test_wait_for_element_resolves_and_waits() -> None:
    page = DummyPage()
    kw = TestableWait(page)

    kw.wait_for_element("css:#box", state="attached", timeout="2s")

    assert page.last_find_args == ("#box",)
    assert page.element.wait_until_calls == [("attached", 2000)]


def test_wait_for_element_rejects_invalid_state() -> None:
    kw = TestableWait(DummyPage())
    with pytest.raises(LocatorSyntaxError, match="state must be one of"):
        kw.wait_for_element("css:#x", state="gone", timeout="1s")


def test_wait_for_url_delegates() -> None:
    page = DummyPage()
    kw = TestableWait(page)

    kw.wait_for_url("/ok", timeout="500ms")

    assert page.wait_for_url_calls == [("/ok", 500)]


def test_wait_for_function_delegates() -> None:
    page = DummyPage()
    kw = TestableWait(page)

    kw.wait_for_function("() => true", timeout="1s")

    assert page.wait_for_function_calls == [("() => true", 1000)]


def test_wait_for_function_rejects_empty_expression() -> None:
    kw = TestableWait(DummyPage())
    with pytest.raises(LocatorSyntaxError, match="expression cannot be empty"):
        kw.wait_for_function("   ")


def test_wait_for_load_state_passes_through_to_wait_for_load() -> None:
    page = DummyPage()
    kw = TestableWait(page)

    kw.wait_for_load_state()

    assert page.wait_for_load_calls == [("loading", 10_000)]

    kw.wait_for_load_state("complete", timeout="3s")

    assert page.wait_for_load_calls == [("loading", 10_000), ("complete", 3000)]


def test_sleep_milliseconds() -> None:
    page = DummyPage()
    kw = TestableWait(page)

    kw.sleep_milliseconds("100")

    assert page.wait_calls == [100]


def test_sleep_milliseconds_rejects_over_max() -> None:
    kw = TestableWait(DummyPage())
    with pytest.raises(VibiumLibraryError, match="exceeds maximum"):
        kw.sleep_milliseconds(30_001)
