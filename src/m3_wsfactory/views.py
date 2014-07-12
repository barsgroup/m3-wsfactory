# -*- coding: utf-8 -*-

"""
views.py

:Created: 3/19/14
:Author: timic
"""

import logging
logger = logging.getLogger(__name__)

from functools import partial
import traceback
from cStringIO import StringIO

from django.core.handlers.wsgi import LimitedStream
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt

from spyne import EventManager

from wsfactory.config import Settings

from models import LogEntry


def handle_wsgi_close(ctx, log=None):
    log.api = ctx.method_name or "unknown"
    log.in_object = unicode(ctx.in_object or "") or None


def handle_exception(e, log=None):
    log.traceback = e


def api_handler(request, service):
    service_handler = Settings.get_service_handler(service)
    if service_handler:
        logger.debug("Hitting service %s." % service)
        log = LogEntry(
            url="%s %s" % (request.method, request.get_full_path()),
            application=service)
        request_body = request.META["wsgi.input"].read(
            request._stream.remaining)
        request.META["wsgi.input"] = StringIO(request_body)
        request._stream = LimitedStream(
            request.META["wsgi.input"], request._stream.remaining)
        service_handler.event_manager.add_listener(
            "wsgi_close", partial(handle_wsgi_close, log=log))
        service_handler.app.event_manager.add_listener(
            "method_call_exception", partial(handle_exception, log=log))

        try:
            response = csrf_exempt(service_handler)(request)
        except Exception:
            log.traceback = unicode(traceback.format_exc(), errors="ignore")
            raise
        else:
            if response.content:
                log.response = response.content
        finally:
            if request_body:
                log.request = request_body
            log.save()
            service_handler.event_manager = EventManager(service_handler)
            service_handler.app.event_manager = EventManager(
                service_handler.app)

        return response
    else:
        msg = "Service %s not found" % service
        logger.info(msg)
        raise Http404(msg)

