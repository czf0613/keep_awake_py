#include "pm.h"
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