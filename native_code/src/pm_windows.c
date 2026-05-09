#include "pm.h"
#include <windows.h>

static HANDLE h_thread = NULL;
static SRWLOCK mutex = SRWLOCK_INIT;

static DWORD WINAPI run_forever(LPVOID args)
{
    do
    {
        SetThreadExecutionState(ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED);
        Sleep(5000);
    } while (h_thread != NULL);

    return 0;
}

static bool prevent_sleep(void)
{
    AcquireSRWLockExclusive(&mutex);

    h_thread = CreateThread(NULL, 0, run_forever, NULL, 0, NULL);
    bool success = h_thread != NULL;

    ReleaseSRWLockExclusive(&mutex);

    return success;
}

static void allow_sleep(void)
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

PyObject *pm_prevent_sleep(PyObject *self, PyObject *args)
{
    if (prevent_sleep())
    {
        Py_RETURN_TRUE;
    }
    else
    {
        Py_RETURN_FALSE;
    }
}

PyObject *pm_allow_sleep(PyObject *self, PyObject *args)
{
    allow_sleep();
    Py_RETURN_NONE;
}
