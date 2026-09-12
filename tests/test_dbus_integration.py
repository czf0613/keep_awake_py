"""Use a private D-Bus daemon and synthetic desktop service, never the real desktop."""

import atexit
import importlib
import shutil
import socket
import subprocess
import sys
import sysconfig
from threading import Event, Thread

import pytest
from jeepney import HeaderFields, new_method_return
from jeepney.bus_messages import message_bus
from jeepney.io.blocking import open_dbus_connection


@pytest.mark.parametrize(
    "service", ["org.gnome.SessionManager", "org.freedesktop.ScreenSaver"]
)
def test_real_dbus_round_trip(monkeypatch, tmp_path, service):
    executable = shutil.which("dbus-daemon")
    if executable is None:
        pytest.skip("dbus-daemon is not installed")
    if sys.platform == "darwin":
        # Exercise Linux's authentication path. Jeepney's BSD SCM_CREDS branch
        # is not compatible with macOS; this backend is used only on Linux.
        monkeypatch.delattr(socket, "SCM_CREDS", raising=False)
    config = tmp_path / "bus.conf"
    # No host service directories: the private bus must not activate real
    # desktop services while testing the fallback path.
    config.write_text(
        "<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen>"
        '<auth>EXTERNAL</auth><policy context="default">'
        '<allow send_destination="*"/><allow receive_sender="*"/>'
        '<allow own="*"/></policy></busconfig>',
        encoding="utf-8",
    )
    daemon = subprocess.Popen(
        [
            executable,
            "--config-file={}".format(config),
            "--nofork",
            "--print-address=1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    server = None
    worker = None
    backend = None
    stop = Event()
    errors = []
    calls = []
    try:
        address = daemon.stdout.readline().strip()
        assert address, "Private D-Bus daemon did not start"
        monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", address)
        server = open_dbus_connection()
        assert server.send_and_get_reply(
            message_bus.RequestName(service), timeout=5
        ).body == (1,)

        def serve():
            try:
                while not stop.is_set():
                    try:
                        message = server.receive(timeout=0.1)
                    except TimeoutError:
                        continue
                    method = message.header.fields.get(HeaderFields.member)
                    if method not in ("Inhibit", "Uninhibit", "UnInhibit"):
                        continue
                    calls.append(message)
                    response = (
                        new_method_return(message, "u", (0,))
                        if method == "Inhibit"
                        else new_method_return(message)
                    )
                    server.send(response)
            except BaseException as exc:
                errors.append(exc)

        worker = Thread(target=serve, daemon=True)
        worker.start()
        sys.modules.pop("keep_awake.dbus_api", None)
        backend = importlib.import_module("keep_awake.dbus_api")
        if sysconfig.get_config_var("Py_GIL_DISABLED"):
            assert not sys._is_gil_enabled()
        assert backend.session_on()
        assert backend.session_on()
        backend.session_off()
        assert len(calls) == 2
        assert calls[0].header.fields[HeaderFields.interface] == service
        assert calls[1].body == (0,)
        assert not errors
    finally:
        if backend is not None:
            backend.session_off()
            atexit.unregister(backend.session_off)
        stop.set()
        if worker is not None:
            worker.join(timeout=2)
        if server is not None:
            server.close()
        daemon.terminate()
        try:
            daemon.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            daemon.kill()
            daemon.communicate()
        sys.modules.pop("keep_awake.dbus_api", None)
