FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system deps: curl for healthcheck, libs for Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2t64 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

# Install Playwright Chromium browser binary (D-08 JS fallback)
RUN uv run playwright install chromium

# Copy application code
COPY . .

# Create non-root user and set ownership
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && mkdir -p /home/appuser/.cache \
    && chown -R appuser:appgroup /app /home/appuser/.cache

USER appuser

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
