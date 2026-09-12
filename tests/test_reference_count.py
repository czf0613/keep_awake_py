"""Public ownership semantics, with the OS calls replaced by a small backend."""

import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from types import SimpleNamespace

import pytest

import keep_awake


class Backend:
    def __init__(self):
        self.active = False
        self.starts = 0
        self.stops = 0
        self.acquire_ok = True
        self.release_error = None

    def acquire(self):
        self.starts += 1
        if self.acquire_ok:
            self.active = True
        return self.acquire_ok

    def release(self):
        self.stops += 1
        self.active = False
        if self.release_error is not None:
            raise self.release_error


@pytest.fixture(params=["darwin", "win32", "linux"])
def backend(request, monkeypatch):
    state = Backend()
    monkeypatch.setattr(keep_awake, "os_platform", request.param)
    monkeypatch.setattr(keep_awake, "_references", 0, raising=False)
    monkeypatch.setattr(keep_awake, "_shutting_down", False, raising=False)
    monkeypatch.setitem(
        sys.modules,
        "keep_awake._native_api",
        SimpleNamespace(_prevent_sleep=state.acquire, _allow_sleep=state.release),
    )
    monkeypatch.setitem(
        sys.modules,
        "keep_awake.dbus_api",
        SimpleNamespace(session_on=state.acquire, session_off=state.release),
    )
    return state


def test_two_acquisitions_require_two_releases(backend):
    assert keep_awake.prevent_sleep()
    assert keep_awake.prevent_sleep()
    assert backend.starts == 1
    keep_awake.allow_sleep()
    assert backend.active
    assert backend.stops == 0
    keep_awake.allow_sleep()
    assert not backend.active
    assert backend.stops == 1


def test_excess_release_never_creates_negative_ownership(backend):
    keep_awake.allow_sleep()
    keep_awake.allow_sleep()
    assert backend.stops == 0
    assert keep_awake.prevent_sleep()
    keep_awake.allow_sleep()
    assert not backend.active
    assert backend.stops == 1


def test_failed_acquisition_does_not_increment_count(backend):
    backend.acquire_ok = False
    assert not keep_awake.prevent_sleep()
    keep_awake.allow_sleep()
    assert backend.stops == 0
    backend.acquire_ok = True
    assert keep_awake.prevent_sleep()
    keep_awake.allow_sleep()
    assert not backend.active


def test_failed_final_release_does_not_leave_a_stale_count(backend):
    assert keep_awake.prevent_sleep()
    backend.release_error = RuntimeError("release failed")
    with pytest.raises(RuntimeError):
        keep_awake.allow_sleep()
    assert not backend.active
    backend.release_error = None
    assert keep_awake.prevent_sleep()
    assert backend.active
    assert backend.starts == 2
    keep_awake.allow_sleep()
    assert not backend.active


def test_short_lived_thread_cannot_release_long_lived_owner(backend):
    assert keep_awake.prevent_sleep()

    def short_task():
        assert keep_awake.prevent_sleep()
        keep_awake.allow_sleep()

    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(short_task).result(timeout=5)
    assert backend.active
    keep_awake.allow_sleep()
    assert not backend.active


def test_concurrent_acquisitions_hold_until_the_last_release(backend):
    acquired = Barrier(8)
    released = Barrier(8)

    def owner(index):
        assert keep_awake.prevent_sleep()
        acquired.wait(timeout=5)
        if index != 0:
            keep_awake.allow_sleep()
        released.wait(timeout=5)
        if index == 0:
            assert backend.active
            keep_awake.allow_sleep()

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(owner, range(8)))
    assert not backend.active
    assert backend.starts == backend.stops == 1


def test_nested_reusable_guard_preserves_outer_owner(backend):
    guard = keep_awake.KeepAwakeGuard()
    with guard:
        with guard:
            assert backend.active
        assert backend.active
    assert not backend.active
    with guard:
        assert backend.active
    assert not backend.active
    assert backend.starts == backend.stops == 2


def test_guard_releases_after_body_exception(backend):
    with pytest.raises(ValueError):
        with keep_awake.KeepAwakeGuard():
            raise ValueError("work failed")
    assert not backend.active
    assert backend.stops == 1


def test_failed_guard_does_not_release_another_threads_success(backend):
    guard = keep_awake.KeepAwakeGuard()
    backend.acquire_ok = False
    owner_ready = Event()
    release_owner = Event()

    def successful_owner():
        backend.acquire_ok = True
        with guard:
            owner_ready.set()
            assert release_owner.wait(timeout=5)

    with ThreadPoolExecutor(max_workers=1) as pool:
        try:
            with guard:
                assert not backend.active
                future = pool.submit(successful_owner)
                assert owner_ready.wait(timeout=5)
            assert backend.active
        finally:
            release_owner.set()
        future.result(timeout=5)
    assert not backend.active
    assert backend.stops == 1


def test_shutdown_releases_all_references_once_and_rejects_new_work(backend):
    for _ in range(3):
        assert keep_awake.prevent_sleep()
    keep_awake._shutdown()
    assert not backend.active
    assert backend.stops == 1
    keep_awake._shutdown()
    keep_awake.allow_sleep()
    assert not keep_awake.prevent_sleep()
    assert backend.starts == backend.stops == 1


def test_shutdown_without_acquisition_does_not_touch_backend(backend):
    keep_awake._shutdown()
    assert not keep_awake.prevent_sleep()
    assert backend.starts == backend.stops == 0


def test_interrupted_shutdown_clears_ownership_and_stays_closed(backend):
    assert keep_awake.prevent_sleep()
    assert keep_awake.prevent_sleep()
    backend.release_error = KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        keep_awake._shutdown()
    assert not backend.active
    assert keep_awake._references == 0
    assert not keep_awake.prevent_sleep()
    keep_awake._shutdown()
    keep_awake.allow_sleep()
    assert backend.stops == 1


def test_shutdown_waits_for_inflight_acquisition_then_releases(backend, monkeypatch):
    entered = Event()
    finish = Event()
    acquire = keep_awake._acquire_backend

    def slow_acquire():
        entered.set()
        assert finish.wait(timeout=5)
        return acquire()

    monkeypatch.setattr(keep_awake, "_acquire_backend", slow_acquire)
    with ThreadPoolExecutor(max_workers=2) as pool:
        owner = pool.submit(keep_awake.prevent_sleep)
        try:
            assert entered.wait(timeout=5)
            shutdown = pool.submit(keep_awake._shutdown)
        finally:
            finish.set()
        assert owner.result(timeout=5)
        shutdown.result(timeout=5)
    assert not backend.active
    assert not keep_awake.prevent_sleep()
    assert backend.starts == backend.stops == 1
