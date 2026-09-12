"""Linux desktop inhibition over a private, lazily opened D-Bus connection."""

import logging
from threading import Lock
from typing import Optional

from jeepney import DBusAddress, DBusErrorResponse, MessageType, new_method_call
from jeepney.io.blocking import DBusConnection, open_dbus_connection

_logger = logging.getLogger(__name__)
_mutex = Lock()
_connection: Optional[DBusConnection] = None
_cookie: Optional[int] = None
_backend = None
_timeout = 5.0
_app_id = "org.python.keep_awake"
_reason = "Keep system and screen awake"

# GNOME flags: suspend (4) | idle (8). Method capitalization differs by API.
_backends = (
    (
        DBusAddress(
            "/org/gnome/SessionManager",
            "org.gnome.SessionManager",
            "org.gnome.SessionManager",
        ),
        "susu",
        (_app_id, 0, _reason, 12),
        "Uninhibit",
    ),
    (
        DBusAddress(
            "/org/freedesktop/ScreenSaver",
            "org.freedesktop.ScreenSaver",
            "org.freedesktop.ScreenSaver",
        ),
        "ss",
        (_app_id, _reason),
        "UnInhibit",
    ),
)


def _call(connection, address, method, signature, body):
    message = new_method_call(address, method, signature, body)
    reply = connection.send_and_get_reply(message, timeout=_timeout)
    if reply.header.message_type == MessageType.error:
        raise DBusErrorResponse(reply)
    return reply.body


def _close(connection):
    try:
        connection.close()
    except OSError:
        _logger.debug("Failed to close the D-Bus connection", exc_info=True)


def session_on() -> bool:
    """Acquire one process-wide inhibitor, returning False if unavailable."""
    global _connection, _cookie, _backend
    with _mutex:
        if _cookie is not None:
            return True
        connection = None
        try:
            connection = open_dbus_connection(bus="SESSION")
            for backend in _backends:
                address, signature, body, _ = backend
                try:
                    result = _call(connection, address, "Inhibit", signature, body)
                except DBusErrorResponse:
                    continue
                if (
                    len(result) != 1
                    or type(result[0]) is not int
                    or not 0 <= result[0] <= 0xFFFFFFFF
                ):
                    raise ValueError("Inhibit must return a UInt32 cookie")
                _connection, _cookie, _backend = connection, result[0], backend
                return True
        except (
            DBusErrorResponse,
            OSError,
            EOFError,
            KeyError,
            ValueError,
            RuntimeError,
            StopIteration,
        ) as exc:
            _logger.debug("Unable to inhibit the desktop session: %s", exc)
        finally:
            if connection is not None and connection is not _connection:
                # Also releases an inhibitor whose reply was lost, malformed,
                # or interrupted before ownership transferred to module state.
                _close(connection)
        return False


def session_off() -> None:
    """Release the inhibitor; disconnect even when the service cannot reply."""
    global _connection, _cookie, _backend
    with _mutex:
        if _connection is None:
            return
        try:
            _call(_connection, _backend[0], _backend[3], "u", (_cookie,))
        except (DBusErrorResponse, OSError, EOFError, ValueError) as exc:
            _logger.debug("Unable to release the desktop inhibitor: %s", exc)
        finally:
            _close(_connection)
            _connection, _cookie, _backend = None, None, None
