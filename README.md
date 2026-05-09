# Keep Awake

Prevent your system and screen from going to sleep. Useful for long-running computations, downloads, or any task that requires the system to stay active.

## Installation

```shell
pip install keep_awake
```

On Linux, install with the `linux` extra to pull in the D-Bus dependency:

```shell
pip install keep_awake[linux]
```

## Usage

```python
from keep_awake import prevent_sleep, allow_sleep

prevent_sleep()  # returns True if successful
# ... do your long-running work ...
allow_sleep()
```

Or use the context manager for automatic cleanup:

```python
from keep_awake import KeepAwakeGuard

with KeepAwakeGuard():
    # system stays awake within this block
    pass
```

### Notes

- `prevent_sleep()` returns a `bool` indicating success.
- `allow_sleep()` is safe to call multiple times or without a prior `prevent_sleep()`.
- If the process exits without calling `allow_sleep()`, the system will resume normal power management automatically.
- All methods are thread-safe on every platform.

## Supported Platforms

| Platform | Architecture | Implementation |
|----------|-------------|----------------|
| macOS | arm64, x86_64 | IOKit + CoreFoundation (C extension) |
| Windows | x86_64 | SetThreadExecutionState (C extension) |
| Linux | any | D-Bus (`org.freedesktop.ScreenSaver`), supports GNOME & KDE |

### Linux Prerequisites

If `pip install keep_awake[linux]` fails, install these system packages first:

```shell
# Debian / Ubuntu
sudo apt install cmake pkg-config libdbus-1-dev libglib2.0-dev

# Fedora
sudo dnf install cmake pkg-config dbus-devel glib2-devel
```

## Development

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```shell
# Build
uv build

# Build C extension in-place (macOS / Windows only)
uv run setup.py build_ext --inplace

# Run tests
uv run pytest
```

## License

MIT
