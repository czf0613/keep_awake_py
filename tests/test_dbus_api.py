"""Exercise Linux protocol/lifecycle logic without a desktop session."""

import atexit
import importlib
import sys
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from jeepney import HeaderFields, MessageType


@pytest.fixture
def backend(monkeypatch):
    monkeypatch.setitem(sys.modules, "dbus", None)
    sys.modules.pop("keep_awake.dbus_api", None)
    try:
        module = importlib.import_module("keep_awake.dbus_api")
    except ImportError as exc:
        pytest.fail(
            "Linux backend must import without a native D-Bus binding: {}".format(exc)
        )
    yield module
    module.session_off()
    atexit.unregister(module.session_off)
    sys.modules.pop("keep_awake.dbus_api", None)


class Connection:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []
        self.closed = False

    def send_and_get_reply(self, message, *, timeout):
        assert timeout > 0
        assert not self.closed
        message.serialise(serial=1)
        self.calls.append(message)
        reply = next(self.replies)
        if isinstance(reply, BaseException):
            raise reply
        return reply

    def close(self):
        self.closed = True


def reply(body=(), error=None):
    fields = {HeaderFields.error_name: error} if error else {}
    return SimpleNamespace(
        body=body,
        header=SimpleNamespace(
            message_type=MessageType.error if error else MessageType.method_return,
            fields=fields,
        ),
    )


def connect(monkeypatch, backend, connection):
    monkeypatch.setattr(backend, "open_dbus_connection", lambda **kwargs: connection)


def test_import_and_allow_do_not_open_bus(backend, monkeypatch):
    def unavailable(**kwargs):
        pytest.fail("allow_sleep opened the session bus without an inhibitor")

    monkeypatch.setattr(backend, "open_dbus_connection", unavailable)
    assert backend.session_off() is None


@pytest.mark.parametrize(
    "error",
    [
        OSError("offline"),
        KeyError("DBUS_SESSION_BUS_ADDRESS"),
        ValueError("bad address"),
        RuntimeError("unsupported transport"),
    ],
)
def test_connection_failure_returns_false_and_can_retry(backend, monkeypatch, error):
    def unavailable(**kwargs):
        raise error

    monkeypatch.setattr(backend, "open_dbus_connection", unavailable)
    assert backend.session_on() is False
    connection = Connection([reply((7,)), reply()])
    connect(monkeypatch, backend, connection)
    assert backend.session_on() is True


def test_gnome_cookie_zero_and_idempotent_cleanup(backend, monkeypatch):
    connection = Connection([reply((0,)), reply()])
    connect(monkeypatch, backend, connection)
    assert backend.session_on() is True
    assert backend.session_on() is True
    assert backend.session_off() is None
    assert backend.session_off() is None
    assert connection.closed
    assert len(connection.calls) == 2
    inhibit, release = connection.calls
    assert inhibit.header.fields[HeaderFields.destination] == "org.gnome.SessionManager"
    assert inhibit.header.fields[HeaderFields.path] == "/org/gnome/SessionManager"
    assert inhibit.header.fields[HeaderFields.signature] == "susu"
    assert inhibit.body == (
        "org.python.keep_awake",
        0,
        "Keep system and screen awake",
        12,
    )
    assert release.header.fields[HeaderFields.member] == "Uninhibit"
    assert release.header.fields[HeaderFields.signature] == "u"
    assert release.body == (0,)


def test_freedesktop_fallback_uses_correct_signature_and_spelling(backend, monkeypatch):
    connection = Connection(
        [
            reply(error="org.freedesktop.DBus.Error.ServiceUnknown"),
            reply((42,)),
            reply(),
        ]
    )
    connect(monkeypatch, backend, connection)
    assert backend.session_on() is True
    backend.session_off()
    inhibit, release = connection.calls[1:]
    assert (
        inhibit.header.fields[HeaderFields.destination] == "org.freedesktop.ScreenSaver"
    )
    assert inhibit.header.fields[HeaderFields.path] == "/org/freedesktop/ScreenSaver"
    assert inhibit.header.fields[HeaderFields.signature] == "ss"
    assert inhibit.body == ("org.python.keep_awake", "Keep system and screen awake")
    assert release.header.fields[HeaderFields.member] == "UnInhibit"
    assert release.body == (42,)


@pytest.mark.parametrize(
    "response",
    [
        reply(()),
        reply(("7",)),
        reply((-1,)),
        reply((2**32,)),
        reply((True,)),
        TimeoutError(),
        OSError("closed"),
    ],
)
def test_failed_acquisition_closes_connection(backend, monkeypatch, response):
    connection = Connection([response])
    connect(monkeypatch, backend, connection)
    assert backend.session_on() is False
    assert connection.closed


def test_no_supported_service_returns_false(backend, monkeypatch):
    connection = Connection(
        [reply(error="org.freedesktop.DBus.Error.ServiceUnknown")] * 2
    )
    connect(monkeypatch, backend, connection)
    assert backend.session_on() is False
    assert connection.closed


@pytest.mark.parametrize("error", [KeyboardInterrupt(), SystemExit()])
def test_interrupted_acquisition_closes_connection(backend, monkeypatch, error):
    connection = Connection([error])
    connect(monkeypatch, backend, connection)
    with pytest.raises(type(error)):
        backend.session_on()
    assert connection.closed


@pytest.mark.parametrize(
    "response",
    [TimeoutError(), OSError("disconnected"), reply(error="org.example.Failed")],
)
def test_failed_release_still_disconnects_and_can_restart(
    backend, monkeypatch, response
):
    connection = Connection([reply((5,)), response])
    connect(monkeypatch, backend, connection)
    assert backend.session_on()
    backend.session_off()
    assert connection.closed
    next_connection = Connection([reply((6,)), reply()])
    connect(monkeypatch, backend, next_connection)
    assert backend.session_on()


def test_concurrent_calls_share_one_inhibitor(backend, monkeypatch):
    connection = Connection([reply((5,)), reply()])
    connect(monkeypatch, backend, connection)
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert all(pool.map(lambda _: backend.session_on(), range(40)))
        list(pool.map(lambda _: backend.session_off(), range(40)))
    assert len(connection.calls) == 2
    assert connection.closed
