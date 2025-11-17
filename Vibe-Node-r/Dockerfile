
# --- Stage 1: Build the React Frontend ---
# Use a Node.js image as the builder
FROM node:20-slim as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# --- Stage 2: Build the Python Backend ---
# Use the Python image for the final container
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
COPY session.py .
COPY agents.py .
COPY mcp_handler.py .
# Copy the built frontend static files from the 'builder' stage's /app/build directory
# into a 'build' directory in the final container. The Python app is configured to serve from 'build'.
COPY --from=builder /app/build ./build
EXPOSE 8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
