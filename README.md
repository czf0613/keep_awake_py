# Keep Awake

Prevent idle system sleep and keep the display awake while Python is doing work.
Supports **CPython 3.8+**, including free-threaded (no-GIL) CPython 3.13/3.14.

## Installation

```sh
# Windows / macOS
pip install keep_awake

# Linux desktop
pip install 'keep_awake[linux]'
```

Windows and macOS use a C extension. A matching wheel avoids a local compiler;
otherwise installation builds from source. Linux uses the pure Python
[Jeepney](https://jeepney.readthedocs.io/en/latest/) D-Bus client and requires no
project C extension or D-Bus development headers.

## Usage

```python
from keep_awake import prevent_sleep, allow_sleep

if not prevent_sleep():
    raise RuntimeError("Could not acquire a sleep inhibitor")
try:
    # Do long-running work here.
    pass
finally:
    allow_sleep()
```

For automatic cleanup:

```python
from keep_awake import KeepAwakeGuard

with KeepAwakeGuard():
    # Do long-running work here.
    pass
```

- `prevent_sleep()` returns `True` after acquiring an inhibitor, or `False` if
  the backend cannot acquire one.
- `allow_sleep()` returns `None` and is safe to call repeatedly or before acquiring.
- Calls are synchronized across threads, including no-GIL builds. All callers
  share **one process-wide inhibitor**, without reference counting. Avoid nested
  or overlapping guards: any `allow_sleep()` releases the shared inhibitor.
- `KeepAwakeGuard` preserves the original API: acquisition failure does not raise.
  Use the explicit boolean-returning API when success is required.
- Process exit releases the OS resources. These requests do not override manual
  sleep, lid closure, or administrator power policy.

## Platforms

| Platform | Implementation |
| --- | --- |
| macOS arm64 / x86_64 | IOKit display-idle assertion, protected by a native mutex |
| Windows x86_64 | `SetThreadExecutionState` on a dedicated, synchronized worker |
| Linux desktop | GNOME SessionManager, falling back to `org.freedesktop.ScreenSaver` |

On Linux, run inside a logged-in graphical session with
`DBUS_SESSION_BUS_ADDRESS` set and a supported inhibition service. GNOME requests
suspend and idle inhibition; the freedesktop fallback depends on the desktop's
implementation of idle inhibition. Headless servers and minimal compositors may
not provide either service. An unavailable bus/service returns `False`; omitting
the required `linux` extra produces a dependency import error.

The connection opens on first acquisition and closes on release, including when
release fails. If the desktop/session service restarts, release and reacquire the
inhibitor. Actual GNOME/KDE power behavior still requires desktop validation.

## Development and publishing

```sh
uv sync --frozen
uv run --frozen pytest -q
uv build
```

CI checks Python 3.8–3.14 and free-threaded 3.13t/3.14t on Linux, Windows and both
macOS architectures whenever changes reach `master` or a pull request targets it.
Publishing a GitHub Release runs the checks and builds before uploading the
sdist and native wheels to PyPI through Trusted Publishing.

See [development and release instructions](https://github.com/czf0613/keep_awake_py/blob/master/docs/DEVELOPMENT.md),
[compatibility findings and verification limits](https://github.com/czf0613/keep_awake_py/blob/master/docs/COMPATIBILITY.md), and
[Codex repository guidance](https://github.com/czf0613/keep_awake_py/blob/master/AGENTS.md).

## License

[MIT](https://github.com/czf0613/keep_awake_py/blob/master/LICENSE)
