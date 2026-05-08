import pytest

from rfvibium.errors import LocatorSyntaxError, VibiumLibraryError
from rfvibium.keywords import interaction as interaction_module
from rfvibium.keywords.interaction import InteractionKeywords


class _LoggerSpy:
    def __init__(self) -> None:
        self.messages = []

    def info(self, message, html=False) -> None:
        self.messages.append(message)


class DummyElement:
    def __init__(self) -> None:
        self.clicked = False
        self.double_clicked = False
        self.hovered = False
        self.focused = False
        self.filled_value = None
        self.typed_text = None
        self.cleared = False
        self.checked = False
        self.unchecked = False
        self.selected_option = None
        self.dispatched = None
        self.pressed_key = None
        self.scrolled_into_view = False
        self.uploaded_files = None
        self.drag_calls: list = []
        self.attr_name = None

    def click(self) -> None:
        self.clicked = True

    def dblclick(self) -> None:
        self.double_clicked = True

    def hover(self) -> None:
        self.hovered = True

    def focus(self) -> None:
        self.focused = True

    def fill(self, value) -> None:
        self.filled_value = value

    def type(self, text) -> None:
        self.typed_text = text

    def clear(self) -> None:
        self.cleared = True

    def check(self) -> None:
        self.checked = True

    def uncheck(self) -> None:
        self.unchecked = True

    def select_option(self, value) -> None:
        self.selected_option = value

    def dispatch_event(self, event_type, event_init=None) -> None:
        self.dispatched = (event_type, event_init)

    def press(self, key) -> None:
        self.pressed_key = key

    def scroll_into_view(self) -> None:
        self.scrolled_into_view = True

    def set_files(self, files) -> None:
        self.uploaded_files = list(files)

    def drag_to(self, target, timeout=None) -> None:
        self.drag_calls.append((target, timeout))

    def inner_text(self) -> str:
        return "INNER TEXT"

    def html(self) -> str:
        return "<div>HTML</div>"

    def value(self) -> str:
        return "VALUE"

    def attr(self, name: str):
        self.attr_name = name
        return "ATTR_VALUE"

    def get_attribute(self, name: str):
        self.attr_name = name
        return "ATTR_VALUE"

    def bounds(self):
        return {"x": 1, "y": 2, "width": 3, "height": 4}

    def bounding_box(self):
        return {"x": 1, "y": 2, "width": 3, "height": 4}

    def is_visible(self) -> bool:
        return True

    def is_hidden(self) -> bool:
        return False

    def is_enabled(self) -> bool:
        return True

    def is_checked(self) -> bool:
        return False

    def is_editable(self) -> bool:
        return True

    def role(self) -> str:
        return "button"

    def label(self) -> str:
        return "Save"

    def text(self) -> str:
        return "ELEMENT TEXT"


class DummyPage:
    def __init__(self) -> None:
        self.last_args = None
        self.last_kwargs = None
        self.element = DummyElement()
        self.scroll_calls = []

    def find(self, *args, **kwargs):
        self.last_args = args
        self.last_kwargs = kwargs
        return self.element

    def scroll(self, direction="down", amount=3, selector=None):
        self.scroll_calls.append(
            {"direction": direction, "amount": amount, "selector": selector}
        )

    def evaluate(self, expression: str):
        if expression == "document.body ? document.body.innerText : ''":
            return "PAGE TEXT"
        return {"expression": expression}


class DummySession:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def require_page(self) -> DummyPage:
        return self._page

    def resolve_scope(self, scope=None):
        return self._page if scope is None else scope


class DummyDragPage:
    """``find`` returns a fresh element each call (needed for drag and drop)."""

    def __init__(self) -> None:
        self.find_log = []

    def find(self, *args, **kwargs):
        el = DummyElement()
        self.find_log.append((args, kwargs, el))
        return el


class TestableInteraction(InteractionKeywords):
    def __init__(self, page: DummyPage) -> None:
        self._session = DummySession(page)


# ---------------------------------------------------------------------------
# Click Element
# ---------------------------------------------------------------------------


def test_click_element_with_plain_css_selector() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.click_element("input[name='q']")

    assert page.last_args == ("input[name='q']",)
    assert page.last_kwargs == {}
    assert page.element.clicked is True


def test_click_element_with_role_prefix() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.click_element("role:button")

    assert page.last_args == ()
    assert page.last_kwargs == {"role": "button"}


