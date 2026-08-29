from unittest.mock import MagicMock, patch

from rfvibium.browser_session import BrowserSession, SessionPool
from rfvibium.library import Vibium


class DummySession:
    def __init__(self) -> None:
        self.open_kwargs: dict | None = None
        self.open_return = object()

    def open(self, **kwargs):
        self.open_kwargs = kwargs
        return self.open_return


@patch("vibium.browser.start")
def test_browser_session_create_passes_launch_options(mock_start: MagicMock) -> None:
    browser = MagicMock()
    page = MagicMock()
    browser.page.return_value = page
    mock_start.return_value = browser

    BrowserSession.create(
        url="wss://example.com/bidi",
        engine="firefox",
        channel="beta",
        headless=True,
        headers={"Authorization": "Bearer x"},
    )

    mock_start.assert_called_once_with(
        "wss://example.com/bidi",
        engine="firefox",
        channel="beta",
        headless=True,
        headers={"Authorization": "Bearer x"},
    )


@patch("vibium.browser.start")
def test_browser_session_create_omits_optional_launch_args(
    mock_start: MagicMock,
) -> None:
    browser = MagicMock()
    browser.page.return_value = MagicMock()
    mock_start.return_value = browser

    BrowserSession.create(headless=False)

    mock_start.assert_called_once_with(
        None,
        engine=None,
        channel=None,
        headless=False,
        headers=None,
    )


@patch("rfvibium.browser_session.BrowserSession.create")
def test_session_pool_open_forwards_engine_options(mock_create: MagicMock) -> None:
    session = MagicMock()
    browser = object()
    session.browser = browser
    mock_create.return_value = session
    pool = SessionPool(headless=True)

    result = pool.open(engine="Firefox", channel="release")

    mock_create.assert_called_once_with(
        url=None,
        engine="Firefox",
        channel="release",
        headless=True,
        headers=None,
    )
    assert result is browser


@patch("rfvibium.browser_session.BrowserSession.create")
def test_session_pool_open_headless_overrides_library_default(
    mock_create: MagicMock,
) -> None:
    session = MagicMock()
    session.browser = object()
    mock_create.return_value = session
    pool = SessionPool(headless=True)

    pool.open(headless=False)

    mock_create.assert_called_once_with(
        url=None,
        engine=None,
        channel=None,
        headless=False,
        headers=None,
    )


def test_open_browser_passes_launch_options() -> None:
    lib = Vibium(headless=True)
    session = DummySession()
    lib._session = session

    lib.open_browser(
        url="ws://host/bidi",
        engine="firefox",
        channel="beta",
        headless=False,
        headers={"X-Token": "t"},
    )

    assert session.open_kwargs == {
        "url": "ws://host/bidi",
        "engine": "firefox",
        "channel": "beta",
        "headless": False,
        "headers": {"X-Token": "t"},
    }


def test_open_browser_without_engine_passes_none() -> None:
    lib = Vibium()
    session = DummySession()
    lib._session = session

    lib.open_browser()

    assert session.open_kwargs == {
        "url": None,
        "engine": None,
        "channel": None,
        "headless": None,
        "headers": None,
    }


def test_open_browser_uses_library_headless_when_omitted() -> None:
    lib = Vibium(headless=True)
    session = DummySession()
    lib._session = session

    lib.open_browser(engine="firefox")

    assert session.open_kwargs == {
        "url": None,
        "engine": "firefox",
        "channel": None,
        "headless": None,
        "headers": None,
    }
