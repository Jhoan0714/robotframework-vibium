"""Unit tests for ``Vibium.keywords.capture`` (screenshots and PDF)."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from rfvibium.errors import ScreenshotError, VibiumLibraryError
from rfvibium.keywords import capture as capture_module
from rfvibium.keywords.capture import (
    CaptureKeywords,
    _next_auto_screenshot_path,
    _path_for_log,
    _resolve_screenshot_path,
)


class DummyWaitUntil:
    def __init__(self) -> None:
        self.loaded_calls = 0
        self.loaded_should_raise: Exception | None = None

    def loaded(self, state=None, timeout=None) -> None:
        self.loaded_calls += 1
        if self.loaded_should_raise is not None:
            raise self.loaded_should_raise


class DummyPage:
    def __init__(self, screenshot_responses) -> None:
        # screenshot_responses: list of either bytes (success) or Exception instances
        self._responses = list(screenshot_responses)
        self.screenshot_calls = 0
        self.last_screenshot_full_page = None
        self.last_screenshot_clip = None
        self.pdf_calls = 0
        self.wait_until = DummyWaitUntil()
        self.last_find_args = None
        self.last_find_kwargs = None
        self.last_find_all_args = None
        self.last_find_all_kwargs = None
        self.evaluate_calls = []
        self.find_element = _DummyElement("one", text="hello", html="<div>hello</div>")
        self.find_all_elements = [
            _DummyElement("e1"),
            _DummyElement("e2"),
            _DummyElement("e3"),
        ]
        self.content_value = "<html><body>doc</body></html>"
        self.a11y_value = {"tree": "ok"}

    def screenshot(self, full_page=None, clip=None) -> bytes:
        self.screenshot_calls += 1
        self.last_screenshot_full_page = full_page
        self.last_screenshot_clip = clip
        response = self._responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    def pdf(self) -> bytes:
        self.pdf_calls += 1
        return b"PDFDATA"

    def evaluate(self, expression: str):
        self.evaluate_calls.append(expression)
        if expression == "document.body ? document.body.innerText : ''":
            return "PAGE TEXT"
        if expression == "document.body ? document.body.innerHTML : ''":
            return "<main>INNER</main>"
        return {"expression": expression}

    def find(self, *args, **kwargs):
        self.last_find_args = args
        self.last_find_kwargs = kwargs
        return self.find_element

    def find_all(self, *args, **kwargs):
        self.last_find_all_args = args
        self.last_find_all_kwargs = kwargs
        return list(self.find_all_elements)

    def content(self) -> str:
        return self.content_value

    def a11y_tree(self, everything=False):
        return {"everything": everything, **self.a11y_value}


class _DummyElement:
    def __init__(self, name: str, text: str = "", html: str = "") -> None:
        self.name = name
        self._text = text or f"text-{name}"
        self._html = html or f"<div>{name}</div>"
        self.element_screenshot_calls = 0

    def text(self) -> str:
        return self._text

    def html(self) -> str:
        return self._html

    def screenshot(self) -> bytes:
        self.element_screenshot_calls += 1
        return b"ELPNG"

    def __repr__(self) -> str:
        return f"Element(name='{self.name}')"


class DummySession:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def require_page(self) -> DummyPage:
        return self._page

    def resolve_scope(self, scope=None):
        return self._page if scope is None else scope


class TestableCapture(CaptureKeywords):
    def __init__(self, page: DummyPage) -> None:
        self.library = SimpleNamespace(_session=DummySession(page))


def test_take_screenshot_succeeds_on_first_attempt(tmp_path: Path) -> None:
    page = DummyPage([b"PNGDATA"])
    kw = TestableCapture(page)

    out = kw.take_screenshot(str(tmp_path / "ok.png"))

    assert page.screenshot_calls == 1
    assert page.wait_until.loaded_calls == 0
    assert Path(out).read_bytes() == b"PNGDATA"
    assert page.last_screenshot_full_page is None
    assert page.last_screenshot_clip is None


def test_take_screenshot_passes_full_page_and_clip(tmp_path: Path) -> None:
    page = DummyPage([b"PNG"])
    kw = TestableCapture(page)
    clip = {"x": 1, "y": 2, "width": 100, "height": 200}

    kw.take_screenshot(str(tmp_path / "clip.png"), full_page=True, clip=clip)

    assert page.last_screenshot_full_page is True
    assert page.last_screenshot_clip == {"x": 1, "y": 2, "width": 100, "height": 200}


def test_take_screenshot_accepts_clip_json_string(tmp_path: Path) -> None:
    page = DummyPage([b"PNG"])
    kw = TestableCapture(page)

    kw.take_screenshot(
        str(tmp_path / "j.png"),
        clip='{"x": 0, "y": 0, "width": 10, "height": 20}',
    )

    assert page.last_screenshot_clip == {"x": 0, "y": 0, "width": 10, "height": 20}


def test_take_screenshot_rejects_incomplete_clip(tmp_path: Path) -> None:
    page = DummyPage([b"PNG"])
    kw = TestableCapture(page)
    with pytest.raises(ScreenshotError, match="missing"):
        kw.take_screenshot(str(tmp_path / "bad.png"), clip={"x": 0, "y": 0, "width": 1})


def test_take_element_screenshot_uses_find_and_element_api(tmp_path: Path) -> None:
    page = DummyPage([b"PNGDATA"])
    kw = TestableCapture(page)

    out = kw.take_element_screenshot("css:#card", output_path=str(tmp_path / "el.png"))

    assert page.last_find_args == ("#card",)
    assert page.last_find_kwargs == {}
    assert page.find_element.element_screenshot_calls == 1
    assert page.screenshot_calls == 0
    assert Path(out).read_bytes() == b"ELPNG"


def test_take_screenshot_retries_after_stale_context_error(tmp_path: Path) -> None:
    stale = RuntimeError("unknown error: Cannot find context with specified id")
    page = DummyPage([stale, b"PNGDATA"])
    kw = TestableCapture(page)

    out = kw.take_screenshot(str(tmp_path / "retry.png"))

    assert page.screenshot_calls == 2
    assert page.wait_until.loaded_calls == 1
    assert Path(out).read_bytes() == b"PNGDATA"


def test_take_screenshot_does_not_retry_on_unrelated_error(tmp_path: Path) -> None:
    other = RuntimeError("disk full")
    page = DummyPage([other])
    kw = TestableCapture(page)

    with pytest.raises(ScreenshotError, match="disk full"):
        kw.take_screenshot(str(tmp_path / "fail.png"))

    assert page.screenshot_calls == 1
    assert page.wait_until.loaded_calls == 0


def test_take_screenshot_fails_if_second_attempt_also_fails(tmp_path: Path) -> None:
    stale = RuntimeError("Cannot find context with specified id")
    other = RuntimeError("Cannot find context with specified id")
    page = DummyPage([stale, other])
    kw = TestableCapture(page)

    with pytest.raises(ScreenshotError, match="Cannot find context"):
        kw.take_screenshot(str(tmp_path / "twofail.png"))

    assert page.screenshot_calls == 2
    assert page.wait_until.loaded_calls == 1


def test_take_screenshot_tolerates_failure_in_wait_until_loaded(tmp_path: Path) -> None:
    stale = RuntimeError("execution context was destroyed")
    page = DummyPage([stale, b"PNGDATA"])
    page.wait_until.loaded_should_raise = RuntimeError("wait failed")
    kw = TestableCapture(page)

    out = kw.take_screenshot(str(tmp_path / "wait_fail.png"))

    assert page.screenshot_calls == 2
    assert page.wait_until.loaded_calls == 1
    assert Path(out).read_bytes() == b"PNGDATA"


def test_take_screenshot_creates_parent_directory(tmp_path: Path) -> None:
    page = DummyPage([b"PNGDATA"])
    kw = TestableCapture(page)

    nested = tmp_path / "a" / "b" / "c" / "shot.png"
    out = kw.take_screenshot(str(nested))

    assert Path(out) == nested.resolve()
    assert nested.exists()


# ---------------------------------------------------------------------------
# Log embedding
# ---------------------------------------------------------------------------


class _LoggerSpy:
    def __init__(self) -> None:
        self.messages: list[tuple[str, bool]] = []

    def info(self, message: str, html: bool = False) -> None:
        self.messages.append((message, html))


def _html_messages(spy):
    return [msg for msg, html in spy.messages if html]


def test_take_screenshot_embeds_html_snippet_in_log(
    monkeypatch, tmp_path: Path
) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(capture_module, "logger", spy)

    page = DummyPage([b"PNGDATA"])
    kw = TestableCapture(page)

    out = kw.take_screenshot(str(tmp_path / "shot.png"))

    html_msgs = _html_messages(spy)
    assert len(html_msgs) == 1
    assert "<img" in html_msgs[0]
    assert 'width="800px"' in html_msgs[0]
    assert Path(out).name in html_msgs[0]


def test_take_screenshot_can_skip_embedding(monkeypatch, tmp_path: Path) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(capture_module, "logger", spy)

    page = DummyPage([b"PNGDATA"])
    kw = TestableCapture(page)

    kw.take_screenshot(str(tmp_path / "shot.png"), embed=False)

    assert _html_messages(spy) == []


def test_take_screenshot_respects_custom_width(monkeypatch, tmp_path: Path) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(capture_module, "logger", spy)

    page = DummyPage([b"PNGDATA"])
    kw = TestableCapture(page)

    kw.take_screenshot(str(tmp_path / "shot.png"), width="1200px")

    html_msgs = _html_messages(spy)
    assert html_msgs
    assert 'width="1200px"' in html_msgs[0]


def test_path_for_log_outside_robot_returns_file_uri(tmp_path: Path) -> None:
    image = tmp_path / "x.png"
    image.write_bytes(b"data")

    result = _path_for_log(image)

    assert result.startswith("file://")
    assert result.endswith("x.png")


# ---------------------------------------------------------------------------
# Screenshot path resolution
# ---------------------------------------------------------------------------


def test_resolve_screenshot_path_outside_robot_uses_cwd(monkeypatch) -> None:
    monkeypatch.setattr(capture_module, "_robot_output_dir", lambda: None)

    resolved = _resolve_screenshot_path("screenshot.png")

    assert resolved.is_absolute()
    assert resolved.name == "screenshot.png"
    assert resolved == (Path.cwd() / "screenshot.png").resolve()


def test_resolve_screenshot_path_relative_goes_under_output_media(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(capture_module, "_robot_output_dir", lambda: str(tmp_path))

    resolved = _resolve_screenshot_path("screenshot.png")

    assert resolved == (tmp_path / "media" / "screenshot.png").resolve()


def test_resolve_screenshot_path_relative_subdir_goes_under_output_media(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(capture_module, "_robot_output_dir", lambda: str(tmp_path))

    resolved = _resolve_screenshot_path("login/step1.png")

    assert resolved == (tmp_path / "media" / "login" / "step1.png").resolve()


def test_resolve_screenshot_path_absolute_is_respected(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(capture_module, "_robot_output_dir", lambda: str(tmp_path))

    absolute = tmp_path / "somewhere" / "shot.png"
    resolved = _resolve_screenshot_path(str(absolute))

    assert resolved == absolute.resolve()


def test_take_screenshot_default_writes_under_output_media(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(capture_module, "_robot_output_dir", lambda: str(tmp_path))

    page = DummyPage([b"PNGDATA"])
    kw = TestableCapture(page)

    out = kw.take_screenshot()

    assert Path(out) == (tmp_path / "media" / "vibium-screenshot-1.png").resolve()
    assert Path(out).read_bytes() == b"PNGDATA"


def test_take_screenshot_auto_numbers_successive_calls(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(capture_module, "_robot_output_dir", lambda: str(tmp_path))

    page = DummyPage([b"A", b"B", b"C"])
    kw = TestableCapture(page)

    first = kw.take_screenshot()
    second = kw.take_screenshot()
    third = kw.take_screenshot()

    media = tmp_path / "media"
    assert Path(first) == (media / "vibium-screenshot-1.png").resolve()
    assert Path(second) == (media / "vibium-screenshot-2.png").resolve()
    assert Path(third) == (media / "vibium-screenshot-3.png").resolve()
    assert Path(first).read_bytes() == b"A"
    assert Path(second).read_bytes() == b"B"
    assert Path(third).read_bytes() == b"C"


def test_take_screenshot_auto_skips_existing_files(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(capture_module, "_robot_output_dir", lambda: str(tmp_path))

    media = tmp_path / "media"
    media.mkdir()
    (media / "vibium-screenshot-1.png").write_bytes(b"old1")
    (media / "vibium-screenshot-2.png").write_bytes(b"old2")

    page = DummyPage([b"new"])
    kw = TestableCapture(page)

    out = kw.take_screenshot()

    assert Path(out) == (media / "vibium-screenshot-3.png").resolve()
    assert (media / "vibium-screenshot-1.png").read_bytes() == b"old1"


def test_take_screenshot_explicit_path_is_not_auto_numbered(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(capture_module, "_robot_output_dir", lambda: str(tmp_path))

    page = DummyPage([b"A", b"B"])
    kw = TestableCapture(page)

    first = kw.take_screenshot("login.png")
    second = kw.take_screenshot("login.png")

    assert first == second
    assert Path(first).read_bytes() == b"B"


def test_next_auto_screenshot_path_outside_robot(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(capture_module, "_robot_output_dir", lambda: None)
    monkeypatch.chdir(tmp_path)

    first = _next_auto_screenshot_path()
    first.write_bytes(b"seed")
    second = _next_auto_screenshot_path()

    assert first.name == "vibium-screenshot-1.png"
    assert second.name == "vibium-screenshot-2.png"


def test_screenshot_error_is_catchable_as_base(tmp_path: Path) -> None:
    page = DummyPage([RuntimeError("disk full")])
    kw = TestableCapture(page)

    with pytest.raises(VibiumLibraryError):
        kw.take_screenshot(str(tmp_path / "x.png"))


def test_screenshot_error_inherits_from_vibium_library_error() -> None:
    assert issubclass(ScreenshotError, VibiumLibraryError)


# ---------------------------------------------------------------------------
# Save PDF
# ---------------------------------------------------------------------------


def test_save_pdf_with_explicit_path(tmp_path: Path) -> None:
    page = DummyPage([b"PNGDATA"])
    kw = TestableCapture(page)

    out = kw.save_pdf(str(tmp_path / "report.pdf"))

    assert Path(out) == (tmp_path / "report.pdf").resolve()
    assert Path(out).read_bytes() == b"PDFDATA"
    assert page.pdf_calls == 1


def test_save_pdf_embeds_link_in_log(monkeypatch, tmp_path: Path) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(capture_module, "logger", spy)
    page = DummyPage([b"PNGDATA"])
    kw = TestableCapture(page)

    out = kw.save_pdf(str(tmp_path / "report.pdf"))

    html_msgs = _html_messages(spy)
    assert len(html_msgs) == 1
    assert "Open PDF" in html_msgs[0]
    assert Path(out).name in html_msgs[0]


def test_save_pdf_can_skip_embed(monkeypatch, tmp_path: Path) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(capture_module, "logger", spy)
    page = DummyPage([b"PNGDATA"])
    kw = TestableCapture(page)

    kw.save_pdf(str(tmp_path / "report.pdf"), embed=False)

    assert _html_messages(spy) == []


def test_save_pdf_default_path_under_output_media(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(capture_module, "_robot_output_dir", lambda: str(tmp_path))
    page = DummyPage([b"PNGDATA"])
    kw = TestableCapture(page)

    out = kw.save_pdf()

    assert Path(out) == (tmp_path / "media" / "vibium-page-1.pdf").resolve()
    assert Path(out).read_bytes() == b"PDFDATA"


def test_save_pdf_auto_numbers_successive_calls(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(capture_module, "_robot_output_dir", lambda: str(tmp_path))
    page = DummyPage([b"PNGDATA"])
    kw = TestableCapture(page)

    first = kw.save_pdf()
    second = kw.save_pdf()

    media = tmp_path / "media"
    assert Path(first) == (media / "vibium-page-1.pdf").resolve()
    assert Path(second) == (media / "vibium-page-2.pdf").resolve()


def test_capture_keywords_use_explicit_scope_when_provided(tmp_path: Path) -> None:
    active_page = DummyPage([b"ACTIVE"])
    scope_page = DummyPage([b"SCOPE", b"PNGDATA"])
    kw = TestableCapture(active_page)

    shot = kw.take_screenshot(str(tmp_path / "scope-shot.png"), scope=scope_page)
    element_shot = kw.take_element_screenshot(
        "css:#card", output_path=str(tmp_path / "scope-el.png"), scope=scope_page
    )
    pdf = kw.save_pdf(str(tmp_path / "scope.pdf"), scope=scope_page)

    assert Path(shot).read_bytes() == b"SCOPE"
    assert Path(element_shot).read_bytes() == b"ELPNG"
    assert Path(pdf).read_bytes() == b"PDFDATA"
    assert scope_page.screenshot_calls == 1
    assert scope_page.find_element.element_screenshot_calls == 1
    assert scope_page.pdf_calls == 1
    assert active_page.screenshot_calls == 0
    assert active_page.pdf_calls == 0