def test_click_element_combines_role_and_text() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.click_element("role:button", "text:Log in")

    assert page.last_args == ()
    assert page.last_kwargs == {"role": "button", "text": "Log in"}


def test_click_element_preserves_xpath_with_equals() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.click_element("xpath://input[@id='email' and @type='text']")

    assert page.last_args == ()
    assert page.last_kwargs == {"xpath": "//input[@id='email' and @type='text']"}


def test_click_element_without_locators_raises() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError, match="(?i)at least one locator"):
        kw.click_element()


def test_click_element_with_duplicate_axis_raises() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError, match="Duplicate locator filter"):
        kw.click_element("role:button", "role:link")


def test_click_element_rejects_list_argument_with_hint() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError, match=r"@\{VAR\}"):
        kw.click_element(["role:button", "text:Log in"])  # type: ignore[arg-type]


def test_click_element_rejects_stringified_list_with_hint() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError, match=r"stringified Python list"):
        kw.click_element("['role:button', 'text:Log in']")


def test_click_element_rejects_collapsed_prefixes_with_hint() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError, match="collapsed into a single string"):
        kw.click_element("role:button text:Log in")


# ---------------------------------------------------------------------------
# Fill Element — ergonomic mode (value as last positional)
# ---------------------------------------------------------------------------


def test_fill_element_css_selector_with_value_last() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.fill_element("input[name='email']", "user@example.com")

    assert page.last_args == ("input[name='email']",)
    assert page.last_kwargs == {}
    assert page.element.filled_value == "user@example.com"


def test_fill_element_combines_filters_with_value_last() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.fill_element("role:textbox", "label:E-mail", "user@example.com")

    assert page.last_args == ()
    assert page.last_kwargs == {"role": "textbox", "label": "E-mail"}
    assert page.element.filled_value == "user@example.com"


# ---------------------------------------------------------------------------
# Fill Element — explicit value= mode
# ---------------------------------------------------------------------------


def test_fill_element_explicit_value_kwarg() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.fill_element("role:textbox", value="user@example.com")

    assert page.last_kwargs == {"role": "textbox"}
    assert page.element.filled_value == "user@example.com"


def test_fill_element_explicit_value_with_value_that_looks_like_locator() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.fill_element("input#comment", value="role:admin")

    assert page.last_args == ("input#comment",)
    assert page.element.filled_value == "role:admin"


def test_fill_element_empty_string_value_is_allowed() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.fill_element("input#x", value="")

    assert page.element.filled_value == ""


# ---------------------------------------------------------------------------
# Fill Element — error cases
# ---------------------------------------------------------------------------


def test_fill_element_rejects_ambiguous_last_positional() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError, match="looks like a locator"):
        kw.fill_element("role:textbox", "label:E-mail")


def test_fill_element_rejects_single_positional_without_value() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError, match="locator and a value"):
        kw.fill_element("role:textbox")


def test_fill_element_rejects_value_without_locator() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError, match="(?i)at least one locator"):
        kw.fill_element(value="user@example.com")


# ---------------------------------------------------------------------------
# Find Element
# ---------------------------------------------------------------------------


def test_find_element_returns_repr_and_merges_filters() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    result = kw.find_element("role:button", "text:Submit")

    assert page.last_kwargs == {"role": "button", "text": "Submit"}
    assert isinstance(result, str)


def test_get_text_with_locator_reads_element_text() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    result = kw.get_element_text("role:button", "text:Save")

    assert result == "ELEMENT TEXT"
    assert page.last_args == ()
    assert page.last_kwargs == {"role": "button", "text": "Save"}


def test_element_read_keywords_call_expected_methods() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    assert kw.get_element_inner_text("role:button") == "INNER TEXT"
    assert kw.get_element_html("role:button") == "<div>HTML</div>"
    assert kw.get_element_value("role:button") == "VALUE"
    assert kw.get_element_attr("data-id", "role:button") == "ATTR_VALUE"
    assert page.element.attr_name == "data-id"
    assert kw.get_element_attribute("aria-label", "role:button") == "ATTR_VALUE"
    assert page.element.attr_name == "aria-label"
    assert kw.get_element_bounds("role:button") == {
        "x": 1,
        "y": 2,
        "width": 3,
        "height": 4,
    }
    assert kw.get_element_bounding_box("role:button") == {
        "x": 1,
        "y": 2,
        "width": 3,
        "height": 4,
    }
    assert kw.element_is_visible("role:button") is True
    assert kw.element_is_hidden("role:button") is False
    assert kw.element_is_enabled("role:button") is True
    assert kw.element_is_checked("role:button") is False
    assert kw.element_is_editable("role:button") is True
    assert kw.get_element_role("role:button") == "button"
    assert kw.get_element_label("role:button") == "Save"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def test_click_element_logs_locator(monkeypatch) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(interaction_module, "logger", spy)
    kw = TestableInteraction(DummyPage())

    kw.click_element("role:button", "text:Log in")

    assert spy.messages == ["Clicking element 'role:button text:Log in'."]


