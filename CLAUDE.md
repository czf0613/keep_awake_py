# CLAUDE.md

## Network Access

This repository is hosted on GitHub, which is not accessible in some countries. If there's a network issue, set the HTTP proxy and HTTPS proxy to `localhost:7890`:

```bash
export http_proxy=http://localhost:7890
export https_proxy=http://localhost:7890
```

## Package Manager

We use `uv` to manage this project. Always use `uv` commands for project operations:

- `uv run` to execute scripts and commands
- `uv add` to add dependencies
- `uv sync` to sync the environment

## Building

Build the C extension in-place before running or testing:

```bash
uv run setup.py build_ext --inplace
```

On Linux, no C extension is needed — the implementation uses pure Python with D-Bus.

## Testing

Tests are in the `tests/` directory. Run tests with:

```bash
uv run pytest tests/test_run.py -v -s
```

Only run the full suite (`uv run pytest -v -s`) when explicitly asked or before a commit/push.

## Project Structure

```
native_code/
  CMakeLists.txt      # IDE hints only, NOT for building
  include/
    pm.h              # Header declaring Python-level wrapper functions
  src/
    ext.c             # Python module entry point (method table + init)
    pm_macos.c        # macOS implementation (IOKit + CoreFoundation)
    pm_windows.c      # Windows implementation (SetThreadExecutionState)
src/
  keep_awake/
    __init__.py       # Public API: prevent_sleep, allow_sleep, KeepAwakeGuard
    _native_api.pyi   # Type stubs for the C extension
    dbus_api.py       # Linux implementation (pure Python, D-Bus)
    py.typed          # PEP 561 marker
```

The `CMakeLists.txt` is **only** for IDE code navigation and hints (e.g. CLion, VS Code IntelliSense). Do **not** use CMake to build this project. Always build via `setup.py` (which is invoked automatically by `uv` / `pip`).

## Documentation

Write docstrings and type annotations in the `.pyi` stub files, not in C code. Every public function exposed by the C extension must have a corresponding annotated entry in the `.pyi` file.

## C Code Style

- **No docstrings in C method tables.** Pass `NULL` for the `ml_doc` field in `PyMethodDef`. All documentation belongs in the `.pyi` stub files.
- **Declare variables near first use.** Do not group declarations at the top of a function.
- **Always use braces for control flow.** Every `if`, `else`, `for`, and `while` body must be wrapped in `{}`, even if it is a single statement.
