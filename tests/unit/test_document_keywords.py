from types import SimpleNamespace

import pytest

from rfvibium.errors import VibiumLibraryError
from rfvibium.keywords.document import DocumentKeywords


class DummyPage:
    def __init__(self) -> None:
        self.content: str | None = None

    def set_content(self, html: str) -> None:
        self.content = html


class DummySession:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def require_page(self) -> DummyPage:
        return self._page


class TestableDocument(DocumentKeywords):
    def __init__(self, page: DummyPage) -> None:
        self.library = SimpleNamespace(_session=DummySession(page))


def test_set_page_content() -> None:
    page = DummyPage()
    kw = TestableDocument(page)

    kw.set_page_content("<html><body>hi</body></html>")

    assert page.content == "<html><body>hi</body></html>"


def test_set_page_content_allows_empty_string() -> None:
    page = DummyPage()
    kw = TestableDocument(page)

    kw.set_page_content("")

    assert page.content == ""


def test_set_page_content_rejects_none() -> None:
    kw = TestableDocument(DummyPage())
    with pytest.raises(VibiumLibraryError, match="html is required"):
        kw.set_page_content(None)  # type: ignore[arg-type]
