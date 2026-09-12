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

- Every successful `prevent_sleep()` adds one reference and returns `True`.
  Failure returns `False` without adding a reference.
- Pair each successful acquisition with one `allow_sleep()`, which returns `None`.
  The OS inhibitor is released only when the shared reference count reaches zero.
  Calling `allow_sleep()` when the count is already zero does nothing.
- Calls are synchronized across threads, including no-GIL builds. All callers
  share **one OS inhibitor with a reference count**. If thread A acquires and
  thread B acquires then releases, the count changes `1 → 2 → 1`, so sleep remains
  inhibited until A releases. A release may happen on a different thread.
- Use the public API only. Calling the private C extension directly bypasses
  synchronization, reference counting and exit cleanup, and is unsupported.
- Nested and overlapping `KeepAwakeGuard` scopes are supported, including reuse
  of the same guard. Each scope releases only its own successful acquisition.
  Acquisition failure still does not raise; use the boolean-returning API when
  success is required.
- On normal interpreter shutdown, one shared `atexit` handler releases the backend
  even if several references remain. Acquisitions after this cleanup return `False`.
  Forced termination, interpreter crashes and `os._exit()` bypass this handler;
  use a guard or `try/finally` for cleanup during normal execution.
  These requests do not override manual sleep, lid closure, or administrator power
  policy.

## Platforms

| Platform | Implementation |
| --- | --- |
| macOS arm64 / x86_64 | IOKit display-idle assertion, serialized by the Python API |
| Windows x86_64 / ARM64 | `SetThreadExecutionState` on a dedicated, synchronized worker |
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

Native Windows ARM64 wheels are built for Python 3.11–3.14 and 3.13t/3.14t.
Python 3.8–3.10 remains supported on Windows x86_64. This matches the native ARM64
interpreters available through uv.

## Migrating from the idempotent API

Repeated successful calls now require matching releases. Code that previously
called `prevent_sleep()` many times but released only once must balance its calls
or use a guard around each unit of work. Do not manually release an acquisition
already owned by a guard, or release after a failed acquisition: the counter is
shared and cannot identify a mismatched manual release.

## Development and publishing

```sh
uv sync --frozen
uv run --frozen pytest -q
uv build
```

CI checks Python 3.8–3.14 and free-threaded 3.13t/3.14t on Linux, Windows x86_64 and
both macOS architectures, plus the six Windows ARM64 configurations above,
whenever changes reach `master` or a pull request targets it.
Publishing a GitHub Release runs the checks and builds before uploading the
sdist and native wheels to PyPI through Trusted Publishing.

See [development and release instructions](https://github.com/czf0613/keep_awake_py/blob/master/docs/DEVELOPMENT.md),
[compatibility findings and verification limits](https://github.com/czf0613/keep_awake_py/blob/master/docs/COMPATIBILITY.md), and
[Codex repository guidance](https://github.com/czf0613/keep_awake_py/blob/master/AGENTS.md).

## License

[MIT](https://github.com/czf0613/keep_awake_py/blob/master/LICENSE)
