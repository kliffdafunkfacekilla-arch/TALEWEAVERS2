# Dockerfile for TALEWEAVERS World Architect (C++ + Python Wrapper)
FROM python:3.10-slim

# Install C++ build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the specific service folder
COPY saga_architect/ /app/

# Build the C++ Engine with verbose output to debug failures
RUN mkdir -p build && cd build && \
    cmake .. && \
    make VERBOSE=1

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn pydantic

EXPOSE 8012

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012"]
