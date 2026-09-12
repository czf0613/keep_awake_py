#include "pm.h"
#include <windows.h>

/* All entry points require the public Python API's lock.
 * The ready/stop events synchronize communication with the native worker. */
static HANDLE h_thread = NULL;
static HANDLE stop_event = NULL;
static HANDLE ready_event = NULL;
static bool started = false;

static DWORD WINAPI run_forever(LPVOID args)
{
    started = SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED) != 0;
    SetEvent(ready_event);
    if (started)
    {
        WaitForSingleObject(stop_event, INFINITE);
        SetThreadExecutionState(ES_CONTINUOUS);
    }
    return 0;
}

/* Called with the public Python lock held, after any worker has exited. */
static void close_handles(void)
{
    if (h_thread != NULL)
    {
        CloseHandle(h_thread);
        h_thread = NULL;
    }
    if (stop_event != NULL)
    {
        CloseHandle(stop_event);
        stop_event = NULL;
    }
    if (ready_event != NULL)
    {
        CloseHandle(ready_event);
        ready_event = NULL;
    }
}

static bool prevent_sleep(void)
{
    if (h_thread != NULL)
    {
        return true;
    }
    stop_event = CreateEventW(NULL, TRUE, FALSE, NULL);
    ready_event = CreateEventW(NULL, TRUE, FALSE, NULL);
    if (stop_event == NULL || ready_event == NULL)
    {
        close_handles();
        return false;
    }
    started = false;
    h_thread = CreateThread(NULL, 0, run_forever, NULL, 0, NULL);
    if (h_thread == NULL)
    {
        close_handles();
        return false;
    }
    WaitForSingleObject(ready_event, INFINITE);
    bool success = started;
    if (!success)
    {
        WaitForSingleObject(h_thread, INFINITE);
        close_handles();
    }
    return success;
}

static void allow_sleep(void)
{
    if (h_thread != NULL)
    {
        SetEvent(stop_event);
        WaitForSingleObject(h_thread, INFINITE);
        close_handles();
    }
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
