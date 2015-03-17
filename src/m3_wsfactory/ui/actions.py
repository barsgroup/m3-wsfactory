# -*- coding: utf-8 -*-

"""
actions.py

:Created: 3/12/14
:Author: timic
"""
from django.utils.translation import ugettext as _
from django.core.cache.backends.locmem import LocMemCache

from m3 import ApplicationLogicException
from m3.actions import ControllerCache
from m3_ext.ui.fields import ExtStringField
from m3_ext.ui.misc.store import ExtJsonWriter

import objectpack

from wsfactory import _helpers
from wsfactory.config import Settings

from m3_wsfactory.ui.controller import observer
from m3_wsfactory.models import LogEntry
from m3_wsfactory.ui import models
from m3_wsfactory.ui import forms


class ExtendDesktopMixin(object):

    def extend_menu(self, menu):
        return menu_item(
            _(u"Администрирование"),
            _(u"Реестр веб-сервисов"),
            self.title,
            action=self.list_window_action,
            menu=menu)


class BaseEditablePack(objectpack.ObjectPack):

    need_check_permission = True

    def declare_context(self, action):
        result = super(BaseEditablePack, self).declare_context(action)
        if action in (
                self.save_action,
                self.new_window_action,
                self.edit_window_action):
            result[self.id_param_name] = {
                "type": lambda x: str(x) if (x and x != "0") else 0
            }
        elif action is self.delete_action:
            result[self.id_param_name] = {
                "type": lambda str_list: [
                    x.strip() for x in str_list.split(",")]
            }
        return result

    def extend_menu(self, menu):
        return menu_item(
            _(u"Администрирование"),
            _(u"Реестр веб-сервисов"),
            self.title,
            action=self.list_window_action,
            menu=menu)


class ServicePack(BaseEditablePack):

    model = models.Service

    add_window = edit_window = forms.ServiceEditWindow

    columns = [
        {
            "data_index": "id",
            "header": _(u"Код"),
        },
        {
            "data_index": "name",
            "header": _(u"Наименование"),
        }
    ]

    def __init__(self):
        super(ServicePack, self).__init__()
        self.select_api_action = ApiSelectAction()
        self.actions.append(self.select_api_action)

    def get_edit_window_params(self, params, request, context):
        params = super(ServicePack, self).get_edit_window_params(
            params, request, context)
        params["select_api_url"] = self.select_api_action.get_absolute_url()
        return params


class ApiSelectAction(objectpack.SelectorWindowAction):

    def configure_action(self, request, context):
        self.data_pack = ControllerCache.find_pack(ApiPack)


class ApiPack(objectpack.ObjectPack):

    model = models.Api
    need_check_permission = True
    column_name_on_select = "name"
    columns = [
        {
            "data_index": "code",
            "header": _(u"Код"),
        },
        {
            "data_index": "id",
            "header": _(u"Идентификатор"),
        },
        {
            "data_index": "name",
            "header": _(u"Наименование"),
        }
    ]

    def declare_context(self, action):
        result = super(ApiPack, self).declare_context(action)

        if action in (self.select_window_action, self.rows_action):
            result["exclude"] = {"type": lambda x: x.strip(",")}

        return result

    def get_rows_query(self, request, context):
        return super(ApiPack, self).get_rows_query(request, context).exclude(
            id__in=context.exclude)


class SecurityPack(BaseEditablePack):

    model = models.Security
    add_window = edit_window = forms.SecurityEditWindow
    columns = [
        {
            "data_index": "code",
            "header": _(u"Код"),
            "width": 1,
        },
        {
            "data_index": "name",
            "header": _(u"Наименование"),
            "width": 2,
        },
    ]

    def declare_context(self, action):
        result = super(SecurityPack, self).declare_context(action)
        if action is self.save_action:
            result["module"] = {"type": "unicode"}
            result["paramNames"] = {
                "type": lambda x: unicode(x).split(",") if x else []}
        return result

    def get_edit_window_params(self, params, request, context):
        params = super(SecurityPack, self).get_edit_window_params(
            params, request, context)

        params["security_module_values"] = (
            models.SecurityModule.objects.values_list("id", "name"))
        params["params_pack"] = ControllerCache.find_pack(
            SecurityParamsGridPack)

        return params

    def save_row(self, obj, create_new, request, context):
        param_types = dict(
            (key, (value, value_type))
            for key, value, value_type in
            models.SecurityParamDeclaration.objects.filter(
                module=context.module
            ).values_list("key", "value", "valueType"))
        for param_name in context.paramNames:
            value = request.REQUEST.get(param_name, None)
            default_value, value_type = param_types.get(param_name)
            if value or default_value:
                obj.set_param(param_name, value or None, value_type)
        obj.save()


