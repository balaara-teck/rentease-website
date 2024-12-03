import os
import sys
import django

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engine.settings')
django.setup()

# Print Python path
print("Python Path:")
for p in sys.path:
    print(f"  - {p}")

# Try importing project modules
try:
    from engine import settings
    print("\nSuccessfully imported engine.settings")
except Exception as e:
    print(f"\nError importing engine.settings: {e}")

try:
    from RentEase import views
    print("Successfully imported RentEase.views")
except Exception as e:
    print(f"Error importing RentEase.views: {e}")

# Try importing specific views
try:
    from RentEase.views import property_list, property_detail
    print("Successfully imported specific views")
except Exception as e:
    print(f"Error importing specific views: {e}")
