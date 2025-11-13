# --- Stage 1: Build the React Frontend ---
FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci  # Switch to ci for lock-exact installs (faster, reproducible—fails if mismatch)

COPY . .
RUN npm run build

# --- Stage 2: Python Backend ---
FROM python:3.11-slim

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY main.py .
COPY session.py .
COPY agents.py .

# Copy built frontend
COPY --from=builder /app/build ./build

EXPOSE 8080

# Dynamic port for Cloud Run
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app