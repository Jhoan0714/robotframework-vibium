"""Browser context keywords: cookies and persisted storage state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from robot.api import logger
from robot.api.deco import keyword

from .capture import _path_for_log, _resolve_capture_path


DEFAULT_STORAGE_PATTERN = "vibium-storage-{index}.json"


class CookieKeywords:
    """Keywords for reading and modifying cookies in the active browser context."""

    @keyword("List Cookies")
    def list_cookies(self, context: object = None) -> List[Dict[str, Any]]:
        """Return all cookies from the active browser context.

        | =Argument= | =Description= |
        | ``context`` | Optional context handle. When omitted, uses active context. |

        Returns:
            list[dict]: Cookie entries as returned by Vibium context API.

        Example:
            | @{cookies}=    List Cookies
        """
        ctx = _resolve_context(self._session, context)
        cookies = ctx.cookies()
        logger.info(f"Listed {len(cookies)} cookie(s).")
        return list(cookies)

    @keyword("Set Cookie")
    def set_cookie(
        self,
        name: str,
        value: str,
        url: str = "",
        domain: str = "",
        path: str = "",
        http_only: bool = False,
        secure: bool = False,
        same_site: str = "",
        expiry: Optional[int] = None,
        context: object = None,
    ) -> None:
        """Create or update a cookie in the active browser context.

        | =Argument= | =Description= |
        | ``name`` | Cookie name. |
        | ``value`` | Cookie value. |
        | ``url`` | Optional cookie URL scope. Default is empty. |
        | ``domain`` | Optional cookie domain. Used when ``url`` is empty. |
        | ``path`` | Optional cookie path. |
        | ``http_only`` | Marks cookie as HTTP-only when ``True``. |
        | ``secure`` | Marks cookie as secure when ``True``. |
        | ``same_site`` | Optional SameSite policy (for example ``Lax``, ``Strict``, ``None``). |
        | ``expiry`` | Optional Unix expiry timestamp. |
        | ``context`` | Optional context handle. When omitted, uses active context. |

        Note:
            When both ``url`` and ``domain`` are omitted, this keyword uses the
            current page URL as scope.

        Example:
            | Set Cookie    session_id    abc123
            | Set Cookie    pref_theme    dark    domain=example.com    path=/
        """
        ctx = _resolve_context(self._session, context)
        page = _page_for_context(self._session, ctx)

        cookie: Dict[str, Any] = {
            "name": name,
            "value": value,
            "url": url or (None if domain else page.url()),
            "domain": None if url else (domain or None),
            "path": path or None,
            "httpOnly": http_only or None,
            "secure": secure or None,
            "sameSite": same_site or None,
            "expiry": expiry,
        }

        cookie = {k: v for k, v in cookie.items() if v is not None}

        logger.info(f"Setting cookie '{name}'.")
        ctx.set_cookies([cookie])

    @keyword("Clear Cookies")
    def clear_cookies(self, context: object = None) -> None:
        """Remove all cookies from the active browser context.

        | =Argument= | =Description= |
        | ``context`` | Optional context handle. When omitted, uses active context. |

        Example:
            | Clear Cookies
        """
        ctx = _resolve_context(self._session, context)
        logger.info("Clearing all cookies.")
        ctx.clear_cookies()


class StorageKeywords:
    """Keywords for exporting and restoring browser storage state."""

    @keyword("Export Storage State")
    def export_storage_state(
        self,
        output_path: Optional[str] = None,
        embed: bool = True,
        context: object = None,
    ) -> str:
        """Export cookies and storage data to a JSON file.

        | =Argument= | =Description= |
        | ``output_path`` | Optional output file path. When omitted, an auto-numbered file is created under ``media/``. |
        | ``embed`` | When ``True`` (default), logs an HTML link to the artifact. |
        | ``context`` | Optional context handle. When omitted, uses active context. |

        Returns:
            str: Absolute path of the generated JSON file.

        Example:
            | ${state}=    Export Storage State
            | ${state}=    Export Storage State    output_path=state.json
        """
        ctx = _resolve_context(self._session, context)
        state = ctx.storage()

        path = (
            _next_auto_storage_path()
            if output_path is None
            else _resolve_capture_path(output_path)
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")

        logger.info(f"Exported storage state to '{path}'.")
        if embed:
            self._log_storage_artifact(path)
        return str(path)

    @keyword("Restore Storage State")
    def restore_storage_state(self, path: str, context: object = None) -> None:
        """Restore cookies and storage data from a JSON state file.

        | =Argument= | =Description= |
        | ``path`` | Path to a JSON file previously generated by ``Export Storage State``. |
        | ``context`` | Optional context handle. When omitted, uses active context. |

        Example:
            | Restore Storage State    state.json
        """
        ctx = _resolve_context(self._session, context)

        resolved = _resolve_capture_path(path)
        raw = resolved.read_text(encoding="utf-8")
        state = json.loads(raw)
        logger.info(f"Restoring storage state from '{resolved}'.")
        ctx.set_storage(state)

    @staticmethod
    def _log_storage_artifact(path: Path) -> None:
        href = _path_for_log(path)
        name = path.name
        html = f'<a href="{href}" target="_blank">Open storage state: {name}</a>'
        logger.info(html, html=True)


def _next_auto_storage_path() -> Path:
    index = 1
    while True:
        candidate = _resolve_capture_path(DEFAULT_STORAGE_PATTERN.format(index=index))
        if not candidate.exists():
            return candidate
        index += 1


def _resolve_context(session: object, context: object = None):
    if hasattr(session, "resolve_context"):
        return session.resolve_context(context=context)
    page = session.require_page()
    return page.context if context is None else context


def _page_for_context(session: object, context: object):
    if hasattr(session, "get_active_page_for_context"):
        return session.get_active_page_for_context(context)
    return session.require_page()