class BaseParamsGridPack(objectpack.ObjectPack):

    _is_primary_for_model = False
    need_check_permission = True
    allow_paging = False
    columns = [
        {
            "data_index": "key",
            "hidden": True,
        },
        {
            "data_index": "valueType",
            "hidden": True,
        },
        {
            "data_index": "name",
        },
        {
            "data_index": "value",
            "editor": ExtStringField(),
            "column_renderer": "valueRenderer"
        },
        {
            "data_index": "valueEditor",
            "hidden": True
        }
    ]

    def prepare_row(self, obj, request, context):
        obj = super(BaseParamsGridPack, self).prepare_row(
            obj, request, context)

        obj.valueEditor = forms.EditorFabric.create_editor(obj.valueType, **{
            "allow_blank": not getattr(obj, "required", False),
            "value": unicode(obj.value or "")
        }).render()
        obj.name = obj.name or obj.key

        return obj

    def configure_grid(self, grid):
        super(BaseParamsGridPack, self).configure_grid(grid)
        grid.top_bar.items[:] = []
        grid.top_bar.hidden = True
        grid.editor = True
        grid.local_edit = True
        grid.store.writer = ExtJsonWriter(write_all_fields=True)


class SecurityParamsGridPack(BaseParamsGridPack):

    model = models.SecurityParamDeclaration

    def declare_context(self, action):
        result = {}
        if action is self.rows_action:
            result["security_code"] = result["module_code"] = {
                "type": "unicode", "default": None,
            }
        return result

    def prepare_row(self, obj, request, context):
        obj = super(SecurityParamsGridPack, self).prepare_row(
            obj, request, context)

        if context.security_code:
            security = models.Security.objects.get(code=context.security_code)
            obj.value = security.get_param(obj.key) or obj.value

        return obj

    def get_rows_query(self, request, context):
        return self.model.objects.filter(module=context.module_code)


class ApplicationPack(BaseEditablePack):

    model = models.Application
    add_window = edit_window = forms.ApplicationEditWindow

    columns = [
        {
            "data_index": "name",
            "header": _(u"Код"),
            "width": 3,
        },
        {
            "data_index": "service",
            "header": _(u"Услуга"),
            "width": 3,
        },
        {
            "data_index": "InProtocol.code",
            "header": _(u"IN"),
            "width": 2,
        },
        {
            "data_index": "OutProtocol.code",
            "header": _(u"OUT"),
            "width": 2,
        },
    ]

    def get_edit_window_params(self, params, request, context):
        params = super(ApplicationPack, self).get_edit_window_params(
            params, request, context)

        params.update({
            "service_data": list(
                models.Service.objects.values_list("id", "name")),
            "protocol_data": list(
                models.Protocol.objects.values_list("id", "name")),
            "security_data": [(None, '---')] + list(
                models.Security.objects.values_list("id", "name")),
            "InProtocol_param_pack": ControllerCache.find_pack(
                InProtocolParamsGridPack),
            "OutProtocol_param_pack": ControllerCache.find_pack(
                OutProtocolParamsGridPack),
        })
        return params

    def declare_context(self, action):
        result = super(ApplicationPack, self).declare_context(action)

        if action is self.save_action:
            result.update({
                "InProtocol.code": {"type": "unicode"},
                "OutProtocol.code": {"type": "unicode"},
                "paramNames": {
                    "type": lambda x: unicode(x).split(",") if x else []}
            })

        return result

    def save_row(self, obj, create_new, request, context):

        in_proto_param_types = dict(
            ("InProtocol.{0}".format(key), (value, value_type))
            for key, value, value_type in
            models.ProtocolParamDeclaration.objects.filter(
                protocol=getattr(context, "InProtocol.code")
            ).values_list("key", "value", "valueType"))

        out_proto_param_types = dict(
            ("OutProtocol.{0}".format(key), (value, value_type))
            for key, value, value_type in
            models.ProtocolParamDeclaration.objects.filter(
                protocol=getattr(context, "OutProtocol.code")
            ).values_list("key", "value", "valueType"))
        in_proto_param_types.update(out_proto_param_types)

        for param_name in context.paramNames:
            value = request.REQUEST.get(param_name, None)
            default_value, value_type = in_proto_param_types.get(param_name)
            old_value = obj.get_param(param_name)
            if value or default_value:
                obj.set_param(
                    param_name, value or None, value_type)
            elif old_value:
                obj.delete_param(param_name)

        obj.save()


