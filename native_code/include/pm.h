#ifndef PM_H
#define PM_H

#include <Python.h>

PyObject *pm_prevent_sleep(PyObject *self, PyObject *args);

PyObject *pm_allow_sleep(PyObject *self, PyObject *args);

#endif // PM_H
