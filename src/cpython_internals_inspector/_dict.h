#ifndef cpython_internals_inspector_DICT_H
#define cpython_internals_inspector_DICT_H

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "pycore_dict.h"

/* Собирает информацию о PyDictObject и возвращает новый dict.
 * Вызывающий владеет ссылкой на возвращённый словарь.
 */
PyObject *get_dict_structure(PyObject *self, PyObject *obj);

#endif /* cpython_internals_inspector_DICT_H */
