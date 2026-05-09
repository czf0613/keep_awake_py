from setuptools import setup, Extension
import sys

c_modules = []
os_platform = sys.platform

if os_platform == "win32":
    c_modules.append(
        Extension(
            "keep_awake._native_api",
            sources=["native_code/src/pm_windows.c", "native_code/src/ext.c"],
            include_dirs=["native_code/include"],
            extra_compile_args=["/utf-8"],
        )
    )
elif os_platform == "darwin":
    c_modules.append(
        Extension(
            "keep_awake._native_api",
            sources=["native_code/src/pm_macos.c", "native_code/src/ext.c"],
            include_dirs=["native_code/include"],
            extra_link_args=["-framework", "CoreFoundation", "-framework", "IOKit"],
        )
    )
elif os_platform == "linux":
    # nothing todo, native python implementation
    pass
else:
    raise ValueError("Unsupported platform")

setup(ext_modules=c_modules)
