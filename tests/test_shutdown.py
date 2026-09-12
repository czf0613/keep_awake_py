"""Use actual interpreter exit, with synthetic OS backends on every platform."""

import json
import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize("platform", ["darwin", "win32", "linux"])
@pytest.mark.parametrize(
    "exit_mode, returncode", [("normal", 0), ("sys_exit", 7), ("error", 1)]
)
def test_exit_releases_outstanding_references(platform, exit_mode, returncode):
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import atexit
                import json
                import sys
                from types import SimpleNamespace

                events = []

                def report():
                    # Registered first: runs after the library's cleanup.
                    events.append(["late_acquire", keep_awake.prevent_sleep()])
                    print(json.dumps(events))

                atexit.register(report)
                import keep_awake

                def acquire():
                    events.append(["acquire"])
                    return True

                def release():
                    events.append(["release"])

                sys.modules["keep_awake._native_api"] = SimpleNamespace(
                    _prevent_sleep=acquire, _allow_sleep=release
                )
                sys.modules["keep_awake.dbus_api"] = SimpleNamespace(
                    session_on=acquire, session_off=release
                )
                keep_awake.os_platform = sys.argv[1]
                for _ in range(3):
                    assert keep_awake.prevent_sleep()
                if sys.argv[2] == "sys_exit":
                    sys.exit(7)
                if sys.argv[2] == "error":
                    raise RuntimeError("intentional exit")
                """
            ),
            platform,
            exit_mode,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == returncode, result.stderr
    assert json.loads(result.stdout) == [
        ["acquire"],
        ["release"],
        ["late_acquire", False],
    ]
    assert "Exception ignored in atexit callback" not in result.stderr
