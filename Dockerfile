# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies for psycopg2 and other packages
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations (Optional: Can also be done in the release phase/command)
# RUN python manage.py migrate --noinput

# Expose the port the app runs on
EXPOSE 8000

# Start daphne
CMD daphne -b 0.0.0.0 -p $PORT websocket_project.asgi:application
