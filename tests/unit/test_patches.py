"""Unit tests for the runtime patches that work around upstream Vibium bugs."""

from __future__ import annotations

import asyncio

import pytest

from rfvibium import _patches


@pytest.fixture
def reset_patches(monkeypatch):
    original = asyncio.create_subprocess_exec
    monkeypatch.setattr(_patches, "_applied", False)
    yield
    asyncio.create_subprocess_exec = original  # type: ignore[assignment]
    monkeypatch.setattr(_patches, "_applied", False)


def test_apply_once_wraps_create_subprocess_exec(reset_patches) -> None:
    original = asyncio.create_subprocess_exec

    _patches.apply_once()

    assert asyncio.create_subprocess_exec is not original
    assert getattr(asyncio.create_subprocess_exec, "__wrapped__", None) is original


def test_apply_once_is_idempotent(reset_patches) -> None:
    _patches.apply_once()
    first = asyncio.create_subprocess_exec

    _patches.apply_once()

    assert asyncio.create_subprocess_exec is first


def test_patched_call_injects_default_limit(reset_patches) -> None:
    seen = {}

    async def fake_original(*args, **kwargs):
        seen["args"] = args
        seen["kwargs"] = kwargs
        return "ok"

    asyncio.create_subprocess_exec = fake_original  # type: ignore[assignment]

    _patches.apply_once()

    result = asyncio.get_event_loop().run_until_complete(
        asyncio.create_subprocess_exec("echo", "hi")
    )

    assert result == "ok"
    assert seen["args"] == ("echo", "hi")
    assert seen["kwargs"]["limit"] == _patches.STDOUT_BUFFER_LIMIT_BYTES


def test_patched_call_preserves_explicit_limit(reset_patches) -> None:
    seen = {}

    async def fake_original(*args, **kwargs):
        seen["kwargs"] = kwargs
        return "ok"

    asyncio.create_subprocess_exec = fake_original  # type: ignore[assignment]

    _patches.apply_once()

    asyncio.get_event_loop().run_until_complete(
        asyncio.create_subprocess_exec("echo", limit=1234)
    )

    assert seen["kwargs"]["limit"] == 1234
