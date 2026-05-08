import pytest

from rfvibium.errors import BrowserSessionError
from rfvibium.keywords.navigation import NavigationKeywords


class DummyWaitUntil:
    def __init__(self) -> None:
        self.url_calls = []

    def url(self, expected_url_fragment, timeout=None) -> None:
        self.url_calls.append((expected_url_fragment, timeout))


class DummyContext:
    _next_id = 1

    def __init__(self) -> None:
        self.id = f"c{DummyContext._next_id}"
        DummyContext._next_id += 1
        self.closed = False

    def new_page(self):
        return DummyPage(context=self)

    def close(self):
        self.closed = True


class DummyPage:
    _next_id = 1

    def __init__(self, url: str = "about:blank", context=None) -> None:
        self.id = f"p{DummyPage._next_id}"
        DummyPage._next_id += 1
        self._url = url
        self.context = context if context is not None else DummyContext()
        self.wait_until = DummyWaitUntil()
        self.closed = False
        self._frames = []
        self.back_calls = 0
        self.forward_calls = 0
        self.reload_calls = 0
        self.bring_to_front_calls = 0

    def go(self, url: str) -> None:
        self._url = url

    def back(self) -> None:
        self.back_calls += 1

    def forward(self) -> None:
        self.forward_calls += 1

    def reload(self) -> None:
        self.reload_calls += 1

    def bring_to_front(self) -> None:
        self.bring_to_front_calls += 1

    def url(self) -> str:
        return self._url

    def close(self) -> None:
        self.closed = True

    def frames(self):
        return list(self._frames)

    def frame(self, name_or_url: str):
        value = str(name_or_url)
        for frame in self._frames:
            if value in getattr(frame, "name", ""):
                return frame
            if value in frame.url():
                return frame
        return None


class DummyFrame:
    def __init__(self, url: str, name: str = "", id_: str = "") -> None:
        self._url = url
        self.name = name
        self.id = id_
        self.back_calls = 0
        self.forward_calls = 0
        self.reload_calls = 0

    def url(self) -> str:
        return self._url

    def back(self) -> None:
        self.back_calls += 1

    def forward(self) -> None:
        self.forward_calls += 1

    def reload(self) -> None:
        self.reload_calls += 1

    def title(self) -> str:
        return ""


class DummyBrowser:
    def __init__(self, pages=None) -> None:
        self._contexts = []
        self._pages = []
        for page in list(pages or []):
            if page.context is None:
                page.context = DummyContext()
            self._contexts.append(page.context)
            self._pages.append(page)

    def pages(self):
        return [p for p in self._pages if not p.closed]

    def new_page(self):
        context = self._contexts[-1] if self._contexts else DummyContext()
        page = DummyPage(context=context)
        self._pages.append(page)
        return page

    def new_context(self):
        context = DummyContext()
        self._contexts.append(context)
        return context


