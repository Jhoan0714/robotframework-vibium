"""Scoped library settings (Global / Suite / Test)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .errors import VibiumLibraryError


class Scope(str, Enum):
    """Lifetime of a library setting override."""

    Global = "Global"
    Suite = "Suite"
    Test = "Test"


def parse_scope(value: object) -> Scope:
    """Parse ``Global`` / ``Suite`` / ``Test`` / ``Task`` (case-insensitive)."""
    if isinstance(value, Scope):
        return value
    raw = str(value).strip().lower()
    if raw == "global":
        return Scope.Global
    if raw == "suite":
        return Scope.Suite
    if raw in ("test", "task"):
        return Scope.Test
    raise VibiumLibraryError(
        f"Invalid scope {value!r}. Use Global, Suite, or Test/Task."
    )


@dataclass
class ScopedSetting:
    typ: Scope
    setting: Any


class SettingsStack:
    """Stack of scoped settings; ``get()`` returns the innermost value.

    - ``Global`` updates every frame
    - ``Suite`` overrides at current suite (and clears an active Test frame)
    - ``Test``/``Task`` overrides for the current test only
    """

    def __init__(self, global_setting: Any = None) -> None:
        self._stack: dict[str, ScopedSetting] = {
            "g": ScopedSetting(Scope.Global, global_setting)
        }
        self._suite_ids: list[str] = []
        self._current_test_id: str | None = None

    def start_suite(self, suite_id: str) -> None:
        parent = self.get()
        self._suite_ids.append(suite_id)
        self._stack[suite_id] = ScopedSetting(Scope.Suite, parent)

    def end_suite(self, suite_id: str) -> None:
        self._stack.pop(suite_id, None)
        if self._suite_ids and self._suite_ids[-1] == suite_id:
            self._suite_ids.pop()

    def start_test(self, test_id: str) -> None:
        parent = self.get()
        self._current_test_id = test_id
        self._stack[test_id] = ScopedSetting(Scope.Test, parent)

    def end_test(self, test_id: str) -> None:
        self._stack.pop(test_id, None)
        if self._current_test_id == test_id:
            self._current_test_id = None

    def get(self) -> Any:
        return list(self._stack.values())[-1].setting

    def set(self, setting: Any, scope: Scope) -> Any:
        original = self.get()
        if scope is Scope.Global:
            for frame in self._stack.values():
                frame.setting = setting
            return original

        if scope is Scope.Suite:
            if not self._suite_ids:
                for frame in self._stack.values():
                    frame.setting = setting
                return original
            last_key = list(self._stack.keys())[-1]
            if self._stack[last_key].typ is Scope.Test:
                self._stack.pop(last_key)
            suite_id = self._suite_ids[-1]
            self._stack[suite_id] = ScopedSetting(Scope.Suite, setting)
            return original

        if scope is Scope.Test:
            if self._current_test_id is None:
                raise VibiumLibraryError(
                    "scope=Test/Task can only be set while a test is running."
                )
            self._stack[self._current_test_id] = ScopedSetting(Scope.Test, setting)
            return original

        raise VibiumLibraryError(f"Unknown scope {scope!r}.")
