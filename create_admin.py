import os
from dotenv import load_dotenv
import django

# Load environment variables from .env file
load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "automated_tests_backend.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get("DJANGO_ADMIN_USERNAME", "admin")
email = os.environ.get("DJANGO_ADMIN_EMAIL", "admin@example.com")
password = os.environ.get("DJANGO_ADMIN_PASSWORD", "admin123")

if not User.objects.filter(username=username).exists():
    print("Creating admin user...")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print("Admin user already exists.")