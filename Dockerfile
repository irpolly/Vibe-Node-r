
# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Make port 8080 available to the world outside this container
# Cloud Run expects the container to listen on the port defined by the PORT env var.
# 8080 is the default.
EXPOSE 8080

# Run main.py when the container launches using gunicorn
# The API_KEY will be injected by the Cloud Run service from Secret Manager.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
# Note: For local testing, you can set the PORT environment variable before running the container:
# docker run -e PORT=8080 -p 8080:8080 your-image

