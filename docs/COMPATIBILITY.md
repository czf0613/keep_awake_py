# Compatibility review

## Findings addressed

| Area | Finding | Change |
| --- | --- | --- |
| Python 3.8 packaging | SPDX string `project.license` fails with setuptools versions available on 3.8 | Declare dynamic license metadata and set `license="MIT"` through setuptools; require a PEP 621/editable-capable backend |
| C compilation | `bool` depended on transitive headers that differ between CPython versions | Explicitly include `<stdbool.h>` |
| Free-threaded CPython | Native import re-enabled the GIL | Declare support with guarded `PyUnstable_Module_SetGIL`; define `Py_GIL_DISABLED` when compiling Windows free-threaded builds |
| Windows lifecycle | Every acquisition created another worker/handle; release forcibly terminated a thread | Reuse one worker; acknowledge the initial OS request; stop with an event and join; retain SRWLOCK synchronization |
| Linux dependency | `dbus-python` itself contains a C extension | Use pure Python Jeepney, retaining the `linux` extra |
| Linux initialization | Import opened a session bus and resolved the service outside error handling | Connect only when acquiring; missing/invalid/unsupported bus addresses or unavailable services return `False` |
| Linux ownership | Closing the default shared bus could affect other D-Bus users | Own and close a private connection |
| Linux release | A failed release could leave stale state with no recovery | Always disconnect and clear local state, including when the service times out |
| Linux cancellation | Interrupting an acquisition could bypass connection cleanup | Close untransferred connections in `finally`, preserving `KeyboardInterrupt`/`SystemExit` |
| Linux concurrency | Fast paths accessed shared state outside the lock | Serialize acquisition, release and transport operations under one lock |
| Linux API coverage | Only the freedesktop service was tried | Try GNOME SessionManager with suspend + idle flags, then the freedesktop interface; preserve each API's method capitalization |

Python source and stubs use Python 3.8-compatible syntax. Native code uses the
long-standing CPython API except for a guarded free-threading declaration. The
Windows worker touches no Python objects; SRWLOCK plus Windows event signaling
synchronize its state. The macOS assertion is protected by a pthread mutex.

## Verification boundaries

Unit tests cover cookies (including zero), protocol fields, fallback, malformed
responses, connection/release failures, retry and concurrent calls. Private-bus
tests send real D-Bus messages to synthetic services. Native tests exercise
concurrency, Windows handle accounting and preservation of disabled GIL state.
CI additionally compiles and installs distributions across the supported matrix.

Local verification on 2026-09-12 (macOS arm64):

- CPython 3.8–3.14: 26 tests passed per regular interpreter; the no-GIL and Windows
  handle-count tests were skipped where inapplicable.
- CPython 3.13t/3.14t: 27 tests passed per interpreter; only Windows handle counting
  was skipped. Native import left the GIL disabled.
- Python 3.8, 3.13t and 3.14t sdists/wheels built, passed `twine check`, and passed
  the same tests after installation into separate environments. The sdist includes
  both native platforms' sources/headers and typing files, without built binaries.
- `actionlint`, Python compilation, targeted Ruff error checks and lockfile
  consistency passed. Remote Windows/Linux/macOS x86_64 CI awaits the first push.

On macOS only, the private-bus tests select Linux-style authentication instead of
Jeepney's incompatible BSD credential branch. Production macOS calls the native
extension, so this adjustment is confined to the Linux protocol test harness.

No automated test here proves that a real GNOME/KDE/compositor installation will
keep the display and machine awake. Idle-inhibition support and power policy vary
by desktop. The freedesktop fallback requests idle inhibition; it does not force
system-wide suspension policy. These APIs do not override lid closure, manual
sleep or administrator policy.

The API remains process-wide and idempotent, not reference counted. Overlapping
guards can release one another's inhibitor. `KeepAwakeGuard` retains its existing
behavior of not raising when acquisition returns `False`; use `prevent_sleep()`
directly if failure must abort the operation.

There is no background monitoring of desktop/service restarts. If the session
service disappears, call `allow_sleep()` and reacquire after reconnecting. Do not
carry an active inhibitor across `fork()`; acquire inside the child instead.
D-Bus method replies have a five-second timeout; Jeepney's initial bus handshake
has its own behavior and is not covered by an overall deadline.

## Upstream references

- [CPython free-threaded extension support](https://docs.python.org/3.13/howto/free-threading-extensions.html)
- [SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate)
- [Freedesktop idle inhibition specification](https://specifications.freedesktop.org/idle-inhibit/latest/)
- [GNOME SessionManager D-Bus interface](https://github.com/GNOME/gnome-session/blob/main/gnome-session/org.gnome.SessionManager.xml)
- [Jeepney blocking I/O API](https://jeepney.readthedocs.io/en/latest/api/blocking.html)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
