"""Shared typing aliases and small typing-related helpers for keywords / Libdoc.

Uses Vibium sync types directly. Union aliases only where a single argument
accepts more than one shape (optional ``scope=``, ``*locators``, etc.).
"""

from __future__ import annotations

from typing import Optional, Union

from vibium import Element
from vibium.sync_api import Browser, BrowserContext, Page

# Re-export for ``from rfvibium.types import Element, Page, ...``.
__all__ = [
    "Browser",
    "BrowserContext",
    "Element",
    "FindScope",
    "Locator",
    "Page",
    "PageScope",
    "UNSET",
    "UnsetType",
]


class UnsetType:
    """Sentinel for 'keyword arg was omitted' (distinct from ``None``).

    ``__repr__`` is empty so Libdoc does not show ``<object object at 0x...>``.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return ""


UNSET = UnsetType()

# Optional page/frame scope (Vibium frames are ``Page`` objects). ``None`` = active page.
PageScope = Optional[Page]

# Nested find / actions: page/frame or a parent ``Element``. ``None`` = active page.
FindScope = Optional[Union[Page, Element]]

# One ``*locators`` token: strategy string (e.g. ``css:#x``) or an element handle.
Locator = Union[Element, str]
