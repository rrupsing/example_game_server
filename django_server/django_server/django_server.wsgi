import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'django_server.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
path = '/var/www/mobile_server/django_server'
if path not in sys.path:
    sys.path.append(path)
