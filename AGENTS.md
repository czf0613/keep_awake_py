# Repository guidance for Codex

## Scope and layout

`keep_awake` prevents idle sleep through a small, synchronous Python API.
Support CPython 3.8 and later, including free-threaded 3.13/3.14 builds.

- `src/keep_awake/__init__.py`: public `prevent_sleep`, `allow_sleep`, `KeepAwakeGuard`.
- `src/keep_awake/dbus_api.py`: Linux D-Bus implementation using pure Python Jeepney.
- `src/keep_awake/_native_api.pyi`: native API annotations and docstrings.
- `native_code/src/ext.c`: CPython module initialization.
- `native_code/src/pm_macos.c`: IOKit assertions serialized by the public Python API.
- `native_code/src/pm_windows.c`: a synchronized worker owning Windows execution state.
- `tests/`: unit tests, private D-Bus protocol tests, and native smoke tests.
- `.github/workflows/`: compatibility CI and PyPI Trusted Publishing.

Use the standard filename `AGENTS.md` for these instructions. Keep user-facing
documentation in `README.md` and maintenance instructions in `docs/DEVELOPMENT.md`.

## Commands

Use `uv` for dependency management, execution and builds:

```sh
uv sync --frozen
uv run --frozen pytest -q
uv build
```

`uv sync` builds the editable C extension automatically on Windows/macOS. When
editing C code, explicitly rebuild before testing: `uv run setup.py build_ext --inplace`.
Linux has no project C extension. `native_code/CMakeLists.txt` is for IDE hints
only; never use CMake to build this package.

Run relevant tests during changes and the complete suite before claiming repository
verification or committing. The normal suite is safe without a Linux desktop:
the integration tests start a private D-Bus daemon and synthetic services. Never
assume these tests demonstrate actual desktop power-management behavior. Real
Linux desktop tests require `KEEP_AWAKE_DESKTOP_TEST=1` and the `linux` extra.
Native smoke tests briefly acquire and release actual power assertions.

After changing dependencies, run `uv lock --default-index https://pypi.org/simple`
and include the updated `uv.lock`. Check Python 3.8 and free-threaded Python in
addition to the development interpreter; see `docs/DEVELOPMENT.md`.

## Implementation contracts

- Preserve `requires-python = ">=3.8"`; avoid newer syntax and unguarded newer APIs.
- The public API uses a shared reference count under a Python lock. Each successful
  `prevent_sleep()` requires one `allow_sleep()`. Only 0-to-1 and 1-to-0 transitions
  call the backend. Failed acquisition does not count; release at zero is a no-op.
- Private native/D-Bus backends remain idempotent. Do not add a second counter there.
  Guards must track successful entries per thread and support nesting; failed
  entries must not release another caller's reference.
- The public Python lock serializes reference ownership and native C entry points,
  including no-GIL builds. Do not add a redundant C mutex. Direct private extension
  calls are unsupported and have no concurrency guarantee. Windows ready/stop
  events are still required to synchronize communication with its native worker.
- Register exit cleanup only in the public module. On interpreter exit, release
  all remaining references once under its lock and reject subsequent acquisitions.
  Do not use a single `allow_sleep()` as the exit handler: it only releases one
  reference. Backends must not register their own exit handlers.
- D-Bus calls must use a private connection, retain it while inhibited, and close
  it on failure/release. Do not connect during module import or close another
  library's shared session bus.
- Keep the Linux dependency pure Python. Do not replace it with a native binding
  without revisiting Python-version and no-GIL support.
- Use `Py_GIL_DISABLED` guards for free-threading APIs, and define the macro for
  Windows builds based on `sysconfig`. Do not force `PYTHON_GIL=0` to hide missing
  extension support in tests.
- Include C standard headers explicitly. Declare variables near first use and
  always use braces around control-flow bodies.
- Keep `ml_doc` as `NULL` in C method tables. Document each exposed native function
  with annotations in `_native_api.pyi`.
- CI includes native Windows ARM64 on `windows-11-arm`, Python 3.11–3.14 and
  3.13t/3.14t. Preserve the architecture assertion so x64 emulation cannot pass as
  ARM64 coverage. Use an explicit `cpython-<version>-windows-aarch64-none` request
  throughout those jobs; a version-only request can select x64 Python under
  emulation. Older Python versions remain covered on Windows x86_64.
- macOS CI must use explicitly selected, uv-managed single-architecture Python
  and matching `ARCHFLAGS`. Check both the wheel tag and its binary with `lipo`.
  Never merge artifact downloads into one directory: duplicate filenames can be
  written concurrently. Assemble distributions sequentially and reject duplicates.
- Preserve unrelated local changes. Commit, push, and actual release publication
  are distinct actions; do them only when requested.

## Network access

If GitHub access fails and the local proxy is available, retry the affected command
with `http_proxy=http://localhost:7890` and `https_proxy=http://localhost:7890`.
Do not bake local proxy or mirror settings into published packages or CI.
