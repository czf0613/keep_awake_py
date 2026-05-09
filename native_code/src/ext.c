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
    return PyModule_Create(&module);
}
