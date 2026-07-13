"""Dialog handling keywords."""

from __future__ import annotations

from robot.api import logger
from robot.api.deco import keyword


class DialogKeywords:
    """Keywords for browser dialogs (alert/confirm/prompt)."""

    def __init__(self, library):
        self.library = library

    @keyword("Dialog Accept")
    def dialog_accept(self, text: str = "") -> None:
        """Configure the next browser dialog to be accepted.

        | =Argument= | =Description= |
        | ``text`` | Optional prompt text used for ``prompt`` dialogs. Default is empty (accept without text). |

        Example:
            | Dialog Accept
            | Dialog Accept    my value
        """
        page = self.library._session.require_page()
        prompt_text = text if text != "" else None

        if prompt_text is None:
            logger.info("Configuring dialog handler: accept.")
            page.on_dialog("accept")
            return

        logger.info("Configuring dialog handler: accept with prompt text.")

        def _accept_with_text(dialog) -> None:
            dialog.accept(prompt_text)

        page.on_dialog(_accept_with_text)

    @keyword("Dialog Dismiss")
    def dialog_dismiss(self) -> None:
        """Configure the next browser dialog to be dismissed.

        Example:
            | Dialog Dismiss
        """
        page = self.library._session.require_page()
        logger.info("Configuring dialog handler: dismiss.")
        page.on_dialog("dismiss")
