"""Navigation-oriented keywords."""

from __future__ import annotations

from robot.api import logger
from robot.api.deco import keyword

from ..errors import BrowserSessionError


class NavigationKeywords:
    """Keywords for browser and URL navigation."""

    def __init__(self, library):
        self.library = library

    @keyword("Go To")
    def go_to(self, url: str) -> None:
        """Navigate the active page to the given URL.

        | =Argument= | =Description= |
        | ``url`` | Absolute or relative URL to open. |

        Example:
            | Go To    https://example.com
        """
        page = self.library._session.require_page()
        logger.info(f"Navigating to '{url}'.")
        page.go(url)

    @keyword("Go Back")
    def go_back(self, scope: object = None) -> None:
        """Go one step back in history for the resolved scope.

        | =Argument= | =Description= |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        logger.info("Navigating one entry back in history.")
        page.back()

    @keyword("Go Forward")
    def go_forward(self, scope: object = None) -> None:
        """Go one step forward in history for the resolved scope.

        | =Argument= | =Description= |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        logger.info("Navigating one entry forward in history.")
        page.forward()

    @keyword("Reload Page")
    def reload_page(self, scope: object = None) -> None:
        """Reload the resolved scope.

        | =Argument= | =Description= |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        logger.info("Reloading page.")
        page.reload()

    @keyword("List Pages")
    def list_pages(self, browser: object = None) -> list[str]:
        """List open browser pages as ``index: url`` strings.

        | =Argument= | =Description= |
        | ``browser`` | Optional browser handle returned by ``Open Browser``. When omitted, uses the active browser. |

        Returns:
            list[str]: All open pages. The active page is prefixed with ``*``.

        Raises:
            BrowserSessionError: If no browser is open.

        Example:
            | @{pages}=    List Pages
        """
        target_browser = self.library._session.resolve_browser(browser)
        current = self.library._session.get_active_page(browser=target_browser)
        pages = self.library._session.pages(browser=target_browser)
        result = []
        for index, page in enumerate(pages):
            marker = "*" if page.id == current.id else " "
            result.append(f"{marker}{index}: {page.url()}")
        logger.info(f"Listed {len(result)} open page(s).")
        return result

    @keyword("New Page")
    def new_page(
        self, url: str = "", context: object = None, browser: object = None
    ) -> str:
        """Create a new page/tab and set it as active.

        | =Argument= | =Description= |
        | ``url`` | Optional URL to navigate immediately after opening the page. Default is empty (stay on about:blank). |
        | ``context`` | Optional context handle. When provided, page is opened inside that context. |
        | ``browser`` | Optional browser handle returned by ``Open Browser``. When omitted, uses the active browser. |

        Returns:
            str: Current URL of the new page.

        Raises:
            BrowserSessionError: If no browser is open.

        Example:
            | ${url}=    New Page
            | ${url}=    New Page    https://robotframework.org
        """
        page = self.library._session.new_page(context=context, browser=browser)
        if url:
            logger.info(f"Opening new page and navigating to '{url}'.")
            page.go(url)
        else:
            logger.info("Opening new page.")
        return page.url()

    @keyword("Switch Page")
    def switch_page(self, page: object = None) -> None:
        """Bring the given page to the foreground.

        This keyword maps directly to Vibium ``page.bring_to_front()`` and updates
        ``session.page`` to the focused page.

        | =Argument= | =Description= |
        | ``page`` | Optional page object to focus. When omitted, uses the active page. |

        Example:
            | Switch Page    page=${page2}
        """
        target = self.library._session.resolve_scope(page)
        target.bring_to_front()
        self.library._session.set_active_page(target)
        logger.info("Brought page to front and updated active page.")

    @keyword("Close Page")
    def close_page(self, scope: object = None) -> None:
        """Close the resolved page scope.

        | =Argument= | =Description= |
        | ``scope`` | Optional page object to close. When omitted, closes the active page. |

        Note:
            This keyword delegates close semantics to Vibium. It does not perform
            extra validation about title/url availability.

        Example:
            | Close Page
            | Close Page    scope=${page2}
        """
        page = self.library._session.resolve_scope(scope)
        url = page.url()
        self.library._session.close_page(page)
        logger.info(f"Closed page '{url}'.")

    @keyword("Get Active Page")
    def get_active_page(self, browser: object = None):
        """Return the current active page scope object.

        | =Argument= | =Description= |
        | ``browser`` | Optional browser handle returned by ``Open Browser``. When omitted, uses the active browser. |

        Returns:
            object: Active page object from session.

        Example:
            | ${page}=    Get Active Page
        """
        scope = self.library._session.get_active_page(browser=browser)
        logger.info("Returning active scope object.")
        return scope

    @keyword("Get Frame")
    def get_frame(self, name_or_url: str, scope: object = None):
        """Return a child frame from the resolved scope by name or URL fragment.

        | =Argument= | =Description= |
        | ``name_or_url`` | Frame name or URL fragment accepted by Vibium ``frame(...)``. |
        | ``scope`` | Optional page/frame object where the frame lookup starts. When omitted, uses the active scope. |

        Returns:
            object: Frame object returned by Vibium.

        Raises:
            BrowserSessionError: If no frame matches ``name_or_url``.

        Example:
            | ${frame}=    Get Frame    checkout-frame    scope=${page}
        """
        frame = self.library._session.resolve_scope(scope).frame(name_or_url)
        if frame is None:
            raise BrowserSessionError(
                f"Get Frame could not find a frame matching: {name_or_url!r}"
            )
        logger.info(f"Resolved frame '{frame.url()}' from provided scope.")
        return frame

    @keyword("List Frames")
    def list_frames(
        self,
        scope: object = None,
        include_url: bool = False,
        include_title: bool = False,
    ) -> list[dict]:
        """List frames available from the resolved scope.

        | =Argument= | =Description= |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        | ``include_url`` | When ``True``, resolves ``frame.url()`` for each frame. Default ``False`` for better performance. |
        | ``include_title`` | When ``True``, resolves ``frame.title()`` for each frame. Default ``False`` for better performance. |

        Returns:
            list[dict]: Frame metadata with ``index``, ``url`` and ``title``.
            Title/url values come from Vibium and may be empty strings.

        Example:
            | @{frames}=    List Frames
            | @{frames}=    List Frames    scope=${page}
        """
        active_scope = self.library._session.resolve_scope(scope)
        frames = list(active_scope.frames())
        result = []
        for index, frame in enumerate(frames):
            frame_attributes = {
                "index": index,
                "url": frame.url() if include_url else "",
                "title": frame.title() if include_title else "",
            }
            result.append(frame_attributes)
        logger.info(f"Listed {len(result)} frame(s).")
        return result

    def _require_browser(self, browser: object = None):
        return self.library._session.resolve_browser(browser)

    @keyword("New Context")
    def new_context(self, browser: object = None):
        """Create a new browser context and make it active.

        | =Argument= | =Description= |
        | ``browser`` | Optional browser handle returned by ``Open Browser``. When omitted, uses the active browser. |
        """
        context = self.library._session.new_context(browser=browser)
        logger.info("Created new browser context.")
        return context

    @keyword("Get Active Context")
    def get_active_context(self, browser: object = None):
        """Return the active context for selected browser."""
        context = self.library._session.get_active_context(browser=browser)
        logger.info("Returning active context object.")
        return context

    @keyword("List Contexts")
    def list_contexts(self, browser: object = None) -> list[str]:
        """List known contexts for selected browser."""
        contexts = self.library._session.contexts(browser=browser)
        active = self.library._session.get_active_context(browser=browser)
        result: list[str] = []
        for index, ctx in enumerate(contexts):
            marker = (
                "*" if getattr(ctx, "id", None) == getattr(active, "id", None) else " "
            )
            result.append(f"{marker}{index}: {ctx.id}")
        logger.info(f"Listed {len(result)} context(s).")
        return result

    @keyword("Switch Context")
    def switch_context(self, context: object, browser: object = None) -> None:
        """Set context as active for selected browser."""
        self.library._session.switch_context(context=context, browser=browser)
        logger.info("Switched active context.")

    @keyword("Close Context")
    def close_context(self, context: object = None, browser: object = None) -> None:
        """Close one context and clear active page when needed."""
        self.library._session.close_context(context=context, browser=browser)
        logger.info("Closed browser context.")
