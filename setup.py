from setuptools import setup, Extension
import sys

c_modules = []

if sys.platform == "win32":
    c_modules.append(
        Extension(
            "keep_awake._native_api",
            sources=["libpm/src/pm_windows.c", "src/keep_awake/py_module.c"],
            include_dirs=["libpm/include"],
            extra_compile_args=["/utf-8"],
        )
    )
elif sys.platform == "darwin":
    c_modules.append(
        Extension(
            "keep_awake._native_api",
            sources=["libpm/src/pm_macos.c", "src/keep_awake/py_module.c"],
            include_dirs=["libpm/include"],
            extra_link_args=["-framework", "CoreFoundation", "-framework", "IOKit"],
        )
    )
elif sys.platform == "linux":
    # nothing todo, native python implementation
    pass
else:
    raise ValueError("Unsupported platform")

setup(ext_modules=c_modules)
