import json
from pathlib import Path

from rfvibium.keywords import context as context_module
from rfvibium.keywords.context import StorageKeywords


class DummyContext:
    def __init__(self, state=None) -> None:
        self._state = state or {"cookies": [], "origins": []}
        self.restored = None

    def storage(self):
        return dict(self._state)

    def set_storage(self, state) -> None:
        self.restored = state


class DummyPage:
    def __init__(self) -> None:
        self.context = DummyContext()


class DummySession:
    def __init__(self, page) -> None:
        self._page = page

    def require_page(self):
        return self._page


class TestableStorage(StorageKeywords):
    def __init__(self, page) -> None:
        self._session = DummySession(page)


def test_export_storage_state_writes_json(tmp_path: Path) -> None:
    page = DummyPage()
    kw = TestableStorage(page)

    out = kw.export_storage_state(str(tmp_path / "state.json"), embed=False)

    written = Path(out)
    assert written.read_text(encoding="utf-8") == json.dumps(
        page.context.storage(), indent=2
    )


def test_restore_storage_state_reads_and_applies(tmp_path: Path) -> None:
    page = DummyPage()
    kw = TestableStorage(page)
    payload = {"cookies": [{"name": "x", "value": "y"}], "origins": []}
    path = tmp_path / "in.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    kw.restore_storage_state(str(path))

    assert page.context.restored == payload


def test_export_storage_state_embeds_link(monkeypatch, tmp_path: Path) -> None:
    class _Spy:
        def __init__(self) -> None:
            self.messages = []

        def info(self, message, html=False) -> None:
            self.messages.append((message, html))

    spy = _Spy()
    monkeypatch.setattr(context_module, "logger", spy)
    page = DummyPage()
    kw = TestableStorage(page)

    kw.export_storage_state(str(tmp_path / "state.json"), embed=True)

    html_msgs = [m for m, h in spy.messages if h]
    assert len(html_msgs) == 1
    assert "Open storage state" in html_msgs[0]
