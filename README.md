# Keep Awake

Keep your system on and screen on, it will not fall asleep. It is useful in some long term calculations.



## How to use?

```shell
pip install keep_awake==1.0.2
```

This module exposes only two methods: `prevent_sleep` and `allow_sleep`, both of them taks no arguments.

`prevent_sleep` returns a boolean value that indicates whether the operation is successful. After you call this method, your system and screen will keep working until you invoke `allow_sleep`.

You won't have any exceptions by calling any methods twice, or calling `allow_sleep` without calling `prevent_sleep`, they have built-in protection.

If you forget to call `allow_sleep` before exiting your program, it doesn't matter, it will back to usual once the module is released.



## Supported platforms

### macOS✅

Both arm64 and x64 are OK, this code only depends on `IOKit` and `CoreFoundation`, which is built-in macOS Framework.

Methods on macOS are concurrent safe.



### Windows✅

We didn't test widely on various versions of Windows because I have no Windows computer :(

But basically, it can work fine on `Windows 10 x64` and `Windows 11 x64`. I have already tested.

Keeping system awake on Windows needs a dedicated thread to loop periodically, so it is hard to perform concurrent-control. Do NOT try any race condition on Windows!



### Linux❌

Planning to do, but Linux distros are very complicated, we are still finding some way to implement.



## Building & Debugging

We use `uv` to manage the project, so it is very easy to build and test it.

For building:

```shell
uv build
```

For testing

```shell
uv run pytest
```

