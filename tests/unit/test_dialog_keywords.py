from rfvibium.keywords import dialogs as dialogs_module
from rfvibium.keywords.dialogs import DialogKeywords


class _LoggerSpy:
    def __init__(self) -> None:
        self.messages = []

    def info(self, message, html=False) -> None:
        self.messages.append(message)


class DummySession:
    def __init__(self, page) -> None:
        self._page = page

    def require_page(self):
        return self._page


class DummyPage:
    def __init__(self) -> None:
        self.handlers = []

    def on_dialog(self, handler) -> None:
        self.handlers.append(handler)


class DummyDialog:
    def __init__(self) -> None:
        self.accepted_with = None

    def accept(self, text=None) -> None:
        self.accepted_with = text


class TestableDialogs(DialogKeywords):
    def __init__(self, page) -> None:
        self._session = DummySession(page)


def test_dialog_accept_without_text_uses_accept_mode(monkeypatch) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(dialogs_module, "logger", spy)
    page = DummyPage()
    kw = TestableDialogs(page)

    kw.dialog_accept()

    assert page.handlers == ["accept"]
    assert spy.messages == ["Configuring dialog handler: accept."]


def test_dialog_accept_with_text_registers_callable(monkeypatch) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(dialogs_module, "logger", spy)
    page = DummyPage()
    kw = TestableDialogs(page)

    kw.dialog_accept("my prompt value")

    assert len(page.handlers) == 1
    assert callable(page.handlers[0])
    dialog = DummyDialog()
    page.handlers[0](dialog)
    assert dialog.accepted_with == "my prompt value"
    assert spy.messages == ["Configuring dialog handler: accept with prompt text."]


def test_dialog_dismiss_uses_dismiss_mode(monkeypatch) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(dialogs_module, "logger", spy)
    page = DummyPage()
    kw = TestableDialogs(page)

    kw.dialog_dismiss()

    assert page.handlers == ["dismiss"]
    assert spy.messages == ["Configuring dialog handler: dismiss."]
