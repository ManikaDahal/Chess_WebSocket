# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Create a non-root user (Hugging Face default is 1000)
RUN useradd -m -u 1000 user

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY --chown=user:user . /app/

# Switch to the non-root user
USER user

# Expose the port Hugging Face Spaces expects
EXPOSE 7860

# Command to run the application using Daphne (ASGI) on port 7860
CMD ["daphne", "-b", "0.0.0.0", "-p", "7860", "websocket_project.asgi:application"]
