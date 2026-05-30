# ── Stage: base ───────────────────────────────────────────────────────────────
# Runtime dependencies saja — digunakan sebagai dasar stage lainnya.
FROM python:3.11-slim AS base

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN python -m pip install --no-cache-dir --upgrade pip setuptools>=68 wheel && \
    pip install --no-cache-dir .

# ── Stage: test ───────────────────────────────────────────────────────────────
# Menyertakan dev dependencies dan test files. Digunakan khusus untuk pytest.
FROM base AS test

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY tests/ tests/

# Set env vars dummy agar pydantic-settings tidak error saat test
ENV BUDGET_API_BASE_URL=http://api.budget-test.local \
    BUDGET_API_USERNAME=test \
    BUDGET_API_PASSWORD=test

CMD ["python", "-m", "pytest", "tests/", "-v"]

# ── Stage: production ─────────────────────────────────────────────────────────
# Image ramping untuk deployment — tidak menyertakan test files.
FROM base AS production

ENV MCP_LOG_LEVEL=INFO

EXPOSE 9170

CMD ["uvicorn", "budget_sekolah_mcp.asgi:app", "--host", "0.0.0.0", "--port", "9170"]
