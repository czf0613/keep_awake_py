# Native API for keep_awake module

def _prevent_sleep() -> bool:
    """Prevent the system from sleeping. Returns True if successful, False otherwise.
    Now the screen will not turn off and system will not go to sleep.
    Requires the public Python API's lock, including on free-threaded CPython.
    Direct calls to this private extension are unsupported and are not synchronized.
    Repeated calls share one process-wide inhibitor; they are not reference counted.
    The public Python API manages reference counting around this private backend.
    """
    pass

def _allow_sleep() -> None:
    """Release the inhibitor; requires the public Python API's lock.

    Sequential repeated releases are safe. Direct calls are unsupported.
    """
    pass
