"""Page-level mouse keywords mapped to Vibium ``Page.mouse`` (sync API)."""

from __future__ import annotations

from typing import Optional, Union

from robot.api import logger
from robot.api.deco import keyword

from ..errors import VibiumLibraryError


class MouseKeywords:
    """Low-level mouse input on the active page (viewport coordinates)."""

    @staticmethod
    def _coerce_axis(name: str, value: object) -> float:
        if value is None:
            raise VibiumLibraryError(
                f"Mouse {name} must be a number (viewport pixels); got none/omitted."
            )
        if isinstance(value, bool):
            raise VibiumLibraryError(
                f"Mouse {name} must be a number, not a boolean ({value!r})."
            )
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                raise VibiumLibraryError(f"Mouse {name} cannot be an empty string.")
            try:
                return float(raw)
            except ValueError as exc:
                raise VibiumLibraryError(
                    f"Mouse {name} must be a number, got {value!r}."
                ) from exc
        raise VibiumLibraryError(
            f"Mouse {name} must be a number, got {type(value).__name__}: {value!r}."
        )

    @staticmethod
    def _normalize_button(button: object) -> int:
        if isinstance(button, bool):
            raise VibiumLibraryError(
                f"Mouse button must be an integer 0, 1, or 2, not boolean ({button!r})."
            )
        if isinstance(button, int):
            value = button
        elif isinstance(button, str):
            raw = button.strip()
            if not raw:
                raise VibiumLibraryError("Mouse button cannot be an empty string.")
            try:
                value = int(raw, 10)
            except ValueError as exc:
                raise VibiumLibraryError(
                    f"Mouse button must be 0, 1, or 2, got {button!r}."
                ) from exc
        else:
            raise VibiumLibraryError(
                "Mouse button must be an integer 0, 1, or 2, "
                f"got {type(button).__name__}: {button!r}."
            )
        if value not in (0, 1, 2):
            raise VibiumLibraryError(
                f"Mouse button must be 0 (left), 1 (middle), or 2 (right); got {value}."
            )
        return value

    @staticmethod
    def _assert_default_button(button: int) -> None:
        """Vibium sync mouse helpers do not take a button id (except implicit left)."""
        if button != 0:
            raise VibiumLibraryError(
                "Non-default mouse buttons are not supported by the current "
                "Vibium Python sync API: `page.mouse.click`, `page.mouse.down()`, "
                "and `page.mouse.up()` do not accept a button parameter. "
                "Use `button=0` (or omit it)."
            )

    @keyword("Mouse Click")
    def mouse_click(
        self,
        x: Optional[Union[int, float, str]] = None,
        y: Optional[Union[int, float, str]] = None,
        button: Union[int, str] = 0,
    ) -> None:
        """Click at ``(x, y)`` viewport coordinates.

        | =Argument= | =Description= |
        | ``x`` | Horizontal viewport coordinate (number or numeric string). |
        | ``y`` | Vertical viewport coordinate (number or numeric string). |
        | ``button`` | Mouse button id. Default is ``0`` (left). |

        Note:
            Current Vibium sync mouse API only supports left button behavior for
            this keyword.

        Raises:
            VibiumLibraryError: If coordinates are missing/invalid or button is not
            supported.

        Example:
            | Mouse Click    120    340
            | Mouse Click    10    20    button=0
        """
        page = self._session.require_page()
        btn = MouseKeywords._normalize_button(button)
        MouseKeywords._assert_default_button(btn)

        xf = MouseKeywords._coerce_axis("x", x)
        yf = MouseKeywords._coerce_axis("y", y)
        logger.info(f"Mouse click at ({xf}, {yf}) (button={btn}).")
        page.mouse.click(xf, yf)

    @keyword("Mouse Move")
    def mouse_move(self, x: Union[int, float, str], y: Union[int, float, str]) -> None:
        """Move mouse pointer to ``(x, y)`` viewport coordinates.

        | =Argument= | =Description= |
        | ``x`` | Horizontal viewport coordinate (number or numeric string). |
        | ``y`` | Vertical viewport coordinate (number or numeric string). |

        Raises:
            VibiumLibraryError: If coordinate values are invalid.

        Example:
            | Mouse Move    100    200
        """
        page = self._session.require_page()
        xf = MouseKeywords._coerce_axis("x", x)
        yf = MouseKeywords._coerce_axis("y", y)
        logger.info(f"Mouse move to ({xf}, {yf}).")
        page.mouse.move(xf, yf)

    @keyword("Mouse Down")
    def mouse_down(self, button: Union[int, str] = 0) -> None:
        """Press mouse button down.

        | =Argument= | =Description= |
        | ``button`` | Mouse button id. Default is ``0`` (left). |

        Note:
            Current Vibium sync mouse API only supports left button behavior for
            this keyword.

        Raises:
            VibiumLibraryError: If button is invalid or unsupported.

        Example:
            | Mouse Down
            | Mouse Down    button=0
        """
        page = self._session.require_page()
        btn = MouseKeywords._normalize_button(button)
        MouseKeywords._assert_default_button(btn)
        logger.info("Mouse button down (left).")
        page.mouse.down()

    @keyword("Mouse Up")
    def mouse_up(self, button: Union[int, str] = 0) -> None:
        """Release mouse button.

        | =Argument= | =Description= |
        | ``button`` | Mouse button id. Default is ``0`` (left). |

        Note:
            Current Vibium sync mouse API only supports left button behavior for
            this keyword.

        Raises:
            VibiumLibraryError: If button is invalid or unsupported.

        Example:
            | Mouse Up
            | Mouse Up    button=0
        """
        page = self._session.require_page()
        btn = MouseKeywords._normalize_button(button)
        MouseKeywords._assert_default_button(btn)
        logger.info("Mouse button up (left).")
        page.mouse.up()
