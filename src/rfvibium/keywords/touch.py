"""Page-level touch keywords mapped to Vibium ``Page.touch`` (sync API)."""

from __future__ import annotations

from robot.api import logger
from robot.api.deco import keyword

from ..utils import coerce_viewport_axis


class TouchKeywords:
    """Low-level touch input on the active page (viewport coordinates)."""

    def __init__(self, library):
        self.library = library

    @keyword("Touch Tap", tags=["Touch", "Action"])
    def touch_tap(
        self,
        x: int | float | str | None = None,
        y: int | float | str | None = None,
    ) -> None:
        """Tap at ``(x, y)`` viewport coordinates via touch input.

        Distinct from ``Mouse Click`` (mouse path) and from element ``Tap``
        (locator/handle target).

        | =Argument= | =Description= |
        | ``x`` | Horizontal viewport coordinate (number or numeric string). |
        | ``y`` | Vertical viewport coordinate (number or numeric string). |

        Raises:
            VibiumLibraryError: If coordinates are missing or invalid.

        Example:
            | Touch Tap    120    340
            | Touch Tap    10.5    20
        """
        page = self.library._session.require_page()
        xf = coerce_viewport_axis("x", x, kind="Touch")
        yf = coerce_viewport_axis("y", y, kind="Touch")
        logger.info(f"Touch tap at ({xf}, {yf}).")
        page.touch.tap(xf, yf)
