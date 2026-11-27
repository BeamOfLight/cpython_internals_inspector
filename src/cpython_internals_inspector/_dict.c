#include "_dict.h"
#include "_utils.h"

/* ------------------------------------------------------------------ */
/* Чтение dk_indices                                                   */
/* ------------------------------------------------------------------ */

/* Читает элемент dk_indices по индексу i.
 * base    — указатель на начало dk_indices (char dk_indices[])
 * i       — позиция в массиве индексов
 * elem_size — размер элемента в байтах (1, 2, 4 или 8)
 *
 * Возвращает значение слота: >= 0 — индекс записи в dk_entries,
 * DKIX_EMPTY (-1) или DKIX_DUMMY (-2).
 */
static Py_ssize_t
read_dict_index(const char *base, Py_ssize_t i, int elem_size)
{
    switch (elem_size) {
    case 1:
        return (Py_ssize_t)((const int8_t *)base)[i];
    case 2:
        return (Py_ssize_t)((const int16_t *)base)[i];
    case 4:
        return (Py_ssize_t)((const int32_t *)base)[i];
    default:
        return (Py_ssize_t)((const int64_t *)base)[i];
    }
}

/* Создаёт список значений из dk_indices.
 * base      — указатель на начало dk_indices (char dk_indices[])
 * count     — количество элементов (dk_size)
 * elem_size — размер элемента в байтах (1, 2, 4 или 8)
 *
 * Возвращает новый список Py_ssize_t-значений (DKIX_EMPTY/DKIX_DUMMY
 * сохраняются как -1/-2) или NULL при ошибке.
 */
static PyObject *
build_dict_indices_list(const char *base, Py_ssize_t count, int elem_size)
{
    PyObject *list = PyList_New(count);
    if (list == NULL) {
        return NULL;
    }

    for (Py_ssize_t i = 0; i < count; i++) {
        Py_ssize_t val = read_dict_index(base, i, elem_size);
        PyObject *item = PyLong_FromSsize_t(val);
        if (item == NULL) {
            Py_DECREF(list);
            return NULL;
        }
        PyList_SET_ITEM(list, i, item);
    }

    return list;
}

/* ------------------------------------------------------------------ */
/* Построение списка записей dk_entries                                */
/* ------------------------------------------------------------------ */

/* Создаёт список записей из dk_entries.
 * keys  — указатель на PyDictKeysObject
 *
 * Возвращает новый список словарей или NULL при ошибке.
 */
static PyObject *
build_dict_entries_list(PyDictKeysObject *keys)
{
    PyObject *entries_list = PyList_New(0);
    if (entries_list == NULL) {
        return NULL;
    }

    if (keys->dk_kind == DICT_KEYS_GENERAL) {
        PyDictKeyEntry *entries = DK_ENTRIES(keys);
        for (Py_ssize_t i = 0; i < keys->dk_nentries; i++) {
            PyObject *key = entries[i].me_key;
            PyObject *value = entries[i].me_value;
            Py_hash_t hash = entries[i].me_hash;

            if (key == NULL) {
                PyList_Append(entries_list, Py_None);
                continue;
            }

            PyObject *item = PyDict_New();
            if (item == NULL) {
                goto error;
            }

            PyObject *py_hash = PyLong_FromSsize_t(hash);
            if (py_hash == NULL ||
                PyDict_SetItemString(item, "hash", py_hash) < 0) {
                Py_XDECREF(py_hash);
                Py_DECREF(item);
                goto error;
            }
            Py_DECREF(py_hash);

            if (PyDict_SetItemString(item, "key_from_ptr", key) < 0 ||
                PyDict_SetItemString(item, "value_from_ptr",
                    value != NULL ? value : Py_None) < 0) {
                Py_DECREF(item);
                goto error;
            }

            if (PyList_Append(entries_list, item) < 0) {
                Py_DECREF(item);
                goto error;
            }
            Py_DECREF(item);
        }
    } else {
        /* UNICODE или SPLIT */
        PyDictUnicodeEntry *entries = DK_UNICODE_ENTRIES(keys);
        for (Py_ssize_t i = 0; i < keys->dk_nentries; i++) {
            PyObject *key = entries[i].me_key;
            PyObject *value = NULL;

            if (keys->dk_kind == DICT_KEYS_UNICODE) {
                value = entries[i].me_value;
            }

            if (key == NULL) {
                PyList_Append(entries_list, Py_None);
                continue;
            }

            PyObject *item = PyDict_New();
            if (item == NULL) {
                goto error;
            }

            if (PyDict_SetItemString(item, "key_from_ptr", key) < 0 ||
                PyDict_SetItemString(item, "value_from_ptr",
                    value != NULL ? value : Py_None) < 0) {
                Py_DECREF(item);
                goto error;
            }

            if (PyList_Append(entries_list, item) < 0) {
                Py_DECREF(item);
                goto error;
            }
            Py_DECREF(item);
        }
    }

    return entries_list;

error:
    Py_DECREF(entries_list);
    return NULL;
}

