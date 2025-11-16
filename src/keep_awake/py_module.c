#include <Python.h>
#include "pm.h"

static PyObject *py_prevent_sleep(PyObject *obj, PyObject *args)
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

static PyObject *py_allow_sleep(PyObject *obj, PyObject *args)
{
    allow_sleep();
    Py_RETURN_NONE;
}

static PyMethodDef ModMethods[] = {
    {"_prevent_sleep", py_prevent_sleep, METH_NOARGS, NULL},
    {"_allow_sleep", py_allow_sleep, METH_NOARGS, NULL},
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