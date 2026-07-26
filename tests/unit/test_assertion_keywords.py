"""Unit tests for ``Vibium.keywords.assertions`` (read-only page keywords)."""

from types import SimpleNamespace

import pytest

from rfvibium.errors import LocatorSyntaxError
from rfvibium.keywords.assertions import AssertionKeywords


class DummyWaitUntil:
    def __init__(self) -> None:
        self.loaded_calls = 0
        self.loaded_should_raise: Exception | None = None

    def loaded(self, state=None, timeout=None) -> None:
        self.loaded_calls += 1
        if self.loaded_should_raise is not None:
            raise self.loaded_should_raise


class DummyPage:
    def __init__(self, screenshot_responses) -> None:
        self._responses = list(screenshot_responses)
        self.screenshot_calls = 0
        self.last_screenshot_full_page = None
        self.last_screenshot_clip = None
        self.pdf_calls = 0
        self.wait_until = DummyWaitUntil()
        self.last_find_args = None
        self.last_find_kwargs = None
        self.last_find_all_args = None
        self.last_find_all_kwargs = None
        self.evaluate_calls = []
        self.find_element = _DummyElement("one", text="hello", html="<div>hello</div>")
        self.find_all_elements = [
            _DummyElement("e1"),
            _DummyElement("e2"),
            _DummyElement("e3"),
        ]
        self.content_value = "<html><body>doc</body></html>"
        self.a11y_value = {"tree": "ok"}

    def screenshot(self, full_page=None, clip=None) -> bytes:
        self.screenshot_calls += 1
        self.last_screenshot_full_page = full_page
        self.last_screenshot_clip = clip
        response = self._responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    def pdf(self) -> bytes:
        self.pdf_calls += 1
        return b"PDFDATA"

    def evaluate(self, expression: str):
        self.evaluate_calls.append(expression)
        if expression == "document.body ? document.body.innerText : ''":
            return "PAGE TEXT"
        if expression == "document.body ? document.body.innerHTML : ''":
            return "<main>INNER</main>"
        return {"expression": expression}

    def find(self, *args, **kwargs):
        self.last_find_args = args
        self.last_find_kwargs = kwargs
        return self.find_element

    def find_all(self, *args, **kwargs):
        self.last_find_all_args = args
        self.last_find_all_kwargs = kwargs
        return list(self.find_all_elements)

    def content(self) -> str:
        return self.content_value

    def a11y_tree(self, everything=False):
        return {"everything": everything, **self.a11y_value}

    def url(self) -> str:
        return "https://example.com/current"

    def title(self) -> str:
        return "Example Title"


class _DummyElement:
    def __init__(self, name: str, text: str = "", html: str = "") -> None:
        self.name = name
        self._text = text or f"text-{name}"
        self._html = html or f"<div>{name}</div>"
        self.element_screenshot_calls = 0

    def text(self) -> str:
        return self._text

    def html(self) -> str:
        return self._html

    def screenshot(self) -> bytes:
        self.element_screenshot_calls += 1
        return b"ELPNG"

    def __repr__(self) -> str:
        return f"Element(name='{self.name}')"


class DummySession:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def require_page(self) -> DummyPage:
        return self._page

    def resolve_scope(self, scope=None):
        return self._page if scope is None else scope


class TestableAssertions(AssertionKeywords):
    def __init__(self, page: DummyPage) -> None:
        self.library = SimpleNamespace(_session=DummySession(page))


# ---------------------------------------------------------------------------
# Reading content keywords
# ---------------------------------------------------------------------------


def test_get_html_page_outer_and_inner() -> None:
    page = DummyPage([b"PNGDATA"])
    kw = TestableAssertions(page)

    assert kw.get_html() == "<html><body>doc</body></html>"
    assert kw.get_html(outer=False) == "<main>INNER</main>"


def test_get_html_element_outer() -> None:
    page = DummyPage([b"PNGDATA"])
    kw = TestableAssertions(page)

    result = kw.get_html("xpath://div[@id='x']")

    assert result == "<div>hello</div>"
    assert page.last_find_kwargs == {"xpath": "//div[@id='x']"}


def test_get_html_element_inner_not_supported() -> None:
    page = DummyPage([b"PNGDATA"])
    kw = TestableAssertions(page)

    with pytest.raises(LocatorSyntaxError, match="outer=True"):
        kw.get_html("input#x", outer=False)


def test_find_elements_returns_repr_list_with_limit() -> None:
    page = DummyPage([b"PNGDATA"])
    kw = TestableAssertions(page)

    result = kw.find_elements("css:.row", limit=2)

    assert result == ["Element(name='e1')", "Element(name='e2')"]
    assert page.last_find_all_args == (".row",)
    assert page.last_find_all_kwargs == {}


def test_find_elements_rejects_invalid_limit() -> None:
    page = DummyPage([b"PNGDATA"])
    kw = TestableAssertions(page)

    with pytest.raises(LocatorSyntaxError, match="limit"):
        kw.find_elements("css:.row", limit=0)


def test_count_elements_uses_find_all_length() -> None:
    page = DummyPage([b"PNGDATA"])
    kw = TestableAssertions(page)

    assert kw.count_elements("role:listitem") == 3


def test_evaluate_javascript_returns_page_result() -> None:
    page = DummyPage([b"PNGDATA"])
    kw = TestableAssertions(page)

    result = kw.evaluate_javascript("1 + 1")

    assert result == {"expression": "1 + 1"}


def test_get_accessibility_tree_supports_everything_flag() -> None:
    page = DummyPage([b"PNGDATA"])
    kw = TestableAssertions(page)

    result = kw.get_accessibility_tree(everything=True)

    assert "'everything': True" in result


def test_assertion_keywords_use_explicit_scope_when_provided() -> None:
    active_page = DummyPage([b"PNGDATA"])
    scope_page = DummyPage([b"PNGDATA"])
    kw = TestableAssertions(active_page)

    assert kw.get_url(scope=scope_page) == "https://example.com/current"
    assert kw.get_title(scope=scope_page) == "Example Title"
    assert kw.get_page_text(scope=scope_page) == "PAGE TEXT"
    assert kw.get_html(scope=scope_page) == "<html><body>doc</body></html>"
    assert kw.find_elements("css:.row", scope=scope_page) == [
        "Element(name='e1')",
        "Element(name='e2')",
        "Element(name='e3')",
    ]
    assert kw.count_elements("css:.row", scope=scope_page) == 3
    assert kw.evaluate_javascript("2 + 2", scope=scope_page) == {"expression": "2 + 2"}
    assert "'everything': False" in kw.get_accessibility_tree(scope=scope_page)