class BaseProtocolParamsGridPack(BaseParamsGridPack):

    model = models.ProtocolParamDeclaration
    param_attr = None

    def declare_context(self, action):
        result = super(BaseProtocolParamsGridPack, self).declare_context(action)
        if action is self.rows_action:
            ControllerCache.find_pack(ApplicationPack)
            result["protocol_code"] = result["app_code"] = {
                "type": "unicode", "default": None}
        return result

    def get_rows_query(self, request, context):
        return self.model.objects.filter(protocol=context.protocol_code)

    def prepare_row(self, obj, request, context):
        obj = super(BaseProtocolParamsGridPack, self).prepare_row(
            obj, request, context)
        if context.app_code:
            app = models.Application.objects.get(id=context.app_code)
            obj.value = app.get_param(
                "{0}.{1}".format(self.param_attr, obj.key)) or obj.value

        return obj


class InProtocolParamsGridPack(BaseProtocolParamsGridPack):

    param_attr = "InProtocol"


class OutProtocolParamsGridPack(BaseProtocolParamsGridPack):

    param_attr = "OutProtocol"


class LogPack(objectpack.ObjectPack):

    model = LogEntry
    need_check_permission = True
    width = 800
    height = 600
    list_sort_order = ("-time",)
    columns = [
        {
            "data_index": "time",
            "header": _(u"Время"),
            "width": 2,
            "sortable": True,
        },
        {
            "data_index": "url",
            "header": _("URL"),
            "width": 2,
        },
        {
            "data_index": "service",
            "header": _(u"Услуга"),
            "width": 2,
            "searchable": True,
            "sortable": True,
        },
        {
            "data_index": "api",
            "header": _(u"Метод"),
            "width": 2,
        },
        {
            "data_index": "in_object",
            "header": _(u"Параметры запроса"),
            "width": 3,
        },
        {
            "data_index": "request",
            "header": _(u"Запрос"),
            "width": 1,
        },
        {
            "data_index": "response",
            "header": _(u"Ответ"),
            "width": 1,
        },
        {
            "data_index": "traceback",
            "header": _(u"Трассировка ошибки"),
            "width": 1,
        }
    ]

    def extend_menu(self, menu):
        return menu_item(
            _(u"Администрирование"),
            _(u"Реестр веб-сервисов"),
            self.title,
            action=self.list_window_action,
            menu=menu)


@observer.subscribe
class CheckCache(object):

    listen = [
        ".*/(Application|Service|Security)Pack/"
        "Object(Save|AddWindow|EditWindow|Delete)Action"
    ]

    def before(self, request, context):
        cache = _helpers.get_cache("wsfactory")
        if isinstance(cache, LocMemCache):
            raise ApplicationLogicException(
                _(u"Данная операция не работает с локальным кэшированием."
                  u" Обратитесь к администратору системы!"))

    def save_object(self, obj):
        if obj.hash != Settings.hash():
            raise ApplicationLogicException(
                _(u"Версия конфигурации устарела!"))
        return obj


def menu_item(*path, **params):
    action = params.get("action")
    menu = params.get("menu")
    path = list(path)
    item = menu.Item(path.pop(), action)
    while path:
        item = menu.SubMenu(path.pop(), item, icon='menu-dicts-16')
    return item