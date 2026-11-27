#include "_utils.h"

/* ------------------------------------------------------------------ */
/* Вспомогательные функции записи в PyUnicodeWriter                    */
/* ------------------------------------------------------------------ */

int
writer_write_ascii(PyUnicodeWriter *writer, const char *str)
{
    return PyUnicodeWriter_WriteASCII(writer, str, (Py_ssize_t)strlen(str));
}

int
writer_write_format(PyUnicodeWriter *writer, const char *fmt, ...)
{
    va_list vargs;
    va_start(vargs, fmt);
    PyObject *s = PyUnicode_FromFormatV(fmt, vargs);
    va_end(vargs);
    if (s == NULL) {
        return -1;
    }
    int ret = PyUnicodeWriter_WriteStr(writer, s);
    Py_DECREF(s);
    return ret;
}
