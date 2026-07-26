import pytest

from rfvibium.browser_session import SessionPool
from rfvibium.errors import BrowserSessionError, VibiumLibraryError


def test_require_page_without_open_raises_browser_session_error() -> None:
    session = SessionPool()
    with pytest.raises(BrowserSessionError, match="Open Browser"):
        session.require_page()


def test_browser_session_error_is_catchable_as_base() -> None:
    session = SessionPool()
    with pytest.raises(VibiumLibraryError):
        session.require_page()


def test_browser_session_error_inherits_from_vibium_library_error() -> None:
    assert issubclass(BrowserSessionError, VibiumLibraryError)


class FakeContext:
    def __init__(self, id_: str) -> None:
        self.id = id_


class FakePage:
    def __init__(self, id_: str, context: FakeContext) -> None:
        self.id = id_
        self.context = context


class FakeBrowser:
    def __init__(self, name: str) -> None:
        self.name = name
        self.stopped = False
        self._ctx = FakeContext(f"{name}-c1")
        self._pages = [FakePage(f"{name}-p1", self._ctx)]

    def page(self):
        return self._pages[0]

    def pages(self):
        return list(self._pages)

    def new_page(self):
        page = FakePage(f"{self.name}-p{len(self._pages)+1}", self._ctx)
        self._pages.append(page)
        return page

    def new_context(self):
        self._ctx = FakeContext(f"{self.name}-c{len(self._pages)+1}")
        return self._ctx

    def stop(self):
        self.stopped = True


class FailingBrowser(FakeBrowser):
    def stop(self):
        raise RuntimeError(f"{self.name}-stop-failed")


def _register(pool: SessionPool, browser: FakeBrowser) -> None:
    from rfvibium.browser_session import BrowserSession

    sess = BrowserSession(
        browser=browser, context=browser.page().context, page=browser.page()
    )
    sess._contexts.append(browser.page().context)
    sess._active_page_by_context[id(browser.page().context)] = browser.page()
    pool._sessions.append(sess)
    pool._by_browser_id[id(browser)] = sess
    pool.browser = browser
    pool.context = browser.page().context
    pool.page = browser.page()


def test_close_non_registered_browser_raises() -> None:
    session = SessionPool()
    b1 = FakeBrowser("a")
    b2 = FakeBrowser("b")
    _register(session, b1)

    with pytest.raises(BrowserSessionError, match="not registered"):
        session.close(browser=b2)


def test_close_active_browser_promotes_last_opened() -> None:
    session = SessionPool()
    b1 = FakeBrowser("a")
    b2 = FakeBrowser("b")
    _register(session, b1)
    _register(session, b2)

    session.close(browser=b2)

    assert b2.stopped is True
    assert session.browser is b1
    assert session.page is b1.page()


def test_close_all_is_best_effort_and_raises_aggregate_error() -> None:
    session = SessionPool()
    ok = FakeBrowser("ok")
    bad = FailingBrowser("bad")
    _register(session, ok)
    _register(session, bad)

    with pytest.raises(BrowserSessionError, match="one or more"):
        session.close_all()

    assert session.browser is None
    assert session.page is None
    assert session.browser_count() == 0
    assert ok.stopped is True
