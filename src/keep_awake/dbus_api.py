import dbus
from typing import Optional
from threading import Lock
import atexit

_bus = dbus.SessionBus()
_iface = dbus.Interface(
    _bus.get_object("org.freedesktop.ScreenSaver", "/org/freedesktop/ScreenSaver"),
    "org.freedesktop.ScreenSaver",
)
_cookie: Optional[int] = None
_mutex = Lock()


def session_on() -> bool:
    global _cookie
    if _cookie is not None:
        return True

    with _mutex:
        if _cookie is not None:
            return True

        try:
            cookie = _iface.Inhibit("org.python.keep_awake", "Keep screen awake")
            _cookie = int(cookie)

            return True
        except dbus.DBusException as e:
            print(f"Failed to communicate with dbus: {e}")
            return False
        except ValueError as e:
            print(f"Failed to parse dbus response: {e}")
            return False


def session_off() -> None:
    global _cookie
    if _cookie is None:
        return

    with _mutex:
        if _cookie is None:
            return

        try:
            _iface.UnInhibit(dbus.UInt32(_cookie))
            _cookie = None
        except dbus.DBusException as e:
            print(f"Failed to communicate with dbus: {e}")


atexit.register(_bus.close())
