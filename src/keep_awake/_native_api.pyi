# Native API for keep_awake module

def _prevent_sleep() -> bool:
    """Prevent the system from sleeping. Returns True if successful, False otherwise.
    Now the screen will not turn off and system will not go to sleep.
    Calls are synchronized on macOS and Windows, including free-threaded CPython.
    Repeated calls share one process-wide inhibitor; they are not reference counted.
    """
    pass

def _allow_sleep() -> None:
    """Release the process-wide inhibitor. Safe to call repeatedly or from another thread."""
    pass
