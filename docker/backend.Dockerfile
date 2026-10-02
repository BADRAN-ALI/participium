FROM python:3.11-slim

WORKDIR /usr/src/app

# Install Python dependencies first to leverage Docker layer caching.
COPY src/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application source.
COPY src/backend/ .

EXPOSE 5050

# Development server; --without-threads keeps the single-connection SQLAlchemy session safe.
CMD ["flask", "--app", "wsgi:app", "run", "--host", "0.0.0.0", "--port", "5050", "--without-threads"]
