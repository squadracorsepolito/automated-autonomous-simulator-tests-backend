# automated-tests-backend

# Automated Race Result Backend

This project is a Django-based backend for securely uploading and retrieving autonomous driving race results. It includes token-based authentication, file upload handling, and protected API endpoints.

## Features

- **Token Authentication** with Django REST Framework
- **Protected API endpoints** requiring authentication
- **Upload API** for sending race results and `.zip` or `.bag` files
- **List API** to fetch sorted race results
- **HTML test client** for login and upload
- File uploads saved in `media/rosbags/`
- Structured model to store race data

## Model Fields (`Rosbags`)

- `track_name` – `CharField`
- `mission_name` – `CharField`
- `number_of_laps_completed` – `IntegerField`
- `number_of_evaluated_cones_yellow` – `IntegerField`
- `number_of_evaluated_cones_blue` – `IntegerField`
- `is_successful` – `BooleanField`
- `rosbag_file` – `FileField` (`.zip`/`.bag` file)
- `avg_lap_time` – `FloatField`
- `timestamp` – `DateTimeField`

## Authentication

1. Use the `/api-token-auth/` endpoint (POST) with `username` and `password` to get a token.
2. Send the token in `Authorization: Token <token>` header for all protected endpoints.

## API Endpoints

The API exposes the following endpoints for managing `Rosbag` instances:

| Method | Endpoint                     | Description                                                                 |
|--------|------------------------------|-----------------------------------------------------------------------------|
| `GET`  | `/api/rosbags/`              | Returns a list of all rosbags. Automatically cleans up missing file entries. |
| `POST` | `/api/rosbags/`              | Uploads a new rosbag (expects YAML and DB3 files). Triggers parsing + JSON creation. |
| `PUT`  | `/api/rosbags/{pk}/`         | Fully updates an existing rosbag (requires all fields).                    |
| `PATCH`| `/api/rosbags/{pk}/`         | Partially updates a rosbag (only specified fields are changed).            |
| `DELETE`| `/api/rosbags/{pk}/`        | Deletes a rosbag and its associated files from the filesystem.             |
| `GET`  | `/api/rosbags/{pk}/json/`    | Return the rosbag's JSON representation.                                   |
| `GET`  | `/api/rosbags/{pk}/ros/`    | Return the rosbag's ROS1 representation.                                    |

---

These endpoints are automatically generated using **Django REST Framework’s** `DefaultRouter` in combination with a `ModelViewSet`. Here's how:

- The backend defines a `RosbagViewSet` class that inherits from `ModelViewSet`, providing all standard CRUD operations:
  - `list`, `create`, `retrieve`, `update`, `partial_update`, `destroy`

- The router registration looks like this:

  ```python
  from rest_framework.routers import DefaultRouter
  from .views import RosbagViewSet

  router = DefaultRouter()
  router.register(r'rosbags', RosbagViewSet, basename='rosbags')
    ```

## Pagination

The `GET /api/rosbags/` endpoint uses **pagination by default**, as configured in the Django REST Framework settings.

### - Page size is customizable

You can control how many items are returned per page by passing the optional `page_size` query parameter:

- `GET /api/rosbags/` – returns the **first page** with the **default page size** (e.g., 10 items)
- `GET /api/rosbags/?page=2` – returns the **second page**
- `GET /api/rosbags/?page_size=20` – returns the **first page with 20 items**
- `GET /api/rosbags/?page=3&page_size=15` – returns **page 3**, **15 items per page**

> A maximum limit (`max_page_size`) may apply to prevent performance issues.

---

The response format includes metadata about the pagination:

```json
{
  "count": 120,
  "next": "http://localhost:8000/api/rosbags/?page=2&page_size=10",
  "previous": null,
  "results": [
    {
      "id": 1,
      "track_name": "Test Track",
      ...
    },
    ...
  ]
}
```

## Test Page

Open `test.html` in your browser:
- Login with username & password
- Submit race data and optional file
- View updated result list in real time

## File Upload Notes

- Uploaded files are stored under `media/rosbags/`
- Make sure to configure `MEDIA_ROOT` and `MEDIA_URL` in `settings.py`
- Use `FormData` on the frontend for file upload support

## Setup

```bash
git clone <this_repo>
cd automated-tests-backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python create_admin.py  # Creates admin user from .env
python manage.py runserver
```

### Environment Variables

Before running the project, create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Then edit `.env` with your local configuration:

```env
# Django Settings
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-secret-key-here-change-in-production
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (optional - if using local database)
DATABASE_URL=sqlite:///db.sqlite3

# Admin User Credentials
DJANGO_ADMIN_USERNAME=admin
DJANGO_ADMIN_EMAIL=admin@example.com
DJANGO_ADMIN_PASSWORD=your_secure_password

# CORS Settings - Comma-separated list of allowed origins
# Example: http://localhost:3000,http://localhost:8000,https://yourdomain.com
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_DEBUG` | Enable debug mode (set to `False` in production) | `False` |
| `DJANGO_SECRET_KEY` | Secret key for Django (change for each environment) | `your-secret-key-here` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection URL | `sqlite:///db.sqlite3` |
| `DJANGO_ADMIN_USERNAME` | Admin user username | `admin` |
| `DJANGO_ADMIN_EMAIL` | Admin user email | `admin@example.com` |
| `DJANGO_ADMIN_PASSWORD` | Admin user password | `your_secure_password` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | `http://localhost:3000` |

**Note:** The `.env` file is excluded from version control (see `.gitignore`). Each environment (development, staging, production) should have its own `.env` configuration.