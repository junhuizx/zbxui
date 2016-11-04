"""
WSGI config for zbxui project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import sys

path = '/var/www/html/zbxui'

if path not in sys.path:
    sys.path.append(path)

from django.core.wsgi import get_wsgi_application

#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zbxui.settings")
os.environ["DJANGO_SETTINGS_MODULE"]="zbxui.settings"
application = get_wsgi_application()
