#include "pm.h"
#include <windows.h>

static volatile bool flag = false;

// Windows下的防止休眠本质上是靠新开启一个线程来实现的
// 这个线程一直轮询防止休眠
DWORD WINAPI run_forever(LPVOID arg)
{
    while (flag)
    {
        SetThreadExecutionState(ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED);
        Sleep(1000);
    }

    return 0;
}

// 由于windows下的机制问题，Windows的防休眠与允许休眠都很难做到线程安全
// 高频调用的情况下，的确可能会出现内存泄漏
PM_API bool prevent_sleep(void)
{
    flag = true;
    HANDLE handle = CreateThread(NULL, 0, run_forever, NULL, 0, NULL);
    return handle != NULL;
}

PM_API void allow_sleep(void)
{
    flag = false;
}