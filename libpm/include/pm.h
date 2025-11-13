#ifndef PM_H
#define PM_H

#include <stdbool.h>

#ifdef _Win32
#define PM_API __declspec(dllexport)
#else
#define PM_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

    PM_API bool prevent_sleep(void);

    PM_API void allow_sleep(void);

#ifdef __cplusplus
}
#endif

#endif // PM_H