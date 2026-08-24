"""Capture-related keywords (screenshots and PDF artifacts)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from robot.api import logger
from robot.api.deco import keyword

from ..errors import ScreenshotError
from ..locator import format_locators, resolve_required_locators

_STALE_CONTEXT_MARKERS = (
    "cannot find context",
    "context not found",
    "no such frame",
    "no such window",
    "target closed",
    "execution context was destroyed",
)

SCREENSHOT_SUBDIR = "media"
DEFAULT_SCREENSHOT_PATTERN = "vibium-screenshot-{index}.png"
DEFAULT_ELEMENT_SCREENSHOT_PATTERN = "vibium-element-screenshot-{index}.png"
DEFAULT_PDF_PATTERN = "vibium-page-{index}.pdf"


def _is_stale_context_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return any(marker in message for marker in _STALE_CONTEXT_MARKERS)


_CLIP_RECT_KEYS = ("x", "y", "width", "height")


def _normalize_screenshot_clip(clip: object) -> dict[str, Any] | None:
    """Return a clip dict for ``page.screenshot`` or ``None``."""
    if clip is None:
        return None
    if isinstance(clip, str):
        try:
            parsed = json.loads(clip)
        except json.JSONDecodeError as exc:
            raise ScreenshotError(f"Invalid clip JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ScreenshotError("clip JSON must be an object")
        clip = parsed
    if isinstance(clip, dict):
        missing = [k for k in _CLIP_RECT_KEYS if k not in clip]
        if missing:
            raise ScreenshotError(f"clip missing required keys: {', '.join(missing)}")
        return {k: clip[k] for k in _CLIP_RECT_KEYS}
    raise ScreenshotError("clip must be a dict, JSON string, or None")


class CaptureKeywords:
    """Keywords to capture visual artifacts from the active page."""

    def __init__(self, library):
        self.library = library

    @keyword("Take Screenshot")
    def take_screenshot(
        self,
        *locators: str,
        output_path: str | None = None,
        embed: bool = True,
        width: str = "800px",
        full_page: bool | None = None,
        clip: object = None,
        scope: object = None,
    ) -> str:
        """Capture a PNG screenshot of the page or a matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Optional locator tokens. When provided, captures the matched element. When omitted, captures the page. |
        | ``output_path`` | Optional output file path. When omitted, an auto-numbered file is created under ``media/``. |
        | ``embed`` | When ``True`` (default), embeds an image preview in Robot logs. |
        | ``width`` | Render width used in embedded HTML preview. Default is ``800px``. |
        | ``full_page`` | Optional flag forwarded to Vibium ``page.screenshot``. ``True`` attempts to capture the full scrollable page. Ignored when locators are provided. |
        | ``clip`` | Optional clipping rectangle. Accepts a dict or JSON object string with keys ``x``, ``y``, ``width``, ``height``. Ignored when locators are provided. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Returns:
            str: Absolute path of the generated PNG file.

        Raises:
            ScreenshotError: When clip parsing fails or screenshot capture fails.

        Note:
            Page screenshots are only supported on the **top-level** browsing
            context (the tab's root page). Using ``scope`` with a frame object
            from ``Get Frame`` typically fails for page captures. Prefer
            locators (element screenshot) or ``scope`` on the main page
            (optionally with ``clip``).

        Example:
            | ${path}=    Take Screenshot
            | ${path}=    Take Screenshot    full_page=${TRUE}
            | ${path}=    Take Screenshot    output_path=home.png    clip={"x": 0, "y": 0, "width": 800, "height": 600}
            | ${path}=    Take Screenshot    css:.chart-card    output_path=chart.png
            | ${path}=    Take Screenshot    role:img    alt:Logo
        """
        page = self.library._session.resolve_scope(scope)
        if locators:
            args, kwargs = resolve_required_locators(locators)
            path = (
                _next_auto_element_screenshot_path()
                if output_path is None
                else _resolve_capture_path(output_path)
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(
                f"Taking element screenshot of '{format_locators(locators)}' -> {path}."
            )
            return self._capture_png_with_stale_page_retry(
                page,
                path,
                embed,
                width,
                lambda: page.find(*args, **kwargs).screenshot(),
            )

        path = (
            _next_auto_screenshot_path()
            if output_path is None
            else _resolve_capture_path(output_path)
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized_clip = _normalize_screenshot_clip(clip)
        return self._capture_png_with_stale_page_retry(
            page,
            path,
            embed,
            width,
            lambda: page.screenshot(full_page=full_page, clip=normalized_clip),
        )

    def _capture_png_with_stale_page_retry(
        self,
        page,
        path: Path,
        embed: bool,
        width: str,
        take_bytes: Callable[[], bytes],
    ) -> str:
        last_exc: BaseException | None = None
        for attempt in range(2):
            try:
                png_bytes = take_bytes()
                path.write_bytes(png_bytes)
                if embed:
                    self._log_screenshot(path, width)
                return str(path)
            except Exception as exc:
                last_exc = exc
                if attempt == 0 and _is_stale_context_error(exc):
                    try:
                        page.wait_for_load()
                    except Exception:
                        pass
                    continue
                break

        raise ScreenshotError(f"Unable to take screenshot: {last_exc}") from last_exc

    @keyword("Save Page As Pdf")
    def save_page_as_pdf(
        self,
        output_path: str | None = None,
        embed: bool = True,
        scope: object = None,
    ) -> str:
        """Save the resolved page scope as PDF.

        | =Argument= | =Description= |
        | ``output_path`` | Optional output file path. When omitted, an auto-numbered file is created under ``media/``. |
        | ``embed`` | When ``True`` (default), logs an HTML link to the PDF artifact. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Returns:
            str: Absolute path of the generated PDF file.

        Note:
            Like ``Take Screenshot``, PDF generation is expected to work on the
            **top-level** page context. A frame ``scope`` from ``Get Frame`` may
            be unsupported by Vibium for this operation.

        Example:
            | ${pdf}=    Save Page As Pdf
            | ${pdf}=    Save Page As Pdf    output_path=report.pdf    embed=${FALSE}
        """
        page = self.library._session.resolve_scope(scope)
        path = (
            _next_auto_pdf_path()
            if output_path is None
            else _resolve_capture_path(output_path)
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        pdf_bytes = page.pdf()
        path.write_bytes(pdf_bytes)
        if embed:
            self._log_pdf(path)
        return str(path)

    @staticmethod
    def _log_screenshot(path: Path, width: str) -> None:
        src = _path_for_log(path)
        html = (
            f'<a href="{src}" target="_blank">'
            f'<img src="{src}" width="{width}" '
            f'style="border:1px solid #ccc;border-radius:4px;">'
            f"</a>"
        )
        logger.info(html, html=True)

    @staticmethod
    def _log_pdf(path: Path) -> None:
        href = _path_for_log(path)
        name = path.name
        html = f'<a href="{href}" target="_blank">Open PDF: {name}</a>'
        logger.info(html, html=True)


def _robot_output_dir() -> str | None:
    """Return Robot Framework's ``${OUTPUT DIR}`` or ``None`` outside RF."""
    try:
        from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError

        try:
            return BuiltIn().get_variable_value("${OUTPUT DIR}")
        except RobotNotRunningError:
            return None
    except Exception:  # pragma: no cover - defensive import guard
        return None


def _resolve_capture_path(output_path: str) -> Path:
    """Resolve output path for capture keywords."""
    raw = Path(output_path).expanduser()
    if raw.is_absolute():
        return raw.resolve()

    output_dir = _robot_output_dir()
    if output_dir:
        return (Path(output_dir) / SCREENSHOT_SUBDIR / raw).resolve()
    return raw.resolve()


# Backward-compatible name used by ``assertions`` and unit tests.
_resolve_screenshot_path = _resolve_capture_path


def _next_auto_capture_path(filename_pattern: str) -> Path:
    """Return the next available path for ``filename_pattern`` with ``{index}``."""
    index = 1
    while True:
        candidate = _resolve_capture_path(filename_pattern.format(index=index))
        if not candidate.exists():
            return candidate
        index += 1


def _next_auto_screenshot_path() -> Path:
    return _next_auto_capture_path(DEFAULT_SCREENSHOT_PATTERN)


def _next_auto_element_screenshot_path() -> Path:
    return _next_auto_capture_path(DEFAULT_ELEMENT_SCREENSHOT_PATTERN)


def _next_auto_pdf_path() -> Path:
    return _next_auto_capture_path(DEFAULT_PDF_PATTERN)


def _path_for_log(path: Path) -> str:
    """Return a log-friendly path for HTML links/images."""
    output_dir = _robot_output_dir()

    if output_dir:
        try:
            return os.path.relpath(str(path), start=str(output_dir)).replace(
                os.sep, "/"
            )
        except ValueError:
            pass

    return path.as_uri()
