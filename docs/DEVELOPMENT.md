# Development and releases

## Local checks

Use [uv](https://docs.astral.sh/uv/) and a C compiler on Windows/macOS. The default
interpreter is selected by `.python-version`; the minimum supported version is
independently defined as Python 3.8 in `pyproject.toml`.

```sh
uv sync --frozen
uv run setup.py build_ext --inplace  # after editing native code
uv run --frozen python -m compileall -q src tests setup.py
uv run --frozen pytest -q
uv build
uvx twine check dist/*

# Isolated environments avoid replacing the main development environment.
uv run --isolated --python 3.8 --frozen pytest -q
uv run --isolated --python 3.13t --frozen pytest -q
uv run --isolated --python 3.14t --frozen pytest -q
```

The isolated commands rebuild/install the project for their interpreter. Native
extension imports are tested without forcing the GIL off; enabling it on import
is a test failure. Each release requires distinct wheels for normal and
free-threaded CPython.

On Linux, install `dbus-daemon` to run the private-bus integration tests. They use
synthetic GNOME/freedesktop services and do not contact the real desktop. To check
actual desktop behavior in your own logged-in session:

```sh
uv sync --extra linux
KEEP_AWAKE_DESKTOP_TEST=1 uv run pytest tests/test_run.py -v
```

This smoke test checks API success and cleanup. Confirm display/system idle
behavior separately over a configured idle interval; a successful API call does
not prove desktop policy honored the request.

## CI

`.github/workflows/ci.yml` runs on pushes and pull requests to `master`, can be
started manually, and is reused by the release workflow. Its 42 jobs cover:

- CPython 3.8–3.14 and free-threaded 3.13t/3.14t.
- Ubuntu x86_64, Windows x86_64, macOS x86_64 and macOS arm64.
- Windows ARM64 on `windows-11-arm`: Python 3.11–3.14 and 3.13t/3.14t, the native
  versions available through uv. CI asserts `sysconfig.get_platform() == 'win-arm64'`
  to reject accidental x64 emulation. These six jobs also contribute release wheels.
- Python/stub compilation, native extension compilation, tests, sdist/wheel
  builds, distribution metadata, and testing a separately installed wheel.

Linux desktop smoke tests are opt-in; private D-Bus service tests run on Ubuntu.
Windows uses MSVC via setuptools. CMake remains an IDE-only file.

Public reference-count tests cover the two-thread ownership scenario, concurrent
acquisition/release, nested/shared guards and failed requests on all three backend
routes. Private backends stay idempotent: tests invoking private entry points must
not assume they maintain public ownership counts.
Exit tests use real subprocess termination, including `sys.exit()` and uncaught
exceptions, and verify that later exit callbacks cannot reacquire. Native tests
observe the actual C release call; private-bus tests verify that interpreter exit
sends the corresponding GNOME/freedesktop release message.

## Publish to PyPI

Trusted Publisher configuration for the existing `keep-awake` project:

| Field | Value |
| --- | --- |
| GitHub owner | `czf0613` |
| Repository | `keep_awake_py` |
| Workflow filename | `publish.yml` |
| GitHub environment | `pypi` |

The workflow uses GitHub OIDC with `id-token: write` only in the publishing job.
No PyPI API token is required. Keep these names in sync with the PyPI publisher
and GitHub environment if renaming the repository/workflow.

1. Update `[project].version` in `pyproject.toml` to an unused version, then update
   the lockfile. Version `1.1.3` already exists on PyPI and cannot be overwritten.
2. Run checks, commit and push the approved changes to `master`.
3. Create a tag matching the version (for example `1.1.4` or `v1.1.4`) and publish
   its GitHub Release. A draft or an ordinary push does not publish to PyPI.
4. `publish.yml` checks tag/version equality, runs the complete CI matrix, then
   uploads the sdist and Windows/macOS wheels. Published prereleases also trigger
   this workflow; use an appropriate prerelease package version if intended.

Linux installs from the portable sdist and compiles no project C code. Do not
publish the Linux-generated `py3-none-any` wheel: it would also be selected on
Windows/macOS without a matching native wheel, where `_native_api` would be missing.

Uploading an existing filename/version fails rather than silently skipping it.
If a publish partially succeeds, inspect PyPI before retrying. Installing and
testing the workflow locally does not establish that remote CI or OIDC upload has
run successfully; those are verified by the first authorized push/release.

## Compatibility review

See [COMPATIBILITY.md](COMPATIBILITY.md) for findings, upstream references and
the limits of automated verification.
