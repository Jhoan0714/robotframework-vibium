"""Public package exports for Robot Framework import."""

from .errors import (
    BrowserSessionError,
    LocatorSyntaxError,
    ScreenshotError,
    VibiumLibraryError,
)
from .library import Vibium

__all__ = [
    "Vibium",
    "VibiumLibraryError",
    "LocatorSyntaxError",
    "BrowserSessionError",
    "ScreenshotError",
]
