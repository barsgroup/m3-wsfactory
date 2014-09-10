# -*- coding: utf-8 -*-

"""               
spyne_models.py
                  
:Created: 04 Sep 2014  
:Author: tim    
"""
from functools import partial

from lxml import objectify, etree
from spyne import (
    ComplexModelBase, ComplexModelMeta, XmlAttribute, XmlData, Unicode,
    Boolean)

from wsfactory.config import Settings

__all__ = (
    "ApplicationType", "ApiType", "ProtocolType", "ParamType",
    "ProtocolDirectionType", "ServiceType", "ServiceApiType",
    "SecurityModuleType", "SecurityType"
)


class ComplexModel(ComplexModelBase):

    __namespace__ = Settings.NAMESPACE
    __metaclass__ = ComplexModelMeta

    @classmethod
    def get_fields(cls):
        return cls.get_flat_type_info(cls).keys()

    @classmethod
    def init_from(cls, other):
        getter = dict.get if isinstance(other, dict) else getattr
        is_objectified = isinstance(other, objectify.ObjectifiedElement)
        retval = cls()
        flat_type_info = cls.get_flat_type_info(cls)
        for k in flat_type_info:
            type_info = flat_type_info[k]
            v = getter(other, k, None)
            if is_objectified:
                if issubclass(type_info, XmlAttribute):
                    v = other.attrib.get(k, None)
                elif issubclass(type_info, XmlData):
                    _v = getattr(other, "pyval", None)
                    if _v is not None:
                        v = _v
                else:
                    el = getattr(other, k, None)
                    if type_info.Attributes.max_occurs > 1:
                        items = [] if el is None else other.findall(el.tag)
                    else:
                        items = [el]
                    if issubclass(type_info, ComplexModel):
                        items = [type_info.init_from(item) for item in items]
                    if type_info.Attributes.max_occurs > 1:
                        v = items
                    else:
                        v = items[0]
            setattr(retval, k, v)
        return retval

    def objectify(self, tag_name=None, parent=None):
        el = etree.Element(
            tag_name or self.get_type_name(),
            nsmap={None: self.get_namespace()})

        for attr, type_info in self._type_info.iteritems():
            value = getattr(self, attr, None)
            if value is not None:
                if issubclass(type_info, XmlAttribute):
                    el.attrib[attr] = value
                elif issubclass(type_info, XmlData):
                    el.text = value
                else:
                    if type_info.Attributes.max_occurs == 1:
                        items = [value]
                    else:
                        items = value
                    if issubclass(type_info, ComplexModel):
                        objectifier = lambda i: i.objectify(attr, el)
                    else:
                        objectifier = lambda i: self._make_el(attr, i, el)
                    map(objectifier, items)
        el = objectify.fromstring(etree.tostring(el, encoding="utf8"))
        if parent is not None:
            parent.append(el)
        return el

    @staticmethod
    def _make_el(tag_name, text, parent=None):
        if parent:
            objectifier = partial(etree.SubElement, parent)
        else:
            objectifier = etree.Element
        el = objectifier(tag_name)
        el.text = text
        return el


class Param(ComplexModel):

    value = XmlData(Unicode)
    key = XmlAttribute(Unicode, use="required")
    valueType = XmlAttribute(Unicode, use="required")


class ParamDeclaration(Param):

    name = XmlAttribute(Unicode)
    required = XmlAttribute(Boolean)


class ProtocolDirection(ComplexModel):

    code = XmlAttribute(Unicode, use="required")
    security = XmlAttribute(Unicode)

    Param = Param.customize(min_occurs=0, max_occurs="unbounded")


class Application(ComplexModel):

    name = XmlAttribute(Unicode, use="required")
    service = XmlAttribute(Unicode, use="required")
    tns = XmlAttribute(Unicode)

    InProtocol = ProtocolDirection.customize(min_occurs=1, max_occurs=1)
    OutProtocol = ProtocolDirection.customize(min_occurs=1, max_occurs=1)


class Protocol(ComplexModel):

    code = XmlAttribute(Unicode, use="required")
    name = XmlAttribute(Unicode, use="required")
    module = XmlAttribute(Unicode, use="required")
    direction = XmlAttribute(
        Unicode(values=["IN", "OUT", "BOTH"]), use="required", )

    Param = ParamDeclaration.customize(min_occurs=0, max_occurs="unbounded")


class Api(ComplexModel):

    code = XmlAttribute(Unicode, use="required")
    name = XmlAttribute(Unicode, use="required")
    module = XmlAttribute(Unicode, use="required")


class ServiceApi(ComplexModel):

    code = XmlAttribute(Unicode, use="required")


class Service(ComplexModel):

    code = XmlAttribute(Unicode, use="required")
    name = XmlAttribute(Unicode, use="required")

    Api = ServiceApi.customize(min_occurs=1, max_occurs="unbounded")


class Module(ComplexModel):
    """
    Security module
    """

    path = XmlAttribute(Unicode, use="required")
    code = XmlAttribute(Unicode, use="required")
    name = XmlAttribute(Unicode, use="required")

    Param = ParamDeclaration.customize(min_occurs=0, max_occurs="unbounded")


class Security(ComplexModel):

    code = XmlAttribute(Unicode, use="required")
    name = XmlAttribute(Unicode, use="required")
    module = XmlAttribute(Unicode, use="required")

    Param = Param.customize(min_occurs=0, max_occurs="unbounded")
