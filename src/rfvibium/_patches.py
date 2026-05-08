"""Runtime workarounds for upstream Vibium client issues.

All patches are:
- Idempotent: ``apply_once`` is safe to call multiple times.
- Defensive: they only inject defaults via ``setdefault`` and never override
  caller-specified values.

Patches applied:

- ``asyncio.create_subprocess_exec`` is wrapped to default ``limit`` to 64 MiB.
  Vibium's ``BiDiClient._receive_loop`` reads BiDi JSON messages line-by-line
  over the binary's stdout pipe. ``asyncio.StreamReader`` defaults to a 64 KiB
  buffer, which is trivially exceeded by any base64-encoded screenshot and
  raises ``asyncio.LimitOverrunError``. That kills the receive loop and any
  subsequent operation fails with ``Connection closed``. Upstream should pass
  ``limit=...`` to ``create_subprocess_exec`` inside
  ``vibium.binary.VibiumProcess.start``; until then we set a sane default for
  the whole process.
"""

from __future__ import annotations

import asyncio

STDOUT_BUFFER_LIMIT_BYTES = 64 * 1024 * 1024  # 64 MiB

_applied = False


def apply_once() -> None:
    """Install patches a single time per Python process."""
    global _applied
    if _applied:
        return

    original = asyncio.create_subprocess_exec

    async def create_subprocess_exec_with_limit(*args, **kwargs):
        kwargs.setdefault("limit", STDOUT_BUFFER_LIMIT_BYTES)
        return await original(*args, **kwargs)

    create_subprocess_exec_with_limit.__wrapped__ = original  # type: ignore[attr-defined]
    asyncio.create_subprocess_exec = create_subprocess_exec_with_limit  # type: ignore[assignment]
    _applied = True
