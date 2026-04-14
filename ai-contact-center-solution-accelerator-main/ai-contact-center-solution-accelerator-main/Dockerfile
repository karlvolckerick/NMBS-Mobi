FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies without BuildKit-specific mounts for broad builder compatibility
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY . .

# Install the project
RUN uv sync --frozen --no-dev


# Production stage
FROM python:3.12-slim-bookworm AS production

# Create non-root user for security
RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

WORKDIR /app

# Copy only the virtual environment and application code from builder
COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv
COPY --from=builder --chown=nonroot:nonroot /app/src /app/src
COPY --from=builder --chown=nonroot:nonroot /app/config.yaml /app/config.yaml

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root user
USER nonroot

# Run the application
CMD ["fastapi", "run", "src/ai_contact_centre_solution_accelerator/main.py", "--port", "80"]
