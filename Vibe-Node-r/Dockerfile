# --- Stage 1: Build the React Frontend ---
FROM node:20-slim AS builder

WORKDIR /app

RUN npm install -g npm@11.6.2  # Bump to latest—nukes ancient lock woes

COPY package*.json ./
RUN npm ci  # Keep for speed/reproducibility; now sync-safe

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