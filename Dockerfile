FROM python:3.11-slim

WORKDIR /app/src/image-creator

# Install uv via pip
RUN pip install uv

# Copy project files
COPY src/image-creator/__init__.py ./
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies with uv using lockfile
RUN uv sync --frozen

COPY src/image-creator ./

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Run the application
CMD ["uv", "run", "python", "main.py"]