# Auth Starter

A reusable authentication foundation built with a **FastAPI** backend, **React + TypeScript** frontend, and **PostgreSQL** database.

It includes registration, username availability checks, email verification, secure password hashing, login/logout, protected sessions, password recovery, and a local email inbox for development.

## Features

- Email and username registration
- Database-enforced unique email addresses and usernames
- Live username availability endpoint
- Argon2id password hashing
- One-use, expiring email-verification links
- Login with either username or email
- Server-side revocable sessions in `HttpOnly` cookies
- CSRF protection for cookie-authenticated actions
- Password reset with automatic session revocation
- Rate limiting for registration, login, and recovery endpoints
- Local PostgreSQL database and Mailpit email inbox through Docker

## Technology

| Area | Tool |
| --- | --- |
| Backend API | Python 3.12+ and FastAPI |
| Database | PostgreSQL 17 |
| Database migrations | Alembic and SQLAlchemy |
| Frontend | React, TypeScript, Vite |
| Local services | Docker Compose and Mailpit |

## Prerequisites

Install these before running the project:

1. [Python 3.12 or newer](https://www.python.org/downloads/)
2. [Node.js](https://nodejs.org/)
3. [Docker Desktop](https://www.docker.com/products/docker-desktop/)

Confirm the installations in PowerShell:

```powershell
py --version
node --version
npm --version
docker --version
```

## Run locally for the first time

Open PowerShell in the project folder:

```powershell
cd "C:\Users\Asenika\Documents\Codex\2026-09-03\i\auth-starter"
```

### 1. Start PostgreSQL and the local email inbox

```powershell
docker compose up -d
docker compose ps
```

You should see `auth-starter-db` and `auth-starter-mailpit`.

### 2. Set up the backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
.\.venv\Scripts\alembic.exe upgrade head
```

Start the API:

```powershell
.\.venv\Scripts\fastapi.exe dev app\main.py
```

Leave this PowerShell window open.

### 3. Set up the frontend

Open a **second** PowerShell window:

```powershell
cd "C:\Users\Asenika\Documents\Codex\2026-09-03\i\auth-starter\frontend"
npm install --cache .npm-cache
npm run dev
```

Open the application in your browser:

- Frontend: [http://localhost:5173](http://localhost:5173)
- API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- API health check: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- Local email inbox: [http://127.0.0.1:8025](http://127.0.0.1:8025)

## Test the authentication flow

1. Open the frontend at `http://localhost:5173`.
2. Create a new account.
3. Open Mailpit at `http://127.0.0.1:8025`.
4. Open the verification email and select its link.
5. Sign in with your verified username or email and password.
6. Open the Account page.
7. Test **Forgot password?** from the Sign in page.

Mailpit is only a local test inbox. No verification or password-reset email is sent to the internet during development.

## Project structure

```text
auth-starter/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Configuration, database, rate limiting
│   │   ├── models/       # SQLAlchemy database models
│   │   ├── schemas/      # Request and response validation
│   │   └── services/     # Email and session helpers
│   ├── alembic/          # Database migration history
│   ├── .env.example      # Safe configuration template
│   └── pyproject.toml    # Python dependencies
├── frontend/
│   ├── src/pages/        # Registration, login, recovery, account screens
│   └── package.json      # JavaScript dependencies
├── compose.yaml          # PostgreSQL and Mailpit containers
└── README.md
```

## Configuration and secrets

The local configuration is stored in `backend/.env`.

Do **not** upload this file to GitHub. It is already excluded by `.gitignore`.

For production, use a new long random value for `SESSION_SECRET`, configure a real email provider, and change these settings:

```text
ENVIRONMENT=production
COOKIE_SECURE=true
```

Production must run behind HTTPS. The application enables HTTPS redirects when `ENVIRONMENT=production`.

## Useful commands

### Stop local services

```powershell
docker compose down
```

### Start local services again

```powershell
docker compose up -d
```

### Apply new database migrations

Run this after pulling changes that add a migration:

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
```

### Build the frontend for production

```powershell
cd frontend
npm run build
```

### Check current database tables

```powershell
docker compose exec db psql -U auth_user -d auth_starter -c "\dt"
```

## Troubleshooting

### API health says `database: unavailable`

Run:

```powershell
docker compose up -d
docker compose ps
```

Then restart FastAPI.

### Mailpit does not open

Run:

```powershell
docker compose up -d mailpit
docker compose logs mailpit --tail 50
```

Then open `http://127.0.0.1:8025`.

### Frontend cannot connect to the API

Make sure both are running:

- FastAPI: `http://localhost:8000/api/health`
- React: `http://localhost:5173`

### `npm install` cannot use the default cache

Use the project-local cache command shown above:

```powershell
npm install --cache .npm-cache
```

## Security notes

This project provides a strong starting point, but deployment remains a security responsibility. Before putting it on the public internet, use HTTPS, a real transactional email provider, secure environment-variable storage, backups, monitoring, and a shared Redis-backed rate limiter when running more than one API server.
