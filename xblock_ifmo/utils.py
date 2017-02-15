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

    :param cls: Class, which name to convert of
    :param capitalize: List of names, that should be left as single word
    :return:
    """
    capitalize = ["XBlock"] + (capitalize or [])
    name = cls.__name__

    for x in capitalize:
        name = name.replace(x, x.capitalize())
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def DefaultedDescriptor(base_class, default_condition=lambda x: x is None, **args):  # pylint: disable=invalid-name
    """
    Создаёт потомок класса, у которого переопределен __get__.

    Вызывает __get__ у родителя. Если он удовлетворяет условию default_condition, возвращает default.

    Используется для изменения поведения дескриптора (поля у XBlock'а). Значение по-умолчанию у него возвращается в том
    случае, если закого поля в принципе не существует в его сериализованной версии (например, прочитанной из БД). При
    этом, у поля может быть ранее задано значение, которое не может корректно использовано, например None или пустая
    строка. В таком случае иногда может потребоваться вернуть в качестве ответа неоторое непустное значение
    по-умолчанию.

    Пример: в настройках XBlock'а инструктор задал пустое значение для ссылки на сервис отображающий отчёты. Подсистема
    платформы не считает его пустым, а ассоциирует его с пустой строкой, но это не имеет смысла, и требуется в этом
    случае использовать некоторое значение по-умолчанию.

    :param base_class: Базовый класс дескриптора
    :param default_condition: Условие, при котором требуется вернуть значение по-умолчанию.
    :param args: Остальные параметры дескриптора
    :return:
    """
    def __get__(self, xblock, xblock_class):
        value = super(self.__class__, self).__get__(xblock, xblock_class)
        return self._default if default_condition(value) else value
    derived_dict = {
        "__get__": __get__,
    }
    derived = type("%sNoneDefaulted" % base_class.__name__, (base_class,), derived_dict)
    return derived(**args)
