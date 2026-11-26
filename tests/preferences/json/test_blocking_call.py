# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of blocking calls that survive the cancellation of their caller."""

import asyncio
import threading

import pytest

from gandi_mcp.preferences.json.blocking_call import run_to_completion

pytestmark = pytest.mark.anyio


async def test_returns_the_result() -> None:
    assert await run_to_completion(lambda: 42) == 42


async def test_raises_the_error_of_the_call() -> None:
    def fail() -> None:
        raise OSError("disk")

    with pytest.raises(OSError, match="disk"):
        await run_to_completion(fail)


async def blocked_call(succeed: bool) -> tuple[list[str], threading.Event, asyncio.Task[str]]:
    events: list[str] = []
    started, release = threading.Event(), threading.Event()

    def call() -> str:
        started.set()
        release.wait(5)
        events.append("finished")
        if not succeed:
            raise OSError("failed")
        return "acquired"

    task = asyncio.ensure_future(run_to_completion(call, undo=lambda r: events.append(f"undo {r}")))
    await asyncio.to_thread(started.wait, 5)
    task.cancel()
    await asyncio.sleep(0.05)
    events.append("cancel requested")
    return events, release, task


async def test_cancellation_waits_for_the_call_then_undoes_it() -> None:
    events, release, task = await blocked_call(succeed=True)
    assert not task.done()

    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert events == ["cancel requested", "finished", "undo acquired"]


async def test_cancellation_of_a_failing_call_undoes_nothing() -> None:
    events, release, task = await blocked_call(succeed=False)

    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert events == ["cancel requested", "finished"]
