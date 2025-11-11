# Project Firefly Dockerfile
# Optimized for Raspberry Pi (ARM architecture)

FROM python:3.11-alpine

# Set metadata
LABEL maintainer="Project Firefly"
LABEL description="Lightweight DNS filtering application with whitelist-only policy"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create application user (for security)
RUN addgroup -g 1000 firefly && \
    adduser -D -u 1000 -G firefly firefly

# Create application directories
RUN mkdir -p /app/data /app/logs && \
    chown -R firefly:firefly /app

# Set working directory
WORKDIR /app

# Install system dependencies (minimal set for Alpine)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    wget \
    && rm -rf /var/cache/apk/*

# Copy requirements first (for better layer caching)
COPY --chown=firefly:firefly requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=firefly:firefly app/ ./app/
COPY --chown=firefly:firefly config/ ./config/
COPY --chown=firefly:firefly run.py .

# Make run.py executable
RUN chmod +x run.py

# Create volumes for persistent data
VOLUME ["/app/data", "/app/logs"]

# Expose ports
# DNS server (UDP)
EXPOSE 53/udp
# Web interface
EXPOSE 8080/tcp

# Switch to non-root user
USER firefly

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/api/stats || exit 1

# Run application
CMD ["python", "run.py"]