/* ------------------------------------------------------------------ */
/* Построение ma_keys                                                  */
/* ------------------------------------------------------------------ */

/* Создаёт и заполняет словарь с данными из PyDictKeysObject.
 * keys      — указатель на PyDictKeysObject
 * dk_size   — размер таблицы индексов (1 << dk_log2_size)
 * elem_size — размер элемента dk_indices в байтах
 *
 * Возвращает новый dict или NULL при ошибке.
 */
static PyObject *
build_ma_keys_dict(PyDictKeysObject *keys,
                   Py_ssize_t dk_size,
                   int elem_size)
{
    PyObject *ma_keys_dict = PyDict_New();
    if (ma_keys_dict == NULL) {
        return NULL;
    }

    SET_FIELD_IN(ma_keys_dict, keys->dk_refcnt, dk_refcnt, PyLong_FromSsize_t);
    SET_FIELD_IN(ma_keys_dict, keys->dk_log2_size, dk_log2_size, PyLong_FromLong);
    SET_FIELD_IN(ma_keys_dict, keys->dk_log2_index_bytes, dk_log2_index_bytes, PyLong_FromLong);
    SET_FIELD_IN(ma_keys_dict, keys->dk_kind, dk_kind, PyLong_FromLong);
    SET_FIELD_IN(ma_keys_dict, keys->dk_version, dk_version, PyLong_FromUnsignedLong);
    SET_FIELD_IN(ma_keys_dict, keys->dk_usable, dk_usable, PyLong_FromSsize_t);
    SET_FIELD_IN(ma_keys_dict, keys->dk_nentries, dk_nentries, PyLong_FromSsize_t);

    /* dk_indices */
    PyObject *dk_indices_list = build_dict_indices_list(
        keys->dk_indices, dk_size, elem_size);
    if (dk_indices_list == NULL) {
        goto error;
    }

    if (PyDict_SetItemString(ma_keys_dict, "dk_indices", dk_indices_list) < 0) {
        Py_DECREF(dk_indices_list);
        goto error;
    }
    Py_DECREF(dk_indices_list);

    /* entries */
    PyObject *keys_entries = build_dict_entries_list(keys);
    if (keys_entries == NULL) {
        goto error;
    }

    if (PyDict_SetItemString(ma_keys_dict, "entries", keys_entries) < 0) {
        Py_DECREF(keys_entries);
        goto error;
    }
    Py_DECREF(keys_entries);

    return ma_keys_dict;

error:
    Py_DECREF(ma_keys_dict);
    return NULL;
}

/* ------------------------------------------------------------------ */
/* Построение ma_values                                                */
/* ------------------------------------------------------------------ */

/* Создаёт список значений из PyDictValues для split-словаря.
 * values_struct — указатель на PyDictValues (может быть NULL)
 * nentries      — количество записей (dk_nentries)
 *
 * Возвращает:
 *   - новый список PyObject* (NULL-значения заменены на None), если values_struct != NULL;
 *   - Py_None с инкрементированной ссылкой, если values_struct == NULL;
 *   - NULL при ошибке.
 */
