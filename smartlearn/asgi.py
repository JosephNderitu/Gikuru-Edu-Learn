"""
ASGI config for smartlearn project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from whitenoise import WhiteNoise

from .settings import BASE_DIR

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartlearn.settings')

application = get_asgi_application()
application = WhiteNoise(application, root=os.path.join(BASE_DIR, 'staticfiles'))
