# Compatibility review

## Findings addressed

| Area | Finding | Change |
| --- | --- | --- |
| Python 3.8 packaging | SPDX string `project.license` fails with setuptools versions available on 3.8 | Declare dynamic license metadata and set `license="MIT"` through setuptools; require a PEP 621/editable-capable backend |
| C compilation | `bool` depended on transitive headers that differ between CPython versions | Explicitly include `<stdbool.h>` |
| Free-threaded CPython | Native import re-enabled the GIL | Declare support with guarded `PyUnstable_Module_SetGIL`; define `Py_GIL_DISABLED` when compiling Windows free-threaded builds |
| Windows lifecycle | Every acquisition created another worker/handle; release forcibly terminated a thread | Reuse one worker; acknowledge the initial OS request; stop with an event and join; serialize callers through the public Python lock |
| Linux dependency | `dbus-python` itself contains a C extension | Use pure Python Jeepney, retaining the `linux` extra |
| Linux initialization | Import opened a session bus and resolved the service outside error handling | Connect only when acquiring; missing/invalid/unsupported bus addresses or unavailable services return `False` |
| Linux ownership | Closing the default shared bus could affect other D-Bus users | Own and close a private connection |
| Linux release | A failed release could leave stale state with no recovery | Always disconnect and clear local state, including when the service times out |
| Linux cancellation | Interrupting an acquisition could bypass connection cleanup | Close untransferred connections in `finally`, preserving `KeyboardInterrupt`/`SystemExit` |
| Linux concurrency | Fast paths accessed shared state outside the lock | Serialize acquisition, release and transport operations under one lock |
| Linux API coverage | Only the freedesktop service was tried | Try GNOME SessionManager with suspend + idle flags, then the freedesktop interface; preserve each API's method capitalization |
| Public ownership | One caller's release could cancel another caller's active work | Count successful acquisitions under a Python lock; release the OS inhibitor only at zero; guards track successful entries per thread |
| Interpreter exit | Only Linux registered cleanup; one public release would leave multiple references active | Register a shared exit handler in the public module, release all outstanding references, and reject later acquisitions |
| Windows ARM64 | No native ARM64 CI or release wheels | Add six native Windows ARM64 jobs (Python 3.11–3.14 and 3.13t/3.14t), with an architecture assertion |
| ARM64 interpreter selection | Version-only uv requests selected emulated x64 Python for three ARM64 jobs | Explicitly request `cpython-<version>-windows-aarch64-none` for all ARM64 build/test commands, retaining the architecture assertion |

Python source and stubs use Python 3.8-compatible syntax. Native code uses the
long-standing CPython API except for a guarded free-threading declaration. The
public Python lock serializes all native entry points. The Windows worker touches
no Python objects; ready/stop event signaling and joining synchronize its state
with the caller. Redundant C mutexes have been removed. Direct private extension
calls bypass this protection and are unsupported. The
extension uses process-global C state (`m_size = -1`); subinterpreter ownership
is not supported by this design.

## Verification boundaries

Unit tests cover cookies (including zero), protocol fields, fallback, malformed
responses, connection/release failures, retry and concurrent calls. Private-bus
tests send real D-Bus messages to synthetic services. Native tests exercise
concurrency, Windows handle accounting and preservation of disabled GIL state.
CI additionally compiles and installs distributions across the supported matrix.

Local verification on 2026-09-12 (macOS arm64):

- CPython 3.8–3.14: 78 tests passed per regular interpreter; the no-GIL and Windows
  handle-count tests were skipped where inapplicable.
- CPython 3.13t/3.14t: 79 tests passed per interpreter; only Windows handle counting
  was skipped. Native import left the GIL disabled.
- Reference-count checks include real Linux cleanup after an interrupted final
  release; the next acquisition must contact the backend again. Independent review
  confirmed the final count and backend lifecycle agree.
- Subprocess tests verify shared exit cleanup, actual macOS native release and
  GNOME/freedesktop release messages on the private bus. Native concurrency tests
  use the supported public API, including on free-threaded Python.
- Python 3.8 and 3.14t sdists/wheels built, passed `twine check`, and passed
  the same tests after installation into separate environments. The sdist includes
  both native platforms' sources/headers and typing files, without built binaries.
- `actionlint`, Python compilation, targeted Ruff error checks and lockfile
  consistency passed. Remote CI runs Windows x86_64/ARM64, Linux and macOS x86_64
  checks; the local results above do not cover those environments.

On macOS only, the private-bus tests select Linux-style authentication instead of
Jeepney's incompatible BSD credential branch. Production macOS calls the native
extension, so this adjustment is confined to the Linux protocol test harness.

No automated test here proves that a real GNOME/KDE/compositor installation will
keep the display and machine awake. Idle-inhibition support and power policy vary
by desktop. The freedesktop fallback requests idle inhibition; it does not force
system-wide suspension policy. These APIs do not override lid closure, manual
sleep or administrator policy.

The public API now maintains a shared reference count: each successful acquisition
requires one release. Nested and overlapping guards release their own successful
entries, including when one guard is shared across threads. Private backends remain
idempotent and are invoked only on the first acquisition and final release.
`KeepAwakeGuard` retains its nonraising acquisition-failure behavior; use
`prevent_sleep()` directly if failure must abort the operation. A mismatched manual
release can still consume another owner's reference, so callers must balance only
successful acquisitions and must not manually release a guard's reference.

The public module owns the only `atexit` handler. It serializes with API calls,
releases the backend once regardless of the remaining reference count, and
rejects new acquisitions after cleanup begins. Importing without acquiring does
not load or contact a backend on exit. This covers normal interpreter shutdown,
including `sys.exit()` and an uncaught Python exception. It does not run after
unhandled termination signals, fatal interpreter errors or `os._exit()`.

There is no background monitoring of desktop/service restarts. If the session
service disappears, call `allow_sleep()` and reacquire after reconnecting. Do not
carry an active inhibitor across `fork()`; acquire inside the child instead.
D-Bus method replies have a five-second timeout; Jeepney's initial bus handshake
has its own behavior and is not covered by an overall deadline.

## Upstream references

- [CPython free-threaded extension support](https://docs.python.org/3.13/howto/free-threading-extensions.html)
- [CPython module state and subinterpreters](https://docs.python.org/3/c-api/module.html)
- [Python exit handlers and their limits](https://docs.python.org/3/library/atexit.html)
- [SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate)
- [Freedesktop idle inhibition specification](https://specifications.freedesktop.org/idle-inhibit/latest/)
- [GNOME SessionManager D-Bus interface](https://github.com/GNOME/gnome-session/blob/main/gnome-session/org.gnome.SessionManager.xml)
- [Jeepney blocking I/O API](https://jeepney.readthedocs.io/en/latest/api/blocking.html)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
- [GitHub hosted runners, including Windows ARM64](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [uv Python variants and architecture selection](https://docs.astral.sh/uv/concepts/python-versions/)
