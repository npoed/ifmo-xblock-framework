# -*- coding=utf-8 -*-

import collections
import datetime
import hashlib
import pytz
import re

from django.core.exceptions import PermissionDenied
from functools import partial, wraps


def require(condition):
    if not condition:
        raise PermissionDenied


def now():
    """
    Текущее время в UTC, tz-aware.

    :return: Время в UTC
    """
    return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


def default_time(fn):
    # TODO: This decorator cannot be loaded form ifmo_xblock.utils. WHY?!
    def default_timed(**kwargs):
        qtime = kwargs.get('qtime')
        if qtime is None:
            qtime = now()
        kwargs['qtime'] = qtime
        return fn(**kwargs)
    return default_timed


def reify(meth):
    """
    Decorator which caches value so it is only computed once.
    Keyword arguments:
    inst
    """
    def getter(inst):
        """
        Set value to meth name in dict and returns value.
        """
        value = meth(inst)
        inst.__dict__[meth.__name__] = value
        return value
    return property(getter)


def reify_f(function):
    memo = {}

    @wraps(function)
    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            memo[args] = rv
            return rv
    return wrapper


def datetime_mapper(x, date_format):
    """

    :param x:
    :return:
    """

    def transform_value(value):
        if isinstance(value, dict):
            return datetime_mapper(value, date_format)
        elif isinstance(value, datetime.datetime):
            return value.strftime(date_format)
        else:
            return value

    return dict(map(lambda (key, val): (key, transform_value(val)), x.items()))


def deep_update(d, u):
    for k, v in u.iteritems():
        if isinstance(d, collections.MutableMapping):
            if isinstance(v, collections.Mapping):
                r = deep_update(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        else:
            d = {k: u[k]}
    return d


def get_sha1(file_handler):
    BLOCK_SIZE = 2**10 * 8  # 8kb
    sha1 = hashlib.sha1()
    for block in iter(partial(file_handler.read, BLOCK_SIZE), ''):
        sha1.update(block)
    file_handler.seek(0)
    return sha1.hexdigest()


def file_storage_path(location, filename):
    # pylint: disable=no-member
    """
    Get file path of storage.
    """
    path = (
        '{loc.org}/{loc.course}/{loc.block_type}/{loc.block_id}'
        '/{filename}'.format(
            loc=location,
            filename=filename
        )
    )
    return path


def convert_xblock_name(cls, capitalize=None):
    """
    Converts XBlock class name from CamelCase to underscore_style.

    Capitalize is optional param containing list of names that should be left as single word.
    I.e. XBlock should be left as xblock, so default value is ['XBlock']. Any additional values
    are expected.

    :param name: Class name to convert
    :param capitalize: List of names, that should be left as single word
    :return:
    """
    capitalize = ["XBlock"] + (capitalize or [])
    name = cls.__name__

    for x in capitalize:
        name = name.replace(x, x.capitalize())
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
