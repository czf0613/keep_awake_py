#include "pm.h"

#ifdef __APPLE__
#include <pthread.h>
#include <IOKit/pwr_mgt/IOPMLib.h>
#include <CoreFoundation/CoreFoundation.h>

static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static IOPMAssertionID sleepAssertion = kIOPMNullAssertionID;
#define reasonForActive CFSTR("需要保持系统活动以确保后台任务执行")

PM_API bool prevent_sleep(void)
{
    pthread_mutex_lock(&lock);

    bool success = true;
    if (sleepAssertion == kIOPMNullAssertionID)
    {
        IOReturn status = IOPMAssertionCreateWithName(kIOPMAssertionTypePreventUserIdleDisplaySleep, kIOPMAssertionLevelOn, reasonForActive, &sleepAssertion);

        success &= (status == kIOReturnSuccess);
    }

    pthread_mutex_unlock(&lock);
    return success;
}

PM_API void allow_sleep(void)
{
    pthread_mutex_lock(&lock);

    if (sleepAssertion != kIOPMNullAssertionID)
    {
        IOPMAssertionRelease(sleepAssertion);
        sleepAssertion = kIOPMNullAssertionID;
    }

    pthread_mutex_unlock(&lock);
}
#endif // __APPLE__

#ifdef _Win32
#include <windows.h>

static volatile bool flag = false;

// Windows下的防止休眠本质上是靠新开启一个线程来实现的
// 这个线程一直轮询防止休眠
static void run_forever(void)
{
    while (flag)
    {
        SetThreadExecutionState(ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED);
        Sleep(1000);
    }
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
#endif // _Win32