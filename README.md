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

- `POST /api/upload/` – Upload race data and file (requires token)
- `GET /api/list/` – Retrieve list of race results (requires token)
- `POST /api-token-auth/` – Get token by passing credentials

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
python manage.py createsuperuser  # Optional
python manage.py runserver
