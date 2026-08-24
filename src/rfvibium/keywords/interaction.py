"""Interaction keywords aligned to Vibium's ``Page.find`` + ``Element`` API.

Public contract:

- ``Click`` / ``Find Element`` accept one or more locator tokens;
  each token uses ``strategy:value`` syntax or a plain CSS selector. Tokens
  are merged into a single ``page.find(...)`` call.
- ``Fill Text`` additionally accepts a value. Two usage modes:
    1. Ergonomic (value as last positional).
    2. Explicit (``value=...`` as Robot Framework keyword argument).
  The ergonomic mode is refused when the last positional looks like a locator
  (starts with a known ``strategy:`` prefix); the user must then use
  ``value=...`` to disambiguate.
- ``Upload Files`` resolves ``*locators`` like other interaction keywords and
  requires file paths via the keyword-only argument ``files=`` (a string or a
  list/tuple of strings).
- ``Drag And Drop`` resolves a **source** element and a **target** element
  (each as one locator token or a list/tuple of tokens) and calls
  ``source.drag_to(target)``.
"""

from __future__ import annotations

import json
from typing import Any

from robot.api import logger
from robot.api.deco import keyword

from ..errors import LocatorSyntaxError
from ..locator import (
    format_locators,
    looks_like_locator,
    merge_locators,
    resolve_required_locators,
)
from ..utils import parse_timeout_ms

_UNSET = object()


