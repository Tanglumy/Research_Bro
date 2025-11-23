"""Pytest configuration for running async tests without external plugins.

The test suite includes many `async def` tests but the repository does not
depend on pytest-asyncio. This hook executes coroutine tests using
`asyncio.run`, which keeps the suite lightweight and avoids an extra
dependency. It also sets a lightweight offline flag so modules can choose
stubbed data paths during tests.
"""

import asyncio
import inspect
import os
from typing import Any


# Encourage modules to use stubbed/offline paths during tests
os.environ.setdefault("OFFLINE_MODE", "1")


def pytest_pyfunc_call(pyfuncitem: Any) -> bool | None:
    """Allow pytest to execute coroutine tests without extra plugins."""
    test_function = pyfuncitem.obj
    if inspect.iscoroutinefunction(test_function):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_function(**pyfuncitem.funcargs))
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        return True
    return None
