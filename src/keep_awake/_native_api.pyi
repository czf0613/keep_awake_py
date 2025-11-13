# Native API for keep_awake module

def prevent_sleep() -> bool:
    """Prevent the system from sleeping. Returns True if successful, False otherwise.
    Now the screen will not turn off and system will not go to sleep.
    This method is concurrent-safe on macOS, not safe on Windows(for some reasons).
    """
    pass

def allow_sleep() -> None:
    """Reset the power management state. This method is concurrent-safe on macOS, not safe on Windows."""
    pass
