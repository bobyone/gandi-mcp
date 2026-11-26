# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run a blocking call in a worker thread, letting it finish even when cancelled."""

import asyncio
from collections.abc import Callable


async def run_to_completion[T](
    function: Callable[[], T], undo: Callable[[T], None] | None = None
) -> T:
    """Run ``function`` in a worker thread and wait for its end, cancelled or not.

    A thread cannot be interrupted: on cancellation, this waits until the call has
    finished, runs ``undo`` on its result if it succeeded (for example to release a lock
    acquired too late), then lets the cancellation propagate. A file is therefore never
    left half written, nor a lock left held, by a cancelled caller.
    """
    worker = asyncio.ensure_future(asyncio.to_thread(function))
    cancelled = False
    while not worker.done():
        try:
            await asyncio.shield(worker)
        except asyncio.CancelledError:
            cancelled = True
        except Exception:
            break
    if cancelled:
        if undo is not None and not worker.cancelled() and worker.exception() is None:
            undo(worker.result())
        raise asyncio.CancelledError
    return worker.result()
