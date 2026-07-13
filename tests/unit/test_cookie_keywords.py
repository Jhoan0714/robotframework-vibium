from types import SimpleNamespace

from rfvibium.keywords.context import CookieKeywords


class DummyContext:
    def __init__(self) -> None:
        self._cookies = [{"name": "a", "value": "1"}]
        self.set_calls = []
        self.cleared = False

    def cookies(self):
        return list(self._cookies)

    def set_cookies(self, cookies) -> None:
        self.set_calls.append(cookies)
        for c in cookies:
            self._cookies = [x for x in self._cookies if x.get("name") != c.get("name")]
            self._cookies.append(dict(c))

    def clear_cookies(self) -> None:
        self.cleared = True
        self._cookies.clear()


class DummyPage:
    def __init__(self) -> None:
        self.context = DummyContext()

    def url(self) -> str:
        return "https://example.com/app"


class DummySession:
    def __init__(self, page) -> None:
        self._page = page

    def require_page(self):
        return self._page


class TestableCookies(CookieKeywords):
    def __init__(self, page) -> None:
        self.library = SimpleNamespace(_session=DummySession(page))


def test_list_cookies_returns_context_cookies() -> None:
    page = DummyPage()
    kw = TestableCookies(page)

    result = kw.list_cookies()

    assert result == [{"name": "a", "value": "1"}]


def test_set_cookie_uses_page_url_when_no_url_or_domain() -> None:
    page = DummyPage()
    kw = TestableCookies(page)

    kw.set_cookie("session", "abc123")

    assert page.context.set_calls == [
        [{"name": "session", "value": "abc123", "url": "https://example.com/app"}]
    ]


def test_set_cookie_uses_explicit_url() -> None:
    page = DummyPage()
    kw = TestableCookies(page)

    kw.set_cookie("x", "y", url="https://other.test/")

    assert page.context.set_calls == [
        [{"name": "x", "value": "y", "url": "https://other.test/"}]
    ]


def test_set_cookie_uses_domain_when_given() -> None:
    page = DummyPage()
    kw = TestableCookies(page)

    kw.set_cookie("x", "y", domain=".example.com", path="/")

    assert page.context.set_calls == [
        [{"name": "x", "value": "y", "domain": ".example.com", "path": "/"}]
    ]


def test_clear_cookies_calls_context() -> None:
    page = DummyPage()
    kw = TestableCookies(page)

    kw.clear_cookies()

    assert page.context.cleared is True
    assert page.context.cookies() == []
