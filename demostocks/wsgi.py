"""
WSGI config for demostocks project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demostocks.settings')

application = get_wsgi_application()

# Automatically run database migrations and seed default superuser on WSGI startup
try:
    from django.core.management import call_command
    from django.contrib.auth import get_user_model
    call_command('migrate', interactive=False)
    User = get_user_model()
    u = User.objects.filter(username='admin').first()
    if not u:
        u = User(
            username='admin',
            email='admin@example.com',
            firstname='Admin',
            lastname='User',
            is_superuser=True,
            is_staff=True,
            is_active=True
        )
    u.set_password('Admin@12345')
    u.save()
except Exception as e:
    print(f"Auto-migration error on startup: {e}")