class InteractionKeywords:
    """Keywords for user-like interactions."""

    def __init__(self, library):
        self.library = library

    @keyword("Map Elements")
    def map_elements(self, scope: object = None) -> str:
        """Return accessibility tree information for the resolved scope.

            | =Argument= | =Description= |
            | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

            Returns:
        str: Accessibility tree as a string representation.

            Example:
                | ${tree}=    Map Elements
                | ${tree}=    Map Elements    scope=${frame}
        """
        page = self.library._session.resolve_scope(scope)
        return str(page.a11y_tree())

    @keyword("Click")
    def click(self, *locators: str, scope: object = None) -> None:
        """Click the element resolved from locator token(s).

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens merged into one ``page.find(...)`` call. Supports ``strategy:value`` tokens (for example ``role:``, ``text:``, ``label:``, ``xpath:``) and plain CSS selectors. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |


                Example:
                    | Click    role:button    text:Log in
                    | Click    css:.submit
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Clicking element '{format_locators(locators)}'.")
        page.find(*args, **kwargs).click()

    @keyword("Find Element")
    def find_element(self, *locators: str, scope: object = None) -> str:
        """Resolve locator token(s) and return a human-readable element representation.

            | =Argument= | =Description= |
            | ``*locators`` | Locator tokens merged into one ``page.find(...)`` call. |
            | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

            Returns:
        str: ``repr`` string for the matched element.

            Example:
                | ${el}=    Find Element    role:textbox    label:E-mail
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Finding element '{format_locators(locators)}'.")
        return repr(page.find(*args, **kwargs))

    @keyword("Get Text")
    def get_text(self, *locators: str, scope: object = None) -> str:
        """Return ``element.text()`` for the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |


                Returns:
                    str: Element text.
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Reading text from element '{format_locators(locators)}'.")
        return page.find(*args, **kwargs).text()

    @keyword("Get Inner Text")
    def get_inner_text(self, *locators: str, scope: object = None) -> str:
        """Return ``element.inner_text()`` for the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Reading inner text from element '{format_locators(locators)}'.")
        return page.find(*args, **kwargs).inner_text()

    @keyword("Get Value")
    def get_value(self, *locators: str, scope: object = None) -> str:
        """Return ``element.value()`` for the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single form element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Reading value from element '{format_locators(locators)}'.")
        return page.find(*args, **kwargs).value()

    @keyword("Get Attribute")
    def get_attribute(
        self, name: str, *locators: str, scope: object = None
    ) -> str | None:
        """Return an attribute value from the matched element.

        | =Argument= | =Description= |
        | ``name`` | Attribute name to read. |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Returns:
            str | None: Attribute value or ``None`` when attribute is absent.
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(
            f"Reading attribute '{name}' from element '{format_locators(locators)}'."
        )
        return page.find(*args, **kwargs).attr(name)

    @keyword("Get Bounds")
    def get_bounds(self, *locators: str, scope: object = None) -> object:
        """Return ``element.bounds()`` for the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Reading bounds from element '{format_locators(locators)}'.")
        return page.find(*args, **kwargs).bounds()

    @keyword("Element Is Visible")
    def element_is_visible(self, *locators: str, scope: object = None) -> bool:
        """Check whether the matched element is visible.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Checking visibility of element '{format_locators(locators)}'.")
        return page.find(*args, **kwargs).is_visible()

    @keyword("Element Is Hidden")
    def element_is_hidden(self, *locators: str, scope: object = None) -> bool:
        """Check whether the matched element is hidden.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Checking hidden state of element '{format_locators(locators)}'.")
        return page.find(*args, **kwargs).is_hidden()

    @keyword("Element Is Enabled")
    def element_is_enabled(self, *locators: str, scope: object = None) -> bool:
        """Check whether the matched element is enabled.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Checking enabled state of element '{format_locators(locators)}'.")
        return page.find(*args, **kwargs).is_enabled()

    @keyword("Element Is Checked")
    def element_is_checked(self, *locators: str, scope: object = None) -> bool:
        """Check whether the matched element is checked.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Checking checked state of element '{format_locators(locators)}'.")
        return page.find(*args, **kwargs).is_checked()

    @keyword("Element Is Editable")
    def element_is_editable(self, *locators: str, scope: object = None) -> bool:
        """Check whether the matched element is editable.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(
            f"Checking editable state of element '{format_locators(locators)}'."
        )
        return page.find(*args, **kwargs).is_editable()

    @keyword("Get Role")
    def get_role(self, *locators: str, scope: object = None) -> str:
        """Return semantic role for the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Reading role of element '{format_locators(locators)}'.")
        return page.find(*args, **kwargs).role()

    @keyword("Get Label")
    def get_label(self, *locators: str, scope: object = None) -> str:
        """Return accessible label for the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Reading label of element '{format_locators(locators)}'.")
        return page.find(*args, **kwargs).label()

    @keyword("Fill Text")
    def fill_text(
        self,
        *locators: str,
        value: object = _UNSET,
        secret: bool = False,
        scope: object = None,
    ) -> None:
        """Fill the matched element, replacing existing content.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens plus optional trailing value (ergonomic mode). |
        | ``value`` | Explicit value to type. When provided, all positional arguments are treated as locators. |
        | ``secret`` | When ``True``, masks typed value in logs as ``***``. Default is ``False``. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Note:
            The ergonomic form requires at least one locator and one trailing value.
            If the trailing value looks like a locator token, pass it with ``value=``.

        Example:
            | Fill Text    role:textbox    label:E-mail    user@example.com
            | Fill Text    role:textbox    label:Password    value=s3cret    secret=${TRUE}
        """
        page = self.library._session.resolve_scope(scope)
        locator_tokens, final_value = self._resolve_fill_arguments(locators, value)
        args, kwargs = resolve_required_locators(locator_tokens)
        display_value = "***" if secret else repr(final_value)
        logger.info(
            f"Typing text {display_value} into element "
            f"'{format_locators(locator_tokens)}'."
        )
        page.find(*args, **kwargs).fill(final_value)

    @keyword("Press Keys")
    def press_keys(self, key: str, *locators: str, scope: object = None) -> None:
        """Press a key or combo on the matched element.

        Page-level keystrokes (no locator) use ``Keyboard Key    press``.

        | =Argument= | =Description= |
        | ``key`` | Keyboard key or combo supported by Vibium (for example ``Enter``, ``Control+a``). |
        | ``*locators`` | Locator tokens to resolve a single element. At least one is required. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Example:
            | Press Keys    Enter    role:textbox    label:Search
            | Press Keys    Control+a    css:#editor
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Pressing key '{key}' on element '{format_locators(locators)}'.")
        page.find(*args, **kwargs).press(key)

    @keyword("Double Click")
    def double_click(self, *locators: str, scope: object = None) -> None:
        """Double-click the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Double-clicking element '{format_locators(locators)}'.")
        page.find(*args, **kwargs).dblclick()

    @keyword("Hover")
    def hover(self, *locators: str, scope: object = None) -> None:
        """Hover the mouse pointer over the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Hovering element '{format_locators(locators)}'.")
        page.find(*args, **kwargs).hover()

    @keyword("Focus")
    def focus(self, *locators: str, scope: object = None) -> None:
        """Set focus on the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Focusing element '{format_locators(locators)}'.")
        page.find(*args, **kwargs).focus()

    @keyword("Clear Text")
    def clear_text(self, *locators: str, scope: object = None) -> None:
        """Clear the value of the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Clearing element '{format_locators(locators)}'.")
        page.find(*args, **kwargs).clear()

    @keyword("Type Text")
    def type_text(
        self,
        *locators: str,
        text: object = _UNSET,
        secret: bool = False,
        scope: object = None,
    ) -> None:
        """Type text into the matched element in append mode.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens plus optional trailing text (ergonomic mode). |
        | ``text`` | Explicit text to type. When provided, all positional arguments are treated as locators. |
        | ``secret`` | When ``True``, masks typed text in logs as ``***``. Default is ``False``. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        locator_tokens, final_text = self._resolve_tail_value_arguments(
            keyword_name="Type Text",
            positional=locators,
            explicit=text,
            explicit_name="text",
        )
        args, kwargs = resolve_required_locators(locator_tokens)
        display_value = "***" if secret else repr(final_text)
        logger.info(
            f"Typing text {display_value} into element "
            f"'{format_locators(locator_tokens)}' (append mode)."
        )
        page.find(*args, **kwargs).type(final_text)

    @keyword("Select Option")
    def select_option(
        self, *locators: str, value: object = _UNSET, scope: object = None
    ) -> None:
        """Select an option value in a matched ``<select>`` element.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens plus optional trailing option value. |
        | ``value`` | Explicit option value to select. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        locator_tokens, option_value = self._resolve_tail_value_arguments(
            keyword_name="Select Option",
            positional=locators,
            explicit=value,
            explicit_name="value",
        )
        args, kwargs = resolve_required_locators(locator_tokens)
        logger.info(
            f"Selecting option {repr(option_value)} in element "
            f"'{format_locators(locator_tokens)}'."
        )
        page.find(*args, **kwargs).select_option(option_value)

    @keyword("Check")
    def check(self, *locators: str, scope: object = None) -> None:
        """Check a matched checkbox or radio control.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Checking element '{format_locators(locators)}'.")
        page.find(*args, **kwargs).check()

    @keyword("Uncheck")
    def uncheck(self, *locators: str, scope: object = None) -> None:
        """Uncheck a matched checkbox control.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Unchecking element '{format_locators(locators)}'.")
        page.find(*args, **kwargs).uncheck()

    @keyword("Scroll Into View")
    def scroll_into_view(self, *locators: str, scope: object = None) -> None:
        """Scroll until the matched element is in view.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Scrolling element into view '{format_locators(locators)}'.")
        page.find(*args, **kwargs).scroll_into_view()

    @keyword("Scroll")
    def scroll(
        self,
        direction: str = "down",
        amount: int = 3,
        *locators: str,
        scope: object = None,
    ) -> None:
        """Scroll the page or a CSS container selector.

            | =Argument= | =Description= |
            | ``direction`` | Scroll direction accepted by Vibium. Default is ``down``. |
            | ``amount`` | Scroll amount/steps. Default is ``3``. |
            | ``*locators`` | Optional single CSS selector limiting scroll container. |
            | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

            Raises:
        LocatorSyntaxError: If non-CSS locator axes are used for scoped scroll.

            Example:
                | Scroll
                | Scroll    up    2
                | Scroll    down    3    .panel
        """
        page = self.library._session.resolve_scope(scope)
        selector = self._resolve_scroll_selector(locators)
        if selector:
            logger.info(
                f"Scrolling direction='{direction}' amount={amount} "
                f"within selector '{selector}'."
            )
        else:
            logger.info(f"Scrolling direction='{direction}' amount={amount}.")
        page.scroll(direction=direction, amount=amount, selector=selector)

    @keyword("Dispatch Event")
    def dispatch_event(
        self,
        *locators: str,
        event: str,
        event_init: object = None,
        scope: object = None,
    ) -> None:
        """Dispatch a DOM event on the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens to resolve a single element. |
        | ``event`` | Event name to dispatch (for example ``click`` or ``change``). |
        | ``event_init`` | Optional event init payload as dict or JSON object string. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |


                Raises:
                    LocatorSyntaxError: If ``event_init`` is invalid JSON/object shape.
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        init_payload = self._coerce_event_init(event_init)
        logger.info(
            f"Dispatching event '{event}' on element '{format_locators(locators)}'."
        )
        page.find(*args, **kwargs).dispatch_event(event, init_payload)

    @keyword("Upload Files")
    def upload_files(self, *locators: str, files: object, scope: object = None) -> None:
        """Upload one or more files into a matched file input.

            | =Argument= | =Description= |
            | ``*locators`` | Locator tokens to resolve a single file input element. |
            | ``files`` | File path string or list/tuple of path strings. |
            | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

            Raises:
        LocatorSyntaxError: If file paths are empty/invalid.

            Example:
                | Upload Files    css:input[type='file']    files=/tmp/a.pdf
                | Upload Files    xpath://input[@type='file']    files=@{LIST}
        """
        page = self.library._session.resolve_scope(scope)
        file_paths = InteractionKeywords._coerce_upload_files(files)
        args, kwargs = resolve_required_locators(locators)
        logger.info(
            f"Uploading {len(file_paths)} file(s) to element "
            f"'{format_locators(locators)}'."
        )
        page.find(*args, **kwargs).set_files(file_paths)

    @keyword("Drag And Drop")
    def drag_and_drop(
        self,
        source: object,
        target: object,
        timeout: str | None = None,
        scope: object = None,
    ) -> None:
        """Drag one resolved element to another.

        | =Argument= | =Description= |
        | ``source`` | Source locator token string or list/tuple of locator tokens. |
        | ``target`` | Target locator token string or list/tuple of locator tokens. |
        | ``timeout`` | Optional Robot timeout string for drag action. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |


                Raises:
                    LocatorSyntaxError: If source/target locator shapes are invalid.

                Example:
                    | Drag And Drop    css:#src    css:#tgt
                    | Drag And Drop    source=@{SRC}    target=@{TGT}    timeout=10s
        """
        page = self.library._session.resolve_scope(scope)
        src_tokens = InteractionKeywords._coerce_locator_token_group("source", source)
        tgt_tokens = InteractionKeywords._coerce_locator_token_group("target", target)
        src_args, src_kwargs = resolve_required_locators(src_tokens)
        tgt_args, tgt_kwargs = resolve_required_locators(tgt_tokens)
        timeout_ms: int | None = None
        if timeout is not None and str(timeout).strip():
            timeout_ms = parse_timeout_ms(str(timeout))

        logger.info(
            f"Dragging from '{format_locators(src_tokens)}' "
            f"to '{format_locators(tgt_tokens)}'."
        )
        source_el = page.find(*src_args, **src_kwargs)
        target_el = page.find(*tgt_args, **tgt_kwargs)
        source_el.drag_to(target_el, timeout=timeout_ms)

    @staticmethod
    def _resolve_fill_arguments(locators, value):
        return InteractionKeywords._resolve_tail_value_arguments(
            keyword_name="Fill Text",
            positional=locators,
            explicit=value,
            explicit_name="value",
        )

    @staticmethod
    def _resolve_tail_value_arguments(
        keyword_name, positional, explicit, explicit_name
    ):
        if explicit is not _UNSET:
            if not positional:
                raise LocatorSyntaxError(
                    f"{keyword_name} requires at least one locator before "
                    f"'{explicit_name}='."
                )
            return tuple(positional), explicit

        if len(positional) < 2:
            raise LocatorSyntaxError(
                f"{keyword_name} requires at least one locator and a {explicit_name}. "
                f"Pass the {explicit_name} as the last argument or as "
                f"'{explicit_name}=...'."
            )

        candidate = positional[-1]
        if looks_like_locator(candidate):
            prefix = candidate.strip().split(":", 1)[0]
            raise LocatorSyntaxError(
                f"{keyword_name}: the last argument '{candidate}' looks like a "
                f"locator (prefix '{prefix}:'), not a value. "
                f"Pass the {explicit_name} explicitly with "
                f"'{explicit_name}=...' to disambiguate."
            )

        return tuple(positional[:-1]), candidate

    @staticmethod
    def _coerce_locator_token_group(side: str, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise LocatorSyntaxError(
                    f"Drag And Drop: {side} locator cannot be an empty string."
                )
            return (stripped,)
        if isinstance(value, (list, tuple)):
            if not value:
                raise LocatorSyntaxError(
                    f"Drag And Drop: {side} must contain at least one locator token."
                )
            out: list[str] = []
            for index, item in enumerate(value):
                if not isinstance(item, str):
                    raise LocatorSyntaxError(
                        f"Drag And Drop: each {side} locator token must be a string, "
                        f"got {type(item).__name__} at index {index}."
                    )
                piece = item.strip()
                if not piece:
                    raise LocatorSyntaxError(
                        f"Drag And Drop: empty {side} locator token at index {index}."
                    )
                out.append(piece)
            return tuple(out)
        raise LocatorSyntaxError(
            f"Drag And Drop: {side} must be a string or a list/tuple of strings, "
            f"got {type(value).__name__}."
        )

    @staticmethod
    def _coerce_upload_files(files: object) -> list[str]:
        if isinstance(files, str):
            stripped = files.strip()
            if not stripped:
                raise LocatorSyntaxError(
                    "Upload Files: 'files' cannot be an empty string."
                )
            return [stripped]

        if isinstance(files, (list, tuple)):
            if not files:
                raise LocatorSyntaxError(
                    "Upload Files: 'files' cannot be an empty list."
                )
            out: list[str] = []
            for index, item in enumerate(files):
                if not isinstance(item, str):
                    raise LocatorSyntaxError(
                        "Upload Files: each entry in 'files' must be a string, "
                        f"got {type(item).__name__} at index {index}."
                    )
                piece = item.strip()
                if not piece:
                    raise LocatorSyntaxError(
                        f"Upload Files: empty string in 'files' at index {index}."
                    )
                out.append(piece)
            return out

        raise LocatorSyntaxError(
            "Upload Files: 'files' must be a string or a list/tuple of strings, "
            f"got {type(files).__name__}."
        )

    @staticmethod
    def _coerce_event_init(event_init: object) -> Any:
        if event_init is None:
            return None
        if isinstance(event_init, str):
            raw = event_init.strip()
            if not raw:
                return None
            try:
                decoded = json.loads(raw)
            except ValueError as exc:
                raise LocatorSyntaxError(
                    "Dispatch Event: 'event_init' must be valid JSON when passed "
                    f"as a string. Received: {event_init!r}"
                ) from exc
            if not isinstance(decoded, dict):
                raise LocatorSyntaxError(
                    "Dispatch Event: 'event_init' JSON must decode to an object."
                )
            return decoded
        if isinstance(event_init, dict):
            return event_init
        raise LocatorSyntaxError(
            "Dispatch Event: 'event_init' must be a dict, JSON object string, "
            "or omitted."
        )

    @staticmethod
    def _resolve_scroll_selector(locators):
        if not locators:
            return None

        args, kwargs = merge_locators(locators)
        if kwargs:
            raise LocatorSyntaxError(
                "Scroll only accepts a CSS selector when scoped "
                "(e.g. Scroll    down    3    .panel). "
                "Semantic axes like role:/xpath: are not supported by page.scroll."
            )
        if len(args) != 1:
            raise LocatorSyntaxError(
                "Scroll accepts at most one CSS selector when scoped."
            )
        return args[0]
