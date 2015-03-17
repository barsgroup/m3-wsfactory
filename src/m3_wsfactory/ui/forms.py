# -*- coding: utf-8 -*-

"""
forms.py

:Created: 3/19/14
:Author: timic
"""
from django.utils.translation import ugettext as _
from m3.actions import ActionContext

import objectpack
from m3_ext.ui import all_components as ext
from objectpack.ui import make_combo_box
from m3_wsfactory.ui.helpers import recur_getattr


class EditorFabric(object):

    _types = {
        "string": ext.ExtStringField,
        "text": ext.ExtTextArea,
        "bool": ext.ExtCheckBox,
        "password": ext.ExtStringField,
        "float": ext.ExtNumberField,
        "int": ext.ExtNumberField,
    }

    @classmethod
    def create_editor(cls, editor_type, **kwargs):
        editor_cls = cls._types[editor_type]
        params = cls.get_editor_params(editor_type)
        params.update(kwargs)
        return editor_cls(**params)

    @classmethod
    def get_editor_params(cls, editor_type):
        return {
            "int": {"allow_decimals": False},
            "password": {"input_type": "password"}
        }.get(editor_type, {})


class ServiceEditWindow(objectpack.BaseEditWindow):

    def _init_components(self):
        super(ServiceEditWindow, self)._init_components()
        self.code_field = ext.ExtStringField(
            label=_(u"Код"),
            name="code",
            allow_blank=False,
            anchor="100%")
        self.name_field = ext.ExtStringField(
            label=_(u"Наименование"),
            name="name",
            allow_blank=False,
            anchor="100%")
        self.api_json_field = ext.ExtStringField(
            name="api_flat_json",
            hidden=True)
        self.hash_field = ext.ExtStringField(
            name="hash",
            hidden=True)
        self.api_grid = ext.ExtObjectGrid(
            header=True,
            title=_(u"Сервис-методы"),
            flex=1)

    def _do_layout(self):
        super(ServiceEditWindow, self)._do_layout()
        self.height = 500
        self.width = 600
        self.layout = 'vbox'
        self.layout_config = {'align': 'stretch', 'pack': 'start'}
        self.form.layout_config = {'height': 250}

        self.form.items.extend((
            self.code_field,
            self.name_field,
            self.api_json_field,
        ))

        self.items.append(self.api_grid)

    def set_params(self, params):
        super(ServiceEditWindow, self).set_params(params)
        self.template_globals = "ui-js/service-edit-window.js"
        self.api_grid.allow_paging = False
        self.api_grid.add_column(
            data_index="id",
            header=_(u"Код"))
        self.api_grid.top_bar.items.extend((
            ext.ExtButton(
                text=_(u"Добавить"),
                icon_cls="add_item",
                handler="addApi"),
            ext.ExtButton(
                text=_(u"Удалить"),
                icon_cls="delete_item",
                handler="deleteApi")))
        self.api_grid.store = ext.ExtDataStore()
        obj = params["object"]
        codes = map(lambda a: [a.id], obj.Api or [])

        self.api_grid.store.load_data(codes)
        self.api_grid.store._listeners._data.update({
            "add": "onApiEditing",
            "remove": "onApiEditing"})
        self.select_api_url = params["select_api_url"]


class SecurityEditWindow(objectpack.BaseEditWindow):

    def _init_components(self):
        super(SecurityEditWindow, self)._init_components()
        self.code_field = ext.ExtStringField(
            label=_(u"Код"),
            name="code",
            allow_blank=False,
            anchor="100%")
        self.module_field = make_combo_box(
            label=_(u"Модуль"),
            name="module",
            allow_blank=False,
            anchor="100%")
        self.name_field = ext.ExtStringField(
            label=_(u"Наименование"),
            name="name",
            allow_blank=False,
            anchor="100%")
        self.hash_field = ext.ExtStringField(
            name="hash",
            hidden=True)
        self.param_grid = ext.ExtObjectGrid(
            header=True,
            title=u"Параметры",
            anchor="100%",
            height=150,
        )

    def _do_layout(self):
        super(SecurityEditWindow, self)._do_layout()
        self.form.items.extend((
            self.module_field,
            self.code_field,
            self.name_field,
            self.hash_field,
            self.param_grid
        ))

    def set_params(self, params):
        super(SecurityEditWindow, self).set_params(params)
        self.template_globals = "ui-js/security-edit-window.js"
        self.height = 300
        self.module_field.data = params["security_module_values"]
        params["params_pack"].configure_grid(self.param_grid)
        self.param_grid.action_context = ActionContext(
            module_code=getattr(params["object"], "module", None),
            security_code=getattr(params["object"], "code", None)
        )


