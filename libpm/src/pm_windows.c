#include "pm.h"
#include <windows.h>

static HANDLE h_thread = NULL;
static SRWLOCK mutex = SRWLOCK_INIT;

DWORD WINAPI run_forever(LPVOID args)
{
    do
    {
        SetThreadExecutionState(ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED);
        Sleep(5000);
    } while (h_thread != NULL);

    return 0;
}

PM_API bool prevent_sleep(void)
{
    AcquireSRWLockExclusive(&mutex);

    h_thread = CreateThread(NULL, 0, run_forever, NULL, 0, NULL);
    bool success = h_thread != NULL;

    ReleaseSRWLockExclusive(&mutex);

    return success;
}

PM_API void allow_sleep(void)
{
    AcquireSRWLockExclusive(&mutex);

    if (h_thread != NULL)
    {
        TerminateThread(h_thread, 0);
        CloseHandle(h_thread);
        h_thread = NULL;
    }

    ReleaseSRWLockExclusive(&mutex);
}