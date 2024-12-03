#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    # Build paths inside the project
    BASE_DIR = Path(__file__).resolve().parent

    # Add the project root directory to the Python path
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engine.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    try:
        execute_from_command_line(sys.argv)
    except Exception as e:
        print(f"\nError: {e}")
        print("\nPython path:")
        for path in sys.path:
            print(f"  - {path}")
        raise


if __name__ == '__main__':
    main()
