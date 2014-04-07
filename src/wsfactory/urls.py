# -*- coding: utf-8 -*-

"""
urls.py

:Created: 3/19/14
:Author: timic
"""
from django.conf.urls import patterns, url

urlpatterns = patterns(
    'wsfactory.views',
    url(r'^wsfactory/api$', 'api_list'),
    url(r'^wsfactory/api/(?P<Service>.*)/(?P<InProto>.*)/(?P<OutProto>.*)$',
        'handle_api_call'),
    url(r'^wsfactory/api/(?P<Service>.*)/(?P<InProto>.*)$',
        'handle_api_call'),
)