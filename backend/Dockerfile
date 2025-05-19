# Start from a Python base image
FROM python:3.11-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if any (e.g., for psycopg2 build if not using binary)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev

# Copy the requirements file into the container
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application code into the container
# This will be overridden by the volume mount in docker-compose.yml for development,
# but is useful for building a standalone image.
COPY . /app/

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn
# For development, we often override this in docker-compose.yml for live reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]