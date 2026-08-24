from unittest.mock import MagicMock, patch

import pytest

from rfvibium.browser_session import BrowserSession, SessionPool
from rfvibium.errors import VibiumLibraryError
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

    BrowserSession.create(headless=True, engine="firefox", channel="beta")

    mock_start.assert_called_once_with(
        headless=True, engine="firefox", channel="beta"
    )


@patch("vibium.browser.start")
def test_browser_session_create_omits_engine_by_default(
    mock_start: MagicMock,
) -> None:
    browser = MagicMock()
    browser.page.return_value = MagicMock()
    mock_start.return_value = browser

    BrowserSession.create(headless=False)

    mock_start.assert_called_once_with(headless=False, engine=None, channel=None)


@patch("rfvibium.browser_session.BrowserSession.create")
def test_session_pool_open_forwards_engine_options(mock_create: MagicMock) -> None:
    session = MagicMock()
    browser = object()
    session.browser = browser
    mock_create.return_value = session
    pool = SessionPool(headless=True)

    result = pool.open(engine="firefox", channel="release")

    mock_create.assert_called_once_with(
        headless=True, engine="firefox", channel="release"
    )
    assert result is browser


def test_open_browser_delegates_normalized_engine_options() -> None:
    lib = Vibium()
    session = DummySession()
    lib._session = session

    lib.open_browser(engine="Firefox", channel="Beta")

    assert session.open_kwargs == {"engine": "firefox", "channel": "beta"}


def test_open_browser_without_engine_passes_none() -> None:
    lib = Vibium()
    session = DummySession()
    lib._session = session

    lib.open_browser()

    assert session.open_kwargs == {"engine": None, "channel": None}


@pytest.mark.parametrize("engine", ["safari", "", "  "])
def test_open_browser_rejects_invalid_engine(engine: str) -> None:
    lib = Vibium()

    with pytest.raises(VibiumLibraryError, match="unsupported engine|cannot be empty"):
        lib.open_browser(engine=engine)


@pytest.mark.parametrize("channel", ["nightly", "", "  "])
def test_open_browser_rejects_invalid_channel(channel: str) -> None:
    lib = Vibium()

    with pytest.raises(VibiumLibraryError, match="unsupported channel|cannot be empty"):
        lib.open_browser(engine="firefox", channel=channel)


def test_open_browser_rejects_channel_with_chrome() -> None:
    lib = Vibium()

    with pytest.raises(VibiumLibraryError, match="firefox only"):
        lib.open_browser(engine="chrome", channel="beta")
