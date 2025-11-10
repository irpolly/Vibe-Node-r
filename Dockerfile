
# --- Stage 1: Build the React Frontend ---
# Use a Node.js image as the builder
FROM node:20-slim as builder

# Set the working directory
WORKDIR /app

# Copy package.json and install dependencies
# This leverages Docker layer caching
COPY package*.json ./
RUN npm install

# Copy the rest of the frontend source code
COPY . .

# Build the static files. This creates a /app/build directory.
RUN npm run build

# --- Stage 2: Build the Python Backend ---
# Use the Python image for the final container
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy Python dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python backend code
COPY main.py .
COPY session.py .
COPY agents.py .

# Copy the local JS libraries
COPY libs ./libs

# Copy the built frontend static files from the 'builder' stage's /app/build directory
# into a 'build' directory in the final container. The Python app is configured to serve from 'build'.
COPY --from=builder /app/build ./build

# Make port 8080 available
EXPOSE 8080

# Run the Gunicorn server
# The API_KEY will be injected by the Cloud Run service from Secret Manager.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