def test_fill_element_logs_value_by_default(monkeypatch) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(interaction_module, "logger", spy)
    kw = TestableInteraction(DummyPage())

    kw.fill_element("role:textbox", value="user@example.com")

    assert any(
        "user@example.com" in msg and "role:textbox" in msg for msg in spy.messages
    )


def test_fill_element_masks_value_when_secret(monkeypatch) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(interaction_module, "logger", spy)
    kw = TestableInteraction(DummyPage())

    kw.fill_element("role:textbox", value="s3cret", secret=True)

    joined = " ".join(spy.messages)
    assert "***" in joined
    assert "s3cret" not in joined


def test_press_key_logs_key(monkeypatch) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(interaction_module, "logger", spy)

    page = DummyPage()

    class _KB:
        def press(self, key: str) -> None:
            page.pressed = key

    page.keyboard = _KB()
    kw = TestableInteraction(page)

    kw.press_key("Enter")

    assert spy.messages == ["Pressing key 'Enter' on active page."]


def test_press_key_with_locator_uses_element_press() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.press_key("Enter", "role:textbox", "label:Search")

    assert page.last_kwargs == {"role": "textbox", "label": "Search"}
    assert page.element.pressed_key == "Enter"


def test_press_keys_uses_keyboard_combo(monkeypatch) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(interaction_module, "logger", spy)
    page = DummyPage()

    class _KB:
        def press(self, key: str) -> None:
            page.pressed_combo = key

    page.keyboard = _KB()
    kw = TestableInteraction(page)

    kw.press_keys("Control+a")

    assert page.pressed_combo == "Control+a"
    assert spy.messages == ["Pressing key combo 'Control+a' on active page."]


def test_type_text_with_explicit_text_kwarg() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.type_text("role:textbox", text="hello")

    assert page.last_kwargs == {"role": "textbox"}
    assert page.element.typed_text == "hello"


def test_type_text_rejects_ambiguous_last_positional() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError, match="looks like a locator"):
        kw.type_text("role:textbox", "label:Email")


def test_type_text_masks_value_when_secret(monkeypatch) -> None:
    spy = _LoggerSpy()
    monkeypatch.setattr(interaction_module, "logger", spy)
    kw = TestableInteraction(DummyPage())

    kw.type_text("input#x", text="secret", secret=True)

    joined = " ".join(spy.messages)
    assert "***" in joined
    assert "secret" not in joined


def test_clear_element_calls_clear() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.clear_element("css:#email")

    assert page.element.cleared is True


def test_double_click_element_calls_dblclick() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.double_click_element("role:button", "text:Open")

    assert page.last_kwargs == {"role": "button", "text": "Open"}
    assert page.element.double_clicked is True


def test_hover_element_calls_hover() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.hover_element("xpath://button[@id='x']")

    assert page.last_kwargs == {"xpath": "//button[@id='x']"}
    assert page.element.hovered is True


def test_focus_element_calls_focus() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.focus_element("input[name='q']")

    assert page.last_args == ("input[name='q']",)
    assert page.element.focused is True


def test_select_option_with_explicit_value_kwarg() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.select_option("role:combobox", value="blue")

    assert page.last_kwargs == {"role": "combobox"}
    assert page.element.selected_option == "blue"


def test_select_option_rejects_ambiguous_last_positional() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError, match="looks like a locator"):
        kw.select_option("role:combobox", "text:Blue")


def test_check_and_uncheck_keywords() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.check_element("role:checkbox", "text:Terms")
    kw.uncheck_element("role:checkbox", "text:Terms")

    assert page.element.checked is True
    assert page.element.unchecked is True


def test_dispatch_event_with_dict_payload() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.dispatch_event("role:button", event="click", event_init={"bubbles": True})

    assert page.element.dispatched == ("click", {"bubbles": True})


