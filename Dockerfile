# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /usr/src/app

# Install system dependencies that might be needed by Python packages (if any)
# For now, this is minimal. Add more if specific packages require them.
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /usr/src/app
COPY dockyard_app/requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the .flaskenv file (if you want to bundle it, or manage env vars differently)
COPY dockyard_app/.flaskenv ./

# Copy the rest of the application code into the container at /usr/src/app
COPY dockyard_app/ ./dockyard_app/

# Make port 5001 available to the world outside this container
# This is the port specified in run.py
EXPOSE 5001

# Define environment variables for Flask (can also be set in .flaskenv or at runtime)
ENV FLASK_APP=dockyard_app/run.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5001
# SECRET_KEY should ideally be set at runtime for production, but can have a default here for dev
ENV SECRET_KEY='dev-secret-key-please-change'
# TEMPLATE_SOURCES_URL can be overridden at runtime
ENV TEMPLATE_SOURCES_URL='https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json'


# Run run.py when the container launches
# Using flask run which is good for development. For production, gunicorn would be better.
# CMD ["python", "dockyard_app/run.py"]
# Using flask run command:
CMD ["flask", "run"]
