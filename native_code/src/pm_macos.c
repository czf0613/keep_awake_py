#include "pm.h"
#include <IOKit/pwr_mgt/IOPMLib.h>
#include <CoreFoundation/CoreFoundation.h>

/* All entry points require the public Python API's lock. */
static IOPMAssertionID sleepAssertion = kIOPMNullAssertionID;
#define reasonForActive CFSTR("需要保持系统活动以确保后台任务执行")

static bool prevent_sleep(void)
{
    bool success = true;
    if (sleepAssertion == kIOPMNullAssertionID)
    {
        IOReturn status = IOPMAssertionCreateWithName(kIOPMAssertionTypePreventUserIdleDisplaySleep, kIOPMAssertionLevelOn, reasonForActive, &sleepAssertion);

        success &= (status == kIOReturnSuccess);
    }

    return success;
}

static void allow_sleep(void)
{
    if (sleepAssertion != kIOPMNullAssertionID)
    {
        IOPMAssertionRelease(sleepAssertion);
        sleepAssertion = kIOPMNullAssertionID;
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
