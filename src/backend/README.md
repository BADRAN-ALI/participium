# Participium Backend

Python/Flask backend with SQLAlchemy persistence, REST APIs, Swagger/OpenAPI documentation, and pytest-based tests.

## Setup

Create a local environment file first:

### Windows PowerShell

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python wsgi.py
```

### Linux / macOS

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python wsgi.py
```

The backend normally runs at `http://localhost:5050`.

Swagger UI is available at `http://localhost:5050/apidocs/`.

## Tests

```bash
python -m pytest
```

The test suite contains unit, integration, black-box, white-box, and end-to-end coverage.