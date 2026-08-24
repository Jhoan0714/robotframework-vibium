"""Page emulation keywords mapped to Vibium viewport and window APIs (sync)."""

from __future__ import annotations

from typing import Any

from robot.api import logger
from robot.api.deco import keyword

from ..errors import VibiumLibraryError


class EmulationKeywords:
    """Viewport and OS-window keywords for the active page."""

    def __init__(self, library):
        self.library = library

    @staticmethod
    def _as_int(name: str, value: int | str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise VibiumLibraryError(
                f"{name} must be an integer, got {value!r}."
            ) from exc

    @keyword("Set Viewport Size")
    def set_viewport_size(
        self,
        width: int | str,
        height: int | str,
    ) -> None:
        """Set the active page viewport size in CSS pixels.

        | =Argument= | =Description= |
        | ``width`` | Viewport width in pixels. |
        | ``height`` | Viewport height in pixels. |

        Example:
            | Set Viewport Size    1280    720
        """
        page = self.library._session.require_page()
        w = EmulationKeywords._as_int("width", width)
        h = EmulationKeywords._as_int("height", height)
        size = {"width": w, "height": h}
        logger.info(f"Setting viewport size to {w}x{h}.")
        page.set_viewport(size)

    @keyword("Get Viewport Size")
    def get_viewport_size(self) -> dict[str, Any]:
        """Return the active page viewport size.

        Returns:
            dict: Mapping with ``width`` and ``height`` integers (CSS pixels).

        Example:
            | ${size}=    Get Viewport Size
            | Log    ${size}[width] x ${size}[height]
        """
        page = self.library._session.require_page()
        size = page.viewport()
        logger.info(f"Viewport size is {size.get('width')}x{size.get('height')}.")
        return dict(size)

    @keyword("Set Window")
    def set_window(
        self,
        width: int | str | None = None,
        height: int | str | None = None,
        x: int | str | None = None,
        y: int | str | None = None,
        state: str | None = None,
    ) -> None:
        """Set the OS browser window size, position, and/or state.

        Unlike ``Set Viewport Size``, this changes the window frame, not the
        CSS viewport.

        | =Argument= | =Description= |
        | ``width`` | Optional window width in pixels. |
        | ``height`` | Optional window height in pixels. |
        | ``x`` | Optional window X position on screen. |
        | ``y`` | Optional window Y position on screen. |
        | ``state`` | Optional window state (for example ``normal``, ``maximized``, ``minimized``, ``fullscreen``). Passed through to Vibium. |

        At least one argument is required.

        Example:
            | Set Window    width=1280    height=800
            | Set Window    x=100    y=50
            | Set Window    state=maximized
            | Set Window    width=1280    height=800    x=0    y=0
        """
        page = self.library._session.require_page()
        options: dict[str, Any] = {}
        if width is not None:
            options["width"] = EmulationKeywords._as_int("width", width)
        if height is not None:
            options["height"] = EmulationKeywords._as_int("height", height)
        if x is not None:
            options["x"] = EmulationKeywords._as_int("x", x)
        if y is not None:
            options["y"] = EmulationKeywords._as_int("y", y)
        if state is not None:
            options["state"] = state
        if not options:
            raise VibiumLibraryError(
                "Set Window requires at least one of: width, height, x, y, state."
            )
        logger.info(f"Setting window {options}.")
        page.set_window(**options)

    @keyword("Get Window Info")
    def get_window_info(self) -> dict[str, Any]:
        """Return the OS browser window size, position, and state.

        Returns:
            dict: Window info as returned by Vibium ``page.window()``.

        Example:
            | ${info}=    Get Window Info
            | Log    ${info}[width] x ${info}[height]
        """
        page = self.library._session.require_page()
        info = page.window()
        logger.info(f"Window info: {info}.")
        return dict(info)
