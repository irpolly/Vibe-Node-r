
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

# Define environment variable for the API key
# This should be set in the Cloud Run service configuration for security.
ENV API_KEY=""

# Run main.py when the container launches
# Use gunicorn for a production-ready server
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
