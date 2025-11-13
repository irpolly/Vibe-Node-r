# --- Stage 1: Build the React Frontend ---
FROM node:20-slim AS builder

WORKDIR /app

RUN npm install -g npm@latest

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build  # ← This now creates /app/build

# --- Stage 2: Python Backend ---
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY session.py .
COPY agents.py .

# ← CORRECT: Copy from builder's /app/build
COPY --from=builder /app/build ./build

EXPOSE 8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app