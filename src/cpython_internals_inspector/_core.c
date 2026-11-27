#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "_dict.h"

/* ------------------------------------------------------------------ */
/* Точка входа                                                        */
/* ------------------------------------------------------------------ */

static PyObject *
cpython_internals_inspector_get_structure(PyObject *self, PyObject *obj)
{
    if (PyDict_Check(obj)) {
        return get_dict_structure(NULL, obj);
    }
    PyErr_Format(PyExc_TypeError,
                 "get_structure() does not support type '%s' yet",
                 Py_TYPE(obj)->tp_name);
    return NULL;
}


static PyMethodDef cpython_internals_inspector_methods[] = {
    {"get_structure", cpython_internals_inspector_get_structure, METH_O,
     "Get dictionary structure."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef cpython_internals_inspectormodule = {
    PyModuleDef_HEAD_INIT,
    "cpython_internals_inspector",
    "Memory layout analyzer for CPython objects.",
    -1,
    cpython_internals_inspector_methods
};

PyMODINIT_FUNC
PyInit__core(void)
{
    return PyModule_Create(&cpython_internals_inspectormodule);
}
