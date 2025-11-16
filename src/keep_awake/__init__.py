import sys


__all__ = ["prevent_sleep", "allow_sleep", "KeepAwakeGuard"]
os_platform = sys.platform


def prevent_sleep() -> bool:
    """Prevent the system from going to sleep."""

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


def allow_sleep() -> None:
    """Allow the system to go to sleep. (Resume its power mamagement behavior)"""

    if os_platform in ["darwin", "win32"]:
        from ._native_api import _allow_sleep

        _allow_sleep()
    elif os_platform == "linux":
        from .dbus_api import session_off

        session_off()
    else:
        raise NotImplementedError(f"Platform '{os_platform}' is not supported.")


class KeepAwakeGuard:
    """A context manager to keep the system awake within its scope."""

    def __enter__(self):
        prevent_sleep()

    def __exit__(self, exc_type, exc_value, traceback):
        allow_sleep()
