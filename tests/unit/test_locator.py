import pytest
from vibium import Element

from rfvibium.errors import LocatorSyntaxError, VibiumLibraryError
from rfvibium.locators.locator import (
    is_element_handle,
    looks_like_locator,
    merge_locators,
    parse_locator,
    resolve_element,
)


def test_locator_syntax_error_inherits_from_vibium_library_error() -> None:
    assert issubclass(LocatorSyntaxError, VibiumLibraryError)


# ---------------------------------------------------------------------------
# parse_locator
# ---------------------------------------------------------------------------


def test_plain_string_is_css_selector() -> None:
    args, kwargs = parse_locator("input[name='q']")
    assert args == ("input[name='q']",)
    assert kwargs == {}


def test_css_prefix_returns_positional_selector() -> None:
    args, kwargs = parse_locator("css:#listing > tbody > tr")
    assert args == ("#listing > tbody > tr",)
    assert kwargs == {}


def test_css_prefix_preserves_id_selector_for_robot_framework() -> None:
    # Without the explicit ``css:`` prefix, a cell starting with ``#`` is
    # treated by Robot Framework as a comment, so users must be able to
    # write ``css:#id`` to keep the selector intact.
    args, kwargs = parse_locator("css:#login-button")
    assert args == ("#login-button",)
    assert kwargs == {}


def test_xpath_prefix_preserves_full_value() -> None:
    args, kwargs = parse_locator("xpath://input[@id='email' and @type='text']")
    assert args == ()
    assert kwargs == {"xpath": "//input[@id='email' and @type='text']"}


def test_role_prefix_sets_role_kwarg() -> None:
    args, kwargs = parse_locator("role:button")
    assert args == ()
    assert kwargs == {"role": "button"}


def test_text_prefix_preserves_spaces_and_punctuation() -> None:
    args, kwargs = parse_locator("text:Forgot your password?")
    assert args == ()
    assert kwargs == {"text": "Forgot your password?"}


def test_unknown_prefix_is_treated_as_css_selector() -> None:
    args, kwargs = parse_locator("custom:value")
    assert args == ("custom:value",)
    assert kwargs == {}


def test_empty_target_raises_locator_syntax_error() -> None:
    with pytest.raises(LocatorSyntaxError):
        parse_locator("   ")


def test_prefix_without_value_raises_locator_syntax_error() -> None:
    with pytest.raises(LocatorSyntaxError):
        parse_locator("xpath:")


def test_non_string_raises_locator_syntax_error() -> None:
    with pytest.raises(LocatorSyntaxError):
        parse_locator(123)  # type: ignore[arg-type]


def test_list_locator_gives_actionable_hint() -> None:
    with pytest.raises(LocatorSyntaxError, match=r"\$\{VAR\}.*@\{VAR\}"):
        parse_locator(["role:button", "text:Log in"])  # type: ignore[arg-type]


def test_tuple_locator_gives_actionable_hint() -> None:
    with pytest.raises(LocatorSyntaxError, match=r"@\{VAR\}"):
        parse_locator(("role:button",))  # type: ignore[arg-type]


def test_stringified_list_from_rf_type_conversion_raises() -> None:
    with pytest.raises(LocatorSyntaxError, match=r"stringified Python list"):
        parse_locator("['role:button', 'text:Login']")


def test_stringified_tuple_from_rf_type_conversion_raises() -> None:
    with pytest.raises(LocatorSyntaxError, match=r"stringified Python tuple"):
        parse_locator("('role:button', 'text:Login')")


def test_locator_errors_can_be_caught_as_vibium_library_error() -> None:
    with pytest.raises(VibiumLibraryError):
        parse_locator("   ")


def test_css_attribute_selector_is_not_flagged_as_stringified_list() -> None:
    args, kwargs = parse_locator("[data-testid='login']")
    assert args == ("[data-testid='login']",)
    assert kwargs == {}

    args, kwargs = parse_locator("input[name='q']")
    assert args == ("input[name='q']",)


def test_collapsed_prefixes_raise_with_hint() -> None:
    with pytest.raises(LocatorSyntaxError, match=r"collapsed into a single string"):
        parse_locator("role:button text:Log in")


def test_collapsed_prefixes_detected_for_xpath_and_text() -> None:
    with pytest.raises(LocatorSyntaxError, match=r"' text:'"):
        parse_locator("xpath://button text:Log in")


def test_value_with_space_but_no_known_prefix_is_allowed() -> None:
    args, kwargs = parse_locator("text:Forgot your password?")
    assert kwargs == {"text": "Forgot your password?"}

    args, kwargs = parse_locator("label:E-mail address")
    assert kwargs == {"label": "E-mail address"}


# ---------------------------------------------------------------------------
# looks_like_locator
# ---------------------------------------------------------------------------


def test_looks_like_locator_recognizes_known_prefixes() -> None:
    assert looks_like_locator("role:button") is True
    assert looks_like_locator("text:Log in") is True
    assert looks_like_locator("xpath://div") is True
    assert looks_like_locator("  label:E-mail") is True
    assert looks_like_locator("css:#listing") is True


