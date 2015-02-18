# -*- coding: utf-8 -*-
"""
models.py

:Created: 5/23/14
:Author: timic
"""
import json
import logging
from wsfactory import _helpers
from wsfactory.config import Settings, ImproperlyConfigured

logger = logging.getLogger(__name__)

from itertools import imap

from objectpack import VirtualModel

import spyne_models
from helpers import (
    ElementRootAccessor, InstanceDescriptorMixin,
    recur_getattr, field_property)


class SettingsProxy(object):

    Protocols = ElementRootAccessor("Protocols", "Protocol")
    ApiRegistry = ElementRootAccessor("ApiRegistry", "Api")
    Services = ElementRootAccessor("Services", "Service")
    SecurityModules = ElementRootAccessor("SecurityProfile/Modules", "Module")
    SecurityProfiles = ElementRootAccessor("SecurityProfile", "Security")
    Applications = ElementRootAccessor(
        "Applications", "Application", "name")

proxy = SettingsProxy()


class BaseModel(VirtualModel, InstanceDescriptorMixin):

    _proxy = proxy
    _type_info = None
    _root = None
    _doc_root = None

    @classmethod
    def _get_ids(cls):
        doc, items, _hash = getattr(cls._proxy, cls._root)
        return imap(lambda item: (doc, item, _hash), items)

    def __init__(self, config=None):
        if config is None:
            self.id = None
            self._obj = self._type_info.init_from({})
            self._el = None
            self._el_orig = None
            self._doc_root, _, self.hash = getattr(self._proxy, self._root)
        else:
            self._doc_root, (
                self.id, self._el), self.hash = config
            self._obj = self._type_info.init_from(self._el)
        for k in self._obj.get_fields():
            setattr(self, k, field_property(self._obj, k))

    def __repr__(self):
        if self._obj is None:
            return super(BaseModel, self).__repr__()
        else:
            return self._type_info.to_string(self._obj)


class BaseParametrisedModel(BaseModel):

    def _get_params_root(self, name):
        parts = name.rsplit(".", 1)
        base = parts.pop(0)
        if parts:
            param_name = parts[0]
            obj = recur_getattr(self, base)
        else:
            param_name = name
            obj = self
        return obj, param_name

    def get_param(self, name):
        """
        :param name: Имя параметра ("name" или "InProtocol.validation")
        :type name: str
        """
        obj, param_name = self._get_params_root(name)
        for param in obj.Param or []:
            if param.key == param_name:
                return param.value

    def set_param(self, name, value, value_type):
        obj, param_name = self._get_params_root(name)
        obj.Param = obj.Param or []
        for param in obj.Param:
            if param.key == param_name:
                param.value = value
                break
        else:
            param = spyne_models.Param(
                key=param_name, value=value, valueType=value_type)
            obj.Param.append(param)

    def delete_param(self, name):
        obj, param_name = self._get_params_root(name)
        to_remove = None
        for param in obj.Param or []:
            if param.key == param_name:
                to_remove = param
        if to_remove:
            obj.Param.remove(to_remove)


class EditableMixin(object):

    @_helpers.lock
    def save(self):
        el = self._obj.objectify()
        if self._el is not None:
            self._doc_root.replace(self._el, el)
        else:
            self._doc_root.append(el)
        try:
            Settings.dump(Settings.config_path())
        finally:
            self._proxy._force_load = True
            Settings.reload()

    @_helpers.lock
    def safe_delete(self):
        self._el.getparent().remove(self._el)
        try:
            Settings.dump(Settings.config_path())
            result = True
        except ImproperlyConfigured:
            result = False
        finally:
            self._proxy._force_load = True
            Settings.reload()
        return result


class Protocol(BaseModel):

    _type_info = spyne_models.Protocol
    _root = "Protocols"


class Api(BaseModel):

    _type_info = spyne_models.Api
    _root = "ApiRegistry"

    class _meta:
        verbose_name = u"Метод"
        verbose_name_plural = u"Методы"


class SecurityModule(BaseModel):

    _root = "SecurityModules"
    _type_info = spyne_models.Module


class SecurityParamDeclaration(VirtualModel):

    @classmethod
    def _get_ids(cls):
        return (
            (param, module)
            for module in SecurityModule.objects.all()
            for param in module.Param
        )

    def __init__(self, params=None):
        param, module = params
        self.name = param.name
        self.key = param.key
        self.valueType = param.valueType
        self.value = param.value
        self.module = module.code


class Security(BaseParametrisedModel, EditableMixin):

    _root = "SecurityProfiles"
    _type_info = spyne_models.Security
    _param_attrs = ("Param",)

    class _meta:
        verbose_name = u"Профиль безопасности"
        verbose_name_plural = u"Профили безопасности"


class Service(BaseModel, EditableMixin):

    _root = "Services"
    _type_info = spyne_models.Service

    class _meta:
        verbose_name = u"Услуга"
        verbose_name_plural = u"Реестр услуг"

    @property
    def api_flat(self):
        return map(lambda a: a.id, self.Api or [])

    @api_flat.setter
    def api_flat(self, values):
        if values:
            self.Api = map(
                lambda value: spyne_models.ServiceApi(id=value), values)
        else:
            raise ValueError("Service api list cannot be empty!")

    @property
    def api_flat_json(self):
        return json.dumps(self.api_flat)

    @api_flat_json.setter
    def api_flat_json(self, json_values):
        self.api_flat = json.loads(json_values)


class Application(BaseParametrisedModel, EditableMixin):

    _type_info = spyne_models.Application
    _root = "Applications"

    def __init__(self, config=None):
        super(Application, self).__init__(config)
        if not self.id:
            self.InProtocol = self._type_info.InProtocol()
            self.OutProtocol = self._type_info.OutProtocol()

    class _meta:
        verbose_name = u"Веб-сервис"
        verbose_name_plural = u"Реестр веб-сервисов"


class ProtocolParamDeclaration(VirtualModel):

    @classmethod
    def _get_ids(cls):
        return (
            (param, protocol)
            for protocol in Protocol.objects.all()
            for param in protocol.Param or []
        )

    def __init__(self, params=None):
        param, protocol = params
        self.name = param.name
        self.key = param.key
        self.valueType = param.valueType
        self.value = param.value
        self.required = param.required
        self.protocol = protocol.code