def test_dispatch_event_with_json_payload_string() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.dispatch_event("input#email", event="input", event_init='{"bubbles": true}')

    assert page.element.dispatched == ("input", {"bubbles": True})


def test_dispatch_event_rejects_invalid_json() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError, match="must be valid JSON"):
        kw.dispatch_event("input#email", event="input", event_init="{bad")


def test_upload_files_single_path() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.upload_files("css:input[type='file']", files="/tmp/a.pdf")

    assert page.last_args == ("input[type='file']",)
    assert page.last_kwargs == {}
    assert page.element.uploaded_files == ["/tmp/a.pdf"]


def test_upload_files_multiple_paths() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.upload_files("role:textbox", "text:Avatar", files=["/a.png", "/b.png"])

    assert page.last_kwargs == {"role": "textbox", "text": "Avatar"}
    assert page.element.uploaded_files == ["/a.png", "/b.png"]


def test_upload_files_requires_keyword_files() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(TypeError, match="files"):
        kw.upload_files("css:input[type='file']")


def test_upload_files_requires_at_least_one_locator() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(LocatorSyntaxError, match="At least one locator is required"):
        kw.upload_files(files="/only/path.pdf")


def test_drag_and_drop_with_string_locators() -> None:
    page = DummyDragPage()
    kw = TestableInteraction(page)

    kw.drag_and_drop("css:#src", "css:#tgt")

    assert len(page.find_log) == 2
    assert page.find_log[0][0] == ("#src",)
    assert page.find_log[1][0] == ("#tgt",)
    src_el = page.find_log[0][2]
    tgt_el = page.find_log[1][2]
    assert src_el.drag_calls == [(tgt_el, None)]


def test_drag_and_drop_with_list_locators() -> None:
    page = DummyDragPage()
    kw = TestableInteraction(page)

    kw.drag_and_drop(
        source=["role:button", "text:From"],
        target=["role:button", "text:To"],
    )

    assert page.find_log[0][1] == {"role": "button", "text": "From"}
    assert page.find_log[1][1] == {"role": "button", "text": "To"}
    src_el = page.find_log[0][2]
    tgt_el = page.find_log[1][2]
    assert src_el.drag_calls[0][0] is tgt_el


def test_drag_and_drop_passes_timeout_ms() -> None:
    page = DummyDragPage()
    kw = TestableInteraction(page)

    kw.drag_and_drop("css:a", "css:b", timeout="1.5s")

    src_el = page.find_log[0][2]
    assert src_el.drag_calls[0][1] == 1500


def test_drag_and_drop_rejects_invalid_source_type() -> None:
    kw = TestableInteraction(DummyDragPage())
    with pytest.raises(LocatorSyntaxError, match="source must be a string"):
        kw.drag_and_drop(123, "css:b")


def test_drag_and_drop_rejects_empty_source_list() -> None:
    kw = TestableInteraction(DummyDragPage())
    with pytest.raises(LocatorSyntaxError, match="source must contain"):
        kw.drag_and_drop(source=[], target="css:b")


def test_scroll_element_into_view_calls_element_method() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.scroll_element_into_view("xpath://div[@id='target']")

    assert page.last_kwargs == {"xpath": "//div[@id='target']"}
    assert page.element.scrolled_into_view is True


def test_scroll_calls_page_scroll_without_selector() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.scroll("down", 5)

    assert page.scroll_calls == [{"direction": "down", "amount": 5, "selector": None}]


def test_scroll_calls_page_scroll_with_css_selector() -> None:
    page = DummyPage()
    kw = TestableInteraction(page)

    kw.scroll("up", 2, ".panel")

    assert page.scroll_calls == [{"direction": "up", "amount": 2, "selector": ".panel"}]


def test_scroll_rejects_semantic_locator_scope() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError, match="only accepts a CSS selector"):
        kw.scroll("down", 1, "role:list")


# ---------------------------------------------------------------------------
# Typed errors
# ---------------------------------------------------------------------------


def test_locator_error_is_typed_as_locator_syntax_error() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(LocatorSyntaxError):
        kw.click_element("role:")


def test_empty_locator_call_is_locator_syntax_error() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(LocatorSyntaxError):
        kw.click_element()


def test_typed_errors_are_catchable_as_base() -> None:
    kw = TestableInteraction(DummyPage())
    with pytest.raises(VibiumLibraryError):
        kw.click_element()