static PyObject *
build_ma_values_list(PyDictValues *values_struct, Py_ssize_t nentries)
{
    if (values_struct == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    PyObject *values = PyList_New(0);
    if (values == NULL) {
        return NULL;
    }

    for (Py_ssize_t i = 0; i < nentries; i++) {
        PyObject *value = values_struct->values[i];
        if (PyList_Append(values, value != NULL ? value : Py_None) < 0) {
            Py_DECREF(values);
            return NULL;
        }
    }

    return values;
}


/* Создаёт словарь extra со служебной информацией о структуре.
 * keys          — указатель на PyDictKeysObject
 * idx_elem_size — размер элемента dk_indices в байтах
 *
 * Возвращает новый dict или NULL при ошибке.
 */
static PyObject *
build_extra_dict(PyDictKeysObject *keys, Py_ssize_t idx_elem_size)
{
    PyObject *extra = PyDict_New();
    if (extra == NULL) {
        return NULL;
    }

    const char *entry_type = (keys->dk_kind == DICT_KEYS_GENERAL)
        ? "PyDictKeyEntry"
        : "PyDictUnicodeEntry";
    PyObject *py_entry_type = PyUnicode_FromString(entry_type);
    if (py_entry_type == NULL ||
        PyDict_SetItemString(extra, "entry_type", py_entry_type) < 0) {
        Py_XDECREF(py_entry_type);
        goto error;
    }
    Py_DECREF(py_entry_type);

    PyObject *py_idx_elem_size = PyLong_FromSsize_t(idx_elem_size);
    if (py_idx_elem_size == NULL ||
        PyDict_SetItemString(extra, "idx_elem_size", py_idx_elem_size) < 0) {
        Py_XDECREF(py_idx_elem_size);
        goto error;
    }
    Py_DECREF(py_idx_elem_size);

    return extra;

error:
    Py_DECREF(extra);
    return NULL;
}

/* ------------------------------------------------------------------ */
/* Публичный API                                                       */
/* ------------------------------------------------------------------ */

PyObject *
get_dict_structure(PyObject *self, PyObject *obj)
{
    if (!PyDict_Check(obj)) {
        PyErr_SetString(PyExc_TypeError, "expected dict");
        return NULL;
    }

    PyDictObject *mp = (PyDictObject *)obj;
    PyDictKeysObject *keys = mp->ma_keys;
    Py_ssize_t dk_size = (Py_ssize_t)1 << keys->dk_log2_size;
    Py_ssize_t idx_elem_size = (Py_ssize_t)1 << (keys->dk_log2_index_bytes - keys->dk_log2_size);

    PyObject *result = PyDict_New();
    if (result == NULL) {
        return NULL;
    }

    /* Верхний уровень: поля PyDictObject */
    SET_FIELD_IN(result, mp->ma_used, ma_used, PyLong_FromSsize_t);

    /* Добавление extra */
    PyObject *extra = build_extra_dict(keys, idx_elem_size);
    if (extra == NULL) {
        goto error;
    }

    if (PyDict_SetItemString(result, "extra", extra) < 0) {
        Py_DECREF(extra);
        goto error;
    }
    Py_DECREF(extra);


    /* Добавление ma_keys */
    PyObject *ma_keys_dict = build_ma_keys_dict(keys, dk_size, idx_elem_size);
    if (ma_keys_dict == NULL) {
        goto error;
    }

    if (PyDict_SetItemString(result, "ma_keys", ma_keys_dict) < 0) {
        Py_DECREF(ma_keys_dict);
        goto error;
    }
    Py_DECREF(ma_keys_dict);

    /* Добавление ma_values */
    if (keys->dk_kind == DICT_KEYS_SPLIT) {
        PyObject *values = build_ma_values_list(
            mp->ma_values, keys->dk_nentries);
        if (values == NULL) {
            goto error;
        }

        if (PyDict_SetItemString(result, "ma_values", values) < 0) {
            Py_DECREF(values);
            goto error;
        }
        Py_DECREF(values);
    }

    return result;

error:
    Py_DECREF(result);
    return NULL;
}
