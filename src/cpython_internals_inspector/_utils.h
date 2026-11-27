#ifndef cpython_internals_inspector_UTILS_H
#define cpython_internals_inspector_UTILS_H

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdarg.h>
#include <string.h>

/* Вспомогательные функции записи в PyUnicodeWriter */
int writer_write_ascii(PyUnicodeWriter *writer, const char *str);
int writer_write_format(PyUnicodeWriter *writer, const char *fmt, ...);

/* Вставляет значение поля в поддерево `parent` по ключу `#field`.
 * `parent` уже должен быть создан.
 */
#define SET_FIELD_IN(parent, expr, field, conv)                              \
    do {                                                                     \
        PyObject *_v = (conv)(expr);                                         \
        if (_v == NULL ||                                                    \
            PyDict_SetItemString((parent), #field, _v) < 0) {                \
            Py_XDECREF(_v);                                                  \
            goto error;                                                      \
        }                                                                    \
        Py_DECREF(_v);                                                       \
    } while (0)

#endif /* cpython_internals_inspector_UTILS_H */
