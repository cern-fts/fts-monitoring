#!/usr/bin/env python3
import os
import sys

path = os.path.dirname(__file__)
if path not in sys.path:
  sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.core.wsgi import get_wsgi_application

_application = get_wsgi_application()

def application(environ, start_response):
    os.environ['BASE_URL'] = environ['SCRIPT_NAME']
    if 'SSL_CLIENT_S_DN' in environ:
        os.environ['SSL_CLIENT_S_DN'] = environ['SSL_CLIENT_S_DN']
    return _application(environ, start_response)