class DummySession:
    def __init__(self, page=None, browser=None) -> None:
        self.page = page
        self.browser = browser
        self.context = getattr(page, "context", None)
        self._active_page_by_browser = {}
        self._active_context_by_browser = {}
        self._active_page_by_context = {}
        self._contexts = []
        self._context_to_browser = {}
        if browser is not None:
            for candidate in browser.pages():
                ctx = candidate.context
                if ctx not in self._contexts:
                    self._contexts.append(ctx)
                self._context_to_browser[id(ctx)] = browser
            if page is not None:
                self._active_page_by_browser[id(browser)] = page
                self._active_context_by_browser[id(browser)] = page.context
                self._active_page_by_context[id(page.context)] = page

    def require_page(self):
        if self.page is None:
            raise BrowserSessionError("No active page. Call `Open Browser` first.")
        return self.page

    def resolve_scope(self, scope=None):
        if scope is None:
            return self.require_page()
        return scope

    def resolve_browser(self, browser=None):
        target = self.browser if browser is None else browser
        if target is None:
            raise BrowserSessionError("No active browser. Call `Open Browser` first.")
        if (
            target is not self.browser
            and id(target) not in self._active_page_by_browser
        ):
            raise BrowserSessionError(
                "Browser handle is not registered in this session."
            )
        return target

    def pages(self, browser=None):
        return self.resolve_browser(browser).pages()

    def resolve_context(self, context=None, browser=None):
        if context is None:
            target_browser = self.resolve_browser(browser)
            out = self._active_context_by_browser.get(id(target_browser))
            if out is None:
                raise BrowserSessionError(
                    "No active context for provided browser. Open context first."
                )
            return out
        if id(context) not in self._context_to_browser:
            raise BrowserSessionError(
                "Context handle is not associated with a registered browser in this session."
            )
        if browser is not None and self._context_to_browser[
            id(context)
        ] is not self.resolve_browser(browser):
            raise BrowserSessionError(
                "Context handle does not belong to provided browser."
            )
        return context

    def set_active_page(self, page, browser=None):
        if browser is not None:
            target = self.resolve_browser(browser)
        else:
            target = self._context_to_browser.get(id(page.context), self.browser)
            target = self.resolve_browser(target)
        self._active_page_by_browser[id(target)] = page
        self._active_context_by_browser[id(target)] = page.context
        self._active_page_by_context[id(page.context)] = page
        self._context_to_browser[id(page.context)] = target
        if page.context not in self._contexts:
            self._contexts.append(page.context)
        self.browser = target
        self.context = page.context
        self.page = page

    def get_active_page(self, browser=None):
        if browser is None:
            return self.require_page()
        target = self.resolve_browser(browser)
        if id(target) not in self._active_page_by_browser:
            raise BrowserSessionError(
                "No active page for provided browser. Open a page first."
            )
        return self._active_page_by_browser[id(target)]

    def new_page(self, browser=None, context=None):
        if context is not None:
            ctx = self.resolve_context(context=context, browser=browser)
            page = ctx.new_page()
            owner = self._context_to_browser[id(ctx)]
        else:
            owner = self.resolve_browser(browser)
            page = owner.new_page()
            ctx = page.context
        self._context_to_browser[id(ctx)] = owner
        if ctx not in self._contexts:
            self._contexts.append(ctx)
        self.set_active_page(page, browser=owner)
        return page

    def close_page(self, page=None):
        target = self.require_page() if page is None else page
        owner = self._context_to_browser[id(target.context)]
        target.close()
        remaining = [p for p in owner.pages() if p.context is target.context]
        if remaining:
            self.set_active_page(remaining[-1], browser=owner)
        else:
            self._active_page_by_context.pop(id(target.context), None)
            self._active_page_by_browser.pop(id(owner), None)
            if self.page is target:
                self.page = None

    def new_context(self, browser=None):
        owner = self.resolve_browser(browser)
        ctx = owner.new_context()
        self._contexts.append(ctx)
        self._context_to_browser[id(ctx)] = owner
        self._active_context_by_browser[id(owner)] = ctx
        if self.browser is owner:
            self.context = ctx
            self.page = None
        return ctx

    def get_active_context(self, browser=None):
        return self.resolve_context(browser=browser)

    def contexts(self, browser=None):
        owner = self.resolve_browser(browser)
        return [
            c for c in self._contexts if self._context_to_browser.get(id(c)) is owner
        ]

    def switch_context(self, context, browser=None):
        ctx = self.resolve_context(context=context, browser=browser)
        owner = self._context_to_browser[id(ctx)]
        self._active_context_by_browser[id(owner)] = ctx
        self.browser = owner
        self.context = ctx
        self.page = self._active_page_by_context.get(id(ctx))

    def close_context(self, context=None, browser=None):
        ctx = self.resolve_context(context=context, browser=browser)
        owner = self._context_to_browser[id(ctx)]
        ctx.close()
        self._contexts = [c for c in self._contexts if c is not ctx]
        self._context_to_browser.pop(id(ctx), None)
        self._active_page_by_context.pop(id(ctx), None)
        if self._active_context_by_browser.get(id(owner)) is ctx:
            remaining = self.contexts(browser=owner)
            self._active_context_by_browser[id(owner)] = (
                remaining[-1] if remaining else None
            )


