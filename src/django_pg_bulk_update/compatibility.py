"""
This file contains number of functions to handle different software versions compatibility
"""
import json

import django
from django.db import connection, connections, models, DefaultConnectionProxy
from typing import Dict, Any, Optional, Union, Tuple


def zip_longest(*args, **kwargs):
    """
    https://docs.python.org/3.5/library/itertools.html#itertools.zip_longest
    """
    try:
        # python 3
        from itertools import zip_longest
        return zip_longest(*args, **kwargs)
    except ImportError:
        # python 2.7
        from itertools import izip_longest
        return izip_longest(*args, **kwargs)


def jsonb_available():  # type: () -> bool
    """
    Checks if we can use JSONField.
    It is available since django 1.9 and doesn't support Postgres < 9.4
    :return: Bool
    """
    return get_postgres_version(as_tuple=False) >= 90400 and (django.VERSION[0] > 1 or django.VERSION[1] > 8)


def hstore_available():  # type: () -> bool
    """
    Checks if we can use HStoreField.
    It is available since django 1.9 and doesn't support Postgres < 9.4
    :return: Bool
    """
    return django.VERSION[0] > 1 or django.VERSION[1] >= 8


def array_available():  # type: () -> bool
    """
    Checks if we can use ArrayField.
    It is available since django 1.9 and doesn't support Postgres < 9.4
    :return: Bool
    """
    return django.VERSION[0] > 1 or django.VERSION[1] >= 8


def hstore_serialize(value):  # type: (Dict[Any, Any]) -> Dict[str, str]
    """
    Django before 1.10 doesn't convert HStoreField values to string automatically
    Which causes a bug in cursor.execute(). This function converts all key/values to string
    :param value: A dict
    :return:
    """
    val = {
        str(k): json.dumps(v) if isinstance(v, (dict, list)) else str(v)
        for k, v in value.items()
    }
    return val


def get_postgres_version(using=None, as_tuple=True):  # type: (Optional[str], bool) -> Union(Tuple[int], int)
    """
    Returns Postgres server verion used
    :param using: Connection alias to use
    :param as_tuple: If true, returns result as tuple, otherwize as concatenated integer
    :return: Database version as tuple (major, minor, revision) if as_tuple is true.
        A single number major*10000 + minor*100 + revision if false.
    """
    conn = connection if using is None else connections[using]
    num = conn.cursor().connection.server_version
    return (num / 10000, num % 10000 / 100, num % 100) if as_tuple else num


def get_field_db_type(field, connection):  # type: (models.Field, DefaultConnectionProxy) -> str
    """
    Get database field type used for this field.
    :param field: django.db.models.Field instance
    :param connection: Datbase connection used
    :return: Database type name (str)
    """
    # We should resolve value as array for IN operator.
    # db_type() as id field returned 'serial' instead of 'integer' here
    # reL_db_type() return integer, but it is not available before django 1.10
    db_type = field.db_type(connection)
    if db_type == 'serial':
        db_type = 'integer'
    elif db_type == 'bigserial':
        db_type = 'biginteger'

    return db_type
