import os
import sys
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent

# Add the project directory to the Python path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engine.settings')

print("Current working directory:", os.getcwd())
print("\nPython path:")
for path in sys.path:
    print(f"  - {path}")

print("\nTrying to import WSGI application...")
try:
    from engine.wsgi import application
    print("Successfully imported WSGI application")
except Exception as e:
    import traceback
    print(f"\nError importing WSGI application: {e}")
    print("\nTraceback:")
    print(traceback.format_exc())
