"""Native smoke and concurrency checks; no Linux desktop is required."""

import os
import subprocess
import sys
import sysconfig
import textwrap
from concurrent.futures import ThreadPoolExecutor

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform not in ("darwin", "win32"), reason="Native backend only"
)


def test_native_import_preserves_disabled_gil():
    if not sysconfig.get_config_var("Py_GIL_DISABLED"):
        pytest.skip("Requires free-threaded CPython")
    environment = os.environ.copy()
    environment.pop("PYTHON_GIL", None)
    result = subprocess.run(
        [
            sys.executable,
            "-Werror",
            "-c",
            "import sys; assert not sys._is_gil_enabled(); import keep_awake._native_api; assert not sys._is_gil_enabled()",
        ],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_native_concurrent_calls():
    from keep_awake import prevent_sleep, allow_sleep

    def cycle(_):
        acquired = 0
        try:
            for _ in range(2):
                assert prevent_sleep()
                acquired += 1
        finally:
            for _ in range(acquired):
                allow_sleep()

    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(cycle, range(40)))
    finally:
        allow_sleep()


def test_interpreter_exit_calls_native_release():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import keep_awake
                from keep_awake import _native_api

                release = _native_api._allow_sleep

                def observed_release():
                    release()
                    print("native released")

                _native_api._allow_sleep = observed_release
                for _ in range(3):
                    assert keep_awake.prevent_sleep()
                """
            ),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "native released"
    assert not result.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Windows handle accounting")
def test_windows_repeated_acquisition_does_not_leak_handles():
    import ctypes
    from ctypes import wintypes

    from keep_awake import prevent_sleep, allow_sleep

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.GetProcessHandleCount.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
    ]

    def handle_count():
        count = wintypes.DWORD()
        assert kernel.GetProcessHandleCount(
            kernel.GetCurrentProcess(), ctypes.byref(count)
        )
        return count.value

    allow_sleep()
    before = handle_count()
    acquired = 0
    try:
        for _ in range(50):
            assert prevent_sleep()
            acquired += 1
    finally:
        for _ in range(acquired):
            allow_sleep()
    assert handle_count() <= before + 2
