import pytest

from rfvibium.errors import LocatorSyntaxError, VibiumLibraryError
from rfvibium.keywords.waits import WaitKeywords


class DummyWaitUntil:
    def __init__(self) -> None:
        self.fn_calls: list = []
        self.url_calls: list = []
        self.loaded_calls: list = []

    def __call__(self, fn, timeout=None) -> None:
        self.fn_calls.append((fn, timeout))

    def url(self, pattern, timeout=None) -> None:
        self.url_calls.append((pattern, timeout))

    def loaded(self, state=None, timeout=None) -> None:
        self.loaded_calls.append((state, timeout))


class DummyElement:
    def __init__(self) -> None:
        self.wait_until_calls: list = []

    def wait_until(self, state=None, timeout=None) -> None:
        self.wait_until_calls.append((state, timeout))


class DummyPage:
    def __init__(self) -> None:
        self.wait_until = DummyWaitUntil()
        self.wait_calls: list = []
        self.element = DummyElement()
        self.last_find_args = None
        self.last_find_kwargs = None

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
        self._session = DummySession(page)


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

    assert page.wait_until.url_calls == [("/ok", 500)]


def test_wait_for_function_delegates() -> None:
    page = DummyPage()
    kw = TestableWait(page)

    kw.wait_for_function("() => true", timeout="1s")

    assert page.wait_until.fn_calls == [("() => true", 1000)]


def test_wait_for_function_rejects_empty_expression() -> None:
    kw = TestableWait(DummyPage())
    with pytest.raises(LocatorSyntaxError, match="expression cannot be empty"):
        kw.wait_for_function("   ")


def test_wait_for_load_state_passes_through_to_loaded() -> None:
    page = DummyPage()
    kw = TestableWait(page)

    kw.wait_for_load_state()

    assert page.wait_until.loaded_calls == [("loading", 10_000)]

    kw.wait_for_load_state("complete", timeout="3s")

    assert page.wait_until.loaded_calls == [("loading", 10_000), ("complete", 3000)]


def test_sleep_milliseconds() -> None:
    page = DummyPage()
    kw = TestableWait(page)

    kw.sleep_milliseconds("100")

    assert page.wait_calls == [100]


def test_sleep_milliseconds_rejects_over_max() -> None:
    kw = TestableWait(DummyPage())
    with pytest.raises(VibiumLibraryError, match="exceeds maximum"):
        kw.sleep_milliseconds(30_001)
