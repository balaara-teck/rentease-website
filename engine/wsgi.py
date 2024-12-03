"""
WSGI config for engine project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Add the project root directory to the Python path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engine.settings')

try:
    application = get_wsgi_application()
except Exception as e:
    import traceback
    print(f"Error loading WSGI application: {e}")
    print("Traceback:")
    print(traceback.format_exc())
    print("\nPython path:")
    for path in sys.path:
        print(f"  - {path}")
    raise
