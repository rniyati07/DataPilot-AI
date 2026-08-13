# Backend Dockerfile for QueryVista
# Multi-stage build for smaller production image

# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app/backend

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Runtime stage
FROM python:3.12-slim AS runtime

WORKDIR /app/backend

# Install runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy backend application code
COPY backend/app ./app
COPY backend/data ./data

# Create uploads directory (will be mounted as volume in production)
RUN mkdir -p ./data/uploads

# Expose backend port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]