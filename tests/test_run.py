from keep_awake import prevent_sleep, allow_sleep, KeepAwakeGuard
import os
import sys

import pytest

pytestmark = [
    pytest.mark.desktop,
    pytest.mark.skipif(
        sys.platform == "linux" and os.environ.get("KEEP_AWAKE_DESKTOP_TEST") != "1",
        reason="Real Linux desktop test is opt-in",
    ),
]


def test_no_sleep():
    try:
        assert prevent_sleep()
    finally:
        assert allow_sleep() is None

    with KeepAwakeGuard():
        pass
