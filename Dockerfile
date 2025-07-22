# Live HLS Stream Monitor Docker Container
FROM python:3.10-slim

# Set metadata
LABEL maintainer="Live HLS Stream Monitor"
LABEL description="Real-time HLS stream monitoring and analysis tool"
LABEL version="1.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app directory
WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Copy requirements first for better Docker layer caching
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt && \
    pip install --user --no-cache-dir psutil

# Copy application code
COPY --chown=appuser:appuser . .

# Expose the port the app runs on
EXPOSE 8181

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8181/api/health-check || exit 1

# Run the application
CMD ["python", "app.py"]
