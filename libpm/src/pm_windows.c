#include "pm.h"
#include <windows.h>

static HANDLE hthread = NULL;
static SRWLOCK mutex = SRWLOCK_INIT;

// Windows下的防止休眠本质上是靠新开启一个线程来实现的
// 这个线程一直轮询防止休眠，线程停止，自然而然就恢复休眠了
DWORD WINAPI run_forever(LPVOID args)
{
    while (hthread != NULL)
    {
        SetThreadExecutionState(ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED);
        Sleep(5000);
    }

    return 0;
}

// 由于windows下的机制问题，Windows的防休眠与允许休眠都很难做到线程安全
// 高频调用的情况下，的确可能会出现内存泄漏
PM_API bool prevent_sleep(void)
{
    AcquireSRWLockExclusive(&mutex);

    hthread = CreateThread(NULL, 0, run_forever, NULL, 0, NULL);
    bool success = hthread != NULL;

    ReleaseSRWLockExclusive(&mutex);

    return success;
}

PM_API void allow_sleep(void)
{
    AcquireSRWLockExclusive(&mutex);

    if (hthread != NULL)
    {
        TerminateThread(hthread, 0);
        CloseHandle(hthread);
        hthread = NULL;
    }

    ReleaseSRWLockExclusive(&mutex);
}