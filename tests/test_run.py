from keep_awake import prevent_sleep, allow_sleep


def test_no_sleep():
    assert prevent_sleep()


def test_allow_sleep():
    assert allow_sleep() is None
