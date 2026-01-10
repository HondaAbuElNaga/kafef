
TestApp
=======

Overview
--------

`testapp` is a small Django project that contains an `exams` app for creating and taking audio-enabled exams. The repo includes a virtual environment layout under `kafef/` and an example SQLite database in `testapp/db.sqlite3` for development.

Project structure (relevant)
- `testapp/` — Django project root (settings, urls, wsgi/asgi, manage.py)
- `testapp/exams/` — Django app containing models, views, templates, and migrations
- `media/` — Uploaded/generated audio and answer files
	- `media/exams_audio/` — exam-level audio (short/other)
	- `media/questions_audio/` — per-question audio files
	- `media/temp_audio/` — temporary audio files
- `static/` — project static assets
- `templates/` — HTML templates (includes `templates/exams/take_exam.html` and `exam_list.html`)

Requirements
------------

- Python 3.10+ recommended
- Django 4+ (project contains `django` in the included venv packages)

If you want to produce an explicit requirements file for this environment run:

```bash
kafef\Scripts\python -m pip freeze > requirements.txt
```

Setup (development)
-------------------

1. Activate the provided virtual environment (on Windows):

```powershell
.\kafef\Scripts\Activate.ps1
```

Or with cmd:

```cmd
kafef\Scripts\activate.bat
```

2. (Optional) Install dependencies if you created `requirements.txt`:

```bash
pip install -r requirements.txt
```

3. Apply migrations and prepare the database:

```bash
python manage.py migrate
```

4. Create a superuser (optional):

```bash
python manage.py createsuperuser
```

Run the development server
--------------------------

Start Django's development server:

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser. The project routes are defined in `testapp/urls.py` and the `exams` app includes pages to list and take exams (`templates/exams/`).

Media & Static files
--------------------

- Uploaded audio and generated files live under `media/` in these subfolders: `exams_audio`, `questions_audio`, `temp_audio`.
- During development Django serves media when `DEBUG = True` and `MEDIA_URL`/`MEDIA_ROOT` are configured in `testapp/settings.py`.
- Collect static files for production:

```bash
python manage.py collectstatic
```

Tests
-----

Run the project's tests with:

```bash
python manage.py test
```

Notes about the `exams` app
---------------------------

- The `exams` app contains models and migrations in `testapp/exams/migrations/`.
- It includes functionality for associating audio files with exams/questions and serving them to users while taking exams. See `testapp/exams/views.py` and `testapp/exams/templates/exams/` for behavior and UI.

Development tips
----------------

- If you need to recreate the DB while preserving migrations:

```bash
del testapp\db.sqlite3
python manage.py migrate
```

- To inspect installed packages inside the bundled venv:

```bash
kafef\Scripts\python -m pip list
```

Deployment
----------

For production, use a proper WSGI/ASGI server (Gunicorn/Uvicorn + a reverse proxy). Ensure:

- `DEBUG = False` in `testapp/settings.py`
- `ALLOWED_HOSTS` is set
- Media files are served by your web server (NGINX/Apache) or cloud storage

Contributing
------------

1. Create an issue describing the change
2. Open a PR with tests for new features/bug fixes

License & Contact
-----------------

This repository does not include an explicit license file. Contact the project owner for licensing and contribution details.

If you'd like, I can also:
- generate a `requirements.txt` from the existing venv,
- add a small `README` section describing the main models and views in `testapp/exams`, or
- wire up a simple management command to clean `media/temp_audio/`.

