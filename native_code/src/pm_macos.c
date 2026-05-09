#include "pm.h"
#include <pthread.h>
#include <IOKit/pwr_mgt/IOPMLib.h>
#include <CoreFoundation/CoreFoundation.h>

static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static IOPMAssertionID sleepAssertion = kIOPMNullAssertionID;
#define reasonForActive CFSTR("需要保持系统活动以确保后台任务执行")

static bool prevent_sleep(void)
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

static void allow_sleep(void)
{
    pthread_mutex_lock(&lock);

    if (sleepAssertion != kIOPMNullAssertionID)
    {
        IOPMAssertionRelease(sleepAssertion);
        sleepAssertion = kIOPMNullAssertionID;
    }

    pthread_mutex_unlock(&lock);
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
