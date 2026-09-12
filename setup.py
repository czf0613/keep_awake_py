from setuptools import setup, Extension
import sys
import sysconfig

c_modules = []
os_platform = sys.platform
macros = (
    [("Py_GIL_DISABLED", "1")] if sysconfig.get_config_var("Py_GIL_DISABLED") else []
)

if os_platform == "win32":
    c_modules.append(
        Extension(
            "keep_awake._native_api",
            sources=["native_code/src/pm_windows.c", "native_code/src/ext.c"],
            include_dirs=["native_code/include"],
            extra_compile_args=["/utf-8"],
            define_macros=macros,
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

# SPDX project.license strings require setuptools versions unavailable on Python 3.8.
setup(ext_modules=c_modules, license="MIT")
