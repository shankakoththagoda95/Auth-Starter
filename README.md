# Auth Starter

A reusable authentication foundation built with FastAPI, React, and PostgreSQL.

## What is here so far?

- `backend/`: the Python API. Its health endpoint is `http://localhost:8000/api/health`.
- `frontend/`: the React website, shown at `http://localhost:5173`.
- `compose.yaml`: local PostgreSQL and Mailpit, a development-only email inbox at `http://localhost:8025`.

## First run

1. Open a PowerShell window in this folder.
2. Start the database and local email inbox: `docker compose up -d`.
3. Create the API environment: `py -m venv backend/.venv`.
4. Activate it: `backend/.venv/Scripts/Activate.ps1`.
5. Install API packages: `pip install -e "./backend[dev]"`.
6. Copy the configuration template: `Copy-Item backend/.env.example backend/.env`. Keep the development values for now.
7. In `backend/`, start the API: `fastapi dev app/main.py`.
8. In a second PowerShell window, run `npm install` inside `frontend/`, then `npm run dev`.

## Never commit

The `backend/.env` file holds configuration and future secrets. It is intentionally excluded by `.gitignore`.