class TestableNavigation(NavigationKeywords):
    def __init__(self, session) -> None:
        self._session = session


def test_list_pages_marks_active_page() -> None:
    ctx = DummyContext()
    p1 = DummyPage("https://example.com", context=ctx)
    p2 = DummyPage("https://example.com/docs", context=ctx)
    browser = DummyBrowser([p1, p2])
    session = DummySession(page=p2, browser=browser)
    kw = TestableNavigation(session)

    result = kw.list_pages()

    assert result == [
        " 0: https://example.com",
        "*1: https://example.com/docs",
    ]


def test_new_page_without_url_sets_active_page() -> None:
    p1 = DummyPage("https://example.com")
    browser = DummyBrowser([p1])
    session = DummySession(page=p1, browser=browser)
    kw = TestableNavigation(session)

    out = kw.new_page()

    assert out == "about:blank"
    assert session.page.url() == "about:blank"
    assert len(browser.pages()) == 2


def test_new_page_with_url_navigates() -> None:
    p1 = DummyPage("https://example.com")
    browser = DummyBrowser([p1])
    session = DummySession(page=p1, browser=browser)
    kw = TestableNavigation(session)

    out = kw.new_page("https://robotframework.org")

    assert out == "https://robotframework.org"
    assert session.page.url() == "https://robotframework.org"


def test_new_page_uses_explicit_browser() -> None:
    p1 = DummyPage("https://example.com")
    p2 = DummyPage("https://example.org")
    browser_a = DummyBrowser([p1])
    browser_b = DummyBrowser([p2])
    session = DummySession(page=p1, browser=browser_a)
    session._active_page_by_browser[id(browser_b)] = p2
    kw = TestableNavigation(session)

    out = kw.new_page(browser=browser_b)

    assert out == "about:blank"
    assert session.browser is browser_b
    assert session.page.url() == "about:blank"


def test_switch_page_brings_explicit_page_to_front() -> None:
    ctx = DummyContext()
    p1 = DummyPage("https://example.com", context=ctx)
    p2 = DummyPage("https://docs.example.com", context=ctx)
    browser = DummyBrowser([p1, p2])
    session = DummySession(page=p1, browser=browser)
    kw = TestableNavigation(session)

    kw.switch_page(page=p2)

    assert p2.bring_to_front_calls == 1
    assert session.page is p2


def test_switch_page_uses_active_page_when_page_omitted() -> None:
    ctx = DummyContext()
    p1 = DummyPage("https://example.com", context=ctx)
    p2 = DummyPage("https://docs.example.com", context=ctx)
    browser = DummyBrowser([p1, p2])
    session = DummySession(page=p1, browser=browser)
    kw = TestableNavigation(session)

    kw.switch_page()

    assert p1.bring_to_front_calls == 1
    assert p2.bring_to_front_calls == 0
    assert session.page is p1


def test_navigation_keywords_use_explicit_scope_when_provided() -> None:
    page = DummyPage("https://example.com")
    frame = DummyFrame("https://example.com/frame", name="frame-a")
    session = DummySession(page=page, browser=DummyBrowser([page]))
    kw = TestableNavigation(session)

    kw.go_back(scope=frame)
    kw.go_forward(scope=frame)
    kw.reload_page(scope=frame)

    assert frame.back_calls == 1
    assert frame.forward_calls == 1
    assert frame.reload_calls == 1


def test_close_page_default_closes_active_scope() -> None:
    ctx = DummyContext()
    p1 = DummyPage("https://example.com", context=ctx)
    p2 = DummyPage("https://docs.example.com", context=ctx)
    browser = DummyBrowser([p1, p2])
    session = DummySession(page=p2, browser=browser)
    kw = TestableNavigation(session)

    kw.close_page()

    assert p2.closed is True
    assert session.page is p1


