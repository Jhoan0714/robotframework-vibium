from rfvibium.library import Vibium


class DummySession:
    def __init__(self) -> None:
        self.open_called = False
        self.open_return = object()
        self.close_called = False
        self.close_all_called = False
        self.closed_browser = None

    def open(self, **kwargs):
        self.open_called = True
        self.open_kwargs = kwargs
        return self.open_return

    def close(self, browser=None) -> None:
        self.close_called = True
        self.closed_browser = browser

    def close_all(self) -> None:
        self.close_all_called = True


def test_open_browser_delegates_to_session() -> None:
    lib = Vibium()
    session = DummySession()
    lib._session = session

    out = lib.open_browser()

    assert session.open_called is True
    assert out is session.open_return


def test_close_browser_delegates_to_session() -> None:
    lib = Vibium()
    session = DummySession()
    lib._session = session

    lib.close_browser()

    assert session.close_called is True
    assert session.closed_browser is None


def test_close_browser_accepts_explicit_handle() -> None:
    lib = Vibium()
    session = DummySession()
    lib._session = session
    handle = object()

    lib.close_browser(browser=handle)

    assert session.close_called is True
    assert session.closed_browser is handle


def test_close_all_browsers_delegates_to_session() -> None:
    lib = Vibium()
    session = DummySession()
    lib._session = session

    lib.close_all_browsers()

    assert session.close_all_called is True


def test_library_version_comes_from_version_module() -> None:
    from rfvibium.version import __version__

    assert Vibium.ROBOT_LIBRARY_VERSION == __version__
    assert __version__  # non-empty