class ApplicationMainTab(objectpack.WindowTab):

    title = _(u"Параметры")

    def init_components(self, win):
        super(ApplicationMainTab, self).init_components(win)
        win.service_field = make_combo_box(
            name="service",
            label=_(u"Услуга"),
            allow_blank=False,
            anchor="100%")
        win.name_field = ext.ExtStringField(
            name="name",
            label=_(u"Код"),
            allow_blank=False,
            anchor="100%")

        win.tns_field = ext.ExtStringField(
            name="tns",
            label=_(u"TNS"),
            anchor="100%",
            allow_blank=True)

        win.hash_field = ext.ExtStringField(
            name="hash",
            hidden=True)

    def do_layout(self, win, tab):
        tab.items.extend((
            win.service_field, win.name_field, win.tns_field, win.hash_field))

    def set_params(self, win, params):
        super(ApplicationMainTab, self).set_params(win, params)
        win.service_field.data = params["service_data"]


class BaseProtocolTab(objectpack.WindowTab):

    direction = None
    title = None

    def init_components(self, win):
        super(BaseProtocolTab, self).init_components(win)
        self.proto_field = make_combo_box(
            name="{0}.code".format(self.direction),
            label=_(u"Протокол"),
            allow_blank=False,
            anchor="100%")
        setattr(win, "{0}_field".format(self.direction), self.proto_field)
        self.security_field = make_combo_box(
            name="{0}.security".format(self.direction),
            label=_(u"Профиль безопасности"),
            anchor="100%")
        setattr(
            win, "{0}_sec_field".format(self.direction), self.security_field)
        self.param_grid = ext.ExtObjectGrid(
            header=True,
            title=u"Параметры",
            anchor="100%",
            height=145)
        setattr(win, "{0}_param_grid".format(self.direction), self.param_grid)

    def do_layout(self, win, tab):
        super(BaseProtocolTab, self).do_layout(win, tab)
        tab.items.extend((
            self.proto_field, self.security_field, self.param_grid
        ))

    def set_params(self, win, params):
        super(BaseProtocolTab, self).set_params(win, params)
        self.proto_field.data = params["protocol_data"]
        self.security_field.data = params["security_data"]
        params[
            "{0}_param_pack".format(self.direction)
        ].configure_grid(self.param_grid)
        self.param_grid.action_context = ActionContext(
            app_code=params["object"].id,
            protocol_code=recur_getattr(
                params["object"], "{0}.code".format(self.direction), None))


class InProtocolTab(BaseProtocolTab):

    direction = "InProtocol"
    title = _(u"Входящий протокол")
    template = "ui-js/in-protocol-tab.js"


class OutProtocolTab(BaseProtocolTab):

    direction = "OutProtocol"
    title = _(u"Исходящий протокол")
    template = "ui-js/out-protocol-tab.js"


class ApplicationEditWindow(objectpack.TabbedEditWindow):

    def __init__(self, *args, **kwargs):
        self.tabs = [
            ApplicationMainTab(),
            InProtocolTab(),
            OutProtocolTab()
        ]
        super(ApplicationEditWindow, self).__init__(*args, **kwargs)

    def set_params(self, params):
        super(ApplicationEditWindow, self).set_params(params)
        self.height = 350
        self.width = 400
        self.template_globals = "ui-js/application-edit-window.js"


def container(*items, **params):
    cnt = ext.ExtContainer(**params)
    cnt.items.extend(items)
    return cnt
