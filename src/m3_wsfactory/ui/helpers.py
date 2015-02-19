# -*- coding: utf-8 -*-

"""               
helpers.py
                  
:Created: 08 Sep 2014  
:Author: tim    
"""

import logging
logger = logging.getLogger(__name__)

from functools import partial
from threading import RLock

from wsfactory.config import Settings, ImproperlyConfigured, track_config


class ElementRootAccessor(object):

    def __init__(self, root, name, key="code"):
        self.root = root
        self.name = name
        self.key = key
        self._doc = None
        self._items = None
        self._hash = None
        self._lock = RLock()

    @track_config
    def __get__(self, instance, owner):
        _hash = Settings.hash()

        if self._doc is not None:
            force_load = getattr(instance, "_force_load", False)
            if self._hash == _hash and not force_load:
                return self._doc, self._items, self._hash

        self._hash = _hash

        settings = Settings()
        path = "/".join(map(lambda p: "{{{0}}}{1}".format(
            Settings.NAMESPACE, p), self.root.split("/")))
        root = settings._document.find(path)

        if root is None:
            raise ValueError("{0} element not found".format(self.root))
        self._doc = root
        tag_name = "{{{0}}}{1}".format(Settings.NAMESPACE, self.name)
        self._items = [
            (item.attrib.get(self.key), item)
            for item in self._doc.getchildren()
            if item.tag == tag_name
        ]
        setattr(instance, "_force_load", False)
        return self._doc, self._items, self._hash

    def __set__(self, instance, value):
        pass

    def __delete__(self, instance):
        pass


class InstanceDescriptorMixin(object):
    """Magic with instance descriptors"""

    def __getattribute__(self, name):
        value = object.__getattribute__(self, name)
        if hasattr(value, '__get__'):
            value = value.__get__(self, self.__class__)
        return value

    def __setattr__(self, name, value):
        try:
            obj = object.__getattribute__(self, name)
        except AttributeError:
            pass
        else:
            if hasattr(obj, '__set__'):
                return obj.__set__(self, value)
        return object.__setattr__(self, name, value)


def _get_field(self, obj, field):
    return getattr(obj, field, None)


def _set_field(self, value, obj, field):
    setattr(obj, field, value)


def field_property(obj, field):
    getter = partial(_get_field, obj=obj, field=field)
    setter = partial(_set_field, obj=obj, field=field)
    return property(getter, setter)


def recur_getattr(obj, attr, default=None):
    try:
        return reduce(lambda o, part: getattr(o, part), attr.split("."), obj)
    except AttributeError:
        return default


def recur_setattr(obj, attr, value):
    parts = attr.rsplit(".", 1)
    head = parts.pop(0)
    if parts:
        tail = parts[0]
        obj_attr = recur_getattr(obj, head)
        setattr(obj_attr, tail, value)
    else:
        setattr(obj, attr, value)