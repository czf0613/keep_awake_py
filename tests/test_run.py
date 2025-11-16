from keep_awake import prevent_sleep, allow_sleep, KeepAwakeGuard


def test_no_sleep():
    assert prevent_sleep()
    assert allow_sleep() is None

    with KeepAwakeGuard():
        pass
