# Use uv's official Python image
FROM ghcr.io/astral-sh/uv:0.9-python3.13-bookworm-slim@sha256:bf39f30fb4598ceff268ef845db12d8ea373405b4fbe99056dd198dcfc7c61af

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (production only, frozen lockfile)
RUN uv sync --frozen --no-dev --no-install-project

# Copy the application files
COPY app ./app

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application using Gunicorn via uv
CMD ["uv", "run", "--no-dev", "gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app.app:app"]
