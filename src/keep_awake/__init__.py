import atexit
import sys
from threading import Lock, local
from typing import final

__all__ = ["prevent_sleep", "allow_sleep", "KeepAwakeGuard"]
os_platform = sys.platform
_mutex = Lock()
_references = 0
_shutting_down = False


def prevent_sleep() -> bool:
    """Acquire one sleep-prevention reference; failed requests are not counted."""
    global _references
    with _mutex:
        if _shutting_down:
            return False
        if _references == 0 and not _acquire_backend():
            return False
        _references += 1
        return True


def allow_sleep() -> None:
    """Release one reference, allowing sleep only after the last release."""
    global _references
    with _mutex:
        if _references == 0:
            return
        if _references == 1:
            try:
                _release_backend()
            finally:
                # Backends clean up even if release is interrupted. Never cache
                # success after the underlying inhibitor may have been removed.
                _references = 0
        else:
            _references -= 1


def _shutdown() -> None:
    """Release all outstanding references and prevent new work during exit."""
    global _references, _shutting_down
    with _mutex:
        _shutting_down = True
        try:
            if _references:
                _release_backend()
        finally:
            _references = 0


def _acquire_backend() -> bool:

    # in macOS and windows, just call the native api
    if os_platform in ["darwin", "win32"]:
        from ._native_api import _prevent_sleep

        return _prevent_sleep()
    elif os_platform == "linux":
        # in linux, use dbus to send a message to avoid sleep
        from .dbus_api import session_on

        return session_on()
    else:
        raise NotImplementedError(f"Platform '{os_platform}' is not supported.")


def _release_backend() -> None:
    if os_platform in ["darwin", "win32"]:
        from ._native_api import _allow_sleep

        _allow_sleep()
    elif os_platform == "linux":
        from .dbus_api import session_off

        session_off()
    else:
        raise NotImplementedError(f"Platform '{os_platform}' is not supported.")


atexit.register(_shutdown)


@final
class KeepAwakeGuard:
    """Own a reference for each successful entry, including nested scopes."""

    def __init__(self):
        # One guard may be nested or shared across threads. Failed entries must
        # never consume another entry's successful acquisition.
        self._state = local()

    def __enter__(self):
        if not hasattr(self._state, "entries"):
            self._state.entries = []
        entries = self._state.entries
        entries.append(False)
        try:
            entries[-1] = prevent_sleep()
        except BaseException:
            entries.pop()
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        entries = getattr(self._state, "entries", ())
        if entries and entries.pop():
            allow_sleep()
