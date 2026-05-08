from rfvibium.keywords.context import CookieKeywords, StorageKeywords


class DummyContext:
    def __init__(self, name: str) -> None:
        self.name = name
        self.cookies_data = [{"name": f"{name}_cookie", "value": "1"}]
        self.last_set_cookies = None
        self.cleared = False
        self.storage_data = {
            "cookies": [],
            "origins": [{"origin": f"https://{name}.example"}],
        }
        self.last_set_storage = None

    def cookies(self):
        return list(self.cookies_data)

    def set_cookies(self, cookies):
        self.last_set_cookies = cookies

    def clear_cookies(self):
        self.cleared = True

    def storage(self):
        return self.storage_data

    def set_storage(self, state):
        self.last_set_storage = state


class DummyPage:
    def __init__(self, url: str, context: DummyContext) -> None:
        self._url = url
        self.context = context

    def url(self):
        return self._url


class DummySession:
    def __init__(
        self, default_context: DummyContext, alt_context: DummyContext
    ) -> None:
        self.default_context = default_context
        self.alt_context = alt_context
        self.default_page = DummyPage("https://default.example", default_context)
        self.alt_page = DummyPage("https://alt.example", alt_context)

    def resolve_context(self, context=None, browser=None):
        return self.default_context if context is None else context

    def get_active_page_for_context(self, context):
        return self.default_page if context is self.default_context else self.alt_page


class TestableCookies(CookieKeywords):
    def __init__(self, session):
        self._session = session


class TestableStorage(StorageKeywords):
    def __init__(self, session):
        self._session = session


def test_list_cookies_uses_explicit_context() -> None:
    default_ctx = DummyContext("default")
    alt_ctx = DummyContext("alt")
    kw = TestableCookies(DummySession(default_ctx, alt_ctx))

    cookies = kw.list_cookies(context=alt_ctx)

    assert cookies[0]["name"] == "alt_cookie"


def test_set_cookie_uses_page_url_from_context_page() -> None:
    default_ctx = DummyContext("default")
    alt_ctx = DummyContext("alt")
    kw = TestableCookies(DummySession(default_ctx, alt_ctx))

    kw.set_cookie("sid", "abc", context=alt_ctx)

    assert alt_ctx.last_set_cookies[0]["url"] == "https://alt.example"
