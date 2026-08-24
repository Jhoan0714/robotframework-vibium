"""Document/DOM injection keywords mapped to Vibium page APIs (sync)."""

from __future__ import annotations

from robot.api import logger
from robot.api.deco import keyword


class DocumentKeywords:
    """Keywords that replace or inject page document content."""

    def __init__(self, library):
        self.library = library

    @keyword("Set Page Content")
    def set_page_content(self, html: str) -> None:
        """Replace the active page HTML with ``html``.

        This does not navigate to a URL; it sets document content in place
        (Vibium ``page.set_content``).

        | =Argument= | =Description= |
        | ``html`` | Full HTML document or fragment to inject. |

        Example:
            | Set Page Content    <html><body><h1>Hello</h1></body></html>
        """
        page = self.library._session.require_page()
        preview = html if len(html) <= 60 else f"{html[:57]}..."
        logger.info(f"Setting page content ({len(html)} chars): {preview!r}.")
        page.set_content(html)