def test_close_page_uses_explicit_scope() -> None:
    ctx = DummyContext()
    p1 = DummyPage("https://example.com", context=ctx)
    p2 = DummyPage("https://docs.example.com", context=ctx)
    browser = DummyBrowser([p1, p2])
    session = DummySession(page=p1, browser=browser)
    kw = TestableNavigation(session)

    kw.close_page(scope=p2)

    assert p2.closed is True
    assert session.page is p1


def test_page_keywords_require_open_browser() -> None:
    session = DummySession(page=None, browser=None)
    kw = TestableNavigation(session)

    with pytest.raises(BrowserSessionError, match="Open Browser"):
        kw.list_pages()


def test_get_active_page_returns_session_scope() -> None:
    page = DummyPage("https://example.com")
    session = DummySession(page=page, browser=DummyBrowser([page]))
    kw = TestableNavigation(session)

    assert kw.get_active_page() is page


def test_get_active_page_from_explicit_browser() -> None:
    page = DummyPage("https://example.com")
    other = DummyPage("https://example.org")
    browser = DummyBrowser([page])
    browser2 = DummyBrowser([other])
    session = DummySession(page=page, browser=browser)
    session._active_page_by_browser[id(browser2)] = other
    kw = TestableNavigation(session)

    assert kw.get_active_page(browser=browser2) is other


def test_new_context_creates_and_activates_context() -> None:
    page = DummyPage("https://example.com", context=DummyContext())
    browser = DummyBrowser([page])
    session = DummySession(page=page, browser=browser)
    kw = TestableNavigation(session)

    ctx = kw.new_context()

    assert ctx is session.context
    assert session.page is None


def test_list_contexts_marks_active() -> None:
    page = DummyPage("https://example.com", context=DummyContext())
    browser = DummyBrowser([page])
    session = DummySession(page=page, browser=browser)
    ctx2 = session.new_context()
    kw = TestableNavigation(session)

    out = kw.list_contexts()

    assert out[-1].startswith("*")
    assert ctx2.id in out[-1]


def test_get_frame_resolves_by_name() -> None:
    page = DummyPage("https://example.com")
    frame = DummyFrame("https://example.com/frame-a", name="a")
    page._frames = [frame]
    session = DummySession(page=page, browser=DummyBrowser([page]))
    kw = TestableNavigation(session)

    out = kw.get_frame("a", scope=page)

    assert out is frame


def test_get_frame_missing_raises_typed_error() -> None:
    page = DummyPage("https://example.com")
    session = DummySession(page=page, browser=DummyBrowser([page]))
    kw = TestableNavigation(session)

    with pytest.raises(BrowserSessionError, match="could not find a frame"):
        kw.get_frame("missing", scope=page)


def test_list_frames_returns_fast_payload_by_default() -> None:
    page = DummyPage("https://example.com")
    page._frames = [
        DummyFrame("https://example.com/frame-a", name="a"),
        DummyFrame("https://example.com/frame-b", name="b"),
    ]
    session = DummySession(page=page, browser=DummyBrowser([page]))
    kw = TestableNavigation(session)

    result = kw.list_frames()

    assert result == [
        {"index": 0, "url": "", "title": ""},
        {"index": 1, "url": "", "title": ""},
    ]


def test_list_frames_can_include_url_and_title() -> None:
    page = DummyPage("https://example.com")
    page._frames = [
        DummyFrame("https://example.com/frame-a", name="a"),
        DummyFrame("https://example.com/frame-b", name="b"),
    ]
    session = DummySession(page=page, browser=DummyBrowser([page]))
    kw = TestableNavigation(session)

    result = kw.list_frames(include_url=True, include_title=True)

    assert result == [
        {"index": 0, "url": "https://example.com/frame-a", "title": ""},
        {"index": 1, "url": "https://example.com/frame-b", "title": ""},
    ]