def test_looks_like_locator_rejects_unknown_prefixes_and_values() -> None:
    assert looks_like_locator("user@example.com") is False
    assert looks_like_locator("input[name='q']") is False
    assert looks_like_locator("custom:value") is False
    assert looks_like_locator("") is False
    assert looks_like_locator(None) is False  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# merge_locators
# ---------------------------------------------------------------------------


def test_merge_single_semantic_locator() -> None:
    args, kwargs = merge_locators(["role:button"])
    assert args == ()
    assert kwargs == {"role": "button"}


def test_merge_combines_role_and_text() -> None:
    args, kwargs = merge_locators(["role:button", "text:Log in"])
    assert args == ()
    assert kwargs == {"role": "button", "text": "Log in"}


def test_merge_combines_css_selector_with_semantic_filters() -> None:
    args, kwargs = merge_locators([".nav", "role:link", "text:Home"])
    assert args == (".nav",)
    assert kwargs == {"role": "link", "text": "Home"}


def test_merge_css_prefix_is_equivalent_to_bare_selector() -> None:
    args_bare, kwargs_bare = merge_locators([".nav", "role:link"])
    args_prefixed, kwargs_prefixed = merge_locators(["css:.nav", "role:link"])
    assert args_bare == args_prefixed == (".nav",)
    assert kwargs_bare == kwargs_prefixed == {"role": "link"}


def test_merge_rejects_duplicate_css_and_css_prefix() -> None:
    with pytest.raises(LocatorSyntaxError, match="Multiple CSS selectors"):
        merge_locators([".nav", "css:.footer"])


def test_merge_preserves_xpath_with_equals_and_brackets() -> None:
    args, kwargs = merge_locators(["xpath://input[@id='email' and @type='text']"])
    assert args == ()
    assert kwargs == {"xpath": "//input[@id='email' and @type='text']"}


def test_merge_rejects_duplicate_axis() -> None:
    with pytest.raises(LocatorSyntaxError, match="Duplicate locator filter 'role'"):
        merge_locators(["role:button", "role:link"])


def test_merge_rejects_multiple_css_selectors() -> None:
    with pytest.raises(LocatorSyntaxError, match="Multiple CSS selectors"):
        merge_locators([".nav", ".footer"])


def test_merge_rejects_empty_iterable() -> None:
    with pytest.raises(LocatorSyntaxError, match="At least one locator"):
        merge_locators([])


# ---------------------------------------------------------------------------
# resolve_element / is_element_handle
# ---------------------------------------------------------------------------


class FakeElement(Element):
    """Minimal Vibium ``Element`` subclass for handle-path unit tests."""

    def __init__(self) -> None:
        # Skip Element.__init__ (needs async client); isinstance still holds.
        self.clicked = False

    def click(self, timeout=None) -> None:
        self.clicked = True

    def text(self) -> str:
        return "x"

    def __repr__(self) -> str:
        return "FakeElement()"


class _PageLike:
    def __init__(self) -> None:
        self.find_calls: list[tuple] = []
        self.element = FakeElement()

    def find(self, *args, **kwargs):
        self.find_calls.append((args, kwargs))
        return self.element


class _SessionLike:
    def __init__(self, page: _PageLike) -> None:
        self._page = page

    def resolve_scope(self, scope=None):
        return self._page if scope is None else scope


def test_is_element_handle_requires_vibium_element() -> None:
    class DuckTyped:
        def click(self) -> None:
            pass

        def text(self) -> str:
            return "x"

    assert is_element_handle(FakeElement()) is True
    assert is_element_handle(DuckTyped()) is False
    assert is_element_handle(_PageLike()) is False
    assert is_element_handle("css:button") is False
    assert is_element_handle(None) is False


def test_resolve_element_returns_handle_alone() -> None:
    session = _SessionLike(_PageLike())
    el = FakeElement()

    assert resolve_element(session, el) is el
    assert session._page.find_calls == []


def test_resolve_element_rejects_handle_with_scope() -> None:
    session = _SessionLike(_PageLike())
    el = FakeElement()

    with pytest.raises(LocatorSyntaxError, match="do not pass scope"):
        resolve_element(session, el, scope=session._page)


def test_resolve_element_rejects_handle_mixed_with_locators() -> None:
    session = _SessionLike(_PageLike())
    el = FakeElement()

    with pytest.raises(LocatorSyntaxError, match="Do not mix"):
        resolve_element(session, el, "css:button")


def test_resolve_element_finds_from_locator_strings() -> None:
    page = _PageLike()
    session = _SessionLike(page)

    out = resolve_element(session, "role:button", "text:Go")

    assert out is page.element
    assert page.find_calls == [((), {"role": "button", "text": "Go"})]


def test_resolve_element_forwards_timeout_to_find() -> None:
    page = _PageLike()
    session = _SessionLike(page)

    out = resolve_element(session, "css:#x", timeout=500)

    assert out is page.element
    assert page.find_calls == [(("#x",), {"timeout": 500})]


def test_resolve_element_omits_timeout_when_none() -> None:
    page = _PageLike()
    session = _SessionLike(page)

    resolve_element(session, "css:#x", timeout=None)

    assert page.find_calls == [(("#x",), {})]


def test_resolve_element_requires_a_target() -> None:
    session = _SessionLike(_PageLike())

    with pytest.raises(LocatorSyntaxError, match="At least one locator or element"):
        resolve_element(session)
