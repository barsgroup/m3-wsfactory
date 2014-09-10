// основной блок для потомков
var win = Ext.getCmp('{{ component.client_id }}');

{% block content %}{% endblock %}

{% include "ui-js/column-editor.js" %}

// подключение шаблонов вкладок
{% for t in component.tabs_templates %}
    {% include t %}
{% endfor %}
