FROM python:3.11-slim

WORKDIR /mcp_server

### Install general package requirements ###
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies with uv using lockfile
COPY ./pyproject.toml ./uv.lock ./
COPY src/mcp_server/__init__.py src/mcp_server/__init__.py
RUN python -m pip install --upgrade --no-cache-dir pip && \
    pip install --no-cache-dir uv && \
    uv venv .venv && \
    . .venv/bin/activate && \
    uv sync --frozen
ENV PATH="/mcp_server/.venv/bin:$PATH"
COPY ./src ./src

# Expose port
ENV API_PORT=8001
EXPOSE 8001

# Run the application
CMD ["start-mcp"]