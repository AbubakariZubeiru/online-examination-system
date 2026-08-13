# Online Examination System

A functional Flask web app for creating, taking, and grading multiple-choice exams,
with three roles: **Admin**, **Teacher**, and **Student**.

## Features

- **Auth**: Register (as teacher or student) and log in, with hashed passwords.
- **Admin**: Dashboard with platform stats, user management (enable/disable/delete),
  and oversight of all exams (delete).
- **Teacher**: Create exams, add multiple-choice questions (with per-question marks),
  publish/unpublish exams, view per-exam results.
- **Student**: Browse published exams, take an exam with a live countdown timer
  (auto-submits at time-up), see instant auto-graded results with answer review,
  and view history of past attempts.
- A default admin account is auto-created on first run from the `.env` file.

## Setup

1. Create a virtual environment (recommended) and install dependencies:

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Review `.env` — it already contains working defaults, including the seeded
   admin login:

   ```
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=Admin@123
   ```

   Change `SECRET_KEY` and the admin password before any real deployment.

3. Run the app:

   ```bash
   python run.py
   ```

4. Open `http://localhost:5000` in your browser.
   - Log in as `admin` / `Admin@123` to manage users and exams.
   - Register a teacher account to create and publish exams.
   - Register a student account to take published exams.

The SQLite database (`instance/exam_system.db`) is created automatically on
first run — no manual migration step needed.

### Quickly testing the Teacher and Student interfaces

The Admin role is deliberately limited to user/exam oversight — it cannot
create or take exams itself (that's the Teacher's and Student's job). To try
those interfaces without manually registering accounts, run the demo seeder
once the app has been started at least once:

```bash
python seed_demo.py
```

This creates (if they don't already exist):
- `teacher_demo` / `Teacher@123` — owns a published exam, "General Knowledge Quiz"
- `student_demo` / `Student@123` — can immediately take that exam

Log out of admin and log in as either to explore that role's interface. The
script is safe to re-run; it skips anything that already exists.

## Running Tests

```bash
pip install -r requirements.txt   # includes pytest
pytest
```

Tests cover registration/login, teacher exam creation & publishing, correct
and incorrect auto-grading, admin user management (including disabling a
user's login), and role-based access enforcement (`tests/test_app.py`).

## Deployment

- **`wsgi.py`** — production entry point (`gunicorn wsgi:app`); `run.py` stays
  for local development with the Flask reloader.
- **`Procfile`** — for Heroku/Render-style platforms.
- **`Dockerfile`** / **`docker-compose.yml`** — containerized run:
  ```bash
  docker compose up --build
  ```
  Set a real `SECRET_KEY` and admin password in `.env` before deploying
  anywhere public, and point `DATABASE_URL` at a persistent/production
  database (e.g. Postgres) rather than the default SQLite file.

## Project Structure

```
online-examination-system/
├── app/
│   ├── __init__.py          # App factory, DB/login init, admin seeding
│   ├── models/models.py     # User, Exam, Question, Choice, Submission, Answer
│   ├── routes/
│   │   ├── auth.py          # register/login/logout
│   │   ├── admin.py         # user & exam management
│   │   ├── teacher.py       # exam & question CRUD, publishing, results
│   │   └── student.py       # browse/take exams, results, history
│   ├── services/assessment.py  # grading logic (auto-scores MCQ submissions)
│   ├── static/css/style.css
│   └── templates/           # Jinja2 templates for each role
├── tests/
│   ├── conftest.py           # pytest fixtures (isolated temp-file DB per run)
│   └── test_app.py           # auth, teacher, student, admin functional tests
├── config.py                 # Config loaded from .env
├── run.py                    # Local dev entry point
├── wsgi.py                   # Production entry point (gunicorn)
├── seed_demo.py               # One-command demo teacher/student/exam seeder
├── requirements.txt
├── pytest.ini
├── Procfile                  # Heroku/Render style deployment
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── LICENSE
└── .env
```

## Notes on Design Decisions

- **Role-based access** is enforced via a `role_required` decorator (`app/utils.py`)
  checked on every protected route.
- **Grading** is isolated in `app/services/assessment.py` so scoring logic can be
  extended (e.g. partial credit, new question types) without touching route code.
- **One submission per student per exam** is enforced at the database level
  (unique constraint on `exam_id` + `student_id`) and checked in the route.
- Disabling a user account (`is_active_account = False`) immediately blocks login
  without deleting their historical data.
