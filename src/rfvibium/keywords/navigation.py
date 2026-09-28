"""Navigation-oriented keywords."""

from __future__ import annotations

from typing import Optional

from robot.api import logger
from robot.api.deco import keyword

from ..errors import BrowserSessionError
from ..types import Browser, BrowserContext, Page, PageScope


class NavigationKeywords:
    """Keywords for browser and URL navigation."""

    def __init__(self, library):
        self.library = library

    @keyword("Go To", tags=["Page", "Action"])
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

    @keyword("Go Back", tags=["Page", "Action"])
    def go_back(self, scope: PageScope = None) -> None:
        """Go one step back in history for the resolved scope.

        | =Argument= | =Description= |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Example:
            | Go Back
            | Go Back    scope=${page}
        """
        page = self.library._session.resolve_scope(scope)
        logger.info("Navigating one entry back in history.")
        page.back()

    @keyword("Go Forward", tags=["Page", "Action"])
    def go_forward(self, scope: PageScope = None) -> None:
        """Go one step forward in history for the resolved scope.

        | =Argument= | =Description= |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Example:
            | Go Forward
            | Go Forward    scope=${page}
        """
        page = self.library._session.resolve_scope(scope)
        logger.info("Navigating one entry forward in history.")
        page.forward()

    @keyword("Reload", tags=["Page", "Action"])
    def reload(self, scope: PageScope = None) -> None:
        """Reload the resolved scope.

        | =Argument= | =Description= |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Example:
            | Reload
            | Reload    scope=${page}
        """
        page = self.library._session.resolve_scope(scope)
        logger.info("Reloading page.")
        page.reload()

    @keyword("List Pages", tags=["Browser", "Getter"])
    def list_pages(self, browser: Optional[Browser] = None) -> list[str]:
        """List open browser pages as ``index: url`` strings.

        The active page is prefixed with ``*``.

        | =Argument= | =Description= |
        | ``browser`` | Optional browser handle returned by ``Open Browser``. When omitted, uses the active browser. |

        Note:
            Raises ``BrowserSessionError`` if no browser is open.

        Returns:
            Open pages as ``index: url`` strings. The active page is prefixed with ``*``.

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

    @keyword("New Page", tags=["Browser", "Action"])
    def new_page(
        self,
        url: str = "",
        context: Optional[BrowserContext] = None,
        browser: Optional[Browser] = None,
    ) -> str:
        """Create a new page/tab and set it as active.

        | =Argument= | =Description= |
        | ``url`` | Optional URL to navigate immediately after opening the page. Default is empty (stay on about:blank). |
        | ``context`` | Optional context handle. When provided, page is opened inside that context. |
        | ``browser`` | Optional browser handle returned by ``Open Browser``. When omitted, uses the active browser. |

        Note:
            Raises ``BrowserSessionError`` if no browser is open.

        Returns:
            Current URL of the new page.

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

    @keyword("Switch Page", tags=["Page", "Action"])
    def switch_page(self, page: Optional[Page] = None) -> None:
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

    @keyword("Close Page", tags=["Page", "Action"])
    def close_page(self, scope: PageScope = None) -> None:
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

    @keyword("Get Active Page", tags=["Browser", "Getter"])
    def get_active_page(self, browser: Optional[Browser] = None) -> Page:
        """Return the current active page scope object.

        | =Argument= | =Description= |
        | ``browser`` | Optional browser handle returned by ``Open Browser``. When omitted, uses the active browser. |

        Returns:
            Active page object for the selected browser.

        Example:
            | ${page}=    Get Active Page
        """
        scope = self.library._session.get_active_page(browser=browser)
        logger.info("Returning active scope object.")
        return scope

    @keyword("Get Frame", tags=["Page", "Getter"])
    def get_frame(self, name_or_url: str, scope: PageScope = None) -> Page:
        """Return a child frame handle from the resolved scope by name or URL fragment.

        The handle can be passed as ``scope=`` to other keywords.

        | =Argument= | =Description= |
        | ``name_or_url`` | Frame name or URL fragment accepted by Vibium ``frame(...)``. |
        | ``scope`` | Optional page/frame object where the frame lookup starts. When omitted, uses the active scope. |

        Note:
            Raises ``BrowserSessionError`` if no frame matches ``name_or_url``.

        Returns:
            Child frame handle usable as ``scope=`` in other keywords.

        Example:
            | ${frame}=    Get Frame    checkout-frame    scope=${page}
            | ${text}=    Get Text    css:h1    scope=${frame}
        """
        frame = self.library._session.resolve_scope(scope).frame(name_or_url)
        if frame is None:
            raise BrowserSessionError(
                f"Get Frame could not find a frame matching: {name_or_url!r}"
            )
        logger.info(f"Resolved frame '{frame.url()}' from provided scope.")
        return frame

    @keyword("List Frames", tags=["Page", "Getter"])
    def list_frames(
        self,
        scope: PageScope = None,
        include_url: bool = False,
        include_title: bool = False,
    ) -> list[dict]:
        """List frames available from the resolved scope.

        Each entry has ``index``, ``url``, and ``title``. Title/url values come
        from Vibium and may be empty strings when not requested or unavailable.

        | =Argument= | =Description= |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        | ``include_url`` | When ``True``, resolves ``frame.url()`` for each frame. Default ``False`` for better performance. |
        | ``include_title`` | When ``True``, resolves ``frame.title()`` for each frame. Default ``False`` for better performance. |

        Returns:
            Frame metadata dicts with ``index``, ``url``, and ``title`` (url/title may be empty).

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

    def _require_browser(self, browser: Optional[Browser] = None):
        return self.library._session.resolve_browser(browser)

    @keyword("New Context", tags=["BrowserContext", "Action"])
    def new_context(self, browser: Optional[Browser] = None) -> BrowserContext:
        """Create a new browser context and make it active.

        | =Argument= | =Description= |
        | ``browser`` | Optional browser handle returned by ``Open Browser``. When omitted, uses the active browser. |

        Returns:
            Newly created browser context handle.

        Example:
            | ${ctx}=    New Context
            | ${ctx}=    New Context    browser=${browser}
        """
        context = self.library._session.new_context(browser=browser)
        logger.info("Created new browser context.")
        return context

    @keyword("Get Active Context", tags=["BrowserContext", "Getter"])
    def get_active_context(self, browser: Optional[Browser] = None) -> BrowserContext:
        """Return the active context for the selected browser.

        | =Argument= | =Description= |
        | ``browser`` | Optional browser handle returned by ``Open Browser``. When omitted, uses the active browser. |

        Returns:
            Active context handle for the selected browser.

        Example:
            | ${ctx}=    Get Active Context
            | ${ctx}=    Get Active Context    browser=${browser}
        """
        context = self.library._session.get_active_context(browser=browser)
        logger.info("Returning active context object.")
        return context

    @keyword("List Contexts", tags=["BrowserContext", "Getter"])
    def list_contexts(self, browser: Optional[Browser] = None) -> list[str]:
        """List known contexts for the selected browser as ``index: id`` strings.

        The active context is prefixed with ``*``.

        | =Argument= | =Description= |
        | ``browser`` | Optional browser handle returned by ``Open Browser``. When omitted, uses the active browser. |

        Returns:
            Contexts as ``index: id`` strings. The active context is prefixed with ``*``.

        Example:
            | @{contexts}=    List Contexts
            | @{contexts}=    List Contexts    browser=${browser}
        """
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

    @keyword("Switch Context", tags=["BrowserContext", "Action"])
    def switch_context(
        self, context: BrowserContext, browser: Optional[Browser] = None
    ) -> None:
        """Set the given context as active for the selected browser.

        | =Argument= | =Description= |
        | ``context`` | Context handle to activate (for example from ``New Context`` or ``Get Active Context``). |
        | ``browser`` | Optional browser handle returned by ``Open Browser``. When omitted, uses the active browser. |

        Example:
            | ${ctx}=    New Context
            | Switch Context    ${ctx}
        """
        self.library._session.switch_context(context=context, browser=browser)
        logger.info("Switched active context.")

    @keyword("Close Context", tags=["BrowserContext", "Action"])
    def close_context(
        self,
        context: Optional[BrowserContext] = None,
        browser: Optional[Browser] = None,
    ) -> None:
        """Close one context and clear the active page when needed.

        | =Argument= | =Description= |
        | ``context`` | Optional context handle to close. When omitted, closes the active context. |
        | ``browser`` | Optional browser handle returned by ``Open Browser``. When omitted, uses the active browser. |

        Example:
            | Close Context
            | ${ctx}=    New Context
            | Close Context    context=${ctx}
        """
        self.library._session.close_context(context=context, browser=browser)
        logger.info("Closed browser context.")
