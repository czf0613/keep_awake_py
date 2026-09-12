#include <Python.h>
#include "pm.h"

static PyMethodDef ModMethods[] = {
    {"_prevent_sleep", pm_prevent_sleep, METH_NOARGS, NULL},
    {"_allow_sleep", pm_allow_sleep, METH_NOARGS, NULL},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "_native_api",
    NULL,
    -1,
    ModMethods};

PyMODINIT_FUNC PyInit__native_api(void)
{
    PyObject *m = PyModule_Create(&module);
    if (m == NULL)
    {
        return NULL;
    }
#ifdef Py_GIL_DISABLED
    PyUnstable_Module_SetGIL(m, Py_MOD_GIL_NOT_USED);
#endif
    return m;
}
